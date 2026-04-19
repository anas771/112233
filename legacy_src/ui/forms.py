import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date, timedelta
import os
from ui.constants import CLR, FT_TITLE, FT_HEADER, FT_BODY, FT_SMALL, HAS_TTKB, HAS_OPENPYXL
from ui.widgets import ToplevelBase, UIFrame, UILabel, UIButton, UIEntry, UILabelFrame, lbl_entry
from utils.text_utils import fmt_num

if HAS_OPENPYXL:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment

class BatchForm(ToplevelBase):
    def __init__(self, master, db, batch_id=None, on_save=None):
        super().__init__(master)
        self.db = db
        self.batch_id = batch_id
        self.on_save  = on_save
        self.title("إدخال دفعة جديدة" if not batch_id else "تعديل دفعة")
        self.geometry("1100x750")
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

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=15)

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
        UIButton(btn_frm, text="💾 حفظ الدفعة", command=self._save).pack(side="right", padx=20)
        
        if self.batch_id: 
            UIButton(btn_frm, text="📅 السجلات اليومية", command=self._open_daily).pack(side="right", padx=4)
            
        UIButton(btn_frm, text="إلغاء وإغلاق", command=self.destroy).pack(side="left", padx=20)

    def _open_daily(self):
        if not self.batch_id: return
        batch = self.db.fetch_one("SELECT * FROM v_batches WHERE id=?", (self.batch_id,))
        if batch: 
            DailyRecordsWindow(self, self.db, self.batch_id, dict(batch))

    def _build_basic_tab(self, F):
        UILabel(F, text="اسم العنبر *", font=FT_SMALL).grid(row=0, column=0, sticky="e", padx=(8,2), pady=10)
        self.wh_var = tk.StringVar()
        self.wh_combo = ttk.Combobox(F, textvariable=self.wh_var, width=22, font=FT_BODY)
        self.wh_combo["values"] = [r["name"] for r in self.db.fetch_all("SELECT name FROM warehouses ORDER BY name")]
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
        row, col = 0, 0
        for i, (key, lbl) in enumerate(cost_fields):
            if i > 0 and i % 3 == 0: 
                row += 1
                col = 0
            v[key] = lbl_entry(F, lbl, row, col)
            v[key].trace_add("write", lambda *a: self._auto_calc())
            col += 2

        sep = ttk.Separator(F, orient="horizontal")
        sep.grid(row=row+1, column=0, columnspan=6, sticky="ew", pady=15)
        UILabel(F, text="📝 سجل بنود التكاليف التفصيلية", font=FT_HEADER, fg=CLR["nav"]).grid(row=row+2, column=0, columnspan=6, sticky="w", pady=(0,10))
        
        inp_c = UIFrame(F)
        inp_c.grid(row=row+3, column=0, columnspan=6, sticky="ew")
        self.v_cost_name = tk.StringVar()
        self.v_cost_qty = tk.StringVar()
        self.v_cost_comp = tk.StringVar()
        self.v_cost_sup = tk.StringVar()
        UIEntry(inp_c, textvariable=self.v_cost_name, width=18).grid(row=0,column=1, padx=2)
        UIEntry(inp_c, textvariable=self.v_cost_qty, width=8, justify="right").grid(row=0,column=3, padx=2)
        UIEntry(inp_c, textvariable=self.v_cost_comp, width=12, justify="right").grid(row=0,column=5, padx=2)
        UIEntry(inp_c, textvariable=self.v_cost_sup, width=12, justify="right").grid(row=0,column=7, padx=2)
        UIButton(inp_c, text="➕ إضافة", command=self._add_cost_record).grid(row=0,column=8, padx=10)
        UIButton(inp_c, text="🗑 حذف", command=self._del_cost_record).grid(row=0,column=9, padx=2)

        c_cols = ("م", "البند", "الكمية", "قيمة الشركة", "قيمة المشرف", "الإجمالي", "التصنيف")
        self.tv_costs_detail = ttk.Treeview(F, columns=c_cols, show="headings", height=5)
        for c, w in zip(c_cols, [30, 180, 80, 110, 110, 120, 100]):
            self.tv_costs_detail.heading(c, text=c)
            self.tv_costs_detail.column(c, width=w, anchor="center")
        self.tv_costs_detail.grid(row=row+4, column=0, columnspan=6, sticky="ew", pady=10)

        frm_tc = UIFrame(F, bg=CLR["loss_bg"], pady=8, padx=15, bd=1, relief="solid")
        frm_tc.grid(row=row+5, column=0, columnspan=6, sticky="ew", pady=(10,0))
        UILabel(frm_tc, text="إجمالي التكاليف والمصروفات:", font=FT_HEADER, bg=CLR["loss_bg"], fg=CLR["loss"]).pack(side="right")
        self.lbl_total_cost = UILabel(frm_tc, text="0", font=("Arial",16,"bold"), bg=CLR["loss_bg"], fg=CLR["loss"])
        self.lbl_total_cost.pack(side="right", padx=15)

    def _build_sales_tab(self, F):
        canvas = tk.Canvas(F, bg=CLR["bg"], highlightthickness=0)
        v_scroll = ttk.Scrollbar(F, orient="vertical", command=canvas.yview)
        scroll_frm = UIFrame(canvas)
        canvas.configure(yscrollcommand=v_scroll.set)
        canvas.pack(side="right", fill="both", expand=True)
        v_scroll.pack(side="left", fill="y")
        canvas.create_window((0,0), window=scroll_frm, anchor="nw", width=1040)
        scroll_frm.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        f_frm = UILabelFrame(scroll_frm, text="🐓 بيان مبيعات العنبر", font=FT_HEADER, fg=CLR["nav"], padx=10, pady=10)
        f_frm.pack(fill="x", pady=(0,15))
        inp_f = UIFrame(f_frm)
        inp_f.pack(fill="x", pady=5)
        self.v_fs_cust = tk.StringVar()
        self.v_fs_qty = tk.StringVar()
        self.v_fs_price = tk.StringVar()
        self.v_fs_date = tk.StringVar(value=date.today().strftime('%Y-%m-%d'))
        UIEntry(inp_f, textvariable=self.v_fs_cust, width=20).grid(row=0,column=1, padx=4)
        UIEntry(inp_f, textvariable=self.v_fs_qty, width=10, justify="right").grid(row=0,column=3, padx=4)
        UIEntry(inp_f, textvariable=self.v_fs_price, width=10, justify="right").grid(row=0,column=5, padx=4)
        UIEntry(inp_f, textvariable=self.v_fs_date, width=12).grid(row=0,column=7, padx=4)
        UIButton(inp_f, text="➕ إضافة", command=self._add_farm_sale).grid(row=0,column=8, padx=15)
        UIButton(inp_f, text="🗑 حذف", command=self._del_farm_sale).grid(row=0,column=9, padx=4)

        f_cols = ("م", "اسم العميل", "التاريخ", "الكمية", "السعر", "الإجمالي")
        self.tv_farm = ttk.Treeview(f_frm, columns=f_cols, show="headings", height=6)
        for c, w in zip(f_cols, [40, 200, 110, 100, 100, 140]):
            self.tv_farm.heading(c, text=c, anchor="center")
            self.tv_farm.column(c, width=w, anchor="center")
        self.tv_farm.pack(fill="both", expand=True, pady=5)

        m_frm = UILabelFrame(scroll_frm, text="🏢 بيان مبيعات السوق", font=FT_HEADER, fg=CLR["accent"], padx=10, pady=10)
        m_frm.pack(fill="x", pady=15)
        inp_m = UIFrame(m_frm)
        inp_m.pack(fill="x", pady=5)
        self.v_ms_office = tk.StringVar()
        self.v_ms_qty = tk.StringVar()
        self.v_ms_dead = tk.StringVar(value="0")
        self.v_ms_net = tk.StringVar()
        self.v_ms_inv = tk.StringVar()
        UIEntry(inp_m, textvariable=self.v_ms_office, width=18).grid(row=0,column=1, padx=2)
        UIEntry(inp_m, textvariable=self.v_ms_qty, width=8, justify="right").grid(row=0,column=3, padx=2)
        UIEntry(inp_m, textvariable=self.v_ms_dead, width=6, justify="right").grid(row=0,column=5, padx=2)
        UIEntry(inp_m, textvariable=self.v_ms_net, width=10, justify="right").grid(row=0,column=7, padx=2)
        UIEntry(inp_m, textvariable=self.v_ms_inv, width=10).grid(row=0,column=9, padx=2)
        UIButton(inp_m, text="➕ إضافة", command=self._add_market_sale).grid(row=0,column=10, padx=10)
        UIButton(inp_m, text="🗑 حذف", command=self._del_market_sale).grid(row=0,column=11, padx=2)

        m_cols = ("م", "مكتب التسويق", "الكمية", "الوفيات", "المباع", "صافي الفاتورة", "رقم الفاتورة")
        self.tv_mkt = ttk.Treeview(m_frm, columns=m_cols, show="headings", height=6)
        for c, w in zip(m_cols, [40, 200, 80, 80, 80, 110, 110]):
            self.tv_mkt.heading(c, text=c, anchor="center")
            self.tv_mkt.column(c, width=w, anchor="center")
        self.tv_mkt.pack(fill="both", expand=True, pady=5)

        sum_total = UIFrame(F, bg=CLR["profit_bg"], pady=10, padx=20, bd=1, relief="ridge")
        sum_total.pack(fill="x", side="bottom")
        UILabel(sum_total, text="إجمالي الإيرادات والمبيعات:", font=FT_HEADER, bg=CLR["profit_bg"], fg=CLR["profit"]).pack(side="right")
        self.lbl_total_rev = UILabel(sum_total, text="0", font=("Arial",18,"bold"), bg=CLR["profit_bg"], fg=CLR["profit"])
        self.lbl_total_rev.pack(side="right", padx=20)

    def _build_results_tab(self, F):
        v = self._vars
        v["total_sold"] = lbl_entry(F,"إجمالي الطيور المباعة", 0, 0, readonly=True)
        v["total_dead"] = lbl_entry(F,"النافق الكلي", 0, 2)
        v["mort_rate"]  = lbl_entry(F,"نسبة النافق الكلية %", 0, 4, readonly=True)
        v["avg_price"]  = lbl_entry(F,"متوسط سعر البيع", 1, 0, readonly=True)
        v["consumed_birds"] = lbl_entry(F,"طيور مستهلكة", 1, 2)
        v["share_pct"] = lbl_entry(F,"نصيب الشركة %", 2, 0)
        v["share_pct"].set("65")
        v["share_val"] = lbl_entry(F,"نصيب الشركة (ريال)", 2, 2, readonly=True)
        v["partner_name"] = lbl_entry(F,"اسم الشريك", 3, 0)
        v["notes"] = lbl_entry(F,"ملاحظات", 4, 0, 40, colspan=5)

        for key in ("total_dead","consumed_birds","share_pct"): v[key].trace_add("write", lambda *a: self._auto_calc())

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

    def _add_farm_sale(self):
        try:
            q, p = int(self.v_fs_qty.get() or 0), float(self.v_fs_price.get() or 0)
            if q > 0:
                self._farm_sales.append({"customer": self.v_fs_cust.get(), "qty": q, "price": p, "total_val": q*p, "sale_date": self.v_fs_date.get()})
                self._refresh_sales_views(); self._auto_calc()
        except: pass

    def _del_farm_sale(self):
        sel = self.tv_farm.selection()
        if sel:
            self._farm_sales.pop(self.tv_farm.index(sel[0]))
            self._refresh_sales_views(); self._auto_calc()

    def _add_market_sale(self):
        try:
            q, d, n = int(self.v_ms_qty.get() or 0), int(self.v_ms_dead.get() or 0), float(self.v_ms_net.get() or 0)
            if q > 0:
                self._market_sales.append({"office": self.v_ms_office.get(), "qty_sent": q, "deaths": d, "qty_sold": q-d, "net_val": n, "inv_num": self.v_ms_inv.get()})
                self._refresh_sales_views(); self._auto_calc()
        except: pass

    def _del_market_sale(self):
        sel = self.tv_mkt.selection()
        if sel:
            self._market_sales.pop(self.tv_mkt.index(sel[0]))
            self._refresh_sales_views(); self._auto_calc()

    def _refresh_sales_views(self):
        for tv, data in [(self.tv_farm, self._farm_sales), (self.tv_mkt, self._market_sales)]:
            tv.delete(*tv.get_children())
            for i, s in enumerate(data, 1):
                if tv == self.tv_farm: tv.insert("", "end", values=(i, s["customer"], s.get("sale_date", ""), fmt_num(s["qty"]), fmt_num(s["price"],2), fmt_num(s["total_val"])))
                else: tv.insert("", "end", values=(i, s["office"], fmt_num(s["qty_sent"]), fmt_num(s["deaths"]), fmt_num(s["qty_sold"]), fmt_num(s["net_val"]), s["inv_num"]))

    def _add_cost_record(self):
        try:
            name = self.v_cost_name.get()
            q, c, s = float(self.v_cost_qty.get() or 0), float(self.v_cost_comp.get() or 0), float(self.v_cost_sup.get() or 0)
            if name:
                cat = 'feed' if "علف" in name else ('gas' if "غاز" in name else ('sawdust' if "نشارة" in name else ('chicks' if "صوص" in name else ('drugs' if "علاج" in name else 'other'))))
                self._cost_records.append({'cost_name': name, 'qty': q, 'company_val': c, 'supervisor_val': s, 'category': cat})
                self._sync_detailed_to_vars()
        except: pass

    def _del_cost_record(self):
        sel = self.tv_costs_detail.selection()
        if sel:
            self._cost_records.pop(self.tv_costs_detail.index(sel[0]))
            self._sync_detailed_to_vars()

    def _sync_detailed_to_vars(self):
        self._syncing = True
        sums = {k: 0 for k in ['feed_val', 'feed_qty', 'gas_val', 'gas_qty', 'sawdust_val', 'sawdust_qty', 'chick_val', 'drugs_val']}
        for r in self._cost_records:
            cat = r.get('category')
            val, qty = float(r.get('company_val', 0) or 0) + float(r.get('supervisor_val', 0) or 0), float(r.get('qty', 0) or 0)
            if cat == 'feed': sums['feed_val'] += val; sums['feed_qty'] += qty
            elif cat == 'gas': sums['gas_val'] += val; sums['gas_qty'] += qty
            elif cat == 'sawdust': sums['sawdust_val'] += val; sums['sawdust_qty'] += qty
            elif cat == 'chicks': sums['chick_val'] += val
            elif cat == 'drugs': sums['drugs_val'] += val
        for k, v in sums.items():
            if k in self._vars: self._vars[k].set(str(v) if v > 0 else "")
        self._syncing = False; self._refresh_costs_view(); self._auto_calc()

    def _refresh_costs_view(self):
        self.tv_costs_detail.delete(*self.tv_costs_detail.get_children())
        for i, r in enumerate(self._cost_records, 1):
            comp, sup = float(r.get('company_val', 0) or 0), float(r.get('supervisor_val', 0) or 0)
            self.tv_costs_detail.insert("", "end", values=(i, r.get('cost_name'), r.get('qty'), fmt_num(comp), fmt_num(sup), fmt_num(comp+sup), r.get('category')))

    def _auto_calc(self):
        if self._syncing: return
        v = self._vars
        def n(k):
            try: return float(v[k].get() or 0)
            except: return 0.0
        
        # Date and Days
        try:
            d1, d2 = datetime.strptime(v["date_in"].get(), "%Y-%m-%d"), datetime.strptime(v["date_out"].get(), "%Y-%m-%d")
            v["days"].set((d2 - d1).days if (d2 - d1).days > 0 else "")
        except: v["days"].set("")

        # Totals
        cost_keys = ["feed_val","feed_trans","sawdust_val","water_val","gas_val","drugs_val","wh_expenses","house_exp","breeders_pay","qat_pay","rent_val","light_val","sup_wh_pay","sup_co_pay","sup_sale_pay","admin_val","vaccine_pay","delivery_val","mixing_val","wash_val","other_costs"]
        total_cost = n("chick_val") + sum(n(k) for k in cost_keys)
        self.lbl_total_cost.config(text=f"{fmt_num(total_cost)} ريال")

        f_qty, f_val = sum(x['qty'] for x in self._farm_sales), sum(x['total_val'] for x in self._farm_sales)
        m_qty, m_val = sum(x['qty_sold'] for x in self._market_sales), sum(x['net_val'] for x in self._market_sales)
        total_rev = f_val + m_val + sum(n(k) for k in ["offal_val","feed_sale","feed_trans_r","drug_return","gas_return"])
        self.lbl_total_rev.config(text=f"{fmt_num(total_rev)} ريال")

        # Ratios
        chicks, dead, days, weight = n("chicks"), n("total_dead"), n("days"), n("avg_weight")
        mort = (dead/chicks*100) if chicks > 0 else 0
        v["mort_rate"].set(f"{mort:.2f}" if chicks > 0 else "")
        sold = f_qty + m_qty
        v["total_sold"].set(fmt_num(sold))
        v["avg_price"].set(fmt_num((f_val+m_val)/sold, 2) if sold > 0 else "")
        
        fcr = (n("feed_qty")*1000)/(sold*weight) if sold > 0 and weight > 0 else 0
        v["fcr"].set(f"{fcr:.3f}" if fcr > 0 else "")
        
        epef = ((100-mort)*weight*10)/(days*fcr) if days > 0 and fcr > 0 else 0
        self.lbl_epef.config(text=f"{epef:.0f}", foreground=(CLR["profit"] if epef >= 300 else CLR["loss"]))
        
        net = total_rev - total_cost
        self.lbl_net.config(text=f"{fmt_num(net)} ريال", foreground=(CLR["profit"] if net >= 0 else CLR["loss"]))
        v["share_val"].set(fmt_num(net * n("share_pct") / 100))

    def _load_batch(self):
        self._syncing = True
        row = self.db.fetch_one("SELECT * FROM v_batches WHERE id=?", (self.batch_id,))
        if row:
            self.wh_var.set(row["warehouse_name"])
            for k, var in self._vars.items():
                if k in row and row[k] is not None: var.set(str(row[k]))
            f_sales = self.db.fetch_all("SELECT * FROM farm_sales WHERE batch_id=?", (self.batch_id,))
            self._farm_sales = [dict(r) for r in f_sales]
            m_sales = self.db.fetch_all("SELECT * FROM market_sales WHERE batch_id=?", (self.batch_id,))
            self._market_sales = [dict(r) for r in m_sales]
            c_recs = self.db.fetch_all("SELECT * FROM batch_cost_records WHERE batch_id=?", (self.batch_id,))
            self._cost_records = [dict(r) for r in c_recs]
            self._refresh_sales_views(); self._refresh_costs_view()
        self._syncing = False; self._auto_calc()

    def _save(self):
        wh_name = self.wh_var.get().strip()
        if not wh_name: return messagebox.showwarning("تنبيه", "يرجى تحديد اسم العنبر")
        
        def n(k):
            try: return float(self._vars[k].get() or 0)
            except: return 0.0
        def s(k): return self._vars[k].get().strip()
        
        data = {
            "batch_num": s("batch_num"), "date_in": s("date_in"), "date_out": s("date_out"), "days": int(n("days")),
            "chicks": int(n("chicks")), "chick_val": n("chick_val"), "feed_qty": n("feed_qty"), "feed_val": n("feed_val"),
            "feed_trans": n("feed_trans"), "sawdust_qty": n("sawdust_qty"), "sawdust_val": n("sawdust_val"), "water_val": n("water_val"),
            "gas_qty": n("gas_qty"), "gas_val": n("gas_val"), "drugs_val": n("drugs_val"), "wh_expenses": n("wh_expenses"),
            "house_exp": n("house_exp"), "breeders_pay": n("breeders_pay"), "qat_pay": n("qat_pay"), "rent_val": n("rent_val"),
            "light_val": n("light_val"), "sup_wh_pay": n("sup_wh_pay"), "sup_co_pay": n("sup_co_pay"), "sup_sale_pay": n("sup_sale_pay"),
            "admin_val": n("admin_val"), "vaccine_pay": n("vaccine_pay"), "delivery_val": n("delivery_val"), "mixing_val": n("mixing_val"),
            "wash_val": n("wash_val"), "other_costs": n("other_costs"), "total_cost": n("chick_val")+sum(n(k) for k in ["feed_val","feed_trans","sawdust_val","water_val","gas_val","drugs_val","wh_expenses","house_exp","breeders_pay","qat_pay","rent_val","light_val","sup_wh_pay","sup_co_pay","sup_sale_pay","admin_val","vaccine_pay","delivery_val","mixing_val","wash_val","other_costs"]),
            "cust_qty": sum(x['qty'] for x in self._farm_sales), "cust_val": sum(x['total_val'] for x in self._farm_sales),
            "mkt_qty": sum(x['qty_sent'] for x in self._market_sales), "mkt_val": sum(x['net_val'] for x in self._market_sales),
            "offal_val": n("offal_val"), "feed_sale": n("feed_sale"), "feed_trans_r": n("feed_trans_r"), "drug_return": n("drug_return"), "gas_return": n("gas_return"),
            "total_rev": sum(x['total_val'] for x in self._farm_sales) + sum(x['net_val'] for x in self._market_sales) + sum(n(k) for k in ["offal_val","feed_sale","feed_trans_r","drug_return","gas_return"]),
            "total_sold": int(n("total_sold")), "total_dead": int(n("total_dead")), "mort_rate": n("mort_rate"), "avg_weight": n("avg_weight"),
            "fcr": n("fcr"), "avg_price": n("avg_price"), "net_result": n("total_rev")-n("total_cost"), "share_pct": n("share_pct"),
            "share_val": (n("total_rev")-n("total_cost"))*n("share_pct")/100, "notes": s("notes"), "consumed_birds": int(n("consumed_birds")), "partner_name": s("partner_name")
        }
        
        wh = self.db.fetch_one("SELECT id FROM warehouses WHERE name=?", (wh_name,))
        if not wh: 
            wh_id = self.db.execute("INSERT INTO warehouses (name) VALUES (?)", (wh_name,))
        else: wh_id = wh["id"]

        if self.batch_id:
            update_str = ",".join(f"{k}=?" for k in data)
            self.db.execute(f"UPDATE batches SET warehouse_id=?, {update_str} WHERE id=?", [wh_id] + list(data.values()) + [self.batch_id])
            b_id = self.batch_id
        else:
            cols, qs = ",".join(data.keys()), ",".join("?" for _ in data)
            b_id = self.db.execute(f"INSERT INTO batches (warehouse_id, {cols}, created_at) VALUES (?, {qs}, datetime('now'))", [wh_id] + list(data.values()))
        
        self.db.execute("DELETE FROM farm_sales WHERE batch_id=?", (b_id,))
        for fs in self._farm_sales: self.db.execute("INSERT INTO farm_sales (batch_id, customer, qty, price, total_val, sale_date) VALUES (?,?,?,?,?,?)", (b_id, fs["customer"], fs["qty"], fs["price"], fs["total_val"], fs.get("sale_date","")))
        self.db.execute("DELETE FROM market_sales WHERE batch_id=?", (b_id,))
        for ms in self._market_sales: self.db.execute("INSERT INTO market_sales (batch_id, office, qty_sent, deaths, qty_sold, net_val, inv_num) VALUES (?,?,?,?,?,?,?)", (b_id, ms["office"], ms["qty_sent"], ms["deaths"], ms["qty_sold"], ms["net_val"], ms["inv_num"]))
        self.db.execute("DELETE FROM batch_cost_records WHERE batch_id=?", (b_id,))
        for cr in self._cost_records: self.db.execute("INSERT INTO batch_cost_records (batch_id, cost_name, qty, company_val, supervisor_val, category) VALUES (?,?,?,?,?,?)", (b_id, cr['cost_name'], cr['qty'], cr['company_val'], cr['supervisor_val'], cr.get('category','other')))
        
        messagebox.showinfo("تم", "تم حفظ الدفعة بنجاح"); self.on_save() if self.on_save else None; self.destroy()

