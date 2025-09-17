"""Python ctypes wrapper for the optional native language_engine library.

This module tries to load a native library `language_engine` from the
same folder and exposes two simple helpers:

 - get_current_language() -> str | None
 - set_current_language(lang: str) -> bool

If the native library isn't available the module falls back to an
in-memory implementation so callers can use the same API without
conditional code.
"""
from __future__ import annotations

import ctypes
import os
import platform
from typing import Optional

_lib = None
_fallback_lang = "en_US"


def _find_library_path() -> Optional[str]:
    base = os.path.join(os.path.dirname(__file__), "language_engine")
    system = platform.system().lower()
    exts = []
    if system == "windows":
        exts = [".dll"]
    elif system == "darwin":
        exts = [".dylib", ".so"]
    else:
        exts = [".so"]
    for ext in exts:
        p = base + ext
        if os.path.exists(p):
            return p
    return None


def _try_load_lib() -> Optional[ctypes.CDLL]:
    global _lib
    if _lib is not None:
        return _lib
    path = _find_library_path()
    if not path:
        return None
    try:
        _lib = ctypes.CDLL(path)
        # Configure functions
        try:
            _lib.get_current_language.restype = ctypes.c_char_p
        except Exception:
            pass
        try:
            _lib.set_current_language.argtypes = [ctypes.c_char_p]
            _lib.set_current_language.restype = ctypes.c_int
        except Exception:
            pass
        return _lib
    except Exception:
        _lib = None
        return None


def is_available() -> bool:
    """Return True if native language engine library is available."""
    return _try_load_lib() is not None


def get_current_language() -> Optional[str]:
    """Return the current language code as a string, or None if unknown."""
    lib = _try_load_lib()
    if lib is not None and hasattr(lib, 'get_current_language'):
        try:
            res = lib.get_current_language()
            if res is None:
                return None
            if isinstance(res, bytes):
                return res.decode('utf-8', errors='ignore')
            return str(res)
        except Exception:
            return None
    # fallback
    return _fallback_lang


def set_current_language(lang: str) -> bool:
    """Set the language code in the native library if present.

    Returns True on success (native or fallback), False on failure.
    """
    lib = _try_load_lib()
    if lib is not None and hasattr(lib, 'set_current_language'):
        try:
            b = lang.encode('utf-8')
            ret = lib.set_current_language(b)
            return int(ret) == 0
        except Exception:
            return False
    # fallback: set in-memory value
    global _fallback_lang
    try:
        _fallback_lang = str(lang)
        return True
    except Exception:
        return False


__all__ = ["is_available", "get_current_language", "set_current_language"]


