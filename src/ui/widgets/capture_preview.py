"""
擷取畫面預覽元件
顯示 OCR 截圖的縮放預覽
"""

from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage
from PIL import Image

from src.ui.theme import AppTheme


class CapturePreview(QLabel):
    """擷取畫面預覽"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(200, 40)
        self.setMaximumHeight(100)
        self.setStyleSheet(
            f"QLabel {{"
            f" background-color: {AppTheme.BG_SECONDARY};"
            f" border: 1px solid {AppTheme.GOLD_MUTED};"
            f" border-radius: {AppTheme.CORNER_SM}px;"
            f" color: {AppTheme.TEXT_MUTED};"
            f"}}"
        )
        self.setText("尚未擷取畫面")
        self._original_pixmap = None

    def set_image(self, pil_img: Image.Image) -> None:
        """顯示 PIL Image

        Args:
            pil_img: PIL.Image (RGB)
        """
        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")

        data = pil_img.tobytes("raw", "RGB")
        qimg = QImage(data, pil_img.width, pil_img.height, pil_img.width * 3,
                       QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        self._original_pixmap = pixmap

        # 縮放至元件大小，保持比例
        scaled = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.setPixmap(scaled)

    def clear_image(self) -> None:
        """清除預覽"""
        self._original_pixmap = None
        self.clear()
        self.setText("尚未擷取畫面")

    def resizeEvent(self, event):
        """視窗縮放時重新調整圖片"""
        super().resizeEvent(event)
        if self._original_pixmap:
            scaled = self._original_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.setPixmap(scaled)
