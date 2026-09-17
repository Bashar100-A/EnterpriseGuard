"""Compatibility boundary for enterpriseguard.security.

Canonical modules resolve from src/enterpriseguard/security first, with root-only
modules retained as a fallback compatibility surface where necessary.
"""

from __future__ import annotations

from pathlib import Path

__root__ = Path(__file__).resolve().parent
__repo_root__ = __root__.parent.parent
__canonical_root__ = (__repo_root / "src" / "enterpriseguard" / "security").resolve()
__fallback_root__ = __root__.resolve()
__path__ = [str(__canonical_root__), str(__fallback_root__)]

__all__ = []
