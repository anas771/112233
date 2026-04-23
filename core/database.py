from __future__ import annotations

import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "poultry_data.db"

SCHEMA_SQL = """
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
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    warehouse_id     INTEGER NOT NULL REFERENCES warehouses(id),
    batch_num        TEXT    DEFAULT '',
    date_in          TEXT    NOT NULL,
    date_out         TEXT    NOT NULL,
    days             INTEGER DEFAULT 0,
    chicks           INTEGER NOT NULL,
    chick_price      REAL    DEFAULT 0,
    chick_val        REAL    DEFAULT 0,
    feed_qty         REAL    DEFAULT 0,
    feed_val         REAL    DEFAULT 0,
    feed_trans       REAL    DEFAULT 0,
    sawdust_qty      REAL    DEFAULT 0,
    sawdust_val      REAL    DEFAULT 0,
    water_val        REAL    DEFAULT 0,
    gas_qty          REAL    DEFAULT 0,
    gas_val          REAL    DEFAULT 0,
    drugs_val        REAL    DEFAULT 0,
    wh_expenses      REAL    DEFAULT 0,
    house_exp        REAL    DEFAULT 0,
    breeders_pay     REAL    DEFAULT 0,
    qat_pay          REAL    DEFAULT 0,
    rent_val         REAL    DEFAULT 0,
    light_val        REAL    DEFAULT 0,
    sup_wh_pay       REAL    DEFAULT 0,
    sup_co_pay       REAL    DEFAULT 0,
    sup_sale_pay     REAL    DEFAULT 0,
    admin_val        REAL    DEFAULT 0,
    vaccine_pay      REAL    DEFAULT 0,
    delivery_val     REAL    DEFAULT 0,
    mixing_val       REAL    DEFAULT 0,
    wash_val         REAL    DEFAULT 0,
    other_costs      REAL    DEFAULT 0,
    total_cost       REAL    DEFAULT 0,
    cust_qty         INTEGER DEFAULT 0,
    cust_val         REAL    DEFAULT 0,
    mkt_qty          INTEGER DEFAULT 0,
    mkt_val          REAL    DEFAULT 0,
    offal_val        REAL    DEFAULT 0,
    feed_sale        REAL    DEFAULT 0,
    feed_trans_r     REAL    DEFAULT 0,
    drug_return      REAL    DEFAULT 0,
    gas_return       REAL    DEFAULT 0,
    total_rev        REAL    DEFAULT 0,
    total_sold       INTEGER DEFAULT 0,
    total_dead       INTEGER DEFAULT 0,
    mort_rate        REAL    DEFAULT 0,
    avg_weight       REAL    DEFAULT 0,
    fcr              REAL    DEFAULT 0,
    avg_price        REAL    DEFAULT 0,
    net_result       REAL    DEFAULT 0,
    share_pct        REAL    DEFAULT 65,
    share_val        REAL    DEFAULT 0,
    notes            TEXT    DEFAULT '',
    created_at       TEXT,
    consumed_birds   INTEGER DEFAULT 0,
    partner_name     TEXT    DEFAULT '',
    feed_sale_qty    REAL    DEFAULT 0,
    feed_trans_r_qty REAL    DEFAULT 0,
    feed_rem_qty     REAL    DEFAULT 0,
    feed_rem_val     REAL    DEFAULT 0,
    fiscal_year      INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS daily_records (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id   INTEGER NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
    rec_date   TEXT    NOT NULL,
    day_num    INTEGER DEFAULT 0,
    dead_count INTEGER DEFAULT 0,
    feed_kg    REAL    DEFAULT 0,
    water_ltr  REAL    DEFAULT 0,
    notes      TEXT    DEFAULT '',
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

CREATE TABLE IF NOT EXISTS batch_standards (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id   INTEGER NOT NULL UNIQUE REFERENCES batches(id) ON DELETE CASCADE,
    target_fcr REAL DEFAULT 1.8,
    mort_w1    REAL DEFAULT 0.15,
    mort_w2    REAL DEFAULT 0.08,
    mort_w3    REAL DEFAULT 0.06,
    mort_w4    REAL DEFAULT 0.05,
    mort_w5    REAL DEFAULT 0.05,
    mort_w6    REAL DEFAULT 0.05,
    mort_w7    REAL DEFAULT 0.05,
    mort_w8    REAL DEFAULT 0.05,
    feed_w1    REAL DEFAULT 20,
    feed_w2    REAL DEFAULT 45,
    feed_w3    REAL DEFAULT 80,
    feed_w4    REAL DEFAULT 115,
    feed_w5    REAL DEFAULT 145,
    feed_w6    REAL DEFAULT 165,
    feed_w7    REAL DEFAULT 175,
    feed_w8    REAL DEFAULT 180
);

CREATE TABLE IF NOT EXISTS batch_daily_standards (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
    day_num  INTEGER NOT NULL,
    mort_std REAL DEFAULT 0.05,
    feed_std REAL DEFAULT 100,
    UNIQUE(batch_id, day_num)
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

DEFAULT_COST_TYPES = [
    ("chick_val", "الكتاكيت", "مواد", 1, "حبة", 1),
    ("feed_val", "العلف", "مواد", 1, "طن", 2),
    ("feed_trans", "أجور نقل علف", "نقل", 0, None, 3),
    ("sawdust_val", "النشارة", "مواد", 1, "م³", 4),
    ("water_val", "الماء", "مرافق", 0, None, 5),
    ("gas_val", "الغاز", "مرافق", 1, "أسطوانة", 6),
    ("drugs_val", "علاجات وأدوية", "صحة", 0, None, 7),
    ("wh_expenses", "مصاريف عنبر", "تشغيل", 0, None, 8),
    ("house_exp", "مصاريف بيت", "تشغيل", 0, None, 9),
    ("breeders_pay", "أجور مربيين", "رواتب", 0, None, 10),
    ("qat_pay", "قات مربيين", "رواتب", 0, None, 11),
    ("rent_val", "إيجار عنبر", "عقارات", 0, None, 12),
    ("light_val", "إضاءة وكهرباء", "مرافق", 0, None, 13),
    ("sup_wh_pay", "مشرف عنبر", "إشراف", 0, None, 14),
    ("sup_co_pay", "مشرف شركة", "إشراف", 0, None, 15),
    ("sup_sale_pay", "مشرف بيع", "إشراف", 0, None, 16),
    ("admin_val", "إدارة وحسابات", "إدارة", 0, None, 17),
    ("vaccine_pay", "أجور لقاحات", "صحة", 0, None, 18),
    ("delivery_val", "توصيل خدمات", "أخرى", 0, None, 19),
    ("mixing_val", "حمالة وخلط", "أخرى", 0, None, 20),
    ("wash_val", "تغسيل عنبر", "أخرى", 0, None, 21),
    ("other_costs", "مصاريف أخرى", "أخرى", 0, None, 22),
]

DEFAULT_REVENUE_TYPES = [
    ("offal_val", "مبيعات ذبيل", "مبيعات", 0, None, 1),
    ("feed_sale", "مبيعات علف", "مبيعات", 1, "كيس", 2),
    ("feed_trans_r", "علف منقول لعنابر", "تحويل", 1, "كيس", 3),
    ("feed_rem_val", "علف متبقي", "مخزون", 1, "كيس", 4),
    ("drug_return", "مرتجع علاجات", "مرتجعات", 0, None, 5),
    ("gas_return", "نقل غاز/نشارة", "مرتجعات", 0, None, 6),
]

LEGACY_BATCH_COLUMNS = [
    ("fcr", "REAL DEFAULT 0"),
    ("avg_weight", "REAL DEFAULT 0"),
    ("batch_num", "TEXT DEFAULT ''"),
    ("consumed_birds", "INTEGER DEFAULT 0"),
    ("partner_name", "TEXT DEFAULT ''"),
    ("feed_sale_qty", "REAL DEFAULT 0"),
    ("feed_trans_r_qty", "REAL DEFAULT 0"),
    ("feed_rem_qty", "REAL DEFAULT 0"),
    ("feed_rem_val", "REAL DEFAULT 0"),
    ("fiscal_year", "INTEGER DEFAULT 0"),
]


def get_conn(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def execute_script(script: str, db_path: Path = DB_PATH) -> None:
    with get_conn(db_path) as conn:
        conn.executescript(script)


def execute(query: str, params: tuple[object, ...] = (), db_path: Path = DB_PATH) -> int:
    with get_conn(db_path) as conn:
        cursor = conn.execute(query, params)
        conn.commit()
        return cursor.lastrowid


def fetch_one(query: str, params: tuple[object, ...] = (), db_path: Path = DB_PATH) -> sqlite3.Row | None:
    with get_conn(db_path) as conn:
        return conn.execute(query, params).fetchone()


def get_setting(key: str, default: str = "", db_path: Path = DB_PATH) -> str:
    row = fetch_one("SELECT value FROM system_settings WHERE key=?", (key,), db_path)
    return row["value"] if row else default


def set_setting(key: str, value: str, db_path: Path = DB_PATH) -> None:
    execute(
        """
        INSERT INTO system_settings (key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value
        """,
        (key, value),
        db_path,
    )


def ensure_schema(db_path: Path = DB_PATH) -> None:
    execute_script(SCHEMA_SQL, db_path)
    for column_name, column_type in LEGACY_BATCH_COLUMNS:
        _ensure_column("batches", column_name, column_type, db_path)
    _ensure_column("farm_sales", "sale_type", "TEXT DEFAULT 'آجل'", db_path)
    _ensure_column("farm_sales", "sale_date", "TEXT DEFAULT ''", db_path)
    _ensure_column("market_sales", "sale_date", "TEXT DEFAULT ''", db_path)
    _seed_cost_types(db_path)
    _seed_revenue_types(db_path)
    _create_views(db_path)
    _create_indexes(db_path)


def _ensure_column(table_name: str, column_name: str, column_type: str, db_path: Path) -> None:
    try:
        execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}", db_path=db_path)
    except sqlite3.OperationalError:
        pass


def _seed_cost_types(db_path: Path) -> None:
    with get_conn(db_path) as conn:
        conn.executemany(
            """
            INSERT OR IGNORE INTO cost_types(code, name_ar, category, has_qty, unit, sort_order)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            DEFAULT_COST_TYPES,
        )
        conn.commit()


