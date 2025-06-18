#!/usr/bin/env python3
"""
MoE Backend Server - Real-time streaming backend for Mixture of Experts model inference.

This server provides:
- Real-time token streaming during inference
- Expert selection visualization data for each layer and token
- WebSocket-based communication with frontends
- Chat interface with MoE models
- Connection to other services via --bind argument
"""

import asyncio
import json
import logging
import argparse
import time
from typing import Dict, List, Optional, Any, AsyncIterator
from dataclasses import dataclass, asdict
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor
import queue

import torch
from flask import Flask, request, jsonify
from flask_sock import Sock
import requests

# Import the llm_sidechannel components
import sys
import os

from llm_sidechannel.core.mixtral_client import MixtralClient, MixtralResponse
from llm_sidechannel.core.router_analyzer import RouterAnalyzer
from llm_sidechannel.analysis.expert_usage import ExpertUsageAnalyzer
from llm_sidechannel.core.config import MixtralConfig, load_model_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class StreamingToken:
    """A single token in the streaming response."""
    token_id: int
    token_text: str
    position: int
    timestamp: float
    router_data: Optional[Dict[str, Any]] = None

@dataclass
class ExpertSelection:
    """Expert selection data for a single layer and token."""
    layer_idx: int
    token_position: int
    expert_weights: List[float]
    selected_experts: List[int]
    router_logits: List[float]
    timestamp: float

