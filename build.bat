@echo off
echo Building Image Recognition...
echo.

REM 使用 PyInstaller 打包
pyinstaller --noconfirm --clean ^
    --name "image_recognition" ^
    --icon "icon.ico" ^
    --noconsole ^
    --add-data "config.json;." ^
    --add-data "version.py;." ^
    --add-data "update_launcher.bat;." ^
    --add-data "icon.ico;." ^
    --collect-binaries "paddle" ^
    --hidden-import "paddle" ^
    --hidden-import "paddleocr" ^
    --hidden-import "paddlex" ^
    --hidden-import "PIL.PngImagePlugin" ^
    --hidden-import "PIL.JpegImagePlugin" ^
    --hidden-import "shapely" ^
    --hidden-import "pyclipper" ^
    --hidden-import "cv2" ^
    --collect-submodules "cv2" ^
    --collect-submodules "paddle" ^
    --collect-submodules "paddleocr" ^
    --collect-submodules "paddlex" ^
    --collect-data "paddlex" ^
    main.py

echo.
if errorlevel 1 (
    echo Build FAILED!
) else (
    echo Build SUCCESS! Output in dist/image_recognition/
)
pause
