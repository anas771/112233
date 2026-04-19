import sqlite3
import os

class DBManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self._init_db()

    def get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def execute_script(self, script):
        conn = self.get_conn()
        try:
            with conn:
                conn.executescript(script)
        finally:
            conn.close()

    def fetch_all(self, query, params=()):
        conn = self.get_conn()
        try:
            return conn.execute(query, params).fetchall()
        finally:
            conn.close()

    def fetch_one(self, query, params=()):
        conn = self.get_conn()
        try:
            return conn.execute(query, params).fetchone()
        finally:
            conn.close()

    def execute(self, query, params=()):
        with self.get_conn() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.lastrowid

    def _init_db(self):
        self.execute_script("""
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS warehouses (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            name TEXT NOT NULL UNIQUE, 
            notes TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        CREATE TABLE IF NOT EXISTS batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
            batch_num TEXT DEFAULT '',
            date_in TEXT NOT NULL, 
            date_out TEXT NOT NULL, 
            days INTEGER,
            chicks INTEGER NOT NULL, 
            chick_price REAL DEFAULT 0, 
            chick_val REAL DEFAULT 0,
            feed_qty REAL DEFAULT 0, 
            feed_val REAL DEFAULT 0, 
            feed_trans REAL DEFAULT 0,
            sawdust_qty REAL DEFAULT 0, 
            sawdust_val REAL DEFAULT 0, 
            water_val REAL DEFAULT 0,
            gas_qty REAL DEFAULT 0, 
            gas_val REAL DEFAULT 0, 
            drugs_val REAL DEFAULT 0,
            wh_expenses REAL DEFAULT 0, 
            house_exp REAL DEFAULT 0, 
            breeders_pay REAL DEFAULT 0,
            qat_pay REAL DEFAULT 0, 
            rent_val REAL DEFAULT 0, 
            light_val REAL DEFAULT 0,
            sup_wh_pay REAL DEFAULT 0, 
            sup_co_pay REAL DEFAULT 0, 
            sup_sale_pay REAL DEFAULT 0,
            admin_val REAL DEFAULT 0, 
            vaccine_pay REAL DEFAULT 0, 
            delivery_val REAL DEFAULT 0,
            mixing_val REAL DEFAULT 0, 
            wash_val REAL DEFAULT 0, 
            other_costs REAL DEFAULT 0,
            total_cost REAL DEFAULT 0, 
            cust_qty INTEGER DEFAULT 0, 
            cust_val REAL DEFAULT 0,
            mkt_qty INTEGER DEFAULT 0, 
            mkt_val REAL DEFAULT 0, 
            offal_val REAL DEFAULT 0,
            feed_sale REAL DEFAULT 0, 
            feed_trans_r REAL DEFAULT 0, 
            drug_return REAL DEFAULT 0,
            gas_return REAL DEFAULT 0, 
            total_rev REAL DEFAULT 0, 
            total_sold INTEGER DEFAULT 0,
            total_dead INTEGER DEFAULT 0, 
            mort_rate REAL DEFAULT 0, 
            avg_weight REAL DEFAULT 0,
            fcr REAL DEFAULT 0, 
            avg_price REAL DEFAULT 0, 
            net_result REAL DEFAULT 0,
            share_pct REAL DEFAULT 65, 
            share_val REAL DEFAULT 0, 
            notes TEXT DEFAULT '', 
            consumed_birds INTEGER DEFAULT 0,
            partner_name TEXT DEFAULT '',
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS daily_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            batch_id INTEGER NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
            rec_date TEXT NOT NULL, 
            day_num INTEGER DEFAULT 0, 
            dead_count INTEGER DEFAULT 0, 
            feed_kg REAL DEFAULT 0,
            water_ltr REAL DEFAULT 0, 
            notes TEXT DEFAULT '', 
            UNIQUE(batch_id, rec_date)
        );
        CREATE TABLE IF NOT EXISTS farm_sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            batch_id INTEGER NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
            customer TEXT, 
            qty INTEGER DEFAULT 0, 
            price REAL DEFAULT 0, 
            total_val REAL DEFAULT 0,
            sale_date TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS market_sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            batch_id INTEGER NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
            office TEXT, 
            qty_sent INTEGER DEFAULT 0, 
            deaths INTEGER DEFAULT 0, 
            qty_sold INTEGER DEFAULT 0,
            net_val REAL DEFAULT 0, 
            inv_num TEXT
        );
        CREATE TABLE IF NOT EXISTS batch_cost_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id INTEGER NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
            cost_name TEXT,
            qty REAL DEFAULT 0,
            company_val REAL DEFAULT 0,
            supervisor_val REAL DEFAULT 0,
            category TEXT,
            notes TEXT DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_farm_sales_customer ON farm_sales(customer);
        CREATE INDEX IF NOT EXISTS idx_market_sales_office ON market_sales(office);
        CREATE INDEX IF NOT EXISTS idx_batches_warehouse ON batches(warehouse_id);
        """)

        self.execute_script("""
        DROP VIEW IF EXISTS v_batches; 
        CREATE VIEW v_batches AS 
        SELECT b.*, w.name as warehouse_name
        FROM batches b
        JOIN warehouses w ON b.warehouse_id = w.id;
        """)
