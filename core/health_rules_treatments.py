from __future__ import annotations

from collections.abc import Callable

from core.health_types import DailyHealthInput


def apply_treatment_rules(
    entry: DailyHealthInput,
    add_score: Callable[[str, float, str], None],
) -> None:
    if not entry.treatments:
        return

    classes = [t.treatment_class.strip().lower() for t in entry.treatments if t.treatment_class]
    ingredients = [
        (t.active_ingredient or t.product_name or "").strip().lower()
        for t in entry.treatments
    ]
    antibiotic_count = sum(1 for c in classes if c == "antibiotic")
    anticoccidial_count = sum(1 for c in classes if c == "anticoccidial")
    respiratory_count = sum(1 for c in classes if c == "respiratory_support")
    supportive_count = sum(1 for c in classes if c in {"vitamin_electrolyte", "supportive", "immune_support", "liver_support", "probiotic"})

    if anticoccidial_count:
        add_score("coccidiosis", 18.0 + (anticoccidial_count * 3.0), "Anticoccidial treatment recorded.")
    if respiratory_count:
        add_score("respiratory_complex", 14.0 + (respiratory_count * 2.0), "Respiratory support treatment recorded.")
    if antibiotic_count:
        add_score("possible_bacterial_issue", 10.0 + (antibiotic_count * 3.0), "Antibiotic treatment recorded.")

    if antibiotic_count >= 2:
        add_score("treatment_complexity", 22.0, "Multiple antibiotics were used on the same day.")
    if len(classes) >= 4:
        add_score("treatment_complexity", 14.0, "Many treatments were used on the same day.")
    if supportive_count == len(classes):
        add_score("supportive_only", 18.0, "Only supportive treatments are recorded.")

    joined = " ".join(ingredients)
    if any(k in joined for k in ("amprolium", "toltrazuril", "diclazuril", "sulfaquinoxaline", "sulfachloropyrazine")):
        add_score("coccidiosis", 15.0, "Active ingredients include common anticoccidial molecules.")
    if any(k in joined for k in ("tylosin", "tilmicosin", "spiramycin", "lincomycin")):
        add_score("respiratory_complex", 14.0, "Active ingredients are commonly used in respiratory/mycoplasma patterns.")
    if any(k in joined for k in ("colistin", "neomycin", "amoxicillin", "trimethoprim", "sulfamethoxazole")):
        add_score("enteric_disorder", 12.0, "Active ingredients suggest enteric bacterial targeting.")
    if any(k in joined for k in ("vitamin c", "ascorbic", "electrolyte", "betaine")):
        add_score("heat_stress", 8.0, "Supportive ingredients match heat/dehydration stress management.")
