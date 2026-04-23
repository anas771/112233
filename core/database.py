from __future__ import annotations

import re
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
    culls_count INTEGER DEFAULT 0,
    feed_kg    REAL    DEFAULT 0,
    water_ltr  REAL    DEFAULT 0,
    temp_min_c REAL    DEFAULT 0,
    temp_max_c REAL    DEFAULT 0,
    humidity_min_pct REAL DEFAULT 0,
    humidity_max_pct REAL DEFAULT 0,
    clinical_signs_text TEXT DEFAULT '',
    analysis_status TEXT DEFAULT '',
    analysis_summary TEXT DEFAULT '',
    risk_score REAL DEFAULT 0,
    notes      TEXT    DEFAULT '',
    UNIQUE(batch_id, rec_date)
);

CREATE TABLE IF NOT EXISTS treatment_catalog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    active_ingredient TEXT NOT NULL,
    treatment_class TEXT NOT NULL,
    subclass TEXT DEFAULT '',
    route TEXT DEFAULT 'water',
    common_use TEXT DEFAULT '',
    target_patterns TEXT DEFAULT '',
    country_scope TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    is_active INTEGER DEFAULT 1,
    sort_order INTEGER DEFAULT 99,
    UNIQUE(product_name, active_ingredient)
);

CREATE TABLE IF NOT EXISTS daily_treatments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
    record_id INTEGER REFERENCES daily_records(id) ON DELETE CASCADE,
    rec_date TEXT NOT NULL,
    catalog_id INTEGER REFERENCES treatment_catalog(id),
    product_name TEXT NOT NULL,
    active_ingredient TEXT DEFAULT '',
    treatment_class TEXT DEFAULT '',
    dose_text TEXT DEFAULT '',
    notes TEXT DEFAULT ''
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

CREATE TABLE IF NOT EXISTS import_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    source_key TEXT NOT NULL,
    is_default INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS import_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL REFERENCES import_profiles(id) ON DELETE CASCADE,
    source_sheet TEXT NOT NULL,
    source_label TEXT NOT NULL,
    target_kind TEXT NOT NULL,
    target_code TEXT DEFAULT '',
    target_name TEXT DEFAULT '',
    category TEXT DEFAULT '',
    unit TEXT DEFAULT '',
    has_qty INTEGER DEFAULT 0,
    is_auto_created INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(profile_id, source_sheet, source_label, target_kind)
);

CREATE TABLE IF NOT EXISTS import_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_ui TEXT NOT NULL DEFAULT 'web',
    status TEXT NOT NULL DEFAULT 'draft',
    profile_id INTEGER REFERENCES import_profiles(id),
    batch_mode TEXT DEFAULT 'create',
    merge_mode TEXT DEFAULT 'replace',
    target_batch_id INTEGER,
    created_by TEXT DEFAULT '',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    committed_at TEXT
);

