from __future__ import annotations

from collections.abc import Callable

from core.health_catalog import expected_temp_range
from core.health_types import DailyHealthInput


def apply_temperature_rules(
    entry: DailyHealthInput,
    add_score: Callable[[str, float, str], None],
) -> None:
    expected_min, expected_max = expected_temp_range(entry.day_num)
    if entry.temp_max_c <= 0 and entry.temp_min_c <= 0:
        return

    if entry.temp_max_c > expected_max + 2:
        add_score(
            "heat_stress",
            24.0,
            f"Max temperature {entry.temp_max_c:.1f}C is above expected range for day {entry.day_num}.",
        )
    elif entry.temp_max_c > expected_max:
        add_score(
            "heat_stress",
            14.0,
            f"Max temperature is slightly above expected range ({expected_max:.1f}C).",
        )

    if entry.temp_min_c < expected_min - 2:
        add_score(
            "cold_stress",
            24.0,
            f"Min temperature {entry.temp_min_c:.1f}C is below expected range for day {entry.day_num}.",
        )
    elif 0 < entry.temp_min_c < expected_min:
        add_score(
            "cold_stress",
            14.0,
            f"Min temperature is slightly below expected range ({expected_min:.1f}C).",
        )

    spread = entry.temp_max_c - entry.temp_min_c
    if spread > 8:
        add_score("heat_stress", 8.0, f"Large temperature spread observed ({spread:.1f}C).")
        add_score("cold_stress", 8.0, "Daily temperature spread can stress birds.")
