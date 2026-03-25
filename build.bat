@echo off
echo Building EXP Monitor...
echo.

REM 使用 PyInstaller 打包
pyinstaller --noconfirm --clean ^
    --name "exp_monitor" ^
    --icon "icon.ico" ^
    --noconsole ^
    --add-data "config.json;." ^
    --add-data "version.py;." ^
    --add-data "update_launcher.bat;." ^
    --hidden-import "paddle" ^
    --hidden-import "paddleocr" ^
    --hidden-import "PIL.PngImagePlugin" ^
    --hidden-import "PIL.JpegImagePlugin" ^
    --hidden-import "shapely" ^
    --hidden-import "pyclipper" ^
    --collect-submodules "paddle" ^
    --collect-submodules "paddleocr" ^
    main.py

echo.
if errorlevel 1 (
    echo Build FAILED!
) else (
    echo Build SUCCESS! Output in dist/exp_monitor/
)
pause
