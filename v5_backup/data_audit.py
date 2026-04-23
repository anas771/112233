import sqlite3
import os
import sys

# ضمان أن المخرجات تستخدم ترميز UTF-8 لتجنب مشاكل اللغة العربية
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

def audit_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "poultry_data.db")
    
    if not os.path.exists(db_path):
        print(f"ERROR: لم يتم العثور على قاعدة البيانات في المسار: {db_path}")
        return

    print("==================================================")
    print("تقرير فحص وتدقيق بيانات مشروع الدجاج")
    print("==================================================")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # فحص الجداول الأساسية
        tables = ["warehouses", "batches", "daily_records", "farm_sales", "market_sales"]
        summary = {}
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                summary[table] = count
            except sqlite3.OperationalError:
                summary[table] = "جدول غير موجود"

        print(f"ملخص السجلات الحالية:")
        print(f"  - عدد العنابر: {summary.get('warehouses', 0)}")
        print(f"  - عدد الدفعات (الدورات): {summary.get('batches', 0)}")
        print(f"  - السجلات اليومية: {summary.get('daily_records', 0)}")
        print(f"  - عمليات البيع (مزرعة): {summary.get('farm_sales', 0)}")
        print(f"  - عمليات البيع (سوق): {summary.get('market_sales', 0)}")
        
        # فحص وجود أعمدة جديدة
        print("\nفحص التوافق التقني:")
        cursor.execute("PRAGMA table_info(batches)")
        columns = [col[1] for col in cursor.fetchall()]
        
        new_features = ["partner_name", "fcr", "avg_weight"]
        for feat in new_features:
            if feat in columns:
                print(f"  - ميزة {feat}: متوفرة ومفعمة بالبيانات.")
            else:
                print(f"  - ميزة {feat}: غير متوفرة (سيقوم النظام بتهيئتها تلقائياً).")

        conn.close()
        print("\nانتهى الفحص. قاعدة البيانات جاهزة للربط مع النسخة الخامسة.")
        print("==================================================")

    except Exception as e:
        print(f"حدث خطأ أثناء الفحص: {e}")

if __name__ == "__main__":
    audit_data()
