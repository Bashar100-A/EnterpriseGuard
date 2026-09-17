"""Compatibility boundary for the canonical EnterpriseGuard package.

Repository-root execution prefers the source tree under src/enterpriseguard while
retaining the repo-root tree as a temporary fallback compatibility boundary.
"""

from __future__ import annotations

from pathlib import Path

__root__ = Path(__file__).resolve().parent
__repo_root__ = __root__.parent
__canonical_root__ = (__repo_root__ / "src" / "enterpriseguard").resolve()
__fallback_root__ = (__repo_root__ / "enterpriseguard").resolve()
__path__ = [str(__canonical_root__), str(__fallback_root__)]

__all__ = []
