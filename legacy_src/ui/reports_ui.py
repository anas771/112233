import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import os
from ui.constants import CLR, FT_TITLE, FT_HEADER, FT_BODY, FT_SMALL, FT_TINY, HAS_OPENPYXL, HAS_TTKB
from ui.widgets import ToplevelBase, UIFrame, UILabel, UIButton
from utils.text_utils import fmt_num, prepare_text

if HAS_OPENPYXL:
    import openpyxl
    from openpyxl.styles import PatternFill, Alignment, Border, Side

class ReportsCenterWindow(ToplevelBase):
    def __init__(self, master, db, reports):
        super().__init__(master)
        self.db = db
        self.reports = reports
        self.title("مركز التقارير المحاسبية والطباعة الشاملة")
        self.geometry("1100x750")
        self.grab_set()
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
        self.tab_excel = UIFrame(nb, padx=15, pady=15)
        self.tab_debts = UIFrame(nb, padx=15, pady=15)

        nb.add(self.tab_cust, text="👥 كشوفات العملاء")
        nb.add(self.tab_mkt,  text="🏢 كشوفات المكاتب")
        nb.add(self.tab_batch, text="📋 تقارير الدفعات")
        nb.add(self.tab_excel, text="🚀 تكامل Excel الذكي")
        nb.add(self.tab_debts, text="💰 تقرير المديونيات العامة")

        self._build_cust_tab()
        self._build_mkt_tab()
        self._build_batch_tab()
        self._build_excel_tab()
        self._build_debts_tab()

    def _build_cust_tab(self):
        F = self.tab_cust
        ctrl = UIFrame(F, pady=10)
        ctrl.pack(fill="x")
        
        UILabel(ctrl, text="اختر العميل:").pack(side="right", padx=5)
        self.cbo_cust = ttk.Combobox(ctrl, width=25, font=FT_BODY)
        customers = [r['customer'] for r in self.db.fetch_all("SELECT DISTINCT customer FROM farm_sales ORDER BY customer")]
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
        offices = [r['office'] for r in self.db.fetch_all("SELECT DISTINCT office FROM market_sales ORDER BY office")]
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
        
        rows = self.db.fetch_all("SELECT id, batch_num, warehouse_name, date_out, net_result FROM v_batches ORDER BY date_out DESC")
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
            try: os.startfile(path)
            except: pass

    def _export_daily_logs(self):
        sel = self.tv_batches.selection()
        if not sel: return
        b_id = sel[0]
        path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=f"سجلات_يومية_دفعة_{b_id}.pdf")
        if path:
            self.reports.export_daily_records_pdf(b_id, path)
            messagebox.showinfo("تم", "تم تصدير السجلات اليومية")
            try: os.startfile(path)
            except: pass

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
        
        from core.importer import BatchImporter
        importer = BatchImporter(self.db)
        success, msg = importer.import_file(file_path)
        
        if success:
            messagebox.showinfo("نجاح", msg)
            if hasattr(self.master, '_load_batches'): self.master._load_batches()
        else:
            messagebox.showerror("خطأ", msg)

    def _import_xlsm_folder(self):
        folder = filedialog.askdirectory(title="اختر المجلد الذي يحتوي على ملفات .xlsm")
        if not folder: return
        
        from core.importer import BatchImporter
        importer = BatchImporter(self.db) 
        results = importer.import_folder(folder)
        
        summary = ""
        success_count = sum(1 for r in results if r['success'])
        for r in results:
            status = "✅" if r['success'] else "❌"
            summary += f"{status} {r['file']}: {r['message']}\n"
        
        msg = f"تمت معالجة {len(results)} ملفات.\nنجاح: {success_count}\nفشل: {len(results)-success_count}\n\n{summary}"
        if len(msg) > 1000: msg = msg[:1000] + "\n..."
        
        messagebox.showinfo("نتائج الاستيراد", msg)
        if hasattr(self.master, '_load_batches'): self.master._load_batches()

    def _export_cumulative_report(self):
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile="التقرير_التراكمي_الشامل.xlsx")
        if not path: return
        
        from core.exporter import ReportExporter
        exporter = ReportExporter(self.db)
        success, msg = exporter.export_all(path)
        if success:
            if messagebox.askyesno("نجاح", f"{msg}\nهل تريد فتح الملف الآن؟"):
                try: os.startfile(path)
                except: pass
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