class MoEInferenceEngine:
    """Handles MoE model inference with real-time streaming."""
    
    def __init__(self, config: MixtralConfig):
        self.config = config
        self.client = None
        self.router_analyzer = None
        self.usage_analyzer = None
        self.is_loaded = False
        
    async def load_model(self):
        """Load the MoE model in a separate thread."""
        if self.is_loaded:
            return
            
        logger.info("Loading MoE model...")
        loop = asyncio.get_event_loop()
        
        def _load():
            self.client = MixtralClient(
                model_name=self.config.model_name,
                device=self.config.device,
                torch_dtype=self.config.torch_dtype,
                load_in_8bit=self.config.load_in_8bit,
                load_in_4bit=self.config.load_in_4bit,
                device_map=self.config.device_map
            )
            self.router_analyzer = RouterAnalyzer(
                num_experts=self.client.num_experts,
                experts_per_token=self.client.experts_per_token
            )
            self.router_analyzer.set_tokenizer(self.client.tokenizer)
            self.usage_analyzer = ExpertUsageAnalyzer(num_experts=self.client.num_experts)
            return True
            
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = loop.run_in_executor(executor, _load)
            self.is_loaded = await future
            
        logger.info("MoE model loaded successfully")
    
    async def generate_streaming(
        self,
        prompt: str,
        conversation_id: str,
        message_id: str,
        **generation_kwargs
    ) -> AsyncIterator[Dict[str, Any]]:
        """Generate tokens with streaming and real-time expert analysis."""
        if not self.is_loaded:
            await self.load_model()
        
        logger.info(f"Starting streaming generation for conversation {conversation_id}")
        
        # Start generation in a separate thread
        generation_queue = queue.Queue()
        stop_event = threading.Event()
        
        def _generate():
            try:
                # Custom generation with token-by-token streaming
                inputs = self.client.tokenizer(prompt, return_tensors="pt")
                if self.client.device != "cpu":
                    inputs = {k: v.to(self.client.device) for k, v in inputs.items()}
                
                input_length = inputs.input_ids.shape[1]
                generated_tokens = []
                expert_data = []
                
                # Generation parameters
                max_new_tokens = generation_kwargs.get('max_new_tokens', 100)
                temperature = generation_kwargs.get('temperature', 0.7)
                top_p = generation_kwargs.get('top_p', 0.9)
                
                current_input_ids = inputs.input_ids
                
                for step in range(max_new_tokens):
                    if stop_event.is_set():
                        break
                        
                    with torch.no_grad():
                        outputs = self.client.model(
                            input_ids=current_input_ids,
                            attention_mask=torch.ones_like(current_input_ids),
                            output_router_logits=True,
                            return_dict=True
                        )
                    
                    # Get next token
                    logits = outputs.logits[0, -1, :]
                    if temperature > 0:
                        logits = logits / temperature
                        probs = torch.softmax(logits, dim=-1)
                        if top_p < 1.0:
                            sorted_probs, sorted_indices = torch.sort(probs, descending=True)
                            cumulative_probs = torch.cumsum(sorted_probs, dim=-1)
                            sorted_indices_to_remove = cumulative_probs > top_p
                            sorted_indices_to_remove[1:] = sorted_indices_to_remove[:-1].clone()
                            sorted_indices_to_remove[0] = 0
                            indices_to_remove = sorted_indices[sorted_indices_to_remove]
                            probs[indices_to_remove] = 0
                            probs = probs / probs.sum()
                        next_token = torch.multinomial(probs, num_samples=1)
                    else:
                        next_token = torch.argmax(logits, dim=-1, keepdim=True)
                    
                    next_token_id = next_token.item()
                    next_token_text = self.client.tokenizer.decode([next_token_id])
                    
                    # Process router logits if available
                    router_data = None
                    if hasattr(outputs, 'router_logits') and outputs.router_logits:
                        router_selections, expert_usage = self.client._analyze_routing(outputs.router_logits)
                        
                        # Create expert selection data for each layer
                        layer_data = []
                        for layer_idx, router_logits in enumerate(outputs.router_logits):
                            if router_logits is not None:
                                # Get the router logits for the last token
                                last_token_logits = router_logits[0, -1, :].cpu().numpy()
                                router_probs = torch.softmax(router_logits[0, -1, :], dim=-1).cpu().numpy()
                                
                                # Get top experts
                                top_expert_indices = torch.topk(router_logits[0, -1, :], k=self.client.experts_per_token).indices.cpu().numpy()
                                top_expert_weights = router_probs[top_expert_indices]
                                
                                expert_sel = ExpertSelection(
                                    layer_idx=layer_idx,
                                    token_position=len(generated_tokens),
                                    expert_weights=router_probs.tolist(),
                                    selected_experts=top_expert_indices.tolist(),
                                    router_logits=last_token_logits.tolist(),
                                    timestamp=time.time()
                                )
                                layer_data.append(expert_sel)
                        
                        expert_data.extend(layer_data)
                        router_data = {
                            'layer_count': len(outputs.router_logits),
                            'expert_selections': [asdict(sel) for sel in layer_data]
                        }
                    
                    # Create streaming token
                    streaming_token = StreamingToken(
                        token_id=next_token_id,
                        token_text=next_token_text,
                        position=len(generated_tokens),
                        timestamp=time.time(),
                        router_data=router_data
                    )
                    
                    generated_tokens.append(streaming_token)
                    
                    # Send token to queue
                    generation_queue.put({
                        'type': 'token',
                        'data': asdict(streaming_token)
                    })
                    
                    # Update input for next iteration
                    current_input_ids = torch.cat([current_input_ids, next_token.unsqueeze(0)], dim=-1)
                    
                    # Check for end of sequence
                    if next_token_id == self.client.tokenizer.eos_token_id:
                        break
                
                # Send completion signal
                generation_queue.put({
                    'type': 'complete',
                    'data': {
                        'conversation_id': conversation_id,
                        'message_id': message_id,
                        'total_tokens': len(generated_tokens),
                        'total_expert_selections': len(expert_data)
                    }
                })
                
            except Exception as e:
                logger.error(f"Error in generation: {e}")
                generation_queue.put({
                    'type': 'error',
                    'data': {'error': str(e)}
                })
        
        # Start generation thread
        generation_thread = threading.Thread(target=_generate)
        generation_thread.start()
        
        # Yield tokens as they become available
        try:
            while True:
                try:
                    item = generation_queue.get(timeout=30.0)  # 30 second timeout
                    yield item
                    
                    if item['type'] in ['complete', 'error']:
                        break
                        
                except queue.Empty:
                    logger.warning("Generation timeout - stopping")
                    stop_event.set()
                    break
        finally:
            stop_event.set()
            generation_thread.join(timeout=5.0)

