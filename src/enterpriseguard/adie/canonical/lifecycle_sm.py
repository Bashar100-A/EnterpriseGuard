"""Canonical Decision Lifecycle state machine (Stage 3B).

Single ownership point for legal/illegal transitions. No scattered
`if status == ...` allowed elsewhere.

The machine does NOT execute security actions.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet

from .lifecycle import DecisionLifecycle


L = DecisionLifecycle


# Directed edges. Each source state maps to the set of legal next states.
_LEGAL: dict[DecisionLifecycle, FrozenSet[DecisionLifecycle]] = {
    L.PROPOSED:          frozenset({L.VALIDATED, L.CLOSED}),
    L.VALIDATED:         frozenset({L.AUTHORIZED, L.CLOSED}),
    L.AUTHORIZED:        frozenset({L.EMITTED, L.CLOSED}),
    L.EMITTED:           frozenset({L.EXECUTED_EXTERNAL, L.CLOSED}),
    L.EXECUTED_EXTERNAL: frozenset({L.OBSERVED, L.CLOSED}),
    L.OBSERVED:          frozenset({L.ASSESSED, L.CLOSED}),
    L.ASSESSED:          frozenset({L.CLOSED}),
    L.CLOSED:            frozenset(),
}

# Terminal states (no outgoing transitions).
TERMINAL: FrozenSet[DecisionLifecycle] = frozenset({L.CLOSED})

# External boundary: only EXECUTED_EXTERNAL crosses it (as observation).
# ADIE never performs this transition itself; it records what the outside
# world did.
EXTERNAL_OBSERVATION_ENTRY: DecisionLifecycle = L.EXECUTED_EXTERNAL


class LifecycleTransitionError(ValueError):
    """Raised on illegal lifecycle transition."""


@dataclass(frozen=True)
class LifecycleTransition:
    src: DecisionLifecycle
    dst: DecisionLifecycle
    external: bool  # True if this is an external-boundary observation


def legal_transitions(src: DecisionLifecycle) -> FrozenSet[DecisionLifecycle]:
    return _LEGAL.get(src, frozenset())


def is_legal(src: DecisionLifecycle, dst: DecisionLifecycle) -> bool:
    return dst in _LEGAL.get(src, frozenset())


def require_legal(src: DecisionLifecycle, dst: DecisionLifecycle) -> None:
    if not is_legal(src, dst):
        raise LifecycleTransitionError(
            f"illegal lifecycle transition: {src.value} -> {dst.value}"
        )


def transition(
    src: DecisionLifecycle,
    dst: DecisionLifecycle,
    *,
    external_observation: bool = False,
) -> LifecycleTransition:
    """Validate and return a transition record.

    If dst == EXECUTED_EXTERNAL, the caller MUST set external_observation=True
    to make the external-boundary crossing explicit.
    """
    require_legal(src, dst)
    if dst is EXTERNAL_OBSERVATION_ENTRY and not external_observation:
        raise LifecycleTransitionError(
            "transition to EXECUTED_EXTERNAL requires external_observation=True"
        )
    return LifecycleTransition(
        src=src,
        dst=dst,
        external=(dst is EXTERNAL_OBSERVATION_ENTRY),
    )


def all_states() -> FrozenSet[DecisionLifecycle]:
    return frozenset(_LEGAL.keys())


__all__ = [
    "LifecycleTransition",
    "LifecycleTransitionError",
    "TERMINAL",
    "EXTERNAL_OBSERVATION_ENTRY",
    "legal_transitions",
    "is_legal",
    "require_legal",
    "transition",
    "all_states",
]