class WarehousesReportWindow(ToplevelBase):
    def __init__(self, master, db):
        super().__init__(master)
        self.db = db
        self.title("تقرير العنابر الشامل")
        self.geometry("1200x700")
        self._build()
        self._load()

    def _build(self):
        hdr = UIFrame(self, bg=CLR["header"], pady=10)
        hdr.pack(fill="x")
        UILabel(hdr, text="📊 تقرير العنابر الشامل", font=FT_TITLE, bg=CLR["header"], fg="white").pack(side="right", padx=16)

        btn_frm = UIFrame(self, bg=CLR["nav"], pady=6)
        btn_frm.pack(fill="x")
        UIButton(btn_frm, text="📥 تصدير Excel (تحليلي شامل)", command=self._export_excel).pack(side="right", padx=6)
        
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
        batches = self.db.fetch_all("SELECT * FROM v_batches ORDER BY warehouse_name, date_in")
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
            d["net"] += b["net_result_dynamic"] if 'net_result_dynamic' in b else (b["net_result"] or 0)
            d["mort_sum"] += b["mort_rate"] or 0
            d["sold_sum"] += b["total_sold"] or 0
            d["cust_mkt_val_sum"] += (b["cust_val"] or 0) + (b["mkt_val"] or 0)

        self.tree_wh.delete(*self.tree_wh.get_children())
        for wh, d in wh_data.items():
            tag = "profit" if d["net"] >= 0 else "loss"
            avg_m = (d["mort_sum"]/d["count"]) if d["count"] > 0 else 0
            avg_p = (d["cust_mkt_val_sum"]/d["sold_sum"]) if d["sold_sum"] > 0 else 0
            self.tree_wh.insert("", "end", tags=(tag,), values=(wh, d["count"], fmt_num(d["chicks"]), fmt_num(d["cost"]), fmt_num(d["rev"]), f"{'+'if d['net']>=0 else ''}{fmt_num(d['net'])}", f"{avg_m:.1f}%", fmt_num(avg_p)))

        self.tree_all.delete(*self.tree_all.get_children())
        T = {"chicks":0,"cost":0,"rev":0,"net":0,"share":0}
        for b in batches:
            b_num = b["batch_num"] if b["batch_num"] else str(b["id"])
            net = b["net_result_dynamic"] if 'net_result_dynamic' in b else (b["net_result"] or 0)
            tag = "profit" if net >= 0 else "loss"
            self.tree_all.insert("", "end", iid=str(b["id"]), tags=(tag,), values=(b_num, b["warehouse_name"], b["date_in"], b["date_out"], b["days"] or "", fmt_num(b["chicks"]), fmt_num(b["total_cost"]), fmt_num(b["total_rev"]), f"{'+'if net>=0 else ''}{fmt_num(net)}", f"{b['mort_rate'] or 0:.1f}%", fmt_num(b["avg_price"]), fmt_num(b["share_val"])))
            T["chicks"] += b["chicks"] or 0
            T["cost"] += b["total_cost"] or 0
            T["rev"] += b["total_rev"] or 0
            T["net"] += net
            T["share"] += b["share_val"] or 0

        for w in self.sum_frame.winfo_children(): w.destroy()
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
            if "الإيرادات" in lbl or ("صافي" in lbl and "+" in val): val_color = CLR["profit"]
            elif "التكاليف" in lbl or ("صافي" in lbl and "-" in val): val_color = CLR["loss"]
            UILabel(f, text=val, font=(CLR.get("font", "Segoe UI"), 12, "bold"), bg=CLR["white"], fg=val_color).pack(pady=(2,0))

    def _export_excel(self):
        if not HAS_OPENPYXL: return
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel","*.xlsx")], initialfile=f"التقرير_التحليلي_للعنابر_{datetime.now().strftime('%Y%m%d')}.xlsx")
        if not path: return
        # Custom logic for cumulative export could go here, or use ReportExporter
        from core.exporter import ReportExporter
        exporter = ReportExporter(self.db)
        success, msg = exporter.export_all(path)
        if success: messagebox.showinfo("تم", msg)
        else: messagebox.showerror("خطأ", msg)
