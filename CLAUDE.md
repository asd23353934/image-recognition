# Image Recognition - OCR Experience Monitor

## Overview
PySide6 desktop app using PaddleOCR to monitor game window EXP values and estimate leveling rates.

## Tech Stack
- GUI: PySide6
- OCR: PaddleOCR (paddlepaddle + paddleocr)
- Capture: mss + win32gui
- Packaging: PyInstaller

## Architecture
```
src/core/   # Business logic (no Qt dependency)
src/ui/     # PySide6 UI layer
```

## Conventions
- All UI updates on main thread (via Signal/Slot)
- OCR runs in QThread
- Config via ConfigManager
- Theme via AppTheme
- Paths via helpers.resource_path() / user_path()

## Key Files
- `version.py` - Version constant
- `config.json` - User settings persistence
- `src/core/ocr_engine.py` - PaddleOCR wrapper
- `src/core/exp_calculator.py` - EXP calculation logic
- `src/core/record_storage.py` - SQLite session/reading storage
- `src/ui/pages/exp_monitor_page.py` - Main page
- `src/ui/widgets/float_window.py` - Float window
- `src/ui/widgets/exp_chart.py` - EXP line chart
- `src/ui/dialogs/history_dialog.py` - History records viewer
