"""
Image Recognition
主程式入口
"""

import sys
import os

# 添加專案根目錄到路徑
sys.path.insert(0, os.path.dirname(__file__))


def main():
    """主程式"""
    # Qt 6 已自動設定 DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2，無需手動呼叫

    from PySide6.QtWidgets import QApplication
    from src.ui.app import App
    from src.ui.theme import AppTheme

    qt_app = QApplication(sys.argv)
    qt_app.setStyleSheet(AppTheme.build_stylesheet())

    window = App()
    sys.exit(qt_app.exec())


if __name__ == "__main__":
    main()
