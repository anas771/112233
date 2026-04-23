from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TempBand:
    day_min: int
    day_max: int
    min_c: float
    max_c: float


TEMP_BANDS: tuple[TempBand, ...] = (
    TempBand(1, 7, 30.0, 34.0),
    TempBand(8, 14, 28.0, 31.0),
    TempBand(15, 21, 26.0, 29.0),
    TempBand(22, 28, 24.0, 27.0),
    TempBand(29, 1000, 21.0, 25.0),
)

CONDITION_LABELS: dict[str, str] = {
    "heat_stress": "Heat stress pattern",
    "cold_stress": "Cold stress pattern",
    "respiratory_complex": "Respiratory disease pattern",
    "coccidiosis": "Coccidiosis-like pattern",
    "enteric_disorder": "Enteric disorder pattern",
    "possible_bacterial_issue": "Possible bacterial issue",
    "treatment_complexity": "Treatment complexity warning",
    "supportive_only": "Supportive treatment only",
    "dehydration_risk": "Dehydration risk",
}


def expected_temp_range(day_num: int) -> tuple[float, float]:
    for band in TEMP_BANDS:
        if band.day_min <= day_num <= band.day_max:
            return band.min_c, band.max_c
    return 21.0, 25.0
