import cv2
import numpy as np
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsItem
from PySide6.QtCore import Qt, QPointF, Signal, QRectF, QObject
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QPixmap, QPainterPath, QImage, QPolygonF
from visao.utils.segmentation import get_player_polygons
from visao.utils.logger import logger
import threading
import queue

class SegmentationWorker(QObject):
    finished_polys = Signal(list)

segmentation_queue = queue.Queue()

def _segmentation_worker_loop():
    while True:
        task = segmentation_queue.get()
        if task is None:
            break
        worker, image_np = task
        try:
            import cv2
            cv2.imwrite("debug_yolo_input.jpg", image_np)
            polys = get_player_polygons(image_np)
            worker.finished_polys.emit(polys)
        except Exception as e:
            print(f"Erro na segmentação: {e}")
            worker.finished_polys.emit([])
        finally:
            segmentation_queue.task_done()

segmentation_thread = threading.Thread(target=_segmentation_worker_loop, daemon=True)
segmentation_thread.start()

class QuadrilateralItem(QGraphicsItem):
    def __init__(self, points):
        super().__init__()
        self.points = points # Referência aos DraggablePoints
        self.setZValue(5) # Garante que fique ACIMA da imagem (que está no Z=0)
        self.thickness = 3
        
    def boundingRect(self):
        if len(self.points) == 4:
            min_x = min([p.scenePos().x() for p in self.points])
            max_x = max([p.scenePos().x() for p in self.points])
            min_y = min([p.scenePos().y() for p in self.points])
            max_y = max([p.scenePos().y() for p in self.points])
            margin = 10
            return QRectF(min_x - margin, min_y - margin, (max_x - min_x) + margin * 2, (max_y - min_y) + margin * 2).normalized()
        return QRectF(0, 0, 1000, 1000)
        
    # pyrefly: ignore [bad-override]
    def paint(self, painter, option, widget):
        if len(self.points) == 4:
            p0 = self.points[0].scenePos()
            p1 = self.points[1].scenePos()
            p2 = self.points[2].scenePos()
            p3 = self.points[3].scenePos()
            
            # Canetas
            # pyrefly: ignore [missing-attribute]
            pen_horizontal = QPen(QColor(0, 0, 0), self.thickness, Qt.SolidLine) # Duas horizontais em preto
            # pyrefly: ignore [missing-attribute]
            pen_vertical = QPen(QColor(255, 0, 0), self.thickness, Qt.SolidLine)   # Duas verticais em vermelho
            
            # Desenha horizontais (Top: 0 -> 1, Bottom: 3 -> 2)
            painter.setPen(pen_horizontal)
            painter.drawLine(p0, p1)
            painter.drawLine(p3, p2)
            
            # Desenha verticais (Left: 0 -> 3, Right: 1 -> 2)
            painter.setPen(pen_vertical)
            painter.drawLine(p0, p3)
            painter.drawLine(p1, p2)

class DraggablePoint(QGraphicsItem):
    def __init__(self, x, y, canvas, radius=10):
        super().__init__()
        self.radius = radius
        self.canvas = canvas
        self.setPos(x, y)
        # pyrefly: ignore [missing-attribute]
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        # pyrefly: ignore [missing-attribute]
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setZValue(10) # Fica no topo mais alto, acima do QuadrilateralItem
        
    def boundingRect(self):
        margin = 4
        return QRectF(-self.radius - margin, -self.radius - margin, (self.radius + margin) * 2, (self.radius + margin) * 2)
        
    # pyrefly: ignore [bad-override]
    def paint(self, painter, option, widget):
        # Círculo azul apenas para indicar zona de clique, sem preenchimento
        # pyrefly: ignore [missing-attribute]
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(0, 0, 255), 2)) # Azul
        painter.drawEllipse(self.boundingRect().adjusted(1, 1, -1, -1))

    def itemChange(self, change, value):
        # pyrefly: ignore [missing-attribute]
        if change == QGraphicsItem.ItemPositionHasChanged:
            if hasattr(self, 'canvas') and self.canvas and hasattr(self.canvas, 'quad') and self.canvas.quad:
                self.canvas.quad.prepareGeometryChange()
                self.canvas.quad.update()
            if hasattr(self, 'canvas') and self.canvas:
                self.canvas.save_current_points()
            if self.scene():
                self.scene().update()
                self.canvas.viewer_updated.emit()
                
        return super().itemChange(change, value)


