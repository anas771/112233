from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView, 
                             QFrame, QLineEdit, QComboBox, QMessageBox)
from PySide6.QtCore import Qt
from v5.database.models import Warehouse

class InventoryPage(QWidget):
    def __init__(self, db_session, parent=None):
        super().__init__(parent)
        self.db = db_session
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. Header Area
        header_layout = QHBoxLayout()
        title_lbl = QLabel("📦 إدارة المخازن والموارد")
        title_lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #044335;")
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("بحث في الموارد...")
        self.search_input.setFixedWidth(250)
        
        self.add_btn = QPushButton("➕ إضافة مورد جديد")
        self.add_btn.setObjectName("primaryBtn")
        self.add_btn.clicked.connect(self._add_item)
        
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        header_layout.addWidget(self.search_input)
        header_layout.addWidget(self.add_btn)
        
        layout.addLayout(header_layout)
        layout.addSpacing(15)
        
        # 2. Stats Summary (Quick View)
        stats_layout = QHBoxLayout()
        self.feed_stat = self._create_stat_box("إجمالي العلف المتوفر", "0 طن", "#059669")
        self.med_stat = self._create_stat_box("الأدوية واللقاحات", "12 صنف", "#F59E0B")
        self.alert_stat = self._create_stat_box("تنبيهات انخفاض المخزون", "0", "#EF4444")
        
        stats_layout.addWidget(self.feed_stat)
        stats_layout.addWidget(self.med_stat)
        stats_layout.addWidget(self.alert_stat)
        
        layout.addLayout(stats_layout)
        layout.addSpacing(20)
        
        # 3. Main Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "اسم المورد", "التصنيف", "الكمية الحالية", "وحدة القياس", "الإجراءات"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        
        layout.addWidget(self.table)
        
        self.refresh_data()

    def _create_stat_box(self, title, value, color):
        frame = QFrame()
        frame.setStyleSheet(f"""
            background-color: white; 
            border-radius: 10px; 
            border: 1px solid #E2E8F0;
            border-bottom: 3px solid {color};
        """)
        layout = QVBoxLayout(frame)
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #64748B; font-size: 12px;")
        
        value_lbl = QLabel(value)
        value_lbl.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: bold;")
        
        layout.addWidget(title_lbl)
        layout.addWidget(value_lbl)
        return frame

    def refresh_data(self):
        # سيتم جلب البيانات من جدول الموارد (يحتاج لجدول في models.py)
        # حالياً سنعرض العنابر كمخازن مؤقتة
        try:
            self.table.setRowCount(0)
            warehouses = self.db.query(Warehouse).all()
            
            for row, w in enumerate(warehouses):
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(w.id)))
                self.table.setItem(row, 1, QTableWidgetItem(w.name))
                self.table.setItem(row, 2, QTableWidgetItem("مخزن/عنبر"))
                self.table.setItem(row, 3, QTableWidgetItem(str(w.capacity)))
                self.table.setItem(row, 4, QTableWidgetItem("طير"))
                
                # أزرار الإجراءات
                btn = QPushButton("تعديل")
                btn.setStyleSheet("background-color: #F1F5F9; color: #475569; border-radius: 4px; padding: 4px;")
                self.table.setCellWidget(row, 5, btn)
        except Exception as e:
            print(f"Inventory Error: {e}")

    def _add_item(self):
        QMessageBox.information(self, "تنبيه", "هذه الميزة قيد التطوير النهائي")
