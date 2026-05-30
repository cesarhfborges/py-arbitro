from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from visao.models.app_state import AppState
from visao.views.main_window import MainWindow
from visao.views.multi_window import MultiWindow

class MainController:
    def __init__(self, app: QApplication):
        self.app = app
        self.state = AppState()
        self.main_window = MainWindow(self.state, self)
        self.multi_window = None
        
        self.apply_theme()
        self.setup_multi_window()

    def start(self):
        # Exibe a janela primeiro para garantir que o SO a registre corretamente
        self.main_window.show()
        # Maximiza e foca a janela principal
        self.main_window.showMaximized()
        self.main_window.raise_()
        self.main_window.activateWindow()
        
        # Se houver uma janela secundária, aguarda 700ms para o SO renderizar a principal antes de abrir
        if self.multi_window:
            QTimer.singleShot(700, self.show_secondary_window)

    def show_secondary_window(self):
        if self.multi_window:
            self.multi_window.showMaximized()
            # Garante que a principal permaneça perfeitamente maximizada e com foco ativo
            self.main_window.showMaximized()
            self.main_window.raise_()
            self.main_window.activateWindow()

    def setup_multi_window(self):
        screens = self.app.screens()
        if len(screens) > 1 and self.state.settings.get("multi_window_enabled", True):
            self.multi_window = MultiWindow(self.state.settings, self.on_multi_window_closed)
            # Mover a janela para o segundo monitor ANTES de maximizar ou exibir
            screen = screens[1]
            self.multi_window.move(screen.geometry().topLeft())
            
    def on_multi_window_closed(self):
        self.multi_window = None
        self.state.settings["multi_window_enabled"] = False
        self.state.save_settings()
        self.main_window.multi_win_action.setChecked(False)
            
    def update_spectator_view(self, pixmap):
        if self.multi_window:
            self.multi_window.update_image(pixmap)

    def apply_theme(self):
        theme = self.state.settings.get("theme", "auto")
        import darkdetect
        
        is_dark = False
        if theme == "auto":
            is_dark = darkdetect.isDark()
        elif theme == "dark":
            is_dark = True
            
        if is_dark:
            # Tema Escuro Simples
            self.app.setStyleSheet("""
                QWidget {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #2e7d32; /* Verde futebol */
                    color: white;
                    border: none;
                    padding: 8px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #1b5e20;
                }
                QMenuBar {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    border: none;
                    font-size: 13px;
                    font-weight: bold;
                    padding: 4px 10px;
                }
                QMenuBar::item {
                    background-color: transparent;
                    padding: 6px 12px;
                    margin: 0px 2px;
                    border-radius: 4px;
                    color: #ffffff;
                }
                QMenuBar::item:selected {
                    background-color: #2e7d32;
                    color: #ffffff;
                }
                QMenu {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    border: 1px solid #2e7d32;
                }
                QMenu::item:selected {
                    background-color: #2e7d32;
                    color: #ffffff;
                }
                QRadioButton {
                    spacing: 8px;
                    font-size: 13px;
                    font-weight: bold;
                    color: #ffffff;
                }
                QRadioButton:checked {
                    color: #2e7d32;
                }
                QRadioButton::indicator {
                    width: 16px;
                    height: 16px;
                    border-radius: 9px;
                    border: 2px solid #888888;
                    background-color: transparent;
                }
                QRadioButton::indicator:hover {
                    border: 2px solid #2e7d32;
                }
                QRadioButton::indicator:checked {
                    border: 2px solid #2e7d32;
                    background-color: qradialgradient(cx:0.5, cy:0.5, fx:0.5, fy:0.5, radius:0.3, stop:0 #ffffff, stop:0.3 #ffffff, stop:0.35 #2e7d32, stop:1 #2e7d32);
                }
            """)
        else:
            # Tema Claro
            self.app.setStyleSheet("""
                QWidget {
                    background-color: #f5f5f5;
                    color: #333333;
                }
                QPushButton {
                    background-color: #4caf50; /* Verde futebol */
                    color: white;
                    border: none;
                    padding: 8px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #388e3c;
                }
                QMenuBar {
                    background-color: #e0e0e0;
                    color: #333333;
                    border: none;
                    font-size: 13px;
                    font-weight: bold;
                    padding: 4px 10px;
                }
                QMenuBar::item {
                    background-color: transparent;
                    padding: 6px 12px;
                    margin: 0px 2px;
                    border-radius: 4px;
                    color: #333333;
                }
                QMenuBar::item:selected {
                    background-color: #4caf50;
                    color: #ffffff;
                }
                QMenu {
                    background-color: #f5f5f5;
                    color: #333333;
                    border: 1px solid #4caf50;
                }
                QMenu::item:selected {
                    background-color: #4caf50;
                    color: #ffffff;
                }
                QRadioButton {
                    spacing: 8px;
                    font-size: 13px;
                    font-weight: bold;
                    color: #333333;
                }
                QRadioButton:checked {
                    color: #4caf50;
                }
                QRadioButton::indicator {
                    width: 16px;
                    height: 16px;
                    border-radius: 9px;
                    border: 2px solid #666666;
                    background-color: transparent;
                }
                QRadioButton::indicator:hover {
                    border: 2px solid #4caf50;
                }
                QRadioButton::indicator:checked {
                    border: 2px solid #4caf50;
                    background-color: qradialgradient(cx:0.5, cy:0.5, fx:0.5, fy:0.5, radius:0.3, stop:0 #ffffff, stop:0.3 #ffffff, stop:0.35 #4caf50, stop:1 #4caf50);
                }
            """)

    def load_media(self, filepath):
        # Lógica para determinar se é vídeo ou imagem
        if filepath.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            self.state.image_path = filepath
            self.state.video_path = None
        elif filepath.lower().endswith(('.mp4', '.avi', '.mkv')):
            self.state.video_path = filepath
            self.state.image_path = None
        
        self.main_window.on_media_loaded()
