"""Compatibility boundary for the canonical decision package.

Imports resolve to the source tree under src/enterpriseguard/decision.
"""

from __future__ import annotations

from pathlib import Path

__root__ = Path(__file__).resolve().parent
__repo_root__ = __root__.parent.parent
__canonical_root__ = (__repo_root / "src" / "enterpriseguard" / "decision").resolve()
__fallback_root__ = __root__.resolve()
__path__ = [str(__canonical_root__), str(__fallback_root__)]

__all__ = []
