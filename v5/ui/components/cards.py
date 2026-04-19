from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

class KPICard(QFrame):
    def __init__(self, title, value, color="#0078D4", parent=None):
        super().__init__(parent)
        self.setProperty("class", "KPICard")
        
        layout = QVBoxLayout(self)
        
        self.title_lbl = QLabel(title)
        self.title_lbl.setProperty("class", "KPILabel")
        self.title_lbl.setAlignment(Qt.AlignRight)
        
        self.value_lbl = QLabel(str(value))
        self.value_lbl.setProperty("class", "KPIValue")
        self.value_lbl.setAlignment(Qt.AlignRight)
        
        layout.addWidget(self.title_lbl)
        layout.addWidget(self.value_lbl)

    def update_value(self, value):
        self.value_lbl.setText(str(value))
