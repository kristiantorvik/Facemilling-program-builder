"""
Simple application-wide status bar helper.
Register a Tk label from the main UI and call `set_status()` from anywhere.
"""
from typing import Optional
import tkinter as tk

_status_label: Optional[tk.Label] = None
_clear_job = None
_orig_bg = None
_orig_fg = None
_text_var_name: Optional[str] = None
_tk_root = None


def register(label: tk.Label) -> None:
    """Register the Label widget to be used as the status bar and store original colors."""
    global _status_label, _orig_bg, _orig_fg
    _status_label = label
    try:
        _orig_bg = label.cget("bg")
        _orig_fg = label.cget("fg")
    except Exception:
        _orig_bg = None
        _orig_fg = None
    # Capture associated textvariable (if any) so we can update it
    try:
        varname = label.cget('textvariable')
        if varname:
            global _text_var_name, _tk_root
            _text_var_name = varname
            _tk_root = label._root()
    except Exception:
        pass


def set_status(message: str, timeout_ms: int = 0, level: str = "info") -> None:
    """Set status bar text and color.

    level: one of 'info', 'success', 'error', 'warning'
    """
    global _status_label, _clear_job, _orig_bg, _orig_fg
    if _status_label is None:
        return
    colors = {
        'info': {'bg': _orig_bg or 'SystemButtonFace', 'fg': _orig_fg or 'black'},
        'success': {'bg': '#d4edda', 'fg': '#155724'},
        'error': {'bg': '#f8d7da', 'fg': '#721c24'},
        'warning': {'bg': '#fff3cd', 'fg': '#856404'},
    }
    style = colors.get(level, colors['info'])
    # If label uses a textvariable, update that variable so StringVar reflects change.
    try:
        if _text_var_name and _tk_root:
            try:
                _tk_root.setvar(_text_var_name, message)
            except Exception:
                pass
        _status_label.config(bg=style['bg'], fg=style['fg'])
    except Exception:
        try:
            _status_label.config(text=message)
        except Exception:
            pass

    # Cancel pending clear
    try:
        if _clear_job:
            _status_label.after_cancel(_clear_job)
    except Exception:
        pass
    _clear_job = None

    if timeout_ms and timeout_ms > 0:
        def _clear():
            global _status_label, _clear_job, _orig_bg, _orig_fg, _text_var_name, _tk_root
            if _status_label:
                try:
                    if _text_var_name and _tk_root:
                        try:
                            _tk_root.setvar(_text_var_name, "")
                        except Exception:
                            pass
                    _status_label.config(text="", bg=_orig_bg or 'SystemButtonFace', fg=_orig_fg or 'black')
                except Exception:
                    try:
                        _status_label.config(text="")
                    except Exception:
                        pass
            _clear_job = None

        _clear_job = _status_label.after(timeout_ms, _clear)


def clear() -> None:
    """Clear the status bar immediately and restore original colors."""
    global _status_label, _orig_bg, _orig_fg
    if _status_label is None:
        return
    try:
        if _text_var_name and _tk_root:
            try:
                _tk_root.setvar(_text_var_name, "")
            except Exception:
                pass
        _status_label.config(text="", bg=_orig_bg or 'SystemButtonFace', fg=_orig_fg or 'black')
    except Exception:
        try:
            _status_label.config(text="")
        except Exception:
            pass
