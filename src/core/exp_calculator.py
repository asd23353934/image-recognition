"""
經驗值計算模組
儲存時間序列數據並計算經驗值速率
支援跨升級持續累計
"""

import time
from dataclasses import dataclass


@dataclass
class ExpReading:
    """單次經驗值讀數"""
    timestamp: float
    value: int
    percentage: float = 0.0


class ExpCalculator:
    """經驗值速率計算器

    使用逐筆差值累加，而非首尾相減，以正確處理升級重置。
    """

    def __init__(self):
        self.readings: list[ExpReading] = []
        self.level_up_count: int = 0
        self._total_gained: int = 0        # 累計經驗獲取（跨升級）
        self._total_pct_gained: float = 0.0  # 累計百分比增長（跨升級）

    def add_reading(self, value: int, percentage: float = 0.0) -> str | None:
        """新增一筆經驗值讀數

        Returns:
            "level_up" 如偵測到升級，否則 None
        """
        now = time.time()
        result = None

        if self.readings:
            last = self.readings[-1]

            # 偵測升級：經驗值下降或百分比下降
            if value < last.value or percentage < last.percentage:
                self.level_up_count += 1
                result = "level_up"
                # 不清除 readings，繼續累計
            else:
                # 正常增長，累加差值
                self._total_gained += value - last.value
                self._total_pct_gained += percentage - last.percentage

        self.readings.append(ExpReading(timestamp=now, value=value, percentage=percentage))
        return result

    def get_current_exp(self) -> int | None:
        """取得最新經驗值"""
        if not self.readings:
            return None
        return self.readings[-1].value

    def get_current_percentage(self) -> float | None:
        """取得最新百分比"""
        if not self.readings:
            return None
        return self.readings[-1].percentage

    def get_exp_gained(self) -> int:
        """取得累計經驗獲取（跨升級）"""
        return self._total_gained

    def get_elapsed(self) -> float:
        """取得監測時長（秒）"""
        if len(self.readings) < 2:
            return 0.0
        return self.readings[-1].timestamp - self.readings[0].timestamp

    def get_rate_per_min(self) -> float:
        """取得每分鐘經驗值速率"""
        return self._rate_per_sec() * 60

    def get_rate_per_10min(self) -> float:
        """取得每 10 分鐘經驗值速率"""
        return self._rate_per_sec() * 600

    def get_rate_per_60min(self) -> float:
        """取得每 60 分鐘經驗值速率"""
        return self._rate_per_sec() * 3600

    def get_time_to_level(self) -> float | None:
        """預估升級所需時間（分鐘）

        基於平均百分比增長速率計算，不受升級重置影響。

        Returns:
            預估分鐘數，無法計算時回傳 None
        """
        elapsed = self.get_elapsed()
        if elapsed <= 0 or self._total_pct_gained <= 0:
            return None

        pct_rate_per_sec = self._total_pct_gained / elapsed
        last = self.readings[-1]
        remaining = 100.0 - last.percentage

        if remaining <= 0:
            return 0.0

        return remaining / (pct_rate_per_sec * 60)

    def _rate_per_sec(self) -> float:
        """計算每秒平均經驗獲取速率"""
        elapsed = self.get_elapsed()
        if elapsed <= 0:
            return 0.0
        return self._total_gained / elapsed

    def get_summary(self) -> dict:
        """取得摘要資訊"""
        return {
            "current_exp": self.get_current_exp(),
            "current_percentage": self.get_current_percentage(),
            "exp_gained": self.get_exp_gained(),
            "rate_per_min": self.get_rate_per_min(),
            "rate_10min": self.get_rate_per_10min(),
            "rate_60min": self.get_rate_per_60min(),
            "time_to_level_min": self.get_time_to_level(),
            "reading_count": len(self.readings),
            "elapsed_seconds": self.get_elapsed(),
            "level_up_count": self.level_up_count,
        }

    def reset(self) -> None:
        """清除所有讀數"""
        self.readings.clear()
        self.level_up_count = 0
        self._total_gained = 0
        self._total_pct_gained = 0.0
