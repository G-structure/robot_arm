# MoE Backend - Mixture of Experts Real-time Streaming Backend

This backend provides real-time streaming of Mixture of Experts (MoE) model inference, including token generation and expert selection visualization data for each layer and token during inference.

## Features

- **Real-time Token Streaming**: Stream tokens as they are generated during inference
- **Expert Selection Visualization**: Detailed router logits and expert selection data for each layer
- **WebSocket Communication**: Efficient real-time communication with frontends
- **Chat Interface**: Interactive chat with MoE models
- **Remote Operation**: Can run on different machines from the main web UI
- **Binding Support**: Can connect to external services like the robot UI
- **Model Management**: Dynamic model loading and configuration
- **Performance Monitoring**: Health checks and status monitoring

## Architecture

The MoE backend consists of several key components:

### Core Components

1. **MoEInferenceEngine**: Handles model loading and streaming inference
2. **MoEBackendServer**: Main server with WebSocket and HTTP endpoints
3. **MoEBackendClient**: Client library for connecting to the backend
4. **MoEStreamingChat**: High-level interface for chat applications

### Data Flow

```
User Input → WebSocket → Inference Engine → Token-by-Token Generation
                                        ↓
Expert Router Analysis ← Model Forward Pass ← Current Context
            ↓
WebSocket Stream ← Expert Selection Data + Token Data
            ↓
Frontend Visualization
```

## Installation

The MoE backend is part of the robot arm project. Install dependencies using `uv`:

```bash
cd robot_arm
uv sync
```

This will install all required dependencies including:
- PyTorch for model inference
- Transformers for MoE model support
- WebSockets for real-time communication
- Flask for HTTP endpoints
- The llm_sidechannel library for expert analysis

## Usage

### Starting the Backend Server

Start the MoE backend server:

```bash
# Basic usage (default: localhost:8765)
uv run start-moe-backend

# Custom host and port
uv run start-moe-backend --host 0.0.0.0 --port 9000

# Bind to external service (e.g., robot UI)
uv run start-moe-backend --bind localhost:5000

# Specify custom model
uv run start-moe-backend --model mistralai/Mixtral-8x7B-Instruct-v0.1 --preset performance
```

### Command Line Interface

Use the CLI tool for testing and interaction:

```bash
# Interactive chat
uv run moe-cli chat

# Health check
uv run moe-cli health

# Send single message
uv run moe-cli send "Explain how MoE models work"

# Custom backend location
uv run moe-cli --host remote-server --port 8765 chat
```

### Python Client

Use the Python client library to integrate with other applications:

```python
import asyncio
from moe_backend.client import MoEBackendClient, MoEConnectionConfig, MoEStreamingChat

async def example_usage():
    # Configure connection
    config = MoEConnectionConfig(host="localhost", port=8765)
    client = MoEBackendClient(config)
    
    # Create chat interface
    class MyChat(MoEStreamingChat):
        async def _on_token_received(self, token_data):
            print(token_data['token_text'], end='', flush=True)
            
        async def _on_generation_complete(self, completion_data):
            print(f"\nDone! {completion_data['total_tokens']} tokens")
    
    chat = MyChat(client)
    
    # Connect and chat
    await client.connect()
    await chat.load_model()
    await chat.start_chat("Hello, explain mixture of experts!")
    
    # Keep alive until done
    while client.is_connected:
        await asyncio.sleep(0.1)

asyncio.run(example_usage())
```

## Configuration

### Environment Variables

Configure the backend using environment variables:

```bash
export MOE_HOST=localhost
export MOE_PORT=8765
export MOE_MODEL_NAME=mistralai/Mixtral-8x7B-Instruct-v0.1
export MOE_MODEL_PRESET=balanced
export MOE_DEVICE=cuda:0
export MOE_MAX_NEW_TOKENS=512
export MOE_TEMPERATURE=0.7
export MOE_ENABLE_EXPERT_ANALYSIS=true
```

### Model Presets

Available model loading presets:

- **balanced**: Balanced performance and memory usage
- **performance**: Maximum performance (full precision)
- **memory**: Memory optimized (quantization enabled)
- **cpu**: CPU-only execution

## API Endpoints

### HTTP Endpoints

- `GET /health` - Server health status
- `GET /model/info` - Model information
- `GET /conversations` - List conversations
- `GET /conversations/<id>` - Get specific conversation

