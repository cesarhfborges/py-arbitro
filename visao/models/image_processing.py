import cv2
import numpy as np
from PySide6.QtGui import QImage, QPixmap

class ImageProcessor:
    @staticmethod
    def load_image(filepath):
        img = cv2.imread(filepath)
        if img is None:
            return None
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    @staticmethod
    def apply_filter(image_rgb, filter_type):
        if image_rgb is None:
            return None
        
        if filter_type == "bw":
            gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
            return cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
        
        elif filter_type == "invert":
            return cv2.bitwise_not(image_rgb)
        
        elif filter_type == "sepia":
            # Matriz de sépia
            kernel = np.array([[0.393, 0.769, 0.189],
                               [0.349, 0.686, 0.168],
                               [0.272, 0.534, 0.131]])
            sepia_img = cv2.transform(image_rgb, kernel)
            sepia_img = np.clip(sepia_img, 0, 255).astype(np.uint8)
            return sepia_img
        
        return image_rgb

    @staticmethod
    def numpy_to_pixmap(image_rgb):
        if image_rgb is None:
            return QPixmap()
        h, w, ch = image_rgb.shape
        bytes_per_line = ch * w
        # pyrefly: ignore [missing-attribute]
        q_img = QImage(image_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        return QPixmap.fromImage(q_img)
