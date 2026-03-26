"""
主應用程式視窗
QMainWindow 框架 + QTabWidget 多頁面
"""

import os
import sys
import threading

from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QVBoxLayout, QWidget, QApplication,
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QIcon

from src.ui.helpers import resource_path, user_path
from src.ui.theme import AppTheme
from src.ui.config_manager import ConfigManager
from src.ui.toast import ToastManager
from src.core.record_storage import RecordStorage
from src.ui.pages.exp_monitor_page import ExpMonitorPage


class _Dispatcher(QObject):
    """執行緒安全回調調度器"""

    _call = Signal(object)

    def __init__(self, parent):
        super().__init__(parent)
        self._call.connect(self._dispatch, Qt.ConnectionType.QueuedConnection)

    def schedule(self, ms: int, func):
        if ms == 0:
            self._call.emit(func)
        else:
            self._call.emit(lambda: QTimer.singleShot(ms, func))

    def _dispatch(self, func):
        func()


class App(QMainWindow):
    """主應用程式視窗"""

    def __init__(self, ocr_engine=None):
        super().__init__()

        self.setWindowTitle("Image Recognition")
        self.setMinimumSize(800, 600)
        self.resize(800, 600)

        # 設定視窗圖示
        try:
            icon_path = resource_path("icon.ico")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass

        # 管理器
        self._dispatcher = _Dispatcher(self)
        self.config_manager = ConfigManager(user_path("config.json"))
        self.toast_manager = ToastManager(self)
        self.record_storage = RecordStorage(user_path("records.db"))
        self._ocr_engine = ocr_engine

        # 建構 UI
        self._build_ui()

        # 啟動時檢查更新
        QTimer.singleShot(1000, self._check_for_updates)

        self.show()

    def _build_ui(self):
        """建構主 UI"""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Tab 頁面
        self._tabs = QTabWidget()
        layout.addWidget(self._tabs)

        # 經驗值監測頁
        self._exp_page = ExpMonitorPage(
            self, storage=self.record_storage, config_manager=self.config_manager,
            ocr_engine=self._ocr_engine,
        )
        self._tabs.addTab(self._exp_page, "經驗值監測")

    def after(self, ms: int, func):
        """執行緒安全的延遲執行"""
        self._dispatcher.schedule(ms, func)

    # ===== 自動更新 =====

    def _check_for_updates(self):
        """背景檢查更新"""
        def _worker():
            try:
                from src.core.updater import Updater
                updater = Updater()
                result = updater.check_for_updates()
                if result.get("available"):
                    self.after(0, lambda: self._on_update_found(result))
            except Exception:
                pass

        threading.Thread(target=_worker, daemon=True).start()

    def _on_update_found(self, update_info):
        """發現新版本"""
        from src.ui.dialogs.update_dialog import UpdateDialog
        dialog = UpdateDialog(self, update_info)
        dialog.exec()

    # ===== 關閉 =====

    def closeEvent(self, event):
        """關閉視窗時清理資源"""
        self._exp_page.cleanup()
        self.record_storage.close()
        self.config_manager.save()
        event.accept()
