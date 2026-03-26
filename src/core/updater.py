"""
版本管理和自動更新模組
提供版本檢查、下載更新、啟動替換腳本
"""

import os
import sys
import tempfile

try:
    from version import get_version
    CURRENT_VERSION = get_version()
except ImportError:
    CURRENT_VERSION = "1.0.0"

GITHUB_API_URL = "https://api.github.com/repos/asd23353934/image-recognition/releases/latest"

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from packaging import version as pkg_version
    HAS_PACKAGING = True
except ImportError:
    HAS_PACKAGING = False


class Updater:
    """自動更新檢查器與下載器"""

    def __init__(self):
        self.current_version = CURRENT_VERSION
        self.latest_version = None
        self.download_url = None
        self.update_available = False

    def check_for_updates(self):
        """檢查是否有新版本"""
        if not HAS_REQUESTS:
            return {
                'available': False,
                'current': self.current_version,
                'error': 'requests module not installed'
            }

        try:
            response = requests.get(GITHUB_API_URL, timeout=5)
            response.raise_for_status()
            release_data = response.json()

            latest_tag = release_data.get('tag_name', '').lstrip('v')

            if self._compare_versions(latest_tag, self.current_version):
                self.update_available = True
                self.latest_version = latest_tag

                assets = release_data.get('assets', [])
                exe_url = None
                archive_url = None

                for asset in assets:
                    name = asset['name'].lower()
                    url = asset['browser_download_url']
                    if name.endswith('.exe'):
                        exe_url = url
                    elif name.endswith(('.7z', '.zip', '.tar.gz')):
                        archive_url = url

                fallback_url = (
                    f"https://github.com/asd23353934/image-recognition"
                    f"/releases/download/v{latest_tag}"
                    f"/image_recognition_v{latest_tag}.zip"
                )
                self.download_url = exe_url or archive_url or fallback_url

                return {
                    'available': True,
                    'current': self.current_version,
                    'latest': self.latest_version,
                    'download_url': self.download_url,
                    'release_notes': release_data.get('body', '')
                }

            return {
                'available': False,
                'current': self.current_version,
                'latest': self.current_version
            }

        except Exception as e:
            return {
                'available': False,
                'current': self.current_version,
                'error': str(e)
            }

    def download_update(self, url, dest_path, progress_callback=None):
        """下載更新檔案"""
        if not HAS_REQUESTS:
            return False

        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(downloaded, total_size)

            return True

        except Exception:
            try:
                if os.path.exists(dest_path):
                    os.remove(dest_path)
            except Exception:
                pass
            return False

    def get_update_temp_path(self):
        """取得更新暫存檔案路徑"""
        temp_dir = tempfile.gettempdir()
        if self.download_url:
            filename = os.path.basename(self.download_url)
        else:
            filename = "image_recognition_update.zip"
        return os.path.join(temp_dir, filename)

    def get_launcher_path(self):
        """取得更新啟動腳本路徑"""
        from src.ui.helpers import resource_path
        return resource_path("update_launcher.bat")

    def _compare_versions(self, latest, current):
        """比較版本號"""
        if HAS_PACKAGING:
            try:
                return pkg_version.parse(latest) > pkg_version.parse(current)
            except Exception:
                pass
        try:
            latest_parts = [int(x) for x in latest.split('.')]
            current_parts = [int(x) for x in current.split('.')]
            return latest_parts > current_parts
        except Exception:
            return False