class PerspectiveCross(QGraphicsItem):
    def __init__(self, start_pos, H, img_rect, color_hex, canvas):
        super().__init__()
        self.H = np.ascontiguousarray(H) if H is not None else None
        try:
            self.H_inv = np.ascontiguousarray(np.linalg.inv(self.H)) if self.H is not None else None
        except:
            self.H_inv = None
        self.img_rect = img_rect
        self.color = QColor(color_hex)
        self.canvas = canvas
        
        self._offscreen_buffer = None
        
        self.is_visible = True
        self.dash_spacing = 6
        self.setPos(0, 0)
        self.center_pt = start_pos
        self.setZValue(10)
        
        self.thickness = 2
        self.height_val = 50
        self.dash_spacing = 6
        self.is_visible = True
        self.dragging = False

    def boundingRect(self):
        if self.img_rect:
            # Expandir o bounding rect ligeiramente para não cortar a linha grossa nas bordas
            return self.img_rect.adjusted(-10, -10, 10, 10)
        return QRectF(-1000, -1000, 3000, 3000)
        
    def paint(self, painter, option, widget):
        if not hasattr(self, '_logged_paint'):
            logger.log("PerspectiveCross.paint: inicio (1a vez)")
            self._logged_paint = True
            
        if not self.is_visible or self.H is None or self.H_inv is None:
            return
            
        if not self.img_rect: return
            
        rect = self.img_rect.toRect()
        if rect.width() <= 0 or rect.height() <= 0: return
        
        # Buffer QImage alocado apenas 1x para evitar estourar a memória (crash em paint events repetidos)
        if self._offscreen_buffer is None or self._offscreen_buffer.size() != rect.size():
            self._offscreen_buffer = QImage(rect.size(), QImage.Format_ARGB32_Premultiplied)
            
        self._offscreen_buffer.fill(Qt.transparent)
        
        off_painter = QPainter(self._offscreen_buffer)
        off_painter.setRenderHint(QPainter.Antialiasing)
        off_painter.translate(-self.img_rect.topLeft())
        
        pc = self.center_pt
        
        # Mapear Pc para o espaço de mundo (World) usando NumPy para evitar crashes do OpenCV com matrizes F-contiguous
        v_screen = np.array([pc.x(), pc.y(), 1.0], dtype=np.float64)
        v_world = np.dot(self.H_inv, v_screen)
        
        # Prevenção contra divisão por zero
        w_div = v_world[2] if abs(v_world[2]) > 1e-6 else 1e-6
        wx, wy = v_world[0] / w_div, v_world[1] / w_div
        
        off_painter.setPen(QPen(self.color, self.thickness))
        
        def draw_projective_line(L_world):
            import math
            L = np.array(L_world, dtype=np.float64)
            l_screen = np.dot(self.H_inv.T, L)
            A, B, C = float(l_screen[0]), float(l_screen[1]), float(l_screen[2])
            
            rect = self.img_rect
            xmin, xmax = float(rect.left()) - 1000.0, float(rect.right()) + 1000.0
            ymin, ymax = float(rect.top()) - 1000.0, float(rect.bottom()) + 1000.0
            
            pts = []
            
            if abs(B) > 1e-6:
                y = -(A * xmin + C) / B
                if ymin <= y <= ymax: pts.append((xmin, y))
                y = -(A * xmax + C) / B
                if ymin <= y <= ymax: pts.append((xmax, y))
            if abs(A) > 1e-6:
                x = -(B * ymin + C) / A
                if xmin <= x <= xmax: pts.append((x, ymin))
                x = -(B * ymax + C) / A
                if xmin <= x <= xmax: pts.append((x, ymax))
                
            unique_pts = []
            for p in pts:
                if not any(math.hypot(p[0]-up[0], p[1]-up[1]) < 1.0 for up in unique_pts):
                    unique_pts.append(p)
                    
            if len(unique_pts) >= 2:
                off_painter.drawLine(QPointF(unique_pts[0][0], unique_pts[0][1]), 
                                     QPointF(unique_pts[1][0], unique_pts[1][1]))

        # Line 1 (Horizontal no mundo): Y = wy
        draw_projective_line([0.0, 1.0, -float(wy)])
        # Line 2 (Vertical no mundo): X = wx
        draw_projective_line([1.0, 0.0, -float(wx)])
        
        # Desenhar linha tracejada de altura com a cor inversa para destaque visual e espaçamento dinâmico
        inv_color = QColor(255 - self.color.red(), 255 - self.color.green(), 255 - self.color.blue())
        pen = QPen(inv_color, self.thickness)
        # pyrefly: ignore [missing-attribute]
        pen.setStyle(Qt.CustomDashLine)
        pen.setDashPattern([float(self.dash_spacing), float(self.dash_spacing)])
        off_painter.setPen(pen)
        
        off_painter.drawLine(pc.x(), pc.y(), pc.x(), pc.y() - self.height_val)
        
        off_painter.end()
        
        # Apply mask
        if hasattr(self.canvas, 'player_mask_image') and self.canvas.player_mask_image:
            mask_painter = QPainter(self._offscreen_buffer)
            mask_painter.setCompositionMode(QPainter.CompositionMode_DestinationOut)
            mask_painter.drawImage(0, 0, self.canvas.player_mask_image)
            mask_painter.end()
            
        painter.drawImage(self.img_rect.topLeft(), self._offscreen_buffer)

    def mousePressEvent(self, event):
        # Permite mover apenas se a flag ItemIsMovable estiver ativa
        # pyrefly: ignore [missing-attribute]
        if not (self.flags() & QGraphicsItem.ItemIsMovable):
            event.ignore()
            return
            
        if (event.pos() - self.center_pt).manhattanLength() < 25:
            self.dragging = True
            event.accept()
        else:
            event.ignore()

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.center_pt = event.pos()
            # Salvar no canvas para persistência
            if self.canvas.line_a == self:
                self.canvas.saved_line_a_center = self.center_pt
            elif self.canvas.line_d == self:
                self.canvas.saved_line_d_center = self.center_pt
            self.update()
            self.canvas.viewer_updated.emit()
            event.accept()

    def mouseReleaseEvent(self, event):
        self.dragging = False
        event.accept()


