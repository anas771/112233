from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView, 
                             QComboBox, QMessageBox)
from PySide6.QtCore import Qt
from v5.database.models import Batch, DailyRecord
from v5.ui.forms.daily_record_form import DailyRecordForm

class DailyRecordsPage(QWidget):
    def __init__(self, db_session, parent=None):
        super().__init__(parent)
        self.db = db_session
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. اختيار الدفعة
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("اختر الدفعة النشطة:"))
        
        self.batch_cb = QComboBox()
        self.batch_cb.setFixedWidth(250)
        self.batch_cb.currentIndexChanged.connect(self.refresh_data)
        selector_layout.addWidget(self.batch_cb)
        
        self.add_btn = QPushButton("+ إضافة سجل اليوم")
        self.add_btn.setObjectName("primaryBtn")
        self.add_btn.clicked.connect(self._add_record)
        selector_layout.addStretch()
        selector_layout.addWidget(self.add_btn)
        
        layout.addLayout(selector_layout)
        
        # 2. جدول السجلات
        self.table = QTableWidget()
        cols = ["ID", "التاريخ", "العمر (يوم)", "النافق", "العلف (كجم)", "الوزن (جرام)", "المياه", "ملاحظات", "إجراءات"]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.table)
        
        self._populate_batches()

    def _populate_batches(self):
        try:
            batches = self.db.query(Batch).filter(Batch.is_active == True).all()
            self.batch_cb.clear()
            for b in batches:
                self.batch_cb.addItem(f"{b.batch_num} - {b.warehouse.name}", b.id)
            
            if not batches:
                self.batch_cb.addItem("لا توجد دفعات نشطة", None)
                self.add_btn.setEnabled(False)
        except Exception as e:
            print(f"Error populating batches: {e}")

    def refresh_data(self):
        try:
            self.table.setRowCount(0)
            batch_id = self.batch_cb.currentData()
            if not batch_id:
                return

            records = self.db.query(DailyRecord).filter(DailyRecord.batch_id == batch_id).order_by(DailyRecord.rec_date.asc()).all()
            
            # جلب تاريخ بداية الدفعة لحساب العمر
            batch = self.db.query(Batch).get(batch_id)
            
            for row, r in enumerate(records):
                self.table.insertRow(row)
                
                age = (r.rec_date - batch.date_in).days + 1
                
                self.table.setItem(row, 0, QTableWidgetItem(str(r.id)))
                self.table.setItem(row, 1, QTableWidgetItem(r.rec_date.strftime("%Y-%m-%d")))
                self.table.setItem(row, 2, QTableWidgetItem(str(age)))
                self.table.setItem(row, 3, QTableWidgetItem(str(r.dead_count)))
                self.table.setItem(row, 4, QTableWidgetItem(str(r.feed_kg)))
                self.table.setItem(row, 5, QTableWidgetItem("-")) # avg_weight not in daily record
                self.table.setItem(row, 6, QTableWidgetItem(str(r.water_ltr or 0)))
                self.table.setItem(row, 7, QTableWidgetItem(r.notes or ""))
                
                # أزرار
                btn_widget = QWidget()
                btn_layout = QHBoxLayout(btn_widget)
                btn_layout.setContentsMargins(2, 2, 2, 2)
                
                edit_btn = QPushButton("تعديل")
                edit_btn.clicked.connect(lambda checked, rid=r.id: self._edit_record(rid))
                
                del_btn = QPushButton("حذف")
                del_btn.setObjectName("dangerBtn")
                del_btn.clicked.connect(lambda checked, rid=r.id: self._delete_record(rid))
                
                btn_layout.addWidget(edit_btn)
                btn_layout.addWidget(del_btn)
                self.table.setCellWidget(row, 8, btn_widget)
                
        except Exception as e:
            print(f"Error refreshing daily records: {e}")

    def _add_record(self):
        batch_id = self.batch_cb.currentData()
        if not batch_id: return
        
        form = DailyRecordForm(self.db, batch_id=batch_id, parent=self)
        if form.exec():
            self.refresh_data()

    def _edit_record(self, record_id):
        form = DailyRecordForm(self.db, record_id=record_id, parent=self)
        if form.exec():
            self.refresh_data()

    def _delete_record(self, record_id):
        reply = QMessageBox.question(self, "تأكيد", "هل أنت متأكد من حذف هذا السجل؟", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                record = self.db.query(DailyRecord).get(record_id)
                self.db.delete(record)
                self.db.commit()
                self.refresh_data()
            except Exception as e:
                self.db.rollback()
                QMessageBox.critical(self, "خطأ", str(e))
