# Minimal local re-implementation of llm_sidechannel focusing on Mixtral usage

from importlib import metadata

try:
    __version__ = metadata.version("llm-sidechannel")
except metadata.PackageNotFoundError:
    __version__ = "0.1.0-local"

from .core.mixtral_client import MixtralClient
from .core.config import MixtralConfig, load_model_config
from .core.router_analyzer import RouterAnalyzer
from .analysis.expert_usage import ExpertUsageAnalyzer

__all__ = [
    "__version__",
    "MixtralClient",
    "MixtralConfig",
    "load_model_config",
    "RouterAnalyzer",
    "ExpertUsageAnalyzer",
] 