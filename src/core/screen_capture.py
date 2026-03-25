"""
螢幕截圖模組
使用 mss 進行高效能螢幕區域截圖
"""

import mss
import mss.tools
from PIL import Image


class ScreenCapture:
    """螢幕截圖器"""

    def __init__(self):
        self._sct = mss.mss()

    def capture_region(self, bbox: tuple[int, int, int, int]) -> Image.Image:
        """截取螢幕指定區域

        Args:
            bbox: (left, top, width, height) 絕對螢幕座標

        Returns:
            PIL.Image (RGB)
        """
        left, top, width, height = bbox
        monitor = {
            "left": left,
            "top": top,
            "width": width,
            "height": height,
        }
        screenshot = self._sct.grab(monitor)
        # mss 回傳 BGRA，轉為 RGB
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        return img

    def close(self):
        """釋放資源"""
        try:
            self._sct.close()
        except Exception:
            pass