def _seed_revenue_types(db_path: Path) -> None:
    with get_conn(db_path) as conn:
        conn.executemany(
            """
            INSERT OR IGNORE INTO revenue_types(code, name_ar, category, has_qty, unit, sort_order)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            DEFAULT_REVENUE_TYPES,
        )
        conn.commit()


def _create_views(db_path: Path) -> None:
    execute_script(
        """
        DROP VIEW IF EXISTS v_batches;
        CREATE VIEW v_batches AS
            SELECT b.*, w.name AS warehouse_name,
                   COALESCE(b.fiscal_year, CAST(strftime('%Y', b.date_in) AS INTEGER)) AS fy
            FROM batches b
            JOIN warehouses w ON b.warehouse_id = w.id;

        DROP VIEW IF EXISTS v_batch_costs_summary;
        CREATE VIEW v_batch_costs_summary AS
            SELECT bc.batch_id, ct.code, ct.name_ar, ct.category,
                   ct.has_qty, ct.unit, bc.qty, bc.amount, ct.sort_order
            FROM batch_costs bc
            JOIN cost_types ct ON bc.cost_type_id = ct.id;

        DROP VIEW IF EXISTS v_batch_revenues_summary;
        CREATE VIEW v_batch_revenues_summary AS
            SELECT br.batch_id, rt.code, rt.name_ar, rt.category,
                   rt.has_qty, rt.unit, br.qty, br.amount, rt.sort_order
            FROM batch_revenues br
            JOIN revenue_types rt ON br.revenue_type_id = rt.id;
        """,
        db_path,
    )


def _create_indexes(db_path: Path) -> None:
    execute_script(
        """
        CREATE INDEX IF NOT EXISTS idx_batches_warehouse ON batches(warehouse_id);
        CREATE INDEX IF NOT EXISTS idx_batches_fiscal_year ON batches(fiscal_year);
        CREATE INDEX IF NOT EXISTS idx_batches_date_in ON batches(date_in);
        CREATE INDEX IF NOT EXISTS idx_daily_records_batch_date ON daily_records(batch_id, rec_date);
        CREATE INDEX IF NOT EXISTS idx_farm_sales_batch_date ON farm_sales(batch_id, sale_date);
        CREATE INDEX IF NOT EXISTS idx_market_sales_batch_date ON market_sales(batch_id, sale_date);
        CREATE INDEX IF NOT EXISTS idx_batch_costs_batch ON batch_costs(batch_id);
        CREATE INDEX IF NOT EXISTS idx_batch_revenues_batch ON batch_revenues(batch_id);
        """,
        db_path,
    )
