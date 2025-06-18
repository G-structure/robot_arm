"""
Configuration module for MoE Backend Server.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
import os

@dataclass
class MoEBackendConfig:
    """Configuration for MoE Backend Server."""
    
    # Server configuration
    host: str = "localhost"
    port: int = 8765
    bind_to: Optional[str] = None
    
    # Model configuration
    model_name: str = "mistralai/Mixtral-8x7B-Instruct-v0.1"
    model_preset: str = "balanced"
    device: Optional[str] = None
    
    # Streaming configuration
    max_new_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: Optional[int] = None
    
    # Performance configuration
    generation_timeout: int = 30
    max_concurrent_generations: int = 4
    
    # Expert analysis configuration
    enable_expert_analysis: bool = True
    stream_router_logits: bool = True
    detailed_expert_data: bool = True
    
    @classmethod
    def from_env(cls) -> 'MoEBackendConfig':
        """Create configuration from environment variables."""
        return cls(
            host=os.getenv('MOE_HOST', 'localhost'),
            port=int(os.getenv('MOE_PORT', '8765')),
            bind_to=os.getenv('MOE_BIND_TO'),
            model_name=os.getenv('MOE_MODEL_NAME', 'mistralai/Mixtral-8x7B-Instruct-v0.1'),
            model_preset=os.getenv('MOE_MODEL_PRESET', 'balanced'),
            device=os.getenv('MOE_DEVICE'),
            max_new_tokens=int(os.getenv('MOE_MAX_NEW_TOKENS', '512')),
            temperature=float(os.getenv('MOE_TEMPERATURE', '0.7')),
            top_p=float(os.getenv('MOE_TOP_P', '0.9')),
            generation_timeout=int(os.getenv('MOE_GENERATION_TIMEOUT', '30')),
            max_concurrent_generations=int(os.getenv('MOE_MAX_CONCURRENT', '4')),
            enable_expert_analysis=os.getenv('MOE_ENABLE_EXPERT_ANALYSIS', 'true').lower() == 'true',
            stream_router_logits=os.getenv('MOE_STREAM_ROUTER_LOGITS', 'true').lower() == 'true',
            detailed_expert_data=os.getenv('MOE_DETAILED_EXPERT_DATA', 'true').lower() == 'true'
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'host': self.host,
            'port': self.port,
            'bind_to': self.bind_to,
            'model_name': self.model_name,
            'model_preset': self.model_preset,
            'device': self.device,
            'max_new_tokens': self.max_new_tokens,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'top_k': self.top_k,
            'generation_timeout': self.generation_timeout,
            'max_concurrent_generations': self.max_concurrent_generations,
            'enable_expert_analysis': self.enable_expert_analysis,
            'stream_router_logits': self.stream_router_logits,
            'detailed_expert_data': self.detailed_expert_data
        } 