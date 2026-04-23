import sys
import os

# إضافة مجلد المشروع للمسار لتمكين الاستيراد
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from v5.database.connection import db_session
from v5.database.models import Warehouse, Batch

def test_internal_link():
    print("--- اختبار الربط الداخلي للنسخة الخامسة ---")
    try:
        warehouses_count = db_session.query(Warehouse).count()
        batches_count = db_session.query(Batch).count()
        
        print(f"تم العثور على {warehouses_count} عنبر في الجلسة الحالية.")
        print(f"تم العثور على {batches_count} دورة في الجلسة الحالية.")
        
        if warehouses_count == 0:
            from v5.database.connection import DB_URL
            print(f"⚠️ تحذير: الجلسة فارغة! المسار المستخدم هو: {DB_URL}")
            print("سأحاول البحث عن ملف القاعدة في المجلدات المجاورة...")
            
    except Exception as e:
        print(f"❌ خطأ في الاتصال الداخلي: {e}")

if __name__ == "__main__":
    test_internal_link()
