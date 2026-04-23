import unittest
from pathlib import Path
from uuid import uuid4

import core.database as core_db
import web.app as web_app


class WarehousesExportTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(__file__).resolve().parent / ".tmp"
        self.temp_dir.mkdir(exist_ok=True)
        self.db_path = self.temp_dir / f"test_poultry_{uuid4().hex}.db"
        core_db.ensure_schema(self.db_path)

        def test_get_conn():
            return core_db.get_conn(self.db_path)

        self.original_get_conn = web_app.get_conn
        self.original_ensure_schema = web_app.shared_ensure_schema
        web_app.get_conn = test_get_conn
        web_app.shared_ensure_schema = lambda: core_db.ensure_schema(self.db_path)

        with web_app.get_conn() as conn:
            conn.execute(
                "INSERT INTO warehouses(name, notes) VALUES (?, ?)",
                ("Warehouse A", "Primary"),
            )
            warehouse_id = conn.execute("SELECT id FROM warehouses WHERE name=?", ("Warehouse A",)).fetchone()["id"]
            conn.execute(
                """
                INSERT INTO batches(warehouse_id, batch_num, date_in, date_out, chicks, created_at, fiscal_year)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (warehouse_id, "B-1", "2026-04-01", "2026-05-01", 1000, "2026-04-01", 2026),
            )
            self.batch_id = int(conn.execute("SELECT id FROM batches WHERE batch_num='B-1'").fetchone()["id"])
            conn.commit()

        self.app = web_app.create_app()
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()

    def tearDown(self) -> None:
        web_app.get_conn = self.original_get_conn
        web_app.shared_ensure_schema = self.original_ensure_schema
        for suffix in ("", "-shm", "-wal"):
            path = Path(f"{self.db_path}{suffix}")
            if path.exists():
                try:
                    path.unlink()
                except PermissionError:
                    pass

    def test_warehouses_csv_export_uses_current_schema(self) -> None:
        response = self.client.get("/warehouses/export.csv")

        self.assertEqual(response.status_code, 200)
        payload = response.get_data(as_text=True)
        self.assertTrue(
            "id,name,batches_count,notes" in payload
            or "المعرف,اسم العنبر,عدد الدفعات,ملاحظات" in payload
        )
        self.assertIn("Warehouse A", payload)

    def test_warehouses_excel_export_uses_current_schema(self) -> None:
        response = self.client.get("/warehouses/export.xlsx")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertGreater(len(response.data), 0)

    def test_daily_record_with_treatments_triggers_analysis(self) -> None:
        with web_app.get_conn() as conn:
            treatment_id = conn.execute("SELECT id FROM treatment_catalog ORDER BY sort_order LIMIT 1").fetchone()["id"]

        response = self.client.post(
            f"/batches/{self.batch_id}/daily",
            data={
                "rec_date": "2026-04-22",
                "day_num": "18",
                "dead_count": "6",
                "culls_count": "1",
                "feed_kg": "120",
                "water_ltr": "260",
                "temp_min_c": "26.5",
                "temp_max_c": "34.6",
                "humidity_min_pct": "40",
                "humidity_max_pct": "62",
                "clinical_signs_text": "cough and wet litter",
                "notes": "follow up",
                "treatment_catalog_id[]": [str(treatment_id)],
                "treatment_dose[]": ["1ml/L"],
                "treatment_notes[]": ["day-1"],
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

        with web_app.get_conn() as conn:
            row = conn.execute(
                "SELECT analysis_status, analysis_summary, risk_score FROM daily_records WHERE batch_id=? AND rec_date=?",
                (self.batch_id, "2026-04-22"),
            ).fetchone()
            treatment_count = conn.execute(
                "SELECT COUNT(*) AS c FROM daily_treatments WHERE batch_id=? AND rec_date=?",
                (self.batch_id, "2026-04-22"),
            ).fetchone()["c"]
        self.assertIsNotNone(row)
        self.assertTrue((row["analysis_status"] or "").strip())
        self.assertGreater(float(row["risk_score"] or 0), 0)
        self.assertGreater(int(treatment_count), 0)

    def test_daily_record_accepts_custom_treatment_without_catalog(self) -> None:
        response = self.client.post(
            f"/batches/{self.batch_id}/daily",
            data={
                "rec_date": "2026-04-23",
                "day_num": "19",
                "dead_count": "5",
                "culls_count": "0",
                "feed_kg": "110",
                "water_ltr": "245",
                "temp_min_c": "26",
                "temp_max_c": "33",
                "humidity_min_pct": "45",
                "humidity_max_pct": "60",
                "clinical_signs_text": "mild cough",
                "notes": "custom treatment line",
                "treatment_catalog_id[]": [""],
                "treatment_name[]": ["Custom Mix X"],
                "treatment_active[]": ["tylosin + doxycycline"],
                "treatment_class[]": [""],
                "treatment_dose[]": ["1 g/L"],
                "treatment_notes[]": ["free entry"],
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

        with web_app.get_conn() as conn:
            tr = conn.execute(
                "SELECT product_name, active_ingredient, treatment_class FROM daily_treatments WHERE batch_id=? AND rec_date=?",
                (self.batch_id, "2026-04-23"),
            ).fetchone()
            row = conn.execute(
                "SELECT analysis_status, risk_score FROM daily_records WHERE batch_id=? AND rec_date=?",
                (self.batch_id, "2026-04-23"),
            ).fetchone()
        self.assertIsNotNone(tr)
        self.assertEqual((tr["product_name"] or "").strip(), "Custom Mix X")
        self.assertEqual((tr["treatment_class"] or "").strip(), "antibiotic")
        self.assertTrue((row["analysis_status"] or "").strip())


if __name__ == "__main__":
    unittest.main()
