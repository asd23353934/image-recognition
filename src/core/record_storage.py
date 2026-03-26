"""
紀錄儲存模組
使用 SQLite 儲存監測紀錄、讀數與截圖路徑
"""

import os
import sqlite3
from src.core.exp_calculator import ExpReading


class RecordStorage:
    """監測紀錄的 SQLite 儲存層"""

    def __init__(self, db_path: str):
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        cur = self._conn.cursor()
        cur.execute("PRAGMA foreign_keys = ON")
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time REAL NOT NULL,
                end_time REAL NOT NULL,
                window_title TEXT DEFAULT '',
                total_gained INTEGER DEFAULT 0,
                level_up_count INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                timestamp REAL NOT NULL,
                exp_value INTEGER NOT NULL,
                percentage REAL DEFAULT 0.0,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS screenshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                timestamp REAL NOT NULL,
                file_path TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_readings_session_id ON readings(session_id);
            CREATE INDEX IF NOT EXISTS idx_screenshots_session_id ON screenshots(session_id);
        """)
        self._conn.commit()

    def save_session(
        self,
        readings: list[ExpReading],
        window_title: str,
        level_up_count: int,
        screenshot_paths: list[tuple[float, str]] | None = None,
    ) -> int:
        """儲存一次監測紀錄，回傳 session_id"""
        if len(readings) < 2:
            raise ValueError("至少需要 2 筆讀數")

        start_time = readings[0].timestamp
        end_time = readings[-1].timestamp
        # 累加正向差值（跨升級正確計算）
        total_gained = 0
        for i in range(1, len(readings)):
            diff = readings[i].value - readings[i - 1].value
            if diff > 0:
                total_gained += diff

        cur = self._conn.cursor()
        cur.execute(
            "INSERT INTO sessions (start_time, end_time, window_title, total_gained, level_up_count) "
            "VALUES (?, ?, ?, ?, ?)",
            (start_time, end_time, window_title, total_gained, level_up_count),
        )
        session_id = cur.lastrowid

        cur.executemany(
            "INSERT INTO readings (session_id, timestamp, exp_value, percentage) VALUES (?, ?, ?, ?)",
            [(session_id, r.timestamp, r.value, r.percentage) for r in readings],
        )

        if screenshot_paths:
            cur.executemany(
                "INSERT INTO screenshots (session_id, timestamp, file_path) VALUES (?, ?, ?)",
                [(session_id, ts, path) for ts, path in screenshot_paths],
            )

        self._conn.commit()
        return session_id

    def get_sessions(self) -> list[dict]:
        """取得所有紀錄，依時間倒序"""
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM sessions ORDER BY start_time DESC")
        return [dict(row) for row in cur.fetchall()]

    def get_session_readings(self, session_id: int) -> list[dict]:
        """取得紀錄的所有讀數"""
        cur = self._conn.cursor()
        cur.execute(
            "SELECT timestamp, exp_value, percentage FROM readings "
            "WHERE session_id = ? ORDER BY timestamp",
            (session_id,),
        )
        return [dict(row) for row in cur.fetchall()]

    def get_session_screenshots(self, session_id: int) -> list[dict]:
        """取得紀錄的所有截圖"""
        cur = self._conn.cursor()
        cur.execute(
            "SELECT id, timestamp, file_path FROM screenshots "
            "WHERE session_id = ? ORDER BY timestamp",
            (session_id,),
        )
        return [dict(row) for row in cur.fetchall()]

    def delete_session(self, session_id: int) -> None:
        """刪除紀錄，同時清理磁碟截圖檔案"""
        screenshots = self.get_session_screenshots(session_id)
        for s in screenshots:
            try:
                if os.path.exists(s["file_path"]):
                    os.remove(s["file_path"])
            except OSError:
                pass

        cur = self._conn.cursor()
        cur.execute("PRAGMA foreign_keys = ON")
        cur.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        self._conn.commit()

    def close(self) -> None:
        """關閉資料庫連線"""
        self._conn.close()
