import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import shutil
from datetime import datetime
from ui.constants import CLR, FT_TITLE, FT_HEADER, FT_BODY, FT_SMALL, FT_TINY, HAS_TTKB, HAS_MATPLOTLIB, BASE_DIR
from ui.widgets import WindowBase, UIFrame, UILabel, UIButton, ToplevelBase
from ui.forms import BatchForm, DailyRecordsWindow
from ui.dashboard import DashboardWindow
from ui.reports_ui import ReportsCenterWindow, WarehousesReportWindow
from core.reporting import ReportsManager
from core.importer import ExcelImporter
from core.exporter import ReportExporter
from utils.text_utils import fmt_num

if HAS_TTKB:
    import ttkbootstrap as ttkb

class MainWindow(WindowBase):
    def __init__(self, db):
        if HAS_TTKB:
            try: super().__init__(themename="lumen")
            except: super().__init__()
        else: super().__init__()
            
        self.title("نظام إدارة عنابر الدجاج اللاحم — النسخة المطورة 3.8")
        self.geometry("1240x750")
        self.db = db
        self.reports = ReportsManager(db, 
                                     font_path=os.path.join(BASE_DIR, "assets", "Amiri-Regular.ttf"),
                                     logo_path=os.path.join(BASE_DIR, "assets", "logo.png"))
        
        self._build()
        self._load_batches()
        self._update_status()
        self.bind("<Control-n>", lambda e: self._new_batch())
        self.bind("<Control-p>", lambda e: self._open_reports())

    def _build(self):
        # Header
        hdr = UIFrame(self, bg=CLR["header"], pady=12)
        hdr.pack(fill="x")
        
        UILabel(hdr, text="🐔 نظام إدارة عنابر الدجاج اللاحم", font=("Segoe UI", 18, "bold"), bg=CLR["header"], fg="white").pack(side="right", padx=20)
        
        self.lbl_count = UILabel(hdr, text="", font=FT_BODY, bg=CLR["header"], fg="#aad4f5")
        self.lbl_count.pack(side="right", padx=30)

        # Theme Switcher (Right aligned for RTL flow)
        if HAS_TTKB:
            themes = self.style.theme_names()
            self.theme_cbo = ttkb.Combobox(hdr, values=themes, width=12, state="readonly", bootstyle="info")
            self.theme_cbo.pack(side="left", padx=10)
            self.theme_cbo.set("lumen")
            self.theme_cbo.bind("<<ComboboxSelected>>", self._change_theme)
            UILabel(hdr, text="المظهر:", font=FT_SMALL, bg=CLR["header"], fg="white").pack(side="left")

        # Toolbar
        tb = UIFrame(self, bg=CLR["nav"], pady=8)
        tb.pack(fill="x")
        
        btns = [
            ("+ دفعة جديدة", self._new_batch, "success"),
            ("✏️ تعديل", self._edit_batch, "warning"),
            ("🗑 حذف", self._del_batch, "danger"),
            ("📅 السجلات اليومية", self._open_daily, "info"),
            ("📊 تقرير العنابر", self._open_wh_report, "primary"),
            ("📈 لوحة القياس", self._open_dashboard, "success"),
            ("🖨️ PDF", self._export_pdf, "info"),
            ("📊 مركز التقارير", self._open_reports, "primary"),
            ("📥 استيراد Excel", self._import_excel, "warning"),
            ("💾 نسخة احتياطية", self._backup, "secondary")
        ]
        
        for txt, cmd, bstyle in btns:
            if HAS_TTKB:
                UIButton(tb, text=txt, command=cmd, bootstyle=bstyle).pack(side="right", padx=4)
            else:
                UIButton(tb, text=txt, command=cmd, bg=CLR["white"], padx=10).pack(side="right", padx=4)

        # Filter Bar
        fbar = UIFrame(self, pady=8, padx=20)
        fbar.pack(fill="x")
        
        UILabel(fbar, text="تصفية حسب العنبر:").pack(side="right", padx=5)
        self.filter_wh = ttk.Combobox(fbar, width=25, font=FT_BODY)
        self.filter_wh.pack(side="right", padx=5)
        self.filter_wh.bind("<<ComboboxSelected>>", lambda e: self._load_batches())
        UIButton(fbar, text="🔄 عرض الكل", command=self._reset_filter).pack(side="right", padx=10)

        # KPI Cards Frame
        self.kpi_frame = UIFrame(self, pady=10)
        self.kpi_frame.pack(fill="x", padx=15)

        # Main Table
        frm = UIFrame(self, padx=15, pady=(0, 10))
        frm.pack(fill="both", expand=True)
        
        cols = ("ID","رقم الدفعة","العنبر","تاريخ الدخول","تاريخ الخروج","الأيام","الكتاكيت","التكاليف","الإيرادات","صافي النتيجة","النافق%","نصيب الشركة")
        self.tree = ttk.Treeview(frm, columns=cols, show="headings", selectmode="browse")
        for c in cols:
            self.tree.heading(c, text=c)
            anc = "center"
            if c == "العنبر": anc = "e"
            self.tree.column(c, width=100, anchor=anc)
        
        sb = ttk.Scrollbar(frm, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="left", fill="y")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda e: self._edit_batch())

        # Status Bar
        self.stat = UIFrame(self, bg="#eee", pady=5)
        self.stat.pack(side="bottom", fill="x")
        
        self.lbl_stat = UILabel(self.stat, text="جاهز", font=FT_SMALL, bg="#eee")
        self.lbl_stat.pack(side="right", padx=15)
        
        self.lbl_backup = UILabel(self.stat, text="آخر نسخة احتياطية: جاري التحقق...", font=FT_SMALL, bg="#eee", fg="#666")
        self.lbl_backup.pack(side="left", padx=15)

    def _change_theme(self, event):
        if HAS_TTKB:
            new_theme = self.theme_cbo.get()
            try:
                self.style.theme_use(new_theme)
                self._load_batches()
            except: pass

    def _update_status(self):
        last_bk = "غير متاح"
        if os.path.exists("backups"):
            bks = [f for f in os.listdir("backups") if f.endswith(".db")]
            if bks: last_bk = max(bks)
        self.lbl_backup.config(text=f"آخر نسخة احتياطية: {last_bk}")

    def _reset_filter(self):
        self.filter_wh.set("")
        self._load_batches()

    def _load_batches(self):
        wh = self.filter_wh.get().strip()
        query = "SELECT * FROM v_batches"
        params = []
        if wh:
            query += " WHERE warehouse_name=?"
            params.append(wh)
        query += " ORDER BY id DESC"
        
        rows = self.db.fetch_all(query, params)
        self.tree.delete(*self.tree.get_children())
        
        totals = {"cost": 0, "rev": 0, "net": 0, "chicks": 0, "share": 0}
        
        for r in rows:
            is_profit = (r["net_result"] or 0) >= 0
            tag = "profit" if is_profit else "loss"
            sign = "+" if is_profit else ""
            
            self.tree.insert("", "end", iid=r["id"], tags=(tag,), values=(
                r["id"], r["batch_num"], r["warehouse_name"], r["date_in"], r["date_out"],
                r["days"], fmt_num(r["chicks"]), fmt_num(r["total_cost"]), fmt_num(r["total_rev"]),
                f"{sign}{fmt_num(r['net_result'])}", f"{r['mort_rate']:.2f}%", fmt_num(r["share_val"])
            ))
            
            totals["cost"] += r["total_cost"] or 0
            totals["rev"] += r["total_rev"] or 0
            totals["net"] += r["net_result"] or 0
            totals["chicks"] += r["chicks"] or 0
            totals["share"] += r["share_val"] or 0

        self.tree.tag_configure("profit", foreground="#155724")
        self.tree.tag_configure("loss", foreground="#721c24")
        
        # Update KPI Cards
        for w in self.kpi_frame.winfo_children(): w.destroy()
        
        sign_net = "+" if totals["net"] >= 0 else ""
        net_clr = "success" if totals["net"] >= 0 else "danger"
        
        kpis = [
            ("الدفعات", str(len(rows)), "primary"), 
            ("إجمالي الكتاكيت", fmt_num(totals["chicks"]), "info"), 
            ("إجمالي التكاليف", fmt_num(totals["cost"]), "danger"), 
            ("إجمالي الإيرادات", fmt_num(totals["rev"]), "success"), 
            ("صافي النتيجة", f"{sign_net}{fmt_num(totals['net'])}", net_clr), 
            ("نصيب الشركة", fmt_num(totals["share"]), "warning")
        ]
        
        for lbl, val, bstyle in kpis:
            cfrm = UIFrame(self.kpi_frame, bg="white", pady=10, padx=15)
            cfrm.pack(side="right", padx=6)
            if HAS_TTKB:
                UILabel(cfrm, text=lbl, font=FT_TINY, bg="white", bootstyle="secondary").pack()
                UILabel(cfrm, text=val, font=("Segoe UI", 14, "bold"), bg="white", bootstyle=bstyle).pack()
            else:
                UILabel(cfrm, text=lbl, font=FT_TINY, bg="white", fg="#666").pack()
                UILabel(cfrm, text=val, font=("Segoe UI", 14, "bold"), bg="white").pack()
        
        whs = [""] + [r["name"] for r in self.db.fetch_all("SELECT name FROM warehouses ORDER BY name")]
        self.filter_wh["values"] = whs
        self.lbl_count.config(text=f"عدد الدفعات: {len(rows)}")

    def _new_batch(self):
        BatchForm(self, self.db, on_save=self._load_batches)

    def _edit_batch(self):
        sel = self.tree.selection()
        if not sel: return
        BatchForm(self, self.db, batch_id=sel[0], on_save=self._load_batches)

    def _del_batch(self):
        sel = self.tree.selection()
        if not sel: return
        if messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف هذه الدفعة نهائياً؟"):
            self.db.execute("DELETE FROM batches WHERE id=?", (sel[0],))
            self._load_batches()

    def _open_daily(self):
        sel = self.tree.selection()
        if not sel: return
        batch = self.db.fetch_one("SELECT * FROM v_batches WHERE id=?", (sel[0],))
        DailyRecordsWindow(self, self.db, sel[0], dict(batch))

    def _open_dashboard(self):
        DashboardWindow(self, self.db)

    def _open_reports(self):
        ReportsCenterWindow(self, self.db, self.reports)

    def _open_wh_report(self):
        WarehousesReportWindow(self, self.db)

    def _export_pdf(self):
        sel = self.tree.selection()
        if not sel: return
        path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=f"تقرير_دفعة_{sel[0]}.pdf")
        if path:
            if self.reports.export_full_batch_pdf(sel[0], path):
                messagebox.showinfo("تم", "تم تصدير التقرير بنجاح")

    def _import_excel(self):
        path = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
        if path:
            importer = ExcelImporter(self.db)
            if importer.import_batch(path):
                messagebox.showinfo("تم", "تم الاستيراد بنجاح")
                self._load_batches()

    def _backup(self):
        if not os.path.exists("backups"): os.makedirs("backups")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = f"backups/poultry_backup_{ts}.db"
        shutil.copy2("poultry_data.db", dst)
        messagebox.showinfo("تم", f"تم إنشاء نسخة احتياطية في:\n{dst}")
