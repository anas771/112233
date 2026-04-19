"""
منظومة إدارة عنابر الدجاج اللاحم — النسخة المطورة 3.8 (النسخة النهائية الآمنة)
Poultry Farm Management System — Enhanced v3.8
SQLite + Tkinter/ttkbootstrap + Matplotlib — يعمل على Windows بدون إنترنت
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import csv
import os
import shutil
import textwrap
from datetime import datetime, date, timedelta
import sys
from core.reports_manager import ReportsManager
import io

# ضبط ترميز الإخراج ليدعم العربي في التيرمنال
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except:
        pass

# ── دعم المظهر العصري (Classic Plus) ──────────────────────────
try:
    import ttkbootstrap as ttkb
    from ttkbootstrap.constants import *
    WindowBase = ttkb.Window
    
    class ToplevelBase(ttkb.Toplevel):
        def __init__(self, master=None, **kwargs):
            super().__init__(master, **kwargs)
            self.attributes("-alpha", 0.0)
            self._fade_in()
        def _fade_in(self):
            alpha = self.attributes("-alpha")
            if alpha < 1.0:
                self.attributes("-alpha", alpha + 0.15) # تلاشي أسرع وأكثر نعومة
                self.after(25, self._fade_in)
    
    HAS_TTKB = True
except ImportError:
    WindowBase = tk.Tk
    ToplevelBase = tk.Toplevel
    HAS_TTKB = False

# ── مكونات واجهة ذكية تدعم التنسيق الحديث والوضع الليلي ──────────
class UIFrame(ttkb.Frame if HAS_TTKB else tk.Frame):
    def __init__(self, master=None, **kwargs):
        if HAS_TTKB:
            for k in ['bg', 'fg', 'pady', 'padx', 'relief', 'bd', 'highlightbackground', 'highlightthickness']: kwargs.pop(k, None)
        super().__init__(master, **kwargs)

class UILabel(ttkb.Label if HAS_TTKB else tk.Label):
    def __init__(self, master=None, **kwargs):
        if HAS_TTKB:
            for k in ['bg', 'fg', 'activebackground', 'activeforeground', 'relief', 'bd', 'padx', 'pady']: kwargs.pop(k, None)
        super().__init__(master, **kwargs)

class UIButton(ttkb.Button if HAS_TTKB else tk.Button):
    def __init__(self, master=None, **kwargs):
        self.original_style = kwargs.get('bootstyle', 'primary')
        if HAS_TTKB:
            for k in ['bg', 'fg', 'activebackground', 'activeforeground', 'relief', 'bd', 'font', 'padx', 'pady']: kwargs.pop(k, None)
            txt = kwargs.get('text', '')
            if 'حذف' in txt or '🗑' in txt: kwargs.setdefault('bootstyle', 'danger')
            elif 'إلغاء' in txt: kwargs.setdefault('bootstyle', 'secondary')
            elif 'حفظ' in txt or 'إضافة' in txt or '➕' in txt: kwargs.setdefault('bootstyle', 'success')
            elif 'PDF' in txt: kwargs.setdefault('bootstyle', 'info')
            else: kwargs.setdefault('bootstyle', 'primary')
        super().__init__(master, **kwargs)
        # إضافة تأثير تفاعلي بسيط عند مرور الماوس
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, e):
        if HAS_TTKB:
            try:
                curr = self.cget("bootstyle")
                if "-outline" not in str(curr):
                    self.configure(bootstyle=f"{curr}-outline")
            except tk.TclError: pass
    def _on_leave(self, e):
        if HAS_TTKB:
            try:
                self.configure(bootstyle=self.original_style)
            except tk.TclError: pass

class UIEntry(ttkb.Entry if HAS_TTKB else tk.Entry):
    def __init__(self, master=None, **kwargs):
        if HAS_TTKB:
            for k in ['bg', 'fg', 'insertbackground', 'relief', 'bd', 'highlightthickness', 'highlightbackground', 'padx', 'pady']: kwargs.pop(k, None)
        super().__init__(master, **kwargs)

class UILabelFrame(ttkb.Labelframe if HAS_TTKB else tk.LabelFrame):
    def __init__(self, master=None, **kwargs):
        if HAS_TTKB:
            for k in ['bg', 'fg', 'pady', 'padx', 'relief', 'bd', 'font', 'labelanchor']: kwargs.pop(k, None)
            kwargs.setdefault('bootstyle', 'primary')
        super().__init__(master, **kwargs)

# ── دعم الرسوم البيانية ─────────────────────────────────────────
try:
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    # استخدام خط Segoe UI للرسوم البيانية أيضاً لضمان التناسق
    matplotlib.rc('font', family='Segoe UI')
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_ARABIC = True
except ImportError:
    HAS_ARABIC = False

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

# ── المسار الرئيسي للتطبيق ──────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "poultry_data.db")

# ── ألوان "Classic Plus" (Microsoft Fluent Palette) ────────────────
CLR = {
    "bg":       "#F3F2F1", # رمادي ناعم جداً
    "header":   "#005A9E", # أزرق احترافي
    "nav":      "#F3F2F1",
    "white":    "#FFFFFF",
    "profit":   "#107C10", # أخضر فورست
    "loss":     "#A80000", # أحمر غامق
    "warn":     "#847545",
    "profit_bg":"#DFF6DD",
    "loss_bg":  "#FDE7E9",
    "warn_bg":  "#FFF4CE",
    "info_bg":  "#EFF6FC",
    "border":   "#EDEBE9",
    "text":     "#323130", # فحم داكن
    "text2":    "#605E5C", # رمادي النصوص الثانوية
    "accent":   "#0078D4", # لون التفاعل الرئيسي
    "daily_bg": "#FFFFFF",
}

# الخطوط الرسمية لويندوز (Segoe UI) لضمان أعلى جودة
FN = "Segoe UI" if sys.platform == "win32" else "Arial"
FT_TITLE  = (FN, 14, "bold")
FT_HEADER = (FN, 11, "bold")
FT_BODY   = (FN, 10)
FT_SMALL  = (FN, 9)
FT_TINY   = (FN, 8)

# ════════════════════════════════════════════════════════════════
# مدير قاعدة البيانات (DBManager)
# ════════════════════════════════════════════════════════════════
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
        
        # ضمان إضافة الحقول الجديدة لقواعد البيانات القديمة
        try:
            self.execute("ALTER TABLE farm_sales ADD COLUMN sale_date TEXT DEFAULT ''")
        except:
            pass
        
        columns_to_add = [
            ("fcr", "REAL DEFAULT 0"), 
            ("avg_weight", "REAL DEFAULT 0"), 
            ("batch_num", "TEXT DEFAULT ''"), 
            ("consumed_birds", "INTEGER DEFAULT 0"),
            ("partner_name", "TEXT DEFAULT ''")
        ]
        
        for col_name, col_type in columns_to_add:
            try: 
                self.execute(f"ALTER TABLE batches ADD COLUMN {col_name} {col_type}")
            except: 
                pass
                
        self.execute_script("""
        DROP VIEW IF EXISTS v_batches; 
        CREATE VIEW v_batches AS 
        WITH summary_data AS (
            SELECT 
                b.id,
                COALESCE(daily.total_dead_calc, b.total_dead, 0) as dead_total,
                COALESCE(daily.total_feed_kg, b.feed_qty * 1000, 0) as feed_total,
                COALESCE(sales.total_weight_calc, (b.chicks - COALESCE(daily.total_dead_calc, b.total_dead, 0)) * 1.5) as weight_total,
                COALESCE(sales.total_rev_calc, b.total_rev, 0) as rev_total,
                COALESCE(sales.total_sold_calc, b.total_sold, 0) as sold_total
            FROM batches b
            LEFT JOIN (
                SELECT batch_id, SUM(dead_count) as total_dead_calc, SUM(feed_kg) as total_feed_kg 
                FROM daily_records GROUP BY batch_id
            ) daily ON b.id = daily.batch_id
            LEFT JOIN (
                SELECT batch_id, SUM(qty) as total_sold_calc, SUM(total_val) as total_rev_calc, 
                       SUM(qty * 1.5) as total_weight_calc
                FROM farm_sales GROUP BY batch_id
            ) sales ON b.id = sales.batch_id
        )
        SELECT b.*, 
               w.name as warehouse_name,
               (CAST(s.dead_total AS FLOAT) / NULLIF(b.chicks, 0) * 100) as mort_rate,
               (s.feed_total / NULLIF(s.weight_total, 0)) as fcr,
               ((100 - (CAST(s.dead_total AS FLOAT) / NULLIF(b.chicks, 0) * 100)) * (s.weight_total / NULLIF(s.sold_total, 0)) * 10) / (NULLIF(b.days, 0) * NULLIF((s.feed_total / NULLIF(s.weight_total, 0)), 0)) as epef,
               COALESCE(b.net_result, (s.rev_total - COALESCE(b.total_cost, 0))) as net_result_dynamic
        FROM batches b
        JOIN warehouses w ON b.warehouse_id = w.id
        JOIN summary_data s ON b.id = s.id;
        """)

db = DBManager(DB_PATH)

def fmt_num(n, dec=0):
    try:
        n = float(n) if n else 0
        if dec == 0:
            return f"{int(n):,}"
        else:
            return f"{n:,.{dec}f}"
    except: 
        return "—"

def lbl_entry(parent, text, row, col, width=16, readonly=False, colspan=1):
    UILabel(parent, text=text, font=FT_SMALL, bg=CLR["bg"], fg=CLR["text2"], anchor="e").grid(row=row, column=col, sticky="e", padx=(6,2), pady=8)
    v = tk.StringVar()
    state = "readonly" if readonly else "normal"
    bg = "#e9ecef" if readonly else CLR["white"]
    e = UIEntry(parent, textvariable=v, width=width, font=FT_BODY, state=state, bg=bg, relief="solid", highlightthickness=1, highlightbackground=CLR["border"])
    e.grid(row=row, column=col+1, sticky="ew", padx=(2,12), pady=8, columnspan=colspan)
    e.configure(justify="right")
    return v

def prepare_text(text):
    if not text: 
        return ""
    if HAS_ARABIC: 
        return get_display(arabic_reshaper.reshape(str(text)))
    return str(text)

def tprint(text):
    """طباعة آمنة للعربية في التيرمنال"""
    print(prepare_text(text))

def make_backup():
    if not os.path.exists(DB_PATH): 
        return None
    bk_dir = os.path.join(BASE_DIR, "backups")
    os.makedirs(bk_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(bk_dir, f"poultry_data_{ts}.db")
    shutil.copy2(DB_PATH, dest)
    files = sorted([f for f in os.listdir(bk_dir) if f.startswith("poultry_data_") and f.endswith(".db")])
    while len(files) > 10: 
        os.remove(os.path.join(bk_dir, files.pop(0)))
    return dest

# ════════════════════════════════════════════════════════════════
# نافذة السجلات اليومية
# ════════════════════════════════════════════════════════════════
class DailyRecordsWindow(ToplevelBase):
    def __init__(self, master, batch_id, batch_info):
        super().__init__(master)
        self.batch_id = batch_id
        self.batch_info = batch_info
        b_num = batch_info.get("batch_num") or batch_id
        self.title(f"السجلات اليومية — {batch_info.get('warehouse_name','')} — دفعة {b_num}")
        self.geometry("900x600")
        if not HAS_TTKB: 
            self.configure(bg=CLR["bg"])
        self.grab_set()
        self._build()
        self._load()

    def _build(self):
        hdr = UIFrame(self, bg=CLR["header"], pady=10)
        hdr.pack(fill="x")
        b_num = self.batch_info.get("batch_num") or self.batch_id
        UILabel(hdr, text=f"📅 السجلات اليومية — الدفعة رقم {b_num}", font=FT_TITLE, bg=CLR["header"], fg="white").pack(side="right", padx=16)

        inp = UILabelFrame(self, text="إضافة / تعديل سجل يومي", font=FT_HEADER, bg=CLR["daily_bg"], fg=CLR["accent"], padx=10, pady=8)
        inp.pack(fill="x", padx=10, pady=8)

        UILabel(inp, text="التاريخ:", font=FT_SMALL, bg=CLR["daily_bg"]).grid(row=0, column=0, sticky="e", padx=4)
        self.v_date = tk.StringVar(value=date.today().isoformat())
        UIEntry(inp, textvariable=self.v_date, width=14, font=FT_BODY, relief="solid").grid(row=0, column=1, padx=4)

        UILabel(inp, text="اليوم رقم:", font=FT_SMALL, bg=CLR["daily_bg"]).grid(row=0, column=2, sticky="e", padx=4)
        self.v_daynum = tk.StringVar()
        UIEntry(inp, textvariable=self.v_daynum, width=6, font=FT_BODY, relief="solid").grid(row=0, column=3, padx=4)

        UILabel(inp, text="النافق (حبة):", font=FT_SMALL, bg=CLR["daily_bg"]).grid(row=0, column=4, sticky="e", padx=4)
        self.v_dead = tk.StringVar(value="0")
        UIEntry(inp, textvariable=self.v_dead, width=8, font=FT_BODY, relief="solid").grid(row=0, column=5, padx=4)

        UILabel(inp, text="العلف (كجم):", font=FT_SMALL, bg=CLR["daily_bg"]).grid(row=0, column=6, sticky="e", padx=4)
        self.v_feed = tk.StringVar(value="0")
        UIEntry(inp, textvariable=self.v_feed, width=10, font=FT_BODY, relief="solid").grid(row=0, column=7, padx=4)

        UILabel(inp, text="ملاحظة:", font=FT_SMALL, bg=CLR["daily_bg"]).grid(row=1, column=0, sticky="e", padx=4, pady=4)
        self.v_notes = tk.StringVar()
        UIEntry(inp, textvariable=self.v_notes, width=50, font=FT_BODY, relief="solid").grid(row=1, column=1, columnspan=6, padx=4, sticky="ew")

        btn_frm = UIFrame(inp, bg=CLR["daily_bg"])
        btn_frm.grid(row=1, column=7, padx=4)
        UIButton(btn_frm, text="💾 حفظ", font=FT_BODY, bg=CLR["nav"], fg="white", cursor="hand2", relief="flat", padx=8, command=self._save_record).pack(side="right", padx=2)
        UIButton(btn_frm, text="🗑 حذف", font=FT_BODY, bg=CLR["loss_bg"], fg=CLR["loss"], cursor="hand2", relief="flat", padx=8, command=self._del_record).pack(side="right", padx=2)

        cols = ("التاريخ","اليوم","النافق","تراكم النافق","العلف كجم","إجمالي العلف","ملاحظة")
        frm = UIFrame(self, bg=CLR["bg"])
        frm.pack(fill="both", expand=True, padx=10, pady=5)
        self.tree = ttk.Treeview(frm, columns=cols, show="headings", selectmode="browse")
        
        widths = [100, 60, 80, 110, 90, 110, 200]
        for c, w in zip(cols, widths): 
            self.tree.heading(c, text=c, anchor="center")
            self.tree.column(c, width=w, anchor="center")
            
        sb = ttk.Scrollbar(frm, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="left", fill="y")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        sumfrm = UIFrame(self, bg=CLR["info_bg"], pady=10, padx=15)
        sumfrm.pack(fill="x", padx=15, pady=8)
        self.lbl_summary = UILabel(sumfrm, text="", font=FT_BODY, bg=CLR["info_bg"], fg=CLR["accent"])
        self.lbl_summary.pack(side="right")
        
        UIButton(self, text="📥 تصدير السجل إلى Excel", command=self._export_excel, bootstyle="success").pack(pady=15)

    def _load(self):
        rows = db.fetch_all("SELECT rec_date, day_num, dead_count, feed_kg, notes FROM daily_records WHERE batch_id=? ORDER BY rec_date", (self.batch_id,))
        self.tree.delete(*self.tree.get_children())
        cum_dead = 0
        cum_feed = 0.0
        for r in rows:
            cum_dead += r["dead_count"]
            cum_feed += r["feed_kg"]
            self.tree.insert("", "end", iid=r["rec_date"], values=(r["rec_date"], r["day_num"] or "", r["dead_count"], cum_dead, fmt_num(r["feed_kg"],1), fmt_num(cum_feed,1), r["notes"] or ""))
            
        chicks = self.batch_info.get("chicks", 0) or 0
        mort_pct = 0
        if chicks > 0:
            mort_pct = cum_dead / chicks * 100
        self.lbl_summary.config(text=f"إجمالي النافق: {cum_dead:,} طائر ({mort_pct:.2f}%)  |  إجمالي العلف: {fmt_num(cum_feed,1)} كجم  |  عدد الأيام المسجلة: {len(rows)}")

    def _on_select(self, _=None):
        sel = self.tree.selection()
        if not sel: 
            return
            
        r = db.fetch_one("SELECT * FROM daily_records WHERE batch_id=? AND rec_date=?", (self.batch_id, sel[0]))
        if r:
            self.v_date.set(r["rec_date"])
            self.v_daynum.set(str(r["day_num"] or ""))
            self.v_dead.set(str(r["dead_count"]))
            self.v_feed.set(str(r["feed_kg"]))
            self.v_notes.set(r["notes"] or "")

    def _save_record(self):
        rec_date = self.v_date.get().strip()
        if not rec_date: 
            return messagebox.showwarning("تنبيه", "يرجى إدخال التاريخ", parent=self)
            
        try: 
            dead = int(self.v_dead.get() or 0)
            feed = float(self.v_feed.get() or 0)
            daynum = int(self.v_daynum.get() or 0)
        except ValueError: 
            return messagebox.showerror("خطأ", "القيم يجب أن تكون أرقاماً", parent=self)
        
        db.execute("""
            INSERT INTO daily_records (batch_id, rec_date, day_num, dead_count, feed_kg, notes) 
            VALUES (?,?,?,?,?,?)
            ON CONFLICT(batch_id, rec_date) DO UPDATE SET 
                day_num=excluded.day_num, 
                dead_count=excluded.dead_count, 
                feed_kg=excluded.feed_kg, 
                notes=excluded.notes
        """, (self.batch_id, rec_date, daynum, dead, feed, self.v_notes.get()))
        
        row = db.fetch_one("SELECT SUM(dead_count) FROM daily_records WHERE batch_id=?", (self.batch_id,))
        total_dead = row[0] if row and row[0] else 0
        chicks = self.batch_info.get("chicks", 0) or 0
        mort_rate = 0
        if chicks > 0:
            mort_rate = round(total_dead / chicks * 100, 2)
            
        db.execute("UPDATE batches SET total_dead=?, mort_rate=? WHERE id=?", (total_dead, mort_rate, self.batch_id))
        self._load()

        # تسريع الإدخال: الانتقال لليوم التالي وتصفير القيم
        try:
            curr_date = datetime.strptime(rec_date, "%Y-%m-%d")
            self.v_date.set((curr_date + timedelta(days=1)).strftime("%Y-%m-%d"))
        except: 
            pass
            
        try:
            self.v_daynum.set(str(int(self.v_daynum.get() or 0) + 1))
        except: 
            pass
            
        self.v_dead.set("0")
        self.v_feed.set("0")
        self.v_notes.set("")

    def _del_record(self):
        sel = self.tree.selection()
        if not sel: 
            return
        
        if not messagebox.askyesno("تأكيد", f"حذف سجل يوم {sel[0]}؟", parent=self): 
            return
            
        db.execute("DELETE FROM daily_records WHERE batch_id=? AND rec_date=?", (self.batch_id, sel[0]))
        self._load()

    def _export_excel(self):
        if not HAS_OPENPYXL: 
            return messagebox.showerror("خطأ", "مكتبة openpyxl غير مثبتة", parent=self)
            
        b_num = self.batch_info.get("batch_num") or self.batch_id
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel","*.xlsx")], initialfile=f"سجل_يومي_دفعة_{b_num}.xlsx", parent=self)
        if not path: 
            return
            
        rows = db.fetch_all("SELECT rec_date, day_num, dead_count, feed_kg, notes FROM daily_records WHERE batch_id=? ORDER BY rec_date", (self.batch_id,))
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "السجل اليومي"
        ws.sheet_view.rightToLeft = True
        
        hdrs = ["التاريخ","اليوم","النافق","تراكم النافق","العلف كجم","إجمالي العلف","ملاحظة"]
        for ci, h in enumerate(hdrs, 1):
            cell = ws.cell(1, ci, h)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="1F4E79")
            cell.alignment = Alignment(horizontal="center")
            
        cum_dead = 0
        cum_feed = 0.0
        for ri, r in enumerate(rows, 2):
            cum_dead += r["dead_count"]
            cum_feed += r["feed_kg"]
            ws.cell(ri,1,r["rec_date"])
            ws.cell(ri,2,r["day_num"])
            ws.cell(ri,3,r["dead_count"])
            ws.cell(ri,4,cum_dead)
            ws.cell(ri,5,round(r["feed_kg"],2))
            ws.cell(ri,6,round(cum_feed,2))
            ws.cell(ri,7,r["notes"])
            
        for col in ws.columns: 
            ws.column_dimensions[col[0].column_letter].width = 16
            
        wb.save(path)
        messagebox.showinfo("تم", "تم التصدير بنجاح!", parent=self)

# ════════════════════════════════════════════════════════════════
# نافذة إدخال / تعديل دفعة
# ════════════════════════════════════════════════════════════════
class BatchForm(ToplevelBase):
    def __init__(self, master, batch_id=None, on_save=None):
        super().__init__(master)
        self.batch_id = batch_id
        self.on_save  = on_save
        self.title("إدخال دفعة جديدة" if not batch_id else "تعديل دفعة")
        self.geometry("1100x750")
        if not HAS_TTKB: 
            self.configure(bg=CLR["bg"])
        self.resizable(True, True)
        self.grab_set()

        self._vars = {}
        self._farm_sales = []
        self._market_sales = []
        self._cost_records = []
        self._syncing = False
        
        self._build_ui()
        if batch_id: 
            self._load_batch()

    def _build_ui(self):
        hdr = UIFrame(self, bg=CLR["header"], pady=(20, 15))
        hdr.pack(fill="x")
        UILabel(hdr, text="📄 الملف المالي والإحصائي للدفعة", font=FT_TITLE, bg=CLR["header"], fg="white").pack(side="right", padx=20)

        # تحسين شكل التبويبات (Tabs) لتكون أكثر انسيابية
        style = ttk.Style()
        if HAS_TTKB:
            style.configure('TNotebook.Tab', font=FT_HEADER, padding=[20, 8])
        else:
            style.theme_use('default')
            style.configure('TNotebook.Tab', font=FT_HEADER, padding=[15, 5])

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=15)

        # التبويبات مع مسافات مريحة
        self.tab_basic   = UIFrame(self.notebook, padx=25, pady=25)
        self.tab_costs   = UIFrame(self.notebook, padx=25, pady=15)
        self.tab_sales   = UIFrame(self.notebook, padx=25, pady=15)
        self.tab_results = UIFrame(self.notebook, padx=25, pady=25)

        self.notebook.add(self.tab_basic,   text="📋 البيانات الأساسية")
        self.notebook.add(self.tab_costs,   text="💰 سجل التكاليف")
        self.notebook.add(self.tab_sales,   text="📈 سجل المبيعات")
        self.notebook.add(self.tab_results, text="📊 الخلاصة والنتائج")

        self._build_basic_tab(self.tab_basic)
        self._build_costs_tab(self.tab_costs)
        self._build_sales_tab(self.tab_sales)
        self._build_results_tab(self.tab_results)

        btn_frm = UIFrame(self, pady=15)
        btn_frm.pack(fill="x")
        UIButton(btn_frm, text="💾 حفظ الدفعة", font=FT_HEADER, bg=CLR["nav"], fg="white", padx=30, pady=8, cursor="hand2", relief="flat", command=self._save).pack(side="right", padx=20)
        
        if self.batch_id: 
            UIButton(btn_frm, text="📅 السجلات اليومية", font=FT_BODY, bg=CLR["daily_bg"], fg=CLR["accent"], padx=20, pady=8, cursor="hand2", relief="flat", bd=1, command=self._open_daily).pack(side="right", padx=4)
            
        UIButton(btn_frm, text="إلغاء وإغلاق", font=FT_BODY, bg="#e0e0e0", fg=CLR["text"], padx=20, pady=8, cursor="hand2", relief="solid", bd=1, command=self.destroy).pack(side="left", padx=20)

    def _open_daily(self):
        if not self.batch_id: 
            return
        batch = db.fetch_one("SELECT * FROM v_batches WHERE id=?", (self.batch_id,))
        if batch: 
            DailyRecordsWindow(self, self.batch_id, dict(batch))

    def _build_basic_tab(self, F):
        UILabel(F, text="اسم العنبر *", font=FT_SMALL, bg=CLR["bg"], fg=CLR["text2"]).grid(row=0, column=0, sticky="e", padx=(8,2), pady=10)
        self.wh_var = tk.StringVar()
        self.wh_combo = ttk.Combobox(F, textvariable=self.wh_var, width=22, font=FT_BODY)
        self.wh_combo["values"] = [r["name"] for r in db.fetch_all("SELECT name FROM warehouses ORDER BY name")]
        self.wh_combo.grid(row=0, column=1, sticky="ew", padx=(0,20), pady=10)

        v = self._vars
        v["batch_num"] = lbl_entry(F,"رقم الدفعة", 0, 2, 16)
        v["date_in"]  = lbl_entry(F,"تاريخ الدخول *",  1, 0, 16)
        v["date_out"] = lbl_entry(F,"تاريخ الخروج *",  1, 2, 16)
        v["days"]     = lbl_entry(F,"عدد الأيام",      1, 4, 10, readonly=True)
        v["chicks"]      = lbl_entry(F,"عدد الكتاكيت المستلمة *", 2, 0, 16)
        v["chick_val"]   = lbl_entry(F,"إجمالي قيمة الكتاكيت",  2, 2, 16)
        v["avg_weight"]  = lbl_entry(F,"متوسط وزن الطائر (كجم)", 3, 0, 16)
        v["fcr"]         = lbl_entry(F,"معدل التحويل الغذائي FCR", 3, 2, 16, readonly=True)

        for key in ("date_in","date_out","chicks","chick_val","avg_weight"): 
            v[key].trace_add("write", lambda *a: self._auto_calc())

    def _build_costs_tab(self, F):
        v = self._vars
        cost_fields = [
            ("feed_qty","علف—كمية(طن)"),("feed_val","علف—قيمة"),("feed_trans","أجور نقل علف"),
            ("sawdust_qty","نشارة—كمية"),("sawdust_val","نشارة—قيمة"),("water_val","قيمة الماء"),
            ("gas_qty","غاز—كمية"),("gas_val","غاز—قيمة"),("drugs_val","علاجات وأدوية"),
            ("wh_expenses","مصاريف عنبر"),("house_exp","مصاريف بيت"),("breeders_pay","أجور مربيين"),
            ("qat_pay","قات مربيين"),("rent_val","إيجار عنبر"),("light_val","إضاءة"),
            ("sup_wh_pay","مشرف عنبر"),("sup_co_pay","مشرف شركة"),("sup_sale_pay","مشرف بيع"),
            ("admin_val","إدارة وحسابات"),("vaccine_pay","أجور لقاحات"),("delivery_val","توصيل خدمات"),
            ("mixing_val","حمالة وخلط"),("wash_val","تغسيل عنبر"),("other_costs","مصاريف أخرى"),
        ]
        row = 0
        col = 0
        for i, (key, lbl) in enumerate(cost_fields):
            if i > 0 and i % 3 == 0: 
                row += 1
                col = 0
            UILabel(F, text=lbl, font=FT_SMALL, bg=CLR["bg"], fg=CLR["text2"]).grid(row=row, column=col, sticky="e", padx=(8,2), pady=6)
            v[key] = tk.StringVar()
            e = UIEntry(F, textvariable=v[key], width=16, font=FT_BODY, relief="solid", highlightthickness=1, highlightbackground=CLR["border"])
            e.grid(row=row, column=col+1, sticky="ew", padx=(0,20), pady=6)
            e.configure(justify="right")
            
            # منع التعديل اليدوي لبعض الحقول إذا كانت مرتبطة بالتكاليف التفصيلية (اختياري، حالياً نتركه للمزامنة)
            v[key].trace_add("write", lambda *a: self._auto_calc())
            col += 2

        # ── قسم سجل التكاليف التفصيلي (الجديد) ──
        sep = ttk.Separator(F, orient="horizontal")
        sep.grid(row=row+1, column=0, columnspan=6, sticky="ew", pady=15)
        
        UILabel(F, text="📝 سجل بنود التكاليف التفصيلية (من الإكسيل أو مضاف يدوياً)", font=FT_HEADER, bg=CLR["bg"], fg=CLR["nav"]).grid(row=row+2, column=0, columnspan=6, sticky="w", pady=(0,10))
        
        inp_c = UIFrame(F, bg=CLR["bg"])
        inp_c.grid(row=row+3, column=0, columnspan=6, sticky="ew")
        
        UILabel(inp_c, text="البند:", font=FT_SMALL, bg=CLR["bg"]).grid(row=0,column=0, padx=2)
        self.v_cost_name = tk.StringVar()
        UIEntry(inp_c, textvariable=self.v_cost_name, width=18, font=FT_BODY, relief="solid").grid(row=0,column=1, padx=2)
        
        UILabel(inp_c, text="الكمية:", font=FT_SMALL, bg=CLR["bg"]).grid(row=0,column=2, padx=2)
        self.v_cost_qty = tk.StringVar()
        UIEntry(inp_c, textvariable=self.v_cost_qty, width=8, font=FT_BODY, justify="right", relief="solid").grid(row=0,column=3, padx=2)
        
        UILabel(inp_c, text="الشركة:", font=FT_SMALL, bg=CLR["bg"]).grid(row=0,column=4, padx=2)
        self.v_cost_comp = tk.StringVar()
        UIEntry(inp_c, textvariable=self.v_cost_comp, width=12, font=FT_BODY, justify="right", relief="solid").grid(row=0,column=5, padx=2)
        
        UILabel(inp_c, text="المشرف:", font=FT_SMALL, bg=CLR["bg"]).grid(row=0,column=6, padx=2)
        self.v_cost_sup = tk.StringVar()
        UIEntry(inp_c, textvariable=self.v_cost_sup, width=12, font=FT_BODY, justify="right", relief="solid").grid(row=0,column=7, padx=2)
        
        UIButton(inp_c, text="➕ إضافة", font=FT_BODY, bg=CLR["nav"], fg="white", command=self._add_cost_record).grid(row=0,column=8, padx=10)
        UIButton(inp_c, text="🗑 حذف", font=FT_BODY, bg=CLR["loss_bg"], fg=CLR["loss"], command=self._del_cost_record).grid(row=0,column=9, padx=2)

        c_cols = ("م", "البند", "الكمية", "قيمة الشركة", "قيمة المشرف", "الإجمالي", "التصنيف")
        self.tv_costs_detail = ttk.Treeview(F, columns=c_cols, show="headings", height=5)
        c_widths = [30, 180, 80, 110, 110, 120, 100]
        for c, w in zip(c_cols, c_widths):
            self.tv_costs_detail.heading(c, text=c)
            self.tv_costs_detail.column(c, width=w, anchor="center")
        self.tv_costs_detail.grid(row=row+4, column=0, columnspan=6, sticky="ew", pady=10)

        frm_tc = UIFrame(F, bg=CLR["loss_bg"], pady=8, padx=15, bd=1, relief="solid")
        frm_tc.grid(row=row+5, column=0, columnspan=6, sticky="ew", pady=(10,0))
        UILabel(frm_tc, text="إجمالي التكاليف والمصروفات:", font=FT_HEADER, bg=CLR["loss_bg"], fg=CLR["loss"]).pack(side="right")
        self.lbl_total_cost = UILabel(frm_tc, text="0", font=("Arial",16,"bold"), bg=CLR["loss_bg"], fg=CLR["loss"])
        self.lbl_total_cost.pack(side="right", padx=15)

    def _build_sales_tab(self, F):
        # حاوية رئيسية تسمح بالتمرير إذا زاد المحتوى
        canvas = tk.Canvas(F, bg=CLR["bg"], highlightthickness=0)
        v_scroll = ttk.Scrollbar(F, orient="vertical", command=canvas.yview)
        scroll_frm = UIFrame(canvas, bg=CLR["bg"])
        
        canvas.configure(yscrollcommand=v_scroll.set)
        canvas.pack(side="right", fill="both", expand=True)
        v_scroll.pack(side="left", fill="y")
        
        canvas.create_window((0,0), window=scroll_frm, anchor="nw", width=1040) # عرض ثابت تقريباً
        
        def _on_cfg(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        scroll_frm.bind("<Configure>", _on_cfg)

        # ── 1. القسم العلوي: مبيعات العنبر ──
        f_frm = UILabelFrame(scroll_frm, text="🐓 بيان مبيعات العنبر", font=FT_HEADER, bg=CLR["bg"], fg=CLR["nav"], padx=10, pady=10)
        f_frm.pack(fill="x", pady=(0,15))
        
        inp_f = UIFrame(f_frm, bg=CLR["bg"])
        inp_f.pack(fill="x", pady=5)
        UILabel(inp_f, text="اسم العميل:", font=FT_SMALL, bg=CLR["bg"]).grid(row=0,column=0, padx=4)
        self.v_fs_cust = tk.StringVar()
        UIEntry(inp_f, textvariable=self.v_fs_cust, width=20, font=FT_BODY, relief="solid").grid(row=0,column=1, padx=4)
        
        UILabel(inp_f, text="الكمية:", font=FT_SMALL, bg=CLR["bg"]).grid(row=0,column=2, padx=4)
        self.v_fs_qty = tk.StringVar()
        UIEntry(inp_f, textvariable=self.v_fs_qty, width=10, font=FT_BODY, justify="right", relief="solid").grid(row=0,column=3, padx=4)
        
        UILabel(inp_f, text="السعر:", font=FT_SMALL, bg=CLR["bg"]).grid(row=0,column=4, padx=4)
        self.v_fs_price = tk.StringVar()
        UIEntry(inp_f, textvariable=self.v_fs_price, width=10, font=FT_BODY, justify="right", relief="solid").grid(row=0,column=5, padx=4)
        
        UILabel(inp_f, text="التاريخ:", font=FT_SMALL, bg=CLR["bg"]).grid(row=0,column=6, padx=4)
        self.v_fs_date = tk.StringVar(value=date.today().strftime('%Y-%m-%d'))
        UIEntry(inp_f, textvariable=self.v_fs_date, width=12, font=FT_BODY, relief="solid").grid(row=0,column=7, padx=4)
        
        UIButton(inp_f, text="➕ إضافة", font=FT_BODY, bg=CLR["nav"], fg="white", relief="flat", cursor="hand2", command=self._add_farm_sale).grid(row=0,column=8, padx=15)
        UIButton(inp_f, text="🗑 حذف", font=FT_BODY, bg=CLR["loss_bg"], fg=CLR["loss"], relief="flat", cursor="hand2", command=self._del_farm_sale).grid(row=0,column=9, padx=4)

        f_cols = ("م", "اسم العميل", "التاريخ", "الكمية", "السعر", "الإجمالي")
        self.tv_farm = ttk.Treeview(f_frm, columns=f_cols, show="headings", selectmode="browse", height=6)
        widths_f = [40, 200, 110, 100, 100, 140]
        for c, w in zip(f_cols, widths_f): 
            self.tv_farm.heading(c, text=c, anchor="center")
            self.tv_farm.column(c, width=w, anchor="center")
        self.tv_farm.pack(fill="both", expand=True, pady=5)

        sum_f = UIFrame(f_frm, bg=CLR["profit_bg"], pady=5, padx=15)
        sum_f.pack(fill="x")
        self.lbl_cust_tot = UILabel(sum_f, text="إجمالي مبيعات العنبر: 0 طائر | 0 ريال", font=FT_BODY, bg=CLR["profit_bg"], fg=CLR["profit"])
        self.lbl_cust_tot.pack(side="right")

        # ── 2. القسم الأوسط: مبيعات السوق ──
        m_frm = UILabelFrame(scroll_frm, text="🏢 بيان مبيعات السوق (المكاتب)", font=FT_HEADER, bg=CLR["bg"], fg=CLR["accent"], padx=10, pady=10)
        m_frm.pack(fill="x", pady=15)
        
        inp_m = UIFrame(m_frm, bg=CLR["bg"])
        inp_m.pack(fill="x", pady=5)
        UILabel(inp_m, text="المكتب:", font=FT_SMALL, bg=CLR["bg"]).grid(row=0,column=0, padx=2)
        self.v_ms_office = tk.StringVar()
        UIEntry(inp_m, textvariable=self.v_ms_office, width=18, font=FT_BODY, relief="solid").grid(row=0,column=1, padx=2)
        
        UILabel(inp_m, text="الكمية:", font=FT_SMALL, bg=CLR["bg"]).grid(row=0,column=2, padx=2)
        self.v_ms_qty = tk.StringVar()
        UIEntry(inp_m, textvariable=self.v_ms_qty, width=8, font=FT_BODY, justify="right", relief="solid").grid(row=0,column=3, padx=2)
        
        UILabel(inp_m, text="الوفيات:", font=FT_SMALL, bg=CLR["bg"]).grid(row=0,column=4, padx=2)
        self.v_ms_dead = tk.StringVar(value="0")
        UIEntry(inp_m, textvariable=self.v_ms_dead, width=6, font=FT_BODY, justify="right", relief="solid").grid(row=0,column=5, padx=2)
        
        UILabel(inp_m, text="صافي الفاتورة:", font=FT_SMALL, bg=CLR["bg"]).grid(row=0,column=6, padx=2)
        self.v_ms_net = tk.StringVar()
        UIEntry(inp_m, textvariable=self.v_ms_net, width=10, font=FT_BODY, justify="right", relief="solid").grid(row=0,column=7, padx=2)
        
        UILabel(inp_m, text="رقم الفاتورة:", font=FT_SMALL, bg=CLR["bg"]).grid(row=0,column=8, padx=2)
        self.v_ms_inv = tk.StringVar()
        UIEntry(inp_m, textvariable=self.v_ms_inv, width=10, font=FT_BODY, relief="solid").grid(row=0,column=9, padx=2)
        
        UIButton(inp_m, text="➕ إضافة", font=FT_BODY, bg=CLR["nav"], fg="white", relief="flat", cursor="hand2", command=self._add_market_sale).grid(row=0,column=10, padx=10)
        UIButton(inp_m, text="🗑 حذف", font=FT_BODY, bg=CLR["loss_bg"], fg=CLR["loss"], relief="flat", cursor="hand2", command=self._del_market_sale).grid(row=0,column=11, padx=2)

        m_cols = ("م", "مكتب التسويق", "الكمية", "الوفيات", "المباع", "صافي الفاتورة", "رقم الفاتورة")
        self.tv_mkt = ttk.Treeview(m_frm, columns=m_cols, show="headings", selectmode="browse", height=6)
        widths_m = [40, 200, 80, 80, 80, 110, 110]
        for c, w in zip(m_cols, widths_m): 
            self.tv_mkt.heading(c, text=c, anchor="center")
            self.tv_mkt.column(c, width=w, anchor="center")
        self.tv_mkt.pack(fill="both", expand=True, pady=5)

        sum_m = UIFrame(m_frm, bg=CLR["profit_bg"], pady=5, padx=15)
        sum_m.pack(fill="x")
        self.lbl_mkt_tot = UILabel(sum_m, text="إجمالي مبيعات السوق: 0 طائر | 0 ريال", font=FT_BODY, bg=CLR["profit_bg"], fg=CLR["profit"])
        self.lbl_mkt_tot.pack(side="right")

        # ── 3. القسم السفلي: إيرادات أخرى ──
        o_frm = UILabelFrame(scroll_frm, text="💰 إيرادات وضبط مالي إضافي", font=FT_HEADER, bg=CLR["bg"], fg="#607d8b", padx=10, pady=10)
        o_frm.pack(fill="x", pady=(15,0))
        
        v = self._vars
        rev_fields = [
            ("offal_val","مبيعات ذبيل (قيمة)"), ("feed_sale","مبيعات علف (قيمة)"),
            ("feed_trans_r","علف منقول لعنابر (قيمة)"), ("drug_return","مرتجع علاجات"),
            ("gas_return","نقل غاز/نشارة")
        ]
        rf = UIFrame(o_frm, bg=CLR["bg"])
        rf.pack(fill="x")
        row2, col2 = 0, 0
        for i, (key, lbl) in enumerate(rev_fields):
            if i > 0 and i % 3 == 0: 
                row2 += 1
                col2 = 0
            UILabel(rf, text=lbl, font=FT_SMALL, bg=CLR["bg"]).grid(row=row2, column=col2, sticky="e", padx=(8,2), pady=8)
            v[key] = tk.StringVar()
            e = UIEntry(rf, textvariable=v[key], width=14, font=FT_BODY, relief="solid")
            e.grid(row=row2, column=col2+1, sticky="ew", padx=(0,15), pady=8)
            e.configure(justify="right")
            v[key].trace_add("write", lambda *a: self._auto_calc())
            col2 += 2

        # الملخص النهائي للمبيعات (دائم الظهور في تذييل التبويب)
        sum_total = UIFrame(F, bg=CLR["profit_bg"], pady=10, padx=20, bd=1, relief="ridge")
        sum_total.pack(fill="x", side="bottom")
        UILabel(sum_total, text="إجمالي الإيرادات والمبيعات (بيان موحد):", font=FT_HEADER, bg=CLR["profit_bg"], fg=CLR["profit"]).pack(side="right")
        self.lbl_total_rev = UILabel(sum_total, text="0", font=("Arial",18,"bold"), bg=CLR["profit_bg"], fg=CLR["profit"])
        self.lbl_total_rev.pack(side="right", padx=20)

    def _add_farm_sale(self):
        c = self.v_fs_cust.get().strip()
        d_val = self.v_fs_date.get().strip()
        try: 
            q = int(self.v_fs_qty.get() or 0)
            p = float(self.v_fs_price.get() or 0)
        except ValueError: 
            return messagebox.showerror("خطأ", "الكمية والسعر يجب أن تكون أرقاماً", parent=self)
            
        if not c or q <= 0: 
            return messagebox.showwarning("تنبيه", "يرجى إدخال اسم العميل والكمية", parent=self)
            
        self._farm_sales.append({"customer": c, "qty": q, "price": p, "total_val": q * p, "sale_date": d_val})
        self.v_fs_cust.set("")
        self.v_fs_qty.set("")
        self.v_fs_price.set("")
        self._refresh_sales_views()
        self._auto_calc()

    def _del_farm_sale(self):
        sel = self.tv_farm.selection()
        if not sel: 
            return
            
        idx = self.tv_farm.index(sel[0])
        del self._farm_sales[idx]
        self._refresh_sales_views()
        self._auto_calc()

    def _add_market_sale(self):
        off = self.v_ms_office.get().strip()
        try: 
            q = int(self.v_ms_qty.get() or 0)
            d = int(self.v_ms_dead.get() or 0)
            n_val = float(self.v_ms_net.get() or 0)
        except ValueError: 
            return messagebox.showerror("خطأ", "الكمية، الوفيات، وصافي الفاتورة يجب أن تكون أرقاماً", parent=self)
            
        if not off or q <= 0: 
            return messagebox.showwarning("تنبيه", "يرجى إدخال مكتب التسويق والكمية", parent=self)
            
        sold = q - d
        self._market_sales.append({"office": off, "qty_sent": q, "deaths": d, "qty_sold": sold, "net_val": n_val, "inv_num": self.v_ms_inv.get().strip()})
        self.v_ms_office.set("")
        self.v_ms_qty.set("")
        self.v_ms_dead.set("0")
        self.v_ms_net.set("")
        self.v_ms_inv.set("")
        self._refresh_sales_views()
        self._auto_calc()

    def _del_market_sale(self):
        sel = self.tv_mkt.selection()
        if not sel: 
            return
            
        idx = self.tv_mkt.index(sel[0])
        del self._market_sales[idx]
        self._refresh_sales_views()
        self._auto_calc()

    def _refresh_sales_views(self):
        self.tv_farm.delete(*self.tv_farm.get_children())
        for i, s in enumerate(self._farm_sales, 1):
            self.tv_farm.insert("", "end", values=(i, s["customer"], s.get("sale_date", ""), fmt_num(s["qty"]), fmt_num(s["price"],2), fmt_num(s["total_val"])))
            
        self.tv_mkt.delete(*self.tv_mkt.get_children())
        for i, s in enumerate(self._market_sales, 1):
            self.tv_mkt.insert("", "end", values=(i, s["office"], fmt_num(s["qty_sent"]), fmt_num(s["deaths"]), fmt_num(s["qty_sold"]), fmt_num(s["net_val"]), s["inv_num"]))

    def _build_results_tab(self, F):
        v = self._vars
        v["total_sold"] = lbl_entry(F,"إجمالي الطيور المباعة (حبة)", 0, 0, 16, readonly=True)
        v["total_dead"] = lbl_entry(F,"النافق الكلي (حبة)", 0, 2, 16)
        v["mort_rate"]  = lbl_entry(F,"نسبة النافق الكلية %", 0, 4, 16, readonly=True)
        v["avg_price"]  = lbl_entry(F,"متوسط سعر البيع للطائر", 1, 0, 16, readonly=True)
        
        v["consumed_birds"] = lbl_entry(F,"طيور مستهلكة / ضيافة (حبة)", 1, 2, 16)
        
        v["total_dead"].trace_add("write", lambda *a: self._auto_calc())
        v["consumed_birds"].trace_add("write", lambda *a: self._auto_calc())

        v["share_pct"] = lbl_entry(F,"نصيب الشركة من الأرباح %", 2, 0, 16)
        v["share_pct"].set("65")
        v["share_pct"].trace_add("write", lambda *a: self._auto_calc())
        
        v["share_val"] = lbl_entry(F,"نصيب الشركة (ريال)", 2, 2, 16, readonly=True)
        
        v["partner_name"] = lbl_entry(F,"اسم الشريك", 3, 0, 16)
        
        v["notes"] = lbl_entry(F,"ملاحظات إضافية على الدفعة", 4, 0, 40, colspan=5)

        frm_epef = UIFrame(F, pady=5, padx=20, bg=CLR["info_bg"])
        frm_epef.grid(row=5, column=0, columnspan=6, sticky="ew", pady=(10,0))
        UILabel(frm_epef, text="مؤشر الكفاءة الأوروبي (EPEF):", font=("Arial",12,"bold"), bg=CLR["info_bg"]).pack(side="right")
        self.lbl_epef = UILabel(frm_epef, text="0", font=("Arial",14,"bold"), bg=CLR["info_bg"], fg=CLR["accent"])
        self.lbl_epef.pack(side="right", padx=20)

        frm_net = UIFrame(F, pady=15, padx=20, bd=2, relief="groove")
        frm_net.grid(row=6, column=0, columnspan=6, sticky="ew", pady=(20,0))
        UILabel(frm_net, text="صافي النتيجة للدفعة:", font=("Arial",18,"bold")).pack(side="right")
        self.lbl_net = UILabel(frm_net, text="0", font=("Arial",24,"bold"))
        self.lbl_net.pack(side="right", padx=20)
        self._net_frame = frm_net

    def _n(self, key):
        try: 
            return float(self._vars[key].get())
        except: 
            return 0.0

    def _auto_calc(self):
        if self._syncing: return
        v = self._vars
        def parse_date(date_str):
            for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
                try: 
                    return datetime.strptime(date_str.strip(), fmt)
                except: 
                    pass
            return None

        d_in = parse_date(v.get("date_in", tk.StringVar()).get())
        d_out = parse_date(v.get("date_out", tk.StringVar()).get())
        if d_in and d_out: 
            days = (d_out - d_in).days
            if days > 0:
                v["days"].set(days)
            else:
                v["days"].set("")
        else: 
            v["days"].set("")

        chick_val = self._n("chick_val")
        cost_keys = ["feed_val","feed_trans","sawdust_val","water_val","gas_val","drugs_val","wh_expenses","house_exp","breeders_pay","qat_pay","rent_val","light_val","sup_wh_pay","sup_co_pay","sup_sale_pay","admin_val","vaccine_pay","delivery_val","mixing_val","wash_val","other_costs"]
        total_cost = chick_val + sum(self._n(k) for k in cost_keys)
        
        if hasattr(self, 'lbl_total_cost'): 
            self.lbl_total_cost.config(text=f"{fmt_num(total_cost)} ريال")

        total_cust_qty = sum(float(x.get('qty', 0)) for x in self._farm_sales)
        total_cust_val = sum(float(x.get('total_val', 0)) for x in self._farm_sales)
        total_mkt_qty  = sum(float(x.get('qty_sold', 0)) for x in self._market_sales)
        total_mkt_val  = sum(float(x.get('net_val', 0)) for x in self._market_sales)
        
        if hasattr(self, 'lbl_cust_tot'): 
            self.lbl_cust_tot.config(text=f"إجمالي مبيعات العنبر: {fmt_num(total_cust_qty)} طائر | {fmt_num(total_cust_val)} ريال")
            
        if hasattr(self, 'lbl_mkt_tot'): 
            self.lbl_mkt_tot.config(text=f"إجمالي مبيعات السوق: {fmt_num(total_mkt_qty)} طائر | {fmt_num(total_mkt_val)} ريال")

        rev_keys = ["offal_val","feed_sale","feed_trans_r","drug_return","gas_return"]
        total_rev = total_cust_val + total_mkt_val + sum(self._n(k) for k in rev_keys)
        
        if hasattr(self, 'lbl_total_rev'): 
            self.lbl_total_rev.config(text=f"{fmt_num(total_rev)} ريال")

        chicks = self._n("chicks")
        dead = self._n("total_dead")
        days = self._n("days")
        avg_weight = self._n("avg_weight")
        feed_tons = self._n("feed_qty")
        
        mort_rate = 0
        if chicks > 0:
            mort_rate = (dead / chicks * 100)
            
        if "mort_rate" in v: 
            if chicks > 0:
                v["mort_rate"].set(f"{mort_rate:.2f}")
            else:
                v["mort_rate"].set("")

        sold_qty = total_cust_qty + total_mkt_qty
        if "total_sold" in v: 
            v["total_sold"].set(fmt_num(sold_qty))
            
        if sold_qty > 0 and "avg_price" in v: 
            v["avg_price"].set(fmt_num((total_cust_val + total_mkt_val) / sold_qty, 2))

        if sold_qty > 0 and avg_weight > 0 and feed_tons > 0 and "fcr" in v: 
            fcr_val = (feed_tons * 1000) / (sold_qty * avg_weight)
            v["fcr"].set(f"{fcr_val:.3f}")
        else:
            fcr_val = 0
        
        if hasattr(self, 'lbl_epef'):
            if days > 0 and chicks > 0 and avg_weight > 0 and fcr_val > 0:
                # EPEF = ((100 - mort_rate) * avg_weight * 10) / (days * FCR)
                epef = ((100 - mort_rate) * avg_weight * 10) / (days * fcr_val)
                if epef >= 300:
                    self.lbl_epef.config(text=f"{epef:.0f}", foreground=CLR["profit"])
                else:
                    self.lbl_epef.config(text=f"{epef:.0f}", foreground=CLR["loss"])
            else: 
                self.lbl_epef.config(text="0", foreground=CLR["text2"])

        net = total_rev - total_cost
        if hasattr(self, 'lbl_net'): 
            if net >= 0:
                self.lbl_net.config(text=f"{fmt_num(net)} ريال", foreground=CLR["profit"])
            else:
                self.lbl_net.config(text=f"{fmt_num(net)} ريال", foreground=CLR["loss"])
                
        if not HAS_TTKB and hasattr(self, '_net_frame'): 
            try:
                if net >= 0:
                    self._net_frame.config(bg=CLR["profit_bg"])
                else:
                    self._net_frame.config(bg=CLR["loss_bg"])
            except:
                pass
            
        try: 
            v["share_val"].set(fmt_num(net * float(v["share_pct"].get()) / 100))
        except: 
            pass

    def _load_batch(self):
        self._syncing = True
        try:
            row = db.fetch_one("SELECT * FROM v_batches WHERE id=?", (self.batch_id,))
            if not row: 
                return
                
            self.wh_var.set(row["warehouse_name"])
            for k in [x for x in row.keys() if x in self._vars]:
                if row[k] is not None:
                    self._vars[k].set(str(row[k]))
                else:
                    self._vars[k].set("")
        finally:
            self._syncing = False
            self._auto_calc()
            
        f_sales = db.fetch_all("SELECT * FROM farm_sales WHERE batch_id=?", (self.batch_id,))
        if f_sales: 
            self._farm_sales = [dict(r) for r in f_sales]
        elif row["cust_qty"] or row["cust_val"]:
            old_qty = row["cust_qty"] or 0
            old_val = row["cust_val"] or 0
            old_price = 0
            if old_qty > 0:
                old_price = old_val / old_qty
            self._farm_sales.append({"customer": "مبيعات سابقة (مرحلة)", "qty": old_qty, "price": old_price, "total_val": old_val})
            
        self._refresh_sales_views()
        
        c_recs = db.fetch_all("SELECT * FROM batch_cost_records WHERE batch_id=?", (self.batch_id,))
        self._cost_records = [dict(r) for r in c_recs]
        self._refresh_costs_view()
        
        self._auto_calc()

    def _refresh_costs_view(self):
        for i in self.tv_costs_detail.get_children(): self.tv_costs_detail.delete(i)
        for i, r in enumerate(self._cost_records, 1):
            comp = float(r.get('company_val', 0) or 0)
            sup = float(r.get('supervisor_val', 0) or 0)
            tot = comp + sup
            self.tv_costs_detail.insert("", "end", values=(i, r.get('cost_name'), r.get('qty'), fmt_num(comp), fmt_num(sup), fmt_num(tot), r.get('category')))

    def _add_cost_record(self):
        name = self.v_cost_name.get().strip()
        if not name: return
        try:
            qty = float(self.v_cost_qty.get() or 0)
            comp = float(self.v_cost_comp.get() or 0)
            sup = float(self.v_cost_sup.get() or 0)
        except: return messagebox.showerror("خطأ", "الكمية والمبالغ يجب أن تكون أرقاماً")
        
        cat = 'other'
        if "علف" in name: cat = 'feed'
        elif "غاز" in name: cat = 'gas'
        elif "نشارة" in name: cat = 'sawdust'
        elif "كتاكيت" in name or "صوص" in name: cat = 'chicks'
        elif "علاج" in name or "أدوية" in name: cat = 'drugs'
        
        self._cost_records.append({'cost_name': name, 'qty': qty, 'company_val': comp, 'supervisor_val': sup, 'category': cat})
        self.v_cost_name.set(""); self.v_cost_qty.set(""); self.v_cost_comp.set(""); self.v_cost_sup.set("")
        self._sync_detailed_to_vars()
        self._refresh_costs_view()
        self._auto_calc()

    def _del_cost_record(self):
        sel = self.tv_costs_detail.selection()
        if not sel: return
        idx = self.tv_costs_detail.index(sel[0])
        self._cost_records.pop(idx)
        self._sync_detailed_to_vars()
        self._refresh_costs_view()
        self._auto_calc()

    def _sync_detailed_to_vars(self):
        self._syncing = True
        try:
            summary_maps = {
                'feed': ('feed_val', 'feed_qty'),
                'gas': ('gas_val', 'gas_qty'),
                'sawdust': ('sawdust_val', 'sawdust_qty'),
                'chicks': ('chick_val', None),
                'drugs': ('drugs_val', None)
            }
            sums = {k: 0 for k in ['feed_val', 'feed_qty', 'gas_val', 'gas_qty', 'sawdust_val', 'sawdust_qty', 'chick_val', 'drugs_val']}
            for r in self._cost_records:
                cat = r.get('category')
                val = float(r.get('company_val', 0) or 0) + float(r.get('supervisor_val', 0) or 0)
                qty = float(r.get('qty', 0) or 0)
                if cat in summary_maps:
                    v_key, q_key = summary_maps[cat]
                    if v_key: sums[v_key] += val
                    if q_key: sums[q_key] += qty
            for k, v in sums.items():
                if k in self._vars: self._vars[k].set(str(v) if v > 0 else "")
        finally:
            self._syncing = False
            self._auto_calc()

    def _collect(self):
        v = self._vars
        
        def n(k):
            if v.get(k) and v[k].get():
                return float(v[k].get())
            return 0.0
            
        def s(k):
            if v.get(k):
                return v[k].get().strip()
            return ""
        
        chicks_count = int(n("chicks"))
        chick_val_total = n("chick_val")
        chick_price_calc = 0.0
        if chicks_count > 0:
            chick_price_calc = chick_val_total / chicks_count

        cost_keys = ["feed_val","feed_trans","sawdust_val","water_val","gas_val","drugs_val","wh_expenses","house_exp","breeders_pay","qat_pay","rent_val","light_val","sup_wh_pay","sup_co_pay","sup_sale_pay","admin_val","vaccine_pay","delivery_val","mixing_val","wash_val","other_costs"]
        total_cost = chick_val_total + sum(n(k) for k in cost_keys)
        
        total_cust_qty = sum(float(x.get('qty', 0)) for x in self._farm_sales)
        total_cust_val = sum(float(x.get('total_val', 0)) for x in self._farm_sales)
        total_mkt_qty  = sum(float(x.get('qty_sold', 0)) for x in self._market_sales)
        total_mkt_val  = sum(float(x.get('net_val', 0)) for x in self._market_sales)
        
        total_rev  = total_cust_val + total_mkt_val + sum(n(k) for k in ["offal_val","feed_sale","feed_trans_r","drug_return","gas_return"])
        net = total_rev - total_cost
        sold_qty = total_cust_qty + total_mkt_qty
        
        mort_r = 0.0
        if chicks_count > 0:
            mort_r = round(n("total_dead") / chicks_count * 100, 2)
            
        avg_p = 0.0
        if sold_qty > 0:
            avg_p = round((total_cust_val + total_mkt_val) / sold_qty, 2)
            
        sh_pct = n("share_pct") or 65
        sh_val = net * sh_pct / 100
        
        return {
            "batch_num":s("batch_num"),
            "date_in":s("date_in"), "date_out":s("date_out"), "days":int(n("days")),
            "chicks":chicks_count, "chick_price":chick_price_calc, "chick_val":chick_val_total,
            "feed_qty":n("feed_qty"), "feed_val":n("feed_val"), "feed_trans":n("feed_trans"),
            "sawdust_qty":n("sawdust_qty"), "sawdust_val":n("sawdust_val"), "water_val":n("water_val"),
            "gas_qty":n("gas_qty"), "gas_val":n("gas_val"), "drugs_val":n("drugs_val"),
            "wh_expenses":n("wh_expenses"), "house_exp":n("house_exp"), "breeders_pay":n("breeders_pay"),
            "qat_pay":n("qat_pay"), "rent_val":n("rent_val"), "light_val":n("light_val"),
            "sup_wh_pay":n("sup_wh_pay"), "sup_co_pay":n("sup_co_pay"), "sup_sale_pay":n("sup_sale_pay"),
            "admin_val":n("admin_val"), "vaccine_pay":n("vaccine_pay"), "delivery_val":n("delivery_val"),
            "mixing_val":n("mixing_val"), "wash_val":n("wash_val"), "other_costs":n("other_costs"),
            "total_cost":total_cost, 
            "cust_qty":int(total_cust_qty), "cust_val":total_cust_val,
            "mkt_qty":int(total_mkt_qty), "mkt_val":total_mkt_val, 
            "offal_val":n("offal_val"), "feed_sale":n("feed_sale"), "feed_trans_r":n("feed_trans_r"), "drug_return":n("drug_return"), "gas_return":n("gas_return"),
            "total_rev":total_rev, "total_sold":int(sold_qty), "total_dead":int(n("total_dead")), "mort_rate": mort_r,
            "avg_weight":n("avg_weight"), "fcr":n("fcr"),
            "avg_price": avg_p, "net_result":net,
            "share_pct": sh_pct, "share_val": sh_val, "notes":s("notes"),
            "consumed_birds": int(n("consumed_birds")),
            "partner_name": s("partner_name")
        }

    def _save(self):
        wh_name = self.wh_var.get().strip()
        if not wh_name: 
            return messagebox.showwarning("تنبيه", "يرجى تحديد اسم العنبر", parent=self)
            
        d = self._collect()
        if not d["date_in"] or not d["date_out"] or not d["chicks"]: 
            return messagebox.showwarning("تنبيه", "يرجى ملء: تاريخ الدخول والخروج وعدد الكتاكيت", parent=self)

        wh = db.fetch_one("SELECT id FROM warehouses WHERE name=?", (wh_name,))
        if not wh:
            db.execute("INSERT INTO warehouses (name) VALUES (?)", (wh_name,))
            wh = db.fetch_one("SELECT id FROM warehouses WHERE name=?", (wh_name,))
        
        vals = list(d.values())
        if self.batch_id: 
            update_str = ",".join(f"{k}=?" for k in d)
            db.execute(f"UPDATE batches SET {update_str} WHERE id=?", vals+[self.batch_id])
            b_id = self.batch_id
        else: 
            cols_str = ",".join(k for k in d)
            qs_str = ",".join("?" for _ in d)
            b_id = db.execute(f"INSERT INTO batches (warehouse_id,{cols_str},created_at) VALUES (?,{qs_str},datetime('now'))", [wh["id"]]+vals)
            
        db.execute("DELETE FROM farm_sales WHERE batch_id=?", (b_id,))
        for fs in self._farm_sales:
            db.execute("INSERT INTO farm_sales (batch_id, customer, qty, price, total_val, sale_date) VALUES (?,?,?,?,?,?)", (b_id, fs["customer"], fs["qty"], fs["price"], fs["total_val"], fs.get("sale_date","")))
        
        db.execute("DELETE FROM market_sales WHERE batch_id=?", (b_id,))
        for ms in self._market_sales:
            db.execute("INSERT INTO market_sales (batch_id, office, qty_sent, deaths, qty_sold, net_val, inv_num) VALUES (?,?,?,?,?,?,?)", (b_id, ms["office"], ms["qty_sent"], ms["deaths"], ms["qty_sold"], ms["net_val"], ms["inv_num"]))

        db.execute("DELETE FROM batch_cost_records WHERE batch_id=?", (b_id,))
        for cr in self._cost_records:
            db.execute("INSERT INTO batch_cost_records (batch_id, cost_name, qty, company_val, supervisor_val, category, notes) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                       (b_id, cr['cost_name'], cr['qty'], cr['company_val'], cr['supervisor_val'], cr.get('category','other'), cr.get('notes','')))

        messagebox.showinfo("تم", "تم حفظ الدفعة بنجاح", parent=self)
        if self.on_save: 
            self.on_save()
        self.destroy()

# ════════════════════════════════════════════════════════════════
# نافذة مركز التقارير الشامل (Accounting & Reports Center)
# ════════════════════════════════════════════════════════════════
class ReportsCenterWindow(ToplevelBase):
    def __init__(self, master):
        super().__init__(master)
        self.title("مركز التقارير المحاسبية والطباعة الشاملة")
        self.geometry("1100x750")
        if not HAS_TTKB: 
            self.configure(bg=CLR["bg"])
        self.grab_set()
        
        self.reports = master.reports # استخدام مدير التقارير من النافذة الرئيسية
        self._build()

    def _build(self):
        hdr = UIFrame(self, bg=CLR["header"], pady=12)
        hdr.pack(fill="x")
        UILabel(hdr, text="🖨️ مركز التقارير والطباعة للمنظومة", font=FT_TITLE, bg=CLR["header"], fg="white").pack(side="right", padx=20)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=15, pady=15)

        self.tab_cust = UIFrame(nb, padx=15, pady=15)
        self.tab_mkt  = UIFrame(nb, padx=15, pady=15)
        self.tab_batch = UIFrame(nb, padx=15, pady=15)
        self.tab_excel = UIFrame(nb, padx=15, pady=15) # الميزة الجديدة
        self.tab_debts = UIFrame(nb, padx=15, pady=15)

        nb.add(self.tab_cust, text="👥 كشوفات العملاء")
        nb.add(self.tab_mkt,  text="🏢 كشوفات المكاتب")
        nb.add(self.tab_batch, text="📋 تقارير الدفعات")
        nb.add(self.tab_excel, text="🚀 تكامل Excel الذكي") # التبويب الجديد
        nb.add(self.tab_debts, text="💰 تقرير المديونيات العامة")

        self._build_cust_tab()
        self._build_mkt_tab()
        self._build_batch_tab()
        self._build_excel_tab() # بناء التبويب الجديد
        self._build_debts_tab()

    def _build_cust_tab(self):
        F = self.tab_cust
        ctrl = UIFrame(F, pady=10)
        ctrl.pack(fill="x")
        
        UILabel(ctrl, text="اختر العميل:").pack(side="right", padx=5)
        self.cbo_cust = ttk.Combobox(ctrl, width=25, font=FT_BODY)
        customers = [r['customer'] for r in db.fetch_all("SELECT DISTINCT customer FROM farm_sales ORDER BY customer")]
        self.cbo_cust['values'] = customers
        self.cbo_cust.pack(side="right", padx=5)
        
        UIButton(ctrl, text="🔍 عرض", command=self._load_cust_data).pack(side="right", padx=10)
        
        btn_f = UIFrame(F)
        btn_f.pack(fill="x", pady=10)
        UIButton(btn_f, text="📄 تصدير PDF", bootstyle="info", command=self._export_cust_pdf).pack(side="right", padx=5)
        UIButton(btn_f, text="📊 تصدير Excel", bootstyle="success", command=self._export_cust_excel).pack(side="right", padx=5)

        cols = ("التاريخ", "العنبر", "رقم الدفعة", "الكمية", "السعر", "الإجمالي")
        self.tv_cust = ttk.Treeview(F, columns=cols, show="headings", height=15)
        for c in cols: 
            self.tv_cust.heading(c, text=c)
            self.tv_cust.column(c, width=120, anchor="center")
        self.tv_cust.pack(fill="both", expand=True)

    def _load_cust_data(self):
        name = self.cbo_cust.get()
        if not name: return
        data = self.reports.get_customer_statement(name)
        self.tv_cust.delete(*self.tv_cust.get_children())
        for r in data:
            d_date = r['sale_date'] if r['sale_date'] else r['date_out']
            self.tv_cust.insert("", "end", values=(d_date, r['wh_name'], r['batch_num'], fmt_num(r['qty']), fmt_num(r['price'],2), fmt_num(r['total_val'])))

    def _export_cust_pdf(self):
        name = self.cbo_cust.get()
        if not name: return
        path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=f"كشف_حساب_{name}.pdf")
        if path:
            data = self.reports.get_customer_statement(name)
            self.reports.export_customer_pdf(data, name, path)
            messagebox.showinfo("تم", "تم تصدير التقرير")

    def _export_cust_excel(self):
        name = self.cbo_cust.get()
        if not name: return
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=f"كشف_حساب_{name}.xlsx")
        if path:
            data = self.reports.get_customer_statement(name)
            self.reports.export_customer_excel(data, name, path)
            messagebox.showinfo("تم", "تم تصدير ملف Excel")

    def _build_mkt_tab(self):
        F = self.tab_mkt
        ctrl = UIFrame(F, pady=10)
        ctrl.pack(fill="x")
        
        UILabel(ctrl, text="اختر المكتب:").pack(side="right", padx=5)
        self.cbo_mkt = ttk.Combobox(ctrl, width=25, font=FT_BODY)
        offices = [r['office'] for r in db.fetch_all("SELECT DISTINCT office FROM market_sales ORDER BY office")]
        self.cbo_mkt['values'] = offices
        self.cbo_mkt.pack(side="right", padx=5)
        
        UIButton(ctrl, text="🔍 عرض", command=self._load_mkt_data).pack(side="right", padx=10)
        UIButton(F, text="📄 تصدير PDF", bootstyle="info", command=self._export_mkt_pdf).pack(pady=10)

        cols = ("التاريخ", "العنبر", "المرسل", "الوفيات", "المباع", "الصافي", "الفاتورة")
        self.tv_mkt = ttk.Treeview(F, columns=cols, show="headings", height=15)
        for c in cols: 
            self.tv_mkt.heading(c, text=c)
            self.tv_mkt.column(c, width=110, anchor="center")
        self.tv_mkt.pack(fill="both", expand=True)

    def _load_mkt_data(self):
        name = self.cbo_mkt.get()
        if not name: return
        data = self.reports.get_market_statement(name)
        self.tv_mkt.delete(*self.tv_mkt.get_children())
        for r in data:
            self.tv_mkt.insert("", "end", values=(r['date_out'], r['wh_name'], r['qty_sent'], r['deaths'], r['qty_sold'], fmt_num(r['net_val']), r['inv_num']))

    def _export_mkt_pdf(self):
        name = self.cbo_mkt.get()
        if not name: return
        path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=f"كشف_مكتب_{name}.pdf")
        if path:
            data = self.reports.get_market_statement(name)
            self.reports.export_market_pdf(data, name, path)
            messagebox.showinfo("تم", "تم تصدير التقرير")

    def _build_batch_tab(self):
        F = self.tab_batch
        UILabel(F, text="اختر الدفعة لطباعة التقرير الشامل:", font=FT_HEADER).pack(pady=10)
        
        cols = ("رقم الدفعة", "العنبر", "تاريخ الخروج", "صافي الربح/الخسارة")
        self.tv_batches = ttk.Treeview(F, columns=cols, show="headings", height=12)
        for c in cols: 
            self.tv_batches.heading(c, text=c)
            self.tv_batches.column(c, width=150, anchor="center")
        self.tv_batches.pack(fill="both", expand=True, pady=10)
        
        rows = db.fetch_all("SELECT id, batch_num, warehouse_name, date_out, net_result FROM v_batches ORDER BY date_out DESC")
        for r in rows:
            b_n = r['batch_num'] or r['id']
            self.tv_batches.insert("", "end", iid=str(r['id']), values=(b_n, r['warehouse_name'], r['date_out'], fmt_num(r['net_result'])))

        btn_f = UIFrame(F)
        btn_f.pack(fill="x", pady=10)
        UIButton(btn_f, text="📂 طباعة تصفية الدفعة النهائية", bootstyle="primary", command=self._export_full_batch).pack(side="right", padx=5)
        UIButton(btn_f, text="📅 طباعة السجلات اليومية", bootstyle="info", command=self._export_daily_logs).pack(side="right", padx=5)

    def _export_full_batch(self):
        sel = self.tv_batches.selection()
        if not sel: return
        b_id = sel[0]
        path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=f"تصفية_دفعة_{b_id}.pdf")
        if path:
            self.reports.export_full_batch_pdf(b_id, path)
            messagebox.showinfo("تم", "تم تصدير تقرير التصفية")
            os.startfile(path)

    def _export_daily_logs(self):
        sel = self.tv_batches.selection()
        if not sel: return
        b_id = sel[0]
        path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=f"سجلات_يومية_دفعة_{b_id}.pdf")
        if path:
            self.reports.export_daily_records_pdf(b_id, path)
            messagebox.showinfo("تم", "تم تصدير السجلات اليومية")
            os.startfile(path)

    def _build_excel_tab(self):
        F = self.tab_excel
        UILabel(F, text="تكامل Excel الذكي (استيراد وتصدير متطور)", font=FT_TITLE).pack(pady=10)
        UILabel(F, text="يمكنك استيراد نماذج الدفعات الفردية (.xlsm) أو تصدير التقرير التراكمي الشامل.", font=FT_BODY, fg=CLR["text2"]).pack(pady=5)
        
        btn_f = UIFrame(F, pady=30)
        btn_f.pack()
        
        UIButton(btn_f, text="📄 استيراد نموذج فردي واحد", bootstyle="info", command=self._import_single_xlsm).pack(pady=10, fill="x")
        UIButton(btn_f, text="📂 استيراد مجلد النماذج الفردية", bootstyle="success", command=self._import_xlsm_folder).pack(pady=10, fill="x")
        UIButton(btn_f, text="📤 تصدير التقرير التراكمي (54 عمود)", bootstyle="primary", command=self._export_cumulative_report).pack(pady=10, fill="x")
        
        UILabel(F, text="⚠️ تنبيه: الاستيراد سيعالج التكرار بإضافة أكواد (1001، 1002) لتمييز الدفعات.", font=FT_SMALL, fg="orange").pack(pady=20)

    def _import_single_xlsm(self):
        file_path = filedialog.askopenfilename(title="اختر ملف النموذج الفردي (.xlsm)", filetypes=[("Excel Files", "*.xlsm")])
        if not file_path: return
        
        from core.batch_importer import BatchImporter
        importer = BatchImporter(self.master.db)
        success, msg = importer.import_file(file_path)
        
        if success:
            messagebox.showinfo("نجاح", msg)
            if hasattr(self.master, '_load_batches'): self.master._load_batches()
        else:
            messagebox.showerror("خطأ", msg)

    def _import_xlsm_folder(self):
        folder = filedialog.askdirectory(title="اختر المجلد الذي يحتوي على ملفات .xlsm")
        if not folder: return
        
        from core.batch_importer import BatchImporter
        # نستخدم db المعرف عالمياً في main.py أو الممرر للنافذة
        importer = BatchImporter(self.master.db) 
        results = importer.import_folder(folder)
        
        summary = ""
        success_count = sum(1 for r in results if r['success'])
        for r in results:
            status = "✅" if r['success'] else "❌"
            summary += f"{status} {r['file']}: {r['message']}\n"
        
        # عرض النتائج في نافذة منبثقة بسيطة
        msg = f"تمت معالجة {len(results)} ملفات.\nنجاح: {success_count}\nفشل: {len(results)-success_count}\n\n{summary}"
        # تقصير الرسالة إذا كانت طويلة جداً
        if len(msg) > 1000: msg = msg[:1000] + "\n..."
        
        messagebox.showinfo("نتائج الاستيراد", msg)
        # تحديث الواجهة الرئيسية إذا لزم الأمر
        if hasattr(self.master, '_load_batches'): self.master._load_batches()

    def _export_cumulative_report(self):
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile="التقرير_التراكمي_الشامل.xlsx")
        if not path: return
        
        from core.report_exporter import ReportExporter
        exporter = ReportExporter(self.master.db if hasattr(self.master, "db") else db)
        success, msg = exporter.export_all(path)
        if success:
            if messagebox.askyesno("نجاح", f"{msg}\nهل تريد فتح الملف الآن؟"):
                os.startfile(path)
        else:
            messagebox.showerror("خطأ", msg)

    def _build_debts_tab(self):
        F = self.tab_debts
        UILabel(F, text="ملخص إجمالي مسحوبات العملاء (المديونيات التقديرية):", font=FT_HEADER).pack(pady=10)
        
        cols = ("اسم العميل", "إجمالي قيمة المسحوبات")
        self.tv_debts = ttk.Treeview(F, columns=cols, show="headings", height=15)
        for c in cols: 
            self.tv_debts.heading(c, text=c)
            self.tv_debts.column(c, width=250, anchor="center")
        self.tv_debts.pack(fill="both", expand=True)
        
        data = self.reports.get_customer_balances()
        for r in data:
            self.tv_debts.insert("", "end", values=(r['customer'], fmt_num(r['total_bought'])))
        
        UIButton(F, text="📥 تصدير قائمة المديونيات Excel", bootstyle="success", command=self._export_debts_excel).pack(pady=10)

    def _export_debts_excel(self):
        # وظيفة سريعة لتصدير المباشر
        if not HAS_OPENPYXL: return
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile="تقرير_المديونيات.xlsx")
        if path:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "المديونيات"
            ws.append(["اسم العميل", "إجمالي المسحوبات"])
            data = self.reports.get_customer_balances()
            for r in data: ws.append([r['customer'], r['total_bought']])
            wb.save(path)
            messagebox.showinfo("تم", "تم التصدير")

# ════════════════════════════════════════════════════════════════
# نافذة لوحة القياس (Dashboard)
# ════════════════════════════════════════════════════════════════
class DashboardWindow(ToplevelBase):
    def __init__(self, master):
        super().__init__(master)
        self.title("لوحة القياس والرسوم البيانية (Dashboard)")
        self.geometry("1100x650")
        if not HAS_TTKB: 
            self.configure(bg=CLR["bg"])
        self.grab_set()
        self._build()

    def _build(self):
        hdr = UIFrame(self, bg=CLR["header"], pady=10)
        hdr.pack(fill="x")
        UILabel(hdr, text="📈 لوحة القياس التفاعلية (Dashboard)", font=FT_TITLE, bg=CLR["header"], fg="white").pack(side="right", padx=16)

        if not HAS_MATPLOTLIB:
            UILabel(self, text="مكتبة الرسوم البيانية (matplotlib) غير مثبتة", font=FT_HEADER, fg="red").pack(pady=50)
            return

        batches = db.fetch_all("SELECT * FROM v_batches ORDER BY date_in ASC")
        if not batches:
            UILabel(self, text="لا توجد بيانات كافية لعرض الرسوم البيانية.", font=FT_HEADER).pack(pady=50)
            return

        labels = []
        nets = []
        morts = []
        colors = []
        
        for b in batches:
            labels.append(f"دفعة {b['batch_num'] or b['id']}")
            n_val = b['net_result'] or 0
            nets.append(n_val)
            morts.append(b['mort_rate'] or 0)
            if n_val >= 0:
                colors.append(CLR["profit"])
            else:
                colors.append(CLR["loss"])
        
        fig = Figure(figsize=(12, 5), dpi=100)
        fig.patch.set_facecolor(CLR["bg"])

        ax1 = fig.add_subplot(121)
        ax1.bar(labels, nets, color=colors)
        ax1.set_title(prepare_text("صافي الأرباح والخسائر لكل دفعة"), fontsize=14, pad=10)
        ax1.axhline(0, color='black', linewidth=1.2)
        ax1.tick_params(axis='x', rotation=45)

        ax2 = fig.add_subplot(122)
        ax2.plot(labels, morts, marker='o', color=CLR["nav"], linestyle='-', linewidth=2.5, markersize=8)
        ax2.set_title(prepare_text("معدل النافق الكلي (%)"), fontsize=14, pad=10)
        ax2.set_ylim(bottom=0)
        ax2.grid(True, linestyle='--', alpha=0.6)
        ax2.tick_params(axis='x', rotation=45)

        fig.tight_layout(pad=3.0)
        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=15)

# ════════════════════════════════════════════════════════════════
# نافذة تقرير العنابر الشاملة (الإكسل التحليلي)
# ════════════════════════════════════════════════════════════════
class WarehousesReportWindow(ToplevelBase):
    def __init__(self, master):
        super().__init__(master)
        self.title("تقرير العنابر الشامل")
        self.geometry("1200x700")
        if not HAS_TTKB: 
            self.configure(bg=CLR["bg"])
        self._build()
        self._load()

    def _build(self):
        hdr = UIFrame(self, bg=CLR["header"], pady=10)
        hdr.pack(fill="x")
        UILabel(hdr, text="📊 تقرير العنابر الشامل", font=FT_TITLE, bg=CLR["header"], fg="white").pack(side="right", padx=16)

        btn_frm = UIFrame(self, bg=CLR["nav"], pady=6)
        btn_frm.pack(fill="x")
        UIButton(btn_frm, text="📥 تصدير Excel (تحليلي شامل)", font=FT_BODY, bg=CLR["white"], fg=CLR["profit"], padx=10, pady=4, cursor="hand2", relief="flat", command=self._export_excel).pack(side="right", padx=6)
        
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=8, pady=8)
        self.tab_by_wh = UIFrame(nb, bg=CLR["bg"])
        self.tab_overall = UIFrame(nb, bg=CLR["bg"])
        nb.add(self.tab_by_wh, text="📦 ملخص حسب العنبر")
        nb.add(self.tab_overall, text="🏭 الملخص الإجمالي")

        cols_wh = ("العنبر","عدد الدفعات","إجمالي الكتاكيت","إجمالي التكاليف","إجمالي الإيرادات","صافي الربح/الخسارة","متوسط النافق%","متوسط سعر البيع")
        self.tree_wh = ttk.Treeview(self.tab_by_wh, columns=cols_wh, show="headings", selectmode="browse")
        
        widths_wh = [160, 100, 120, 140, 140, 150, 120, 130]
        for c, w in zip(cols_wh, widths_wh): 
            self.tree_wh.heading(c, text=c, anchor="center")
            self.tree_wh.column(c, width=w, anchor="center")
            
        self.tree_wh.tag_configure("profit", background="#f0f9ea")
        self.tree_wh.tag_configure("loss", background="#fff0f0")
        self.tree_wh.pack(fill="both", expand=True)

        cols_all = ("رقم الدفعة","العنبر","تاريخ الدخول","تاريخ الخروج","الأيام","الكتاكيت","التكاليف","الإيرادات","الربح/الخسارة","النافق%","متوسط البيع","نصيب الشركة")
        self.tree_all = ttk.Treeview(self.tab_overall, columns=cols_all, show="headings", selectmode="browse")
        
        widths_all = [80, 130, 95, 95, 55, 85, 110, 110, 120, 70, 100, 110]
        for c, w in zip(cols_all, widths_all): 
            self.tree_all.heading(c, text=c, anchor="center")
            self.tree_all.column(c, width=w, anchor="center")
            
        self.tree_all.tag_configure("profit", background="#f0f9ea")
        self.tree_all.tag_configure("loss", background="#fff0f0")
        self.tree_all.pack(fill="both", expand=True)

        self.sum_frame = UIFrame(self, bg=CLR["info_bg"], pady=8, padx=12)
        self.sum_frame.pack(fill="x")

    def _load(self):
        batches = db.fetch_all("SELECT * FROM v_batches ORDER BY warehouse_name, date_in")
        wh_data = {}
        for b in batches:
            wh = b["warehouse_name"]
            if wh not in wh_data: 
                wh_data[wh] = {"count":0,"chicks":0,"cost":0,"rev":0,"net":0,"mort_sum":0,"sold_sum":0,"cust_mkt_val_sum":0}
            d = wh_data[wh]
            d["count"] += 1
            d["chicks"] += b["chicks"] or 0
            d["cost"] += b["total_cost"] or 0
            d["rev"] += b["total_rev"] or 0
            d["net"] += b["net_result"] or 0
            d["mort_sum"] += b["mort_rate"] or 0
            d["sold_sum"] += b["total_sold"] or 0
            d["cust_mkt_val_sum"] += (b["cust_val"] or 0) + (b["mkt_val"] or 0)

        self.tree_wh.delete(*self.tree_wh.get_children())
        for wh, d in wh_data.items():
            tag = "profit" if d["net"] >= 0 else "loss"
            avg_m = 0
            avg_p = 0
            if d["count"] > 0:
                avg_m = d["mort_sum"]/d["count"]
            if d["sold_sum"] > 0:
                avg_p = d["cust_mkt_val_sum"]/d["sold_sum"]
            self.tree_wh.insert("", "end", tags=(tag,), values=(wh, d["count"], fmt_num(d["chicks"]), fmt_num(d["cost"]), fmt_num(d["rev"]), f"{'+'if d['net']>=0 else ''}{fmt_num(d['net'])}", f"{avg_m:.1f}%", fmt_num(avg_p)))

        self.tree_all.delete(*self.tree_all.get_children())
        T = {"chicks":0,"cost":0,"rev":0,"net":0,"share":0}
        for b in batches:
            b_num = b["batch_num"] if b["batch_num"] else str(b["id"])
            tag = "profit" if (b["net_result"] or 0) >= 0 else "loss"
            self.tree_all.insert("", "end", iid=str(b["id"]), tags=(tag,), values=(b_num, b["warehouse_name"], b["date_in"], b["date_out"], b["days"] or "", fmt_num(b["chicks"]), fmt_num(b["total_cost"]), fmt_num(b["total_rev"]), f"{'+'if (b['net_result'] or 0)>=0 else ''}{fmt_num(b['net_result'])}", f"{b['mort_rate'] or 0:.1f}%", fmt_num(b["avg_price"]), fmt_num(b["share_val"])))
            T["chicks"] += b["chicks"] or 0
            T["cost"] += b["total_cost"] or 0
            T["rev"] += b["total_rev"] or 0
            T["net"] += b["net_result"] or 0
            T["share"] += b["share_val"] or 0

        for w in self.sum_frame.winfo_children(): 
            w.destroy()
            
        sum_items = [
            ("الدفعات", str(len(batches))), 
            ("إجمالي الكتاكيت", fmt_num(T["chicks"])), 
            ("إجمالي التكاليف", fmt_num(T["cost"])), 
            ("إجمالي الإيرادات", fmt_num(T["rev"])), 
            ("صافي النتيجة", f"{'+'if T['net']>=0 else ''}{fmt_num(T['net'])}"), 
            ("نصيب الشركة", fmt_num(T["share"]))
        ]
        
        for lbl, val in sum_items:
            f = UIFrame(self.sum_frame, bg=CLR["white"], padx=15, pady=8, relief="solid", bd=1)
            f.pack(side="right", padx=6)
            UILabel(f, text=lbl, font=FT_TINY, bg=CLR["white"], fg=CLR["text2"]).pack()
            
            val_color = CLR["header"]
            if "الإيرادات" in lbl or ("صافي" in lbl and "+" in val):
                val_color = CLR["profit"]
            elif "التكاليف" in lbl or ("صافي" in lbl and "-" in val):
                val_color = CLR["loss"]
                
            UILabel(f, text=val, font=(FN, 12, "bold"), bg=CLR["white"], fg=val_color).pack(pady=(2,0))

    def _export_excel(self):
        if not HAS_OPENPYXL: 
            return messagebox.showerror("خطأ", "يرجى تثبيت مكتبة openpyxl:\npip install openpyxl", parent=self)
            
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel","*.xlsx")], initialfile=f"التقرير_التحليلي_للعنابر_{datetime.now().strftime('%Y%m%d')}.xlsx", parent=self)
        if not path: 
            return
        
        wb = openpyxl.Workbook()
        hdr_fill = PatternFill("solid", fgColor="1F4E79")
        center = Alignment(horizontal="center", vertical="center")
        thin = Side(style='thin', color='AAAAAA')
        brd = Border(left=thin, right=thin, top=thin, bottom=thin)

        # ── الشيت 1: الخلاصة العامة ──
        ws1 = wb.active
        ws1.title = "الخلاصة الإجمالية"
        ws1.sheet_view.rightToLeft = True
        batches = db.fetch_all("SELECT * FROM v_batches ORDER BY warehouse_name, date_in")
        headers1 = ["رقم الدفعة", "العنبر", "الدخول", "الخروج", "الأيام", "كتاكيت(عدد)", "كتاكيت(قيمة)", "إجمالي التكاليف", "إجمالي الإيرادات", "صافي النتيجة", "ملاحظات"]
        
        for c, h in enumerate(headers1, 1):
            cell = ws1.cell(1, c, h)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = hdr_fill
            cell.alignment = center
            ws1.column_dimensions[get_column_letter(c)].width = 15
            
        for i, b in enumerate(batches, 2):
            b_num = b["batch_num"] if b["batch_num"] else str(b["id"])
            row = [b_num, b["warehouse_name"], b["date_in"], b["date_out"], b["days"] or 0, b["chicks"] or 0, b["chick_val"] or 0, b["total_cost"] or 0, b["total_rev"] or 0, b["net_result"] or 0, b["notes"] or ""]
            for c, v in enumerate(row, 1):
                cell = ws1.cell(i, c, v)
                cell.border = brd
                cell.alignment = center
                if c in [6,7,8,9,10]: 
                    cell.number_format = '#,##0'

        # ── الشيت 2: تفاصيل مبيعات العنبر ──
        ws2 = wb.create_sheet("تفاصيل مبيعات العنبر")
        ws2.sheet_view.rightToLeft = True
        f_sales = db.fetch_all("SELECT f.*, b.batch_num, w.name AS wh_name FROM farm_sales f JOIN batches b ON f.batch_id=b.id JOIN warehouses w ON b.warehouse_id=w.id ORDER BY w.name, b.date_in")
        headers2 = ["العنبر", "رقم الدفعة", "اسم العميل", "الكمية", "السعر", "الإجمالي"]
        
        for c, h in enumerate(headers2, 1):
            cell = ws2.cell(1, c, h)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = hdr_fill
            cell.alignment = center
            ws2.column_dimensions[get_column_letter(c)].width = 18
            
        for i, s in enumerate(f_sales, 2):
            b_n = s["batch_num"] if s["batch_num"] else s["batch_id"]
            row = [s["wh_name"], b_n, s["customer"], s["qty"], s["price"], s["total_val"]]

            for c, v in enumerate(row, 1):

                cell = ws2.cell(i, c, v)

                cell.border = brd

                cell.alignment = center

                if c in [4,5,6]: 

                    if c == 5:

                        cell.number_format = '#,##0.00'

                    else:

                        cell.number_format = '#,##0'



        # ── الشيت 3: تفاصيل مبيعات السوق ──

        ws3 = wb.create_sheet("تفاصيل مبيعات السوق")

        ws3.sheet_view.rightToLeft = True

        m_sales = db.fetch_all("SELECT m.*, b.batch_num, w.name AS wh_name FROM market_sales m JOIN batches b ON m.batch_id=b.id JOIN warehouses w ON b.warehouse_id=w.id ORDER BY w.name, b.date_in")

        headers3 = ["العنبر", "رقم الدفعة", "مكتب التسويق", "الكمية المرسلة", "الوفيات", "المباع", "صافي الفاتورة", "رقم الفاتورة"]

        

        for c, h in enumerate(headers3, 1):

            cell = ws3.cell(1, c, h)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = hdr_fill
            cell.alignment = center
            ws3.column_dimensions[get_column_letter(c)].width = 15
            
        for i, s in enumerate(m_sales, 2):
            b_n = s["batch_num"] if s["batch_num"] else s["batch_id"]
            row = [s["wh_name"], b_n, s["office"], s["qty_sent"], s["deaths"], s["qty_sold"], s["net_val"], s["inv_num"]]
            for c, v in enumerate(row, 1):
                cell = ws3.cell(i, c, v)
                cell.border = brd
                cell.alignment = center
                if c in [4,5,6,7]: 
                    cell.number_format = '#,##0'

        # ── الشيت 4: التكاليف التحليلية ──
        ws4 = wb.create_sheet("التكاليف التحليلية")
        ws4.sheet_view.rightToLeft = True
        headers4 = ["العنبر", "رقم الدفعة", "علف(كمية)", "علف(قيمة)", "أجور نقل علف", "نشارة(كمية)", "نشارة(قيمة)", "ماء", "غاز(كمية)", "غاز(قيمة)", "علاجات", "مصاريف عنبر", "مصاريف بيت", "أجور مربيين", "قات", "إيجار", "إضاءة", "مشرفين", "إدارة", "لقاحات", "أخرى"]
        
        for c, h in enumerate(headers4, 1):
            cell = ws4.cell(1, c, h)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = hdr_fill
            cell.alignment = center
            ws4.column_dimensions[get_column_letter(c)].width = 14
            
        for i, b in enumerate(batches, 2):
            b_n = b["batch_num"] if b["batch_num"] else b["id"]
            superv = (b["sup_wh_pay"] or 0) + (b["sup_co_pay"] or 0) + (b["sup_sale_pay"] or 0)
            other_c = (b["delivery_val"] or 0) + (b["mixing_val"] or 0) + (b["wash_val"] or 0) + (b["other_costs"] or 0)
            row = [b["warehouse_name"], b_n, b["feed_qty"], b["feed_val"], b["feed_trans"], b["sawdust_qty"], b["sawdust_val"], b["water_val"], b["gas_qty"], b["gas_val"], b["drugs_val"], b["wh_expenses"], b["house_exp"], b["breeders_pay"], b["qat_pay"], b["rent_val"], b["light_val"], superv, b["admin_val"], b["vaccine_pay"], other_c]
            
            for c, v in enumerate(row, 1):
                cell = ws4.cell(i, c, v)
                cell.border = brd
                cell.alignment = center
                if c > 2: 
                    cell.number_format = '#,##0'

        wb.save(path)
        messagebox.showinfo("تم", f"تم التصدير التحليلي الشامل بنجاح!\n{path}", parent=self)
        try: 
            os.startfile(path)
        except: 
            pass

# (تم دمج منطق الاستيراد في core/batch_importer.py)

    def _extract_wh_name(self, filename):
        """يستخرج اسم العنبر من اسم الملف بشكل ذكي"""
        # إزالة المسافات والحروف غير المرئية (مثل RLM)
        import unicodedata
        clean = ''.join(c for c in filename if unicodedata.category(c) not in ('Cf',))
        clean = clean.strip()
        # تقطيع عند كلمة "دفعة" -> ما قبلها هو اسم العنبر
        for sep in ['دفعة', 'دورة', 'batch', 'Batch']:
            if sep in clean:
                part = clean.split(sep)[0].strip()
                if part:
                    return part
        return clean[:40]

    def _find_sheet_by_keywords(self, keywords):
        """يجد الورقة الأفضل تطابقاً للكلمات المفتاحية"""
        best, best_score = None, 0
        for name in self.wb.sheetnames:
            score = sum(1 for kw in keywords if kw in name)
            if score > best_score:
                best, best_score = name, score
        return self.wb[best] if best else None

    def _sf(self, v):
        """\u062a\u062d\u0648\u064a\u0644 \u0622\u0645\u0646 \u0644\u0639\u062f\u062f \u062d\u0642\u064a\u0642\u064a"""
        try:
            return float(str(v).replace(',', '').replace(' ', '')) if v not in (None, '', '#DIV/0!') else 0.0
        except:
            return 0.0

    def _si(self, v):
        """\u062a\u062d\u0648\u064a\u0644 \u0622\u0645\u0646 \u0644\u0639\u062f\u062f \u0635\u062d\u064a\u062d"""
        try:
            return int(float(str(v).replace(',', '').replace(' ', ''))) if v not in (None, '', '#DIV/0!') else 0
        except:
            return 0

    # -------- 1. كرت العنبر (سجلات يومية) --------
    def _parse_daily(self, ws):
        rows = list(ws.iter_rows(values_only=True))

        def _is_date_row(row):
            """يتحقق أن الصف يبدأ بتاريخ في أول 3 خلايا"""
            for cell in row[:3]:
                if cell is None:
                    continue
                # datetime.datetime مباشرة
                if hasattr(cell, "year") and hasattr(cell, "month"):
                    return True
                # نص يشبه تاريخ
                s = str(cell).strip()[:10]
                try:
                    datetime.strptime(s, "%Y-%m-%d")
                    return True
                except:
                    pass
            return False

        # إيجاد سطر الرأس: العنوانات مثل التاريخ والوفيات
        # يجب أن يكون الصف التالي صف بيانات تاريخ حقيقي
        hdr = -1
        for i, row in enumerate(rows):
            flat = " ".join(str(c) for c in row if c is not None)
            if "التاريخ" in flat and ("الوفيات" in flat or "النافق" in flat):
                # تحقق: هل الصف التالي له تاريخ حقيقي؟
                for j in range(i+1, min(i+4, len(rows))):
                    if _is_date_row(rows[j]):
                        hdr = i
                        break
                if hdr >= 0:
                    break

        if hdr < 0:
            return  # لا يوجد رأس مناسب

        # حدد مواضع الأعمدة من صف الرأس
        col_date, col_age, col_dead, col_feed_daily = 0, 1, 3, 5
        hdr_row = rows[hdr] if rows else ()
        for ci, cell in enumerate(hdr_row):
            cv = str(cell or "").strip()
            if cv == "التاريخ" or (cv.startswith("تاريخ") and "عمر" not in cv):
                col_date = ci
            elif "العمر" in cv:
                col_age = ci
            elif cv == "الوفيات" and "اجمالي" not in cv:
                col_dead = ci
            elif cv == "نافق" and "اجمالي" not in cv:
                col_dead = ci
            elif "مستهلك" in cv:  # العلف المستهلك يومياً
                col_feed_daily = ci

        daily = []
        for row in rows[hdr + 1:]:
            if not row or len(row) <= col_date:
                continue
            if not _is_date_row(row):
                continue  # تخطى صفوف الإجماليات والعناوين

            date_val = row[col_date] if len(row) > col_date else None
            if date_val is None:
                continue

            if hasattr(date_val, "strftime"):
                rec_date = date_val.strftime("%Y-%m-%d")
            else:
                parsed = None
                for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"):
                    try:
                        parsed = datetime.strptime(str(date_val).strip()[:10], fmt)
                        break
                    except:
                        pass
                if not parsed:
                    continue
                rec_date = parsed.strftime("%Y-%m-%d")

            day_num = self._si(row[col_age] if len(row) > col_age else 0)
            dead    = self._si(row[col_dead] if len(row) > col_dead else 0)
            feed_kg = self._sf(row[col_feed_daily] if len(row) > col_feed_daily else 0)

            daily.append({"rec_date": rec_date, "day_num": day_num, "dead_count": dead, "feed_kg": feed_kg})

        self.daily_rows = daily

    def _parse_farm_sales(self, ws):
        """
        يستخرج المبيعات من ورقة بيان المبيعات.

        هيكل الورقة الثابت:
          - صف 0: عنوان مدمج (يتجاوز)
          - صف 1: رأس الأعمدة (يتجاوز)
          - صف 2+: بيانات فعلية

        تقسيم الأعمدة (ثابت):
          مبيعات العنبر  — A-G  (0-6)
            col 0: اسم العميل
            col 1: العدد  (آجل)
            col 2: السعر  (آجل)
            col 3: إجمالي (آجل)
            col 4: العدد  (نقداً)
            col 5: السعر  (نقداً)
            col 6: إجمالي (نقداً)
          مبيعات السوق   — H-N  (7-13)
            col 7:  اسم المكتب / السائق
            col 8:  الكمية المرسلة
            col 9:  الوفيات
            col 10: المباع
            col 11: صافي الفاتورة
            col 12: رقم الفاتورة
            col 13: التاريخ
        """
        rows = list(ws.iter_rows(values_only=True))
        
        # ── تحديد سطر بداية البيانات ──
        # إذا كان الصف 1 يحتوي كلمات رأس (اسم / عدد) نبدأ من صف 2
        # وإلا نبدأ من صف 0 مباشرة
        data_start = 0
        for i, row in enumerate(rows[:5]):
            flat = " ".join(str(c) for c in row if c is not None)
            if "اسم العميل" in flat or ("العدد" in flat and "السعر" in flat):
                data_start = i + 1   # ابدأ بعد سطر الرأس
                break
        
        # إذا وجدنا سطر رأس مدمج في الصف 0 و رأس حقيقي في الصف 1 → ابدأ من 2
        if data_start == 1:
            flat0 = " ".join(str(c) for c in rows[0] if c is not None)
            if any(kw in flat0 for kw in ["بيان مبيعات", "عنبر", "الفترة"]):
                data_start = 2   # تجاوز صف العنوان + صف الرأس
        
        farm_sales   = []
        market_sales = []

        # قائمة كلمات يجب تجاهلها
        SKIP_WORDS = {"الاجمالي", "إجمالي", "اجمالي", "المجموع", "الاجماليات",
                      "البيان", "بيان", "None", "", "0", "اسم العميل"}

        for row in rows[data_start:]:
            if not row or all(c is None for c in row):
                continue
            ncols = len(row)

            # ─── مبيعات العنبر (cols 0-6) ───
            cust = str(row[0] or "").strip()
            if cust and cust not in SKIP_WORDS and "#" not in cust:
                qty_ajl   = self._si(row[1] if ncols > 1 else 0)
                price_ajl = self._sf(row[2] if ncols > 2 else 0)
                total_ajl = self._sf(row[3] if ncols > 3 else 0)
                qty_nqd   = self._si(row[4] if ncols > 4 else 0)
                price_nqd = self._sf(row[5] if ncols > 5 else 0)
                total_nqd = self._sf(row[6] if ncols > 6 else 0)

                # احسب السعر إذا كان فارغاً
                if not price_ajl and qty_ajl > 0 and total_ajl > 0:
                    price_ajl = round(total_ajl / qty_ajl, 2)
                if not price_nqd and qty_nqd > 0 and total_nqd > 0:
                    price_nqd = round(total_nqd / qty_nqd, 2)

                # مبيعات آجل (دين)
                if qty_ajl > 0:
                    farm_sales.append({
                        "customer":  cust,
                        "qty":       qty_ajl,
                        "price":     price_ajl,
                        "total_val": total_ajl or qty_ajl * price_ajl
                    })

                # مبيعات نقداً (إذا وجدت) — تُسجّل كسجل منفصل بنفس الاسم
                if qty_nqd > 0:
                    farm_sales.append({
                        "customer":  cust + " (نقداً)",
                        "qty":       qty_nqd,
                        "price":     price_nqd,
                        "total_val": total_nqd or qty_nqd * price_nqd
                    })

            # ─── مبيعات السوق (cols 7-13) — فقط إذا الورقة لها >7 أعمدة ───
            if ncols > 7:
                office = str(row[7] or "").strip()
                if office and office not in SKIP_WORDS and "#" not in office:
                    ms_qty  = self._si(row[8]  if ncols > 8  else 0)
                    ms_dead = self._si(row[9]  if ncols > 9  else 0)
                    ms_sold = self._si(row[10] if ncols > 10 else 0)
                    ms_net  = self._sf(row[11] if ncols > 11 else 0)
                    ms_inv  = str(row[12] or "").strip() if ncols > 12 else ""
                    if ms_qty > 0 or ms_net > 0:
                        market_sales.append({
                            "office":    office,
                            "qty_sent":  ms_qty,
                            "deaths":    ms_dead,
                            "qty_sold":  ms_sold or max(0, ms_qty - ms_dead),
                            "net_val":   ms_net,
                            "inv_num":   ms_inv
                        })

        self.farm_sales   = farm_sales
        self.market_sales = market_sales

    def _parse_summary(self, ws):
        """
        يستخرج بيانات التكاليف والإيرادات من ورقة التصفية.
        الخريطة تطابق أسماء الحقول الفعلية في قاعدة البيانات.
        """
        # الخريطة: (قائمة الكلمات المفتاحية، اسم العمود في قاعدة البيانات)
        mapping = [
            # بيانات الكتاكيت
            (['الكتاكيت', 'عدد الكتاكيت', 'طيور', 'عدد الطيور'],       'chicks'),
            (['قيمة الكتاكيت', 'تكلفة الكتاكيت', 'إجمالي قيمة الكتاكيت'],  'chick_val'),
            # العلف
            (['قيمة العلف', 'تكلفة العلف', 'علف\u2014قيمة', 'علف قيمة'],    'feed_val'),
            (['نقل علف', 'أجور نقل', 'بقشيش', 'أجور نقل و بقشيش'],      'feed_trans'),
            (['علف\u2014كمية', 'علف كمية', 'عدد أكياس العلف'],               'feed_qty'),
            # النشارة
            (['نشارة\u2014قيمة', 'نشارة قيمة', 'قيمة النشارة', 'النشارة'],   'sawdust_val'),
            (['نشارة\u2014كمية', 'كمية نشارة'],                               'sawdust_qty'),
            # الغاز
            (['غاز\u2014قيمة', 'غاز قيمة', 'قيمة الغاز', 'الغاز'],          'gas_val'),
            (['غاز\u2014كمية', 'كمية غاز'],                                   'gas_qty'),
            # مياه وكهرباء
            (['مياه', 'مياة', 'قيمة الماء'],                              'water_val'),
            (['كهرباء', 'الكهرباء', 'إضاءة'],                            'light_val'),
            # علاجات
            (['العلاجات', 'ادوية', 'أدوية بيطرية', 'علاج'],             'drugs_val'),
            # أجور مربيين
            (['رواتب', 'أجور مربيين'],                                   'breeders_pay'),
            # مصاريف عنبر
            (['صيانة مباني', 'صيانة و اصلاح', 'مصاريف العنبر'],         'wh_expenses'),
            # مصاريف بيت
            (['مصاريف بيت', 'مصاريف المنزل', 'مصاريف البيت'],           'house_exp'),
            # قات مربيين
            (['قات مربيين', 'قات المربيين'],                             'qat_pay'),
            # إيجار
            (['إيجار', 'ايجار'],                                         'rent_val'),
            # مشرفين
            (['مشرف عنبر'],                                              'sup_wh_pay'),
            (['مشرف شركة'],                                              'sup_co_pay'),
            (['مشرف بيع'],                                               'sup_sale_pay'),
            # إدارة
            (['إدارة وحسابات', 'قرطاسية', 'بريد و هاتف'],               'admin_val'),
            # لقاحات
            (['أجور لقاحات', 'لقاحات', 'تطعيم'],                        'vaccine_pay'),
            # توصيل
            (['توصيل خدمات', 'توصيل'],                                   'delivery_val'),
            # حمالة وخلط
            (['حمالة وخلط', 'خلط'],                                      'mixing_val'),
            # نظافة وتغسيل
            (['تغسيل عنبر', 'نظافة', 'تغسيل'],                          'wash_val'),
            # محروقات
            (['محروقات', 'مصاريف أخرى', 'أخرى'],                        'other_costs'),
            # إجماليات
            (['جمالي المصاريف', 'اجمالي المصاريف', 'إجمالي المصاريف'],  'total_cost'),
            (['جمالي الايردات', 'اجمالي الايرادات', 'إجمالي الإيرادات'], 'total_rev'),
            (['نتيجة الدفعة', 'صافي الربح', 'صافي النتيجة'],            'net_result'),
            (['عدد المبيعات'],                                            'total_sold'),
            (['وفيات في العنبر', 'وفيات العنبر'],                        'total_dead'),
            (['ذبيل', 'إيرادات ذبيل'],                                   'offal_val'),
        ]
        d = {}
        for row in ws.iter_rows(values_only=True):
            # افحص كل خلية كأنها تسمية محتملة
            for ci, cell_label in enumerate(row):
                if cell_label is None:
                    continue
                label_str = str(cell_label).strip()
                # ابحث عن أول رقم في نفس الصف بعد التسمية
                val_candidate = None
                for cell_val in row[ci+1:]:
                    if cell_val is not None and str(cell_val) not in ('', '#DIV/0!', '#VALUE!', '#REF!'):
                        try:
                            val_candidate = float(str(cell_val).replace(',', '').replace(' ', ''))
                            break
                        except:
                            pass  # نص آخر، استمر

                for keywords, db_col in mapping:
                    if any(kw in label_str for kw in keywords):
                        if val_candidate is not None and db_col not in d:
                            d[db_col] = val_candidate

        self.result = d


    def run(self):
        def _sheet_has_daily_data(ws):
            """يتحقق أن الورقة تحتوي على بيانات يومية حقيقية"""
            rows_checked = list(ws.iter_rows(values_only=True, max_row=15))
            for i, row in enumerate(rows_checked):
                flat = " ".join(str(c) for c in row if c is not None)
                if "التاريخ" in flat and ("الوفيات" in flat or "النافق" in flat):
                    # تحقق: هل الصف التالي يحتوي تاريخ datetime؟
                    for j in range(i+1, min(i+4, len(rows_checked))):
                        next_row = rows_checked[j]
                        if next_row and next_row[0] is not None:
                            if hasattr(next_row[0], "year"):
                                return True
            return False

        # Step1: بحث بالكلمات المفتاحية في اسم الورقة
        ws_daily = self._find_sheet_by_keywords(["كرت", "يومي", "نافق", "حصر"])
        # Step2: fallback - أي ورقة تحتوي بيانات يومية حقيقية
        if not ws_daily:
            for name in self.wb.sheetnames:
                if _sheet_has_daily_data(self.wb[name]):
                    ws_daily = self.wb[name]
                    break
        if ws_daily:
            self._parse_daily(ws_daily)
        else:
            self.errors.append("لم يُعثر على ورقة كرت العنبر")

        # find sales sheet (تجنب الورقة اليومية)
        ws_sales = self._find_sheet_by_keywords(["مبيعات", "بيع", "عميل", "عملاء", "بيان"])
        if ws_sales and ws_daily and ws_sales.title == ws_daily.title:
            ws_sales = None
        if ws_sales:
            self._parse_farm_sales(ws_sales)

        # find costs/summary sheet
        ws_sum = self._find_sheet_by_keywords(["تصفية", "حسابات", "تكاليف", "ملخص", "مالي", "اجمالي"])
        if not ws_sum:
            ws_sum = self.wb.worksheets[0] if self.wb.worksheets else None
        if ws_sum:
            self._parse_summary(ws_sum)

        return self




# ════════════════════════════════════════════════════════════════
# النافذة الرئيسية
# ════════════════════════════════════════════════════════════════
class MainWindow(WindowBase):
    def __init__(self):
        if HAS_TTKB:
            try: 
                super().__init__(themename="lumen")
            except: 
                super().__init__()
        else: 
            super().__init__()
            
        self.title("نظام إدارة عنابر الدجاج اللاحم — النسخة المطورة 3.8")
        self.geometry("1200x700")
        if not HAS_TTKB: 
            self.configure(bg=CLR["bg"])
        self.resizable(True, True)
        self.db = db
        self.reports = ReportsManager(db, 
                                     font_path=os.path.join(BASE_DIR, "assets", "Amiri-Regular.ttf"),
                                     logo_path=os.path.join(BASE_DIR, "assets", "logo.png"))
        self._build()
        self._load_batches()
        
        # ربط الاختصارات (Keyboard Shortcuts)
        self.bind("<Control-n>", lambda e: self._new_batch())
        self.bind("<Control-N>", lambda e: self._new_batch())
        self.bind("<Control-p>", lambda e: self._open_reports())
        self.bind("<Control-P>", lambda e: self._open_reports())
        self.bind("<Control-f>", lambda e: self.filter_wh.focus_set())
        self.bind("<Control-F>", lambda e: self.filter_wh.focus_set())

    def _change_theme(self, event):
        if HAS_TTKB:
            new_theme = self.theme_cbo.get()
            try:
                self.style.theme_use(new_theme)
                self._load_batches() # لتحديث ألوان الجداول حسب السمة الجديدة
            except:
                pass

    def _build(self):
        if HAS_TTKB:
            # هيدر علوي مريح للعين
            hdr = ttkb.Frame(self, padding=(20, 15), bootstyle="primary")
            hdr.pack(fill="x")
            
            UILabel(hdr, text="🐔 نظام إدارة عنابر الدجاج اللاحم", font=("Segoe UI", 18, "bold"), bootstyle="inverse-primary").pack(side="right")
            self.lbl_count = UILabel(hdr, text="", font=FT_BODY, bootstyle="inverse-primary")
            self.lbl_count.pack(side="right", padx=30)

            # تبديل السمة (Theme)
            themes = self.style.theme_names() if hasattr(self, 'style') else ttkb.Style().theme_names()
            self.theme_cbo = ttkb.Combobox(hdr, values=themes, width=12, state="readonly", bootstyle="info")
            self.theme_cbo.pack(side="left", padx=10)
            self.theme_cbo.set("lumen")
            self.theme_cbo.bind("<<ComboboxSelected>>", self._change_theme)
            UILabel(hdr, text="مظهر النظام:", font=FT_SMALL, bootstyle="inverse-primary").pack(side="left")

            # شريط أدوات منظم وسهل الاستخدام
            tb = ttkb.Frame(self, padding=8, bootstyle="secondary")
            tb.pack(fill="x")
            
            main_btns = [
                ("+ دفعة جديدة", self._new_batch, "success", "دورة جديدة"),
                ("✏️ تعديل", self._edit_batch, "warning", "تعديل البيانات"),
                ("🗑 حذف", self._del_batch, "danger", "حذف نهائي"),
                ("📅 السجلات اليومية", self._open_daily, "info", "سجل يومي"),
                ("📊 تقرير العنابر", self._open_wh_report, "primary", "تحليل مالي"),
                ("📈 لوحة القياس", self._open_dashboard, "success-outline", "رسوم بيانية"),
                ("🖨️ PDF", self._export_pdf, "info-outline", "تصدير PDF"),
                ("📊 مركز التقارير", self._open_reports, "info", "كشوفات وتقارير محاسبية"),
                ("📥 استيراد Excel", self._import_excel, "warning-outline", "من ملف"),
                ("📂 استيراد مجلد", self._import_folder, "warning", "من مجلد كامل"),
                ("💾 نسخة احتياطية", self._backup, "secondary-outline", "حفظ البيانات")
            ]
            
            for txt, cmd, bstyle, ttip in main_btns:
                btn = UIButton(tb, text=txt, command=cmd, bootstyle=bstyle)
                btn.pack(side="right", padx=4)
                if hasattr(ttkb, 'ToolTip'):
                    ttkb.ToolTip(btn, text=ttip, bootstyle=bstyle)

            # شريط التصفية والبحث
            fbar = ttkb.Frame(self, padding=8)
            fbar.pack(fill="x", padx=12)
            
            UILabel(fbar, text="تصفية حسب العنبر:", font=FT_SMALL).pack(side="right", padx=5)
            self.filter_wh = ttkb.Combobox(fbar, width=22, font=FT_BODY)
            self.filter_wh.pack(side="right", padx=4)
            self.filter_wh.bind("<<ComboboxSelected>>", lambda e: self._load_batches())
            
            ttkb.Button(fbar, text="🔄 عرض الكل", command=lambda: [self.filter_wh.set(""), self._load_batches()], bootstyle="link").pack(side="right", padx=10)

            # زر تبديل الوضع الليلي
            self.dark_var = tk.BooleanVar(value=False)
            self.dark_btn = ttkb.Checkbutton(fbar, text="🌙 وضع ليلي", variable=self.dark_var, command=self._toggle_dark, bootstyle="round-toggle")
            self.dark_btn.pack(side="left", padx=20)

            # لوحة الإحصائيات (KPI Cards) - تصميم Classic Plus
            self.kpi_frame = ttkb.Frame(self, padding=(12, 10))
            self.kpi_frame.pack(fill="x", padx=12)

            # منطقة عرض البيانات الرئيسية
            frm = ttkb.Frame(self)
            frm.pack(fill="both", expand=True, padx=12, pady=(0, 12))
            
            cols = ("رقم الدفعة","العنبر","تاريخ الدخول","تاريخ الخروج","الأيام","الكتاكيت","التكاليف","الإيرادات","صافي النتيجة","النافق%","معدل FCR","نصيب الشركة")
            self.tree = ttkb.Treeview(frm, columns=cols, show="headings", selectmode="browse", bootstyle="primary")
            
        else:
            # النسخة العادية (Standard UI)
            hdr = UIFrame(self, bg=CLR["header"], pady=10)
            hdr.pack(fill="x")
            UILabel(hdr, text="🐔 نظام إدارة عنابر الدجاج اللاحم", font=("Arial",16,"bold"), bg=CLR["header"], fg="white").pack(side="right", padx=20)
            self.lbl_count = UILabel(hdr, text="", font=FT_BODY, bg=CLR["header"], fg="#aad4f5")
            self.lbl_count.pack(side="left", padx=20)

            tb = UIFrame(self, bg=CLR["nav"], pady=6)
            tb.pack(fill="x")
            
            main_btns = [
                ("+ دفعة جديدة", self._new_batch, "#ffffff"),
                ("✏️ تعديل", self._edit_batch, "#d0e8ff"),
                ("🗑 حذف", self._del_batch, "#fce4d6"),
                ("📅 السجلات اليومية", self._open_daily, "#fff2cc"),
                ("📊 تقرير العنابر", self._open_wh_report, "#dce6f1"),
                ("📈 لوحة القياس", self._open_dashboard, "#e2efda"),
                ("🖨️ تصفية PDF", self._export_pdf, "#b3e5fc"),
                ("📊 مركز التقارير", self._open_reports, "#b3e5fc"),
                ("📥 استيراد Excel", self._import_excel, "#fff2cc"),
                ("📂 استيراد مجلد", self._import_folder, "#ffe699"),
                ("💾 نسخ احتياطي", self._backup, "#f5f5f5")
            ]
            
            for txt, cmd, bg in main_btns:
                UIButton(tb, text=txt, command=cmd, font=FT_SMALL, bg=bg, fg=CLR["text"], padx=8, pady=4, cursor="hand2", relief="flat").pack(side="right", padx=3)

            fbar = UIFrame(self, bg=CLR["bg"], pady=4)
            fbar.pack(fill="x", padx=8)
            
            self.filter_wh = ttk.Combobox(fbar, width=20, font=FT_BODY)
            self.filter_wh.pack(side="right", padx=4)
            self.filter_wh.bind("<<ComboboxSelected>>", lambda e: self._load_batches())
            
            UIButton(fbar, text="عرض الكل", font=FT_SMALL, command=lambda: [self.filter_wh.set(""), self._load_batches()], bg=CLR["bg"], relief="flat").pack(side="right", padx=4)

            self.kpi_frame = UIFrame(self, bg=CLR["bg"])
            self.kpi_frame.pack(fill="x", padx=8, pady=4)
            
            frm = UIFrame(self, bg=CLR["bg"])
            frm.pack(fill="both", expand=True, padx=8, pady=(0,8))
            
            cols = ("رقم الدفعة","العنبر","تاريخ الدخول","تاريخ الخروج","الأيام","الكتاكيت","التكاليف","الإيرادات","صافي النتيجة","النافق%","معدل FCR","نصيب الشركة")
            self.tree = ttk.Treeview(frm, columns=cols, show="headings", selectmode="browse")

        # إعداد الأعمدة (مشترك)
        widths_m = [80, 150, 100, 100, 50, 90, 110, 110, 120, 70, 80, 110]
        for c, w in zip(cols, widths_m): 
            self.tree.heading(c, text=c, anchor="center")
            anc = "center"
            if c == "العنبر": anc = "e"
            self.tree.column(c, width=w, anchor=anc)
            
        self.tree.bind("<Double-1>", lambda e: self._edit_batch())
        
        sb_y = ttk.Scrollbar(frm, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb_y.set)
        sb_y.pack(side="left", fill="y")
        self.tree.pack(fill="both", expand=True)

        # شريط الحالة (Status Bar)
        self.status_bar = ttkb.Frame(self, bootstyle="secondary", padding=5) if HAS_TTKB else UIFrame(self, bg="#f0f0f0", pady=2)
        self.status_bar.pack(side="bottom", fill="x")
        self.lbl_status = UILabel(self.status_bar, text="جاهز", font=FT_SMALL)
        self.lbl_status.pack(side="right", padx=10)
        
        last_bk = "غير متاح"
        if os.path.exists("backups"):
            bks = os.listdir("backups")
            if bks: last_bk = max(bks)
        self.lbl_backup = UILabel(self.status_bar, text=f"آخر نسخة احتياطية: {last_bk}", font=FT_SMALL)
        self.lbl_backup.pack(side="left", padx=10)

        # تحسين شكل الجدول
        s = ttk.Style()
        s.configure("Treeview", rowheight=35, font=FT_BODY) 
        s.configure("Treeview.Heading", font=FT_HEADER)

    def _open_reports(self):
        ReportsCenterWindow(self)

    def _toggle_dark(self):
        if not HAS_TTKB: return
        self.style.theme_use("darkly" if self.dark_var.get() else "lumen")
        self._load_batches()

    def _load_batches(self):
        wh_filter = self.filter_wh.get().strip()
        if wh_filter:
            rows = db.fetch_all("SELECT * FROM v_batches WHERE warehouse_name=? ORDER BY date_in DESC", (wh_filter,))
        else:
            rows = db.fetch_all("SELECT * FROM v_batches ORDER BY date_in DESC")
        
        wh_list = [""]
        for r in db.fetch_all("SELECT name FROM warehouses ORDER BY name"):
            wh_list.append(r["name"])
        self.filter_wh["values"] = wh_list
        
        self.tree.delete(*self.tree.get_children())

        T = {"cost":0,"rev":0,"net":0,"chicks":0,"share":0}
        for b in rows:
            profit = False
            if (b["net_result"] or 0) >= 0:
                profit = True
            mort = b["mort_rate"] or 0
            b_num = b["batch_num"] if b["batch_num"] else str(b["id"])
            tag = "profit" if profit else "loss"
            sign = "+" if profit else ""
            self.tree.insert("", "end", iid=str(b["id"]), tags=(tag,), values=(b_num, b["warehouse_name"], b["date_in"], b["date_out"], b["days"], fmt_num(b["chicks"]), fmt_num(b["total_cost"]), fmt_num(b["total_rev"]), f"{sign}{fmt_num(b['net_result'])}", f"{mort:.1f}%", b["fcr"] or "0", fmt_num(b["share_val"])))
            
            T["cost"] += b["total_cost"] or 0
            T["rev"] += b["total_rev"] or 0
            T["net"] += b["net_result"] or 0
            T["chicks"] += b["chicks"] or 0
            T["share"] += b["share_val"] or 0

        for w in self.kpi_frame.winfo_children(): 
            w.destroy()
            
        sign_net = "+" if T['net'] >= 0 else ""
        
        if HAS_TTKB:
            kpis = [
                ("الدفعات", str(len(rows)), "primary", "secondary"), 
                ("إجمالي الكتاكيت", fmt_num(T["chicks"]), "info", "secondary"), 
                ("إجمالي التكاليف", fmt_num(T["cost"]), "danger", "secondary"), 
                ("إجمالي الإيرادات",fmt_num(T["rev"]), "success", "secondary"), 
                ("صافي النتيجة", f"{sign_net}{fmt_num(T['net'])}", "success" if T["net"]>=0 else "danger", "success" if T["net"]>=0 else "danger"), 
                ("نصيب الشركة", fmt_num(T["share"]), "warning", "secondary")
            ]
            
            for lbl, val, val_bstyle, frm_bstyle in kpis:
                # To make KPI card, we use nested frames or standard text but styled
                lfrm = ttkb.Frame(self.kpi_frame, padding=8)
                lfrm.pack(side="right", padx=5)
                ttkb.Label(lfrm, text=lbl, font=FT_SMALL, bootstyle=frm_bstyle).pack()
                ttkb.Label(lfrm, text=val, font=("Arial",14,"bold"), bootstyle=val_bstyle).pack()
        else:
            kpis = [
                ("الدفعات", str(len(rows)), "#dce6f1", CLR["header"]), 
                ("إجمالي الكتاكيت", fmt_num(T["chicks"]), "#dce6f1", CLR["header"]), 
                ("إجمالي التكاليف", fmt_num(T["cost"]), CLR["loss_bg"], CLR["loss"]), 
                ("إجمالي الإيرادات",fmt_num(T["rev"]), CLR["profit_bg"], CLR["profit"]), 
                ("صافي النتيجة", f"{sign_net}{fmt_num(T['net'])}", CLR["profit_bg"] if T["net"]>=0 else CLR["loss_bg"], CLR["profit"] if T["net"]>=0 else CLR["loss"]), 
                ("نصيب الشركة", fmt_num(T["share"]), "#fff2cc", CLR["warn"])
            ]
            
            for lbl, val, bg, fg in kpis:
                frm = UIFrame(self.kpi_frame, bg=bg, padx=12, pady=6, relief="solid", bd=1)
                frm.pack(side="right", padx=3)
                UILabel(frm, text=lbl, font=FT_SMALL, bg=bg, fg=CLR["text2"]).pack()
                UILabel(frm, text=val, font=("Arial",12,"bold"), bg=bg, fg=fg).pack()
            
        self.lbl_count.config(text=f"{len(rows)} دفعة مسجلة")

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel: 
            messagebox.showwarning("تنبيه", "يرجى تحديد دفعة من الجدول أولاً")
            return None
        return int(sel[0])

    def _new_batch(self):
        BatchForm(self, on_save=self._load_batches)
        
    def _edit_batch(self):
        bid = self._selected_id()
        if bid: 
            BatchForm(self, batch_id=bid, on_save=self._load_batches)
            
    def _del_batch(self):
        bid = self._selected_id()
        if not bid:
            return
        if messagebox.askyesno("تأكيد", f"حذف الدفعة رقم {bid} نهائياً؟"):
            db.execute("DELETE FROM batches WHERE id=?", (bid,))
            self._load_batches()
            
    def _open_daily(self):
        bid = self._selected_id()
        if bid: 
            batch = db.fetch_one("SELECT * FROM v_batches WHERE id=?", (bid,))
            if batch:
                DailyRecordsWindow(self, bid, dict(batch))
            
    def _open_wh_report(self): 
        WarehousesReportWindow(self)
        
    def _open_dashboard(self): 
        DashboardWindow(self)
        
    def _backup(self):
        make_backup()
        messagebox.showinfo("نسخ احتياطي", "تم حفظ النسخة الاحتياطية بنجاح")

    
    def _import_excel(self):
        """استيراد دفعة عنبر من ملف Excel باستخدام المحرك الموحد"""
        if not HAS_OPENPYXL:
            return messagebox.showerror("خطأ", "مكتبة openpyxl غير مثبتة.", parent=self)

        path = filedialog.askopenfilename(
            title="اختر ملف Excel للدفعة",
            filetypes=[("Excel Files", "*.xlsx *.xlsm *.xls"), ("All Files", "*.*")],
            parent=self
        )
        if not path: return

        try:
            from core.batch_importer import BatchImporter
            imp = BatchImporter(db)
            success, msg = imp.import_file(path)
            if success:
                self._load_batches()
                messagebox.showinfo("تم الاستيراد", msg, parent=self)
            else:
                messagebox.showerror("فشل الاستيراد", msg, parent=self)
        except Exception as e:
            messagebox.showerror("خطأ", str(e), parent=self)

    def _import_folder(self):
        """استيراد كافة ملفات الإكسل من مجلد واحد باستخدام المحرك الموحد"""
        if not HAS_OPENPYXL:
            return messagebox.showerror("خطأ", "مكتبة openpyxl غير مثبتة.", parent=self)

        target_dir = filedialog.askdirectory(title="اختر المجلد الذي يحتوي على ملفات الإكسل", parent=self)
        if not target_dir: return

        from core.batch_importer import BatchImporter
        imp = BatchImporter(db)
        results = imp.import_folder(target_dir)
        
        self._load_batches()
        success_count = sum(1 for r in results if r['success'])
        report = [f"📊 ملخص عملية الاستيراد الجماعي:", f"✅ تم استيراد {success_count} ملف بنجاح."]
        if success_count < len(results):
            report.append(f"\n❌ فشل استيراد {len(results) - success_count} ملفات:")
            for r in results:
                if not r['success']: report.append(f"- {r['file']}: {r['message']}")
        
        messagebox.showinfo("تقرير الاستيراد", "\n".join(report), parent=self)

    def _save_import_to_db(self, imp, chicks):
        d = imp.result
        wh_name = imp.wh_name
        batch_num_str = imp.filename
        date_in  = imp.daily_rows[0]['rec_date'] if imp.daily_rows else date.today().isoformat()
        date_out = imp.daily_rows[-1]['rec_date'] if imp.daily_rows else date.today().isoformat()
        days_n   = max((datetime.strptime(date_out, '%Y-%m-%d') - datetime.strptime(date_in, '%Y-%m-%d')).days, 1)
        total_dead = sum(r['dead_count'] for r in imp.daily_rows)
        mort_rate  = round(total_dead / chicks * 100, 2) if chicks > 0 else 0
        f_cust_qty = sum(s['qty'] for s in imp.farm_sales)
        f_cust_val = sum(s['total_val'] for s in imp.farm_sales)
        total_cost = d.get('total_cost', 0)
        total_rev  = d.get('total_rev', 0) or f_cust_val
        net_result = d.get('net_result', total_rev - total_cost)
        total_sold = int(f_cust_qty) or int(d.get('total_sold', 0))

        with db.get_conn() as conn:
            wh = conn.execute("SELECT id FROM warehouses WHERE name=?", (wh_name,)).fetchone()
            if not wh:
                conn.execute("INSERT INTO warehouses (name) VALUES (?)", (wh_name,))
                wh = conn.execute("SELECT id FROM warehouses WHERE name=?", (wh_name,)).fetchone()
            wh_id = wh['id']
            cur = conn.execute("""
                INSERT INTO batches (
                    warehouse_id, batch_num, date_in, date_out, days, chicks,
                    chick_val, feed_qty, feed_val, feed_trans, sawdust_qty, sawdust_val,
                    gas_qty, gas_val, water_val, light_val, drugs_val,
                    wh_expenses, house_exp, breeders_pay, qat_pay, rent_val,
                    sup_wh_pay, sup_co_pay, sup_sale_pay, admin_val, vaccine_pay,
                    delivery_val, mixing_val, wash_val, other_costs,
                    offal_val, total_cost, cust_qty, cust_val, total_rev, total_sold,
                    total_dead, mort_rate, net_result, created_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'))
            """, (
                wh_id, batch_num_str, date_in, date_out, days_n, chicks,
                d.get('chick_val', 0), d.get('feed_qty', 0), d.get('feed_val', 0), d.get('feed_trans', 0),
                d.get('sawdust_qty', 0), d.get('sawdust_val', 0), d.get('gas_qty', 0), d.get('gas_val', 0),
                d.get('water_val', 0), d.get('light_val', 0), d.get('drugs_val', 0),
                d.get('wh_expenses', 0), d.get('house_exp', 0), d.get('breeders_pay', 0), d.get('qat_pay', 0), d.get('rent_val', 0),
                d.get('sup_wh_pay', 0), d.get('sup_co_pay', 0), d.get('sup_sale_pay', 0), d.get('admin_val', 0), d.get('vaccine_pay', 0),
                d.get('delivery_val', 0), d.get('mixing_val', 0), d.get('wash_val', 0), d.get('other_costs', 0),
                d.get('offal_val', 0), total_cost, int(f_cust_qty), f_cust_val, total_rev, total_sold,
                total_dead, mort_rate, net_result
            ))
            batch_id = cur.lastrowid
            for r in imp.daily_rows:
                conn.execute("INSERT OR IGNORE INTO daily_records (batch_id, rec_date, day_num, dead_count, feed_kg) VALUES (?,?,?,?,?)",
                    (batch_id, r['rec_date'], r['day_num'], r['dead_count'], r['feed_kg']))
            for s in imp.farm_sales:
                conn.execute("INSERT INTO farm_sales (batch_id, customer, qty, price, total_val) VALUES (?,?,?,?,?)",
                    (batch_id, s['customer'], s['qty'], s['price'], s['total_val']))
            for ms in imp.market_sales:
                conn.execute("INSERT INTO market_sales (batch_id, office, qty_sent, deaths, qty_sold, net_val, inv_num) VALUES (?,?,?,?,?,?,?)",
                    (batch_id, ms["office"], ms["qty_sent"], ms["deaths"], ms["qty_sold"], ms["net_val"], ms["inv_num"]))
            return batch_id
    def _export_pdf(self):
        if not HAS_FPDF:
            messagebox.showerror("خطأ", "مكتبة fpdf غير مثبتة.\nنفّذ: pip install fpdf2", parent=self)
            return
            
        batch_id = self._selected_id()
        if not batch_id: 
            return

        batch_row = db.fetch_one("SELECT * FROM v_batches WHERE id=?", (batch_id,))
        if not batch_row: 
            return
            
        b = dict(batch_row)

        pdf = FPDF()
        pdf.add_page()

        font_path = os.path.join(BASE_DIR, "assets", "Amiri-Regular.ttf")
        if not os.path.exists(font_path):
            messagebox.showerror("خطأ", "ملف الخط Amiri-Regular.ttf غير موجود!", parent=self)
            return
            
        pdf.add_font('Arabic', '', font_path, uni=True)

        logo_path = os.path.join(BASE_DIR, "assets", "logo.png")
        if os.path.exists(logo_path):
            pdf.image(logo_path, x=10, y=8, w=30)

        pdf.set_font('Arabic', '', 18)
        pdf.cell(0, 10, prepare_text("شركة آفاق الريف للدواجن"), ln=True, align='C')
        pdf.set_font('Arabic', '', 14)
        
        b_num = b.get('batch_num') or str(b.get('id', ''))
        title_text = f"تقرير التصفية المالية — دفعة رقم ({b_num}) — {b.get('warehouse_name', '')}"
        pdf.cell(0, 8, prepare_text(title_text), ln=True, align='C')
        
        pdf.set_font('Arabic', '', 11)
        info1 = f"تاريخ الدخول: {b.get('date_in', '')}  |  تاريخ الخروج: {b.get('date_out', '')}  |  عدد الأيام: {b.get('days', 0)}  |  الكتاكيت: {int(b.get('chicks') or 0):,}"
        pdf.cell(0, 7, prepare_text(info1), ln=True, align='C')
        info2 = f"النافق: {int(b.get('total_dead') or 0):,} ({(b.get('mort_rate') or 0):.2f}%)  |  المباع: {int(b.get('total_sold') or 0):,}  |  متوسط السعر: {fmt_num(b.get('avg_price'))} ريال"
        pdf.cell(0, 7, prepare_text(info2), ln=True, align='C')
        pdf.ln(4)

        # ── 1. جدول مطابقة حركة الطيور ──
        pdf.set_font('Arabic', '', 12)
        pdf.set_fill_color(31, 78, 121)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 8, prepare_text("مطابقة حركة الطيور (بالعدد)"), 1, 1, 'C', True)

        pdf.set_font('Arabic', '', 10)
        pdf.set_text_color(0, 0, 0)
        headers_birds = ["الفارق (نقص/زيادة)", "إجمالي المنصرف", "ضيافة/استهلاك", "وفيات السوق", "وفيات العنبر", "مباع السوق", "مباع العنبر", "الكتاكيت"]
        w_b = [23, 24, 23, 24, 24, 24, 24, 24]

        pdf.set_fill_color(240, 246, 255)
        for w, h in zip(w_b, headers_birds): 
            pdf.cell(w, 8, prepare_text(h), 1, 0, 'C', True)
        pdf.ln()

        f_sales = db.fetch_one("SELECT SUM(qty) as sq FROM farm_sales WHERE batch_id=?", (batch_id,))
        f_sold = f_sales['sq'] if f_sales and f_sales['sq'] else 0

        m_sales = db.fetch_one("SELECT SUM(qty_sold) as qs, SUM(deaths) as md FROM market_sales WHERE batch_id=?", (batch_id,))
        m_sold = m_sales['qs'] if m_sales and m_sales['qs'] else 0
        m_dead = m_sales['md'] if m_sales and m_sales['md'] else 0

        chicks = b.get('chicks') or 0
        f_dead = b.get('total_dead') or 0
        consumed_birds = b.get('consumed_birds') or 0

        total_out = f_sold + m_sold + f_dead + m_dead + consumed_birds
        variance = chicks - total_out

        vals_birds = [fmt_num(variance), fmt_num(total_out), fmt_num(consumed_birds), fmt_num(m_dead), fmt_num(f_dead), fmt_num(m_sold), fmt_num(f_sold), fmt_num(chicks)]
        for w, v in zip(w_b, vals_birds): 
            pdf.cell(w, 8, prepare_text(v), 1, 0, 'C')
        pdf.ln(5)

        # ── 2. جدول حركة العلف بالكيس ──
        pdf.set_font('Arabic', '', 12)
        pdf.set_fill_color(31, 78, 121)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 8, prepare_text("حركة العلف (بالكيس) - الطن = 20 كيس / الكيس = 50 كجم"), 1, 1, 'C', True)

        pdf.set_font('Arabic', '', 10)
        pdf.set_text_color(0, 0, 0)
        headers_feed = ["الفارق", "الرصيد المتبقي", "المباع / المنقول", "المستهلك (يومي)", "الوارد للعنبر"]
        w_f = [38, 38, 38, 38, 38]

        pdf.set_fill_color(240, 246, 255)
        for w, h in zip(w_f, headers_feed): 
            pdf.cell(w, 8, prepare_text(h), 1, 0, 'C', True)
        pdf.ln()

        feed_in_tons = b.get('feed_qty') or 0
        feed_in_bags = feed_in_tons * 20

        daily = db.fetch_one("SELECT SUM(feed_kg) as fk FROM daily_records WHERE batch_id=?", (batch_id,))
        consumed_kg = daily['fk'] if daily and daily['fk'] else 0
        consumed_bags = consumed_kg / 50

        feed_val = b.get('feed_val') or 0
        feed_sales_val = (b.get('feed_sale') or 0) + (b.get('feed_trans_r') or 0)
        sold_bags = 0
        if feed_in_bags > 0 and feed_val > 0:
            sold_bags = feed_sales_val / (feed_val / feed_in_bags)

        remaining_bags = feed_in_bags - consumed_bags - sold_bags

        vals_feed = ["0.0", fmt_num(remaining_bags, 1), fmt_num(sold_bags, 1), fmt_num(consumed_bags, 1), fmt_num(feed_in_bags, 1)]
        for w, v in zip(w_f, vals_feed): 
            pdf.cell(w, 8, prepare_text(v), 1, 0, 'C')
        pdf.ln(5)

        # ── 3. الملخص المالي ──
        pdf.set_font('Arabic', '', 12)
        pdf.set_fill_color(31, 78, 121)
        pdf.set_text_color(255,255,255)
        pdf.cell(0, 8, prepare_text("الملخص المالي التفصيلي (التكاليف والإيرادات)"), 1, 1, 'C', True)
        pdf.set_text_color(0,0,0)

        costs = []
        if b.get('chicks'):    
            costs.append(("الكتاكيت",    b.get('chicks'),      b.get('chick_val')))
        if b.get('feed_val'):  
            costs.append(("العلف",        b.get('feed_qty'),    b.get('feed_val')))
        if b.get('sawdust_val'):
            costs.append(("النشارة",     b.get('sawdust_qty'), b.get('sawdust_val')))
        if b.get('gas_val'):   
            costs.append(("الغاز",        b.get('gas_qty'),     b.get('gas_val')))
        if b.get('water_val'): 
            costs.append(("الماء",        "",                   b.get('water_val')))
        if b.get('drugs_val'): 
            costs.append(("العلاجات",     "",                   b.get('drugs_val')))
        if b.get('wh_expenses'):
            costs.append(("مصاريف عنبر","",                   b.get('wh_expenses')))
        if b.get('house_exp'): 
            costs.append(("مصاريف بيت",  "",                   b.get('house_exp')))
        if b.get('breeders_pay'):
            costs.append(("أجور مربيين","",                  b.get('breeders_pay')))
        if b.get('qat_pay'):   
            costs.append(("قات مربيين",   "",                   b.get('qat_pay')))
        if b.get('rent_val'):  
            costs.append(("إيجار عنبر",   "",                   b.get('rent_val')))
        if b.get('light_val'): 
            costs.append(("إضاءة",        "",                   b.get('light_val')))
            
        sup_tot = (b.get('sup_wh_pay') or 0) + (b.get('sup_co_pay') or 0) + (b.get('sup_sale_pay') or 0)
        if sup_tot: 
            costs.append(("إشراف وتسويق", "", sup_tot))
            
        if b.get('admin_val'): 
            costs.append(("إدارة وحسابات","",                  b.get('admin_val')))
        if b.get('vaccine_pay'):
            costs.append(("لقاحات",       "",                  b.get('vaccine_pay')))
            
        oth_tot = (b.get('delivery_val') or 0) + (b.get('mixing_val') or 0) + (b.get('wash_val') or 0) + (b.get('other_costs') or 0)
        if oth_tot: 
            costs.append(("مصاريف أخرى متنوعة", "", oth_tot))

        revs = []
        if f_sold: 
            revs.append(("مبيعات العنبر", f_sold, (b.get('cust_val') or 0)))
        if m_sold: 
            revs.append(("مبيعات السوق",  m_sold, (b.get('mkt_val') or 0)))
        if b.get('offal_val'): 
            revs.append(("بيع ذبيل",       "",                b.get('offal_val')))
        if b.get('feed_sale'): 
            revs.append(("بيع علف",        "",                b.get('feed_sale')))
            
        oth_rev = (b.get('feed_trans_r') or 0) + (b.get('drug_return') or 0) + (b.get('gas_return') or 0)
        if oth_rev: 
            revs.append(("إيرادات أخرى", "", oth_rev))

        max_len = max(len(costs), len(revs), 1)
        costs += [("", "", "")] * (max_len - len(costs))
        revs  += [("", "", "")] * (max_len - len(revs))

        pdf.set_font('Arabic', '', 10)
        pdf.set_fill_color(31, 78, 121)
        pdf.set_text_color(255,255,255)
        pdf.cell(27, 8, prepare_text("القيمة"), 1, 0, 'C', True)
        pdf.cell(22, 8, prepare_text("الكمية"), 1, 0, 'C', True)
        pdf.cell(50, 8, prepare_text("الإيرادات"), 1, 0, 'C', True)
        pdf.cell(27, 8, prepare_text("القيمة"), 1, 0, 'C', True)
        pdf.cell(22, 8, prepare_text("الكمية"), 1, 0, 'C', True)
        pdf.cell(50, 8, prepare_text("التكاليف"), 1, 1, 'C', True)
        pdf.set_text_color(0,0,0)

        for i in range(max_len):
            r_name, r_qty, r_val = revs[i]
            c_name, c_qty, c_val = costs[i]
            fill = (i % 2 == 0)
            if fill: 
                pdf.set_fill_color(240,246,255)
            else:    
                pdf.set_fill_color(255,255,255)
                
            pdf.cell(27, 7, prepare_text(fmt_num(r_val) if r_val else ""), 1, 0, 'C', fill)
            pdf.cell(22, 7, prepare_text(fmt_num(r_qty) if r_qty else ""), 1, 0, 'C', fill)
            pdf.cell(50, 7, prepare_text(r_name), 1, 0, 'R', fill)
            pdf.cell(27, 7, prepare_text(fmt_num(c_val) if c_val else ""), 1, 0, 'C', fill)
            pdf.cell(22, 7, prepare_text(fmt_num(c_qty) if c_qty else ""), 1, 0, 'C', fill)
            pdf.cell(50, 7, prepare_text(c_name), 1, 1, 'R', fill)

        pdf.ln(2)
        def draw_row(label, value, bg=(240,240,240), fg=(0,0,0)):
            pdf.set_fill_color(*bg)
            pdf.set_text_color(*fg)
            pdf.cell(27, 8, prepare_text(fmt_num(value)), 1, 0, 'C', True)
            pdf.cell(171, 8, prepare_text(label), 1, 1, 'R', True)
            pdf.set_text_color(0,0,0)

        draw_row("إجمالي التكاليف",  b.get("total_cost") or 0, (252,228,214),(192,0,0))
        draw_row("إجمالي الإيرادات", b.get("total_rev") or 0,  (226,239,218),(39,104,10))
        
        net = b.get("net_result") or 0
        net_bg = (226,239,218) if net >= 0 else (252,228,214)
        net_fg = (39,104,10) if net >= 0 else (192,0,0)
        
        w_status = "ربح" if net >= 0 else "خسارة"
        draw_row(f"نتيجة الدفعة ({w_status})", abs(net), net_bg, net_fg)
        
        pct = b.get('share_pct') or 65
        share_v = b.get("share_val") or 0
        partner_pct = 100 - int(pct)
        partner_v = net - share_v
        
        draw_row(f"نصيب الشركة ({int(pct)}%)", share_v, (255,242,204),(191,144,0))
        
        p_name = b.get("partner_name", "")
        p_str = f" ({p_name})" if p_name else ""
        draw_row(f"نصيب الشريك{p_str} ({partner_pct}%)", partner_v, (255,242,204),(191,144,0))

        raw_notes = b.get("notes", "")
        if raw_notes:
            pdf.ln(5)
            pdf.set_fill_color(31, 78, 121)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font('Arabic', '', 12)
            pdf.cell(0, 8, prepare_text("ملاحظات الدفعة الإضافية"), border=1, ln=True, align='C', fill=True)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font('Arabic', '', 10)
            for line in textwrap.wrap(raw_notes, width=85):
                pdf.cell(0, 7, prepare_text(line), border=1, ln=True, align='R')

        # ── 4. قسم التواقيع ──
        if pdf.get_y() > 250:
            pdf.add_page()
            
        pdf.set_y(-35)
        
        pdf.set_font('Arabic', '', 12)
        pdf.cell(47.5, 8, prepare_text("المحاسب"), 0, 0, 'C')
        pdf.cell(47.5, 8, prepare_text("المراجع"), 0, 0, 'C')
        pdf.cell(47.5, 8, prepare_text("المدير المالي"), 0, 0, 'C')
        pdf.cell(47.5, 8, prepare_text("المدير العام"), 0, 1, 'C')

        pdf.ln(8)
        pdf.cell(47.5, 8, ".......................", 0, 0, 'C')
        pdf.cell(47.5, 8, ".......................", 0, 0, 'C')
        pdf.cell(47.5, 8, ".......................", 0, 0, 'C')
        pdf.cell(47.5, 8, ".......................", 0, 1, 'C')

        save_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF","*.pdf")], initialfile=f"تصفية_{b.get('warehouse_name', '')}_دفعة_{b_num}.pdf", title="حفظ تقرير PDF", parent=self)
        if save_path:
            pdf.output(save_path)
            messagebox.showinfo("تم", "تم تصدير تقرير التصفية بنجاح!", parent=self)
            try: 
                os.startfile(save_path)
            except: 
                pass

if __name__ == "__main__":
    try:
        app = MainWindow()
        app.mainloop()
    except Exception as e:
        # صمام أمان للأخطاء غير المتوقعة عند التشغيل
        import traceback
        with open("error_log.txt", "a") as f:
            f.write(f"\n[{datetime.now()}] CRITICAL APP ERROR:\n{traceback.format_exc()}\n")
        print(f"حدث خطأ فادح: {e}")