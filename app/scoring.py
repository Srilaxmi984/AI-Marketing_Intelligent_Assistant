"""Overall SEO scoring calculation and weight renormalization module."""

from typing import Dict, List, Tuple
from app.config import settings
from app.schemas import MetricResult, OverallScore


def calculate_overall_score(metrics: List[MetricResult]) -> OverallScore:
    """
    Calculate overall weighted SEO score.
    If any metric is not applicable (e.g. broken_links with 0 checked links),
    it is excluded and the remaining weights are renormalised proportionally.
    """
    # 1. Filter applicable metrics
    applicable: List[Tuple[MetricResult, float]] = []
    excluded_ids = set()

    for m in metrics:
        # Broken links with 0 total links checked is not applicable
        if m.id == "broken_links" and m.total == 0:
            # DECISION: When zero links are checked, broken_links is excluded and remaining metric weights are renormalised to avoid skewing the score.
            excluded_ids.add(m.id)
            continue
        weight = settings.metric_weights.get(m.id, 0.0)
        applicable.append((m, weight))

    if not applicable:
        return OverallScore(score=0.0, weights={}, formula="No applicable metrics.")

    # 2. Renormalize weights
    weight_sum = sum(w for _, w in applicable)
    renormalized_weights: Dict[str, float] = {}
    for m, w in applicable:
        renormalized_weights[m.id] = round(w / weight_sum, 4)

    # 3. Compute weighted score
    terms = []
    total_score = 0.0
    for m, _ in applicable:
        norm_w = renormalized_weights[m.id]
        contribution = m.score * norm_w
        total_score += contribution
        pct = round(norm_w * 100, 1)
        terms.append(f"{m.id} ({pct}% * {m.score})")

    final_score = round(total_score, 1)
    # Clamp between 0.0 and 100.0
    final_score = max(0.0, min(100.0, final_score))
    formula = " + ".join(terms) + f" = {final_score}"

    return OverallScore(
        score=final_score,
        weights=renormalized_weights,
        formula=formula,
    )
