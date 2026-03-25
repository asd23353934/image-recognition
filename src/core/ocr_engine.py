"""
OCR 引擎模組
PaddleOCR 包裝器，提供數字辨識功能
適配 PaddleOCR 3.4.0+ API (predict 方法 + OCRResult 物件)
"""

import logging
import os
import re
from dataclasses import dataclass

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class ExpResult:
    """經驗值辨識結果"""
    raw_text: str       # 原始 OCR 文字，如 "383430[63.43%]"
    exp_value: int      # 經驗值數字，如 383430
    percentage: float   # 百分比，如 63.43


class OcrEngine:
    """PaddleOCR 包裝器"""

    def __init__(self):
        self._ocr = None

    def _ensure_loaded(self):
        """懶載入 PaddleOCR（首次呼叫約 2-5 秒）"""
        if self._ocr is not None:
            return
        os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
        from paddleocr import PaddleOCR
        self._ocr = PaddleOCR(
            lang="ch",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )
        logger.info("PaddleOCR 引擎已載入")

    def recognize_number(self, image: Image.Image) -> int | None:
        """辨識圖片中的純數字

        Args:
            image: PIL.Image 截圖

        Returns:
            辨識出的整數，失敗回傳 None
        """
        self._ensure_loaded()
        try:
            img_array = np.array(image)
            results = list(self._ocr.predict(img_array))

            if not results:
                return None

            res_data = results[0].json.get("res", {})
            rec_texts = res_data.get("rec_texts", [])
            rec_scores = res_data.get("rec_scores", [])

            if not rec_texts:
                return None

            # 收集所有辨識結果，按信心度排序
            candidates = []
            for text, score in zip(rec_texts, rec_scores):
                digits = re.sub(r'[^\d]', '', text)
                if digits:
                    candidates.append((int(digits), float(score)))

            if not candidates:
                return None

            candidates.sort(key=lambda x: x[1], reverse=True)
            return candidates[0][0]

        except Exception as e:
            logger.error("OCR 辨識失敗: %s", e)
            return None

    def recognize_text(self, image: Image.Image) -> str:
        """辨識圖片中的文字（除錯用）

        Args:
            image: PIL.Image 截圖

        Returns:
            辨識出的原始文字
        """
        self._ensure_loaded()
        try:
            img_array = np.array(image)
            results = list(self._ocr.predict(img_array))

            if not results:
                return ""

            res_data = results[0].json.get("res", {})
            rec_texts = res_data.get("rec_texts", [])
            return " ".join(rec_texts)

        except Exception as e:
            logger.error("OCR 文字辨識失敗: %s", e)
            return ""

    def recognize_exp_format(self, image: Image.Image) -> tuple[ExpResult | None, str]:
        """辨識經驗值格式 NUMBER[PERCENT%]

        Args:
            image: PIL.Image 截圖

        Returns:
            (ExpResult | None, raw_text) — 解析結果與原始文字
        """
        self._ensure_loaded()
        try:
            img_array = np.array(image)
            results = list(self._ocr.predict(img_array))

            if not results:
                return None, ""

            res_data = results[0].json.get("res", {})
            rec_texts = res_data.get("rec_texts", [])

            if not rec_texts:
                return None, ""

            raw_text = "".join(rec_texts)

            # 匹配格式: 383430[63.43%] 或 27546(27.55%)
            pattern = r'(\d+)\s*[\[\(]\s*(\d+\.?\d*)\s*%\s*[\]\)]'
            match = re.search(pattern, raw_text)

            if match:
                exp_value = int(match.group(1))
                percentage = float(match.group(2))
                return ExpResult(raw_text=raw_text, exp_value=exp_value, percentage=percentage), raw_text

            return None, raw_text

        except Exception as e:
            logger.error("OCR 辨識失敗: %s", e)
            return None, ""

    def is_loaded(self) -> bool:
        """檢查引擎是否已載入"""
        return self._ocr is not None
