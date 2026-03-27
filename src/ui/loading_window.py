"""
啟動載入視窗
取代 QSplashScreen，使其出現在工作管理員「應用程式」區段
"""

from PySide6.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QFont

from src.ui.theme import AppTheme
from src.ui.helpers import resource_path


class LoadingWindow(QWidget):
    """啟動時的載入視窗，有標題列和關閉按鈕"""

    def __init__(self):
        super().__init__()
        self._loading_complete = False

        self.setWindowTitle("Image Recognition")
        self.setFixedSize(400, 200)
        self.setWindowFlags(
            Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint
        )
        self.setWindowIcon(QIcon(resource_path("icon.ico")))

        # 深色背景 + 藍色邊框
        self.setStyleSheet(f"""
            LoadingWindow {{
                background-color: {AppTheme.BG_DEEP};
                border: 1px solid {AppTheme.GOLD_PRIMARY};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 標題
        title = QLabel("Image Recognition")
        title.setFont(QFont("Microsoft JhengHei", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {AppTheme.TEXT_GOLD}; border: none;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(12)

        # 載入提示
        hint = QLabel("正在載入辨識引擎...")
        hint.setFont(QFont("Microsoft JhengHei", 11))
        hint.setStyleSheet(f"color: {AppTheme.TEXT_SECONDARY}; border: none;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

        # 置中螢幕
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(
                geo.center().x() - self.width() // 2,
                geo.center().y() - self.height() // 2,
            )

    def mark_complete(self):
        """載入完成，允許正常關閉"""
        self._loading_complete = True
        self.close()

    def closeEvent(self, event):
        if not self._loading_complete:
            QApplication.quit()
        event.accept()
