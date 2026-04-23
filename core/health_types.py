from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class DailyTreatment:
    product_name: str
    active_ingredient: str
    treatment_class: str
    dose_text: str = ""
    notes: str = ""


@dataclass(slots=True)
class DailyHealthInput:
    batch_id: int
    rec_date: str
    day_num: int
    dead_count: int
    culls_count: int
    feed_kg: float
    water_ltr: float
    temp_min_c: float
    temp_max_c: float
    humidity_min_pct: float = 0.0
    humidity_max_pct: float = 0.0
    clinical_signs_text: str = ""
    notes: str = ""
    treatments: list[DailyTreatment] = field(default_factory=list)


@dataclass(slots=True)
class RuleHit:
    code: str
    score: float
    reason: str


@dataclass(slots=True)
class HealthAnalysisResult:
    status: str
    risk_score: float
    top_conditions: list[RuleHit]
    future_risk_level: str
    summary: str
