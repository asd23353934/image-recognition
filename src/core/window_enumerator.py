"""
視窗列舉模組
使用 Win32 API 列出可見的應用程式視窗
"""

import win32gui
import win32con


def list_windows() -> list[dict]:
    """列出所有可見的應用程式視窗

    Returns:
        [{"hwnd": int, "title": str}, ...]
    """
    results = []

    def _enum_callback(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        if win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) & win32con.WS_EX_TOOLWINDOW:
            return
        title = win32gui.GetWindowText(hwnd)
        if not title or title in ("Program Manager", "MSCTFIME UI"):
            return
        results.append({"hwnd": hwnd, "title": title})

    win32gui.EnumWindows(_enum_callback, None)
    return results


def get_window_rect(hwnd: int) -> tuple[int, int, int, int] | None:
    """取得視窗位置與大小

    Returns:
        (left, top, width, height) 或 None
    """
    try:
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        return (left, top, right - left, bottom - top)
    except Exception:
        return None


def is_window_valid(hwnd: int) -> bool:
    """檢查視窗是否仍然有效"""
    return bool(win32gui.IsWindow(hwnd))
