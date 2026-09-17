"""Canonical monitors package.

The src tree is authoritative; the repository-root tree remains a compatibility
fallback for legacy root-only modules.
"""

from __future__ import annotations

from pathlib import Path

__root__ = Path(__file__).resolve().parent
__repo_root = __root__.parent.parent.parent
__canonical_root__ = __root__.resolve()
__fallback_root__ = (__repo_root / "enterpriseguard" / "monitors").resolve()
__path__ = [str(__canonical_root__), str(__fallback_root__)]

__all__ = []
