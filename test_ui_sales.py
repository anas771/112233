import tkinter as tk
from tkinter import ttk
import os
import sys

# إضافة المسار الحالي لتمكين استيراد main
sys.path.append(os.getcwd())

try:
    from main import BatchForm, db, CLR, FT_TITLE, FT_HEADER, FT_BODY, FT_SMALL
    import main
except ImportError as e:
    print(f"Error importing: {e}")
    sys.exit(1)

def run_test():
    root = tk.Tk()
    root.withdraw() # لا نحتاج للنافذة الرئيسية
    
    # اختيار دفعة موجودة (مثلا رقم 12 حسين صادق)
    batch_id = 12
    
    print(f"Opening BatchForm for ID {batch_id}...")
    try:
        form = BatchForm(root, batch_id=batch_id)
        
        # الانتقال لتبويب المبيعات (التبويب الثالث)
        # self.notebook.add(self.tab_sales,   text="📈 سجل المبيعات")
        # هو التبويب رقم 2 (0-indexed)
        form.notebook.select(2)
        root.update()
        
        # حفظ صورة للواجهة للتأكد
        from PIL import ImageGrab
        import time
        
        time.sleep(2) # انتظار الرسم
        
        # الحصول على إحداثيات النافذة
        x = form.winfo_rootx()
        y = form.winfo_rooty()
        w = form.winfo_width()
        h = form.winfo_height()
        
        print(f"Capturing screenshot at ({x},{y},{w},{h})...")
        # نستخدم الكاميرا الخاصة بالنظام إذا كانت متوفرة أو Pillow
        # في بيئة Antigravity نفضل استخدام التوليد أو البروز أو مجرد التأكد برمجياً
        
        # بما أننا لا نستطيع رؤية الشاشة مباشرة، سنقوم بمراجعة الكود والتأكد من عدم وجود أخطاء منطقية
        # التأكد من وجود الكانفاس والسكربار
        sales_tab_children = form.tab_sales.winfo_children()
        print("Sales tab content:", [type(c).__name__ for c in sales_tab_children])
        
        has_canvas = any(isinstance(c, tk.Canvas) for c in sales_tab_children)
        if has_canvas:
            print("SUCCESS: Canvas found in sales tab.")
        else:
            print("FAILURE: Canvas NOT found in sales tab.")
            
        form.destroy()
        root.destroy()
        
    except Exception:
        import traceback
        traceback.print_exc()
        root.destroy()

if __name__ == "__main__":
    run_test()
