"""
EnterpriseGuard ADIE - State Checkpoint Layer
=============================================

Version
-------
2.0.0

Purpose
-------
Immutable, integrity-verifiable state checkpoint boundary
for the Adaptive Defense Intelligence Engine (ADIE).

Architecture
------------

    Security State
          |
          v
    Checkpoint Layer
          |
          +--> Immutable Snapshot
          +--> Decision Lineage
          +--> Integrity Verification
          +--> Audit Metadata
          |
          v
    Future Rollback Coordinator
          |
          v
    Authorized Response Layer


Security Boundary
-----------------
This module stores and verifies historical state.

It DOES NOT:

- execute rollback
- restore systems
- modify infrastructure
- execute commands
- invoke response adapters
- perform remediation


Design Principles
-----------------

1. Immutable historical evidence.
2. Deep-copy isolation.
3. Cryptographic integrity verification.
4. Complete ADIE lineage preservation.
5. Deterministic serialization.
6. JSON-compatible export.
7. Fail-safe validation.
8. Separation of evidence and authority.
9. Planning support without execution.
10. Future rollback compatibility.
"""

from __future__ import annotations


from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Mapping, Optional
import copy
import json


__all__ = [
    "MODULE_VERSION",
    "CheckpointError",
    "CheckpointValidationError",
    "CheckpointIntegrityError",
    "CheckpointStatus",
    "CheckpointContext",
    "StateCheckpoint",
    "CheckpointManager",
    "get_checkpoint_manager",
]


MODULE_VERSION = "2.0.0"


# ======================================================================
# Exceptions
# ======================================================================


class CheckpointError(Exception):
    """
    Base checkpoint exception.
    """


class CheckpointValidationError(
    CheckpointError
):
    """
    Raised when checkpoint data is invalid.
    """


class CheckpointIntegrityError(
    CheckpointError
):
    """
    Raised when checkpoint integrity fails.
    """



# ======================================================================
# Enumerations
# ======================================================================


class CheckpointStatus(
    str,
    Enum,
):
    """
    Checkpoint lifecycle state.
    """

    CREATED = "created"

    VERIFIED = "verified"

    INVALID = "invalid"



# ======================================================================
# Utility Functions
# ======================================================================


def _utc_now() -> str:
    """
    Return ISO-8601 UTC timestamp.
    """

    return datetime.now(
        timezone.utc
    ).isoformat()



def _freeze(
    value: Any,
) -> Any:
    """
    Recursively convert objects into immutable structures.
    """

    if isinstance(
        value,
        Mapping,
    ):
        return MappingProxyType(
            {
                key: _freeze(item)
                for key, item in value.items()
            }
        )


    if isinstance(
        value,
        (list, tuple),
    ):
        return tuple(
            _freeze(item)
            for item in value
        )


    if isinstance(
        value,
        (set, frozenset),
    ):
        return frozenset(
            _freeze(item)
            for item in value
        )


    try:

        return copy.deepcopy(
            value
        )

    except Exception as exc:

        raise CheckpointValidationError(
            "Unable to freeze value"
        ) from exc



def _thaw(
    value: Any,
) -> Any:
    """
    Convert immutable checkpoint data into
    detached export representation.
    """

    if isinstance(
        value,
        Mapping,
    ):
        return {
            key: _thaw(item)
            for key, item in value.items()
        }


    if isinstance(
        value,
        tuple,
    ):
        return [
            _thaw(item)
            for item in value
        ]


    if isinstance(
        value,
        (set, frozenset),
    ):
        return [
            _thaw(item)
            for item in value
        ]


    return copy.deepcopy(
        value
    )



# ======================================================================
# Checkpoint Context
# ======================================================================


