from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                             QDateEdit, QSpinBox, QDoubleSpinBox, QPushButton, 
                             QHBoxLayout, QLabel, QComboBox, QTextEdit, QMessageBox)
from PySide6.QtCore import Qt, QDate
from v5.database.models import Batch, DailyRecord

class DailyRecordForm(QDialog):
    def __init__(self, db_session, record_id=None, batch_id=None, parent=None):
        super().__init__(parent)
        self.db = db_session
        self.record_id = record_id
        self.batch_id = batch_id
        
        self.setWindowTitle("إضافة سجل يومي" if not record_id else "تعديل سجل يومي")
        self.setMinimumWidth(450)
        self.setLayoutDirection(Qt.RightToLeft)
        
        self._setup_ui()
        if record_id:
            self._load_data()
        elif batch_id:
            self._prepare_new_record()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignLeft)
        form_layout.setSpacing(12)
        
        self.date_input = QDateEdit(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        
        self.mortality_input = QSpinBox()
        self.mortality_input.setRange(0, 5000)
        
        self.feed_input = QDoubleSpinBox()
        self.feed_input.setRange(0, 10000)
        self.feed_input.setSuffix(" كجم")
        
        self.weight_input = QDoubleSpinBox()
        self.weight_input.setRange(0, 10000)
        self.weight_input.setSuffix(" جرام")
        
        self.water_input = QDoubleSpinBox()
        self.water_input.setRange(0, 50000)
        self.water_input.setSuffix(" لتر")
        
        self.temp_min_input = QDoubleSpinBox()
        self.temp_min_input.setRange(-20, 60)
        
        self.temp_max_input = QDoubleSpinBox()
        self.temp_max_input.setRange(-20, 60)
        
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        
        form_layout.addRow("التاريخ:", self.date_input)
        form_layout.addRow("النافق (عدد):", self.mortality_input)
        form_layout.addRow("العلف المستهلك:", self.feed_input)
        form_layout.addRow("متوسط الوزن:", self.weight_input)
        form_layout.addRow("استهلاك المياه:", self.water_input)
        form_layout.addRow("الحرارة الصغرى:", self.temp_min_input)
        form_layout.addRow("الحرارة العظمى:", self.temp_max_input)
        form_layout.addRow("ملاحظات:", self.notes_input)
        
        layout.addLayout(form_layout)
        
        # الأزرار
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("💾 حفظ")
        self.save_btn.setObjectName("successBtn")
        self.save_btn.clicked.connect(self._save)
        
        self.cancel_btn = QPushButton("إلغاء")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)
        
        self.setStyleSheet("""
            QDialog { background-color: #F8F9FA; }
            QLabel { font-weight: bold; }
            QPushButton#successBtn {
                background-color: #107C10;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
            }
        """)

    def _prepare_new_record(self):
        # يمكن هنا جلب تاريخ آخر سجل وإضافة يوم واحد تلقائياً
        pass

    def _load_data(self):
        try:
            record = self.db.query(DailyRecord).filter(DailyRecord.id == self.record_id).first()
            if record:
                self.date_input.setDate(QDate(record.rec_date.year, record.rec_date.month, record.rec_date.day))
                self.mortality_input.setValue(record.dead_count)
                self.feed_input.setValue(record.feed_kg)
                self.water_input.setValue(record.water_ltr or 0)
                self.temp_max_input.setValue(record.temperature or 0)
                self.notes_input.setText(record.notes or "")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تحميل السجل: {e}")

    def _save(self):
        try:
            if self.record_id:
                record = self.db.query(DailyRecord).filter(DailyRecord.id == self.record_id).first()
            else:
                record = DailyRecord(batch_id=self.batch_id)
                self.db.add(record)
            
            record.rec_date = self.date_input.date().toPython()
            record.dead_count = self.mortality_input.value()
            record.feed_kg = self.feed_input.value()
            record.water_ltr = self.water_input.value()
            record.temperature = self.temp_max_input.value()
            record.notes = self.notes_input.toPlainText().strip()
            
            self.db.commit()
            self.accept()
        except Exception as e:
            self.db.rollback()
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الحفظ: {e}")