class MoEBackendServer:
    """Main MoE backend server with WebSocket support."""
    
    def __init__(self, host: str = "localhost", port: int = 8765, bind_to: Optional[str] = None):
        self.host = host
        self.port = port
        self.bind_to = bind_to
        self.clients = {}
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}
        
        # Initialize Flask app for HTTP endpoints
        self.app = Flask(__name__)
        self.sock = Sock(self.app)
        
        # Initialize inference engine
        config = load_model_config("balanced")  # Use balanced preset
        self.inference_engine = MoEInferenceEngine(config)
        
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup HTTP routes."""
        
        @self.app.route('/health')
        def health():
            return jsonify({
                'status': 'healthy',
                'model_loaded': self.inference_engine.is_loaded,
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/model/info')
        def model_info():
            if not self.inference_engine.is_loaded:
                return jsonify({'error': 'Model not loaded'}), 503
            
            return jsonify({
                'model_name': self.inference_engine.config.model_name,
                'num_experts': self.inference_engine.client.num_experts,
                'experts_per_token': self.inference_engine.client.experts_per_token,
                'device': self.inference_engine.client.device,
                'dtype': str(self.inference_engine.client.torch_dtype)
            })
        
        @self.app.route('/conversations')
        def list_conversations():
            return jsonify({
                'conversations': list(self.conversations.keys()),
                'count': len(self.conversations)
            })
        
        @self.app.route('/conversations/<conversation_id>')
        def get_conversation(conversation_id):
            if conversation_id not in self.conversations:
                return jsonify({'error': 'Conversation not found'}), 404
            
            return jsonify({
                'conversation_id': conversation_id,
                'messages': self.conversations[conversation_id]
            })
        
        @self.sock.route('/ws')
        def websocket_handler(ws):
            """Handle WebSocket connections for real-time streaming."""
            client_id = id(ws)
            self.clients[client_id] = ws
            logger.info(f"Client {client_id} connected")
            
            try:
                while True:
                    message = ws.receive()
                    if message:
                        asyncio.create_task(self._handle_websocket_message(client_id, json.loads(message)))
            except Exception as e:
                logger.error(f"WebSocket error for client {client_id}: {e}")
            finally:
                if client_id in self.clients:
                    del self.clients[client_id]
                logger.info(f"Client {client_id} disconnected")
    
    async def _handle_websocket_message(self, client_id: str, message: Dict[str, Any]):
        """Handle incoming WebSocket messages."""
        try:
            message_type = message.get('type')
            
            if message_type == 'chat':
                await self._handle_chat_message(client_id, message)
            elif message_type == 'load_model':
                await self._handle_load_model(client_id)
            elif message_type == 'get_conversations':
                await self._send_to_client(client_id, {
                    'type': 'conversations',
                    'data': {
                        'conversations': list(self.conversations.keys())
                    }
                })
            else:
                await self._send_to_client(client_id, {
                    'type': 'error',
                    'data': {'error': f'Unknown message type: {message_type}'}
                })
                
        except Exception as e:
            logger.error(f"Error handling message from client {client_id}: {e}")
            await self._send_to_client(client_id, {
                'type': 'error',
                'data': {'error': str(e)}
            })
    
    async def _handle_chat_message(self, client_id: str, message: Dict[str, Any]):
        """Handle chat messages with streaming response."""
        data = message.get('data', {})
        prompt = data.get('prompt', '')
        conversation_id = data.get('conversation_id', f"conv_{int(time.time())}")
        message_id = f"msg_{int(time.time() * 1000)}"
        
        if not prompt:
            await self._send_to_client(client_id, {
                'type': 'error',
                'data': {'error': 'No prompt provided'}
            })
            return
        
        # Initialize conversation if needed
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        
        # Add user message to conversation
        user_message = {
            'role': 'user',
            'content': prompt,
            'timestamp': datetime.now().isoformat(),
            'message_id': message_id + '_user'
        }
        self.conversations[conversation_id].append(user_message)
        
        # Send acknowledgment
        await self._send_to_client(client_id, {
            'type': 'chat_start',
            'data': {
                'conversation_id': conversation_id,
                'message_id': message_id,
                'user_message': user_message
            }
        })
        
        # Generate streaming response
        assistant_content = ""
        async for stream_item in self.inference_engine.generate_streaming(
            prompt, conversation_id, message_id,
            **data.get('generation_params', {})
        ):
            # Send streaming data to client
            await self._send_to_client(client_id, {
                'type': 'stream',
                'data': stream_item
            })
            
            # Accumulate response text
            if stream_item['type'] == 'token':
                assistant_content += stream_item['data']['token_text']
        
        # Add assistant message to conversation
        assistant_message = {
            'role': 'assistant',
            'content': assistant_content,
            'timestamp': datetime.now().isoformat(),
            'message_id': message_id + '_assistant'
        }
        self.conversations[conversation_id].append(assistant_message)
    
    async def _handle_load_model(self, client_id: str):
        """Handle model loading request."""
        await self._send_to_client(client_id, {
            'type': 'model_loading',
            'data': {'status': 'loading'}
        })
        
        try:
            await self.inference_engine.load_model()
            await self._send_to_client(client_id, {
                'type': 'model_loaded',
                'data': {
                    'status': 'loaded',
                    'model_info': {
                        'model_name': self.inference_engine.config.model_name,
                        'num_experts': self.inference_engine.client.num_experts,
                        'experts_per_token': self.inference_engine.client.experts_per_token
                    }
                }
            })
        except Exception as e:
            await self._send_to_client(client_id, {
                'type': 'model_error',
                'data': {'error': str(e)}
            })
    
    async def _send_to_client(self, client_id: str, message: Dict[str, Any]):
        """Send message to specific client."""
        if client_id in self.clients:
            try:
                self.clients[client_id].send(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending to client {client_id}: {e}")
                if client_id in self.clients:
                    del self.clients[client_id]
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients."""
        disconnected = []
        for client_id, ws in self.clients.items():
            try:
                ws.send(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to client {client_id}: {e}")
                disconnected.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected:
            if client_id in self.clients:
                del self.clients[client_id]
    
    def run(self):
        """Run the backend server."""
        logger.info(f"Starting MoE Backend Server on {self.host}:{self.port}")
        
        if self.bind_to:
            logger.info(f"Will bind to external service: {self.bind_to}")
            # TODO: Implement binding to external service (like web_ui.server)
        
        # Run Flask app with WebSocket support
        self.app.run(host=self.host, port=self.port, debug=False, threaded=True)

def main():
    """Main entry point for the MoE backend server."""
    parser = argparse.ArgumentParser(description='MoE Backend Server')
    parser.add_argument('--host', default='localhost', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8765, help='Port to bind to')
    parser.add_argument('--bind', help='External service to bind to (e.g., localhost:5000)')
    parser.add_argument('--model', default='mistralai/Mixtral-8x7B-Instruct-v0.1', help='Model to load')
    parser.add_argument('--preset', default='balanced', help='Model loading preset')
    parser.add_argument('--device', help='Device to load model on')
    
    args = parser.parse_args()
    
    # Create and run server
    server = MoEBackendServer(
        host=args.host,
        port=args.port,
        bind_to=args.bind
    )
    
    try:
        server.run()
    except KeyboardInterrupt:
        logger.info("Shutting down MoE Backend Server...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

if __name__ == '__main__':
    main() 