### WebSocket Endpoints

- `WS /ws` - Real-time streaming communication

### WebSocket Message Types

#### Client → Server

```json
{
  "type": "chat",
  "data": {
    "prompt": "Your message here",
    "conversation_id": "conv_123",
    "generation_params": {
      "max_new_tokens": 100,
      "temperature": 0.7,
      "top_p": 0.9
    }
  }
}
```

```json
{
  "type": "load_model"
}
```

#### Server → Client

**Token Stream:**
```json
{
  "type": "stream",
  "data": {
    "type": "token",
    "data": {
      "token_id": 12345,
      "token_text": " hello",
      "position": 0,
      "timestamp": 1699123456.789,
      "router_data": {
        "layer_count": 32,
        "expert_selections": [
          {
            "layer_idx": 0,
            "token_position": 0,
            "expert_weights": [0.1, 0.9, 0.0, ...],
            "selected_experts": [1, 3],
            "router_logits": [-2.3, 1.8, -4.1, ...],
            "timestamp": 1699123456.789
          }
        ]
      }
    }
  }
}
```

**Generation Complete:**
```json
{
  "type": "stream",
  "data": {
    "type": "complete",
    "data": {
      "conversation_id": "conv_123",
      "message_id": "msg_456",
      "total_tokens": 42,
      "total_expert_selections": 1344
    }
  }
}
```

## Expert Selection Data

Each token generates expert selection data for every MoE layer in the model:

- **Router Logits**: Raw logits from the router network before softmax
- **Expert Weights**: Softmax probabilities for each expert
- **Selected Experts**: Indices of the top-k experts chosen for this token
- **Layer Information**: Which transformer layer this data comes from
- **Timing**: Precise timestamps for performance analysis

This data enables real-time visualization of:
- Which experts are being activated
- How expert usage changes over time
- Load balancing across experts
- Expert specialization patterns

## Performance Considerations

### Memory Usage

- Model loading can require 13-16GB GPU memory for Mixtral-8x7B
- Use quantization presets to reduce memory usage
- Consider 4-bit quantization for lower-end hardware

### Network Bandwidth

- Token streaming: ~1-10 KB/s depending on generation speed
- Expert data: ~50-200 KB/s for detailed router information
- Use `detailed_expert_data=false` to reduce bandwidth

### Latency

- Local inference: 50-200ms per token
- Network overhead: 1-10ms additional latency
- WebSocket provides minimal additional overhead

## Integration with Robot UI

The MoE backend can be bound to the existing robot UI server:

```bash
# Start robot UI on port 5000
uv run start-robot-ui

# Start MoE backend and bind to robot UI
uv run start-moe-backend --bind localhost:5000
```

This enables:
- Unified logging and monitoring
- Shared authentication (if implemented)
- Cross-service communication
- Centralized health monitoring

## Troubleshooting

### Common Issues

**Model Loading Fails:**
```bash
# Check GPU memory
nvidia-smi

# Try CPU mode
uv run start-moe-backend --device cpu

# Use quantization
uv run start-moe-backend --preset memory
```

**Connection Issues:**
```bash
# Check server status
uv run moe-cli health

# Check firewall settings
telnet localhost 8765

# Check logs
uv run start-moe-backend --host 0.0.0.0 --port 8765
```

**Performance Issues:**
```bash
# Monitor resource usage
htop
nvidia-smi

# Reduce generation parameters
uv run moe-cli send "test" --max-new-tokens 10
```

### Logging

The backend provides detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Log levels:
- DEBUG: Detailed token and expert information
- INFO: Server status and major events
- WARNING: Performance issues and recoverable errors
- ERROR: Critical failures

## Development

### Adding New Features

1. **New Message Types**: Add handlers in `server.py` and `client.py`
2. **Expert Analysis**: Extend `MoEInferenceEngine` with new analysis
3. **Model Support**: Add new model configurations in `config.py`
4. **Endpoints**: Add HTTP endpoints in `_setup_routes()`

### Testing

```bash
# Start server in one terminal
uv run start-moe-backend

# Test with CLI in another
uv run moe-cli health
uv run moe-cli send "test message"
```

### Contributing

Follow the existing code style and add appropriate logging. All new features should include:
- Comprehensive error handling
- WebSocket message documentation
- Client library support
- CLI command integration

## License

Part of the robot arm project. See main project license. 