import tkinter as tk
from ui.constants import HAS_MATPLOTLIB, CLR, FT_TITLE, FT_HEADER, FT_BODY, FN, FT_TINY
from ui.widgets import ToplevelBase, UIFrame, UILabel
from utils.text_utils import prepare_text

if HAS_MATPLOTLIB:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure

class DashboardWindow(ToplevelBase):
    def __init__(self, master, db):
        super().__init__(master)
        self.db = db
        self.title("لوحة القياس والرسوم البيانية (Dashboard)")
        self.geometry("1100x650")
        self.grab_set()
        self._build()

    def _build(self):
        hdr = UIFrame(self, bg=CLR["header"], pady=10)
        hdr.pack(fill="x")
        UILabel(hdr, text="📈 لوحة القياس التفاعلية (Dashboard)", font=FT_TITLE, bg=CLR["header"], fg="white").pack(side="right", padx=16)

        if not HAS_MATPLOTLIB:
            UILabel(self, text="مكتبة الرسوم البيانية (matplotlib) غير مثبتة", font=FT_HEADER, fg="red").pack(pady=50)
            return

        batches = self.db.fetch_all("SELECT * FROM v_batches ORDER BY date_in ASC")
        if not batches:
            UILabel(self, text="لا توجد بيانات كافية لعرض الرسوم البيانية.", font=FT_HEADER).pack(pady=50)
            return

        labels = []
        nets = []
        morts = []
        colors = []
        
        for b in batches:
            labels.append(f"دفعة {b['batch_num'] or b['id']}")
            n_val = b['net_result_dynamic'] if 'net_result_dynamic' in b else (b['net_result'] or 0)
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
        ax2.plot(labels, morts, marker='o', color=CLR["header"], linestyle='-', linewidth=2.5, markersize=8)
        ax2.set_title(prepare_text("معدل النافق الكلي (%)"), fontsize=14, pad=10)
        ax2.set_ylim(bottom=0)
        ax2.grid(True, linestyle='--', alpha=0.6)
        ax2.tick_params(axis='x', rotation=45)

        fig.tight_layout(pad=3.0)
        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=15)
