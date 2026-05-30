import os
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSpacerItem, QSizePolicy
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

class TopBar(QWidget):
    def __init__(self, settings):
        super().__init__()
        self.setFixedHeight(60)
        self.setStyleSheet("background-color: #1e1e1e; border: none; border-bottom: 2px solid #2e7d32;")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 5, 20, 5)
        
        self.logo_label = QLabel()
        self.load_logo(settings.get("logo_path", ""))
        layout.addWidget(self.logo_label)
        
        # Se houver um logo em imagem, adicionamos o título textual ao lado dele
        if settings.get("logo_path", "") and os.path.exists(settings.get("logo_path", "")):
            title = QLabel("V.I.S.A.O - Verificação de Impedimento por Sistema de Análise Óptica.")
            title.setStyleSheet("color: white; font-size: 18px; font-weight: bold; margin-left: 10px;")
            layout.addWidget(title)
            
        layout.addStretch()
        
    def load_logo(self, path):
        if path and os.path.exists(path):
            # pyrefly: ignore [missing-attribute]
            pixmap = QPixmap(path).scaledToHeight(40, Qt.SmoothTransformation)
            self.logo_label.setPixmap(pixmap)
        else:
            self.logo_label.setText("⚽ V.I.S.A.O - Verificação de Impedimento por Sistema de Análise Óptica.")
            self.logo_label.setStyleSheet("color: #4caf50; font-size: 18px; font-weight: bold;")