class CanvasView(QGraphicsView):
    viewer_updated = Signal()
    
    def __init__(self):
        super().__init__()
        
        # Desativando aceleração de hardware (OpenGL) para evitar bugs de tela preta ao fazer .grab()
        # self.setViewport(QOpenGLWidget())
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        # pyrefly: ignore [bad-assignment, bad-override]
        self.scene = QGraphicsScene(self)
        # pyrefly: ignore [bad-argument-type]
        self.setScene(self.scene)
        
        # pyrefly: ignore [missing-attribute]
        self.setRenderHint(QPainter.Antialiasing)
        # pyrefly: ignore [missing-attribute]
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        # pyrefly: ignore [missing-attribute]
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        # pyrefly: ignore [missing-attribute]
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        
        self.current_pixmap_item = None
        self.points = []
        self.quad = None
        
        self.show_player_mask = False
        
        self.line_a = None
        self.line_d = None
        self.H = None
        self.homography_line_thickness = 3
        self.player_mask_image = None
        self.seg_thread = None

    def set_image(self, pixmap: QPixmap):
        # pyrefly: ignore [missing-attribute]
        self.scene.clear()
        self.points.clear()
        self.quad = None
        self.line_a = None
        self.line_d = None
        self.player_mask_image = None
        
        # pyrefly: ignore [missing-attribute]
        self.current_pixmap_item = self.scene.addPixmap(pixmap)
        # pyrefly: ignore [missing-attribute]
        self.scene.setSceneRect(self.current_pixmap_item.boundingRect())
        # pyrefly: ignore [missing-attribute]
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        
        # Salva o fator de escala inicial (fit in view) como escala base
        self.base_scale = self.transform().m11()
        if self.base_scale <= 0:
            self.base_scale = 1.0
            
        # Iniciar a segmentação em background
        try:
            image = pixmap.toImage()
            image = image.convertToFormat(QImage.Format_RGB888)
            width = image.width()
            height = image.height()
            bpl = image.bytesPerLine()
            ptr = image.constBits()
            # Lida com o padding da QImage (bytesPerLine) e cria uma CÓPIA 
            # para que a thread não acesse memória desalocada quando QImage sumir
            arr = np.array(ptr, dtype=np.uint8).reshape(height, bpl)
            arr = arr[:, :width * 3].reshape(height, width, 3)
            # YOLO espera imagem no formato BGR, o QImage nos deu RGB.
            arr_bgr = arr[:, :, ::-1].copy()
            
            self.seg_worker = SegmentationWorker()
            self.seg_worker.finished_polys.connect(self.on_segmentation_finished)
            segmentation_queue.put((self.seg_worker, arr_bgr))
        except Exception as e:
            print(f"Erro ao iniciar thread de segmentacao: {e}")

    def on_segmentation_finished(self, polys):
        if not self.current_pixmap_item: return
        rect = self.current_pixmap_item.boundingRect().toRect()
        if rect.width() <= 0 or rect.height() <= 0: return
        
        # Usa QImage em vez de QPixmap para não sobrecarregar recursos do sistema gráfico/GDI
        mask_image = QImage(rect.size(), QImage.Format_ARGB32_Premultiplied)
        mask_image.fill(Qt.transparent)
        
        painter = QPainter(mask_image)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(0, 0, 0, 255))
        painter.setPen(Qt.NoPen)
        
        path = QPainterPath()
        path.setFillRule(Qt.WindingFill)
        
        print(f"[Info] Segmentação retornou {len(polys)} polígonos.")
        
        for poly in polys:
            qpoly = QPolygonF()
            for pt in poly:
                qpoly.append(QPointF(pt[0], pt[1]))
            path.addPolygon(qpoly)
            
        painter.drawPath(path)
        painter.end()
        
        self.player_mask_image = mask_image
        self.viewer_updated.emit()
        self.scene.update()

    def wheelEvent(self, event):
        # Ignora zoom do mouse, controlado pelo slider agora
        pass

    def setup_stage_2(self):
        self._clear_interactive_items()
        if not self.current_pixmap_item: return
            
        rect = self.current_pixmap_item.boundingRect()
        cx, cy = rect.width() / 2, rect.height() / 2
        
        # Se já temos pontos salvos, usa as posições salvas
        if hasattr(self, 'saved_points') and len(self.saved_points) == 4:
            pts = self.saved_points
        else:
            offset_x = min(rect.width(), rect.height()) * 0.3
            offset_y = offset_x * 0.6
            pts = [
                QPointF(cx - offset_x, cy - offset_y),
                QPointF(cx + offset_x, cy - offset_y),
                QPointF(cx + offset_x + 100, cy + offset_y),
                QPointF(cx - offset_x - 100, cy + offset_y)
            ]
            
        self.points.clear()
        for pt_val in pts:
            pt = DraggablePoint(pt_val.x(), pt_val.y(), self)
            # pyrefly: ignore [missing-attribute]
            self.scene.addItem(pt)
            self.points.append(pt)
            
        self.quad = QuadrilateralItem(self.points)
        self.quad.thickness = self.homography_line_thickness
        # pyrefly: ignore [missing-attribute]
        self.scene.addItem(self.quad)
        self.viewer_updated.emit()

    def set_homography_thickness(self, value):
        self.homography_line_thickness = value
        if self.quad:
            self.quad.thickness = value
            self.quad.prepareGeometryChange()
            self.quad.update()

    def save_current_points(self):
        if len(self.points) == 4:
            self.saved_points = [p.scenePos() for p in self.points]

    def calculate_homography(self):
        logger.log("CanvasView.calculate_homography: inicio")
        if len(self.points) != 4: return None
        
        # Quadrado ideal no mundo real (proporção 1:1)
        src_pts = np.array([
            [0, 0],
            [1000, 0],
            [1000, 1000],
            [0, 1000]
        ], dtype=np.float32)
        
        dst_pts = np.array([
            [self.points[0].scenePos().x(), self.points[0].scenePos().y()],
            [self.points[1].scenePos().x(), self.points[1].scenePos().y()],
            [self.points[2].scenePos().x(), self.points[2].scenePos().y()],
            [self.points[3].scenePos().x(), self.points[3].scenePos().y()]
        ], dtype=np.float32)
        
        logger.log(f"CanvasView.calculate_homography: dst_pts={dst_pts.tolist()}")
        H, _ = cv2.findHomography(src_pts, dst_pts)
        logger.log("CanvasView.calculate_homography: findHomography concluido")
        return H

    def setup_stage_3(self, attacker_color, defender_color):
        logger.log("CanvasView.setup_stage_3: inicio")
        if len(self.points) == 4:
            self.H = self.calculate_homography()
        
        logger.log("CanvasView.setup_stage_3: limpando interativos")
        self._clear_interactive_items()
        
        if not self.current_pixmap_item or self.H is None: 
            logger.log("CanvasView.setup_stage_3: imagem ausente ou H nulo. Cancelando.")
            return
            
        rect = self.current_pixmap_item.boundingRect()
        cx, cy = rect.width() / 2, rect.height() / 2
        
        pos_a = self.saved_line_a_center if hasattr(self, 'saved_line_a_center') else QPointF(cx, cy - 50)
        pos_d = self.saved_line_d_center if hasattr(self, 'saved_line_d_center') else QPointF(cx, cy + 50)
        
        logger.log("CanvasView.setup_stage_3: instanciando PerspectiveCross A")
        self.line_a = PerspectiveCross(pos_a, self.H, rect, attacker_color, self)
        # pyrefly: ignore [missing-attribute]
        self.scene.addItem(self.line_a)
        
        logger.log("CanvasView.setup_stage_3: instanciando PerspectiveCross D")
        self.line_d = PerspectiveCross(pos_d, self.H, rect, defender_color, self)
        # pyrefly: ignore [missing-attribute]
        self.line_d.setFlag(QGraphicsItem.ItemIsMovable, False) # Inicia bloqueada, apenas A se move
        # pyrefly: ignore [missing-attribute]
        self.scene.addItem(self.line_d)
        
        logger.log("CanvasView.setup_stage_3: emitindo viewer_updated")
        self.viewer_updated.emit()
        logger.log("CanvasView.setup_stage_3: concluido")

    def _clear_interactive_items(self):
        for pt in self.points:
            # pyrefly: ignore [missing-attribute]
            self.scene.removeItem(pt)
        if self.quad:
            # pyrefly: ignore [missing-attribute]
            self.scene.removeItem(self.quad)
        if self.line_a:
            # pyrefly: ignore [missing-attribute]
            self.scene.removeItem(self.line_a)
        if self.line_d:
            # pyrefly: ignore [missing-attribute]
            self.scene.removeItem(self.line_d)
        
        self.points.clear()
        self.quad = None
        self.line_a = None
        self.line_d = None
