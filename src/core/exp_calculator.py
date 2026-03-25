"""
經驗值計算模組
儲存時間序列數據並計算經驗值速率
"""

import time
from dataclasses import dataclass, field


@dataclass
class ExpReading:
    """單次經驗值讀數"""
    timestamp: float
    value: int
    percentage: float = 0.0


class ExpCalculator:
    """經驗值速率計算器"""

    def __init__(self):
        self.readings: list[ExpReading] = []
        self.level_up_count: int = 0

    def add_reading(self, value: int, percentage: float = 0.0) -> None:
        """新增一筆經驗值讀數"""
        self.readings.append(ExpReading(timestamp=time.time(), value=value, percentage=percentage))

    def check_anomaly(self, value: int, percentage: float) -> str | None:
        """檢查異常並處理升級

        Returns:
            異常訊息字串，正常回傳 None，升級回傳 "level_up"
        """
        if not self.readings:
            return None

        last = self.readings[-1]

        # 偵測升級: 新值為 0 且百分比為 0
        if value == 0 and percentage == 0.0 and last.percentage > 0:
            self.level_up_count += 1
            self.readings.clear()
            return "level_up"

        # 經驗值下降（非升級情況）
        if value < last.value and value != 0:
            return f"經驗值異常下降: {last.value:,} → {value:,}"

        # 百分比下降（非升級情況）
        if percentage < last.percentage and percentage != 0.0:
            return f"百分比異常下降: {last.percentage:.2f}% → {percentage:.2f}%"

        return None

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
        """取得總增加經驗值"""
        if len(self.readings) < 2:
            return 0
        return self.readings[-1].value - self.readings[0].value

    def get_rate_per_min(self) -> float:
        """取得每分鐘經驗值速率"""
        return self._calculate_rate() * 60

    def get_rate_per_10min(self) -> float:
        """取得每 10 分鐘經驗值速率（滾動平均）"""
        return self._calculate_rate() * 600

    def get_rate_per_60min(self) -> float:
        """取得每 60 分鐘經驗值速率（滾動平均）"""
        return self._calculate_rate() * 3600

    def get_time_to_level(self) -> float | None:
        """預估升級所需時間（分鐘）

        Returns:
            預估分鐘數，無法計算時回傳 None
        """
        if len(self.readings) < 2:
            return None

        first = self.readings[0]
        last = self.readings[-1]
        time_diff = last.timestamp - first.timestamp

        if time_diff <= 0:
            return None

        pct_rate_per_sec = (last.percentage - first.percentage) / time_diff
        if pct_rate_per_sec <= 0:
            return None

        remaining = 100.0 - last.percentage
        if remaining <= 0:
            return 0.0

        return remaining / (pct_rate_per_sec * 60)

    def _calculate_rate(self) -> float:
        """計算每秒經驗值速率"""
        if len(self.readings) < 2:
            return 0.0

        first = self.readings[0]
        last = self.readings[-1]
        time_diff = last.timestamp - first.timestamp

        if time_diff <= 0:
            return 0.0

        exp_diff = last.value - first.value
        return exp_diff / time_diff

    def get_summary(self) -> dict:
        """取得摘要資訊"""
        elapsed = 0.0
        if len(self.readings) >= 2:
            elapsed = self.readings[-1].timestamp - self.readings[0].timestamp

        return {
            "current_exp": self.get_current_exp(),
            "current_percentage": self.get_current_percentage(),
            "exp_gained": self.get_exp_gained(),
            "rate_per_min": self.get_rate_per_min(),
            "rate_10min": self.get_rate_per_10min(),
            "rate_60min": self.get_rate_per_60min(),
            "time_to_level_min": self.get_time_to_level(),
            "reading_count": len(self.readings),
            "elapsed_seconds": elapsed,
            "level_up_count": self.level_up_count,
        }

    def reset(self) -> None:
        """清除所有讀數"""
        self.readings.clear()
        self.level_up_count = 0
