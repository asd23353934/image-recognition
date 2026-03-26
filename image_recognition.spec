# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_dynamic_libs
from PyInstaller.utils.hooks import collect_submodules

datas = [('config.json', '.'), ('version.py', '.'), ('update_launcher.bat', '.'), ('icon.ico', '.')]
binaries = []
hiddenimports = ['paddle', 'paddleocr', 'paddlex', 'PIL.PngImagePlugin', 'PIL.JpegImagePlugin', 'shapely', 'pyclipper', 'cv2']
datas += collect_data_files('paddlex')
binaries += collect_dynamic_libs('paddle')
hiddenimports += collect_submodules('cv2')
hiddenimports += collect_submodules('paddle')
hiddenimports += collect_submodules('paddleocr')
hiddenimports += collect_submodules('paddlex')


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='image_recognition',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='image_recognition',
)