@dataclass(
    frozen=True
)
class CheckpointContext:
    """
    ADIE lineage context.

    Connects checkpoint history with the
    decision pipeline:

        State
          |
        Prediction
          |
        Policy
          |
        Decision
          |
        Playbook
          |
        Checkpoint
    """

    state_id: Optional[str] = None

    prediction_id: Optional[str] = None

    decision_id: Optional[str] = None

    playbook_id: Optional[str] = None


    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "state_id": self.state_id,
            "prediction_id": self.prediction_id,
            "decision_id": self.decision_id,
            "playbook_id": self.playbook_id,
        }



# ======================================================================
# State Checkpoint Contract
# ======================================================================


@dataclass(
    frozen=True
)
class StateCheckpoint:
    """
    Immutable ADIE checkpoint object.

    Represents historical evidence only.

    It can prove that stored data has not changed.

    It cannot prove that the original state was true.
    """

    checkpoint_id: str

    created_at: str

    context: CheckpointContext

    state: Mapping[str, Any]


    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )


    integrity_hash: str = ""


    status: CheckpointStatus = (
        CheckpointStatus.CREATED
    )


    immutable: bool = True


    executes_security_actions: bool = False


    def __post_init__(
        self,
    ) -> None:

        if not self.checkpoint_id:

            raise CheckpointValidationError(
                "checkpoint_id cannot be empty"
            )


        if not isinstance(
            self.context,
            CheckpointContext,
        ):

            raise CheckpointValidationError(
                "invalid checkpoint context"
            )


        object.__setattr__(
            self,
            "state",
            _freeze(
                self.state
            ),
        )


        object.__setattr__(
            self,
            "metadata",
            _freeze(
                self.metadata
            ),
        )
    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Return detached JSON-compatible representation.
        """

        return {
            "checkpoint_id": self.checkpoint_id,
            "created_at": self.created_at,
            "context": self.context.to_dict(),
            "state": _thaw(self.state),
            "metadata": _thaw(self.metadata),
            "integrity_hash": self.integrity_hash,
            "status": self.status.value,
            "immutable": self.immutable,
            "executes_security_actions": (
                self.executes_security_actions
            ),
        }



# ======================================================================
# Checkpoint Manager
# ======================================================================


class CheckpointManager:
    """
    ADIE checkpoint management subsystem.

    Responsibilities
    ----------------
    - Create immutable checkpoints.
    - Store historical evidence.
    - Verify integrity.
    - Compare historical states.
    - Maintain lifecycle.

    Non Responsibilities
    --------------------
    - Rollback.
    - Restoration.
    - Execution.
    """


    VERSION = MODULE_VERSION


    def __init__(
        self,
        *,
        max_checkpoints: int = 100,
    ) -> None:


        if isinstance(
            max_checkpoints,
            bool,
        ) or not isinstance(
            max_checkpoints,
            int,
        ):

            raise CheckpointValidationError(
                "max_checkpoints must be integer"
            )


        if max_checkpoints < 1:

            raise CheckpointValidationError(
                "max_checkpoints must be greater than zero"
            )


        self._max_checkpoints = (
            max_checkpoints
        )


        self._checkpoints: dict[
            str,
            StateCheckpoint,
        ] = {}


        self._order: list[str] = []


        self._sequence = 0



    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------


    def create(
        self,
        state: Mapping[str, Any],
        *,
        context: Optional[
            CheckpointContext
        ] = None,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> StateCheckpoint:
        """
        Create immutable checkpoint.
        """


        if not isinstance(
            state,
            Mapping,
        ):

            raise CheckpointValidationError(
                "state must be mapping"
            )


        if context is None:

            context = CheckpointContext()


        if not isinstance(
            context,
            CheckpointContext,
        ):

            raise CheckpointValidationError(
                "invalid context"
            )


        normalized_state = copy.deepcopy(
            dict(state)
        )


        normalized_metadata = copy.deepcopy(
            dict(
                metadata or {}
            )
        )


        self._sequence += 1


        created_at = _utc_now()


        checkpoint_id = (
            self._generate_id(
                normalized_state,
                context,
                created_at,
                self._sequence,
            )
        )


        integrity_hash = (
            self._calculate_hash(
                checkpoint_id,
                created_at,
                context,
                normalized_state,
                normalized_metadata,
            )
        )


        checkpoint = StateCheckpoint(
            checkpoint_id=checkpoint_id,
            created_at=created_at,
            context=context,
            state=normalized_state,
            metadata=normalized_metadata,
            integrity_hash=integrity_hash,
            status=CheckpointStatus.CREATED,
            immutable=True,
            executes_security_actions=False,
        )


        self._checkpoints[
            checkpoint_id
        ] = checkpoint


        self._order.append(
            checkpoint_id
        )


        self._enforce_capacity()


        return checkpoint



    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------


    def get(
        self,
        checkpoint_id: str,
    ) -> Optional[StateCheckpoint]:
        """
        Retrieve checkpoint.
        """

        return self._checkpoints.get(
            checkpoint_id
        )



    def latest(
        self,
    ) -> Optional[StateCheckpoint]:
        """
        Return newest checkpoint.
        """

        if not self._order:

            return None


        return self._checkpoints.get(
            self._order[-1]
        )



    def list_checkpoints(
        self,
    ) -> tuple[StateCheckpoint, ...]:
        """
        Return immutable checkpoint collection.
        """

        return tuple(
            self._checkpoints[item]
            for item in self._order
            if item in self._checkpoints
        )



    # ------------------------------------------------------------------
    # Integrity
    # ------------------------------------------------------------------


    def verify(
        self,
        checkpoint: StateCheckpoint,
    ) -> bool:
        """
        Verify checkpoint fingerprint.
        """


        if not isinstance(
            checkpoint,
            StateCheckpoint,
        ):

            raise CheckpointValidationError(
                "invalid checkpoint"
            )


        expected = (
            self._calculate_hash(
                checkpoint.checkpoint_id,
                checkpoint.created_at,
                checkpoint.context,
                checkpoint.state,
                checkpoint.metadata,
            )
        )


        return (
            expected
            ==
            checkpoint.integrity_hash
        )



    def require_valid(
        self,
        checkpoint: StateCheckpoint,
    ) -> StateCheckpoint:
        """
        Validate checkpoint or raise error.
        """


        if not self.verify(
            checkpoint
        ):

            raise CheckpointIntegrityError(
                "checkpoint integrity failed"
            )


        return checkpoint



    # ------------------------------------------------------------------
    # Comparison
    # ------------------------------------------------------------------


    def compare(
        self,
        first: StateCheckpoint,
        second: StateCheckpoint,
    ) -> dict[str, Any]:
        """
        Compare two historical states.
        """


        self.require_valid(
            first
        )

        self.require_valid(
            second
        )


        first_state = _thaw(
            first.state
        )

        second_state = _thaw(
            second.state
        )


        first_keys = set(
            first_state.keys()
        )

        second_keys = set(
            second_state.keys()
        )


        changed = []


        for key in sorted(
            first_keys
            &
            second_keys
        ):

            if (
                first_state[key]
                !=
                second_state[key]
            ):

                changed.append(
                    key
                )


        return {

            "first_checkpoint_id":
                first.checkpoint_id,

            "second_checkpoint_id":
                second.checkpoint_id,

            "added_keys":
                sorted(
                    second_keys-first_keys
                ),

            "removed_keys":
                sorted(
                    first_keys-second_keys
                ),

            "changed_keys":
                changed,

            "changed":
                bool(
                    changed
                    or
                    first_keys != second_keys
                ),

        }



    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------


    def status(
        self,
    ) -> dict[str, Any]:

        return {

            "module":
                "adie.checkpoint",

            "version":
                MODULE_VERSION,

            "checkpoint_count":
                len(
                    self._checkpoints
                ),

            "max_checkpoints":
                self._max_checkpoints,

            "executes_security_actions":
                False,

        }



    def health_check(
        self,
    ) -> dict[str, Any]:

        return {

            "healthy":
                len(
                    self._checkpoints
                )
                <=
                self._max_checkpoints,

            "module":
                "adie.checkpoint",

            "version":
                MODULE_VERSION,

            "executes_security_actions":
                False,

        }
    # ------------------------------------------------------------------
    # Self Test
    # ------------------------------------------------------------------

    def self_test(
        self,
    ) -> dict[str, Any]:
        """
        Execute deterministic checkpoint subsystem tests.

        Tests:
        - creation
        - immutable isolation
        - integrity verification
        - lineage preservation
        - comparison
        - JSON export
        - security boundary
        """

        tests: dict[str, bool] = {}

        try:

            self._checkpoints.clear()
            self._order.clear()
            self._sequence = 0


            # ----------------------------------------------------------
            # Test 1: Creation
            # ----------------------------------------------------------

            context = CheckpointContext(
                state_id="state-test",
                prediction_id="prediction-test",
                decision_id="decision-test",
                playbook_id="playbook-test",
            )


            source_state = {
                "risk": 0.85,
                "asset": {
                    "name": "server-01",
                    "tags": [
                        "production",
                        "critical",
                    ],
                },
            }


            checkpoint = self.create(
                source_state,
                context=context,
                metadata={
                    "source": "self-test",
                },
            )


            tests["creation"] = (
                isinstance(
                    checkpoint,
                    StateCheckpoint,
                )
                and bool(
                    checkpoint.checkpoint_id
                )
            )


            # ----------------------------------------------------------
            # Test 2: Source isolation
            # ----------------------------------------------------------

            source_state["risk"] = 0.01

            source_state["asset"]["name"] = (
                "modified"
            )

            source_state["asset"]["tags"].append(
                "tampered"
            )


            tests["deep_copy_isolation"] = (
                checkpoint.state["risk"]
                == 0.85

                and checkpoint.state["asset"]["name"]
                == "server-01"

                and tuple(
                    checkpoint.state["asset"]["tags"]
                )
                ==
                (
                    "production",
                    "critical",
                )
            )


            # ----------------------------------------------------------
            # Test 3: Integrity
            # ----------------------------------------------------------

            tests["integrity"] = (
                self.verify(
                    checkpoint
                )
                is True
            )


            # ----------------------------------------------------------
            # Test 4: Lineage
            # ----------------------------------------------------------

            tests["lineage"] = (
                checkpoint.context.state_id
                == "state-test"

                and checkpoint.context.prediction_id
                == "prediction-test"

                and checkpoint.context.decision_id
                == "decision-test"

                and checkpoint.context.playbook_id
                == "playbook-test"
            )


            # ----------------------------------------------------------
            # Test 5: Immutability
            # ----------------------------------------------------------

            immutable = True


            try:

                checkpoint.state[
                    "risk"
                ] = 0.5

                immutable = False

            except Exception:

                pass


            tests["immutability"] = immutable


            # ----------------------------------------------------------
            # Test 6: Comparison
            # ----------------------------------------------------------

            second = self.create(
                {
                    "risk": 0.95,
                    "asset": {
                        "name": "server-01",
                        "tags": [
                            "production",
                            "critical",
                        ],
                    },
                },
                context=context,
            )


            comparison = self.compare(
                checkpoint,
                second,
            )


            tests["comparison"] = (
                comparison["changed"]
                is True

                and "risk"
                in comparison["changed_keys"]
            )


            # ----------------------------------------------------------
            # Test 7: JSON export
            # ----------------------------------------------------------

            try:

                json.dumps(
                    checkpoint.to_dict(),
                    ensure_ascii=False,
                    sort_keys=True,
                )

                json_ok = True

            except Exception:

                json_ok = False


            tests["json_export"] = json_ok


            # ----------------------------------------------------------
            # Test 8: Security boundary
            # ----------------------------------------------------------

            tests["security_boundary"] = (
                checkpoint.executes_security_actions
                is False

                and second.executes_security_actions
                is False
            )


            # ----------------------------------------------------------
            # Test 9: Health
            # ----------------------------------------------------------

            health = self.health_check()


            tests["health"] = (
                health.get(
                    "healthy"
                )
                is True
            )


            passed = all(
                tests.values()
            )


            return {
                "passed": passed,
                "module": "adie.checkpoint",
                "version": MODULE_VERSION,
                "checkpoint_test_passed": passed,
                "tests": tests,
                "executes_security_actions": False,
            }


        except Exception as exc:

            return {
                "passed": False,
                "module": "adie.checkpoint",
                "version": MODULE_VERSION,
                "checkpoint_test_passed": False,
                "tests": tests,
                "error": str(exc),
                "executes_security_actions": False,
            }
            
                    
    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _canonical_payload(
        *,
        checkpoint_id: str,
        created_at: str,
        context: CheckpointContext,
        state: Mapping[str, Any],
        metadata: Mapping[str, Any],
    ) -> str:
        """
        Create deterministic canonical representation.

        Used for integrity hashing.
        """

        payload = {
            "checkpoint_id": checkpoint_id,
            "created_at": created_at,
            "context": context.to_dict(),
            "state": _thaw(state),
            "metadata": _thaw(metadata),
        }


        return json.dumps(
            payload,
            sort_keys=True,
            separators=(
                ",",
                ":",
            ),
            ensure_ascii=False,
            default=str,
        )



    @classmethod
    def _calculate_hash(
        cls,
        checkpoint_id: str,
        created_at: str,
        context: CheckpointContext,
        state: Mapping[str, Any],
        metadata: Mapping[str, Any],
    ) -> str:
        """
        Calculate SHA-256 checkpoint fingerprint.
        """

        payload = cls._canonical_payload(
            checkpoint_id=checkpoint_id,
            created_at=created_at,
            context=context,
            state=state,
            metadata=metadata,
        )


        return sha256(
            payload.encode(
                "utf-8"
            )
        ).hexdigest()



    @staticmethod
    def _generate_id(
        state: Mapping[str, Any],
        context: CheckpointContext,
        created_at: str,
        sequence: int,
    ) -> str:
        """
        Generate deterministic checkpoint identifier.
        """

        payload = {
            "state": _thaw(
                state
            ),
            "context": context.to_dict(),
            "created_at": created_at,
            "sequence": sequence,
        }


        serialized = json.dumps(
            payload,
            sort_keys=True,
            separators=(
                ",",
                ":",
            ),
            ensure_ascii=False,
            default=str,
        )


        digest = sha256(
            serialized.encode(
                "utf-8"
            )
        ).hexdigest()[:20]


        return (
            f"chk-{digest}"
        )



    def _enforce_capacity(
        self,
    ) -> None:
        """
        Remove oldest checkpoints when capacity exceeded.
        """

        while (
            len(
                self._order
            )
            >
            self._max_checkpoints
        ):

            oldest = self._order.pop(
                0
            )


            self._checkpoints.pop(
                oldest,
                None,
            )



# ======================================================================
# Default Manager
# ======================================================================


_default_manager: Optional[
    CheckpointManager
] = None



def get_checkpoint_manager(
) -> CheckpointManager:
    """
    Return process-local ADIE checkpoint manager.
    """

    global _default_manager


    if _default_manager is None:

        _default_manager = CheckpointManager()


    return _default_manager



# ======================================================================
# Module Entry Point
# ======================================================================


def _main() -> int:
    """
    Execute checkpoint self-test.
    """

    manager = CheckpointManager()


    result = manager.self_test()


    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )


    return (
        0
        if result.get(
            "passed"
        )
        else 1
    )



if __name__ == "__main__":

    raise SystemExit(
        _main()
    )        