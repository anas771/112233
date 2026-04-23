from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                             QDateEdit, QSpinBox, QDoubleSpinBox, QPushButton, 
                             QHBoxLayout, QLabel, QComboBox, QTextEdit, QMessageBox)
from PySide6.QtCore import Qt, QDate
from v5.database.models import Batch, Warehouse

class BatchForm(QDialog):
    def __init__(self, db_session, batch_id=None, parent=None):
        super().__init__(parent)
        self.db = db_session
        self.batch_id = batch_id
        
        self.setWindowTitle("إضافة دفعة جديدة" if not batch_id else "تعديل دفعة")
        self.setMinimumWidth(500)
        self.setLayoutDirection(Qt.RightToLeft)
        
        self._setup_ui()
        if batch_id:
            self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignLeft)
        form_layout.setSpacing(15)
        
        # الحقول
        self.warehouse_cb = QComboBox()
        self._populate_warehouses()
        
        self.batch_num_input = QLineEdit()
        self.date_in_input = QDateEdit(QDate.currentDate())
        self.date_in_input.setCalendarPopup(True)
        
        self.chicks_input = QSpinBox()
        self.chicks_input.setRange(0, 100000)
        self.chicks_input.setSingleStep(100)
        
        self.chick_price_input = QDoubleSpinBox()
        self.chick_price_input.setRange(0, 1000)
        self.chick_price_input.setDecimals(2)
        
        self.partner_input = QLineEdit()
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        
        # إضافة الحقول للمخطط
        form_layout.addRow("العنبر:", self.warehouse_cb)
        form_layout.addRow("رقم الدفعة:", self.batch_num_input)
        form_layout.addRow("تاريخ الدخول:", self.date_in_input)
        form_layout.addRow("عدد الكتاكيت:", self.chicks_input)
        form_layout.addRow("سعر الكتكوت:", self.chick_price_input)
        form_layout.addRow("اسم الشريك:", self.partner_input)
        form_layout.addRow("ملاحظات:", self.notes_input)
        
        layout.addLayout(form_layout)
        
        # أزرار التحكم
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
        
        # تطبيق التنسيق (يمكن وراثته من MainWindow أو تطبيقه هنا)
        self.setStyleSheet("""
            QDialog { background-color: white; }
            QLabel { font-weight: bold; color: #323130; }
            QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QTextEdit {
                padding: 8px;
                border: 1px solid #EDEBE9;
                border-radius: 4px;
            }
            QPushButton#successBtn {
                background-color: #107C10;
                color: white;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)

    def _populate_warehouses(self):
        try:
            warehouses = self.db.query(Warehouse).all()
            for w in warehouses:
                self.warehouse_cb.addItem(w.name, w.id)
            if not warehouses:
                self.warehouse_cb.addItem("لا يوجد عنابر مسجلة", None)
        except Exception as e:
            print(f"Error populating warehouses: {e}")

    def _load_data(self):
        try:
            batch = self.db.query(Batch).filter(Batch.id == self.batch_id).first()
            if batch:
                self.batch_num_input.setText(batch.batch_num)
                self.date_in_input.setDate(QDate(batch.date_in.year, batch.date_in.month, batch.date_in.day))
                self.chicks_input.setValue(batch.chicks)
                self.chick_price_input.setValue(batch.chick_price)
                self.partner_input.setText(batch.partner_name or "")
                self.notes_input.setText(batch.notes or "")
                
                # اختيار العنبر الصحيح
                index = self.warehouse_cb.findData(batch.warehouse_id)
                if index >= 0:
                    self.warehouse_cb.setCurrentIndex(index)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تحميل البيانات: {e}")

    def _save(self):
        try:
            warehouse_id = self.warehouse_cb.currentData()
            if warehouse_id is None:
                QMessageBox.warning(self, "تنبيه", "يرجى اختيار العنبر أولاً")
                return

            batch_num = self.batch_num_input.text().strip()
            if not batch_num:
                QMessageBox.warning(self, "تنبيه", "يرجى إدخال رقم الدفعة")
                return

            if self.batch_id:
                batch = self.db.query(Batch).filter(Batch.id == self.batch_id).first()
            else:
                batch = Batch()
                self.db.add(batch)

            batch.warehouse_id = warehouse_id
            batch.batch_num = batch_num
            qdate = self.date_in_input.date()
            batch.date_in = qdate.toPython()
            batch.chicks = self.chicks_input.value()
            batch.chick_price = self.chick_price_input.value()
            batch.partner_name = self.partner_input.text().strip()
            batch.notes = self.notes_input.toPlainText().strip()
            batch.is_active = True

            self.db.commit()
            self.accept()
        except Exception as e:
            self.db.rollback()
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الحفظ: {e}")