class DailyRecordsWindow(ToplevelBase):
    def __init__(self, master, db, batch_id, batch_info):
        super().__init__(master)
        self.db = db
        self.batch_id = batch_id
        self.batch_info = batch_info
        self.title(f"السجلات اليومية - {batch_info.get('warehouse_name','')} - دفعة {batch_info.get('batch_num') or batch_id}")
        self.geometry("900x600")
        self.grab_set()
        self._build()
        self._load()

    def _build(self):
        hdr = UIFrame(self, bg=CLR["header"], pady=10)
        hdr.pack(fill="x")
        UILabel(hdr, text=f"📅 السجلات اليومية للمنظومة", font=FT_TITLE, bg=CLR["header"], fg="white").pack(side="right", padx=16)

        inp = UILabelFrame(self, text="إضافة سجل يومي", font=FT_HEADER, padx=10, pady=8)
        inp.pack(fill="x", padx=10, pady=8)
        self.v_date = tk.StringVar(value=date.today().isoformat())
        self.v_daynum, self.v_dead, self.v_feed, self.v_notes = tk.StringVar(), tk.StringVar(value="0"), tk.StringVar(value="0"), tk.StringVar()
        
        UILabel(inp, text="التاريخ:").grid(row=0, column=0); UIEntry(inp, textvariable=self.v_date, width=14).grid(row=0, column=1)
        UILabel(inp, text="اليوم رقم:").grid(row=0, column=2); UIEntry(inp, textvariable=self.v_daynum, width=6).grid(row=0, column=3)
        UILabel(inp, text="النافق:").grid(row=0, column=4); UIEntry(inp, textvariable=self.v_dead, width=8).grid(row=0, column=5)
        UILabel(inp, text="العلف (كجم):").grid(row=0, column=6); UIEntry(inp, textvariable=self.v_feed, width=10).grid(row=0, column=7)
        UILabel(inp, text="ملاحظة:").grid(row=1, column=0); UIEntry(inp, textvariable=self.v_notes, width=50).grid(row=1, column=1, columnspan=6, sticky="ew")
        
        btn_f = UIFrame(inp); btn_f.grid(row=1, column=7)
        UIButton(btn_f, text="💾 حفظ", command=self._save_record).pack(side="right", padx=2)
        UIButton(btn_f, text="🗑 حذف", command=self._del_record).pack(side="right", padx=2)

        self.tree = ttk.Treeview(self, columns=("التاريخ","اليوم","النافق","تراكم النافق","العلف","إجمالي العلف","ملاحظة"), show="headings")
        for c in self.tree["columns"]: self.tree.heading(c, text=c); self.tree.column(c, width=100, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        
        self.lbl_summary = UILabel(self, text="", font=FT_BODY, fg=CLR["accent"])
        self.lbl_summary.pack(pady=5)
        UIButton(self, text="📥 تصدير Excel", command=self._export_excel).pack(pady=10)

    def _load(self):
        rows = self.db.fetch_all("SELECT rec_date, day_num, dead_count, feed_kg, notes FROM daily_records WHERE batch_id=? ORDER BY rec_date", (self.batch_id,))
        self.tree.delete(*self.tree.get_children()); cum_dead, cum_feed = 0, 0.0
        for r in rows:
            cum_dead += r["dead_count"]; cum_feed += r["feed_kg"]
            self.tree.insert("", "end", iid=r["rec_date"], values=(r["rec_date"], r["day_num"] or "", r["dead_count"], cum_dead, fmt_num(r["feed_kg"],1), fmt_num(cum_feed,1), r["notes"] or ""))
        chicks = self.batch_info.get("chicks", 0) or 0
        mort = (cum_dead/chicks*100) if chicks > 0 else 0
        self.lbl_summary.config(text=f"إجمالي النافق: {cum_dead} ({mort:.2f}%) | إجمالي العلف: {fmt_num(cum_feed,1)} كجم")

    def _on_select(self, _=None):
        sel = self.tree.selection()
        if sel:
            r = self.db.fetch_one("SELECT * FROM daily_records WHERE batch_id=? AND rec_date=?", (self.batch_id, sel[0]))
            if r: self.v_date.set(r["rec_date"]); self.v_daynum.set(str(r["day_num"] or "")); self.v_dead.set(str(r["dead_count"])); self.v_feed.set(str(r["feed_kg"])); self.v_notes.set(r["notes"] or "")

    def _save_record(self):
        try:
            d, dn, dc, f = self.v_date.get(), int(self.v_daynum.get() or 0), int(self.v_dead.get() or 0), float(self.v_feed.get() or 0)
            self.db.execute("INSERT INTO daily_records (batch_id, rec_date, day_num, dead_count, feed_kg, notes) VALUES (?,?,?,?,?,?) ON CONFLICT(batch_id, rec_date) DO UPDATE SET day_num=excluded.day_num, dead_count=excluded.dead_count, feed_kg=excluded.feed_kg, notes=excluded.notes", (self.batch_id, d, dn, dc, f, self.v_notes.get()))
            row = self.db.fetch_one("SELECT SUM(dead_count) FROM daily_records WHERE batch_id=?", (self.batch_id,))
            td = row[0] if row else 0; chicks = self.batch_info.get("chicks", 1)
            self.db.execute("UPDATE batches SET total_dead=?, mort_rate=? WHERE id=?", (td, round(td/chicks*100, 2), self.batch_id))
            self._load(); self.v_daynum.set(str(dn+1)); self.v_dead.set("0"); self.v_feed.set("0"); self.v_notes.set("")
        except: pass

    def _del_record(self):
        sel = self.tree.selection()
        if sel and messagebox.askyesno("تأكيد", "حذف السجل؟"):
            self.db.execute("DELETE FROM daily_records WHERE batch_id=? AND rec_date=?", (self.batch_id, sel[0]))
            self._load()

    def _export_excel(self):
        if not HAS_OPENPYXL: return
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=f"سجل_يومي_دفعة_{self.batch_id}.xlsx")
        if path:
            rows = self.db.fetch_all("SELECT * FROM daily_records WHERE batch_id=? ORDER BY rec_date", (self.batch_id,))
            wb = openpyxl.Workbook(); ws = wb.active; ws.title = "السجل اليومي"; ws.sheet_view.rightToLeft = True
            ws.append(["التاريخ","اليوم","النافق","تراكم النافق","العلف كجم","إجمالي العلف","ملاحظة"])
            cd, cf = 0, 0.0
            for r in rows: cd += r["dead_count"]; cf += r["feed_kg"]; ws.append([r["rec_date"], r["day_num"], r["dead_count"], cd, r["feed_kg"], cf, r["notes"]])
            wb.save(path); messagebox.showinfo("تم", "تم التصدير")
