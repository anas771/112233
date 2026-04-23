from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView, 
                             QComboBox, QMessageBox)
from PySide6.QtCore import Qt
from v5.database.models import Batch, FarmSale
from v5.ui.forms.sale_form import FarmSaleForm

class SalesPage(QWidget):
    def __init__(self, db_session, parent=None):
        super().__init__(parent)
        self.db = db_session
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. شريط الأدوات
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("إدارة المبيعات للدفعة:"))
        
        self.batch_cb = QComboBox()
        self.batch_cb.setFixedWidth(250)
        self.batch_cb.currentIndexChanged.connect(self.refresh_data)
        top_layout.addWidget(self.batch_cb)
        
        self.add_btn = QPushButton("+ إضافة عملية بيع")
        self.add_btn.setObjectName("primaryBtn")
        self.add_btn.clicked.connect(self._add_sale)
        top_layout.addStretch()
        top_layout.addWidget(self.add_btn)
        
        layout.addLayout(top_layout)
        
        # 2. جدول المبيعات
        self.table = QTableWidget()
        cols = ["ID", "التاريخ", "العميل", "العدد", "الوزن", "السعر", "الإجمالي", "إجراءات"]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.table)
        
        self._populate_batches()

    def _populate_batches(self):
        try:
            batches = self.db.query(Batch).all()
            self.batch_cb.clear()
            for b in batches:
                self.batch_cb.addItem(f"{b.batch_num} ({b.warehouse.name})", b.id)
            
            if not batches:
                self.batch_cb.addItem("لا توجد دفعات", None)
                self.add_btn.setEnabled(False)
        except Exception as e:
            print(f"Error: {e}")

    def refresh_data(self):
        try:
            self.table.setRowCount(0)
            batch_id = self.batch_cb.currentData()
            if not batch_id: return

            sales = self.db.query(FarmSale).filter(FarmSale.batch_id == batch_id).order_by(FarmSale.sale_date.desc()).all()
            
            for row, s in enumerate(sales):
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(s.id)))
                self.table.setItem(row, 1, QTableWidgetItem(s.sale_date.strftime("%Y-%m-%d")))
                self.table.setItem(row, 2, QTableWidgetItem(s.customer or "-"))
                self.table.setItem(row, 3, QTableWidgetItem(str(s.qty)))
                self.table.setItem(row, 4, QTableWidgetItem("-")) # total_weight not in model
                self.table.setItem(row, 5, QTableWidgetItem(f"{s.price} ر.س"))
                self.table.setItem(row, 6, QTableWidgetItem(f"{s.total_val:,.2f} ر.س"))
                
                # أزرار
                btn_widget = QWidget()
                btn_layout = QHBoxLayout(btn_widget)
                btn_layout.setContentsMargins(2, 2, 2, 2)
                
                edit_btn = QPushButton("تعديل")
                edit_btn.clicked.connect(lambda checked, sid=s.id: self._edit_sale(sid))
                
                del_btn = QPushButton("حذف")
                del_btn.setObjectName("dangerBtn")
                del_btn.clicked.connect(lambda checked, sid=s.id: self._delete_sale(sid))
                
                btn_layout.addWidget(edit_btn)
                btn_layout.addWidget(del_btn)
                self.table.setCellWidget(row, 7, btn_widget)
                
        except Exception as e:
            print(f"Error: {e}")

    def _add_sale(self):
        batch_id = self.batch_cb.currentData()
        if not batch_id: return
        form = FarmSaleForm(self.db, batch_id=batch_id, parent=self)
        if form.exec():
            self.refresh_data()

    def _edit_sale(self, sale_id):
        form = FarmSaleForm(self.db, sale_id=sale_id, parent=self)
        if form.exec():
            self.refresh_data()

    def _delete_sale(self, sale_id):
        if QMessageBox.question(self, "تأكيد", "هل تريد حذف هذه العملية؟") == QMessageBox.Yes:
            try:
                sale = self.db.query(FarmSale).get(sale_id)
                self.db.delete(sale)
                self.db.commit()
                self.refresh_data()
            except Exception as e:
                self.db.rollback()
                QMessageBox.critical(self, "خطأ", str(e))
