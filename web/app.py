from __future__ import annotations

import csv
import io
import os
import sqlite3
import sys
import tempfile
from datetime import date, datetime
from pathlib import Path
from statistics import mean

from flask import Flask, Response, flash, redirect, render_template, request, url_for
from openpyxl import Workbook
from openpyxl.utils import get_column_letter

try:
    from fpdf import FPDF
    HAS_FPDF = True
except Exception:
    HAS_FPDF = False

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_ARABIC_TOOLS = True
except Exception:
    HAS_ARABIC_TOOLS = False

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    HAS_MATPLOTLIB = True
except Exception:
    HAS_MATPLOTLIB = False


BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
ASSETS_DIR = BASE_DIR / "assets"
REPORT_FONT_PATH = ASSETS_DIR / "Amiri-Regular.ttf"

from core.database import (
    DB_PATH,
    ensure_schema as shared_ensure_schema,
    get_conn,
    get_setting,
    set_setting,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("POULTRY_WEB_SECRET", "poultry-web-local-secret")


def _legacy_web_ensure_schema() -> None:
    schema = """
    CREATE TABLE IF NOT EXISTS system_settings (
        key TEXT PRIMARY KEY,
        value TEXT
    );

    CREATE TABLE IF NOT EXISTS warehouses (
        id    INTEGER PRIMARY KEY AUTOINCREMENT,
        name  TEXT NOT NULL UNIQUE,
        notes TEXT DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS batches (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        warehouse_id   INTEGER NOT NULL REFERENCES warehouses(id),
        batch_num      TEXT    DEFAULT '',
        date_in        TEXT    NOT NULL,
        date_out       TEXT    NOT NULL,
        days           INTEGER DEFAULT 0,
        chicks         INTEGER NOT NULL,
        chick_price    REAL    DEFAULT 0,
        chick_val      REAL    DEFAULT 0,
        feed_qty       REAL    DEFAULT 0,
        feed_val       REAL    DEFAULT 0,
        feed_trans     REAL    DEFAULT 0,
        sawdust_qty    REAL    DEFAULT 0,
        sawdust_val    REAL    DEFAULT 0,
        water_val      REAL    DEFAULT 0,
        gas_qty        REAL    DEFAULT 0,
        gas_val        REAL    DEFAULT 0,
        drugs_val      REAL    DEFAULT 0,
        wh_expenses    REAL    DEFAULT 0,
        house_exp      REAL    DEFAULT 0,
        breeders_pay   REAL    DEFAULT 0,
        qat_pay        REAL    DEFAULT 0,
        rent_val       REAL    DEFAULT 0,
        light_val      REAL    DEFAULT 0,
        sup_wh_pay     REAL    DEFAULT 0,
        sup_co_pay     REAL    DEFAULT 0,
        sup_sale_pay   REAL    DEFAULT 0,
        admin_val      REAL    DEFAULT 0,
        vaccine_pay    REAL    DEFAULT 0,
        delivery_val   REAL    DEFAULT 0,
        mixing_val     REAL    DEFAULT 0,
        wash_val       REAL    DEFAULT 0,
        other_costs    REAL    DEFAULT 0,
        total_cost     REAL    DEFAULT 0,
        cust_qty       INTEGER DEFAULT 0,
        cust_val       REAL    DEFAULT 0,
        mkt_qty        INTEGER DEFAULT 0,
        mkt_val        REAL    DEFAULT 0,
        offal_val      REAL    DEFAULT 0,
        feed_sale      REAL    DEFAULT 0,
        feed_trans_r   REAL    DEFAULT 0,
        drug_return    REAL    DEFAULT 0,
        gas_return     REAL    DEFAULT 0,
        total_rev      REAL    DEFAULT 0,
        total_sold     INTEGER DEFAULT 0,
        total_dead     INTEGER DEFAULT 0,
        mort_rate      REAL    DEFAULT 0,
        avg_weight     REAL    DEFAULT 0,
        fcr            REAL    DEFAULT 0,
        avg_price      REAL    DEFAULT 0,
        net_result     REAL    DEFAULT 0,
        share_pct      REAL    DEFAULT 65,
        share_val      REAL    DEFAULT 0,
        notes          TEXT    DEFAULT '',
        created_at     TEXT,
        consumed_birds INTEGER DEFAULT 0,
        partner_name   TEXT    DEFAULT '',
        feed_sale_qty  REAL    DEFAULT 0,
        feed_trans_r_qty REAL  DEFAULT 0,
        feed_rem_qty   REAL    DEFAULT 0,
        feed_rem_val   REAL    DEFAULT 0,
        fiscal_year    INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS daily_records (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id    INTEGER NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
        rec_date    TEXT    NOT NULL,
        day_num     INTEGER DEFAULT 0,
        dead_count  INTEGER DEFAULT 0,
        feed_kg     REAL    DEFAULT 0,
        water_ltr   REAL    DEFAULT 0,
        notes       TEXT    DEFAULT '',
        UNIQUE(batch_id, rec_date)
    );

    CREATE TABLE IF NOT EXISTS farm_sales (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id  INTEGER NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
        sale_date TEXT    DEFAULT '',
        sale_type TEXT    DEFAULT 'آجل',
        customer  TEXT,
        qty       INTEGER DEFAULT 0,
        price     REAL    DEFAULT 0,
        total_val REAL    DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS market_sales (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id  INTEGER NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
        sale_date TEXT    DEFAULT '',
        office    TEXT,
        qty_sent  INTEGER DEFAULT 0,
        deaths    INTEGER DEFAULT 0,
        qty_sold  INTEGER DEFAULT 0,
        net_val   REAL    DEFAULT 0,
        inv_num   TEXT
    );

    CREATE TABLE IF NOT EXISTS cost_types (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        code       TEXT    NOT NULL UNIQUE,
        name_ar    TEXT    NOT NULL,
        category   TEXT    DEFAULT 'أخرى',
        has_qty    INTEGER DEFAULT 0,
        unit       TEXT,
        sort_order INTEGER DEFAULT 99,
        is_active  INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS batch_costs (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id     INTEGER NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
        cost_type_id INTEGER NOT NULL REFERENCES cost_types(id),
        qty          REAL    DEFAULT 0,
        amount       REAL    DEFAULT 0,
        notes        TEXT    DEFAULT '',
        UNIQUE(batch_id, cost_type_id)
    );

    CREATE TABLE IF NOT EXISTS revenue_types (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        code       TEXT    NOT NULL UNIQUE,
        name_ar    TEXT    NOT NULL,
        category   TEXT    DEFAULT 'مبيعات',
        has_qty    INTEGER DEFAULT 0,
        unit       TEXT,
        sort_order INTEGER DEFAULT 99,
        is_active  INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS batch_revenues (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id        INTEGER NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
        revenue_type_id INTEGER NOT NULL REFERENCES revenue_types(id),
        qty             REAL    DEFAULT 0,
        amount          REAL    DEFAULT 0,
        notes           TEXT    DEFAULT '',
        UNIQUE(batch_id, revenue_type_id)
    );
    """

    with get_conn() as conn:
        conn.executescript(schema)
        conn.executemany(
            """
            INSERT OR IGNORE INTO cost_types(code, name_ar, category, has_qty, unit, sort_order)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                ("chick_val", "الكتاكيت", "مواد", 1, "حبة", 1),
                ("feed_val", "العلف", "مواد", 1, "طن", 2),
                ("drugs_val", "علاجات وأدوية", "صحة", 0, None, 3),
                ("gas_val", "الغاز", "مرافق", 1, "اسطوانة", 4),
                ("other_costs", "مصاريف أخرى", "أخرى", 0, None, 5),
            ],
        )
        conn.executemany(
            """
            INSERT OR IGNORE INTO revenue_types(code, name_ar, category, has_qty, unit, sort_order)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                ("offal_val", "مبيعات ذبيل", "مبيعات", 0, None, 1),
                ("feed_sale", "مبيعات علف", "مبيعات", 1, "كيس", 2),
                ("drug_return", "مرتجع علاجات", "مرتجعات", 0, None, 3),
            ],
        )
        conn.commit()


