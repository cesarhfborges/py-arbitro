from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
import os

class MultiWindow(QMainWindow):
    def __init__(self, settings, on_close_callback=None):
        super().__init__()
        self.setWindowTitle("V.I.S.A.O - Espectador")
        self.resize(800, 600)
        
        self.settings = settings
        self.on_close_callback = on_close_callback
        
        # Tema Escuro
        self.setStyleSheet("""
            QWidget {
                background-color: #121212;
                color: #ffffff;
            }
        """)
        
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        self.logo_label = QLabel()
        # pyrefly: ignore [missing-attribute]
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.load_logo(self.settings.get("logo_path", ""))
        
        self.image_label = QLabel("Aguardando imagem...")
        # pyrefly: ignore [missing-attribute]
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 2px solid #2e7d32;")
        self.image_label.setMinimumSize(1, 1) # Impede que a imagem expanda a janela infinitamente
        
        layout.addWidget(self.logo_label)
        layout.addWidget(self.image_label, 1) # Expande para ocupar o espaço
        
        self._original_pixmap = None

    def load_logo(self, path):
        if path and os.path.exists(path):
            # pyrefly: ignore [missing-attribute]
            pixmap = QPixmap(path).scaledToHeight(60, Qt.SmoothTransformation)
            self.logo_label.setPixmap(pixmap)
        else:
            self.logo_label.setText("⚽ V.I.S.A.O (Live)")
            self.logo_label.setStyleSheet("color: #4caf50; font-size: 28px; font-weight: bold;")

    def update_image(self, pixmap: QPixmap):
        if not pixmap.isNull():
            self._original_pixmap = pixmap
            self._scale_and_set_image()
        else:
            self._original_pixmap = None
            self.image_label.setText("Aguardando imagem...")
            
    def _scale_and_set_image(self):
        if self._original_pixmap and not self._original_pixmap.isNull():
            scaled_pixmap = self._original_pixmap.scaled(
                self.image_label.size(), 
                # pyrefly: ignore [missing-attribute]
                Qt.KeepAspectRatio, 
                # pyrefly: ignore [missing-attribute]
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Re-escala a imagem original ao invés do pixmap já escalado
        self._scale_and_set_image()

    def closeEvent(self, event):
        # Desativa a configuração se a janela for fechada manualmente
        if self.settings:
            self.settings["multi_window_enabled"] = False
        if self.on_close_callback:
            self.on_close_callback()
        super().closeEvent(event)
