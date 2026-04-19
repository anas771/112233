from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
                             QComboBox, QFrame, QScrollArea, QGridLayout, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from .styles import DesignTokens
from ..database import get_session
from ..models import Batch, BatchCost, BatchRevenue
from ..services.batch_service import BatchService
import pandas as pd
from fpdf import FPDF
import os

class ReportsView(QWidget):
    def __init__(self):
        super().__init__()
        self.service = BatchService()
        self.current_report_data = None
        self.setup_ui()
        self.load_batches()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(25)

        # Header Area
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(30, 20, 30, 0)
        
        title_container = QVBoxLayout()
        title = QLabel("📄 مركز التقارير والتصفيات")
        title.setStyleSheet(f"font-size: 26px; font-weight: bold; color: {DesignTokens.PRIMARY};")
        subtitle = QLabel("إصدار تقارير التصفية النهائية، التحليل المالي، والأداء الفني")
        subtitle.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 14px;")
        title_container.addWidget(title)
        title_container.addWidget(subtitle)
        header_layout.addLayout(title_container)
        
        header_layout.addStretch()
        
        lbl_batch = QLabel("اختر الدفعة للتصفية:")
        lbl_batch.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-weight: 500;")
        header_layout.addWidget(lbl_batch)
        
        self.batch_selector = QComboBox()
        self.batch_selector.setFixedWidth(300)
        header_layout.addWidget(self.batch_selector)
        
        btn_generate = QPushButton("🔍 عرض المعاينة")
        btn_generate.setObjectName("PrimaryButton")
        btn_generate.setFixedWidth(180)
        btn_generate.clicked.connect(self.generate_preview)
        header_layout.addWidget(btn_generate)
        
        layout.addWidget(header_widget)

        # Preview Area
        preview_container = QWidget()
        preview_container_layout = QVBoxLayout(preview_container)
        preview_container_layout.setContentsMargins(30, 0, 30, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet(f"background-color: {DesignTokens.BG_DARK}; border-radius: 12px; border: 1px solid {DesignTokens.BORDER};")
        
        self.preview_content = QWidget()
        self.preview_content.setStyleSheet("background: transparent;")
        self.preview_layout = QVBoxLayout(self.preview_content)
        self.preview_layout.setAlignment(Qt.AlignTop)
        self.preview_layout.setContentsMargins(30, 30, 30, 30)
        self.preview_layout.setSpacing(20)
        
        # Welcome placeholder
        self.placeholder = QLabel("يرجى اختيار دفعة والضغط على 'عرض المعاينة' لإظهار تصفية الحساب")
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 16px; margin-top: 150px;")
        self.preview_layout.addWidget(self.placeholder)
        
        self.scroll.setWidget(self.preview_content)
        preview_container_layout.addWidget(self.scroll)
        layout.addWidget(preview_container)

        # Bottom Actions
        actions_container = QWidget()
        actions = QHBoxLayout(actions_container)
        actions.setContentsMargins(30, 0, 30, 30)

        self.btn_excel = QPushButton("📊 تصدير ملف Excel احترافي")
        self.btn_excel.setObjectName("NavButton")
        self.btn_excel.setEnabled(False)
        self.btn_excel.setFixedWidth(250)
        self.btn_excel.setStyleSheet(f"color: {DesignTokens.PRIMARY}; border: 1px solid {DesignTokens.PRIMARY}44;")
        self.btn_excel.clicked.connect(self.export_excel)
        
        self.btn_pdf = QPushButton("📥 تصدير تقرير PDF")
        self.btn_pdf.setObjectName("PrimaryButton")
        self.btn_pdf.setEnabled(False)
        self.btn_pdf.setFixedWidth(250)
        self.btn_pdf.clicked.connect(self.export_pdf)
        
        actions.addStretch()
        actions.addWidget(self.btn_excel)
        actions.addWidget(self.btn_pdf)
        layout.addWidget(actions_container)

    def load_batches(self):
        self.batch_selector.blockSignals(True)
        self.batch_selector.clear()
        with get_session() as session:
            batches = session.query(Batch).all()
            for b in batches:
                self.batch_selector.addItem(f"دفعة {b.batch_num} - {b.warehouse.name}", b.id)
        self.batch_selector.blockSignals(False)

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clear_layout(item.layout())

    def generate_preview(self):
        try:
            batch_id = self.batch_selector.currentData()
            if not batch_id: return
            
            self.current_report_data = self.service.get_financial_summary(batch_id)
            if not self.current_report_data:
                QMessageBox.warning(self, "تنبيه", "فشل في استرجاع بيانات التصفية.")
                return
            
            for i in reversed(range(self.preview_layout.count())): 
                item = self.preview_layout.itemAt(i)
                if item and item.widget():
                    item.widget().setParent(None)
                elif item and item.layout():
                    self.clear_layout(item.layout())
                
            self.btn_pdf.setEnabled(True)
            self.btn_excel.setEnabled(True)
            
            data = self.current_report_data
            
            report_header = QLabel(f"تقرير تصفية الدفعة رقم: {data.get('batch_num', 'N/A')}")
            report_header.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {DesignTokens.ACCENT}; margin-bottom: 20px;")
            self.preview_layout.addWidget(report_header)
            
            stats_grid = QGridLayout()
            stats = [
                ("عدد الكتاكيت", f"{data.get('chicks', 0):,}", "🐥"),
                ("إجمالي النافق", f"{data.get('total_dead', 0):,}", "📉"),
                ("نسبة النافق", f"{data.get('mort_rate', 0):.2f}%", "📊"),
                ("إجمالي الوزن المباع", f"{data.get('total_weight', 0):,.2f} كجم", "⚖️"),
                ("متوسط السعر", f"{data.get('avg_price', 0):,.2f}", "💵"),
                ("معامل التحويل FCR", f"{data.get('fcr', 0):.2f}", "⚖️"),
                ("إجمالي التكاليف", f"{data.get('total_cost', 0):,.2f}", "💰"),
                ("صافي الربح", f"{data.get('net_result', 0):,.2f}", "🏆")
            ]
            for i, (label, val, icon) in enumerate(stats):
                card = QFrame()
                card.setStyleSheet(f"background-color: {DesignTokens.BG_CARD}; border: 1px solid {DesignTokens.BORDER}; padding: 15px;")
                l = QVBoxLayout(card)
                l.addWidget(QLabel(f"{icon} {label}"))
                v = QLabel(val)
                v.setStyleSheet("font-size: 22px; font-weight: 800;")
                l.addWidget(v)
                stats_grid.addWidget(card, i // 4, i % 4)
            self.preview_layout.addLayout(stats_grid)
            
            # Detailed Tables (Costs & Revenues)
            self.add_section_title("💰 تفاصيل التكاليف التشغيلية:")
            self.costs_table = self.create_styled_table(["البند", "الكمية", "القيمة"])
            self.costs_table.setRowCount(len(data.get('costs', [])))
            for i, c in enumerate(data.get('costs', [])):
                self.costs_table.setItem(i, 0, QTableWidgetItem(c['type']))
                qty_str = f"{c['qty']:,.1f}" if c.get('qty') is not None else "---"
                self.costs_table.setItem(i, 1, QTableWidgetItem(qty_str))
                self.costs_table.setItem(i, 2, QTableWidgetItem(f"{c['amount']:,.2f}"))
            self.costs_table.setFixedHeight(min(400, (len(data.get('costs', [])) * 35) + 40))
            self.preview_layout.addWidget(self.costs_table)

            self.add_section_title("💹 تفاصيل الإيرادات والمبيعات:")
            self.rev_table = self.create_styled_table(["نوع الإيراد", "الكمية", "القيمة"])
            self.rev_table.setRowCount(len(data.get('revenues', [])))
            for i, r in enumerate(data.get('revenues', [])):
                self.rev_table.setItem(i, 0, QTableWidgetItem(r['type']))
                self.rev_table.setItem(i, 1, QTableWidgetItem(f"{r['qty']:,}"))
                self.rev_table.setItem(i, 2, QTableWidgetItem(f"{r['amount']:,.2f}"))
            self.rev_table.setFixedHeight(min(400, (len(data.get('revenues', [])) * 35) + 40))
            self.preview_layout.addWidget(self.rev_table)

            self.preview_layout.addStretch()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def add_section_title(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {DesignTokens.PRIMARY}; margin-top: 25px;")
        self.preview_layout.addWidget(lbl)

    def create_styled_table(self, headers):
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setStyleSheet(f"QTableWidget {{ background-color: {DesignTokens.BG_CARD}; border-radius: 8px; }}")
        return table

    def export_excel(self): pass
    def export_pdf(self): pass
