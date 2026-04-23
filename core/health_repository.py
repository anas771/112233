from __future__ import annotations

import sqlite3

from core.health_types import DailyHealthInput, DailyTreatment, HealthAnalysisResult


def load_daily_input(conn: sqlite3.Connection, batch_id: int, rec_date: str) -> DailyHealthInput | None:
    row = conn.execute(
        """
        SELECT *
        FROM daily_records
        WHERE batch_id = ? AND rec_date = ?
        """,
        (batch_id, rec_date),
    ).fetchone()
    if not row:
        return None

    treatment_rows = conn.execute(
        """
        SELECT product_name, active_ingredient, treatment_class, dose_text, notes
        FROM daily_treatments
        WHERE batch_id = ? AND rec_date = ?
        ORDER BY id
        """,
        (batch_id, rec_date),
    ).fetchall()
    treatments = [
        DailyTreatment(
            product_name=t["product_name"],
            active_ingredient=t["active_ingredient"] or "",
            treatment_class=t["treatment_class"] or "",
            dose_text=t["dose_text"] or "",
            notes=t["notes"] or "",
        )
        for t in treatment_rows
    ]

    return DailyHealthInput(
        batch_id=batch_id,
        rec_date=rec_date,
        day_num=int(row["day_num"] or 0),
        dead_count=int(row["dead_count"] or 0),
        culls_count=int(row["culls_count"] or 0),
        feed_kg=float(row["feed_kg"] or 0),
        water_ltr=float(row["water_ltr"] or 0),
        temp_min_c=float(row["temp_min_c"] or 0),
        temp_max_c=float(row["temp_max_c"] or 0),
        humidity_min_pct=float(row["humidity_min_pct"] or 0),
        humidity_max_pct=float(row["humidity_max_pct"] or 0),
        clinical_signs_text=row["clinical_signs_text"] or "",
        notes=row["notes"] or "",
        treatments=treatments,
    )


def load_history_before(conn: sqlite3.Connection, batch_id: int, rec_date: str, days: int = 3) -> list[dict[str, float]]:
    rows = conn.execute(
        """
        SELECT dead_count, culls_count, feed_kg, water_ltr, temp_min_c, temp_max_c
        FROM daily_records
        WHERE batch_id = ? AND rec_date < ?
        ORDER BY rec_date DESC
        LIMIT ?
        """,
        (batch_id, rec_date, days),
    ).fetchall()
    return [dict(row) for row in rows]


def save_daily_analysis(conn: sqlite3.Connection, batch_id: int, rec_date: str, result: HealthAnalysisResult) -> None:
    top_codes = ",".join(hit.code for hit in result.top_conditions) or "none"
    summary = f"{result.summary} Signals: {top_codes}"
    conn.execute(
        """
        UPDATE daily_records
        SET analysis_status = ?, analysis_summary = ?, risk_score = ?
        WHERE batch_id = ? AND rec_date = ?
        """,
        (result.status, summary, result.risk_score, batch_id, rec_date),
    )
