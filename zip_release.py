#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打包後壓縮腳本
將 dist/image_recognition/ 壓縮為 ZIP 發布檔案
"""

import os
import re
import sys
import zipfile


def get_version() -> str:
    """從 version.py 讀取版本號"""
    try:
        with open("version.py", "r", encoding="utf-8") as f:
            content = f.read()
        match = re.search(r'VERSION = "([^"]+)"', content)
        return match.group(1) if match else "unknown"
    except Exception as e:
        print(f"  WARNING: cannot read version.py: {e}")
        return "unknown"


def zip_release() -> int:
    """壓縮 dist/image_recognition/ 為 ZIP

    Returns:
        0 成功, 1 失敗
    """
    version = get_version()
    src_dir = os.path.join("dist", "image_recognition")
    zip_name = f"image_recognition_v{version}.zip"
    zip_path = os.path.join("dist", zip_name)

    print("=" * 55)
    print("  image_recognition - ZIP release")
    print("=" * 55)
    print()
    print(f"  Version: v{version}")
    print(f"  Source:   {src_dir}")
    print(f"  Output:   {zip_path}")
    print()

    # 確認來源目錄存在
    if not os.path.isdir(src_dir):
        print(f"ERROR: directory not found: {src_dir}")
        print("  Please run: pyinstaller image_recognition.spec")
        return 1

    # 若舊 ZIP 存在先刪除
    if os.path.exists(zip_path):
        os.remove(zip_path)
        print(f"  Deleted old {zip_name}")

    # 計算檔案數量
    total_files = sum(len(files) for _, _, files in os.walk(src_dir))
    print(f"  {total_files} files, compressing...")

    compressed = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for root, _dirs, files in os.walk(src_dir):
            for filename in sorted(files):
                full_path = os.path.join(root, filename)
                arcname = os.path.relpath(full_path, "dist")
                zf.write(full_path, arcname)
                compressed += 1
                if compressed % 50 == 0:
                    print(f"    {compressed}/{total_files}...")

    # 統計結果
    zip_bytes = os.path.getsize(zip_path)
    src_bytes = sum(
        os.path.getsize(os.path.join(r, f))
        for r, _, files in os.walk(src_dir)
        for f in files
    )
    ratio = (1 - zip_bytes / src_bytes) * 100 if src_bytes > 0 else 0

    print()
    print("Compress done!")
    print(f"  Original: {src_bytes / 1024 / 1024:.1f} MB")
    print(f"  ZIP size: {zip_bytes / 1024 / 1024:.1f} MB  ({ratio:.0f}% saved)")
    print(f"  Output:   {zip_path}")
    return 0


if __name__ == "__main__":
    sys.exit(zip_release())
