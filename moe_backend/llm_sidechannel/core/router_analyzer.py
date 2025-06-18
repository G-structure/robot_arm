"""Very lightweight RouterAnalyzer for the local llm_sidechannel implementation."""

from __future__ import annotations

from typing import List, Dict, Any, Optional

__all__ = ["RouterAnalyzer"]

class RouterAnalyzer:
    """Analyse per-token expert selections and provide simple summaries."""

    def __init__(self, num_experts: int = 8, experts_per_token: int = 2):
        self.num_experts = num_experts
        self.experts_per_token = experts_per_token
        self.tokenizer = None

    # Tokenizer is used for optional pretty-printing
    def set_tokenizer(self, tokenizer):
        self.tokenizer = tokenizer

    def analyze_routing_decisions(
        self,
        routing_decisions: List[Dict[str, Any]],
        tokens: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """Return simple statistics over a list of routing_decision dicts."""
        usage = {i: 0 for i in range(self.num_experts)}
        for entry in routing_decisions:
            for ex in entry.get("selected_experts", []):
                usage[ex] += 1

        total = sum(usage.values()) + 1e-9
        percentages = {k: v / total for k, v in usage.items()}

        return {
            "total_tokens": len(tokens) if tokens is not None else None,
            "usage_counts": usage,
            "usage_percentages": percentages,
        }

    # Convenience
    def get_expert_usage_summary(self, analysis_results: Dict[str, Any]) -> str:
        top = sorted(analysis_results["usage_counts"].items(), key=lambda x: x[1], reverse=True)[:5]
        return "Expert usage (top): " + ", ".join(f"E{idx}:{cnt}" for idx, cnt in top) 