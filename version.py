"""
版本管理
統一管理程式版本號
"""

VERSION = "1.2.0"

CHANGELOG = """
v1.2.0 (2026-03-27)
-------------------
改進:
- 載入視窗改為正式視窗，出現在工作管理員「應用程式」區段，可直接關閉
- 抑制 PaddlePaddle/PaddleOCR 第三方套件警告與雜訊日誌
- 啟動加速：App import 與 OCR 預載並行執行
- 啟動加速：numpy/PIL 延遲至 OCR 引擎首次載入時才 import
- 啟動加速：FloatWindow 延遲至首次使用時才建立
- 打包後自動壓縮為 zip（含版本號），使用獨立 zip_release.py 腳本

v1.1.0 (2026-03-26)
-------------------
新功能:
- 啟動畫面 (Splash Screen) + OCR 背景預載
- 單一實例檢查，防止重複開啟
- SQLite 紀錄儲存系統，支援保存/查詢歷史紀錄
- 歷史紀錄對話框
- EXP 折線圖表
- 浮動視窗新增 10 分鐘速率顯示與底部狀態提示
- 視窗選單自動重新整理
- 設定自動保存/還原（視窗選擇與監測區域）

改進:
- 主題從 RPG 金色風格改為科技藍風格
- 對話框改為無邊框簡潔風格
- 經驗值計算器重寫：跨升級持續累計
- OCR 架構調整：截圖在主執行緒、辨識在工作者執行緒
- PyInstaller 打包修補（Paddle DLL、subprocess、paddlex 依賴）
- 建置輸出從 exp_monitor 改名為 image_recognition

修正:
- 修正自動更新 GitHub repo URL 錯誤
- 修正日誌顯示 HTML injection 問題
- 修正區域選取遮罩記憶體洩漏
- OCR 語言設定改為從 config.json 讀取
- 監測期間自動偵測目標視窗關閉並暫停
- 浮動視窗新增最大尺寸限制
- 更新 .gitignore 排除執行時資料庫

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
