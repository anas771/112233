from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QComboBox, QFrame, QMessageBox)
from PySide6.QtCore import Qt
from v5.database.models import Batch, DailyRecord, FarmSale, MarketSale, CostRecord
from v5.services.report_generator import ReportGenerator
from v5.services.nano_report_generator import NanoReportGenerator

class ReportsPage(QWidget):
    def __init__(self, db_session, parent=None):
        super().__init__(parent)
        self.db = db_session
        self.report_gen = ReportGenerator()
        self.nano_gen = NanoReportGenerator()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. اختيار الدفعة
        selector_layout = QVBoxLayout()
        selector_layout.addWidget(QLabel("اختر الدفعة لإصدار تقرير عنها:"))
        
        self.batch_cb = QComboBox()
        self.batch_cb.setFixedWidth(300)
        selector_layout.addWidget(self.batch_cb)
        
        layout.addLayout(selector_layout)
        layout.addSpacing(20)
        
        # 2. خيارات التقارير
        options_frame = QFrame()
        options_frame.setFrameShape(QFrame.StyledPanel)
        options_layout = QVBoxLayout(options_frame)
        
        self.nano_report_btn = QPushButton("🍌 إصدار تقرير نانو الفاخر (Nanobanana Style)")
        self.nano_report_btn.setObjectName("premiumBtn")
        self.nano_report_btn.setMinimumHeight(60)
        self.nano_report_btn.clicked.connect(self._generate_nano_report)
        
        self.full_report_btn = QPushButton("📄 تقرير ختامي بسيط (PDF)")
        self.full_report_btn.clicked.connect(self._generate_full_report)
        
        self.daily_report_btn = QPushButton("📅 تقرير السجلات اليومية")
        self.daily_report_btn.clicked.connect(self._generate_daily_report)
        
        self.financial_report_btn = QPushButton("💰 التقرير المالي والأرباح")
        self.financial_report_btn.clicked.connect(self._generate_financial_report)
        
        options_layout.addWidget(self.nano_report_btn)
        options_layout.addWidget(self.full_report_btn)
        options_layout.addWidget(self.daily_report_btn)
        options_layout.addWidget(self.financial_report_btn)
        
        layout.addWidget(options_frame)
        layout.addStretch()
        
        self._populate_batches()

    def _populate_batches(self):
        try:
            batches = self.db.query(Batch).all()
            for b in batches:
                self.batch_cb.addItem(f"{b.batch_num} - {b.warehouse.name}", b.id)
        except Exception as e:
            print(f"Error: {e}")

    def _generate_nano_report(self):
        batch_id = self.batch_cb.currentData()
        if not batch_id: return
        
        try:
            batch = self.db.query(Batch).get(batch_id)
            if not batch: return
            
            # تحديث الإحصائيات قبل التقرير
            from v5.services.calculator import PoultryCalculator
            batch = PoultryCalculator.calculate_batch_stats(batch)
            
            daily = self.db.query(DailyRecord).filter(DailyRecord.batch_id == batch_id).order_by(DailyRecord.day_num).all()
            sales = self.db.query(FarmSale).filter(FarmSale.batch_id == batch_id).all()
            costs = self.db.query(CostRecord).filter(CostRecord.batch_id == batch_id).all()
            
            filepath = self.nano_gen.generate_nano_report(batch, daily, sales, costs)
            QMessageBox.information(self, "نجاح", f"تم إنشاء تقرير نانو بنجاح:\n{filepath}")
            os.startfile(os.path.abspath(filepath))
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل إصدار تقرير نانو: {str(e)}")

    def _generate_daily_report(self):
        batch_id = self.batch_cb.currentData()
        if not batch_id: return
        try:
            batch = self.db.query(Batch).get(batch_id)
            daily = self.db.query(DailyRecord).filter(DailyRecord.batch_id == batch_id).order_by(DailyRecord.day_num).all()
            filepath = self.nano_gen.generate_daily_report(batch, daily)
            QMessageBox.information(self, "نجاح", f"تم إنشاء تقرير السجلات اليومية:\n{filepath}")
            os.startfile(os.path.abspath(filepath))
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def _generate_financial_report(self):
        batch_id = self.batch_cb.currentData()
        if not batch_id: return
        try:
            batch = self.db.query(Batch).get(batch_id)
            sales = self.db.query(FarmSale).filter(FarmSale.batch_id == batch_id).all()
            market = self.db.query(MarketSale).filter(MarketSale.batch_id == batch_id).all()
            costs = self.db.query(CostRecord).filter(CostRecord.batch_id == batch_id).all()
            
            filepath = self.nano_gen.generate_financial_report(batch, sales, market, costs)
            QMessageBox.information(self, "نجاح", f"تم إنشاء التقرير المالي بنجاح:\n{filepath}")
            os.startfile(os.path.abspath(filepath))
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل إصدار التقرير المالي: {str(e)}")

    def _generate_full_report(self):
        batch_id = self.batch_cb.currentData()
        if not batch_id: return
        
        try:
            batch = self.db.query(Batch).get(batch_id)
            daily = self.db.query(DailyRecord).filter(DailyRecord.batch_id == batch_id).all()
            sales = self.db.query(FarmSale).filter(FarmSale.batch_id == batch_id).all()
            costs = self.db.query(CostRecord).filter(CostRecord.batch_id == batch_id).all()
            
            filepath = self.report_gen.generate_batch_report(batch, daily, sales, costs)
            QMessageBox.information(self, "نجاح", f"تم إنشاء التقرير بنجاح في:\n{filepath}")
            os.startfile(os.path.abspath(filepath))
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def _info(self, msg):
        QMessageBox.information(self, "تنبيه", msg)

import os
