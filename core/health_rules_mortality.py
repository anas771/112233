from __future__ import annotations

from collections.abc import Callable

from core.health_types import DailyHealthInput


def apply_mortality_rules(
    entry: DailyHealthInput,
    history: list[dict[str, float]],
    add_score: Callable[[str, float, str], None],
) -> None:
    today_total = entry.dead_count + entry.culls_count
    if today_total <= 0:
        return

    if today_total >= 10:
        add_score("possible_bacterial_issue", 16.0, f"High daily loss observed ({today_total}).")
    if today_total >= 20:
        add_score("possible_bacterial_issue", 12.0, "Losses crossed a critical daily threshold.")

    if not history:
        return

    last_values = [int(row.get("dead_count", 0) + row.get("culls_count", 0)) for row in history]
    avg_recent = (sum(last_values) / len(last_values)) if last_values else 0
    if avg_recent > 0 and today_total >= avg_recent * 1.5:
        add_score(
            "possible_bacterial_issue",
            18.0,
            f"Daily losses increased sharply compared to recent average ({avg_recent:.1f}).",
        )

    if len(last_values) >= 2:
        if today_total > last_values[0] > last_values[1]:
            add_score("possible_bacterial_issue", 16.0, "Losses are increasing for three consecutive days.")
            add_score("dehydration_risk", 8.0, "Rising loss trend can indicate worsening conditions.")

    if entry.day_num <= 10 and today_total >= 6:
        add_score("cold_stress", 10.0, "Early-age losses suggest brooding/environment instability.")
