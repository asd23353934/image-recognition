"""
經驗值監測頁面
主功能頁面：選擇視窗 → 選取區域 → OCR 監測 → 速率推算
"""

import logging
import threading

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFrame,
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QObject

from src.core.ocr_engine import OcrEngine, ExpResult
from src.core.screen_capture import ScreenCapture
from src.core.exp_calculator import ExpCalculator
from src.core.record_storage import RecordStorage
from src.core.window_enumerator import list_windows, get_window_rect, is_window_valid
from src.ui.theme import AppTheme
from src.ui.widgets.capture_preview import CapturePreview
from src.ui.widgets.log_viewer import LogViewer
from src.ui.widgets.region_overlay import RegionOverlay
from src.ui.widgets.float_window import FloatWindow

logger = logging.getLogger(__name__)


class OcrWorker(QObject):
    """OCR 背景工作者 — 在 QThread 中執行"""

    result_ready = Signal(object, object, str)  # (PIL.Image, ExpResult|None, raw_text)
    error_occurred = Signal(str)
    engine_loaded = Signal()  # OCR 引擎載入完成
    trigger = Signal(object)  # 觸發 OCR（傳入已截圖的 PIL.Image）

    def __init__(self, ocr: OcrEngine):
        super().__init__()
        self.ocr = ocr
        self._running = False
        self.trigger.connect(self.do_ocr)

    def do_ocr(self, img):
        """執行 OCR（在工作者執行緒中）"""
        try:
            was_loaded = self.ocr.is_loaded()
            result, raw_text = self.ocr.recognize_exp_format(img)
            if not was_loaded and self.ocr.is_loaded():
                self.engine_loaded.emit()
            self.result_ready.emit(img, result, raw_text)
        except Exception as e:
            self.error_occurred.emit(str(e))


