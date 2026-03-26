"""
浮動視窗
置頂迷你視窗，顯示即時經驗值數據
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QPoint, QRectF
from PySide6.QtGui import QFont, QPainter, QColor, QPen, QBrush, QPainterPath

from src.ui.theme import AppTheme

# 拖曳調整大小的邊緣偵測範圍 (px)
_RESIZE_MARGIN = 8


class FloatWindow(QWidget):
    """經驗值數據浮動視窗"""

    def __init__(self, parent=None):
        super().__init__(None)  # 獨立視窗，不設 parent

        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.setMinimumSize(200, 160)
        self.setMaximumSize(600, 500)
        self.resize(250, 210)

        # 拖曳狀態
        self._dragging = False
        self._drag_offset = QPoint()

        # 調整大小狀態
        self._resizing = False
        self._resize_start_pos = QPoint()
        self._resize_start_size = None

        self._build_ui()

    def _build_ui(self):
        """建構 UI"""
        # 不在 QWidget 層級設背景，改由 paintEvent 繪製圓角半透明背景
        self.setStyleSheet(
            "QWidget { background: transparent; border: none; }"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 12)
        layout.setSpacing(2)

        # 標題列
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Image Recognition")
        title.setStyleSheet(
            f"color: {AppTheme.TEXT_GOLD}; font-size: 11px; font-weight: bold;"
        )
        title_row.addWidget(title)
        title_row.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.clicked.connect(self.hide)
        close_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none;"
            f" color: {AppTheme.TEXT_MUTED}; font-size: 16px; }}"
            f"QPushButton:hover {{ color: {AppTheme.ACCENT_RED}; }}"
        )
        title_row.addWidget(close_btn)
        layout.addLayout(title_row)

        # 數據標籤
        label_style = (
            f"color: {AppTheme.TEXT_SECONDARY}; font-size: 11px;"
        )
        value_style = (
            f"color: {AppTheme.TEXT_HIGHLIGHT}; font-size: 13px;"
            f" font-weight: bold;"
        )
        green_style = (
            f"color: {AppTheme.ACCENT_GREEN}; font-size: 13px;"
            f" font-weight: bold;"
        )
        yellow_style = (
            f"color: {AppTheme.ACCENT_YELLOW}; font-size: 13px;"
            f" font-weight: bold;"
        )

        # 當前經驗值
        row1 = QHBoxLayout()
        row1.setSpacing(4)
        lbl1 = QLabel("當前經驗:")
        lbl1.setStyleSheet(label_style)
        row1.addWidget(lbl1)
        self.exp_value_lbl = QLabel("--")
        self.exp_value_lbl.setStyleSheet(value_style)
        row1.addWidget(self.exp_value_lbl)
        row1.addStretch()
        layout.addLayout(row1)

        # 每分鐘預估
        row_min = QHBoxLayout()
        row_min.setSpacing(4)
        lbl_min = QLabel("每分鐘:")
        lbl_min.setStyleSheet(label_style)
        row_min.addWidget(lbl_min)
        self.rate_min_lbl = QLabel("--")
        self.rate_min_lbl.setStyleSheet(green_style)
        row_min.addWidget(self.rate_min_lbl)
        row_min.addStretch()
        layout.addLayout(row_min)

        # 10 分鐘預估
        row_10 = QHBoxLayout()
        row_10.setSpacing(4)
        lbl_10 = QLabel("10分鐘:")
        lbl_10.setStyleSheet(label_style)
        row_10.addWidget(lbl_10)
        self.rate_10min_lbl = QLabel("--")
        self.rate_10min_lbl.setStyleSheet(green_style)
        row_10.addWidget(self.rate_10min_lbl)
        row_10.addStretch()
        layout.addLayout(row_10)

        # 60 分鐘預估
        row3 = QHBoxLayout()
        row3.setSpacing(4)
        lbl3 = QLabel("60分鐘:")
        lbl3.setStyleSheet(label_style)
        row3.addWidget(lbl3)
        self.rate_60min_lbl = QLabel("--")
        self.rate_60min_lbl.setStyleSheet(yellow_style)
        row3.addWidget(self.rate_60min_lbl)
        row3.addStretch()
        layout.addLayout(row3)

        # 預估升級時間
        row_ttl = QHBoxLayout()
        row_ttl.setSpacing(4)
        lbl_ttl = QLabel("升級時間:")
        lbl_ttl.setStyleSheet(label_style)
        row_ttl.addWidget(lbl_ttl)
        self.ttl_lbl = QLabel("--")
        self.ttl_lbl.setStyleSheet(yellow_style)
        row_ttl.addWidget(self.ttl_lbl)
        row_ttl.addStretch()
        layout.addLayout(row_ttl)

        # 底部警告提示行
        self.warning_lbl = QLabel("")
        self.warning_lbl.setStyleSheet(
            f"color: {AppTheme.ACCENT_ORANGE}; font-size: 10px; font-weight: bold;"
            f" padding: 2px 0 0 0;"
        )
        self.warning_lbl.setFixedHeight(16)
        layout.addWidget(self.warning_lbl)

    # ===== 自繪圓角半透明背景 =====

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        radius = AppTheme.CORNER_MD
        rect = QRectF(1, 1, self.width() - 2, self.height() - 2)

        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        # 半透明背景 (alpha ≈ 200/255 ≈ 78%)
        painter.fillPath(path, QBrush(QColor(6, 9, 15, 200)))

        # 藍色邊框
        pen = QPen(QColor(AppTheme.GOLD_PRIMARY), 2)
        painter.setPen(pen)
        painter.drawPath(path)

        painter.end()

    # ===== 數據更新 =====

    def update_data(self, summary: dict) -> None:
        """更新顯示數據

        Args:
            summary: ExpCalculator.get_summary() 的結果
        """
        current = summary.get("current_exp")
        pct = summary.get("current_percentage")
        if current is not None and pct is not None:
            self.exp_value_lbl.setText(f"{current:,}[{pct:.2f}%]")
        elif current is not None:
            self.exp_value_lbl.setText(f"{current:,}")
        else:
            self.exp_value_lbl.setText("--")

        rate_min = summary.get("rate_per_min", 0)
        self.rate_min_lbl.setText(f"+{rate_min:,.0f}")

        rate_10 = summary.get("rate_10min", 0)
        self.rate_10min_lbl.setText(f"+{rate_10:,.0f}")

        rate_60 = summary.get("rate_60min", 0)
        self.rate_60min_lbl.setText(f"+{rate_60:,.0f}")

        ttl = summary.get("time_to_level_min")
        if ttl is not None:
            if ttl >= 60:
                hours = int(ttl) // 60
                mins = int(ttl) % 60
                self.ttl_lbl.setText(f"{hours}小時{mins}分鐘")
            elif ttl < 1:
                self.ttl_lbl.setText("少於1分鐘")
            else:
                self.ttl_lbl.setText(f"{ttl:.0f}分鐘")
        else:
            self.ttl_lbl.setText("--")

    def show_warning(self, text: str):
        """更新底部警告提示（空字串則清除）"""
        self.warning_lbl.setText(text)
        if text == "擷取正常":
            self.warning_lbl.setStyleSheet(
                f"color: {AppTheme.ACCENT_GREEN}; font-size: 10px; font-weight: bold;"
                f" padding: 2px 0 0 0;"
            )
        elif text:
            self.warning_lbl.setStyleSheet(
                f"color: {AppTheme.ACCENT_ORANGE}; font-size: 10px; font-weight: bold;"
                f" padding: 2px 0 0 0;"
            )
        else:
            self.warning_lbl.setStyleSheet(
                f"color: {AppTheme.ACCENT_ORANGE}; font-size: 10px; font-weight: bold;"
                f" padding: 2px 0 0 0;"
            )

    def reset_data(self):
        """重置所有顯示數據"""
        self.exp_value_lbl.setText("--")
        self.rate_min_lbl.setText("--")
        self.rate_10min_lbl.setText("--")
        self.rate_60min_lbl.setText("--")
        self.ttl_lbl.setText("--")
        self.warning_lbl.setText("")

    # ===== 邊緣偵測 =====

    def _in_resize_zone(self, pos: QPoint) -> bool:
        """判斷滑鼠是否在右下角 resize 區域"""
        return (
            pos.x() >= self.width() - _RESIZE_MARGIN
            and pos.y() >= self.height() - _RESIZE_MARGIN
        )

    # ===== 拖曳 & 調整大小 =====

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            if self._in_resize_zone(pos):
                self._resizing = True
                self._resize_start_pos = event.globalPosition().toPoint()
                self._resize_start_size = self.size()
            else:
                self._dragging = True
                self._drag_offset = pos

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()

        if self._resizing:
            delta = event.globalPosition().toPoint() - self._resize_start_pos
            new_w = max(self.minimumWidth(), self._resize_start_size.width() + delta.x())
            new_h = max(self.minimumHeight(), self._resize_start_size.height() + delta.y())
            self.resize(new_w, new_h)
        elif self._dragging:
            new_pos = event.globalPosition().toPoint() - self._drag_offset
            self.move(new_pos)
        else:
            # 更新游標樣式
            if self._in_resize_zone(pos):
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            else:
                self.unsetCursor()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            self._resizing = False
