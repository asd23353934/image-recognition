"""
Image Recognition
主程式入口
"""

import sys
import os
import threading
import warnings
import logging

# 添加專案根目錄到路徑
sys.path.insert(0, os.path.dirname(__file__))

# 抑制第三方套件警告與日誌
os.environ.setdefault("GLOG_minloglevel", "3")        # 隱藏 PaddlePaddle C++ glog (INFO/WARNING/oneDNN)
os.environ.setdefault("FLAGS_logtostderr", "0")        # 不輸出 glog 到 stderr
os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
warnings.filterwarnings("ignore", message="urllib3.*chardet.*charset_normalizer")  # requests 版本警告
warnings.filterwarnings("ignore", message="No ccache found")                       # paddle ccache 提示
logging.getLogger("paddlex").setLevel(logging.ERROR)   # 隱藏 paddlex Creating model 等 info
logging.getLogger("paddleocr").setLevel(logging.ERROR)


# 過濾 paddlex 透過 root logger 輸出的 Connectivity check 訊息
class _PaddleLogFilter(logging.Filter):
    _BLOCKED = ("Connectivity check",)

    def filter(self, record):
        msg = record.getMessage()
        return not any(k in msg for k in self._BLOCKED)


logging.getLogger().addFilter(_PaddleLogFilter())

# PyInstaller 打包環境修補
if getattr(sys, 'frozen', False) and sys.platform == 'win32':
    # 將 paddle DLL 路徑加入搜尋路徑
    _paddle_libs = os.path.join(sys._MEIPASS, "paddle", "libs")
    if os.path.isdir(_paddle_libs):
        os.environ["PATH"] = _paddle_libs + os.pathsep + os.environ.get("PATH", "")
        os.add_dll_directory(_paddle_libs)

    import ctypes
    # 隱藏 console（如果存在的話）
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE

    # 讓所有 subprocess 預設使用 CREATE_NO_WINDOW
    import subprocess
    _original_popen_init = subprocess.Popen.__init__

    def _patched_popen_init(self, *args, **kwargs):
        if sys.platform == 'win32' and 'creationflags' not in kwargs:
            kwargs['creationflags'] = (
                subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
            )
        _original_popen_init(self, *args, **kwargs)

    subprocess.Popen.__init__ = _patched_popen_init

    # 繞過 paddlex 依賴檢查（必須在 import paddleocr/paddlex 之前執行）
    # PyInstaller 環境下 importlib.metadata.version() 無法偵測已打包的套件，
    # 導致模組載入時 `if is_dep_available(...): import cv2` 等判斷失敗
    # 使用底層 patch，避免 import paddlex 觸發 import chain
    import importlib.metadata as _meta
    import importlib.util as _util
    _original_version = _meta.version

    # 套件名稱 → 實際 import 名稱的對應表
    _PKG_IMPORT_MAP = {
        "opencv-contrib-python": "cv2",
        "opencv-python": "cv2",
        "pillow": "PIL",
        "python-bidi": "bidi",
        "scikit-learn": "sklearn",
    }

    def _patched_version(name):
        try:
            return _original_version(name)
        except _meta.PackageNotFoundError:
            # 只對「模組確實存在但 metadata 遺失」的套件回傳假版本
            import_name = _PKG_IMPORT_MAP.get(name, name.replace("-", "_"))
            if _util.find_spec(import_name) is not None:
                return "0.0.0"
            raise

    _meta.version = _patched_version


def main():
    """主程式"""
    # 單一實例檢查（Windows Mutex）
    if sys.platform == 'win32':
        import ctypes
        _mutex = ctypes.windll.kernel32.CreateMutexW(None, True, "ImageRecognition_SingleInstance")
        if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            ctypes.windll.user32.MessageBoxW(
                None, "應用程式已在執行中。", "Image Recognition", 0x40  # MB_ICONINFORMATION
            )
            return

    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer

    from src.ui.theme import AppTheme
    from src.core.ocr_engine import OcrEngine
    from src.ui.loading_window import LoadingWindow

    qt_app = QApplication(sys.argv)
    qt_app.setStyleSheet(AppTheme.build_stylesheet())

    # 建立載入視窗（取代 QSplashScreen，可在工作管理員中關閉）
    loading_window = LoadingWindow()
    loading_window.show()
    qt_app.processEvents()

    # 讀取 OCR 語言設定
    import json
    ocr_lang = "ch"
    try:
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        with open(config_path, "r", encoding="utf-8") as f:
            ocr_lang = json.load(f).get("settings", {}).get("ocr_lang", "ch")
    except Exception:
        pass

    # 背景預載 OCR 引擎
    ocr_engine = OcrEngine(lang=ocr_lang)
    engine_ready = threading.Event()
    engine_error = [None]  # 用 list 包裝以便在閉包中賦值

    def _preload():
        try:
            # 暫時重導 stderr (OS fd + Python) 以隱藏 findstr/paddle C++ 雜訊
            _orig_fd = os.dup(2)
            _devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(_devnull, 2)
            os.close(_devnull)
            _orig_stderr = sys.stderr
            sys.stderr = open(os.devnull, "w")
            try:
                ocr_engine.preload()
            finally:
                sys.stderr.close()
                sys.stderr = _orig_stderr
                os.dup2(_orig_fd, 2)
                os.close(_orig_fd)
        except Exception as e:
            engine_error[0] = str(e)
        engine_ready.set()

    threading.Thread(target=_preload, daemon=True).start()

    # 並行預先 import App（其 import chain 含 numpy/PIL/mss 等較重模組）
    _app_cls = [None]

    def _import_app():
        from src.ui.app import App
        _app_cls[0] = App

    _import_thread = threading.Thread(target=_import_app, daemon=True)
    _import_thread.start()

    # 保持主視窗參考，避免被 GC 回收
    window = None

    def _check_ready():
        nonlocal window
        if engine_ready.is_set():
            _import_thread.join()  # 確保 import 完成（通常已完成）
            App = _app_cls[0]
            window = App(ocr_engine=ocr_engine)
            loading_window.mark_complete()
            if engine_error[0]:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    window, "引擎載入警告",
                    f"OCR 辨識引擎載入失敗，辨識功能可能無法使用。\n\n錯誤: {engine_error[0]}",
                )
        else:
            QTimer.singleShot(100, _check_ready)

    QTimer.singleShot(100, _check_ready)

    sys.exit(qt_app.exec())


if __name__ == "__main__":
    main()
