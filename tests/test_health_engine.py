import unittest

from core.health_engine import analyze_daily_health
from core.health_types import DailyHealthInput, DailyTreatment


class HealthEngineRulesTest(unittest.TestCase):
    def test_heat_stress_signal_from_temperature(self) -> None:
        entry = DailyHealthInput(
            batch_id=1,
            rec_date="2026-04-22",
            day_num=18,
            dead_count=2,
            culls_count=0,
            feed_kg=120.0,
            water_ltr=380.0,
            temp_min_c=29.0,
            temp_max_c=35.5,
            clinical_signs_text="panting",
        )
        result = analyze_daily_health(entry, history=[{"dead_count": 1, "culls_count": 0}])
        self.assertTrue(any(hit.code == "heat_stress" for hit in result.top_conditions))
        self.assertGreater(result.risk_score, 0)

    def test_coccidiosis_signal_with_treatment_and_mortality(self) -> None:
        entry = DailyHealthInput(
            batch_id=1,
            rec_date="2026-04-22",
            day_num=16,
            dead_count=8,
            culls_count=1,
            feed_kg=98.0,
            water_ltr=180.0,
            temp_min_c=25.0,
            temp_max_c=30.0,
            clinical_signs_text="bloody diarrhea",
            treatments=[
                DailyTreatment(
                    product_name="Toltrazuril",
                    active_ingredient="toltrazuril",
                    treatment_class="anticoccidial",
                    dose_text="1ml/L",
                )
            ],
        )
        result = analyze_daily_health(
            entry,
            history=[
                {"dead_count": 4, "culls_count": 0},
                {"dead_count": 3, "culls_count": 0},
            ],
        )
        top_codes = [hit.code for hit in result.top_conditions]
        self.assertIn("coccidiosis", top_codes)


if __name__ == "__main__":
    unittest.main()
