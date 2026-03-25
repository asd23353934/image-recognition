"""
配置管理模組
處理配置文件的讀寫
"""

import json
import logging
import os

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_path):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self):
        """載入配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"settings": {}}
        except Exception as e:
            logger.error("無法載入 config.json: %s", e)
            return {"settings": {}}

    def save(self):
        """儲存配置文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error("保存配置失敗: %s", e)
            return False

    def get_settings(self, key, default=None):
        """獲取設定值"""
        return self.config.get('settings', {}).get(key, default)

    def set_settings(self, key, value):
        """設定設定值"""
        if 'settings' not in self.config:
            self.config['settings'] = {}
        self.config['settings'][key] = value
