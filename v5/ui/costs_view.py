from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView, 
                             QComboBox, QMessageBox)
from PySide6.QtCore import Qt
from v5.database.models import Batch, CostRecord
from v5.ui.forms.cost_form import CostForm

class CostsPage(QWidget):
    def __init__(self, db_session, parent=None):
        super().__init__(parent)
        self.db = db_session
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. شريط الأدوات
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("إدارة التكاليف للدفعة:"))
        
        self.batch_cb = QComboBox()
        self.batch_cb.setFixedWidth(250)
        self.batch_cb.currentIndexChanged.connect(self.refresh_data)
        top_layout.addWidget(self.batch_cb)
        
        self.add_btn = QPushButton("+ إضافة مصروف")
        self.add_btn.setObjectName("primaryBtn")
        self.add_btn.clicked.connect(self._add_cost)
        top_layout.addStretch()
        top_layout.addWidget(self.add_btn)
        
        layout.addLayout(top_layout)
        
        # 2. جدول التكاليف
        self.table = QTableWidget()
        cols = ["ID", "التاريخ", "التصنيف", "المبلغ", "البيان", "إجراءات"]
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

            costs = self.db.query(CostRecord).filter(CostRecord.batch_id == batch_id).order_by(CostRecord.date_recorded.desc()).all()
            
            for row, c in enumerate(costs):
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(c.id)))
                self.table.setItem(row, 1, QTableWidgetItem(c.date_recorded.strftime("%Y-%m-%d")))
                self.table.setItem(row, 2, QTableWidgetItem(c.category))
                self.table.setItem(row, 3, QTableWidgetItem(f"{c.company_val:,.2f} ر.س"))
                self.table.setItem(row, 4, QTableWidgetItem(c.notes or "-"))
                
                # أزرار
                btn_widget = QWidget()
                btn_layout = QHBoxLayout(btn_widget)
                btn_layout.setContentsMargins(2, 2, 2, 2)
                
                edit_btn = QPushButton("تعديل")
                edit_btn.clicked.connect(lambda checked, cid=c.id: self._edit_cost(cid))
                
                del_btn = QPushButton("حذف")
                del_btn.setObjectName("dangerBtn")
                del_btn.clicked.connect(lambda checked, cid=c.id: self._delete_cost(cid))
                
                btn_layout.addWidget(edit_btn)
                btn_layout.addWidget(del_btn)
                self.table.setCellWidget(row, 5, btn_widget)
                
        except Exception as e:
            print(f"Error: {e}")

    def _add_cost(self):
        batch_id = self.batch_cb.currentData()
        if not batch_id: return
        form = CostForm(self.db, batch_id=batch_id, parent=self)
        if form.exec():
            self.refresh_data()

    def _edit_cost(self, cost_id):
        form = CostForm(self.db, cost_id=cost_id, parent=self)
        if form.exec():
            self.refresh_data()

    def _delete_cost(self, cost_id):
        if QMessageBox.question(self, "تأكيد", "هل تريد حذف هذا المصروف؟") == QMessageBox.Yes:
            try:
                cost = self.db.query(CostRecord).get(cost_id)
                self.db.delete(cost)
                self.db.commit()
                self.refresh_data()
            except Exception as e:
                self.db.rollback()
                QMessageBox.critical(self, "خطأ", str(e))
