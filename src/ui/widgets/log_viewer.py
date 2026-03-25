"""
日誌顯示元件
顯示帶時間戳的日誌訊息
"""

from datetime import datetime

from PySide6.QtWidgets import QTextEdit
from PySide6.QtCore import Qt

from src.ui.theme import AppTheme


class LogViewer(QTextEdit):
    """時間戳日誌顯示器"""

    MAX_LINES = 500

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMinimumHeight(100)
        self.setStyleSheet(
            f"QTextEdit {{"
            f" background-color: {AppTheme.BG_SECONDARY};"
            f" color: {AppTheme.TEXT_PRIMARY};"
            f" border: 1px solid {AppTheme.GOLD_MUTED};"
            f" border-radius: {AppTheme.CORNER_SM}px;"
            f" font-family: 'Consolas', 'Microsoft JhengHei';"
            f" font-size: 11px;"
            f" padding: 4px;"
            f"}}"
        )
        self._line_count = 0

    def append_log(self, message: str) -> None:
        """新增帶時間戳的日誌訊息

        Args:
            message: 日誌文字
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        colored_line = (
            f'<span style="color:{AppTheme.TEXT_MUTED}">[{timestamp}]</span> '
            f'<span style="color:{AppTheme.TEXT_PRIMARY}">{message}</span>'
        )
        self.append(colored_line)
        self._line_count += 1

        # 限制行數，避免記憶體增長
        if self._line_count > self.MAX_LINES:
            self._trim_lines()

        # 自動捲動到底部
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _trim_lines(self):
        """移除最舊的行"""
        cursor = self.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        # 刪除前 100 行
        for _ in range(100):
            cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        cursor.deleteChar()  # 刪除多餘的換行
        self._line_count -= 100

    def clear_log(self) -> None:
        """清除所有日誌"""
        self.clear()
        self._line_count = 0
