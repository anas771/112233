from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                             QDateEdit, QSpinBox, QDoubleSpinBox, QPushButton, 
                             QHBoxLayout, QLabel, QComboBox, QTextEdit, QMessageBox)
from PySide6.QtCore import Qt, QDate
from v5.database.models import Batch, CostRecord

class CostForm(QDialog):
    def __init__(self, db_session, cost_id=None, batch_id=None, parent=None):
        super().__init__(parent)
        self.db = db_session
        self.cost_id = cost_id
        self.batch_id = batch_id
        
        self.setWindowTitle("إضافة مصروفات" if not cost_id else "تعديل مصروفات")
        self.setMinimumWidth(450)
        self.setLayoutDirection(Qt.RightToLeft)
        
        self._setup_ui()
        if cost_id:
            self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignLeft)
        form_layout.setSpacing(12)
        
        self.date_input = QDateEdit(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        
        self.category_cb = QComboBox()
        self.category_cb.addItems(["علف", "أدوية", "لقاحات", "نشارة", "كهرباء/ماء", "عمالة", "نقل", "أخرى"])
        
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0, 1000000)
        self.amount_input.setSuffix(" ر.س")
        
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("وصف المصروف (مثلاً: فاتورة كهرباء شهر 5)")
        
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        
        form_layout.addRow("التاريخ:", self.date_input)
        form_layout.addRow("التصنيف:", self.category_cb)
        form_layout.addRow("المبلغ:", self.amount_input)
        form_layout.addRow("البيان:", self.description_input)
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
            QDialog { background-color: #FAFAFA; }
            QLabel { font-weight: bold; color: #333; }
            QPushButton#successBtn {
                background-color: #E81123;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
            }
        """)

    def _load_data(self):
        try:
            cost = self.db.query(CostRecord).get(self.cost_id)
            if cost:
                self.date_input.setDate(QDate(cost.date_recorded.year, cost.date_recorded.month, cost.date_recorded.day))
                self.category_cb.setCurrentText(cost.category)
                self.amount_input.setValue(cost.company_val)
                self.description_input.setText(cost.cost_name or "")
                self.notes_input.setText(cost.notes or "")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def _save(self):
        try:
            if self.cost_id:
                cost = self.db.query(CostRecord).get(self.cost_id)
            else:
                cost = CostRecord(batch_id=self.batch_id)
                self.db.add(cost)
            
            cost.date_recorded = self.date_input.date().toPython()
            cost.category = self.category_cb.currentText()
            cost.company_val = self.amount_input.value()
            cost.cost_name = self.description_input.text().strip()
            cost.notes = self.notes_input.toPlainText().strip()
            
            self.db.commit()
            self.accept()
        except Exception as e:
            self.db.rollback()
            QMessageBox.critical(self, "خطأ", str(e))
