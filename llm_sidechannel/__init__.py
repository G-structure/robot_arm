"""Top-level shim to expose `llm_sidechannel` from within `moe_backend`.

This avoids having to change import paths in existing code (e.g. `from llm_sidechannel.core...`).
"""

from importlib import import_module as _import_module
import sys as _sys

# Import the real implementation located under moe_backend.llm_sidechannel
_real_pkg = _import_module("moe_backend.llm_sidechannel")

# Re-export everything at the top-level
_sys.modules[__name__] = _real_pkg
for _k in getattr(_real_pkg, "__all__", []):
    globals()[_k] = getattr(_real_pkg, _k)

# Also propagate submodules so `import llm_sidechannel.core` works
for _subname, _module in _sys.modules.items():
    if _subname.startswith("moe_backend.llm_sidechannel"):
        # Compute new public name
        _public = _subname.replace("moe_backend.llm_sidechannel", "llm_sidechannel", 1)
        _sys.modules[_public] = _module 