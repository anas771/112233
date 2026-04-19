import sys
import os
from PySide6.QtWidgets import QApplication
from app.ui.main_window import MainWindow
from app.ui.styles import apply_modern_style

def main():
    # 1. تهيئة التطبيق مع دعم الشاشات عالية الدقة
    app = QApplication(sys.argv)
    
    # 2. تطبيق الثيم المطور (Modern Dark/Light Theme)
    apply_modern_style(app)
    
    # تحسين مظهر الخطوط في ويندوز
    app.setStyle("Fusion")
    
    # 3. تشغيل النافذة الرئيسية المطورة
    print("Launching Modern Poultry Pro v5.0...")
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
