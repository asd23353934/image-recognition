"""
歷史紀錄對話框
顯示已保存的監測紀錄、折線圖與匯出功能
"""

import csv
import os
from datetime import datetime

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QFrame,
    QFileDialog, QMessageBox, QSplitter,
)
from PySide6.QtCore import Qt

from src.core.record_storage import RecordStorage
from src.ui.dialogs.base_dialog import BaseDialog
from src.ui.theme import AppTheme
from src.ui.widgets.exp_chart import ExpChart


class HistoryDialog(BaseDialog):
    """歷史紀錄對話框"""

    def __init__(self, storage: RecordStorage, parent=None):
        super().__init__(parent, "歷史紀錄", width=900, height=600)
        self._storage = storage
        self._current_session_id: int | None = None

        # 允許調整大小
        self.setMinimumSize(700, 450)
        self.setMaximumSize(16777215, 16777215)

        self._build_content()
        self._refresh_sessions()

    def _build_content(self):
        layout = QVBoxLayout(self.inner)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # ===== Left panel =====
        left_widget = QFrame()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)

        title = QLabel("歷史紀錄")
        title.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {AppTheme.TEXT_GOLD}; padding: 4px;"
        )
        left_layout.addWidget(title)

        self._session_list = QListWidget()
        self._session_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {AppTheme.BG_SECONDARY};
                border: 1px solid {AppTheme.GOLD_MUTED};
                border-radius: {AppTheme.CORNER_SM}px;
            }}
            QListWidget::item {{
                color: {AppTheme.TEXT_PRIMARY};
                padding: 8px;
                border-bottom: 1px solid {AppTheme.BG_TERTIARY};
            }}
            QListWidget::item:selected {{
                background-color: {AppTheme.BG_CARD_HOVER};
                color: {AppTheme.TEXT_GOLD};
            }}
        """)
        self._session_list.currentItemChanged.connect(self._on_session_selected)
        left_layout.addWidget(self._session_list)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)

        self._delete_btn = QPushButton("刪除")
        self._delete_btn.setFixedHeight(32)
        self._delete_btn.setEnabled(False)
        self._delete_btn.setStyleSheet(
            f"QPushButton {{ background-color: {AppTheme.ACCENT_RED}; color: #fff;"
            f" border: 1px solid {AppTheme.ACCENT_RED_HOVER}; border-radius: 4px; font-weight: bold; }}"
            f"QPushButton:hover {{ background-color: {AppTheme.ACCENT_RED_HOVER}; }}"
            f"QPushButton:disabled {{ background-color: {AppTheme.BG_TERTIARY}; color: {AppTheme.TEXT_MUTED}; }}"
        )
        self._delete_btn.clicked.connect(self._on_delete)
        btn_row.addWidget(self._delete_btn)

        refresh_btn = QPushButton("重新整理")
        refresh_btn.setFixedHeight(32)
        refresh_btn.clicked.connect(self._refresh_sessions)
        btn_row.addWidget(refresh_btn)

        left_layout.addLayout(btn_row)
        splitter.addWidget(left_widget)

        # ===== Right panel =====
        right_widget = QFrame()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        # 匯出區域容器（圖表 + 統計摘要，grab 此 widget 即可匯出完整截圖）
        self._export_area = QFrame()
        self._export_area.setObjectName("export_area")
        self._export_area.setStyleSheet(
            f"QFrame#export_area {{ background-color: {AppTheme.BG_SECONDARY}; border: none; }}"
        )
        export_area_layout = QVBoxLayout(self._export_area)
        export_area_layout.setContentsMargins(0, 0, 0, 0)
        export_area_layout.setSpacing(0)

        # Chart
        self._chart = ExpChart()
        export_area_layout.addWidget(self._chart, stretch=2)

        # Session detail frame
        detail_frame = QFrame()
        detail_frame.setObjectName("detail_frame")
        detail_frame.setStyleSheet(
            f"QFrame#detail_frame {{ background-color: {AppTheme.BG_CARD};"
            f" border: 1px solid {AppTheme.GOLD_MUTED}; border-radius: {AppTheme.CORNER_SM}px;"
            f" padding: 8px; }}"
        )
        detail_layout = QHBoxLayout(detail_frame)
        detail_layout.setSpacing(16)

        self._detail_labels: dict[str, QLabel] = {}
        for key, name in [
            ("duration", "監測時長"),
            ("gained", "累計獲取"),
            ("rate", "每分鐘"),
            ("level_ups", "升級次數"),
        ]:
            col = QVBoxLayout()
            col.setSpacing(2)
            header = QLabel(name)
            header.setStyleSheet(f"color: {AppTheme.TEXT_MUTED}; font-size: 11px; border: none;")
            value_lbl = QLabel("--")
            value_lbl.setStyleSheet(f"color: {AppTheme.TEXT_GOLD}; font-size: 14px; font-weight: bold; border: none;")
            col.addWidget(header, alignment=Qt.AlignmentFlag.AlignCenter)
            col.addWidget(value_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
            self._detail_labels[key] = value_lbl
            detail_layout.addLayout(col)

        export_area_layout.addWidget(detail_frame)

        right_layout.addWidget(self._export_area, stretch=2)

        # Export buttons
        export_row = QHBoxLayout()
        export_row.setSpacing(4)
        export_row.addStretch()

        self._export_btn = QPushButton("匯出紀錄")
        self._export_btn.setFixedHeight(32)
        self._export_btn.setEnabled(False)
        self._export_btn.setStyleSheet(
            f"QPushButton {{ background-color: {AppTheme.ACCENT_GREEN}; color: #fff;"
            f" border: 1px solid {AppTheme.ACCENT_GREEN_HOVER}; border-radius: 4px; font-weight: bold; }}"
            f"QPushButton:hover {{ background-color: {AppTheme.ACCENT_GREEN_HOVER}; }}"
            f"QPushButton:disabled {{ background-color: {AppTheme.BG_TERTIARY}; color: {AppTheme.TEXT_MUTED}; }}"
        )
        self._export_btn.clicked.connect(self._on_export)
        export_row.addWidget(self._export_btn)

        right_layout.addLayout(export_row)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

    # ===== Session list =====

    def _refresh_sessions(self) -> None:
        self._session_list.clear()
        self._current_session_id = None
        self._delete_btn.setEnabled(False)
        self._export_btn.setEnabled(False)
        self._chart.clear()
        self._clear_detail()

        sessions = self._storage.get_sessions()
        for s in sessions:
            start = datetime.fromtimestamp(s["start_time"]).strftime("%Y-%m-%d %H:%M")
            title = s["window_title"][:20] if s["window_title"] else ""
            gained = f"+{s['total_gained']:,}"
            text = f"{start}  {title}  {gained}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, s["id"])
            self._session_list.addItem(item)

    def _on_session_selected(self, current: QListWidgetItem | None, _previous):
        if not current:
            self._current_session_id = None
            self._delete_btn.setEnabled(False)
            self._export_btn.setEnabled(False)
            self._chart.clear()
            self._clear_detail()
            return

        session_id = current.data(Qt.ItemDataRole.UserRole)
        self._current_session_id = session_id
        self._delete_btn.setEnabled(True)
        self._load_session_detail(session_id)

    def _load_session_detail(self, session_id: int) -> None:
        readings = self._storage.get_session_readings(session_id)
        self._chart.set_readings(readings)
        self._export_btn.setEnabled(len(readings) >= 2)

        if len(readings) >= 2:
            duration_s = readings[-1]["timestamp"] - readings[0]["timestamp"]
            mins = int(duration_s) // 60
            secs = int(duration_s) % 60
            self._detail_labels["duration"].setText(f"{mins}:{secs:02d}")

            # 累加正向差值（跨升級正確計算）
            gained = 0
            for i in range(1, len(readings)):
                diff = readings[i]["exp_value"] - readings[i - 1]["exp_value"]
                if diff > 0:
                    gained += diff
            self._detail_labels["gained"].setText(f"+{gained:,}")

            if duration_s > 0:
                rate = gained / duration_s * 60
                self._detail_labels["rate"].setText(f"+{int(rate):,}")
            else:
                self._detail_labels["rate"].setText("--")
        else:
            self._clear_detail()

        # Level ups from session table
        sessions = self._storage.get_sessions()
        for s in sessions:
            if s["id"] == session_id:
                self._detail_labels["level_ups"].setText(str(s["level_up_count"]))
                break

    def _clear_detail(self):
        for lbl in self._detail_labels.values():
            lbl.setText("--")

    # ===== Actions =====

    def _on_delete(self):
        if self._current_session_id is None:
            return
        reply = QMessageBox.question(
            self,
            "確認刪除",
            "確定要刪除此筆紀錄？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._storage.delete_session(self._current_session_id)
        self._refresh_sessions()
        self._toast("紀錄已刪除")

    def _on_export(self):
        """匯出圖表 (PNG) + 完整數據 (CSV) 到選擇的資料夾"""
        if self._current_session_id is None:
            return
        dest = QFileDialog.getExistingDirectory(self, "選擇匯出資料夾")
        if not dest:
            return

        try:
            self._do_export(dest)
        except Exception as e:
            self._toast(f"匯出失敗: {e}")

    def _do_export(self, dest: str):
        """執行匯出邏輯"""
        readings = self._storage.get_session_readings(self._current_session_id)

        # 取得 session 資訊
        session_info = None
        for s in self._storage.get_sessions():
            if s["id"] == self._current_session_id:
                session_info = s
                break

        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        exported = []

        # 匯出圖表 PNG（含圖表 + 統計摘要，與畫面一致）
        chart_path = os.path.join(dest, f"exp_chart_{timestamp_str}.png")
        pixmap = self._export_area.grab()
        pixmap.save(chart_path, "PNG")
        exported.append("圖表")

        # 匯出完整數據 CSV
        if readings:
            csv_path = os.path.join(dest, f"exp_data_{timestamp_str}.csv")
            with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)

                # 摘要資訊
                if session_info:
                    writer.writerow(["# 監測摘要"])
                    writer.writerow(["視窗", session_info["window_title"]])
                    start_str = datetime.fromtimestamp(session_info["start_time"]).strftime("%Y-%m-%d %H:%M:%S")
                    end_str = datetime.fromtimestamp(session_info["end_time"]).strftime("%Y-%m-%d %H:%M:%S")
                    writer.writerow(["開始時間", start_str])
                    writer.writerow(["結束時間", end_str])
                    duration_s = session_info["end_time"] - session_info["start_time"]
                    writer.writerow(["監測時長(秒)", f"{duration_s:.0f}"])
                    writer.writerow(["累計獲取", session_info["total_gained"]])
                    writer.writerow(["升級次數", session_info["level_up_count"]])
                    if duration_s > 0:
                        writer.writerow(["每分鐘速率", f"{session_info['total_gained'] / duration_s * 60:.1f}"])
                        writer.writerow(["每小時速率", f"{session_info['total_gained'] / duration_s * 3600:.1f}"])
                    writer.writerow([])

                # 逐筆讀數
                writer.writerow(["# 詳細讀數"])
                writer.writerow(["時間", "經驗值", "百分比(%)", "獲取量", "累計獲取"])
                base_value = readings[0]["exp_value"]
                prev_value = base_value
                for r in readings:
                    time_str = datetime.fromtimestamp(r["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                    gain = max(r["exp_value"] - prev_value, 0)
                    cumulative = r["exp_value"] - base_value
                    writer.writerow([
                        time_str,
                        r["exp_value"],
                        f"{r['percentage']:.2f}",
                        gain,
                        cumulative,
                    ])
                    prev_value = r["exp_value"]

            exported.append(f"數據({len(readings)}筆)")

        self._toast(f"已匯出: {', '.join(exported)}")

    def _toast(self, message: str):
        app = self.window()
        if hasattr(app, "toast_manager"):
            app.toast_manager.show(message, "success")
