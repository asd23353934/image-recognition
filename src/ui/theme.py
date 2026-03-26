"""
主題系統 — PySide6 QSS 版本
集中管理所有顏色、字型、尺寸等樣式設定，並提供 QSS 全域樣式表
科技藍主題 — 深色背景、藍色強調
"""

from PySide6.QtGui import QFont


class AppTheme:
    """應用程式主題常量 — 科技藍風格"""

    # ===== 背景色階層（由深到淺）=====
    BG_DARKEST    = "#020408"
    BG_DEEP       = "#060a14"
    BG_PRIMARY    = "#060a14"
    BG_SECONDARY  = "#0d1525"
    BG_TERTIARY   = "#162035"
    BG_CARD       = "#0f1a2e"
    BG_CARD_HOVER = "#162844"

    # ===== 主色調（藍色系）=====
    # 注意: GOLD_* 為歷史命名，實際色值為藍色系
    GOLD_PRIMARY = "#3b82f6"   # 主藍色
    GOLD_LIGHT   = "#93c5fd"   # 淺藍色
    GOLD_DARK    = "#1d4ed8"   # 深藍色
    GOLD_MUTED   = "#1e3a5f"   # 暗藍色

    # ===== 裝飾邊框 =====
    BORDER_GOLD         = "#3b82f6"
    BORDER_GOLD_SUBTLE  = "#1e3a5f"

    # ===== 強調色 =====
    ACCENT_BLUE         = "#3b82f6"
    ACCENT_GREEN        = "#10b981"
    ACCENT_GREEN_HOVER  = "#0d9668"
    ACCENT_YELLOW       = "#fbbf24"
    ACCENT_RED          = "#ef4444"
    ACCENT_RED_HOVER    = "#dc2626"
    ACCENT_ORANGE       = "#fb923c"

    # ===== 文字色 =====
    TEXT_PRIMARY   = "#f1f5f9"
    TEXT_SECONDARY = "#94a3b8"
    TEXT_MUTED     = "#64748b"
    TEXT_GOLD      = "#93c5fd"
    TEXT_HIGHLIGHT = "#ffffff"

    # ===== 字型 =====
    FONT_FAMILY = "Microsoft JhengHei"

    # ===== 圓角 =====
    CORNER_LG = 12
    CORNER_MD = 8
    CORNER_SM = 4

    # ===== 邊框 =====
    BORDER_WIDTH = 2

    @classmethod
    def build_stylesheet(cls) -> str:
        """回傳完整 QSS 全域樣式表字串"""
        return f"""
        QWidget {{
            background-color: {cls.BG_PRIMARY};
            color: {cls.TEXT_PRIMARY};
            font-family: "{cls.FONT_FAMILY}";
            font-size: 12px;
        }}
        QMainWindow {{
            background-color: {cls.BG_PRIMARY};
        }}

        QPushButton {{
            background-color: {cls.BG_TERTIARY};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.GOLD_MUTED};
            border-radius: 4px;
            padding: 2px 8px;
            font-family: "{cls.FONT_FAMILY}";
            font-size: 11px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {cls.BG_SECONDARY};
            border-color: {cls.GOLD_PRIMARY};
            color: {cls.TEXT_HIGHLIGHT};
        }}
        QPushButton:pressed {{
            background-color: {cls.BG_DARKEST};
            border-color: {cls.GOLD_DARK};
        }}
        QPushButton:disabled {{
            color: {cls.TEXT_MUTED};
            border-color: {cls.BG_TERTIARY};
        }}

        QComboBox {{
            background-color: {cls.BG_TERTIARY};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.GOLD_MUTED};
            border-radius: 4px;
            padding: 2px 8px;
            font-family: "{cls.FONT_FAMILY}";
            font-size: 11px;
        }}
        QComboBox:hover {{
            border-color: {cls.GOLD_PRIMARY};
        }}
        QComboBox::drop-down {{
            border: none;
            padding-right: 4px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid {cls.GOLD_PRIMARY};
            width: 0; height: 0;
        }}
        QComboBox QAbstractItemView {{
            background-color: {cls.BG_SECONDARY};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.GOLD_MUTED};
            selection-background-color: {cls.GOLD_DARK};
            selection-color: {cls.TEXT_HIGHLIGHT};
            outline: none;
        }}

        QScrollBar:vertical {{
            background: {cls.BG_SECONDARY};
            width: 8px;
            border-radius: 4px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {cls.BG_TERTIARY};
            border-radius: 4px;
            min-height: 20px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {cls.GOLD_PRIMARY};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0; background: none;
        }}

        QLabel {{
            color: {cls.TEXT_PRIMARY};
            background-color: transparent;
        }}

        QTextEdit {{
            background-color: {cls.BG_SECONDARY};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.GOLD_MUTED};
            border-radius: 4px;
            font-family: "{cls.FONT_FAMILY}";
            font-size: 11px;
        }}

        QTabWidget::pane {{
            border: 1px solid {cls.GOLD_MUTED};
            border-radius: 4px;
            background-color: {cls.BG_PRIMARY};
        }}
        QTabBar::tab {{
            background-color: {cls.BG_TERTIARY};
            color: {cls.TEXT_SECONDARY};
            border: 1px solid {cls.GOLD_MUTED};
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            padding: 6px 16px;
            font-family: "{cls.FONT_FAMILY}";
            font-size: 11px;
            font-weight: bold;
        }}
        QTabBar::tab:selected {{
            background-color: {cls.BG_PRIMARY};
            color: {cls.TEXT_GOLD};
            border-color: {cls.GOLD_PRIMARY};
        }}
        QTabBar::tab:hover:!selected {{
            background-color: {cls.BG_SECONDARY};
            color: {cls.TEXT_PRIMARY};
        }}

        QToolTip {{
            background-color: {cls.BG_SECONDARY};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.GOLD_DARK};
            border-radius: 4px;
            padding: 4px 10px;
            font-family: "{cls.FONT_FAMILY}";
            font-size: 11px;
        }}

        QDialog {{
            background-color: {cls.BG_DEEP};
        }}

        QProgressBar {{
            background-color: {cls.BG_CARD};
            border: 1px solid {cls.GOLD_MUTED};
            border-radius: {cls.CORNER_SM}px;
        }}
        QProgressBar::chunk {{
            background-color: {cls.GOLD_PRIMARY};
            border-radius: {cls.CORNER_SM}px;
        }}
        """

    @classmethod
    def get_font(cls, size: int, bold: bool = False) -> QFont:
        """取得 QFont 物件"""
        f = QFont(cls.FONT_FAMILY, size)
        if bold:
            f.setBold(True)
        return f
