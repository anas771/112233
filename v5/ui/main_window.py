from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QStackedWidget, QFrame, QSizePolicy)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont
from v5.ui.dashboard import DashboardPage
from v5.ui.batches_view import BatchesPage
from v5.ui.daily_records_view import DailyRecordsPage
from v5.ui.sales_view import SalesPage
from v5.ui.costs_view import CostsPage
from v5.ui.reports_view import ReportsPage
from v5.ui.inventory_view import InventoryPage
from v5.ui.settings_view import SettingsPage

class MainWindow(QMainWindow):
    def __init__(self, db_session):
        super().__init__()
        self.db = db_session
        self.setWindowTitle("نظام إدارة الدواجن الاحترافي v5.0")
        self.resize(1200, 800)
        self.setLayoutDirection(Qt.RightToLeft) # دعم كامل للعربية من البداية
        
        # تحميل التنسيق
        self._load_stylesheet()
        
        # المكون الرئيسي
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. القائمة الجانبية (Side Menu)
        self.side_menu = QFrame()
        self.side_menu.setObjectName("sideMenu")
        side_layout = QVBoxLayout(self.side_menu)
        side_layout.setContentsMargins(0, 20, 0, 0)
        side_layout.setSpacing(5)
        
        # الشعار أو اسم البرنامج
        logo_label = QLabel("🐔 دوجي برو")
        logo_label.setObjectName("logoLabel")
        logo_label.setAlignment(Qt.AlignCenter)
        side_layout.addWidget(logo_label)
        
        # أزرار التنقل
        self.nav_btns = {}
        menu_items = [
            ("dashboard", "📊 لوحة التحكم"),
            ("batches", "📋 إدارة الدفعات"),
            ("daily", "📅 السجلات اليومية"),
            ("inventory", "📦 المخازن"),
            ("sales", "💰 المبيعات"),
            ("costs", "💸 التكاليف"),
            ("reports", "📈 التقارير"),
            ("settings", "⚙️ الإعدادات")
        ]
        
        for key, text in menu_items:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.clicked.connect(lambda checked, k=key: self._switch_view(k))
            side_layout.addWidget(btn)
            self.nav_btns[key] = btn
            
        side_layout.addStretch()
        
        # 2. منطقة المحتوى (Content Area)
        content_container = QVBoxLayout()
        
        # الهيدر (Header)
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(60)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        self.view_title = QLabel("لوحة التحكم")
        header_layout.addWidget(self.view_title)
        header_layout.addStretch()
        
        user_info = QLabel("المسؤول: أنس")
        user_info.setObjectName("userInfo")
        header_layout.addWidget(user_info)
        
        content_container.addWidget(header)
        
        # كدس الصفحات (Stacked Widget)
        self.pages = QStackedWidget()
        self.pages.setObjectName("contentArea")
        
        # إضافة الصفحات
        self.dashboard = DashboardPage(self.db)
        self.batches_page = BatchesPage(self.db)
        self.daily_page = DailyRecordsPage(self.db)
        self.sales_page = SalesPage(self.db)
        self.costs_page = CostsPage(self.db)
        self.reports_page = ReportsPage(self.db)
        self.inventory_page = InventoryPage(self.db)
        self.settings_page = SettingsPage(self.db)
        
        self.pages.addWidget(self.dashboard)
        self.pages.addWidget(self.batches_page)
        self.pages.addWidget(self.daily_page)
        self.pages.addWidget(self.sales_page)
        self.pages.addWidget(self.costs_page)
        self.pages.addWidget(self.reports_page)
        self.pages.addWidget(self.inventory_page)
        self.pages.addWidget(self.settings_page)
        
        # صفحة مؤقتة للبقية
        self.placeholder = QLabel("هذه الصفحة قيد الإنشاء...")
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.pages.addWidget(self.placeholder)
        
        content_container.addWidget(self.pages)
        
        # إضافة الكل للمخطط الرئيسي
        main_layout.addWidget(self.side_menu)
        main_layout.addLayout(content_container)
        
        # اختيار الصفحة الأولى
        self.nav_btns["dashboard"].setChecked(True)

    def _load_stylesheet(self):
        import os
        style_path = os.path.join(os.path.dirname(__file__), "styles", "modern.qss")
        if os.path.exists(style_path):
            with open(style_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

    def _switch_view(self, key):
        titles = {
            "dashboard": "📊 لوحة التحكم",
            "batches": "📋 إدارة الدفعات",
            "daily": "📅 السجلات اليومية",
            "sales": "💰 المبيعات",
            "costs": "💸 التكاليف",
            "reports": "📈 التقارير",
            "settings": "⚙️ الإعدادات"
        }
        self.view_title.setText(titles.get(key, ""))
        
        if key == "dashboard":
            self.pages.setCurrentWidget(self.dashboard)
        elif key == "batches":
            self.pages.setCurrentWidget(self.batches_page)
        elif key == "daily":
            self.pages.setCurrentWidget(self.daily_page)
        elif key == "sales":
            self.pages.setCurrentWidget(self.sales_page)
        elif key == "costs":
            self.pages.setCurrentWidget(self.costs_page)
        elif key == "reports":
            self.pages.setCurrentWidget(self.reports_page)
        elif key == "inventory":
            self.pages.setCurrentWidget(self.inventory_page)
        elif key == "settings":
            self.pages.setCurrentWidget(self.settings_page)
        else:
            self.pages.setCurrentWidget(self.placeholder)
            
        print(f"Switching to {key}")
