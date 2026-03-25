"""
視窗選擇對話框
列出可見應用程式視窗供使用者選取
"""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QWidget,
)
from PySide6.QtCore import Qt

from src.ui.dialogs.base_dialog import BaseDialog
from src.ui.theme import AppTheme
from src.core.window_enumerator import list_windows


class WindowSelectDialog(BaseDialog):
    """視窗選擇對話框"""

    def __init__(self, parent):
        super().__init__(parent, "選擇監測視窗", 500, 400)
        self.selected_hwnd = None
        self.selected_title = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self.inner)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # 標題
        title_lbl = QLabel("選擇要監測的應用程式視窗")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet(
            f"color: {AppTheme.TEXT_GOLD}; font-size: 14px; font-weight: bold;"
            f" background: transparent; border: none;"
        )
        layout.addWidget(title_lbl)

        # 視窗列表
        self.window_list = QListWidget()
        self.window_list.setStyleSheet(
            f"QListWidget {{"
            f" background-color: {AppTheme.BG_SECONDARY};"
            f" border: 1px solid {AppTheme.GOLD_MUTED};"
            f" border-radius: 4px;"
            f" color: {AppTheme.TEXT_PRIMARY};"
            f"}}"
            f"QListWidget::item {{"
            f" padding: 6px 8px;"
            f" border-radius: 3px;"
            f"}}"
            f"QListWidget::item:selected {{"
            f" background-color: {AppTheme.GOLD_DARK};"
            f" color: #000000;"
            f"}}"
            f"QListWidget::item:hover {{"
            f" background-color: {AppTheme.BG_TERTIARY};"
            f"}}"
        )
        self.window_list.itemDoubleClicked.connect(self._on_confirm)
        layout.addWidget(self.window_list)

        # 重新整理 + 按鈕列
        btn_row = QWidget()
        btn_row.setStyleSheet("background: transparent;")
        br = QHBoxLayout(btn_row)
        br.setContentsMargins(0, 0, 0, 0)
        br.setSpacing(8)

        refresh_btn = QPushButton("重新整理")
        refresh_btn.setFixedHeight(32)
        refresh_btn.clicked.connect(self._refresh_windows)
        br.addWidget(refresh_btn)

        br.addStretch()

        confirm_btn = QPushButton("確認")
        confirm_btn.setFixedSize(100, 32)
        confirm_btn.clicked.connect(self._on_confirm)
        confirm_btn.setStyleSheet(
            f"QPushButton {{ background-color: {AppTheme.GOLD_PRIMARY};"
            f" color: {AppTheme.BG_DEEP}; border: 1px solid {AppTheme.GOLD_DARK};"
            f" border-radius: 4px; font-weight: bold; }}"
            f"QPushButton:hover {{ background-color: {AppTheme.GOLD_LIGHT}; }}"
        )
        br.addWidget(confirm_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(80, 32)
        cancel_btn.clicked.connect(self.close)
        br.addWidget(cancel_btn)

        layout.addWidget(btn_row)

        # 初始載入
        self._refresh_windows()

    def _refresh_windows(self):
        """重新列舉可見視窗"""
        self.window_list.clear()
        windows = list_windows()
        for w in windows:
            item = QListWidgetItem(f"[{w['hwnd']}] {w['title']}")
            item.setData(Qt.ItemDataRole.UserRole, w)
            self.window_list.addItem(item)

    def _on_confirm(self):
        """確認選擇"""
        current = self.window_list.currentItem()
        if not current:
            return
        data = current.data(Qt.ItemDataRole.UserRole)
        self.selected_hwnd = data["hwnd"]
        self.selected_title = data["title"]
        self.accept()