CREATE TABLE IF NOT EXISTS import_run_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES import_runs(id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    file_path TEXT DEFAULT '',
    fingerprint_sha256 TEXT DEFAULT '',
    detected_warehouse TEXT DEFAULT '',
    detected_batch_num TEXT DEFAULT '',
    detected_date_in TEXT DEFAULT '',
    target_batch_id INTEGER,
    status TEXT DEFAULT 'pending',
    reason TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS import_run_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES import_runs(id) ON DELETE CASCADE,
    run_file_id INTEGER NOT NULL REFERENCES import_run_files(id) ON DELETE CASCADE,
    line_kind TEXT NOT NULL,
    source_sheet TEXT DEFAULT '',
    source_row INTEGER DEFAULT 0,
    source_label TEXT DEFAULT '',
    qty REAL DEFAULT 0,
    amount REAL DEFAULT 0,
    rec_date TEXT DEFAULT '',
    payload_json TEXT DEFAULT '',
    mapping_status TEXT DEFAULT 'unmapped',
    target_kind TEXT DEFAULT '',
    target_code TEXT DEFAULT '',
    target_name TEXT DEFAULT '',
    category TEXT DEFAULT '',
    unit TEXT DEFAULT '',
    has_qty INTEGER DEFAULT 0,
    is_auto_created INTEGER DEFAULT 0,
    apply_flag INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS import_file_fingerprints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fingerprint_sha256 TEXT NOT NULL,
    profile_id INTEGER,
    batch_num TEXT DEFAULT '',
    date_in TEXT DEFAULT '',
    first_run_id INTEGER,
    last_run_id INTEGER,
    import_count INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(fingerprint_sha256, batch_num, date_in)
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

DEFAULT_IMPORT_PROFILE_PV4 = ("poultry_v4_default", "poultry_v4", 1, 1)
DEFAULT_IMPORT_PROFILE_GENERIC = ("generic_excel_default", "generic_excel", 1, 1)
DEFAULT_IMPORT_PROFILES = [
    DEFAULT_IMPORT_PROFILE_PV4,
    DEFAULT_IMPORT_PROFILE_GENERIC,
]

DEFAULT_IMPORT_MAPPINGS = [
    ("اجمالي التكاليف", "الكتاكيت", "cost", "chick_val", "الكتاكيت", "مواد", "حبة", 1, 0),
    ("اجمالي التكاليف", "العلف", "cost", "feed_val", "العلف", "مواد", "طن", 1, 0),
    ("اجمالي التكاليف", "العلفطن", "cost", "feed_val", "العلف", "مواد", "طن", 1, 0),
    ("اجمالي التكاليف", "العلاجات", "cost", "drugs_val", "علاجات وأدوية", "صحة", "", 0, 0),
    ("اجمالي التكاليف", "الغاز", "cost", "gas_val", "الغاز", "مرافق", "أسطوانة", 1, 0),
    ("اجمالي التكاليف", "الغازدبة", "cost", "gas_val", "الغاز", "مرافق", "أسطوانة", 1, 0),
    ("اجمالي التكاليف", "النشارة", "cost", "sawdust_val", "النشارة", "مواد", "كيس", 1, 0),
    ("اجمالي التكاليف", "مصاريفعنبر", "cost", "wh_expenses", "مصاريف عنبر", "تشغيل", "", 0, 0),
    ("اجمالي التكاليف", "مصاريفبيت", "cost", "house_exp", "مصاريف بيت", "تشغيل", "", 0, 0),
    ("اجمالي التكاليف", "علفمباع", "revenue", "feed_sale", "مبيعات علف", "مبيعات", "كيس", 1, 0),
    ("اجمالي التكاليف", "علفمتبقي", "revenue", "feed_rem_val", "علف متبقي", "مخزون", "كيس", 1, 0),
    ("اجمالي التكاليف", "مردودعلاجات", "revenue", "drug_return", "مرتجع علاجات", "مرتجعات", "", 0, 0),
    ("اجمالي التكاليف", "بيعذبل", "revenue", "offal_val", "مبيعات ذبيل", "مبيعات", "", 0, 0),
    ("اجمالي التكاليف", "اجماليالبيع", "ignore", "", "", "", "", 0, 0),
    ("اجمالي التكاليف", "الاجماليالمبيعات", "ignore", "", "", "", "", 0, 0),
    ("اجمالي التكاليف", "اجماليالتكاليف", "ignore", "", "", "", "", 0, 0),
    ("اجمالي التكاليف", "نتيجةالدفعة", "ignore", "", "", "", "", 0, 0),
    ("تكاليف العلف", "علفمباعللعملاءنقدا", "revenue", "feed_sale", "مبيعات علف", "مبيعات", "كيس", 1, 0),
    ("تكاليف العلف", "علفمتبقيفيالعنبر", "revenue", "feed_rem_val", "علف متبقي", "مخزون", "كيس", 1, 0),
]

DEFAULT_TREATMENT_CATALOG = [
    ("Tylosin 100", "tylosin", "antibiotic", "macrolide", "water", "respiratory support", "respiratory,mycoplasma", "Egypt,Saudi,Yemen", 1),
    ("Tilmicosin", "tilmicosin", "antibiotic", "macrolide", "water", "respiratory support", "respiratory,mycoplasma", "Egypt,Saudi,Yemen", 2),
    ("Spiramycin", "spiramycin", "antibiotic", "macrolide", "water", "respiratory support", "respiratory", "Egypt,Saudi,Yemen", 3),
    ("Erythromycin", "erythromycin", "antibiotic", "macrolide", "water", "respiratory support", "respiratory", "Egypt,Saudi,Yemen", 4),
    ("Doxycycline 20", "doxycycline", "antibiotic", "tetracycline", "water", "respiratory and bacterial support", "respiratory,bacterial", "Egypt,Saudi,Yemen", 5),
    ("Oxytetracycline", "oxytetracycline", "antibiotic", "tetracycline", "water", "bacterial support", "bacterial,enteric,respiratory", "Egypt,Saudi,Yemen", 6),
    ("Chlortetracycline", "chlortetracycline", "antibiotic", "tetracycline", "feed", "bacterial support", "bacterial,enteric", "Egypt,Saudi,Yemen", 7),
    ("Florfenicol", "florfenicol", "antibiotic", "amphenicol", "water", "bacterial respiratory support", "respiratory,bacterial", "Egypt,Saudi,Yemen", 8),
    ("Enrofloxacin", "enrofloxacin", "antibiotic", "fluoroquinolone", "water", "bacterial support", "bacterial,systemic", "Egypt,Saudi,Yemen", 9),
    ("Norfloxacin", "norfloxacin", "antibiotic", "fluoroquinolone", "water", "bacterial support", "bacterial,enteric", "Egypt,Saudi,Yemen", 10),
    ("Ciprofloxacin", "ciprofloxacin", "antibiotic", "fluoroquinolone", "water", "bacterial support", "bacterial", "Egypt,Saudi,Yemen", 11),
    ("Amoxicillin", "amoxicillin", "antibiotic", "penicillin", "water", "bacterial support", "enteric,bacterial", "Egypt,Saudi,Yemen", 12),
    ("Ampicillin", "ampicillin", "antibiotic", "penicillin", "water", "bacterial support", "enteric,bacterial", "Egypt,Saudi,Yemen", 13),
    ("Colistin", "colistin", "antibiotic", "polymyxin", "water", "enteric bacterial support", "enteric,bacterial", "Egypt,Saudi,Yemen", 14),
    ("Gentamicin", "gentamicin", "antibiotic", "aminoglycoside", "water", "systemic bacterial support", "bacterial", "Egypt,Saudi,Yemen", 15),
    ("Neomycin", "neomycin", "antibiotic", "aminoglycoside", "water", "enteric bacterial support", "enteric,bacterial", "Egypt,Saudi,Yemen", 16),
    ("Lincomycin", "lincomycin", "antibiotic", "lincosamide", "water", "respiratory support", "respiratory,bacterial", "Egypt,Saudi,Yemen", 17),
    ("Lincomycin Spectinomycin", "lincomycin spectinomycin", "antibiotic", "combination", "water", "respiratory support", "respiratory,mycoplasma", "Egypt,Saudi,Yemen", 18),
    ("Sulfa Trimethoprim", "sulfadiazine trimethoprim", "antibiotic", "sulfonamide", "water", "bacterial support", "enteric,bacterial", "Egypt,Saudi,Yemen", 19),
    ("Sulfamethoxazole Trimethoprim", "sulfamethoxazole trimethoprim", "antibiotic", "sulfonamide", "water", "bacterial support", "enteric,bacterial", "Egypt,Saudi,Yemen", 20),
    ("Fosfomycin", "fosfomycin", "antibiotic", "phosphonic", "water", "bacterial support", "bacterial", "Egypt,Saudi,Yemen", 21),
    ("Sulfaquinoxaline", "sulfaquinoxaline", "anticoccidial", "sulfonamide", "water", "coccidiosis support", "coccidiosis,enteric", "Egypt,Saudi,Yemen", 22),
    ("Sulfachloropyrazine", "sulfachloropyrazine", "anticoccidial", "sulfonamide", "water", "coccidiosis support", "coccidiosis", "Egypt,Saudi,Yemen", 23),
    ("Amprolium", "amprolium", "anticoccidial", "coccidiostat", "water", "coccidiosis support", "coccidiosis,enteric", "Egypt,Saudi,Yemen", 24),
    ("Toltrazuril", "toltrazuril", "anticoccidial", "triazine", "water", "coccidiosis support", "coccidiosis,bloody_diarrhea", "Egypt,Saudi,Yemen", 25),
    ("Diclazuril", "diclazuril", "anticoccidial", "triazine", "water", "coccidiosis support", "coccidiosis", "Egypt,Saudi,Yemen", 26),
    ("Robenidine", "robenidine", "anticoccidial", "feed-additive", "feed", "coccidiosis prevention", "coccidiosis", "Egypt,Saudi,Yemen", 27),
    ("Maduramicin", "maduramicin", "anticoccidial", "ionophore", "feed", "coccidiosis prevention", "coccidiosis", "Egypt,Saudi,Yemen", 28),
    ("Salinomycin", "salinomycin", "anticoccidial", "ionophore", "feed", "coccidiosis prevention", "coccidiosis", "Egypt,Saudi,Yemen", 29),
    ("Monensin", "monensin", "anticoccidial", "ionophore", "feed", "coccidiosis prevention", "coccidiosis", "Egypt,Saudi,Yemen", 30),
    ("Bromhexine", "bromhexine", "respiratory_support", "mucolytic", "water", "respiratory support", "respiratory,mucus", "Egypt,Saudi,Yemen", 31),
    ("Menthol Eucalyptus", "menthol eucalyptus", "respiratory_support", "aromatic", "water", "respiratory comfort", "respiratory,supportive", "Egypt,Saudi,Yemen", 32),
    ("Expectorant Mix", "herbal expectorant", "respiratory_support", "supportive", "water", "respiratory comfort", "respiratory,supportive", "Egypt,Saudi,Yemen", 33),
    ("Vitamin AD3E", "vitamins ad3e", "vitamin_electrolyte", "fat-soluble", "water", "supportive", "supportive,stress", "Egypt,Saudi,Yemen", 34),
    ("Vitamin C", "ascorbic acid", "vitamin_electrolyte", "water-soluble", "water", "heat stress support", "supportive,heat_stress", "Egypt,Saudi,Yemen", 35),
    ("Vitamin K3", "vitamin k3", "vitamin_electrolyte", "water-soluble", "water", "supportive", "bleeding,supportive", "Egypt,Saudi,Yemen", 36),
    ("B Complex", "vitamin b complex", "vitamin_electrolyte", "water-soluble", "water", "appetite and nerve support", "supportive,recovery", "Egypt,Saudi,Yemen", 37),
    ("Electrolytes", "electrolyte mix", "vitamin_electrolyte", "electrolyte", "water", "rehydration support", "supportive,dehydration", "Egypt,Saudi,Yemen", 38),
    ("Sodium Bicarbonate", "sodium bicarbonate", "supportive", "electrolyte", "water", "heat support", "heat_stress,supportive", "Egypt,Saudi,Yemen", 39),
    ("Betaine", "betaine", "supportive", "osmolyte", "water", "heat support", "heat_stress,supportive", "Egypt,Saudi,Yemen", 40),
    ("Liver Tonic", "silymarin mix", "liver_support", "hepatic_support", "water", "liver support", "supportive,recovery", "Egypt,Saudi,Yemen", 41),
    ("Choline Chloride", "choline chloride", "liver_support", "hepatic_support", "water", "liver support", "supportive,metabolic", "Egypt,Saudi,Yemen", 42),
    ("Probiotic Mix", "bacillus mix", "probiotic", "gut flora", "water", "gut health support", "enteric,supportive", "Egypt,Saudi,Yemen", 43),
    ("Yeast Probiotic", "saccharomyces cerevisiae", "probiotic", "yeast", "feed", "gut health support", "enteric,supportive", "Egypt,Saudi,Yemen", 44),
    ("Enzyme Mix", "xylanase phytase", "supportive", "digestive", "feed", "digestive support", "enteric,supportive", "Egypt,Saudi,Yemen", 45),
    ("Immune Booster", "beta glucan", "immune_support", "immunomodulator", "water", "immune support", "supportive,immune", "Egypt,Saudi,Yemen", 46),
    ("Selenium Vitamin E", "selenium vitamin e", "immune_support", "antioxidant", "water", "immune support", "supportive,immune", "Egypt,Saudi,Yemen", 47),
    ("Organic Acids", "formic propionic acids", "supportive", "acidifier", "water", "gut and water hygiene support", "enteric,supportive", "Egypt,Saudi,Yemen", 48),
    ("Water Sanitizer", "hydrogen peroxide silver", "disinfectant", "water-line", "water", "water sanitation", "preventive,biosecurity", "Egypt,Saudi,Yemen", 49),
    ("Barn Disinfectant", "quaternary ammonium glutaraldehyde", "disinfectant", "surface", "spray", "environment sanitation", "preventive,biosecurity", "Egypt,Saudi,Yemen", 50),
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

DAILY_RECORD_EXTRA_COLUMNS = [
    ("culls_count", "INTEGER DEFAULT 0"),
    ("temp_min_c", "REAL DEFAULT 0"),
    ("temp_max_c", "REAL DEFAULT 0"),
    ("humidity_min_pct", "REAL DEFAULT 0"),
    ("humidity_max_pct", "REAL DEFAULT 0"),
    ("clinical_signs_text", "TEXT DEFAULT ''"),
    ("analysis_status", "TEXT DEFAULT ''"),
    ("analysis_summary", "TEXT DEFAULT ''"),
    ("risk_score", "REAL DEFAULT 0"),
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
    for column_name, column_type in DAILY_RECORD_EXTRA_COLUMNS:
        _ensure_column("daily_records", column_name, column_type, db_path)
    _ensure_column("farm_sales", "sale_type", "TEXT DEFAULT 'آجل'", db_path)
    _ensure_column("farm_sales", "sale_date", "TEXT DEFAULT ''", db_path)
    _ensure_column("market_sales", "sale_date", "TEXT DEFAULT ''", db_path)
    _seed_cost_types(db_path)
    _seed_revenue_types(db_path)
    _seed_import_profiles(db_path)
    _seed_import_mappings(db_path)
    _seed_treatment_catalog(db_path)
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


def _normalize_source_label(value: str) -> str:
    raw = (value or "").strip().lower()
    compact = re.sub(r"\s+", "", raw)
    return "".join(ch for ch in compact if ch.isalnum())


def _seed_import_profiles(db_path: Path) -> None:
    with get_conn(db_path) as conn:
        for profile in DEFAULT_IMPORT_PROFILES:
            conn.execute(
                """
                INSERT OR IGNORE INTO import_profiles(name, source_key, is_default, is_active)
                VALUES (?, ?, ?, ?)
                """,
                profile,
            )
            conn.execute(
                """
                UPDATE import_profiles
                SET is_default=1, is_active=1, updated_at=CURRENT_TIMESTAMP
                WHERE name=? AND source_key=?
                """,
                (profile[0], profile[1]),
            )
            conn.execute(
                """
                UPDATE import_profiles
                SET is_default=0, updated_at=CURRENT_TIMESTAMP
                WHERE source_key=? AND name<>?
                """,
                (profile[1], profile[0]),
            )
        conn.commit()


def _seed_import_mappings(db_path: Path) -> None:
    with get_conn(db_path) as conn:
        profile = conn.execute(
            "SELECT id FROM import_profiles WHERE name=? AND source_key=?",
            (DEFAULT_IMPORT_PROFILE_PV4[0], DEFAULT_IMPORT_PROFILE_PV4[1]),
        ).fetchone()
        if not profile:
            return
        profile_id = int(profile["id"])
        for (
            source_sheet,
            source_label,
            target_kind,
            target_code,
            target_name,
            category,
            unit,
            has_qty,
            is_auto_created,
        ) in DEFAULT_IMPORT_MAPPINGS:
            conn.execute(
                """
                INSERT INTO import_mappings(
                    profile_id, source_sheet, source_label, target_kind, target_code, target_name,
                    category, unit, has_qty, is_auto_created, is_active
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                ON CONFLICT(profile_id, source_sheet, source_label, target_kind)
                DO UPDATE SET
                    target_code=excluded.target_code,
                    target_name=excluded.target_name,
                    category=excluded.category,
                    unit=excluded.unit,
                    has_qty=excluded.has_qty,
                    is_auto_created=excluded.is_auto_created,
                    is_active=1,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (
                    profile_id,
                    source_sheet,
                    _normalize_source_label(source_label),
                    target_kind,
                    target_code,
                    target_name,
                    category,
                    unit,
                    int(has_qty),
                    int(is_auto_created),
                ),
            )
        conn.commit()


def _seed_treatment_catalog(db_path: Path) -> None:
    with get_conn(db_path) as conn:
        conn.executemany(
            """
            INSERT OR IGNORE INTO treatment_catalog(
                product_name, active_ingredient, treatment_class, subclass, route,
                common_use, target_patterns, country_scope, sort_order
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            DEFAULT_TREATMENT_CATALOG,
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
        CREATE INDEX IF NOT EXISTS idx_daily_treatments_batch_date ON daily_treatments(batch_id, rec_date);
        CREATE INDEX IF NOT EXISTS idx_daily_treatments_record ON daily_treatments(record_id);
        CREATE INDEX IF NOT EXISTS idx_treatment_catalog_class ON treatment_catalog(treatment_class, is_active);
        CREATE INDEX IF NOT EXISTS idx_farm_sales_batch_date ON farm_sales(batch_id, sale_date);
        CREATE INDEX IF NOT EXISTS idx_market_sales_batch_date ON market_sales(batch_id, sale_date);
        CREATE INDEX IF NOT EXISTS idx_batch_costs_batch ON batch_costs(batch_id);
        CREATE INDEX IF NOT EXISTS idx_batch_revenues_batch ON batch_revenues(batch_id);
        CREATE INDEX IF NOT EXISTS idx_import_runs_profile_status ON import_runs(profile_id, status);
        CREATE INDEX IF NOT EXISTS idx_import_run_files_run ON import_run_files(run_id);
        CREATE INDEX IF NOT EXISTS idx_import_run_files_fingerprint ON import_run_files(fingerprint_sha256);
        CREATE INDEX IF NOT EXISTS idx_import_run_lines_run ON import_run_lines(run_id);
        CREATE INDEX IF NOT EXISTS idx_import_run_lines_file ON import_run_lines(run_file_id);
        CREATE INDEX IF NOT EXISTS idx_import_mappings_profile ON import_mappings(profile_id, is_active);
        CREATE INDEX IF NOT EXISTS idx_import_fingerprints_sha ON import_file_fingerprints(fingerprint_sha256);
        """,
        db_path,
    )
