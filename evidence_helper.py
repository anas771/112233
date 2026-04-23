import tkinter as tk
from tkinter import ttk, messagebox
import json
from datetime import datetime
import os

class EvidenceHelper:
    def __init__(self, root):
        self.root = root
        self.root.title("مساعد توثيق الجرائم الإلكترونية - نسخة مفعلة")
        self.root.geometry("600x550")
        self.root.configure(bg="#f4f4f4")
        
        # ملف تخزين البيانات
        self.db_file = "evidence_data.json"
        self.load_data()

        self.setup_ui()

    def setup_ui(self):
        # العنوان
        header = tk.Label(self.root, text="نظام توثيق أدلة التشهير والإساءة", font=("Arial", 16, "bold"), bg="#2c3e50", fg="white", pady=10)
        header.pack(fill="x")

        # حالة التفعيل
        status_bar = tk.Label(self.root, text="● النسخة مفعلة لـ حمير وحيش", font=("Arial", 10), bg="#27ae60", fg="white")
        status_bar.pack(fill="x")

        main_frame = tk.Frame(self.root, bg="#f4f4f4", padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        # حقل اسم المتهم
        tk.Label(main_frame, text="اسم الحساب/الشخص المسيء:", font=("Arial", 12), bg="#f4f4f4").grid(row=0, column=1, sticky="e", pady=5)
        self.name_entry = tk.Entry(main_frame, width=40, font=("Arial", 12), justify="right")
        self.name_entry.grid(row=0, column=0, pady=5)
        self.name_entry.insert(0, "صاحب الحساب")

        # حقل الرابط
        tk.Label(main_frame, text="رابط المنشور أو الملف الشخصي:", font=("Arial", 12), bg="#f4f4f4").grid(row=1, column=1, sticky="e", pady=5)
        self.link_entry = tk.Entry(main_frame, width=40, font=("Arial", 12), justify="right")
        self.link_entry.grid(row=1, column=0, pady=5)
        self.link_entry.insert(0, "https://www.facebook.com/profile.php?id=61576197621620")

        # وصف الإساءة
        tk.Label(main_frame, text="وصف الإساءة (مثلاً: صورة بالذكاء الاصطناعي):", font=("Arial", 12), bg="#f4f4f4").grid(row=2, column=1, sticky="e", pady=5)
        self.desc_text = tk.Text(main_frame, width=40, height=5, font=("Arial", 12))
        self.desc_text.tag_configure("right", justify="right")
        self.desc_text.grid(row=2, column=0, pady=5)
        self.desc_text.insert("1.0", "استخدام صور بالذكاء الاصطناعي لتشويه سمعة حمير وحيش", "right")

        # أزرار التحكم
        btn_frame = tk.Frame(main_frame, bg="#f4f4f4")
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20)

        save_btn = tk.Button(btn_frame, text="حفظ الدليل", command=self.save_evidence, bg="#27ae60", fg="white", font=("Arial", 12, "bold"), width=15)
        save_btn.pack(side="right", padx=10)

        report_btn = tk.Button(btn_frame, text="تصدير تقرير للشرطة", command=self.generate_report, bg="#2980b9", fg="white", font=("Arial", 12, "bold"), width=15)
        report_btn.pack(side="left", padx=10)

        # قائمة العرض
        self.tree = ttk.Treeview(main_frame, columns=("Date", "Name"), show="headings", height=5)
        self.tree.heading("Date", text="التاريخ")
        self.tree.heading("Name", text="اسم الحساب")
        self.tree.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=10)
        self.update_list()

    def save_evidence(self):
        name = self.name_entry.get()
        link = self.link_entry.get()
        desc = self.desc_text.get("1.0", tk.END).strip()

        if not name or not link:
            messagebox.showwarning("تنبيه", "يرجى إدخال الاسم والرابط على الأقل")
            return

        evidence = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "name": name,
            "link": link,
            "description": desc
        }

        self.evidences.append(evidence)
        with open(self.db_file, "w", encoding="utf-8") as f:
            json.dump(self.evidences, f, ensure_ascii=False, indent=4)
        
        messagebox.showinfo("نجاح", "تم حفظ الدليل بنجاح")
        self.update_list()

    def load_data(self):
        if os.path.exists(self.db_file):
            with open(self.db_file, "r", encoding="utf-8") as f:
                self.evidences = json.load(f)
        else:
            self.evidences = []

    def update_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for ev in self.evidences:
            self.tree.insert("", "end", values=(ev["date"], ev["name"]))

    def generate_report(self):
        if not self.evidences:
            messagebox.showwarning("تنبيه", "لا توجد أدلة لتصديرها")
            return

        report_name = f"تقرير_بلاغ_{datetime.now().strftime('%Y%m%d')}.txt"
        with open(report_name, "w", encoding="utf-8") as f:
            f.write("=== تقرير بلاغ جريمة إلكترونية (تشويه سمعة) ===\n")
            f.write(f"تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d')}\n")
            f.write("-" * 40 + "\n\n")
            for i, ev in enumerate(self.evidences, 1):
                f.write(f"الدليل رقم ({i}):\n")
                f.write(f"- التاريخ: {ev['date']}\n")
                f.write(f"- اسم الحساب المسيء: {ev['name']}\n")
                f.write(f"- الرابط: {ev['link']}\n")
                f.write(f"- الوصف: {ev['description']}\n")
                f.write("-" * 20 + "\n")
        
        messagebox.showinfo("تم التصدير", f"تم إنشاء التقرير باسم: {report_name}\nيمكنك طباعته وتقديمه للجهات المختصة.")

if __name__ == "__main__":
    root = tk.Tk()
    app = EvidenceHelper(root)
    root.mainloop()
