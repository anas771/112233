from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout
from .dashboard_view import DashboardView
from .batches_view import BatchesView
from .daily_records_view import DailyRecordsView
from .sales_view import SalesView
from .management_view import ManagementView
from .reports_view import ReportsView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modern Poultry Pro v5.0")
        self.resize(1200, 800)
        
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Add tabs (placeholder widgets for missing views)
        self.tabs.addTab(DashboardView(), "🏠 لوحة التحكم")
        self.tabs.addTab(BatchesView(), "📦 الدفعات")
        self.tabs.addTab(DailyRecordsView(), "📅 السجل اليومي")
        self.tabs.addTab(SalesView(), "💰 المبيعات")
        self.tabs.addTab(ReportsView(), "📄 التقارير والتصفيات")
        self.tabs.addTab(ManagementView(), "⚙️ الإدارة")
