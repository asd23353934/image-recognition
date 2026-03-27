<!-- SPECTRA:START v1.0.1 -->

# Spectra Instructions

This project uses Spectra for Spec-Driven Development(SDD). Specs live in `openspec/specs/`, change proposals in `openspec/changes/`.

## Use `/spectra:*` skills when:

- A discussion needs structure before coding → `/spectra:discuss`
- User wants to plan, propose, or design a change → `/spectra:propose`
- Tasks are ready to implement → `/spectra:apply`
- There's an in-progress change to continue → `/spectra:ingest`
- User asks about specs or how something works → `/spectra:ask`
- Implementation is done → `/spectra:archive`

## Workflow

discuss? → propose → apply ⇄ ingest → archive

- `discuss` is optional — skip if requirements are clear
- Requirements change mid-work? Plan mode → `ingest` → resume `apply`

## Parked Changes

Changes can be parked（暫存）— temporarily moved out of `openspec/changes/`. Parked changes won't appear in `spectra list` but can be found with `spectra list --parked`. To restore: `spectra unpark <name>`. The `/spectra:apply` and `/spectra:ingest` skills handle parked changes automatically.

<!-- SPECTRA:END -->

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