def to_float(value: str | None, default: float = 0.0) -> float:
    if value is None:
        return default
    value = value.strip()
    if not value:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def to_int(value: str | None, default: int = 0) -> int:
    if value is None:
        return default
    value = value.strip()
    if not value:
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def recalc_batch(batch_id: int) -> None:
    with get_conn() as conn:
        b = conn.execute("SELECT * FROM batches WHERE id=?", (batch_id,)).fetchone()
        if not b:
            return

        fixed_cost = sum(
            float(b[k] or 0)
            for k in [
                "chick_val",
                "feed_val",
                "feed_trans",
                "sawdust_val",
                "water_val",
                "gas_val",
                "drugs_val",
                "wh_expenses",
                "house_exp",
                "breeders_pay",
                "qat_pay",
                "rent_val",
                "light_val",
                "sup_wh_pay",
                "sup_co_pay",
                "sup_sale_pay",
                "admin_val",
                "vaccine_pay",
                "delivery_val",
                "mixing_val",
                "wash_val",
                "other_costs",
            ]
        )
        dyn_cost = conn.execute(
            "SELECT COALESCE(SUM(amount),0) FROM batch_costs WHERE batch_id=?", (batch_id,)
        ).fetchone()[0]
        total_cost = max(fixed_cost, float(dyn_cost or 0))

        farm = conn.execute(
            "SELECT COALESCE(SUM(total_val),0), COALESCE(SUM(qty),0) FROM farm_sales WHERE batch_id=?",
            (batch_id,),
        ).fetchone()
        market = conn.execute(
            "SELECT COALESCE(SUM(net_val),0), COALESCE(SUM(qty_sold),0) FROM market_sales WHERE batch_id=?",
            (batch_id,),
        ).fetchone()
        extra_rev = conn.execute(
            "SELECT COALESCE(SUM(amount),0) FROM batch_revenues WHERE batch_id=?", (batch_id,)
        ).fetchone()[0]
        total_rev = float(farm[0] or 0) + float(market[0] or 0) + float(extra_rev or 0)
        total_sold = int((farm[1] or 0) + (market[1] or 0))
        total_dead = int(
            conn.execute(
                "SELECT COALESCE(SUM(dead_count),0) FROM daily_records WHERE batch_id=?",
                (batch_id,),
            ).fetchone()[0]
            or 0
        )
        chicks = int(b["chicks"] or 0)
        mort_rate = (total_dead / chicks * 100) if chicks > 0 else 0
        net_result = total_rev - total_cost

        conn.execute(
            """
            UPDATE batches
            SET total_cost=?, total_rev=?, total_sold=?, total_dead=?, mort_rate=?, net_result=?
            WHERE id=?
            """,
            (total_cost, total_rev, total_sold, total_dead, mort_rate, net_result, batch_id),
        )
        conn.commit()


def get_filters() -> tuple[list[sqlite3.Row], list[int]]:
    with get_conn() as conn:
        warehouses = conn.execute("SELECT id, name FROM warehouses ORDER BY name").fetchall()
        years = [
            int(row["fy"])
            for row in conn.execute(
                """
                SELECT DISTINCT COALESCE(fiscal_year, CAST(substr(date_in, 1, 4) AS INTEGER)) AS fy
                FROM batches
                WHERE COALESCE(fiscal_year, CAST(substr(date_in, 1, 4) AS INTEGER)) > 0
                ORDER BY fy DESC
                """
            ).fetchall()
        ]
    return warehouses, years


def make_where_clause(warehouse_id: int | None, fiscal_year: int | None) -> tuple[str, list[int]]:
    where: list[str] = []
    params: list[int] = []
    if warehouse_id:
        where.append("b.warehouse_id=?")
        params.append(warehouse_id)
    if fiscal_year:
        where.append("COALESCE(b.fiscal_year, CAST(substr(b.date_in, 1, 4) AS INTEGER))=?")
        params.append(fiscal_year)
    return (" WHERE " + " AND ".join(where)) if where else "", params


def create_database_backup() -> Path:
    backups_dir = BASE_DIR / "backups"
    backups_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destination = backups_dir / f"poultry_web_backup_{timestamp}.db"
    with sqlite3.connect(DB_PATH) as src_conn, sqlite3.connect(destination) as dst_conn:
        src_conn.backup(dst_conn)
    return destination


