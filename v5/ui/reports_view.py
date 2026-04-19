from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QComboBox, QFrame, QMessageBox)
from PySide6.QtCore import Qt
from v5.database.models import Batch, DailyRecord, FarmSale, CostRecord
from v5.services.report_generator import ReportGenerator

class ReportsPage(QWidget):
    def __init__(self, db_session, parent=None):
        super().__init__(parent)
        self.db = db_session
        self.report_gen = ReportGenerator()
        
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
        
        self.full_report_btn = QPushButton("📄 إصدار تقرير ختامي شامل (PDF)")
        self.full_report_btn.setMinimumHeight(50)
        self.full_report_btn.clicked.connect(self._generate_full_report)
        
        self.daily_report_btn = QPushButton("📅 تقرير السجلات اليومية")
        self.daily_report_btn.clicked.connect(lambda: self._info("قيد التطوير"))
        
        self.financial_report_btn = QPushButton("💰 التقرير المالي والأرباح")
        self.financial_report_btn.clicked.connect(lambda: self._info("قيد التطوير"))
        
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
            
            # محاولة فتح الملف تلقائياً
            os.startfile(os.path.abspath(filepath))
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def _info(self, msg):
        QMessageBox.information(self, "تنبيه", msg)

import os
