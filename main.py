import sys
import traceback
import datetime
import faulthandler
from PySide6.QtWidgets import QApplication, QMessageBox
from visao.controllers.main_controller import MainController

def global_exception_handler(exc_type, exc_value, exc_traceback):
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print("ERRO CRÍTICO ENCONTRADO:\n", error_msg, file=sys.stderr)
    
    try:
        with open("crash.log", "a", encoding="utf-8") as f:
            f.write(f"\n--- Crash at {datetime.datetime.now()} ---\n")
            f.write(error_msg)
    except:
        pass
        
    try:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Ocorreu um erro inesperado!")
        msg.setInformativeText(f"O erro foi salvo no arquivo 'crash.log'.\n\nDetalhes:\n{str(exc_value)}")
        msg.setWindowTitle("Erro Crítico")
        msg.exec()
    except:
        pass

def main():
    with open("crash_c.log", "w") as f_err:
        faulthandler.enable(f_err)
    sys.excepthook = global_exception_handler
    app = QApplication(sys.argv)
    
    # Nome da Aplicação
    app.setApplicationName("V.I.S.A.O")
    app.setApplicationVersion("1.0.0")

    controller = MainController(app)
    controller.start()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
