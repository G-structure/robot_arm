from __future__ import annotations

"""Simplified Mixtral client for local llm_sidechannel re-implementation.

Only implements the functionality required by the MoE backend:
  • Model & tokenizer loading via 🤗 Transformers
  • Text generation with router logits enabled
  • Basic router logit analysis (top-k experts & per-expert counts)
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple
import logging
import math

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig

from .config import MixtralConfig

logger = logging.getLogger(__name__)

__all__ = [
    "MixtralResponse",
    "MixtralClient",
]


@dataclass
class MixtralResponse:
    """Container for a single generation response."""
    text: str
    tokens: List[int]
    router_logits: Optional[List[torch.Tensor]] = None
    router_selections: Optional[List[Dict[str, Any]]] = None
    expert_usage: Optional[Dict[int, int]] = None


class MixtralClient:
    """High-level client for Mixtral MoE models.

    The implementation purposefully avoids any heavyweight dependencies beyond
    HuggingFace Transformers + PyTorch.
    """

    # How many experts to consider "selected" per token
    _EXPERTS_PER_TOKEN_DEFAULT: int = 2

    def __init__(self, **kwargs):
        cfg = MixtralConfig(**kwargs) if not isinstance(kwargs, MixtralConfig) else kwargs
        self.config: MixtralConfig = cfg

        self.device: str = cfg.resolved_device()
        self.torch_dtype = cfg.torch_dtype or (torch.float16 if self.device != "cpu" else torch.float32)

        logger.info("[MixtralClient] Loading model '%s' on %s", cfg.model_name, self.device)

        # --- Tokenizer ---
        self.tokenizer = AutoTokenizer.from_pretrained(cfg.model_name)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # --- Model Config with router logits enabled ---
        hf_cfg = AutoConfig.from_pretrained(cfg.model_name)
        hf_cfg.output_router_logits = True

        model_kwargs: Dict[str, Any] = {
            "torch_dtype": self.torch_dtype,
            "device_map": cfg.device_map,
            "trust_remote_code": True,
        }
        if cfg.load_in_8bit:
            model_kwargs["load_in_8bit"] = True
        if cfg.load_in_4bit:
            model_kwargs["load_in_4bit"] = True

        self.model = AutoModelForCausalLM.from_pretrained(cfg.model_name, config=hf_cfg, **model_kwargs)
        self.model.eval()

        # Expert metadata (defaults if not present)
        self.num_experts: int = getattr(self.model.config, "num_local_experts", 8)
        self.experts_per_token: int = getattr(self.model.config, "num_experts_per_tok", self._EXPERTS_PER_TOKEN_DEFAULT)

        logger.info("[MixtralClient] Experts: %d (per-token: %d)", self.num_experts, self.experts_per_token)

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    @torch.inference_mode()
    def generate(
        self,
        prompt: str,
        max_new_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        do_sample: bool = True,
        analyze_routing: bool = True,
    ) -> MixtralResponse:
        """Generate text with router logits (if enabled)."""
        max_new_tokens = max_new_tokens or self.config.max_new_tokens
        temperature = temperature if temperature is not None else self.config.temperature
        top_p = top_p if top_p is not None else self.config.top_p
        top_k = top_k if top_k is not None else self.config.top_k

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        gen_kwargs: Dict[str, Any] = {
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "do_sample": do_sample,
            "pad_token_id": self.tokenizer.eos_token_id,
            "output_router_logits": analyze_routing,
            "return_dict_in_generate": True,
        }
        if top_k is not None:
            gen_kwargs["top_k"] = top_k

        outputs = self.model.generate(**inputs, **gen_kwargs)

        # Sequence post-processing
        full_tokens = outputs.sequences[0].tolist()
        generated_tokens = full_tokens[len(inputs.input_ids[0]):]
        text = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)

        router_logits = outputs.router_logits if analyze_routing and hasattr(outputs, "router_logits") else None
        selections, usage = self._analyze_routing(router_logits) if router_logits is not None else (None, None)

        return MixtralResponse(
            text=text,
            tokens=generated_tokens,
            router_logits=router_logits,
            router_selections=selections,
            expert_usage=usage,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _analyze_routing(
        self, router_logits: List[torch.Tensor]
    ) -> Tuple[List[Dict[str, Any]], Dict[int, int]]:
        """Turn raw router logits into human-readable expert selections.

        Returns
        -------
        selections : list
            Per-layer selection dictionaries (top experts + probs).
        usage : dict[int, int]
            Counts of how many times each expert was selected across all layers/tokens.
        """
        selections: List[Dict[str, Any]] = []
        usage: Dict[int, int] = {i: 0 for i in range(self.num_experts)}

        for layer_idx, layer_logits in enumerate(router_logits):
            # layer_logits: [batch, seq_len, num_experts]
            probs = torch.softmax(layer_logits, dim=-1)
            top_vals, top_idx = torch.topk(probs, k=self.experts_per_token, dim=-1)  # [b, seq, k]

            bsz, seq_len, _ = top_idx.shape
            for t in range(seq_len):
                token_selected_experts = top_idx[0, t].tolist()
                token_weights = top_vals[0, t].tolist()
                for ex in token_selected_experts:
                    usage[ex] += 1
                selections.append({
                    "layer_idx": layer_idx,
                    "token_position": t,
                    "selected_experts": token_selected_experts,
                    "expert_probs": token_weights,
                })

        return selections, usage 