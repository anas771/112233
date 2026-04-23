from __future__ import annotations

from collections.abc import Callable

from core.health_types import DailyHealthInput


def apply_combined_rules(
    entry: DailyHealthInput,
    history: list[dict[str, float]],
    add_score: Callable[[str, float, str], None],
) -> None:
    signs = f"{entry.clinical_signs_text} {entry.notes}".lower()
    treatment_classes = {t.treatment_class.strip().lower() for t in entry.treatments if t.treatment_class}
    ingredient_text = " ".join((t.active_ingredient or t.product_name or "").lower() for t in entry.treatments)

    if "cough" in signs or "sneez" in signs or "resp" in signs:
        add_score("respiratory_complex", 16.0, "Respiratory signs were reported in notes.")
    if "diarr" in signs or "bloody" in signs or "enter" in signs:
        add_score("enteric_disorder", 16.0, "Enteric signs were reported in notes.")

    if "anticoccidial" in treatment_classes and entry.day_num >= 10 and entry.dead_count >= 5:
        add_score("coccidiosis", 20.0, "Age, mortality, and anticoccidial treatment pattern match coccidiosis risk.")

    if "antibiotic" in treatment_classes and ("resp" in signs or "cough" in signs):
        add_score("respiratory_complex", 18.0, "Respiratory signs plus antibiotic treatment suggest respiratory complex.")
    if any(k in ingredient_text for k in ("amprolium", "toltrazuril", "diclazuril")) and ("diarr" in signs or "bloody" in signs):
        add_score("coccidiosis", 18.0, "Clinical signs plus anticoccidial ingredient pattern increase coccidiosis risk.")
    if any(k in ingredient_text for k in ("tylosin", "tilmicosin", "lincomycin")) and ("cough" in signs or "sneez" in signs):
        add_score("respiratory_complex", 16.0, "Respiratory signs with respiratory-oriented ingredients increase risk signal.")

    if entry.temp_max_c >= 34 and entry.water_ltr > 0 and entry.feed_kg > 0 and entry.water_ltr > (entry.feed_kg * 2.5):
        add_score("heat_stress", 20.0, "High temperature with elevated water/feed ratio suggests heat stress.")

    if entry.temp_min_c > 0 and entry.temp_max_c > 0 and entry.temp_min_c < 20 and entry.day_num <= 14:
        add_score("cold_stress", 16.0, "Low minimum temperature during brooding period is high-risk.")

    if history:
        prev_dead = int(history[0].get("dead_count", 0) + history[0].get("culls_count", 0))
        if prev_dead > 0 and (entry.dead_count + entry.culls_count) >= prev_dead * 2:
            add_score("possible_bacterial_issue", 14.0, "Losses doubled versus previous day.")
            add_score("dehydration_risk", 10.0, "Sharp daily deterioration increases upcoming risk.")
