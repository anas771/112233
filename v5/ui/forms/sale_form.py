from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                             QDateEdit, QSpinBox, QDoubleSpinBox, QPushButton, 
                             QHBoxLayout, QLabel, QComboBox, QTextEdit, QMessageBox)
from PySide6.QtCore import Qt, QDate
from v5.database.models import Batch, FarmSale

class FarmSaleForm(QDialog):
    def __init__(self, db_session, sale_id=None, batch_id=None, parent=None):
        super().__init__(parent)
        self.db = db_session
        self.sale_id = sale_id
        self.batch_id = batch_id
        
        self.setWindowTitle("إضافة مبيعات مزرعة" if not sale_id else "تعديل مبيعات مزرعة")
        self.setMinimumWidth(450)
        self.setLayoutDirection(Qt.RightToLeft)
        
        self._setup_ui()
        if sale_id:
            self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignLeft)
        form_layout.setSpacing(12)
        
        self.date_input = QDateEdit(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        
        self.customer_input = QLineEdit()
        self.customer_input.setPlaceholderText("اسم المشتري أو التاجر")
        
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(0, 100000)
        self.quantity_input.setSuffix(" طير")
        
        self.weight_input = QDoubleSpinBox()
        self.weight_input.setRange(0, 100000)
        self.weight_input.setSuffix(" كجم")
        
        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 1000)
        self.price_input.setSuffix(" ر.س / كجم")
        
        self.transport_input = QDoubleSpinBox()
        self.transport_input.setRange(0, 100000)
        self.transport_input.setSuffix(" ر.س")
        
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        
        form_layout.addRow("التاريخ:", self.date_input)
        form_layout.addRow("العميل:", self.customer_input)
        form_layout.addRow("الكمية (عدد):", self.quantity_input)
        form_layout.addRow("الوزن الإجمالي:", self.weight_input)
        form_layout.addRow("سعر الكيلو:", self.price_input)
        form_layout.addRow("تكاليف النقل:", self.transport_input)
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
            QDialog { background-color: #FDFDFD; }
            QLabel { font-weight: bold; color: #444; }
            QPushButton#successBtn {
                background-color: #2B88D9;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
            }
        """)

    def _load_data(self):
        try:
            sale = self.db.query(FarmSale).get(self.sale_id)
            if sale:
                self.date_input.setDate(QDate(sale.sale_date.year, sale.sale_date.month, sale.sale_date.day))
                self.customer_input.setText(sale.customer or "")
                self.quantity_input.setValue(sale.qty)
                self.price_input.setValue(sale.price)
                self.notes_input.setText(sale.notes or "")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def _save(self):
        try:
            if self.sale_id:
                sale = self.db.query(FarmSale).get(self.sale_id)
            else:
                sale = FarmSale(batch_id=self.batch_id)
                self.db.add(sale)
            
            sale.sale_date = self.date_input.date().toPython()
            sale.customer = self.customer_input.text().strip()
            sale.qty = self.quantity_input.value()
            sale.price = self.price_input.value()
            sale.notes = self.notes_input.toPlainText().strip()
            
            # حساب الإجمالي
            sale.total_val = sale.qty * sale.price
            
            self.db.commit()
            self.accept()
        except Exception as e:
            self.db.rollback()
            QMessageBox.critical(self, "خطأ", str(e))
