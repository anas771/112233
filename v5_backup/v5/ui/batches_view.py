from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView, 
                             QFrame, QLineEdit, QMessageBox)
from PySide6.QtCore import Qt
from v5.ui.forms.batch_form import BatchForm
from v5.database.models import Batch, Warehouse
from v5.services.calculator import calculate_mortality_rate

class BatchesPage(QWidget):
    def __init__(self, db_session, parent=None):
        super().__init__(parent)
        self.db = db_session
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. شريط الأدوات (Toolbar)
        toolbar = QHBoxLayout()
        
        self.add_btn = QPushButton("+ إضافة دفعة")
        self.add_btn.setObjectName("primaryBtn")
        self.add_btn.clicked.connect(self._add_batch)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 ابحث عن رقم دفعة أو عنبر...")
        self.search_input.setFixedWidth(300)
        
        toolbar.addWidget(self.add_btn)
        toolbar.addStretch()
        toolbar.addWidget(self.search_input)
        
        self.search_input.textChanged.connect(self.refresh_data)
        
        layout.addLayout(toolbar)
        
        # 2. جدول البيانات
        self.table = QTableWidget()
        cols = ["ID", "رقم الدفعة", "العنبر", "تاريخ الدخول", "الكتاكيت", "النافق %", "FCR", "النتيجة", "إجراءات"]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        
        # ضبط تمدد الأعمدة
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        for i in range(len(cols)):
            if i in [0, 4, 5, 6]:
                header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.table)
        
        self.refresh_data()

    def refresh_data(self):
        try:
            self.table.setRowCount(0)
            search_text = self.search_input.text().strip()
            
            query = self.db.query(Batch)
            if search_text:
                query = query.join(Warehouse).filter(
                    (Batch.batch_num.contains(search_text)) | 
                    (Warehouse.name.contains(search_text))
                )
            
            batches = query.order_by(Batch.date_in.desc()).all()
            
            for row, b in enumerate(batches):
                self.table.insertRow(row)
                
                # البيانات الأساسية
                self.table.setItem(row, 0, QTableWidgetItem(str(b.id)))
                self.table.setItem(row, 1, QTableWidgetItem(b.batch_num))
                self.table.setItem(row, 2, QTableWidgetItem(b.warehouse.name if b.warehouse else "غير معروف"))
                self.table.setItem(row, 3, QTableWidgetItem(b.date_in.strftime("%Y-%m-%d")))
                self.table.setItem(row, 4, QTableWidgetItem(str(b.chicks)))
                
                # حسابات سريعة (تحتاج لسجلات يومية، هنا سنضع قيم افتراضية أو محسوبة جزئياً)
                mortality = calculate_mortality_rate(b.chicks, 0) # سيتم تطويره لجلب النافق الفعلي
                self.table.setItem(row, 5, QTableWidgetItem(f"{mortality:.2f}%"))
                self.table.setItem(row, 6, QTableWidgetItem("-")) # FCR يحتاج لمبيعات وعلف
                self.table.setItem(row, 7, QTableWidgetItem("نشط" if b.is_active else "مغلق"))
                
                # أزرار الإجراءات
                actions_layout = QHBoxLayout()
                actions_layout.setContentsMargins(0, 0, 0, 0)
                
                edit_btn = QPushButton("تعديل")
                edit_btn.clicked.connect(lambda checked, bid=b.id: self._edit_batch(bid))
                
                delete_btn = QPushButton("حذف")
                delete_btn.setObjectName("dangerBtn")
                delete_btn.clicked.connect(lambda checked, bid=b.id: self._delete_batch(bid))
                
                actions_widget = QWidget()
                actions_layout.addWidget(edit_btn)
                actions_layout.addWidget(delete_btn)
                actions_widget.setLayout(actions_layout)
                
                self.table.setCellWidget(row, 8, actions_widget)
                
        except Exception as e:
            print(f"Error refreshing batches: {e}")

    def _add_batch(self):
        form = BatchForm(self.db, parent=self)
        if form.exec():
            self.refresh_data()

    def _edit_batch(self, batch_id):
        form = BatchForm(self.db, batch_id=batch_id, parent=self)
        if form.exec():
            self.refresh_data()

    def _delete_batch(self, batch_id):
        reply = QMessageBox.question(self, "تأكيد الحذف", 
                                   "هل أنت متأكد من حذف هذه الدفعة؟ سيتم حذف كافة السجلات المرتبطة بها!",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                batch = self.db.query(Batch).filter(Batch.id == batch_id).first()
                if batch:
                    self.db.delete(batch)
                    self.db.commit()
                    self.refresh_data()
            except Exception as e:
                self.db.rollback()
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الحذف: {e}")
