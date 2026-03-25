"""
版本管理
統一管理程式版本號
"""

VERSION = "1.0.0"

CHANGELOG = """
v1.0.0 (2026-03-25)
-------------------
- 初始版本發布
- OCR 經驗值監測功能
- 浮動視窗即時顯示數據
- 自動更新系統
"""


def get_version():
    return VERSION


def get_changelog():
    return CHANGELOG
