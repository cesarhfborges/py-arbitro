import sys
from PySide6.QtWidgets import QApplication
from visao.controllers.main_controller import MainController

def main():
    app = QApplication(sys.argv)
    
    # Nome da Aplicação
    app.setApplicationName("V.I.S.A.O")
    app.setApplicationVersion("1.0.0")

    controller = MainController(app)
    controller.start()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
