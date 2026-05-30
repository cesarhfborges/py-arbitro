from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal

class StepsPanel(QWidget):
    step_changed = Signal(int)
    verdict_selected = Signal(str)

    def __init__(self):
        super().__init__()
        # pyrefly: ignore [bad-assignment, bad-override]
        self.layout = QHBoxLayout(self)
        # pyrefly: ignore [missing-attribute]
        self.layout.setAlignment(Qt.AlignCenter)
        
        self.btn_prev = QPushButton("Anterior")
        self.btn_prev.clicked.connect(self.on_prev)
        
        self.lbl_step = QLabel("Passo 1: Selecionar Mídia")
        self.lbl_step.setStyleSheet("font-weight: bold; font-size: 14px; margin: 0 20px;")
        
        self.btn_next = QPushButton("Próximo")
        self.btn_next.clicked.connect(self.on_next)
        
        self.btn_verdict_offside = QPushButton("Impedimento Claro")
        self.btn_verdict_offside.setStyleSheet("background-color: #d32f2f;")
        self.btn_verdict_offside.clicked.connect(lambda: self.verdict_selected.emit("Impedimento Claro"))
        self.btn_verdict_offside.hide()
        
        self.btn_verdict_clean = QPushButton("Jogada Limpa")
        self.btn_verdict_clean.setStyleSheet("background-color: #388e3c;")
        self.btn_verdict_clean.clicked.connect(lambda: self.verdict_selected.emit("Jogada Limpa"))
        self.btn_verdict_clean.hide()
        
        # pyrefly: ignore [missing-attribute]
        self.layout.addWidget(self.btn_prev)
        # pyrefly: ignore [missing-attribute]
        self.layout.addWidget(self.lbl_step)
        # pyrefly: ignore [missing-attribute]
        self.layout.addWidget(self.btn_next)
        # pyrefly: ignore [missing-attribute]
        self.layout.addWidget(self.btn_verdict_offside)
        # pyrefly: ignore [missing-attribute]
        self.layout.addWidget(self.btn_verdict_clean)
        
        self.current_step = 1
        self.update_ui()

    def on_prev(self):
        if self.current_step > 1:
            self.current_step -= 1
            self.update_ui()
            self.step_changed.emit(self.current_step)

    def on_next(self):
        if self.current_step < 4:
            self.current_step += 1
            self.update_ui()
            self.step_changed.emit(self.current_step)

    def update_ui(self):
        titles = {
            1: "Passo 1: Selecionar Mídia",
            2: "Passo 2: Posicionar Referências",
            3: "Passo 3: Linhas de Impedimento",
            4: "Passo 4: Veredito"
        }
        self.lbl_step.setText(titles.get(self.current_step, ""))
        
        self.btn_prev.setEnabled(self.current_step > 1)
        
        if self.current_step == 4:
            self.btn_next.hide()
            self.btn_verdict_offside.show()
            self.btn_verdict_clean.show()
        else:
            self.btn_next.show()
            self.btn_verdict_offside.hide()
            self.btn_verdict_clean.hide()
