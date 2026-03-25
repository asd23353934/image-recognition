"""
區域選取遮罩
全螢幕半透明遮罩，支援滑鼠拖曳選取矩形區域
"""

from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, Signal, QRect, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QCursor

from src.ui.theme import AppTheme


class RegionOverlay(QWidget):
    """全螢幕遮罩 + 區域拖曳選取"""

    region_selected = Signal(int, int, int, int)  # left, top, width, height
    cancelled = Signal()

    def __init__(self, target_rect: tuple[int, int, int, int] | None = None):
        """建立遮罩

        Args:
            target_rect: (left, top, width, height) 目標視窗區域，若為 None 則全螢幕
        """
        super().__init__(None)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setCursor(Qt.CursorShape.CrossCursor)

        # 計算覆蓋區域
        if target_rect:
            self._offset_x, self._offset_y, w, h = target_rect
            self.setGeometry(self._offset_x, self._offset_y, w, h)
        else:
            # 全螢幕覆蓋所有螢幕
            screen = QApplication.primaryScreen().geometry()
            self._offset_x = screen.x()
            self._offset_y = screen.y()
            self.setGeometry(screen)

        # 拖曳狀態
        self._dragging = False
        self._start_pos = QPoint()
        self._current_pos = QPoint()
        self._selection = QRect()

    def paintEvent(self, event):
        """繪製半透明遮罩與選取區域"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 半透明黑色遮罩
        painter.fillRect(self.rect(), QColor(0, 0, 0, 120))

        # 繪製選取區域（清除遮罩，顯示下方內容）
        if not self._selection.isNull() and self._selection.isValid():
            # 清除選取區域的遮罩
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(self._selection, QColor(0, 0, 0, 0))

            # 繪製選取邊框
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            pen = QPen(QColor(AppTheme.GOLD_PRIMARY), 2)
            pen.setStyle(Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawRect(self._selection)

            # 顯示選取區域大小
            w = self._selection.width()
            h = self._selection.height()
            size_text = f"{w} x {h}"
            painter.setFont(QFont(AppTheme.FONT_FAMILY, 10))
            painter.setPen(QColor(AppTheme.TEXT_GOLD))
            text_x = self._selection.x() + 4
            text_y = self._selection.y() - 6
            if text_y < 16:
                text_y = self._selection.bottom() + 16
            painter.drawText(text_x, text_y, size_text)

        # 提示文字（下移 60px）
        painter.setPen(QColor(AppTheme.TEXT_PRIMARY))
        painter.setFont(QFont(AppTheme.FONT_FAMILY, 14, QFont.Weight.Bold))
        hint = "拖曳選取監測區域    |    Esc 取消"
        hint_rect = self.rect().adjusted(0, 60, 0, 0)
        painter.drawText(hint_rect, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter, hint)

        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._start_pos = event.position().toPoint()
            self._current_pos = self._start_pos
            self._selection = QRect()

    def mouseMoveEvent(self, event):
        if self._dragging:
            self._current_pos = event.position().toPoint()
            self._selection = QRect(self._start_pos, self._current_pos).normalized()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._dragging:
            self._dragging = False
            self._current_pos = event.position().toPoint()
            self._selection = QRect(self._start_pos, self._current_pos).normalized()
            self.update()
            # 自動確認選取
            self._confirm_selection()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.cancelled.emit()
            self.close()

    def _confirm_selection(self):
        """確認選取"""
        if self._selection.isNull() or not self._selection.isValid():
            return
        if self._selection.width() < 10 or self._selection.height() < 10:
            return

        # 轉換為絕對螢幕座標
        abs_left = self._offset_x + self._selection.x()
        abs_top = self._offset_y + self._selection.y()
        self.region_selected.emit(
            abs_left, abs_top,
            self._selection.width(), self._selection.height()
        )
        self.close()
