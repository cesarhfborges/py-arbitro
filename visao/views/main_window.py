from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QFileDialog, QMessageBox, QStackedWidget,
                               QSlider, QLabel, QApplication, QRadioButton, QCheckBox, QColorDialog,
                               QDialog, QMenuBar, QProgressDialog)
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import Qt, QTimer

class ConfirmDialog(QDialog):
    def __init__(self, parent, title, text):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(320)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        layout.addWidget(self.label)
        
        layout.addSpacing(10)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_no = QPushButton("Não")
        self.btn_yes = QPushButton("Sim")
        
        # Ordem explícita: Não à esquerda, Sim à direita
        btn_layout.addWidget(self.btn_no)
        btn_layout.addWidget(self.btn_yes)
        layout.addLayout(btn_layout)
        
        self.btn_no.clicked.connect(self.reject)
        self.btn_yes.clicked.connect(self.accept)
        
        self.btn_no.setDefault(True)
        self.btn_no.setFocus()
from visao.views.components.top_bar import TopBar
from visao.views.components.canvas_view import CanvasView
from visao.views.components.steps_panel import StepsPanel
from visao.models.image_processing import ImageProcessor

class MainWindow(QMainWindow):
    def __init__(self, app_state, controller):
        super().__init__()
        self.state = app_state
        self.controller = controller
        
        self.setWindowTitle("V.I.S.A.O")
        
        self.setup_menu()
        self.setup_ui()
        
        self.base_image_rgb = None
        self.current_image_rgb = None

    def setup_menu(self):
        menubar = self.menuBar()
        
        # Arquivo
        file_menu = menubar.addMenu("Arquivo")
        open_action = QAction("Abrir Mídia", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.on_open_media)
        file_menu.addAction(open_action)
        
        restart_action = QAction("Reiniciar Análise", self)
        restart_action.setShortcut("Ctrl+R")
        restart_action.triggered.connect(self.on_restart)
        file_menu.addAction(restart_action)
        
        export_action = QAction("Exportar Resultado", self)
        export_action.setShortcut("Ctrl+S")
        export_action.triggered.connect(self.on_export)
        file_menu.addAction(export_action)
        
        # Configurações
        settings_menu = menubar.addMenu("Configurações")
        self.multi_win_action = QAction("Modo Multi-Janela", self, checkable=True)
        self.multi_win_action.setChecked(self.state.settings.get("multi_window_enabled", True))
        self.multi_win_action.triggered.connect(self.on_toggle_multi_window)
        settings_menu.addAction(self.multi_win_action)
        
        # Ajuda
        help_menu = menubar.addMenu("Ajuda")
        about_action = QAction("Sobre", self)
        about_action.triggered.connect(self.on_about)
        help_menu.addAction(about_action)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.top_bar = TopBar(self.state.settings)
        main_layout.addWidget(self.top_bar)
        
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget, 1)
        
        # --- PÁGINA 1: Inicial ---
        page_initial = QWidget()
        initial_layout = QVBoxLayout(page_initial)
        # pyrefly: ignore [missing-attribute]
        initial_layout.setAlignment(Qt.AlignCenter)
        
        btn_open_large = QPushButton("Abrir Imagem/Vídeo")
        btn_open_large.setFixedSize(300, 80)
        btn_open_large.setStyleSheet("font-size: 18px; font-weight: bold;")
        btn_open_large.clicked.connect(self.on_open_media)
        
        initial_layout.addWidget(btn_open_large)
        self.stacked_widget.addWidget(page_initial)
        
        # --- PÁGINA 2: Workspace (Passos 2, 3, 4) ---
        page_workspace = QWidget()
        workspace_layout = QHBoxLayout(page_workspace)
        
        # Painel Esquerdo (Filtros e Controles)
        self.sidebar_widget = QWidget()
        self.sidebar = QVBoxLayout(self.sidebar_widget)
        # pyrefly: ignore [missing-attribute]
        self.sidebar.setAlignment(Qt.AlignTop)
        
        lbl_filters = QLabel("Filtros de Imagem")
        lbl_filters.setStyleSheet("font-weight: bold;")
        self.sidebar.addWidget(lbl_filters)
        
        btn_bw = QPushButton("Preto & Branco")
        btn_bw.clicked.connect(lambda: self.apply_filter("bw"))
        self.sidebar.addWidget(btn_bw)
        
        btn_inv = QPushButton("Inverter Cores")
        btn_inv.clicked.connect(lambda: self.apply_filter("invert"))
        self.sidebar.addWidget(btn_inv)
        
        btn_sepia = QPushButton("Sépia")
        btn_sepia.clicked.connect(lambda: self.apply_filter("sepia"))
        self.sidebar.addWidget(btn_sepia)
        
        btn_reset = QPushButton("Remover Filtros")
        btn_reset.clicked.connect(lambda: self.apply_filter("none"))
        self.sidebar.addWidget(btn_reset)
        
        # Controles do Passo 3
        self.sidebar.addSpacing(30)
        self.step3_controls = QWidget()
        self.step3_layout = QVBoxLayout(self.step3_controls)
        self.step3_layout.setContentsMargins(0, 0, 0, 0)
        lbl_step3 = QLabel("Controles de Linha")
        lbl_step3.setStyleSheet("font-weight: bold; color: #ff9800;")
        self.step3_layout.addWidget(lbl_step3)
        
        # Seleção
        self.radio_a = QRadioButton("Linha Atacante")
        self.radio_a.setChecked(True)
        self.radio_d = QRadioButton("Linha Zagueiro")
        self.radio_a.toggled.connect(self.update_movable_line)
        self.radio_d.toggled.connect(self.update_movable_line)
        self.step3_layout.addWidget(self.radio_a)
        self.step3_layout.addWidget(self.radio_d)
        
        # Cor
        btn_color = QPushButton("Mudar Cor")
        btn_color.clicked.connect(self.on_change_color)
        self.step3_layout.addWidget(btn_color)
        
        # Visibilidade
        self.chk_vis_a = QCheckBox("Visível (Atacante)")
        self.chk_vis_a.setChecked(True)
        self.chk_vis_a.toggled.connect(lambda v: self.on_visibility_changed('a', v))
        self.step3_layout.addWidget(self.chk_vis_a)
        
        self.chk_vis_d = QCheckBox("Visível (Zagueiro)")
        self.chk_vis_d.setChecked(True)
        self.chk_vis_d.toggled.connect(lambda v: self.on_visibility_changed('d', v))
        self.step3_layout.addWidget(self.chk_vis_d)
        
        self.chk_show_mask = QCheckBox("Exibir Jogadores Detectados")
        self.chk_show_mask.setChecked(False)
        self.chk_show_mask.toggled.connect(self.on_show_mask_toggled)
        self.step3_layout.addWidget(self.chk_show_mask)
        
        # Espessura
        lbl_thick = QLabel("Espessura (Ambas)")
        # pyrefly: ignore [missing-attribute]
        self.slider_thick = QSlider(Qt.Horizontal)
        self.slider_thick.setMinimum(0)
        self.slider_thick.setMaximum(40)
        self.slider_thick.setValue(26) # Equivale a 2.02px (0.2 + 26 * 0.07)
        self.slider_thick.valueChanged.connect(self.on_thickness_changed)
        self.step3_layout.addWidget(lbl_thick)
        self.step3_layout.addWidget(self.slider_thick)
        
        # Altura Tracejada
        lbl_height = QLabel("Altura da Projeção")
        # pyrefly: ignore [missing-attribute]
        self.slider_height = QSlider(Qt.Horizontal)
        self.slider_height.setMinimum(0)
        self.slider_height.setMaximum(300)
        self.slider_height.setValue(50)
        self.slider_height.valueChanged.connect(self.on_height_changed)
        self.step3_layout.addWidget(lbl_height)
        self.step3_layout.addWidget(self.slider_height)
        
        # Espaçamento do Tracejado
        lbl_spacing = QLabel("Espaçamento do Tracejado")
        # pyrefly: ignore [missing-attribute]
        self.slider_spacing = QSlider(Qt.Horizontal)
        self.slider_spacing.setMinimum(0)
        self.slider_spacing.setMaximum(40)
        self.slider_spacing.setValue(40) # Equivale a 6.0px (0.1 + 40 * 0.1475)
        self.slider_spacing.valueChanged.connect(self.on_spacing_changed)
        self.step3_layout.addWidget(lbl_spacing)
        self.step3_layout.addWidget(self.slider_spacing)

        self.step3_controls.hide()
        self.sidebar.addWidget(self.step3_controls)
        
        # Controles do Passo 2
        self.step2_controls = QWidget()
        self.step2_layout = QVBoxLayout(self.step2_controls)
        self.step2_layout.setContentsMargins(0, 0, 0, 0)
        lbl_step2 = QLabel("Controles de Referência")
        lbl_step2.setStyleSheet("font-weight: bold; color: #ff9800;")
        self.step2_layout.addWidget(lbl_step2)
        
        lbl_thick_s2 = QLabel("Espessura das Linhas")
        # pyrefly: ignore [missing-attribute]
        self.slider_thick_s2 = QSlider(Qt.Horizontal)
        self.slider_thick_s2.setMinimum(0)
        self.slider_thick_s2.setMaximum(40)
        self.slider_thick_s2.setValue(40) # Equivale a 3.0 (0.2 + 40 * 0.07)
        self.slider_thick_s2.valueChanged.connect(self.on_homography_thickness_changed)
        self.step2_layout.addWidget(lbl_thick_s2)
        self.step2_layout.addWidget(self.slider_thick_s2)
        
        self.step2_controls.hide()
        self.sidebar.addWidget(self.step2_controls)
        
        workspace_layout.addWidget(self.sidebar_widget, 1)
        
        # Centro: Canvas
        self.canvas = CanvasView()
        self.canvas.viewer_updated.connect(self.on_canvas_updated)
        workspace_layout.addWidget(self.canvas, 5)
        
        # Painel Direito: Slider de Zoom
        right_panel = QVBoxLayout()
        # pyrefly: ignore [missing-attribute]
        right_panel.setAlignment(Qt.AlignCenter)
        lbl_zoom = QLabel("Zoom")
        # pyrefly: ignore [missing-attribute]
        lbl_zoom.setAlignment(Qt.AlignCenter)
        # pyrefly: ignore [missing-attribute]
        self.zoom_slider = QSlider(Qt.Vertical)
        self.zoom_slider.setMinimum(10)
        self.zoom_slider.setMaximum(800)
        self.zoom_slider.setValue(100)
        # pyrefly: ignore [missing-attribute]
        self.zoom_slider.setTickPosition(QSlider.TicksRight)
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        
        right_panel.addWidget(lbl_zoom)
        right_panel.addWidget(self.zoom_slider)
        workspace_layout.addLayout(right_panel, 1)
        
        self.stacked_widget.addWidget(page_workspace)
        
        # --- Rodapé ---
        self.steps_panel = StepsPanel()
        self.steps_panel.step_changed.connect(self.on_step_changed)
        self.steps_panel.verdict_selected.connect(self.on_verdict)
        self.steps_panel.hide() # Escondido na etapa 1
        main_layout.addWidget(self.steps_panel)

    def on_toggle_multi_window(self, checked):
        self.state.settings["multi_window_enabled"] = checked
        self.state.save_settings()
        if checked:
            self.controller.setup_multi_window()
            if self.controller.multi_window:
                self.controller.show_secondary_window()
                # pyrefly: ignore [missing-attribute]
                if self.canvas.scene.items():
                    self.controller.update_spectator_view(self.canvas.viewport().grab())
        else:
            if self.controller.multi_window:
                self.controller.multi_window.close()
                self.controller.multi_window = None

    def on_open_media(self):
        from pathlib import Path
        downloads_path = str(Path.home() / "Downloads")
        filepath, _ = QFileDialog.getOpenFileName(self, "Selecionar Mídia", downloads_path, 
                                                  "Imagens e Vídeos (*.png *.jpg *.jpeg *.mp4 *.avi)")
        if filepath:
            self.controller.load_media(filepath)

    def on_restart(self):
        dialog = ConfirmDialog(self, "Reiniciar", "Deseja descartar a mídia atual e recomeçar?")
        # pyrefly: ignore [missing-attribute]
        if dialog.exec() == QDialog.Accepted:
            self.state.image_path = None
            self.base_image_rgb = None
            self.current_image_rgb = None
            # pyrefly: ignore [missing-attribute]
            self.canvas.scene.clear()
            
            # Limpar pontos e posições de linhas persistidas do canvas
            if hasattr(self.canvas, 'saved_points'):
                del self.canvas.saved_points
            if hasattr(self.canvas, 'saved_line_a_center'):
                # pyrefly: ignore [missing-attribute]
                del self.canvas.saved_line_a_center
            if hasattr(self.canvas, 'saved_line_d_center'):
                # pyrefly: ignore [missing-attribute]
                del self.canvas.saved_line_d_center
                
            self.steps_panel.current_step = 1
            self.steps_panel.update_ui()
            self.stacked_widget.setCurrentIndex(0)
            self.steps_panel.hide()
            self.zoom_slider.setValue(100)
            if self.controller.multi_window:
                self.controller.update_spectator_view(None)

    def on_media_loaded(self):
        if self.state.image_path:
            self.base_image_rgb = ImageProcessor.load_image(self.state.image_path)
            # pyrefly: ignore [missing-attribute]
            self.current_image_rgb = self.base_image_rgb.copy()
            
            self.stacked_widget.setCurrentIndex(1)
            self.steps_panel.show()
            self.zoom_slider.setValue(100)
            
            self._update_canvas_image()
            
            # Força o passo 2
            self.steps_panel.current_step = 2
            self.steps_panel.update_ui()
            self.on_step_changed(2)
        elif self.state.video_path:
            QMessageBox.information(self, "Vídeo", "A leitura de vídeo quadro-a-quadro será implementada na próxima versão. Carregue uma imagem.")

    def on_zoom_changed(self, value):
        scale_factor = value / 100.0
        base_scale = getattr(self.canvas, 'base_scale', 1.0)
        self.canvas.resetTransform()
        self.canvas.scale(base_scale * scale_factor, base_scale * scale_factor)
        self.on_canvas_updated()

    def apply_filter(self, filter_type):
        if self.base_image_rgb is None: return
        
        if filter_type == "none":
            self.current_image_rgb = self.base_image_rgb.copy()
        else:
            self.current_image_rgb = ImageProcessor.apply_filter(self.base_image_rgb, filter_type)
        
        self._update_canvas_image()

    def _update_canvas_image(self):
        pixmap = ImageProcessor.numpy_to_pixmap(self.current_image_rgb)
        self.canvas.set_image(pixmap)
        self.on_step_changed(self.steps_panel.current_step)

    def advance_to_stage_3_async(self):
        self.loading_dialog = QProgressDialog("Calculando perspectiva tridimensional...", None, 0, 0, self)
        self.loading_dialog.setWindowTitle("Aguarde")
        self.loading_dialog.setWindowModality(Qt.WindowModal)
        self.loading_dialog.setCancelButton(None)
        self.loading_dialog.show()
        
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self._do_setup_stage_3)
        
    def _do_setup_stage_3(self):
        try:
            self.canvas.setup_stage_3(
                self.state.settings["attacker_line_color"],
                self.state.settings["defender_line_color"]
            )
            self.update_movable_line()
            self.on_thickness_changed(self.slider_thick.value())
        except Exception as e:
            print(f"Erro ao configurar etapa 3: {e}")
        finally:
            if hasattr(self, 'loading_dialog'):
                self.loading_dialog.close()

    def on_step_changed(self, step):
        if step == 2:
            self.step3_controls.hide()
            self.step2_controls.show()
            self.canvas.setup_stage_2()
        elif step == 3:
            self.step2_controls.hide()
            self.step3_controls.show()
            self.advance_to_stage_3_async()
        else:
            self.step2_controls.hide()
            self.step3_controls.hide()
            self.canvas._clear_interactive_items()
            
        self.on_canvas_updated()

    def on_canvas_updated(self):
        # Atualiza a view do espectador capturando o conteúdo do canvas
        # Usa um atraso de 0ms (QTimer) para garantir que a captura ocorra DEPOIS que o Qt pintou a tela
        if self.stacked_widget.currentIndex() == 1:
            if not getattr(self, '_spectator_update_pending', False):
                self._spectator_update_pending = True
                from PySide6.QtCore import QTimer
                QTimer.singleShot(0, self._do_grab_and_update_spectator)

    def _do_grab_and_update_spectator(self):
        self._spectator_update_pending = False
        if self.stacked_widget.currentIndex() == 1:
            # Sem o OpenGL, o .grab() do viewport é perfeitamente seguro e rápido
            pixmap = self.canvas.viewport().grab()
            self.controller.update_spectator_view(pixmap)

    def on_verdict(self, verdict):
        QMessageBox.information(self, "Veredito", f"O Veredito Final é:\n{verdict}")

    def on_export(self):
        path, _ = QFileDialog.getSaveFileName(self, "Exportar Imagem", "", "PNG (*.png)")
        if path:
            pixmap = self.canvas.viewport().grab()
            pixmap.save(path)
            QMessageBox.information(self, "Exportar", "Imagem exportada com sucesso!")

    def on_about(self):
        QMessageBox.about(self, "Sobre o V.I.S.A.O", 
                          "V.I.S.A.O\nVerificação de Impedimento por Sistema de Análise Óptica\nVersão: 1.1.0")

    def update_movable_line(self):
        if self.canvas.line_a and self.canvas.line_d:
            from PySide6.QtWidgets import QGraphicsItem
            # pyrefly: ignore [missing-attribute]
            self.canvas.line_a.setFlag(QGraphicsItem.ItemIsMovable, self.radio_a.isChecked())
            # pyrefly: ignore [missing-attribute]
            self.canvas.line_d.setFlag(QGraphicsItem.ItemIsMovable, self.radio_d.isChecked())
            
            # Sincroniza sliders com a linha selecionada
            self.slider_height.blockSignals(True)
            self.slider_spacing.blockSignals(True)
            
            def spacing_to_step(spacing_val):
                step = round((spacing_val - 0.1) / 0.1475)
                return max(0, min(40, step))
            
            if self.radio_a.isChecked():
                self.slider_height.setValue(self.canvas.line_a.height_val)
                self.slider_spacing.setValue(spacing_to_step(self.canvas.line_a.dash_spacing))
            else:
                self.slider_height.setValue(self.canvas.line_d.height_val)
                self.slider_spacing.setValue(spacing_to_step(self.canvas.line_d.dash_spacing))
                
            self.slider_height.blockSignals(False)
            self.slider_spacing.blockSignals(False)

    def on_change_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            hex_color = color.name()
            if self.radio_a.isChecked() and self.canvas.line_a:
                self.canvas.line_a.color = color
                self.state.settings["attacker_line_color"] = hex_color
                self.canvas.line_a.update()
            elif self.radio_d.isChecked() and self.canvas.line_d:
                self.canvas.line_d.color = color
                self.state.settings["defender_line_color"] = hex_color
                self.canvas.line_d.update()
            self.state.save_settings()
            self.on_canvas_updated()

    def on_visibility_changed(self, line_id, visible):
        if line_id == 'a' and self.canvas.line_a:
            self.canvas.line_a.is_visible = visible
            self.canvas.line_a.update()
            self.on_canvas_updated()
        elif line_id == 'd' and self.canvas.line_d:
            self.canvas.line_d.is_visible = visible
            self.canvas.line_d.update()
            self.on_canvas_updated()

    def on_show_mask_toggled(self, checked):
        self.canvas.show_player_mask = checked
        self.canvas.scene.update()
        self.on_canvas_updated()

    def on_thickness_changed(self, value):
        actual_thickness = 0.2 + value * 0.07
        if self.canvas.line_a:
            self.canvas.line_a.thickness = actual_thickness
            self.canvas.line_a.update()
        if self.canvas.line_d:
            self.canvas.line_d.thickness = actual_thickness
            self.canvas.line_d.update()
        self.on_canvas_updated()

    def on_height_changed(self, value):
        if self.radio_a.isChecked() and self.canvas.line_a:
            self.canvas.line_a.height_val = value
            self.canvas.line_a.update()
        elif self.radio_d.isChecked() and self.canvas.line_d:
            self.canvas.line_d.height_val = value
            self.canvas.line_d.update()
        self.on_canvas_updated()

    def on_spacing_changed(self, value):
        actual_spacing = 0.1 + value * 0.1475
        if self.radio_a.isChecked() and self.canvas.line_a:
            self.canvas.line_a.dash_spacing = actual_spacing
            self.canvas.line_a.update()
        elif self.radio_d.isChecked() and self.canvas.line_d:
            self.canvas.line_d.dash_spacing = actual_spacing
            self.canvas.line_d.update()
        self.on_canvas_updated()

    def on_homography_thickness_changed(self, value):
        actual_thickness = 0.2 + value * 0.07
        self.canvas.set_homography_thickness(actual_thickness)
        self.on_canvas_updated()

    def closeEvent(self, event):
        dialog = ConfirmDialog(self, "Sair", "Deseja realmente fechar o sistema?")
        # pyrefly: ignore [missing-attribute]
        if dialog.exec() == QDialog.Accepted:
            event.accept()
            QApplication.quit()
        else:
            event.ignore()
