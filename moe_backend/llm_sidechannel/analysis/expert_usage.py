"""Very small ExpertUsageAnalyzer for demo purposes."""

from __future__ import annotations

from typing import Dict, List, Any
import math

__all__ = ["ExpertUsageAnalyzer"]

class ExpertUsageAnalyzer:
    """Compute simple statistics about expert usage counts."""

    def __init__(self, num_experts: int = 8):
        self.num_experts = num_experts

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def analyze_expert_distribution(self, expert_usage: Dict[int, int]) -> Dict[str, Any]:
        counts = [expert_usage.get(i, 0) for i in range(self.num_experts)]
        total = sum(counts) + 1e-9  # avoid div0
        percentages = [c / total for c in counts]

        entropy = self._entropy(percentages)
        gini = self._gini(counts)
        load_balance = self._load_balance(counts)

        return {
            "entropy": entropy,
            "gini": gini,
            "load_balance_score": load_balance,
            "total": total,
            "counts": counts,
            "percentages": percentages,
        }

    # ------------------------------------------------------------------
    # Private maths helpers
    # ------------------------------------------------------------------

    def _entropy(self, probs: List[float]) -> float:
        return -(sum(p * math.log(p + 1e-12) for p in probs))

    def _gini(self, counts: List[int]) -> float:
        n = len(counts)
        if n == 0:
            return 0.0
        mean = sum(counts) / n + 1e-9
        return sum(abs(ci - cj) for ci in counts for cj in counts) / (2 * n * sum(counts))

    def _load_balance(self, counts: List[int]) -> float:
        if not counts:
            return 0.0
        ideal = sum(counts) / len(counts) + 1e-9
        return min(c / ideal for c in counts) 