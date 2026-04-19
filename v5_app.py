import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# إضافة المجلد الحالي للمسار لضمان عمل الاستيرادات بشكل صحيح
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from v5.ui.main_window import MainWindow
from v5.database.connection import init_db, db_session

def main():
    # تهيئة قاعدة البيانات (إنشاء الجداول إذا لم تكن موجودة)
    print("Initializing Database...")
    init_db()
    
    app = QApplication(sys.argv)
    
    # ضبط اتجاه التطبيق للعربية
    app.setLayoutDirection(Qt.RightToLeft)
    
    window = MainWindow(db_session)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
