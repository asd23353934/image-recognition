"""
工具函數模組
提供通用的輔助函數
"""

import os
import sys


def resource_path(relative_path):
    """獲取資源文件路徑（支援 PyInstaller 打包）"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def user_path(relative_path):
    """取得使用者可寫入的資料路徑（支援 PyInstaller 打包）

    打包模式使用 exe 所在目錄；開發模式使用專案根目錄。
    """
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.abspath(".")
    return os.path.join(base, relative_path)


def darken_color(hex_color, factor=0.8):
    """將顏色變暗"""
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    r = max(0, int(r * factor))
    g = max(0, int(g * factor))
    b = max(0, int(b * factor))
    return f'#{r:02x}{g:02x}{b:02x}'


def lighten_color(hex_color, factor=1.2):
    """將顏色變亮"""
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    r = min(255, int(r * factor))
    g = min(255, int(g * factor))
    b = min(255, int(b * factor))
    return f'#{r:02x}{g:02x}{b:02x}'
