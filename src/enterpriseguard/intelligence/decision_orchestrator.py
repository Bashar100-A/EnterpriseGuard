"""
EnterpriseGuard - Decision Orchestrator
=======================================

Responsible for:

- Receiving DetectionServiceResult.
- Reading the already-established detection decision.
- Routing the result into an in-memory queue.
- Maintaining a strict separation between detection and response.

Architecture:

    DetectionService
           |
           v
    DecisionOrchestrator
           |
           +---- ESCALATE ---> escalation queue
           |
           +---- ALERT ------> alert queue
           |
           +---- IGNORE -----> no action


Important architectural restrictions:

- This module imports only from detection_service.py.
- No Detector access.
- No ModelManager access.
- No ModelLoader access.
- No ModelRegistry access.
- No training access.
- No pickle.
- No shell execution.
- No network operations.
- No security actions.
- No external system integrations.

This layer only routes decisions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .detection_service import DetectionServiceResult


# ============================================================================
# Decision constants
# ============================================================================

ESCALATE = "ESCALATE"
ALERT = "ALERT"
IGNORE = "IGNORE"


# ============================================================================
# Orchestration Result
# ============================================================================

@dataclass(frozen=True)
class OrchestrationResult:
    """
    Result produced after the DecisionOrchestrator handles a
    DetectionServiceResult.

    The result describes what the orchestrator did internally.

    No external security action is performed.
    """

    decision: str
    queued: bool
    queue_type: str | None = None
    error: str | None = None

    @property
    def success(self) -> bool:
        """
        Return True when orchestration completed without an error.
        """

        return self.error is None

    def to_dict(self) -> dict[str, Any]:
        """Return the orchestration result as a plain dictionary."""

        return asdict(self)


# ============================================================================
# Decision Orchestrator
# ============================================================================

class DecisionOrchestrator:
    """
    Routes detection decisions into in-memory queues.

    The orchestrator does not perform the action represented by the
    decision.

    For example:

        ESCALATE
            -> stores the result in escalation queue

        ALERT
            -> stores the result in alert queue

        IGNORE
            -> stores nothing

    The queues are intentionally in-memory only.
    """

    def __init__(self) -> None:
        """
        Initialize empty decision queues.
        """

        self._escalation_queue: list[DetectionServiceResult] = []
        self._alert_queue: list[DetectionServiceResult] = []

    # ------------------------------------------------------------------------
    # Primary API
    # ------------------------------------------------------------------------

    def handle(
        self,
        result: DetectionServiceResult,
    ) -> OrchestrationResult:
        """
        Handle one DetectionServiceResult.

        Rules:

            1. Invalid result -> safe failure.
            2. Result containing error -> no queue insertion.
            3. ESCALATE -> escalation queue.
            4. ALERT -> alert queue.
            5. IGNORE -> no action.

        No external action is performed.
        """

        if not isinstance(result, DetectionServiceResult):
            return OrchestrationResult(
                decision=IGNORE,
                queued=False,
                error=(
                    "result must be a DetectionServiceResult"
                ),
            )

        # --------------------------------------------------------------------
        # Safety rule:
        #
        # Never queue a failed detection result.
        # --------------------------------------------------------------------

        if result.error is not None:
            return OrchestrationResult(
                decision=result.decision,
                queued=False,
                queue_type=None,
                error=(
                    "Detection result contains an error; "
                    "no orchestration action was queued"
                ),
            )

        decision = self._normalize_decision(result.decision)

        if decision == ESCALATE:
            self._escalation_queue.append(result)

            return OrchestrationResult(
                decision=ESCALATE,
                queued=True,
                queue_type="escalation",
            )

        if decision == ALERT:
            self._alert_queue.append(result)

            return OrchestrationResult(
                decision=ALERT,
                queued=True,
                queue_type="alert",
            )

        if decision == IGNORE:
            return OrchestrationResult(
                decision=IGNORE,
                queued=False,
                queue_type=None,
            )

        return OrchestrationResult(
            decision=decision,
            queued=False,
            queue_type=None,
            error=(
                f"Unsupported decision: {decision}"
            ),
        )

    # ------------------------------------------------------------------------
    # Queue access
    # ------------------------------------------------------------------------

    def get_escalation_queue(
        self,
    ) -> list[DetectionServiceResult]:
        """
        Return a snapshot of the escalation queue.

        A copy is returned so callers cannot directly mutate the
        orchestrator's internal queue.
        """

        return list(self._escalation_queue)

    def get_alert_queue(
        self,
    ) -> list[DetectionServiceResult]:
        """
        Return a snapshot of the alert queue.

        A copy is returned so callers cannot directly mutate the
        orchestrator's internal queue.
        """

        return list(self._alert_queue)

    def clear_queues(self) -> None:
        """
        Clear all pending orchestration entries.
        """

        self._escalation_queue.clear()
        self._alert_queue.clear()

    # ------------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------------

    @staticmethod
    def _normalize_decision(
        decision: Any,
    ) -> str:
        """
        Normalize a decision into its canonical string representation.
        """

        if decision is None:
            return ""

        return str(decision).strip().upper()


# ============================================================================
# Self-Test
# ============================================================================

def self_test() -> bool:
    """
    Lightweight isolated Self-Test.

    The test creates DetectionServiceResult objects directly.

    No:

    - model
    - detector
    - training component
    - filesystem operation
    - network operation
    - shell operation
    - security action

    is required.
    """

    # ------------------------------------------------------------------------
    # Test 1:
    # Queues must be empty at initialization.
    # ------------------------------------------------------------------------

    orchestrator = DecisionOrchestrator()

    assert orchestrator.get_escalation_queue() == []
    assert orchestrator.get_alert_queue() == []

    # ------------------------------------------------------------------------
    # Test 2:
    # ESCALATE -> escalation queue.
    # ------------------------------------------------------------------------

    escalate_result = DetectionServiceResult(
        decision=ESCALATE,
        predicted_class="threat",
        threat_probability=0.95,
        benign_probability=0.05,
        anomaly_score=0.90,
        confidence=0.96,
        model_version="self-test-model",
        error=None,
    )

    orchestration = orchestrator.handle(
        escalate_result
    )

    assert orchestration.success is True
    assert orchestration.decision == ESCALATE
    assert orchestration.queued is True
    assert orchestration.queue_type == "escalation"

    escalation_queue = (
        orchestrator.get_escalation_queue()
    )

    assert len(escalation_queue) == 1
    assert escalation_queue[0] is escalate_result

    assert orchestrator.get_alert_queue() == []

    # ------------------------------------------------------------------------
    # Test 3:
    # ALERT -> alert queue.
    # ------------------------------------------------------------------------

    alert_result = DetectionServiceResult(
        decision=ALERT,
        predicted_class="threat",
        threat_probability=0.75,
        benign_probability=0.25,
        anomaly_score=0.70,
        confidence=0.80,
        model_version="self-test-model",
        error=None,
    )

    orchestration = orchestrator.handle(
        alert_result
    )

    assert orchestration.success is True
    assert orchestration.decision == ALERT
    assert orchestration.queued is True
    assert orchestration.queue_type == "alert"

    alert_queue = orchestrator.get_alert_queue()

    assert len(alert_queue) == 1
    assert alert_queue[0] is alert_result

    # ------------------------------------------------------------------------
    # Test 4:
    # IGNORE -> no queue insertion.
    # ------------------------------------------------------------------------

    ignore_result = DetectionServiceResult(
        decision=IGNORE,
        predicted_class="benign",
        threat_probability=0.10,
        benign_probability=0.90,
        anomaly_score=0.05,
        confidence=0.20,
        model_version="self-test-model",
        error=None,
    )

    orchestration = orchestrator.handle(
        ignore_result
    )

    assert orchestration.success is True
    assert orchestration.decision == IGNORE
    assert orchestration.queued is False
    assert orchestration.queue_type is None

    assert len(
        orchestrator.get_escalation_queue()
    ) == 1

    assert len(
        orchestrator.get_alert_queue()
    ) == 1

    # ------------------------------------------------------------------------
    # Test 5:
    # Result with error must not be escalated.
    # ------------------------------------------------------------------------

    error_result = DetectionServiceResult(
        decision=ESCALATE,
        predicted_class=None,
        threat_probability=None,
        benign_probability=None,
        anomaly_score=None,
        confidence=None,
        model_version=None,
        error="No active model",
    )

    escalation_count_before = len(
        orchestrator.get_escalation_queue()
    )

    alert_count_before = len(
        orchestrator.get_alert_queue()
    )

    orchestration = orchestrator.handle(
        error_result
    )

    assert orchestration.success is False
    assert orchestration.queued is False
    assert orchestration.queue_type is None
    assert orchestration.error is not None

    assert len(
        orchestrator.get_escalation_queue()
    ) == escalation_count_before

    assert len(
        orchestrator.get_alert_queue()
    ) == alert_count_before

    # ------------------------------------------------------------------------
    # Test 6:
    # Queue access returns copies, not internal lists.
    # ------------------------------------------------------------------------

    external_escalation_queue = (
        orchestrator.get_escalation_queue()
    )

    external_escalation_queue.clear()

    assert len(
        orchestrator.get_escalation_queue()
    ) == escalation_count_before

    # ------------------------------------------------------------------------
    # Test 7:
    # clear_queues() must empty both queues.
    # ------------------------------------------------------------------------

    orchestrator.clear_queues()

    assert orchestrator.get_escalation_queue() == []
    assert orchestrator.get_alert_queue() == []

    # ------------------------------------------------------------------------
    # Test 8:
    # Invalid result must fail safely.
    # ------------------------------------------------------------------------

    invalid_result = orchestrator.handle(
        None  # type: ignore[arg-type]
    )

    assert invalid_result.success is False
    assert invalid_result.queued is False
    assert invalid_result.error is not None

    # ------------------------------------------------------------------------
    # Test 9:
    # Unsupported decisions must not be queued.
    # ------------------------------------------------------------------------

    unsupported_result = DetectionServiceResult(
        decision="UNKNOWN",
        predicted_class="unknown",
        threat_probability=0.50,
        benign_probability=0.50,
        anomaly_score=0.50,
        confidence=0.50,
        model_version="self-test-model",
        error=None,
    )

    orchestration = orchestrator.handle(
        unsupported_result
    )

    assert orchestration.success is False
    assert orchestration.queued is False
    assert orchestration.error is not None

    assert orchestrator.get_escalation_queue() == []
    assert orchestrator.get_alert_queue() == []

    return True


# ============================================================================
# Module execution
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("EnterpriseGuard - Decision Orchestrator Self-Test")
    print("=" * 60)

    try:
        self_test()

        print("Self-Test: PASS")
        print("Decision Orchestrator is operational.")

    except AssertionError as exc:
        print("Self-Test: FAIL")
        print(f"Assertion error: {exc}")
        raise SystemExit(1)

    except Exception as exc:
        print("Self-Test: FAIL")
        print(f"Unexpected error: {exc}")
        raise SystemExit(1)