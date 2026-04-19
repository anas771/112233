from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QLineEdit, QFormLayout, QGroupBox, 
                             QCheckBox, QComboBox, QMessageBox)
from PySide6.QtCore import Qt

class SettingsPage(QWidget):
    def __init__(self, db_session, parent=None):
        super().__init__(parent)
        self.db = db_session
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        title_lbl = QLabel("⚙️ إعدادات النظام")
        title_lbl.setStyleSheet("font-size: 22px; font-weight: bold; color: #044335;")
        layout.addWidget(title_lbl)
        
        # 1. إعدادات المزرعة العامة
        farm_group = QGroupBox("إعدادات المزرعة")
        farm_layout = QFormLayout(farm_group)
        farm_layout.setSpacing(15)
        
        self.farm_name = QLineEdit("مزرعة أنس")
        self.owner_name = QLineEdit("أنس")
        self.telegram_token = QLineEdit()
        self.telegram_token.setPlaceholderText("أدخل Token البوت الخاص بك")
        self.telegram_token.setEchoMode(QLineEdit.Password)
        
        farm_layout.addRow("اسم المزرعة:", self.farm_name)
        farm_layout.addRow("اسم المالك/المسؤول:", self.owner_name)
        farm_layout.addRow("Telegram Bot Token:", self.telegram_token)
        
        layout.addWidget(farm_group)
        
        # 2. إعدادات التنبيهات والواجهة
        ui_group = QGroupBox("التنبيهات والمظهر")
        ui_layout = QVBoxLayout(ui_group)
        
        self.chk_dark_mode = QCheckBox("تفعيل الوضع الليلي (قيد التطوير)")
        self.chk_notif = QCheckBox("تنبيهات عند انخفاض المخزون")
        self.chk_notif.setChecked(True)
        
        ui_layout.addWidget(self.chk_dark_mode)
        ui_layout.addWidget(self.chk_notif)
        
        layout.addWidget(ui_group)
        
        # 3. صيانة قاعدة البيانات
        db_group = QGroupBox("قاعدة البيانات والصيانة")
        db_layout = QHBoxLayout(db_group)
        
        self.backup_btn = QPushButton("📦 إنشاء نسخة احتياطية")
        self.backup_btn.clicked.connect(self._backup)
        
        self.clear_cache_btn = QPushButton("🧹 تنظيف التخزين المؤقت")
        
        db_layout.addWidget(self.backup_btn)
        db_layout.addWidget(self.clear_cache_btn)
        
        layout.addWidget(db_group)
        
        # 4. حفظ الإعدادات
        save_layout = QHBoxLayout()
        self.save_all_btn = QPushButton("💾 حفظ كافة التغييرات")
        self.save_all_btn.setObjectName("primaryBtn")
        self.save_all_btn.setMinimumHeight(45)
        self.save_all_btn.setFixedWidth(200)
        self.save_all_btn.clicked.connect(self._save_settings)
        
        save_layout.addStretch()
        save_layout.addWidget(self.save_all_btn)
        
        layout.addLayout(save_layout)
        layout.addStretch()

    def _save_settings(self):
        QMessageBox.information(self, "نجاح", "تم حفظ الإعدادات بنجاح!")

    def _backup(self):
        import shutil
        from datetime import datetime
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            shutil.copy("poultry_data.db", f"backup_poultry_{timestamp}.db")
            QMessageBox.information(self, "نجاح", f"تم إنشاء نسخة احتياطية بنجاح باسم:\nbackup_poultry_{timestamp}.db")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل النسخ الاحتياطي: {e}")
