"""
Client module for MoE Backend Server.
Provides easy interface for connecting to and interacting with the MoE backend.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, AsyncIterator, Callable
import websockets
import requests
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MoEConnectionConfig:
    """Configuration for connecting to MoE backend."""
    host: str = "localhost"
    port: int = 8765
    use_ssl: bool = False
    
    @property
    def ws_url(self) -> str:
        """Get WebSocket URL."""
        scheme = "wss" if self.use_ssl else "ws"
        return f"{scheme}://{self.host}:{self.port}/ws"
    
    @property
    def http_url(self) -> str:
        """Get HTTP URL."""
        scheme = "https" if self.use_ssl else "http"
        return f"{scheme}://{self.host}:{self.port}"

class MoEBackendClient:
    """Client for connecting to MoE Backend Server."""
    
    def __init__(self, config: MoEConnectionConfig):
        self.config = config
        self.websocket = None
        self.is_connected = False
        self.message_handlers: Dict[str, Callable] = {}
        
    async def connect(self):
        """Connect to the MoE backend server."""
        try:
            self.websocket = await websockets.connect(self.config.ws_url)
            self.is_connected = True
            logger.info(f"Connected to MoE backend at {self.config.ws_url}")
            
            # Start message handler task
            asyncio.create_task(self._handle_messages())
            
        except Exception as e:
            logger.error(f"Failed to connect to MoE backend: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from the MoE backend server."""
        if self.websocket and self.is_connected:
            await self.websocket.close()
            self.is_connected = False
            logger.info("Disconnected from MoE backend")
    
    async def _handle_messages(self):
        """Handle incoming messages from the server."""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    message_type = data.get('type')
                    
                    if message_type in self.message_handlers:
                        handler = self.message_handlers[message_type]
                        if asyncio.iscoroutinefunction(handler):
                            await handler(data)
                        else:
                            handler(data)
                            
                except json.JSONDecodeError:
                    logger.warning(f"Received invalid JSON: {message}")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
            self.is_connected = False
        except Exception as e:
            logger.error(f"Error in message handler: {e}")
            self.is_connected = False
    
    def on_message(self, message_type: str, handler: Callable):
        """Register a message handler for a specific message type."""
        self.message_handlers[message_type] = handler
    
    async def send_message(self, message: Dict[str, Any]):
        """Send a message to the server."""
        if not self.is_connected or not self.websocket:
            raise RuntimeError("Not connected to server")
        
        try:
            await self.websocket.send(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise
    
    async def load_model(self):
        """Request the server to load the MoE model."""
        await self.send_message({
            'type': 'load_model'
        })
    
    async def chat(
        self,
        prompt: str,
        conversation_id: Optional[str] = None,
        generation_params: Optional[Dict[str, Any]] = None
    ):
        """Send a chat message to the server."""
        message = {
            'type': 'chat',
            'data': {
                'prompt': prompt,
                'generation_params': generation_params or {}
            }
        }
        
        if conversation_id:
            message['data']['conversation_id'] = conversation_id
        
        await self.send_message(message)
    
    async def get_conversations(self):
        """Get list of conversations from the server."""
        await self.send_message({
            'type': 'get_conversations'
        })
    
    async def get_health(self) -> Dict[str, Any]:
        """Get server health status via HTTP."""
        try:
            response = requests.get(f"{self.config.http_url}/health", timeout=5)
            return response.json()
        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {'error': str(e)}
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get model information via HTTP."""
        try:
            response = requests.get(f"{self.config.http_url}/model/info", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f'HTTP {response.status_code}'}
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return {'error': str(e)}

class MoEStreamingChat:
    """High-level interface for streaming chat with MoE models."""
    
    def __init__(self, client: MoEBackendClient):
        self.client = client
        self.current_tokens = []
        self.current_expert_data = []
        self.conversation_id = None
        
        # Set up message handlers
        self.client.on_message('stream', self._handle_stream)
        self.client.on_message('chat_start', self._handle_chat_start)
        self.client.on_message('model_loaded', self._handle_model_loaded)
        self.client.on_message('model_loading', self._handle_model_loading)
        self.client.on_message('error', self._handle_error)
    
    async def _handle_stream(self, message: Dict[str, Any]):
        """Handle streaming data from the server."""
        stream_data = message.get('data', {})
        stream_type = stream_data.get('type')
        
        if stream_type == 'token':
            token_data = stream_data.get('data', {})
            self.current_tokens.append(token_data)
            
            # Extract expert data if available
            router_data = token_data.get('router_data')
            if router_data:
                self.current_expert_data.extend(router_data.get('expert_selections', []))
            
            # Callback for token received
            await self._on_token_received(token_data)
            
        elif stream_type == 'complete':
            # Generation complete
            await self._on_generation_complete(stream_data.get('data', {}))
            
        elif stream_type == 'error':
            # Generation error
            await self._on_generation_error(stream_data.get('data', {}))
    
    async def _handle_chat_start(self, message: Dict[str, Any]):
        """Handle chat start message."""
        data = message.get('data', {})
        self.conversation_id = data.get('conversation_id')
        self.current_tokens = []
        self.current_expert_data = []
        await self._on_chat_start(data)
    
    async def _handle_model_loaded(self, message: Dict[str, Any]):
        """Handle model loaded message."""
        await self._on_model_loaded(message.get('data', {}))
    
    async def _handle_model_loading(self, message: Dict[str, Any]):
        """Handle model loading message."""
        await self._on_model_loading(message.get('data', {}))
    
    async def _handle_error(self, message: Dict[str, Any]):
        """Handle error message."""
        await self._on_error(message.get('data', {}))
    
    # Override these methods in subclasses or set them as callbacks
    async def _on_token_received(self, token_data: Dict[str, Any]):
        """Called when a new token is received."""
        pass
    
    async def _on_generation_complete(self, completion_data: Dict[str, Any]):
        """Called when generation is complete."""
        pass
    
    async def _on_generation_error(self, error_data: Dict[str, Any]):
        """Called when generation encounters an error."""
        pass
    
    async def _on_chat_start(self, start_data: Dict[str, Any]):
        """Called when chat starts."""
        pass
    
    async def _on_model_loaded(self, model_data: Dict[str, Any]):
        """Called when model is loaded."""
        pass
    
    async def _on_model_loading(self, loading_data: Dict[str, Any]):
        """Called when model is loading."""
        pass
    
    async def _on_error(self, error_data: Dict[str, Any]):
        """Called when an error occurs."""
        pass
    
    async def start_chat(self, prompt: str, **generation_params):
        """Start a new chat conversation."""
        await self.client.chat(
            prompt=prompt,
            conversation_id=self.conversation_id,
            generation_params=generation_params
        )
    
    async def load_model(self):
        """Load the MoE model."""
        await self.client.load_model()
    
    def get_current_text(self) -> str:
        """Get the current generated text."""
        return ''.join(token.get('token_text', '') for token in self.current_tokens)
    
    def get_expert_data(self) -> list:
        """Get the current expert selection data."""
        return self.current_expert_data

# Example usage
class ExampleMoEChat(MoEStreamingChat):
    """Example implementation of MoE streaming chat."""
    
    async def _on_token_received(self, token_data: Dict[str, Any]):
        """Print each token as it's received."""
        token_text = token_data.get('token_text', '')
        print(token_text, end='', flush=True)
        
        # Print expert info if available
        router_data = token_data.get('router_data')
        if router_data:
            layer_count = router_data.get('layer_count', 0)
            print(f"\n[Token {token_data.get('position', 0)}: {layer_count} layers processed]")
    
    async def _on_generation_complete(self, completion_data: Dict[str, Any]):
        """Print completion info."""
        print(f"\n\nGeneration complete:")
        print(f"  Total tokens: {completion_data.get('total_tokens', 0)}")
        print(f"  Total expert selections: {completion_data.get('total_expert_selections', 0)}")
    
    async def _on_model_loaded(self, model_data: Dict[str, Any]):
        """Print model info when loaded."""
        model_info = model_data.get('model_info', {})
        print(f"Model loaded: {model_info.get('model_name', 'Unknown')}")
        print(f"  Experts: {model_info.get('num_experts', 'Unknown')}")
        print(f"  Experts per token: {model_info.get('experts_per_token', 'Unknown')}")
    
    async def _on_error(self, error_data: Dict[str, Any]):
        """Print errors."""
        print(f"Error: {error_data.get('error', 'Unknown error')}")

async def main():
    """Example usage of the MoE client."""
    config = MoEConnectionConfig(host="localhost", port=8765)
    client = MoEBackendClient(config)
    chat = ExampleMoEChat(client)
    
    try:
        await client.connect()
        await chat.load_model()
        
        # Wait for model to load
        await asyncio.sleep(2)
        
        # Start a chat
        await chat.start_chat("Hello! Can you explain how mixture of experts models work?")
        
        # Keep connection alive
        while client.is_connected:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main()) 