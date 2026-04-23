from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout
from PySide6.QtCore import Qt
from v5.ui.components.cards import KPICard
from v5.database.models import Batch, DailyRecord, FarmSale, CostRecord
from sqlalchemy import func

class DashboardPage(QWidget):
    def __init__(self, db_session, parent=None):
        super().__init__(parent)
        self.db = db_session
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 1. قسم البطاقات (KPIs)
        kpi_layout = QGridLayout()
        kpi_layout.setSpacing(15)
        
        self.cards = {
            "total_batches": KPICard("إجمالي الدفعات", "0", "#0078D4"),
            "total_chicks": KPICard("إجمالي الكتاكيت", "0", "#106EBE"),
            "total_profit": KPICard("صافي الأرباح", "0", "#107C10"),
            "avg_mortality": KPICard("متوسط النافق", "0%", "#A80000"),
            "total_feed": KPICard("استهلاك العلف (طن)", "0", "#847545"),
            "total_sales": KPICard("إجمالي المبيعات", "0", "#005A9E")
        }
        
        positions = [(0,0), (0,1), (0,2), (1,0), (1,1), (1,2)]
        for (key, card), pos in zip(self.cards.items(), positions):
            kpi_layout.addWidget(card, *pos)
            
        layout.addLayout(kpi_layout)
        
        # 2. قسم الرسوم البيانية (Charts)
        charts_layout = QHBoxLayout()
        
        chart1_frame = QWidget()
        chart1_frame.setStyleSheet("background-color: #FFFFFF; border-radius: 12px; border: 1px solid #F1F5F9;")
        chart1_frame.setMinimumHeight(300)
        c1_layout = QVBoxLayout(chart1_frame)
        c1_layout.addWidget(QLabel("تحليل مؤشرات الأداء (KPIs)"))
        
        chart2_frame = QWidget()
        chart2_frame.setStyleSheet("background-color: #FFFFFF; border-radius: 12px; border: 1px solid #F1F5F9;")
        chart2_frame.setMinimumHeight(300)
        c2_layout = QVBoxLayout(chart2_frame)
        c2_layout.addWidget(QLabel("توزيع التكاليف والمصروفات"))
        
        charts_layout.addWidget(chart1_frame)
        charts_layout.addWidget(chart2_frame)
        
        layout.addLayout(charts_layout)
        layout.addStretch()
        
        # تحميل البيانات الأولية
        self.refresh_data()

    def refresh_data(self):
        try:
            # 1. عدد الدفعات
            count = self.db.query(Batch).count()
            self.cards["total_batches"].update_value(str(count))
            
            # 2. إجمالي الكتاكيت
            total_chicks = self.db.query(func.sum(Batch.chicks)).scalar() or 0
            self.cards["total_chicks"].update_value(f"{total_chicks:,}")
            
            # 3. إجمالي المبيعات
            total_sales = self.db.query(func.sum(FarmSale.total_val)).scalar() or 0
            self.cards["total_sales"].update_value(f"{total_sales:,.2f} ر.س")
            
            # 4. إجمالي المصروفات
            total_costs = self.db.query(func.sum(CostRecord.company_val)).scalar() or 0
            
            # 5. صافي الأرباح
            profit = total_sales - total_costs
            self.cards["total_profit"].update_value(f"{profit:,.2f} ر.س")
            
            # 6. متوسط النافق
            total_mortality = self.db.query(func.sum(DailyRecord.dead_count)).scalar() or 0
            mortality_pct = (total_mortality / total_chicks * 100) if total_chicks > 0 else 0
            self.cards["avg_mortality"].update_value(f"{mortality_pct:.2f}%")
            
            # 7. استهلاك العلف
            total_feed = self.db.query(func.sum(DailyRecord.feed_kg)).scalar() or 0
            self.cards["total_feed"].update_value(f"{total_feed / 1000:.2f}")
            
        except Exception as e:
            print(f"Dashboard Refresh Error: {e}")
