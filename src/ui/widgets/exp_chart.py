"""
經驗值獲取量折線圖 — 使用 QPainter 自繪
顯示每段時間的經驗獲取量（相鄰讀數差值）
"""

from datetime import datetime

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QPainterPath

from src.ui.theme import AppTheme


class ExpChart(QWidget):
    """EXP 獲取量折線圖"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 200)
        self._readings: list[dict] = []
        self._gains: list[dict] = []  # {timestamp, gain}
        self._margins = {"left": 80, "right": 20, "top": 20, "bottom": 40}
        self._hover_index: int | None = None
        self.setMouseTracking(True)

    def set_readings(self, readings: list[dict]) -> None:
        self._readings = readings
        self._gains = self._compute_gains(readings)
        self._hover_index = None
        self.update()

    def clear(self) -> None:
        self._readings = []
        self._gains = []
        self._hover_index = None
        self.update()

    @staticmethod
    def _compute_gains(readings: list[dict]) -> list[dict]:
        """計算相鄰讀數間的經驗獲取量（含第一筆 gain=0）"""
        gains = []
        if not readings:
            return gains
        # 第一筆：時間 0，獲取量 0
        gains.append({
            "timestamp": readings[0]["timestamp"],
            "gain": 0,
            "exp_value": readings[0]["exp_value"],
            "percentage": readings[0]["percentage"],
        })
        for i in range(1, len(readings)):
            gain = readings[i]["exp_value"] - readings[i - 1]["exp_value"]
            gains.append({
                "timestamp": readings[i]["timestamp"],
                "gain": max(gain, 0),  # 忽略負值（異常）
                "exp_value": readings[i]["exp_value"],
                "percentage": readings[i]["percentage"],
            })
        return gains

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Background
        painter.fillRect(0, 0, w, h, QColor(AppTheme.BG_SECONDARY))
        painter.setPen(QPen(QColor(AppTheme.GOLD_MUTED), 1))
        painter.drawRect(0, 0, w - 1, h - 1)

        m = self._margins
        plot_l = m["left"]
        plot_r = w - m["right"]
        plot_t = m["top"]
        plot_b = h - m["bottom"]
        plot_w = plot_r - plot_l
        plot_h = plot_b - plot_t

        if len(self._gains) < 1 or plot_w <= 0 or plot_h <= 0:
            painter.setPen(QColor(AppTheme.TEXT_MUTED))
            painter.setFont(AppTheme.get_font(14))
            painter.drawText(QRectF(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, "尚無數據")
            painter.end()
            return

        timestamps = [g["timestamp"] for g in self._gains]
        values = [g["gain"] for g in self._gains]
        t_min, t_max = timestamps[0], timestamps[-1]
        v_min = 0  # 獲取量從 0 開始
        v_max = max(values) if values else 1

        # Add padding to y range
        if v_max == 0:
            v_max = 1
        v_max *= 1.1
        v_range = v_max - v_min

        t_range = t_max - t_min
        if t_range == 0:
            t_range = 1

        def to_px(t: float, v: float) -> QPointF:
            x = plot_l + (t - t_min) / t_range * plot_w
            y = plot_b - (v - v_min) / v_range * plot_h
            return QPointF(x, y)

        # Grid lines (horizontal)
        painter.setFont(AppTheme.get_font(9))
        grid_pen = QPen(QColor(AppTheme.BG_TERTIARY), 1, Qt.PenStyle.DashLine)
        label_color = QColor(AppTheme.TEXT_MUTED)
        for i in range(5):
            frac = i / 4
            v = v_min + frac * v_range
            y = plot_b - frac * plot_h
            painter.setPen(grid_pen)
            painter.drawLine(QPointF(plot_l, y), QPointF(plot_r, y))
            painter.setPen(label_color)
            painter.drawText(
                QRectF(0, y - 10, plot_l - 5, 20),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                f"+{int(v):,}",
            )

        # X-axis labels
        label_count = min(6, len(self._gains))
        for i in range(label_count):
            idx = int(i / (label_count - 1) * (len(timestamps) - 1)) if label_count > 1 else 0
            t = timestamps[idx]
            x = to_px(t, v_min).x()
            time_str = datetime.fromtimestamp(t).strftime("%H:%M:%S")
            painter.setPen(label_color)
            painter.drawText(
                QRectF(x - 35, plot_b + 5, 70, 20),
                Qt.AlignmentFlag.AlignCenter,
                time_str,
            )

        # Data line
        line_pen = QPen(QColor(AppTheme.ACCENT_GREEN), 2)
        painter.setPen(line_pen)
        points = [to_px(timestamps[i], values[i]) for i in range(len(self._gains))]

        # Downsample for performance if too many points
        if len(points) > 500:
            step = len(points) // 500
            sampled = [points[i] for i in range(0, len(points), step)]
            if points[-1] != sampled[-1]:
                sampled.append(points[-1])
            draw_points = sampled
        else:
            draw_points = points

        path = QPainterPath()
        path.moveTo(draw_points[0])
        for pt in draw_points[1:]:
            path.lineTo(pt)
        painter.drawPath(path)

        # Data points (only if not too many)
        if len(points) <= 200:
            dot_brush = QBrush(QColor(AppTheme.GOLD_LIGHT))
            painter.setBrush(dot_brush)
            painter.setPen(Qt.PenStyle.NoPen)
            for pt in points:
                painter.drawEllipse(pt, 3, 3)

        # Hover tooltip
        if self._hover_index is not None and 0 <= self._hover_index < len(points):
            idx = self._hover_index
            pt = points[idx]
            g = self._gains[idx]

            # Highlight point
            painter.setBrush(QBrush(QColor(AppTheme.ACCENT_YELLOW)))
            painter.setPen(QPen(QColor(AppTheme.TEXT_HIGHLIGHT), 1))
            painter.drawEllipse(pt, 5, 5)

            # Tooltip box
            time_str = datetime.fromtimestamp(g["timestamp"]).strftime("%H:%M:%S")
            tip_text = f"獲取: +{g['gain']:,}\nEXP: {g['exp_value']:,}\n{g['percentage']:.2f}%\n{time_str}"
            painter.setFont(AppTheme.get_font(10))
            fm = painter.fontMetrics()
            lines = tip_text.split("\n")
            tip_w = max(fm.horizontalAdvance(l) for l in lines) + 16
            tip_h = fm.height() * len(lines) + 12

            tip_x = pt.x() + 10
            tip_y = pt.y() - tip_h - 5
            if tip_x + tip_w > w:
                tip_x = pt.x() - tip_w - 10
            if tip_y < 0:
                tip_y = pt.y() + 10

            painter.setBrush(QBrush(QColor(AppTheme.BG_CARD)))
            painter.setPen(QPen(QColor(AppTheme.GOLD_PRIMARY), 1))
            painter.drawRoundedRect(QRectF(tip_x, tip_y, tip_w, tip_h), 4, 4)

            painter.setPen(QColor(AppTheme.TEXT_PRIMARY))
            for i, line in enumerate(lines):
                painter.drawText(
                    QRectF(tip_x + 8, tip_y + 6 + fm.height() * i, tip_w - 16, fm.height()),
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    line,
                )

        painter.end()

    def mouseMoveEvent(self, event):
        if len(self._gains) < 1:
            return

        pos = event.position()
        m = self._margins
        plot_l = m["left"]
        plot_r = self.width() - m["right"]
        plot_w = plot_r - plot_l

        if plot_w <= 0:
            return

        timestamps = [g["timestamp"] for g in self._gains]
        t_min, t_max = timestamps[0], timestamps[-1]
        t_range = t_max - t_min if t_max != t_min else 1

        # Find nearest point by x
        mouse_t = t_min + (pos.x() - plot_l) / plot_w * t_range
        best_idx = 0
        best_dist = abs(timestamps[0] - mouse_t)
        for i in range(1, len(timestamps)):
            d = abs(timestamps[i] - mouse_t)
            if d < best_dist:
                best_dist = d
                best_idx = i

        if self._hover_index != best_idx:
            self._hover_index = best_idx
            self.update()

    def leaveEvent(self, event):
        if self._hover_index is not None:
            self._hover_index = None
            self.update()
