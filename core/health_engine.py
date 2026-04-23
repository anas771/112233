from __future__ import annotations

from collections import defaultdict

from core.health_catalog import CONDITION_LABELS
from core.health_rules_combined import apply_combined_rules
from core.health_rules_mortality import apply_mortality_rules
from core.health_rules_temperature import apply_temperature_rules
from core.health_rules_treatments import apply_treatment_rules
from core.health_types import DailyHealthInput, HealthAnalysisResult, RuleHit


def _risk_level(score: float) -> tuple[str, str]:
    if score >= 75:
        return "critical", "high"
    if score >= 45:
        return "warning", "medium"
    if score >= 20:
        return "watch", "low"
    return "stable", "low"


def analyze_daily_health(
    entry: DailyHealthInput,
    history: list[dict[str, float]] | None = None,
) -> HealthAnalysisResult:
    history = history or []
    scores: dict[str, float] = defaultdict(float)
    reasons: dict[str, list[str]] = defaultdict(list)

    def add_score(code: str, score: float, reason: str) -> None:
        scores[code] += score
        reasons[code].append(reason)

    apply_temperature_rules(entry, add_score)
    apply_mortality_rules(entry, history, add_score)
    apply_treatment_rules(entry, add_score)
    apply_combined_rules(entry, history, add_score)

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    top_hits: list[RuleHit] = []
    for code, score in ranked[:3]:
        reason_text = reasons[code][0] if reasons[code] else "Rule-based health signal."
        top_hits.append(RuleHit(code=code, score=round(score, 1), reason=reason_text))

    risk_score = round(sum(score for _, score in ranked[:3]), 1)
    status, future_risk_level = _risk_level(risk_score)
    if top_hits:
        top_label = CONDITION_LABELS.get(top_hits[0].code, top_hits[0].code)
        summary = f"{top_label} is the strongest signal today (risk score {risk_score:.1f})."
    else:
        summary = "No strong rule-based disease signal was detected today."

    return HealthAnalysisResult(
        status=status,
        risk_score=risk_score,
        top_conditions=top_hits,
        future_risk_level=future_risk_level,
        summary=summary,
    )
