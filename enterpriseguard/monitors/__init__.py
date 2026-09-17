"""Compatibility boundary for enterpriseguard.monitors.

Canonical modules resolve from src/enterpriseguard/monitors first, with root-only
modules preserved as a fallback when no canonical source module exists.
"""

from __future__ import annotations

from pathlib import Path

__root__ = Path(__file__).resolve().parent
__repo_root__ = __root__.parent.parent
__canonical_root__ = (__repo_root / "src" / "enterpriseguard" / "monitors").resolve()
__fallback_root__ = __root__.resolve()
__path__ = [str(__canonical_root__), str(__fallback_root__)]

__all__ = []