class ExpMonitorPage(QWidget):
    """經驗值監測頁面"""

    exp_updated = Signal(dict)  # 供浮動視窗使用

    def __init__(self, parent=None, storage: RecordStorage | None = None,
                 config_manager=None, ocr_engine: OcrEngine | None = None):
        super().__init__(parent)

        # 核心元件
        self._ocr = ocr_engine or OcrEngine()
        self._capture = ScreenCapture()
        self._calculator = ExpCalculator()
        self._storage = storage
        self._config = config_manager

        # 狀態
        self._selected_hwnd = None
        self._selected_title = None
        self._capture_bbox = None
        self._is_monitoring = False
        self._is_processing = False

        # OCR 工作者執行緒（mss 截圖在主執行緒，OCR 在工作者執行緒）
        self._worker_thread = QThread()
        self._worker = OcrWorker(self._ocr)
        self._worker.moveToThread(self._worker_thread)
        self._worker.result_ready.connect(self._on_ocr_result)
        self._worker.error_occurred.connect(self._on_ocr_error)
        self._worker.engine_loaded.connect(self._on_engine_loaded)
        self._worker_thread.start()

        # 監測計時器
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._do_capture_cycle)

        # 浮動視窗
        self._float_window = FloatWindow()

        # 遮罩參考
        self._overlay = None

        self._build_ui()
        self._restore_settings()

    def _build_ui(self):
        """建構 UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 8, 12, 8)
        main_layout.setSpacing(8)

        # ===== 視窗選擇區 =====
        select_row = QHBoxLayout()
        select_row.setSpacing(8)

        select_label = QLabel("目標視窗:")
        select_label.setStyleSheet(f"color: {AppTheme.TEXT_SECONDARY}; font-size: 12px;")
        select_row.addWidget(select_label)

        self._window_combo = QComboBox()
        self._window_combo.setMinimumWidth(300)
        self._window_combo.setFixedHeight(28)
        select_row.addWidget(self._window_combo, 1)

        original_show_popup = self._window_combo.showPopup
        def _auto_refresh_popup():
            self._refresh_windows()
            original_show_popup()
        self._window_combo.showPopup = _auto_refresh_popup

        self._region_btn = QPushButton("選取監測區域")
        self._region_btn.setFixedHeight(28)
        self._region_btn.clicked.connect(self._show_region_selector)
        self._region_btn.setEnabled(False)
        select_row.addWidget(self._region_btn)

        # 擷取間隔選擇
        interval_label = QLabel("擷取間隔:")
        interval_label.setStyleSheet(f"color: {AppTheme.TEXT_SECONDARY}; font-size: 12px;")
        select_row.addWidget(interval_label)

        self._interval_combo = QComboBox()
        self._interval_combo.setFixedHeight(28)
        self._interval_combo.setFixedWidth(80)
        for text, ms in [("1 秒", 1000), ("2 秒", 2000), ("3 秒", 3000), ("5 秒", 5000), ("10 秒", 10000)]:
            self._interval_combo.addItem(text, ms)
        self._interval_combo.setCurrentIndex(1)  # 預設 2 秒
        select_row.addWidget(self._interval_combo)

        main_layout.addLayout(select_row)

        # ===== 主內容區 =====
        self._preview = CapturePreview()
        main_layout.addWidget(self._preview)

        # Loading 提示
        self._loading_label = QLabel("正在載入辨識引擎，請稍候...")
        self._loading_label.setStyleSheet(
            f"color: {AppTheme.ACCENT_YELLOW}; font-size: 12px; font-weight: bold;"
            f" background-color: rgba(251, 191, 36, 0.1);"
            f" border: 1px solid {AppTheme.ACCENT_YELLOW};"
            f" border-radius: 4px; padding: 6px 12px;"
        )
        self._loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._loading_label.hide()
        main_layout.addWidget(self._loading_label)

        # 數據顯示區
        data_group = QFrame()
        data_group.setObjectName("data_group")
        data_group.setStyleSheet(
            f"QFrame#data_group {{"
            f" background-color: {AppTheme.BG_SECONDARY};"
            f" border: 1px solid {AppTheme.GOLD_MUTED};"
            f" border-radius: {AppTheme.CORNER_MD}px;"
            f"}}"
        )
        data_layout = QVBoxLayout(data_group)
        data_layout.setSpacing(6)
        data_layout.setContentsMargins(12, 10, 12, 10)

        label_style = f"color: {AppTheme.TEXT_SECONDARY}; font-size: 12px;"
        value_style = f"color: {AppTheme.TEXT_HIGHLIGHT}; font-size: 16px; font-weight: bold;"

        # 格式異常警告
        self._warning_label = QLabel("")
        self._warning_label.setStyleSheet(
            f"color: {AppTheme.ACCENT_ORANGE}; font-size: 12px; font-weight: bold;"
            f" background-color: rgba(251, 146, 60, 0.1);"
            f" border: 1px solid {AppTheme.ACCENT_ORANGE};"
            f" border-radius: 4px; padding: 4px 8px;"
        )
        self._warning_label.setWordWrap(True)
        self._warning_label.hide()
        data_layout.addWidget(self._warning_label)

        # 當前經驗值
        row1 = QHBoxLayout()
        row1.addWidget(self._make_label("當前經驗值:", label_style))
        self._exp_label = QLabel("--")
        self._exp_label.setStyleSheet(value_style)
        row1.addWidget(self._exp_label)
        row1.addStretch()
        data_layout.addLayout(row1)

        # 已累計
        row2 = QHBoxLayout()
        row2.addWidget(self._make_label("已累計:", label_style))
        self._gained_label = QLabel("--")
        self._gained_label.setStyleSheet(
            f"color: {AppTheme.ACCENT_GREEN}; font-size: 14px; font-weight: bold;"
        )
        row2.addWidget(self._gained_label)
        row2.addStretch()
        data_layout.addLayout(row2)

        # 每分鐘預估
        row_min = QHBoxLayout()
        row_min.addWidget(self._make_label("每分鐘預估:", label_style))
        self._rate_min_label = QLabel("--")
        self._rate_min_label.setStyleSheet(
            f"color: {AppTheme.ACCENT_GREEN}; font-size: 14px; font-weight: bold;"
        )
        row_min.addWidget(self._rate_min_label)
        row_min.addStretch()
        data_layout.addLayout(row_min)

        # 10 分鐘預估
        row3 = QHBoxLayout()
        row3.addWidget(self._make_label("10 分鐘預估:", label_style))
        self._rate10_label = QLabel("--")
        self._rate10_label.setStyleSheet(
            f"color: {AppTheme.ACCENT_GREEN}; font-size: 14px; font-weight: bold;"
        )
        row3.addWidget(self._rate10_label)
        row3.addStretch()
        data_layout.addLayout(row3)

        # 60 分鐘預估
        row4 = QHBoxLayout()
        row4.addWidget(self._make_label("60 分鐘預估:", label_style))
        self._rate60_label = QLabel("--")
        self._rate60_label.setStyleSheet(
            f"color: {AppTheme.ACCENT_YELLOW}; font-size: 14px; font-weight: bold;"
        )
        row4.addWidget(self._rate60_label)
        row4.addStretch()
        data_layout.addLayout(row4)

        # 預估升級時間
        row_ttl = QHBoxLayout()
        row_ttl.addWidget(self._make_label("預估升級時間:", label_style))
        self._ttl_label = QLabel("--")
        self._ttl_label.setStyleSheet(
            f"color: {AppTheme.ACCENT_YELLOW}; font-size: 14px; font-weight: bold;"
        )
        row_ttl.addWidget(self._ttl_label)
        row_ttl.addStretch()
        data_layout.addLayout(row_ttl)

        # 監測時長
        row5 = QHBoxLayout()
        row5.addWidget(self._make_label("監測時長:", label_style))
        self._elapsed_label = QLabel("--")
        self._elapsed_label.setStyleSheet(
            f"color: {AppTheme.TEXT_SECONDARY}; font-size: 12px;"
        )
        row5.addWidget(self._elapsed_label)
        row5.addStretch()
        data_layout.addLayout(row5)

        main_layout.addWidget(data_group, 1)

        # 控制按鈕
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self._start_btn = QPushButton("開始")
        self._start_btn.setFixedHeight(36)
        self._start_btn.setEnabled(False)
        self._start_btn.clicked.connect(self._on_start)
        self._start_btn.setStyleSheet(
            f"QPushButton {{ background-color: {AppTheme.ACCENT_GREEN};"
            f" color: #ffffff; border: 1px solid {AppTheme.ACCENT_GREEN_HOVER};"
            f" border-radius: 4px; font-weight: bold; font-size: 12px; }}"
            f"QPushButton:hover {{ background-color: {AppTheme.ACCENT_GREEN_HOVER}; }}"
            f"QPushButton:disabled {{ background-color: {AppTheme.BG_TERTIARY};"
            f" color: {AppTheme.TEXT_MUTED}; border-color: {AppTheme.BG_TERTIARY}; }}"
        )
        btn_layout.addWidget(self._start_btn)

        self._pause_btn = QPushButton("暫停")
        self._pause_btn.setFixedHeight(36)
        self._pause_btn.setEnabled(False)
        self._pause_btn.clicked.connect(self._on_pause)
        self._pause_btn.setStyleSheet(
            f"QPushButton {{ background-color: {AppTheme.ACCENT_YELLOW};"
            f" color: #000000; border: 1px solid #e5a800;"
            f" border-radius: 4px; font-weight: bold; font-size: 12px; }}"
            f"QPushButton:hover {{ background-color: #e5a800; }}"
            f"QPushButton:disabled {{ background-color: {AppTheme.BG_TERTIARY};"
            f" color: {AppTheme.TEXT_MUTED}; border-color: {AppTheme.BG_TERTIARY}; }}"
        )
        btn_layout.addWidget(self._pause_btn)

        self._reset_btn = QPushButton("重置")
        self._reset_btn.setFixedHeight(36)
        self._reset_btn.clicked.connect(self._on_reset)
        self._reset_btn.setStyleSheet(
            f"QPushButton {{ background-color: {AppTheme.ACCENT_RED};"
            f" color: #ffffff; border: 1px solid {AppTheme.ACCENT_RED_HOVER};"
            f" border-radius: 4px; font-weight: bold; font-size: 12px; }}"
            f"QPushButton:hover {{ background-color: {AppTheme.ACCENT_RED_HOVER}; }}"
        )
        btn_layout.addWidget(self._reset_btn)

        self._float_btn = QPushButton("浮動視窗")
        self._float_btn.setFixedHeight(36)
        self._float_btn.clicked.connect(self._on_toggle_float)
        self._float_btn.setStyleSheet(
            f"QPushButton {{ background-color: {AppTheme.ACCENT_BLUE};"
            f" color: #ffffff; border: 1px solid #2563eb;"
            f" border-radius: 4px; font-weight: bold; font-size: 12px; }}"
            f"QPushButton:hover {{ background-color: #2563eb; }}"
        )
        btn_layout.addWidget(self._float_btn)

        self._save_btn = QPushButton("保存紀錄")
        self._save_btn.setFixedHeight(36)
        self._save_btn.setEnabled(False)
        self._save_btn.clicked.connect(self._on_save)
        self._save_btn.setStyleSheet(
            f"QPushButton {{ background-color: {AppTheme.ACCENT_BLUE};"
            f" color: #ffffff; border: 1px solid #2563eb;"
            f" border-radius: 4px; font-weight: bold; font-size: 12px; }}"
            f"QPushButton:hover {{ background-color: #2563eb; }}"
            f"QPushButton:disabled {{ background-color: {AppTheme.BG_TERTIARY};"
            f" color: {AppTheme.TEXT_MUTED}; border-color: {AppTheme.BG_TERTIARY}; }}"
        )
        btn_layout.addWidget(self._save_btn)

        self._history_btn = QPushButton("查詢紀錄")
        self._history_btn.setFixedHeight(36)
        self._history_btn.clicked.connect(self._on_show_history)
        self._history_btn.setStyleSheet(
            f"QPushButton {{ background-color: {AppTheme.ACCENT_BLUE};"
            f" color: #ffffff; border: 1px solid #2563eb;"
            f" border-radius: 4px; font-weight: bold; font-size: 12px; }}"
            f"QPushButton:hover {{ background-color: #2563eb; }}"
        )
        btn_layout.addWidget(self._history_btn)

        main_layout.addLayout(btn_layout)

        # ===== 日誌區 =====
        self._log = LogViewer()
        self._log.setMaximumHeight(150)
        main_layout.addWidget(self._log)

        # 初始載入
        self._refresh_windows()

        # 監聽 combo 變化
        self._window_combo.currentIndexChanged.connect(self._on_window_selected)

    def _make_label(self, text: str, style: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(style)
        return lbl

    # ===== 設定保存/還原 =====

    def _restore_settings(self):
        """從 config 還原上次選擇的視窗和區域"""
        if not self._config:
            return

        saved_title = self._config.get_settings("last_window_title")
        saved_region = self._config.get_settings("last_region")

        if saved_title:
            for i in range(self._window_combo.count()):
                data = self._window_combo.itemData(i)
                if data and data.get("title") == saved_title:
                    self._window_combo.setCurrentIndex(i)
                    break

        if saved_region and self._selected_hwnd:
            bbox = tuple(saved_region)
            if len(bbox) == 4:
                self._capture_bbox = bbox

                self._start_btn.setEnabled(True)
                self._log.append_log(
                    f"已還原監測區域: ({bbox[0]}, {bbox[1]}) {bbox[2]}x{bbox[3]}"
                )
                try:
                    img = self._capture.capture_region(self._capture_bbox)
                    self._preview.set_image(img)
                except Exception:
                    pass

    def _save_settings(self):
        """保存當前視窗和區域到 config"""
        if not self._config:
            return
        self._config.set_settings("last_window_title", self._selected_title or "")
        if self._capture_bbox:
            self._config.set_settings("last_region", list(self._capture_bbox))
        else:
            self._config.set_settings("last_region", None)

    # ===== 視窗選擇 =====

    def _refresh_windows(self):
        """重新列舉視窗"""
        prev_hwnd = None
        data = self._window_combo.currentData()
        if data:
            prev_hwnd = data["hwnd"]
        self._window_combo.blockSignals(True)
        self._window_combo.clear()
        self._window_combo.addItem("-- 請選擇視窗 --", None)
        windows = list_windows()
        restore_index = 0
        for i, w in enumerate(windows):
            self._window_combo.addItem(w["title"], w)
            if prev_hwnd and w["hwnd"] == prev_hwnd:
                restore_index = i + 1
        self._window_combo.setCurrentIndex(restore_index)
        self._window_combo.blockSignals(False)

    def _on_window_selected(self, index):
        """視窗選擇變更"""
        data = self._window_combo.currentData()
        if data:
            self._selected_hwnd = data["hwnd"]
            self._selected_title = data["title"]
            self._region_btn.setEnabled(True)
            self._log.append_log(f"已選擇視窗: {self._selected_title}")
            self._save_settings()
        else:
            self._selected_hwnd = None
            self._selected_title = None
            self._region_btn.setEnabled(False)

    # ===== 區域選取 =====

    def _show_region_selector(self):
        """顯示區域選取遮罩"""
        if not self._selected_hwnd:
            return

        if not is_window_valid(self._selected_hwnd):
            self._log.append_log("視窗已失效，請重新選擇")
            return

        rect = get_window_rect(self._selected_hwnd)
        if self._overlay is not None:
            self._overlay.close()
        self._overlay = RegionOverlay(target_rect=rect)
        self._overlay.region_selected.connect(self._on_region_selected)
        self._overlay.cancelled.connect(self._on_region_cancelled)
        self._overlay.show()

    def _on_region_selected(self, left, top, width, height):
        """區域選取完成"""
        self._capture_bbox = (left, top, width, height)

        self._start_btn.setEnabled(True)
        self._log.append_log(f"監測區域已設定: ({left}, {top}) {width}x{height}")

        # 立即截一張預覽
        try:
            img = self._capture.capture_region(self._capture_bbox)
            self._preview.set_image(img)
        except Exception as e:
            self._log.append_log(f"預覽截圖失敗: {e}")

        self._overlay = None
        self._save_settings()

    def _on_region_cancelled(self):
        """區域選取取消"""
        self._log.append_log("已取消區域選取")
        self._overlay = None

    # ===== 監測控制 =====

    def _on_start(self):
        """開始監測"""
        if not self._capture_bbox:
            return

        if not self._ocr.is_loaded():
            self._loading_label.show()
            self._log.append_log("正在載入辨識引擎，請稍候...")

        self._is_monitoring = True
        self._start_btn.setEnabled(False)
        self._pause_btn.setEnabled(True)
        self._region_btn.setEnabled(False)
        self._window_combo.setEnabled(False)
        self._interval_combo.setEnabled(False)

        interval = self._interval_combo.currentData() or 2000
        self._timer.start(interval)
        self._log.append_log(f"開始監測（間隔 {interval/1000:.0f} 秒）")

        # 立即執行第一次
        self._do_capture_cycle()

    def _on_engine_loaded(self):
        """OCR 引擎載入完成"""
        self._loading_label.hide()
        self._log.append_log("辨識引擎載入完成")

    def _on_pause(self):
        """暫停監測"""
        self._is_monitoring = False
        self._timer.stop()
        self._start_btn.setEnabled(True)
        self._pause_btn.setEnabled(False)
        self._region_btn.setEnabled(True)
        self._window_combo.setEnabled(True)
        self._interval_combo.setEnabled(True)
        self._log.append_log("已暫停監測")

    def _on_reset(self):
        """重置所有數據"""
        self._on_pause() if self._is_monitoring else None
        self._timer.stop()
        self._is_monitoring = False
        self._is_processing = False
        self._calculator.reset()

        self._exp_label.setText("--")
        self._gained_label.setText("--")
        self._rate_min_label.setText("--")
        self._rate10_label.setText("--")
        self._rate60_label.setText("--")
        self._ttl_label.setText("--")
        self._elapsed_label.setText("--")
        self._warning_label.hide()
        self._loading_label.hide()
        self._preview.clear_image()
        self._float_window.reset_data()
        self._save_btn.setEnabled(False)

        self._start_btn.setEnabled(bool(self._capture_bbox))
        self._pause_btn.setEnabled(False)
        self._region_btn.setEnabled(bool(self._selected_hwnd))
        self._window_combo.setEnabled(True)
        self._interval_combo.setEnabled(True)

        self._log.append_log("已重置所有數據")

    def _on_toggle_float(self):
        """切換浮動視窗顯示"""
        if self._float_window.isVisible():
            self._float_window.hide()
            self._log.append_log("浮動視窗已隱藏")
        else:
            self._float_window.show()
            self._log.append_log("浮動視窗已顯示")

    # ===== OCR 循環 =====

    def _do_capture_cycle(self):
        """執行一次截圖 + OCR 循環"""
        if self._is_processing:
            return
        if not self._capture_bbox:
            return

        # 檢查目標視窗是否仍然有效
        if self._selected_hwnd and not is_window_valid(self._selected_hwnd):
            self._log.append_log("目標視窗已關閉，自動暫停監測")
            self._on_pause()
            self._warning_label.setText("目標視窗已關閉，請重新選擇視窗")
            self._warning_label.show()
            self._float_window.show_warning("目標視窗已關閉")
            return

        self._is_processing = True
        # 截圖在主執行緒（mss 需要 thread-local），OCR 在工作者執行緒
        try:
            img = self._capture.capture_region(self._capture_bbox)
            self._worker.trigger.emit(img)
        except Exception as e:
            self._is_processing = False
            self._on_ocr_error(str(e))

    def _on_ocr_result(self, img, result, raw_text):
        """OCR 結果回調（主執行緒）"""
        self._is_processing = False

        # 更新預覽
        if img:
            self._preview.set_image(img)

        if result is not None:
            # 格式正常，隱藏警告
            self._warning_label.hide()
            self._float_window.show_warning("擷取正常")

            # 加入讀數（自動偵測升級）
            level_up = self._calculator.add_reading(result.exp_value, result.percentage)
            if level_up:
                self._log.append_log("偵測到升級! 持續累計中")
                self._float_window.show_warning("偵測到升級!")

            summary = self._calculator.get_summary()

            # 更新 UI
            self._exp_label.setText(f"{result.exp_value:,}[{result.percentage:.2f}%]")
            gained = summary["exp_gained"]
            self._gained_label.setText(f"+{gained:,}")
            self._rate_min_label.setText(f"+{summary['rate_per_min']:,.0f}")
            self._rate10_label.setText(f"+{summary['rate_10min']:,.0f}")
            self._rate60_label.setText(f"+{summary['rate_60min']:,.0f}")

            # 預估升級時間
            ttl = summary.get("time_to_level_min")
            if ttl is not None:
                if ttl >= 60:
                    hours = int(ttl) // 60
                    mins = int(ttl) % 60
                    self._ttl_label.setText(f"{hours} 小時 {mins} 分鐘")
                elif ttl < 1:
                    self._ttl_label.setText("少於 1 分鐘")
                else:
                    self._ttl_label.setText(f"{ttl:.0f} 分鐘")
            else:
                self._ttl_label.setText("--")

            elapsed = summary["elapsed_seconds"]
            mins = int(elapsed) // 60
            secs = int(elapsed) % 60
            self._elapsed_label.setText(f"{mins}分{secs}秒")

            # 通知浮動視窗
            self._float_window.update_data(summary)
            self.exp_updated.emit(summary)

            # 啟用按鈕
            self._save_btn.setEnabled(len(self._calculator.readings) >= 2)

            self._log.append_log(
                f"辨識: {result.exp_value:,}[{result.percentage:.2f}%]"
            )
        else:
            # 格式不符
            if raw_text:
                msg = f"格式異常: {raw_text}"
                self._warning_label.setText(msg)
                self._warning_label.show()
                self._float_window.show_warning(msg)
                self._log.append_log(msg)
            else:
                self._float_window.show_warning("無法辨識文字")
                self._log.append_log("無法辨識文字")

    def _on_ocr_error(self, error_msg):
        """OCR 錯誤回調"""
        self._is_processing = False
        msg = f"辨識錯誤: {error_msg}"
        self._float_window.show_warning(msg)
        self._log.append_log(msg)

    # ===== 查詢紀錄 =====

    def _on_show_history(self):
        """開啟歷史紀錄對話框"""
        if not self._storage:
            return
        from src.ui.dialogs.history_dialog import HistoryDialog
        dialog = HistoryDialog(self._storage, self)
        dialog.exec()

    # ===== 保存紀錄 =====

    def _on_save(self):
        """保存當前監測紀錄"""
        if not self._storage or len(self._calculator.readings) < 2:
            return
        try:
            session_id = self._storage.save_session(
                readings=self._calculator.readings,
                window_title=self._selected_title or "",
                level_up_count=self._calculator.level_up_count,
            )
            self._log.append_log(f"紀錄已保存 (ID: {session_id})")
            app = self.window()
            if hasattr(app, "toast_manager"):
                app.toast_manager.show("紀錄已保存", "success")
        except Exception as e:
            self._log.append_log(f"保存失敗: {e}")

    # ===== 清理 =====

    def cleanup(self):
        """清理資源"""
        self._save_settings()
        self._timer.stop()
        self._is_monitoring = False

        # 停止工作者執行緒
        self._worker_thread.quit()
        if not self._worker_thread.wait(5000):
            # 超時強制終止
            self._worker_thread.terminate()
            self._worker_thread.wait(1000)

        self._capture.close()
        if self._float_window:
            self._float_window.close()
