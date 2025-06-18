#!/usr/bin/env python3
"""
CLI for MoE Backend - Command line interface for testing and interacting with the MoE backend.
"""

import asyncio
import argparse
import logging
import sys
from typing import Dict, Any

from .client import MoEBackendClient, MoEConnectionConfig, ExampleMoEChat

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InteractiveMoEChat(ExampleMoEChat):
    """Interactive command-line chat with MoE model."""
    
    def __init__(self, client: MoEBackendClient, show_expert_data: bool = True):
        super().__init__(client)
        self.show_expert_data = show_expert_data
        self.model_ready = False
    
    async def _on_token_received(self, token_data: Dict[str, Any]):
        """Print each token as it's received."""
        token_text = token_data.get('token_text', '')
        print(token_text, end='', flush=True)
        
        # Show expert info if enabled
        if self.show_expert_data:
            router_data = token_data.get('router_data')
            if router_data:
                expert_selections = router_data.get('expert_selections', [])
                if expert_selections:
                    # Show which experts were selected for this token
                    token_pos = token_data.get('position', 0)
                    selected_experts = {}
                    for selection in expert_selections:
                        layer_idx = selection.get('layer_idx', 0)
                        experts = selection.get('selected_experts', [])
                        weights = selection.get('expert_weights', [])
                        if experts:
                            selected_experts[layer_idx] = experts[:2]  # Show top 2
                    
                    if selected_experts:
                        print(f" [T{token_pos}: {dict(list(selected_experts.items())[:3])}...]", end='')
    
    async def _on_generation_complete(self, completion_data: Dict[str, Any]):
        """Print completion info."""
        print(f"\n\n✓ Generation complete:")
        print(f"  Tokens: {completion_data.get('total_tokens', 0)}")
        print(f"  Expert decisions: {completion_data.get('total_expert_selections', 0)}")
        print()
    
    async def _on_model_loaded(self, model_data: Dict[str, Any]):
        """Print model info when loaded."""
        model_info = model_data.get('model_info', {})
        print(f"✓ Model loaded: {model_info.get('model_name', 'Unknown')}")
        print(f"  Experts: {model_info.get('num_experts', 'Unknown')}")
        print(f"  Experts per token: {model_info.get('experts_per_token', 'Unknown')}")
        print()
        self.model_ready = True
    
    async def _on_model_loading(self, loading_data: Dict[str, Any]):
        """Print model loading status."""
        print("⏳ Loading model... (this may take a few minutes)")
    
    async def _on_error(self, error_data: Dict[str, Any]):
        """Print errors."""
        print(f"❌ Error: {error_data.get('error', 'Unknown error')}")
    
    async def _on_chat_start(self, start_data: Dict[str, Any]):
        """Print chat start info."""
        print(f"\n🤖 Assistant: ", end='', flush=True)

async def interactive_chat(config: MoEConnectionConfig, show_expert_data: bool = True):
    """Run interactive chat session."""
    client = MoEBackendClient(config)
    chat = InteractiveMoEChat(client, show_expert_data)
    
    print(f"🚀 Connecting to MoE Backend at {config.ws_url}")
    
    try:
        await client.connect()
        print("✓ Connected to backend")
        
        # Load model
        print("📦 Requesting model load...")
        await chat.load_model()
        
        # Wait for model to be ready
        while not chat.model_ready:
            await asyncio.sleep(0.5)
        
        print("💬 Interactive Chat Started!")
        print("Type 'quit' or 'exit' to stop, 'clear' to start new conversation")
        print("Use 'expert on/off' to toggle expert data display")
        print("-" * 60)
        
        # Interactive loop
        while client.is_connected:
            try:
                user_input = input("\n👤 You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit']:
                    break
                
                if user_input.lower() == 'clear':
                    chat.conversation_id = None
                    print("🗑️  Started new conversation")
                    continue
                
                if user_input.lower().startswith('expert '):
                    setting = user_input.lower().split()[1]
                    if setting == 'on':
                        chat.show_expert_data = True
                        print("✓ Expert data display enabled")
                    elif setting == 'off':
                        chat.show_expert_data = False
                        print("✓ Expert data display disabled")
                    else:
                        print("Usage: expert on/off")
                    continue
                
                # Send chat message
                await chat.start_chat(user_input)
                
                # Small delay to prevent tight loop
                await asyncio.sleep(0.1)
                
            except (KeyboardInterrupt, EOFError):
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                
    except Exception as e:
        print(f"❌ Connection failed: {e}")
    finally:
        await client.disconnect()

async def health_check(config: MoEConnectionConfig):
    """Check backend health."""
    client = MoEBackendClient(config)
    
    print(f"🏥 Checking health of backend at {config.http_url}")
    
    try:
        health = await client.get_health()
        if 'error' in health:
            print(f"❌ Health check failed: {health['error']}")
            return False
        
        print("✓ Backend is healthy")
        print(f"  Status: {health.get('status', 'unknown')}")
        print(f"  Model loaded: {health.get('model_loaded', 'unknown')}")
        print(f"  Timestamp: {health.get('timestamp', 'unknown')}")
        
        # Also try to get model info
        model_info = await client.get_model_info()
        if 'error' not in model_info:
            print(f"✓ Model info available")
            print(f"  Model: {model_info.get('model_name', 'unknown')}")
            print(f"  Experts: {model_info.get('num_experts', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

async def send_single_chat(config: MoEConnectionConfig, prompt: str, show_expert_data: bool = True):
    """Send a single chat message and exit."""
    client = MoEBackendClient(config)
    chat = InteractiveMoEChat(client, show_expert_data)
    
    try:
        await client.connect()
        await chat.load_model()
        
        # Wait for model to be ready
        while not chat.model_ready:
            await asyncio.sleep(0.5)
        
        print(f"👤 User: {prompt}")
        await chat.start_chat(prompt)
        
        # Wait for completion
        timeout = 60  # 60 seconds timeout
        start_time = asyncio.get_event_loop().time()
        
        while client.is_connected:
            if asyncio.get_event_loop().time() - start_time > timeout:
                print("\n⏰ Timeout reached")
                break
            await asyncio.sleep(0.1)
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await client.disconnect()

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='MoE Backend CLI')
    parser.add_argument('--host', default='localhost', help='Backend host')
    parser.add_argument('--port', type=int, default=8765, help='Backend port')
    parser.add_argument('--ssl', action='store_true', help='Use SSL/TLS')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Interactive chat command
    chat_parser = subparsers.add_parser('chat', help='Start interactive chat')
    chat_parser.add_argument('--no-expert-data', action='store_true', 
                           help='Disable expert selection data display')
    
    # Health check command
    subparsers.add_parser('health', help='Check backend health')
    
    # Single message command
    single_parser = subparsers.add_parser('send', help='Send single message')
    single_parser.add_argument('prompt', help='Message to send')
    single_parser.add_argument('--no-expert-data', action='store_true',
                             help='Disable expert selection data display')
    
    args = parser.parse_args()
    
    # Create connection config
    config = MoEConnectionConfig(
        host=args.host,
        port=args.port,
        use_ssl=args.ssl
    )
    
    if args.command == 'chat':
        show_expert_data = not args.no_expert_data
        asyncio.run(interactive_chat(config, show_expert_data))
    elif args.command == 'health':
        asyncio.run(health_check(config))
    elif args.command == 'send':
        show_expert_data = not args.no_expert_data
        asyncio.run(send_single_chat(config, args.prompt, show_expert_data))
    else:
        # Default to interactive chat
        asyncio.run(interactive_chat(config, True))

if __name__ == '__main__':
    main() 