def warehouse_summary_rows(where_clause: str, params: list[int]) -> list[dict[str, object]]:
    query = f"""
        SELECT
            w.name AS warehouse_name,
            COUNT(b.id) AS batches_count,
            COALESCE(SUM(b.chicks), 0) AS chicks_total,
            COALESCE(SUM(b.total_cost), 0) AS cost_total,
            COALESCE(SUM(b.total_rev), 0) AS revenue_total,
            COALESCE(SUM(b.net_result), 0) AS net_total,
            COALESCE(AVG(b.mort_rate), 0) AS avg_mortality
        FROM warehouses w
        LEFT JOIN batches b ON b.warehouse_id = w.id
        {where_clause}
        GROUP BY w.id, w.name
        ORDER BY w.name
    """
    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def year_summary_rows() -> list[dict[str, object]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT
                COALESCE(fiscal_year, CAST(substr(date_in, 1, 4) AS INTEGER)) AS fiscal_year,
                COUNT(*) AS batches_count,
                COALESCE(SUM(total_cost), 0) AS cost_total,
                COALESCE(SUM(total_rev), 0) AS revenue_total,
                COALESCE(SUM(net_result), 0) AS net_total
            FROM batches
            GROUP BY COALESCE(fiscal_year, CAST(substr(date_in, 1, 4) AS INTEGER))
            HAVING fiscal_year > 0
            ORDER BY fiscal_year DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def make_csv_response(filename: str, headers: list[str], rows: list[list[object]]) -> Response:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    writer.writerows(rows)
    csv_text = "\ufeff" + buffer.getvalue()
    return Response(
        csv_text,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def make_excel_response(filename: str, sheet_name: str, headers: list[str], rows: list[list[object]]) -> Response:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = (sheet_name or "Report")[:31]
    sheet.append(headers)
    for row in rows:
        sheet.append(list(row))

    sheet.freeze_panes = "A2"
    for col_idx, header in enumerate(headers, start=1):
        max_length = len(str(header or ""))
        for row_idx in range(2, len(rows) + 2):
            value = sheet.cell(row=row_idx, column=col_idx).value
            max_length = max(max_length, len(str(value or "")))
        sheet.column_dimensions[get_column_letter(col_idx)].width = min(max(max_length + 2, 12), 45)

    output = io.BytesIO()
    workbook.save(output)
    payload = output.getvalue()
    return Response(
        payload,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def make_pdf_response(filename: str, payload: bytes) -> Response:
    return Response(
        payload,
        mimetype="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def ar_text(value: object) -> str:
    text = str(value or "")
    if HAS_ARABIC_TOOLS:
        try:
            return get_display(arabic_reshaper.reshape(text))
        except Exception:
            return text
    return text


def reports_payload(warehouse_id: int | None, fiscal_year: int | None) -> dict[str, object]:
    where_clause, params = make_where_clause(warehouse_id, fiscal_year)
    warehouses, years = get_filters()
    warehouse_rows = warehouse_summary_rows(where_clause, params)

    with get_conn() as conn:
        stats = conn.execute(
            f"""
            SELECT
                COUNT(*) AS batches_count,
                COALESCE(SUM(b.chicks), 0) AS chicks_total,
                COALESCE(SUM(b.total_dead), 0) AS total_dead,
                COALESCE(SUM(b.total_sold), 0) AS total_sold,
                COALESCE(SUM(b.total_cost), 0) AS cost_total,
                COALESCE(SUM(b.total_rev), 0) AS revenue_total,
                COALESCE(SUM(b.net_result), 0) AS net_total,
                COALESCE(AVG(b.fcr), 0) AS avg_fcr,
                COALESCE(AVG(b.mort_rate), 0) AS avg_mortality
            FROM batches b
            {where_clause}
            """,
            params,
        ).fetchone()

        annual_rows = [
            dict(row)
            for row in conn.execute(
                f"""
                SELECT
                    COALESCE(b.fiscal_year, CAST(substr(b.date_in, 1, 4) AS INTEGER)) AS fiscal_year,
                    COUNT(*) AS batches_count,
                    COALESCE(SUM(b.total_cost), 0) AS cost_total,
                    COALESCE(SUM(b.total_rev), 0) AS revenue_total,
                    COALESCE(SUM(b.net_result), 0) AS net_total
                FROM batches b
                {where_clause}
                GROUP BY COALESCE(b.fiscal_year, CAST(substr(b.date_in, 1, 4) AS INTEGER))
                HAVING fiscal_year > 0
                ORDER BY fiscal_year DESC
                """,
                params,
            ).fetchall()
        ]

        batches_rows = [
            dict(row)
            for row in conn.execute(
                f"""
                SELECT b.*, w.name AS warehouse_name
                FROM batches b
                JOIN warehouses w ON w.id = b.warehouse_id
                {where_clause}
                ORDER BY b.date_in DESC, b.id DESC
                LIMIT 25
                """,
                params,
            ).fetchall()
        ]

        sales_by_type_rows = [
            dict(row)
            for row in conn.execute(
                f"""
                SELECT
                    COALESCE(fs.sale_type, 'Unknown') AS sale_type,
                    COALESCE(SUM(fs.qty), 0) AS qty_total,
                    COALESCE(SUM(fs.total_val), 0) AS amount_total
                FROM farm_sales fs
                JOIN batches b ON b.id = fs.batch_id
                {where_clause}
                GROUP BY COALESCE(fs.sale_type, 'Unknown')
                ORDER BY amount_total DESC, qty_total DESC
                """,
                params,
            ).fetchall()
        ]

        market_summary_row = dict(
            conn.execute(
                f"""
                SELECT
                    COALESCE(SUM(ms.qty_sent), 0) AS qty_sent_total,
                    COALESCE(SUM(ms.deaths), 0) AS deaths_total,
                    COALESCE(SUM(ms.qty_sold), 0) AS qty_sold_total,
                    COALESCE(SUM(ms.net_val), 0) AS net_val_total
                FROM market_sales ms
                JOIN batches b ON b.id = ms.batch_id
                {where_clause}
                """,
                params,
            ).fetchone()
        )

        cost_types_rows = [
            dict(row)
            for row in conn.execute(
                f"""
                SELECT
                    ct.name_ar AS type_name,
                    ct.category AS category,
                    COALESCE(SUM(bc.qty), 0) AS qty_total,
                    COALESCE(SUM(bc.amount), 0) AS amount_total
                FROM batch_costs bc
                JOIN cost_types ct ON ct.id = bc.cost_type_id
                JOIN batches b ON b.id = bc.batch_id
                {where_clause}
                GROUP BY ct.id, ct.name_ar, ct.category
                HAVING COALESCE(SUM(bc.qty), 0) > 0 OR COALESCE(SUM(bc.amount), 0) > 0
                ORDER BY amount_total DESC, qty_total DESC
                """,
                params,
            ).fetchall()
        ]

        revenue_types_rows = [
            dict(row)
            for row in conn.execute(
                f"""
                SELECT
                    rt.name_ar AS type_name,
                    rt.category AS category,
                    COALESCE(SUM(br.qty), 0) AS qty_total,
                    COALESCE(SUM(br.amount), 0) AS amount_total
                FROM batch_revenues br
                JOIN revenue_types rt ON rt.id = br.revenue_type_id
                JOIN batches b ON b.id = br.batch_id
                {where_clause}
                GROUP BY rt.id, rt.name_ar, rt.category
                HAVING COALESCE(SUM(br.qty), 0) > 0 OR COALESCE(SUM(br.amount), 0) > 0
                ORDER BY amount_total DESC, qty_total DESC
                """,
                params,
            ).fetchall()
        ]

        daily_summary_row = dict(
            conn.execute(
                f"""
                SELECT
                    COUNT(dr.id) AS entries_count,
                    COALESCE(SUM(dr.dead_count), 0) AS dead_total,
                    COALESCE(SUM(dr.feed_kg), 0) AS feed_total,
                    COALESCE(SUM(dr.water_ltr), 0) AS water_total,
                    COALESCE(AVG(dr.dead_count), 0) AS avg_daily_deaths
                FROM daily_records dr
                JOIN batches b ON b.id = dr.batch_id
                {where_clause}
                """,
                params,
            ).fetchone()
        )

        best_batch_row = conn.execute(
            f"""
            SELECT b.id, b.batch_num, w.name AS warehouse_name, COALESCE(b.net_result, 0) AS net_result
            FROM batches b
            JOIN warehouses w ON w.id = b.warehouse_id
            {where_clause}
            ORDER BY net_result DESC, b.id DESC
            LIMIT 1
            """,
            params,
        ).fetchone()

        worst_batch_row = conn.execute(
            f"""
            SELECT b.id, b.batch_num, w.name AS warehouse_name, COALESCE(b.net_result, 0) AS net_result
            FROM batches b
            JOIN warehouses w ON w.id = b.warehouse_id
            {where_clause}
            ORDER BY net_result ASC, b.id DESC
            LIMIT 1
            """,
            params,
        ).fetchone()

    stats_data = dict(stats) if stats else {}
    cost_total = float(stats_data.get('cost_total') or 0)
    revenue_total = float(stats_data.get('revenue_total') or 0)
    net_total = float(stats_data.get('net_total') or 0)
    chicks_total = float(stats_data.get('chicks_total') or 0)
    dead_total = float(stats_data.get('total_dead') or 0)
    sold_total = float(stats_data.get('total_sold') or 0)

    report_summary = {
        'warehouses_count': len(warehouse_rows),
        'annual_years_count': len(annual_rows),
        'shown_batches_count': int(stats_data.get('batches_count') or 0),
        'cost_total': cost_total,
        'revenue_total': revenue_total,
        'net_total': net_total,
        'chicks_total': chicks_total,
        'total_dead': dead_total,
        'total_sold': sold_total,
    }

    fcr_values = [float(row.get('fcr') or 0) for row in batches_rows if float(row.get('fcr') or 0) > 0]
    mort_values = [float(row.get('mort_rate') or 0) for row in batches_rows]
    margin_pct = (net_total / revenue_total * 100) if revenue_total > 0 else 0.0
    death_rate_pct = (dead_total / chicks_total * 100) if chicks_total > 0 else 0.0
    sold_rate_pct = (sold_total / chicks_total * 100) if chicks_total > 0 else 0.0

    top_warehouse = max(warehouse_rows, key=lambda x: float(x.get('net_total') or 0), default=None)
    best_batch = dict(best_batch_row) if best_batch_row else None
    worst_batch = dict(worst_batch_row) if worst_batch_row else None

    top_cost_type = cost_types_rows[0] if cost_types_rows else None
    top_revenue_type = revenue_types_rows[0] if revenue_types_rows else None
    farm_sales_total = sum(float(row.get('amount_total') or 0) for row in sales_by_type_rows)
    extra_revenues_total = sum(float(row.get('amount_total') or 0) for row in revenue_types_rows)
    market_sales_total = float(market_summary_row.get('net_val_total') or 0)
    daily_entries = int(daily_summary_row.get('entries_count') or 0)

    dashboard_insights = {
        'margin_pct': margin_pct,
        'avg_fcr': mean(fcr_values) if fcr_values else 0,
        'avg_mortality': mean(mort_values) if mort_values else 0,
        'death_rate_pct': death_rate_pct,
        'sold_rate_pct': sold_rate_pct,
        'top_warehouse_name': top_warehouse['warehouse_name'] if top_warehouse else '?',
        'top_warehouse_net': float(top_warehouse['net_total']) if top_warehouse else 0,
        'best_batch_label': (best_batch.get('batch_num') or best_batch.get('id')) if best_batch else '?',
        'best_batch_net': float(best_batch['net_result']) if best_batch else 0,
        'worst_batch_label': (worst_batch.get('batch_num') or worst_batch.get('id')) if worst_batch else '?',
        'worst_batch_net': float(worst_batch['net_result']) if worst_batch else 0,
        'farm_sales_total': farm_sales_total,
        'market_sales_total': market_sales_total,
        'extra_revenues_total': extra_revenues_total,
        'top_cost_type_name': top_cost_type['type_name'] if top_cost_type else '?',
        'top_cost_type_amount': float(top_cost_type['amount_total']) if top_cost_type else 0,
        'top_revenue_type_name': top_revenue_type['type_name'] if top_revenue_type else '?',
        'top_revenue_type_amount': float(top_revenue_type['amount_total']) if top_revenue_type else 0,
        'daily_entries_count': daily_entries,
        'daily_dead_total': float(daily_summary_row.get('dead_total') or 0),
        'daily_feed_total': float(daily_summary_row.get('feed_total') or 0),
        'daily_water_total': float(daily_summary_row.get('water_total') or 0),
        'avg_daily_deaths': float(daily_summary_row.get('avg_daily_deaths') or 0),
    }

    return {
        'where_clause': where_clause,
        'params': params,
        'warehouses': warehouses,
        'years': years,
        'warehouse_rows': warehouse_rows,
        'annual_rows': annual_rows,
        'batches_rows': batches_rows,
        'sales_by_type_rows': sales_by_type_rows,
        'market_summary_row': market_summary_row,
        'cost_types_rows': cost_types_rows,
        'revenue_types_rows': revenue_types_rows,
        'daily_summary_row': daily_summary_row,
        'report_summary': report_summary,
        'dashboard_insights': dashboard_insights,
    }


@app.template_filter("num")
def num_filter(value: float | int | None, digits: int = 0) -> str:
    try:
        if digits == 0:
            return f"{int(float(value or 0)):,}"
        return f"{float(value or 0):,.{digits}f}"
    except Exception:
        return "0"


@app.route("/")
def dashboard():
    warehouse_id = to_int(request.args.get("warehouse_id"), 0) or None
    fiscal_year = to_int(request.args.get("fiscal_year"), 0) or None
    where_clause, params = make_where_clause(warehouse_id, fiscal_year)
    warehouses, years = get_filters()
    with get_conn() as conn:
        stats = conn.execute(
            f"""
            SELECT
              (SELECT COUNT(*) FROM warehouses) AS warehouses_count,
              COUNT(*) AS batches_count,
              COALESCE(SUM(b.total_cost),0) AS total_cost,
              COALESCE(SUM(b.total_rev),0) AS total_rev,
              COALESCE(SUM(b.net_result),0) AS total_net,
              COALESCE(SUM(b.chicks),0) AS chicks_total,
              COALESCE(AVG(b.mort_rate),0) AS avg_mortality
            FROM batches b
            {where_clause}
            """
            ,
            params,
        ).fetchone()
        latest_batches = conn.execute(
            f"""
            SELECT b.*, w.name AS warehouse_name
            FROM batches b
            JOIN warehouses w ON w.id=b.warehouse_id
            {where_clause}
            ORDER BY b.date_in DESC, b.id DESC
            LIMIT 12
            """,
            params,
        ).fetchall()
    return render_template(
        "dashboard.html",
        stats=stats,
        latest_batches=latest_batches,
        filters={"warehouse_id": warehouse_id or "", "fiscal_year": fiscal_year or ""},
        warehouses=warehouses,
        years=years,
    )


@app.route("/warehouses", methods=["GET", "POST"])
def warehouses():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        notes = request.form.get("notes", "").strip()
        if not name:
            flash("اسم العنبر مطلوب.", "error")
            return redirect(url_for("warehouses"))
        with get_conn() as conn:
            conn.execute("INSERT INTO warehouses(name, notes) VALUES (?, ?)", (name, notes))
            conn.commit()
        flash("تم إضافة العنبر بنجاح.", "success")
        return redirect(url_for("warehouses"))

    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT w.*, COUNT(b.id) AS batches_count
            FROM warehouses w
            LEFT JOIN batches b ON b.warehouse_id = w.id
            GROUP BY w.id
            ORDER BY w.id DESC
            """
        ).fetchall()
    return render_template("warehouses.html", warehouses=rows)


@app.get("/warehouses/export.csv")
def export_warehouses_csv():
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT w.id, w.name, COALESCE(w.capacity, 0) AS capacity, w.notes, COUNT(b.id) AS batches_count
            FROM warehouses w
            LEFT JOIN batches b ON b.warehouse_id = w.id
            GROUP BY w.id
            ORDER BY w.id DESC
            """
        ).fetchall()
    payload = [[r["id"], r["name"], r["capacity"], r["batches_count"], r["notes"] or ""] for r in rows]
    return make_csv_response(
        "warehouses.csv",
        ["id", "name", "capacity", "batches_count", "notes"],
        payload,
    )


@app.get("/warehouses/export.xlsx")
def export_warehouses_excel():
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT w.id, w.name, COALESCE(w.capacity, 0) AS capacity, w.notes, COUNT(b.id) AS batches_count
            FROM warehouses w
            LEFT JOIN batches b ON b.warehouse_id = w.id
            GROUP BY w.id
            ORDER BY w.id DESC
            """
        ).fetchall()
    payload = [[r["id"], r["name"], r["capacity"], r["batches_count"], r["notes"] or ""] for r in rows]
    return make_excel_response(
        "warehouses.xlsx",
        "Warehouses",
        ["id", "name", "capacity", "batches_count", "notes"],
        payload,
    )


@app.post("/warehouses/<int:warehouse_id>/delete")
def delete_warehouse(warehouse_id: int):
    with get_conn() as conn:
        linked = conn.execute("SELECT COUNT(*) FROM batches WHERE warehouse_id=?", (warehouse_id,)).fetchone()[0]
        if linked:
            flash("لا يمكن حذف العنبر لأنه مرتبط بدفعات.", "error")
            return redirect(url_for("warehouses"))
        conn.execute("DELETE FROM warehouses WHERE id=?", (warehouse_id,))
        conn.commit()
    flash("تم حذف العنبر.", "success")
    return redirect(url_for("warehouses"))


@app.route("/batches")
def batches():
    warehouse_id = to_int(request.args.get("warehouse_id"), 0) or None
    fiscal_year = to_int(request.args.get("fiscal_year"), 0) or None
    where_clause, params = make_where_clause(warehouse_id, fiscal_year)
    warehouses, years = get_filters()
    with get_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT b.*, w.name AS warehouse_name
            FROM batches b
            JOIN warehouses w ON w.id=b.warehouse_id
            {where_clause}
            ORDER BY b.date_in DESC, b.id DESC
            """,
            params,
        ).fetchall()
    return render_template(
        "batches.html",
        batches=rows,
        warehouses=warehouses,
        years=years,
        filters={"warehouse_id": warehouse_id or "", "fiscal_year": fiscal_year or ""},
    )


@app.route("/batches/new", methods=["GET", "POST"])
def new_batch():
    with get_conn() as conn:
        warehouse_rows = conn.execute("SELECT * FROM warehouses ORDER BY name").fetchall()

    if request.method == "POST":
        warehouse_id = to_int(request.form.get("warehouse_id"))
        batch_num = request.form.get("batch_num", "").strip()
        date_in = request.form.get("date_in", "").strip()
        date_out = request.form.get("date_out", "").strip()
        chicks = to_int(request.form.get("chicks"), 0)
        notes = request.form.get("notes", "").strip()
        days = to_int(request.form.get("days"), 0)
        chick_price = to_float(request.form.get("chick_price"), 0.0)

        if not warehouse_id or not date_in or not date_out or chicks <= 0:
            flash("أكمل الحقول الأساسية: العنبر + تاريخ الدخول + تاريخ الخروج + عدد الكتاكيت.", "error")
            return render_template(
                "batch_form.html",
                warehouses=warehouse_rows,
                batch=None,
                form=request.form,
                action=url_for("new_batch"),
                title="إضافة دفعة",
            )

        chick_val = chick_price * chicks
        with get_conn() as conn:
            batch_id = conn.execute(
                """
                INSERT INTO batches(
                    warehouse_id,batch_num,date_in,date_out,days,chicks,chick_price,chick_val,notes,created_at,fiscal_year
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    warehouse_id,
                    batch_num,
                    date_in,
                    date_out,
                    days,
                    chicks,
                    chick_price,
                    chick_val,
                    notes,
                    date.today().isoformat(),
                    int(date_in[:4]) if len(date_in) >= 4 else 0,
                ),
            ).lastrowid
            conn.commit()
        recalc_batch(batch_id)
        flash("تم إنشاء الدفعة.", "success")
        return redirect(url_for("batch_detail", batch_id=batch_id))

    return render_template(
        "batch_form.html",
        warehouses=warehouse_rows,
        batch=None,
        form={},
        action=url_for("new_batch"),
        title="إضافة دفعة",
    )


@app.route("/batches/<int:batch_id>/edit", methods=["GET", "POST"])
def edit_batch(batch_id: int):
    with get_conn() as conn:
        batch = conn.execute("SELECT * FROM batches WHERE id=?", (batch_id,)).fetchone()
        warehouses_rows = conn.execute("SELECT * FROM warehouses ORDER BY name").fetchall()
    if not batch:
        flash("الدفعة غير موجودة.", "error")
        return redirect(url_for("batches"))

    if request.method == "POST":
        with get_conn() as conn:
            conn.execute(
                """
                UPDATE batches
                SET warehouse_id=?, batch_num=?, date_in=?, date_out=?, days=?, chicks=?, chick_price=?, notes=?
                WHERE id=?
                """,
                (
                    to_int(request.form.get("warehouse_id")),
                    request.form.get("batch_num", "").strip(),
                    request.form.get("date_in", "").strip(),
                    request.form.get("date_out", "").strip(),
                    to_int(request.form.get("days")),
                    to_int(request.form.get("chicks")),
                    to_float(request.form.get("chick_price")),
                    request.form.get("notes", "").strip(),
                    batch_id,
                ),
            )
            conn.commit()
        recalc_batch(batch_id)
        flash("تم تحديث الدفعة.", "success")
        return redirect(url_for("batch_detail", batch_id=batch_id))

    return render_template(
        "batch_form.html",
        warehouses=warehouses_rows,
        batch=batch,
        form=dict(batch),
        action=url_for("edit_batch", batch_id=batch_id),
        title=f"تعديل الدفعة #{batch_id}",
    )


@app.post("/batches/<int:batch_id>/delete")
def delete_batch(batch_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM batches WHERE id=?", (batch_id,))
        conn.commit()
    flash("تم حذف الدفعة.", "success")
    return redirect(url_for("batches"))


@app.route("/batches/<int:batch_id>")
def batch_detail(batch_id: int):
    with get_conn() as conn:
        batch = conn.execute(
            """
            SELECT b.*, w.name AS warehouse_name
            FROM batches b JOIN warehouses w ON w.id=b.warehouse_id
            WHERE b.id=?
            """,
            (batch_id,),
        ).fetchone()
        if not batch:
            flash("الدفعة غير موجودة.", "error")
            return redirect(url_for("batches"))
        daily_count = conn.execute("SELECT COUNT(*) FROM daily_records WHERE batch_id=?", (batch_id,)).fetchone()[0]
        farm_count = conn.execute("SELECT COUNT(*) FROM farm_sales WHERE batch_id=?", (batch_id,)).fetchone()[0]
        market_count = conn.execute("SELECT COUNT(*) FROM market_sales WHERE batch_id=?", (batch_id,)).fetchone()[0]
        records = conn.execute(
            """
            SELECT rec_date, day_num, dead_count, feed_kg, water_ltr
            FROM daily_records
            WHERE batch_id=?
            ORDER BY rec_date DESC
            LIMIT 5
            """,
            (batch_id,),
        ).fetchall()
    return render_template(
        "batch_detail.html",
        batch=batch,
        daily_count=daily_count,
        farm_count=farm_count,
        market_count=market_count,
        recent_daily=records,
    )


@app.route("/batches/<int:batch_id>/daily", methods=["GET", "POST"])
def daily_records(batch_id: int):
    if request.method == "POST":
        with get_conn() as conn:
            conn.execute(
                """
                INSERT INTO daily_records(batch_id, rec_date, day_num, dead_count, feed_kg, water_ltr, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(batch_id, rec_date)
                DO UPDATE SET day_num=excluded.day_num, dead_count=excluded.dead_count,
                              feed_kg=excluded.feed_kg, water_ltr=excluded.water_ltr, notes=excluded.notes
                """,
                (
                    batch_id,
                    request.form.get("rec_date", "").strip(),
                    to_int(request.form.get("day_num")),
                    to_int(request.form.get("dead_count")),
                    to_float(request.form.get("feed_kg")),
                    to_float(request.form.get("water_ltr")),
                    request.form.get("notes", "").strip(),
                ),
            )
            conn.commit()
        recalc_batch(batch_id)
        flash("تم حفظ السجل اليومي.", "success")
        return redirect(url_for("daily_records", batch_id=batch_id))

    with get_conn() as conn:
        batch = conn.execute("SELECT id, batch_num FROM batches WHERE id=?", (batch_id,)).fetchone()
        rows = conn.execute("SELECT * FROM daily_records WHERE batch_id=? ORDER BY rec_date DESC", (batch_id,)).fetchall()
    return render_template("daily_records.html", batch=batch, rows=rows)


@app.get("/batches/<int:batch_id>/daily/export.csv")
def export_daily_records_csv(batch_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT rec_date, day_num, dead_count, feed_kg, water_ltr, notes
            FROM daily_records
            WHERE batch_id=?
            ORDER BY rec_date
            """,
            (batch_id,),
        ).fetchall()
    payload = [
        [r["rec_date"], r["day_num"], r["dead_count"], r["feed_kg"], r["water_ltr"], r["notes"] or ""]
        for r in rows
    ]
    return make_csv_response(
        f"batch_{batch_id}_daily_records.csv",
        ["rec_date", "day_num", "dead_count", "feed_kg", "water_ltr", "notes"],
        payload,
    )


@app.get("/batches/<int:batch_id>/daily/export.xlsx")
def export_daily_records_excel(batch_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT rec_date, day_num, dead_count, feed_kg, water_ltr, notes
            FROM daily_records
            WHERE batch_id=?
            ORDER BY rec_date
            """,
            (batch_id,),
        ).fetchall()
    payload = [
        [r["rec_date"], r["day_num"], r["dead_count"], r["feed_kg"], r["water_ltr"], r["notes"] or ""]
        for r in rows
    ]
    return make_excel_response(
        f"batch_{batch_id}_daily_records.xlsx",
        "DailyRecords",
        ["rec_date", "day_num", "dead_count", "feed_kg", "water_ltr", "notes"],
        payload,
    )


@app.post("/daily/<int:record_id>/delete")
def delete_daily_record(record_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT batch_id FROM daily_records WHERE id=?", (record_id,)).fetchone()
        if not row:
            flash("السجل غير موجود.", "error")
            return redirect(url_for("batches"))
        batch_id = row["batch_id"]
        conn.execute("DELETE FROM daily_records WHERE id=?", (record_id,))
        conn.commit()
    recalc_batch(batch_id)
    flash("تم حذف السجل اليومي.", "success")
    return redirect(url_for("daily_records", batch_id=batch_id))


@app.route("/batches/<int:batch_id>/farm-sales", methods=["GET", "POST"])
def farm_sales(batch_id: int):
    if request.method == "POST":
        qty = to_int(request.form.get("qty"))
        price = to_float(request.form.get("price"))
        with get_conn() as conn:
            conn.execute(
                """
                INSERT INTO farm_sales(batch_id, sale_date, sale_type, customer, qty, price, total_val)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    batch_id,
                    request.form.get("sale_date", "").strip(),
                    request.form.get("sale_type", "").strip() or "آجل",
                    request.form.get("customer", "").strip(),
                    qty,
                    price,
                    qty * price,
                ),
            )
            conn.commit()
        recalc_batch(batch_id)
        flash("تم حفظ مبيعة العنبر.", "success")
        return redirect(url_for("farm_sales", batch_id=batch_id))

    with get_conn() as conn:
        batch = conn.execute("SELECT id, batch_num FROM batches WHERE id=?", (batch_id,)).fetchone()
        rows = conn.execute("SELECT * FROM farm_sales WHERE batch_id=? ORDER BY id DESC", (batch_id,)).fetchall()
    return render_template("farm_sales.html", batch=batch, rows=rows)


@app.post("/farm-sales/<int:sale_id>/delete")
def delete_farm_sale(sale_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT batch_id FROM farm_sales WHERE id=?", (sale_id,)).fetchone()
        if not row:
            flash("المبيعة غير موجودة.", "error")
            return redirect(url_for("batches"))
        batch_id = row["batch_id"]
        conn.execute("DELETE FROM farm_sales WHERE id=?", (sale_id,))
        conn.commit()
    recalc_batch(batch_id)
    flash("تم حذف مبيعة العنبر.", "success")
    return redirect(url_for("farm_sales", batch_id=batch_id))


@app.route("/batches/<int:batch_id>/market-sales", methods=["GET", "POST"])
def market_sales(batch_id: int):
    if request.method == "POST":
        qty_sent = to_int(request.form.get("qty_sent"))
        deaths = to_int(request.form.get("deaths"))
        qty_sold = to_int(request.form.get("qty_sold"), max(0, qty_sent - deaths))
        with get_conn() as conn:
            conn.execute(
                """
                INSERT INTO market_sales(batch_id, sale_date, office, qty_sent, deaths, qty_sold, net_val, inv_num)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    batch_id,
                    request.form.get("sale_date", "").strip(),
                    request.form.get("office", "").strip(),
                    qty_sent,
                    deaths,
                    qty_sold,
                    to_float(request.form.get("net_val")),
                    request.form.get("inv_num", "").strip(),
                ),
            )
            conn.commit()
        recalc_batch(batch_id)
        flash("تم حفظ مبيعة السوق.", "success")
        return redirect(url_for("market_sales", batch_id=batch_id))

    with get_conn() as conn:
        batch = conn.execute("SELECT id, batch_num FROM batches WHERE id=?", (batch_id,)).fetchone()
        rows = conn.execute("SELECT * FROM market_sales WHERE batch_id=? ORDER BY id DESC", (batch_id,)).fetchall()
    return render_template("market_sales.html", batch=batch, rows=rows)


@app.get("/batches/<int:batch_id>/market-sales/export.csv")
def export_market_sales_csv(batch_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT sale_date, office, qty_sent, deaths, qty_sold, net_val, inv_num
            FROM market_sales
            WHERE batch_id=?
            ORDER BY id DESC
            """,
            (batch_id,),
        ).fetchall()
    payload = [
        [r["sale_date"], r["office"] or "", r["qty_sent"], r["deaths"], r["qty_sold"], r["net_val"], r["inv_num"] or ""]
        for r in rows
    ]
    return make_csv_response(
        f"batch_{batch_id}_market_sales.csv",
        ["sale_date", "office", "qty_sent", "deaths", "qty_sold", "net_val", "inv_num"],
        payload,
    )


@app.get("/batches/<int:batch_id>/market-sales/export.xlsx")
def export_market_sales_excel(batch_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT sale_date, office, qty_sent, deaths, qty_sold, net_val, inv_num
            FROM market_sales
            WHERE batch_id=?
            ORDER BY id DESC
            """,
            (batch_id,),
        ).fetchall()
    payload = [
        [r["sale_date"], r["office"] or "", r["qty_sent"], r["deaths"], r["qty_sold"], r["net_val"], r["inv_num"] or ""]
        for r in rows
    ]
    return make_excel_response(
        f"batch_{batch_id}_market_sales.xlsx",
        "MarketSales",
        ["sale_date", "office", "qty_sent", "deaths", "qty_sold", "net_val", "inv_num"],
        payload,
    )


@app.post("/market-sales/<int:sale_id>/delete")
def delete_market_sale(sale_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT batch_id FROM market_sales WHERE id=?", (sale_id,)).fetchone()
        if not row:
            flash("المبيعة غير موجودة.", "error")
            return redirect(url_for("batches"))
        batch_id = row["batch_id"]
        conn.execute("DELETE FROM market_sales WHERE id=?", (sale_id,))
        conn.commit()
    recalc_batch(batch_id)
    flash("تم حذف مبيعة السوق.", "success")
    return redirect(url_for("market_sales", batch_id=batch_id))


@app.route("/batches/<int:batch_id>/costs", methods=["GET", "POST"])
def batch_costs(batch_id: int):
    if request.method == "POST":
        with get_conn() as conn:
            types = conn.execute("SELECT * FROM cost_types WHERE is_active=1 ORDER BY sort_order").fetchall()
            for t in types:
                qty = to_float(request.form.get(f"qty_{t['id']}"), 0.0)
                amount = to_float(request.form.get(f"amount_{t['id']}"), 0.0)
                if qty == 0 and amount == 0:
                    conn.execute("DELETE FROM batch_costs WHERE batch_id=? AND cost_type_id=?", (batch_id, t["id"]))
                else:
                    conn.execute(
                        """
                        INSERT INTO batch_costs(batch_id,cost_type_id,qty,amount)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(batch_id,cost_type_id)
                        DO UPDATE SET qty=excluded.qty, amount=excluded.amount
                        """,
                        (batch_id, t["id"], qty, amount),
                    )
            conn.commit()
        recalc_batch(batch_id)
        flash("تم تحديث التكاليف.", "success")
        return redirect(url_for("batch_costs", batch_id=batch_id))

    with get_conn() as conn:
        batch = conn.execute("SELECT id, batch_num FROM batches WHERE id=?", (batch_id,)).fetchone()
        types = conn.execute("SELECT * FROM cost_types WHERE is_active=1 ORDER BY sort_order").fetchall()
        values = {
            row["cost_type_id"]: row
            for row in conn.execute("SELECT * FROM batch_costs WHERE batch_id=?", (batch_id,)).fetchall()
        }
    return render_template("batch_costs.html", batch=batch, types=types, values=values)


@app.get("/batches/<int:batch_id>/costs/export.csv")
def export_batch_costs_csv(batch_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT ct.code, ct.name_ar, ct.category, COALESCE(bc.qty, 0) AS qty, COALESCE(bc.amount, 0) AS amount
            FROM cost_types ct
            LEFT JOIN batch_costs bc ON bc.cost_type_id = ct.id AND bc.batch_id = ?
            WHERE ct.is_active = 1
            ORDER BY ct.sort_order
            """,
            (batch_id,),
        ).fetchall()
    payload = [[r["code"], r["name_ar"], r["category"], r["qty"], r["amount"]] for r in rows]
    return make_csv_response(
        f"batch_{batch_id}_costs.csv",
        ["code", "name_ar", "category", "qty", "amount"],
        payload,
    )


@app.get("/batches/<int:batch_id>/costs/export.xlsx")
def export_batch_costs_excel(batch_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT ct.code, ct.name_ar, ct.category, COALESCE(bc.qty, 0) AS qty, COALESCE(bc.amount, 0) AS amount
            FROM cost_types ct
            LEFT JOIN batch_costs bc ON bc.cost_type_id = ct.id AND bc.batch_id = ?
            WHERE ct.is_active = 1
            ORDER BY ct.sort_order
            """,
            (batch_id,),
        ).fetchall()
    payload = [[r["code"], r["name_ar"], r["category"], r["qty"], r["amount"]] for r in rows]
    return make_excel_response(
        f"batch_{batch_id}_costs.xlsx",
        "Costs",
        ["code", "name_ar", "category", "qty", "amount"],
        payload,
    )


@app.route("/batches/<int:batch_id>/revenues", methods=["GET", "POST"])
def batch_revenues(batch_id: int):
    if request.method == "POST":
        with get_conn() as conn:
            types = conn.execute("SELECT * FROM revenue_types WHERE is_active=1 ORDER BY sort_order").fetchall()
            for t in types:
                qty = to_float(request.form.get(f"qty_{t['id']}"), 0.0)
                amount = to_float(request.form.get(f"amount_{t['id']}"), 0.0)
                if qty == 0 and amount == 0:
                    conn.execute("DELETE FROM batch_revenues WHERE batch_id=? AND revenue_type_id=?", (batch_id, t["id"]))
                else:
                    conn.execute(
                        """
                        INSERT INTO batch_revenues(batch_id,revenue_type_id,qty,amount)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(batch_id,revenue_type_id)
                        DO UPDATE SET qty=excluded.qty, amount=excluded.amount
                        """,
                        (batch_id, t["id"], qty, amount),
                    )
            conn.commit()
        recalc_batch(batch_id)
        flash("تم تحديث الإيرادات.", "success")
        return redirect(url_for("batch_revenues", batch_id=batch_id))

    with get_conn() as conn:
        batch = conn.execute("SELECT id, batch_num FROM batches WHERE id=?", (batch_id,)).fetchone()
        types = conn.execute("SELECT * FROM revenue_types WHERE is_active=1 ORDER BY sort_order").fetchall()
        values = {
            row["revenue_type_id"]: row
            for row in conn.execute("SELECT * FROM batch_revenues WHERE batch_id=?", (batch_id,)).fetchall()
        }
    return render_template("batch_revenues.html", batch=batch, types=types, values=values)


@app.get("/batches/<int:batch_id>/revenues/export.csv")
def export_batch_revenues_csv(batch_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT rt.code, rt.name_ar, rt.category, COALESCE(br.qty, 0) AS qty, COALESCE(br.amount, 0) AS amount
            FROM revenue_types rt
            LEFT JOIN batch_revenues br ON br.revenue_type_id = rt.id AND br.batch_id = ?
            WHERE rt.is_active = 1
            ORDER BY rt.sort_order
            """,
            (batch_id,),
        ).fetchall()
    payload = [[r["code"], r["name_ar"], r["category"], r["qty"], r["amount"]] for r in rows]
    return make_csv_response(
        f"batch_{batch_id}_revenues.csv",
        ["code", "name_ar", "category", "qty", "amount"],
        payload,
    )


@app.get("/batches/<int:batch_id>/revenues/export.xlsx")
def export_batch_revenues_excel(batch_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT rt.code, rt.name_ar, rt.category, COALESCE(br.qty, 0) AS qty, COALESCE(br.amount, 0) AS amount
            FROM revenue_types rt
            LEFT JOIN batch_revenues br ON br.revenue_type_id = rt.id AND br.batch_id = ?
            WHERE rt.is_active = 1
            ORDER BY rt.sort_order
            """,
            (batch_id,),
        ).fetchall()
    payload = [[r["code"], r["name_ar"], r["category"], r["qty"], r["amount"]] for r in rows]
    return make_excel_response(
        f"batch_{batch_id}_revenues.xlsx",
        "Revenues",
        ["code", "name_ar", "category", "qty", "amount"],
        payload,
    )


@app.route("/reports")
def reports():
    warehouse_id = to_int(request.args.get("warehouse_id"), 0) or None
    fiscal_year = to_int(request.args.get("fiscal_year"), 0) or None
    data = reports_payload(warehouse_id, fiscal_year)

    return render_template(
        "reports.html",
        warehouse_rows=data["warehouse_rows"],
        annual_rows=data["annual_rows"],
        batches_rows=data["batches_rows"],
        sales_by_type_rows=data["sales_by_type_rows"],
        market_summary_row=data["market_summary_row"],
        cost_types_rows=data["cost_types_rows"],
        revenue_types_rows=data["revenue_types_rows"],
        daily_summary_row=data["daily_summary_row"],
        warehouses=data["warehouses"],
        years=data["years"],
        filters={"warehouse_id": warehouse_id or "", "fiscal_year": fiscal_year or ""},
        report_summary=data["report_summary"],
        dashboard_insights=data["dashboard_insights"],
    )


def build_reports_export_payload(
    report_type: str,
    data: dict[str, object],
    where_clause: str,
    params: list[int],
) -> tuple[str, str, list[str], list[list[object]]]:
    if report_type == "warehouses":
        rows = data["warehouse_rows"]
        export_rows = [
            [
                row["warehouse_name"],
                row["batches_count"],
                row["chicks_total"],
                row["cost_total"],
                row["revenue_total"],
                row["net_total"],
                row["avg_mortality"],
            ]
            for row in rows
        ]
        return (
            "warehouses_summary",
            "Warehouses",
            ["warehouse_name", "batches_count", "chicks_total", "cost_total", "revenue_total", "net_total", "avg_mortality"],
            export_rows,
        )

    if report_type == "annual":
        rows = data["annual_rows"]
        export_rows = [
            [
                row["fiscal_year"],
                row["batches_count"],
                row["cost_total"],
                row["revenue_total"],
                row["net_total"],
            ]
            for row in rows
        ]
        return (
            "annual_summary",
            "Annual",
            ["fiscal_year", "batches_count", "cost_total", "revenue_total", "net_total"],
            export_rows,
        )

    if report_type == "batches":
        with get_conn() as conn:
            rows = conn.execute(
                f"""
                SELECT b.id, b.batch_num, w.name AS warehouse_name, b.date_in, b.date_out,
                       b.chicks, b.total_dead, b.mort_rate, b.fcr, b.total_cost, b.total_rev, b.net_result
                FROM batches b
                JOIN warehouses w ON w.id=b.warehouse_id
                {where_clause}
                ORDER BY b.date_in DESC, b.id DESC
                """,
                params,
            ).fetchall()
        export_rows = [
            [
                row["id"],
                row["batch_num"],
                row["warehouse_name"],
                row["date_in"],
                row["date_out"],
                row["chicks"],
                row["total_dead"],
                row["mort_rate"],
                row["fcr"],
                row["total_cost"],
                row["total_rev"],
                row["net_result"],
            ]
            for row in rows
        ]
        return (
            "batches_report",
            "Batches",
            [
                "id",
                "batch_num",
                "warehouse_name",
                "date_in",
                "date_out",
                "chicks",
                "total_dead",
                "mort_rate",
                "fcr",
                "total_cost",
                "total_rev",
                "net_result",
            ],
            export_rows,
        )

    if report_type == "sales_types":
        rows = data["sales_by_type_rows"]
        export_rows = [[row["sale_type"], row["qty_total"], row["amount_total"]] for row in rows]
        return ("sales_by_type", "SalesTypes", ["sale_type", "qty_total", "amount_total"], export_rows)

    if report_type == "cost_types":
        rows = data["cost_types_rows"]
        export_rows = [[row["type_name"], row["category"], row["qty_total"], row["amount_total"]] for row in rows]
        return ("cost_types_summary", "CostTypes", ["type_name", "category", "qty_total", "amount_total"], export_rows)

    if report_type == "revenue_types":
        rows = data["revenue_types_rows"]
        export_rows = [[row["type_name"], row["category"], row["qty_total"], row["amount_total"]] for row in rows]
        return ("revenue_types_summary", "RevenueTypes", ["type_name", "category", "qty_total", "amount_total"], export_rows)

    if report_type == "daily_summary":
        row = data["daily_summary_row"]
        export_rows = [[row["entries_count"], row["dead_total"], row["feed_total"], row["water_total"], row["avg_daily_deaths"]]]
        return (
            "daily_summary",
            "DailySummary",
            ["entries_count", "dead_total", "feed_total", "water_total", "avg_daily_deaths"],
            export_rows,
        )

    raise ValueError("unsupported")


@app.get("/reports/export/<string:report_type>.csv")
def export_reports_csv(report_type: str):
    warehouse_id = to_int(request.args.get("warehouse_id"), 0) or None
    fiscal_year = to_int(request.args.get("fiscal_year"), 0) or None
    data = reports_payload(warehouse_id, fiscal_year)
    where_clause = data["where_clause"]
    params = data["params"]

    try:
        filename_base, _, headers, export_rows = build_reports_export_payload(report_type, data, where_clause, params)
    except ValueError:
        flash("Unsupported report type.", "error")
        return redirect(url_for("reports"))
    return make_csv_response(f"{filename_base}.csv", headers, export_rows)


@app.get("/reports/export/<string:report_type>.xlsx")
def export_reports_excel(report_type: str):
    warehouse_id = to_int(request.args.get("warehouse_id"), 0) or None
    fiscal_year = to_int(request.args.get("fiscal_year"), 0) or None
    data = reports_payload(warehouse_id, fiscal_year)
    where_clause = data["where_clause"]
    params = data["params"]

    try:
        filename_base, sheet_name, headers, export_rows = build_reports_export_payload(report_type, data, where_clause, params)
    except ValueError:
        flash("Unsupported report type.", "error")
        return redirect(url_for("reports"))
    return make_excel_response(f"{filename_base}.xlsx", sheet_name, headers, export_rows)


def build_report_chart_images(data: dict[str, object]) -> list[str]:
    if not HAS_MATPLOTLIB:
        return []

    chart_paths: list[str] = []
    try:
        insights = data.get("dashboard_insights", {})
        warehouse_rows = list(data.get("warehouse_rows", []))
        cost_types_rows = list(data.get("cost_types_rows", []))

        warehouse_labels = [str(r.get("warehouse_name") or "Unknown") for r in warehouse_rows[:8]]
        warehouse_costs = [float(r.get("cost_total") or 0) for r in warehouse_rows[:8]]
        warehouse_revenues = [float(r.get("revenue_total") or 0) for r in warehouse_rows[:8]]

        if warehouse_labels:
            fig, ax = plt.subplots(figsize=(8.5, 3.2))
            x = list(range(len(warehouse_labels)))
            ax.bar([i - 0.2 for i in x], warehouse_costs, width=0.4, label="Costs")
            ax.bar([i + 0.2 for i in x], warehouse_revenues, width=0.4, label="Revenues")
            ax.set_title("Warehouse Financial Comparison")
            ax.set_xticks(x)
            ax.set_xticklabels(warehouse_labels, rotation=20, ha="right")
            ax.legend()
            ax.grid(axis="y", alpha=0.2)
            fig.tight_layout()
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            fig.savefig(tmp.name, dpi=150)
            plt.close(fig)
            chart_paths.append(tmp.name)

        rev_vals = [
            float(insights.get("farm_sales_total") or 0),
            float(insights.get("market_sales_total") or 0),
            float(insights.get("extra_revenues_total") or 0),
        ]
        if sum(rev_vals) > 0:
            fig, ax = plt.subplots(figsize=(8.5, 3.2))
            ax.pie(rev_vals, labels=["Farm", "Market", "Extra"], autopct="%1.1f%%", startangle=90)
            ax.set_title("Revenue Split")
            fig.tight_layout()
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            fig.savefig(tmp.name, dpi=150)
            plt.close(fig)
            chart_paths.append(tmp.name)

        top_cost = cost_types_rows[:8]
        if top_cost:
            labels = [str(r.get("type_name") or "N/A") for r in top_cost]
            vals = [float(r.get("amount_total") or 0) for r in top_cost]
            fig, ax = plt.subplots(figsize=(8.5, 3.2))
            ax.plot(labels, vals, marker="o")
            ax.fill_between(range(len(vals)), vals, alpha=0.15)
            ax.set_title("Top Cost Types")
            ax.tick_params(axis="x", rotation=25)
            ax.grid(axis="y", alpha=0.2)
            fig.tight_layout()
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            fig.savefig(tmp.name, dpi=150)
            plt.close(fig)
            chart_paths.append(tmp.name)
    except Exception:
        return chart_paths

    return chart_paths


@app.get("/reports/export/report.pdf")
def export_reports_pdf():
    if not HAS_FPDF:
        flash("PDF library is not available in this environment.", "error")
        return redirect(url_for("reports"))

    warehouse_id = to_int(request.args.get("warehouse_id"), 0) or None
    fiscal_year = to_int(request.args.get("fiscal_year"), 0) or None
    include_dashboard = request.args.get("include_dashboard", "1") == "1"
    data = reports_payload(warehouse_id, fiscal_year)

    pdf = FPDF()
    pdf.add_page()
    has_arabic_font = REPORT_FONT_PATH.exists()
    if has_arabic_font:
        pdf.add_font("Arabic", "", str(REPORT_FONT_PATH), uni=True)
        pdf.set_font("Arabic", "", 13)
    else:
        pdf.set_font("Arial", "", 12)

    company_name = get_setting("company_name", "Poultry Company")
    pdf.cell(0, 8, ar_text(f"{company_name} - Executive Report"), new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Arabic" if has_arabic_font else "Arial", "", 10)
    pdf.cell(
        0,
        7,
        ar_text(
            f"Report date: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Warehouse filter: {warehouse_id or 'All'} | Fiscal year: {fiscal_year or 'All'}"
        ),
        new_x="LMARGIN",
        new_y="NEXT",
        align="C",
    )
    pdf.ln(3)

    summary = data["report_summary"]
    chart_paths: list[str] = []
    if include_dashboard:
        pdf.set_font("Arabic" if has_arabic_font else "Arial", "", 11)
        pdf.cell(0, 7, ar_text("Dashboard Metrics"), new_x="LMARGIN", new_y="NEXT", align="R")
        pdf.set_font("Arabic" if has_arabic_font else "Arial", "", 10)
        insights = data["dashboard_insights"]
        kpis = [
            f"Total costs: {summary['cost_total']:,.2f}",
            f"Total revenues: {summary['revenue_total']:,.2f}",
            f"Net result: {summary['net_total']:,.2f}",
            f"Profit margin: {insights['margin_pct']:.2f}%",
            f"Average FCR: {insights['avg_fcr']:.3f}",
            f"Average mortality: {insights['avg_mortality']:.2f}%",
            f"Farm sales: {insights['farm_sales_total']:,.2f}",
            f"Market sales: {insights['market_sales_total']:,.2f}",
            f"Extra revenues: {insights['extra_revenues_total']:,.2f}",
        ]
        for line in kpis:
            pdf.cell(0, 6, ar_text(line), new_x="LMARGIN", new_y="NEXT", align="R")

        chart_paths = build_report_chart_images(data)
        for chart_path in chart_paths:
            if pdf.get_y() > 220:
                pdf.add_page()
            pdf.ln(2)
            pdf.image(chart_path, x=12, y=pdf.get_y(), w=185)
            pdf.ln(58)

    pdf.ln(3)
    pdf.set_font("Arabic" if has_arabic_font else "Arial", "", 11)
    pdf.cell(0, 7, ar_text("Warehouse Summary"), new_x="LMARGIN", new_y="NEXT", align="R")
    pdf.set_font("Arabic" if has_arabic_font else "Arial", "", 9)
    headers = ["Warehouse", "Batches", "Costs", "Revenues", "Net"]
    widths = [54, 20, 35, 35, 35]
    for h, w in zip(headers, widths):
        pdf.cell(w, 7, ar_text(h), border=1, align="C")
    pdf.ln()
    for row in data["warehouse_rows"]:
        vals = [
            row["warehouse_name"],
            f"{int(row['batches_count'] or 0)}",
            f"{float(row['cost_total'] or 0):,.0f}",
            f"{float(row['revenue_total'] or 0):,.0f}",
            f"{float(row['net_total'] or 0):,.0f}",
        ]
        for v, w in zip(vals, widths):
            pdf.cell(w, 6, ar_text(v), border=1, align="C")
        pdf.ln()

    pdf.ln(3)
    pdf.set_font("Arabic" if has_arabic_font else "Arial", "", 11)
    pdf.cell(0, 7, ar_text("Top 25 Batches"), new_x="LMARGIN", new_y="NEXT", align="R")
    pdf.set_font("Arabic" if has_arabic_font else "Arial", "", 9)
    headers = ["Batch", "Warehouse", "Date In", "Date Out", "FCR", "Net"]
    widths = [20, 45, 30, 30, 20, 34]
    for h, w in zip(headers, widths):
        pdf.cell(w, 7, ar_text(h), border=1, align="C")
    pdf.ln()
    for row in data["batches_rows"]:
        vals = [
            row.get("batch_num") or row.get("id"),
            row.get("warehouse_name"),
            row.get("date_in"),
            row.get("date_out"),
            f"{float(row.get('fcr') or 0):.3f}",
            f"{float(row.get('net_result') or 0):,.0f}",
        ]
        for v, w in zip(vals, widths):
            pdf.cell(w, 6, ar_text(v), border=1, align="C")
        pdf.ln()

    out = pdf.output(dest="S")
    pdf_bytes = out.encode("latin-1") if isinstance(out, str) else bytes(out)
    suffix = "with_dashboard" if include_dashboard else "without_dashboard"
    filename = f"reports_{suffix}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"

    for chart_path in chart_paths:
        try:
            os.unlink(chart_path)
        except Exception:
            pass

    return make_pdf_response(filename, pdf_bytes)


@app.route("/settings", methods=["GET", "POST"])
def settings():
    keys = [
        ("company_name", "اسم الشركة", "شركة الدواجن"),
        ("farm_address", "العنوان", ""),
        ("contact_number", "رقم التواصل", ""),
        ("currency", "العملة", "ريال"),
        ("manager_name", "المدير العام", ""),
        ("finance_name", "المدير المالي", ""),
        ("auditor_name", "المراجع", ""),
        ("tg_token", "Telegram Bot Token", ""),
        ("tg_chat_id", "Telegram Chat ID", ""),
        ("tg_auto", "التفعيل التلقائي", "0"),
    ]

    if request.method == "POST":
        for key, _, default in keys:
            value = request.form.get(key, default).strip()
            set_setting(key, value)
        flash("تم حفظ الإعدادات.", "success")
        return redirect(url_for("settings"))

    values = {key: get_setting(key, default) for key, _, default in keys}
    return render_template("settings.html", values=values)


@app.post("/settings/backup")
def create_backup():
    backup_path = create_database_backup()
    flash(f"تم إنشاء نسخة احتياطية: {backup_path}", "success")
    return redirect(url_for("settings"))


def create_app() -> Flask:
    shared_ensure_schema()
    return app


if __name__ == "__main__":
    shared_ensure_schema()
    debug_mode = os.environ.get("POULTRY_WEB_DEBUG", "0") == "1"
    app.run(host="127.0.0.1", port=5000, debug=debug_mode)
