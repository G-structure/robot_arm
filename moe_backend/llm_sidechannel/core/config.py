from __future__ import annotations

"""Configuration helpers for Mixtral and MoE models used by the local llm_sidechannel re-implementation."""

from dataclasses import dataclass
from typing import Optional, Union, Dict
import torch

__all__ = [
    "MixtralConfig",
    "load_model_config",
]


def _detect_device() -> str:
    """Return a sensible default device (cuda if available, else cpu)."""
    return "cuda" if torch.cuda.is_available() else "cpu"


@dataclass
class MixtralConfig:
    """Configuration for loading a Mixtral (or other MoE) model."""

    # HuggingFace model identifier
    model_name: str = "mistralai/Mixtral-8x7B-Instruct-v0.1"

    # Device to load the model on (e.g. "cuda", "cpu", "cuda:0")
    device: Optional[str] = None

    # Data type for model weights
    torch_dtype: Optional[torch.dtype] = torch.float16

    # Quantisation flags (require bitsandbytes + CUDA)
    load_in_8bit: bool = False
    load_in_4bit: bool = False

    # Device map passed to transformers ("auto" is usually fine)
    device_map: Optional[Union[str, Dict]] = "auto"

    # Generation defaults
    max_new_tokens: int = 256
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: Optional[int] = None

    # Router logits flag – must be True for expert analysis
    output_router_logits: bool = True

    def resolved_device(self) -> str:
        return self.device or _detect_device()


_PRESET_TABLE: Dict[str, Dict] = {
    # A rough balance between memory and performance (16-bit on GPU if available)
    "balanced": {
        "torch_dtype": torch.float16,
        "load_in_8bit": False,
        "load_in_4bit": False,
    },
    # Full-precision for maximum quality/performance (needs lots of VRAM)
    "performance": {
        "torch_dtype": torch.float16,
        "load_in_8bit": False,
        "load_in_4bit": False,
    },
    # Memory-optimised using 4-bit quantisation
    "memory": {
        "torch_dtype": torch.float16,
        "load_in_8bit": False,
        "load_in_4bit": True,
    },
    # CPU-only inference (slow!)
    "cpu": {
        "device": "cpu",
        "torch_dtype": torch.float32,
        "load_in_8bit": False,
        "load_in_4bit": False,
        "device_map": None,
    },
}


def load_model_config(preset: Optional[str] = None, **overrides) -> MixtralConfig:
    """Return a MixtralConfig from a named preset, applying any overrides."""

    base_kwargs: Dict = {}
    if preset is not None and preset in _PRESET_TABLE:
        base_kwargs.update(_PRESET_TABLE[preset])

    # Apply overrides last
    base_kwargs.update(overrides)

    # Ensure device is set
    if "device" not in base_kwargs or base_kwargs["device"] is None:
        base_kwargs["device"] = _detect_device()

    return MixtralConfig(**base_kwargs) 