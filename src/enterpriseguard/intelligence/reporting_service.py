"""
EnterpriseGuard - Reporting Service
====================================

Responsible for:

- Receiving OrchestrationResult objects.
- Recording decision activity in memory.
- Generating simple security reports.
- Providing summary statistics.
- Providing recent activity.
- Clearing the in-memory history.

Architecture:

    DecisionOrchestrator
            |
            v
    ReportingService
            |
            +---- generate_report()
            |
            +---- get_summary()
            |
            +---- get_recent_activity()
            |
            +---- clear_history()

Important architectural restrictions:

- This module imports only from decision_orchestrator.py.
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

All history is kept in memory only.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from .decision_orchestrator import (
    ALERT,
    ESCALATE,
    IGNORE,
    OrchestrationResult,
)


# ============================================================================
# Reporting Service
# ============================================================================

class ReportingService:
    """
    In-memory reporting layer for orchestration results.

    ReportingService does not make decisions and does not execute actions.

    It only records and summarizes decisions that have already been
    produced by the DecisionOrchestrator.
    """

    def __init__(self) -> None:
        """
        Initialize an empty activity history.
        """

        self._history: list[dict[str, Any]] = []

    # ------------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------------

    def record(
        self,
        result: OrchestrationResult,
    ) -> None:
        """
        Record one OrchestrationResult in memory.

        The original result object is converted into a plain dictionary
        so that the internal history remains independent from the
        caller's object.
        """

        if not isinstance(result, OrchestrationResult):
            raise TypeError(
                "result must be an OrchestrationResult"
            )

        entry = result.to_dict()

        entry["recorded_at"] = (
            datetime.now(timezone.utc).isoformat()
        )

        self._history.append(entry)

    # ------------------------------------------------------------------------
    # Report generation
    # ------------------------------------------------------------------------

    def generate_report(self) -> dict[str, Any]:
        """
        Generate a complete report as a dictionary.

        The report contains:

        - summary
        - recent activity
        - total recorded events
        """

        return {
            "summary": self.get_summary(),
            "recent_activity": self.get_recent_activity(),
            "total_records": len(self._history),
        }

    def generate_json(
        self,
        *,
        indent: int = 2,
    ) -> str:
        """
        Generate the complete report as JSON.

        No file is created.
        The JSON exists only as a returned string.
        """

        return json.dumps(
            self.generate_report(),
            indent=indent,
            ensure_ascii=False,
        )

    # ------------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------------

    def get_summary(self) -> dict[str, Any]:
        """
        Return a summary of recorded decisions.

        The summary contains:

        - alert_count
        - escalation_count
        - ignored_count
        - total_records
        - most_common_decision
        - last_result
        """

        decisions = [
            str(entry.get("decision", "")).upper()
            for entry in self._history
        ]

        counter = Counter(decisions)

        most_common_decision: str | None = None

        if counter:
            most_common_decision = counter.most_common(1)[0][0]

        return {
            "alert_count": counter.get(ALERT, 0),
            "escalation_count": counter.get(ESCALATE, 0),
            "ignored_count": counter.get(IGNORE, 0),
            "total_records": len(self._history),
            "most_common_decision": most_common_decision,
            "last_result": (
                dict(self._history[-1])
                if self._history
                else None
            ),
        }

    # ------------------------------------------------------------------------
    # Recent activity
    # ------------------------------------------------------------------------

    def get_recent_activity(
        self,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Return the most recent activity entries.

        Parameters
        ----------
        limit:
            Maximum number of entries to return.

        Returns
        -------
        list[dict[str, Any]]
            A new list containing copies of the latest records.
        """

        if not isinstance(limit, int):
            raise TypeError(
                "limit must be an integer"
            )

        if limit < 0:
            raise ValueError(
                "limit must not be negative"
            )

        if limit == 0:
            return []

        recent = self._history[-limit:]

        return [
            dict(entry)
            for entry in recent
        ]

    # ------------------------------------------------------------------------
    # History management
    # ------------------------------------------------------------------------

    def clear_history(self) -> None:
        """
        Remove all recorded activity from memory.
        """

        self._history.clear()

    # ------------------------------------------------------------------------
    # Read-only history information
    # ------------------------------------------------------------------------

    def history_size(self) -> int:
        """
        Return the number of records currently held in memory.
        """

        return len(self._history)


# ============================================================================
# Self-Test
# ============================================================================

def self_test() -> bool:
    """
    Lightweight isolated Self-Test.

    The test uses OrchestrationResult objects directly.

    No:

    - detector
    - model
    - training component
    - filesystem operation
    - network operation
    - shell operation
    - security action

    is required.
    """

    # ------------------------------------------------------------------------
    # Test 1:
    # Service starts with empty history.
    # ------------------------------------------------------------------------

    service = ReportingService()

    assert service.history_size() == 0
    assert service.get_recent_activity() == []

    summary = service.get_summary()

    assert summary["alert_count"] == 0
    assert summary["escalation_count"] == 0
    assert summary["ignored_count"] == 0
    assert summary["total_records"] == 0
    assert summary["most_common_decision"] is None
    assert summary["last_result"] is None

    # ------------------------------------------------------------------------
    # Test 2:
    # ALERT is recorded.
    # ------------------------------------------------------------------------

    alert_result = OrchestrationResult(
        decision=ALERT,
        queued=True,
        queue_type="alert",
        error=None,
    )

    service.record(alert_result)

    assert service.history_size() == 1

    activity = service.get_recent_activity()

    assert len(activity) == 1
    assert activity[0]["decision"] == ALERT
    assert activity[0]["queued"] is True
    assert activity[0]["queue_type"] == "alert"
    assert activity[0]["error"] is None
    assert "recorded_at" in activity[0]

    # ------------------------------------------------------------------------
    # Test 3:
    # ESCALATE is recorded.
    # ------------------------------------------------------------------------

    escalate_result = OrchestrationResult(
        decision=ESCALATE,
        queued=True,
        queue_type="escalation",
        error=None,
    )

    service.record(escalate_result)

    assert service.history_size() == 2

    # ------------------------------------------------------------------------
    # Test 4:
    # IGNORE is recorded.
    # ------------------------------------------------------------------------

    ignore_result = OrchestrationResult(
        decision=IGNORE,
        queued=False,
        queue_type=None,
        error=None,
    )

    service.record(ignore_result)

    assert service.history_size() == 3

    # ------------------------------------------------------------------------
    # Test 5:
    # Summary must contain correct counts.
    # ------------------------------------------------------------------------

    summary = service.get_summary()

    assert summary["alert_count"] == 1
    assert summary["escalation_count"] == 1
    assert summary["ignored_count"] == 1
    assert summary["total_records"] == 3

    # Every decision occurs once.
    # Counter.most_common() therefore chooses the first recorded one.
    assert summary["most_common_decision"] == ALERT

    # ------------------------------------------------------------------------
    # Test 6:
    # Last activity must be the IGNORE result.
    # ------------------------------------------------------------------------

    last_result = summary["last_result"]

    assert last_result is not None
    assert last_result["decision"] == IGNORE
    assert last_result["queued"] is False

    # ------------------------------------------------------------------------
    # Test 7:
    # Recent activity limit.
    # ------------------------------------------------------------------------

    recent = service.get_recent_activity(limit=2)

    assert len(recent) == 2
    assert recent[0]["decision"] == ESCALATE
    assert recent[1]["decision"] == IGNORE

    # ------------------------------------------------------------------------
    # Test 8:
    # limit=0 returns an empty list.
    # ------------------------------------------------------------------------

    assert service.get_recent_activity(limit=0) == []

    # ------------------------------------------------------------------------
    # Test 9:
    # Negative limit must fail safely.
    # ------------------------------------------------------------------------

    try:
        service.get_recent_activity(limit=-1)

        raise AssertionError(
            "Negative limit should raise ValueError"
        )

    except ValueError:
        pass

    # ------------------------------------------------------------------------
    # Test 10:
    # Invalid result must be rejected.
    # ------------------------------------------------------------------------

    try:
        service.record(None)  # type: ignore[arg-type]

        raise AssertionError(
            "Invalid result should raise TypeError"
        )

    except TypeError:
        pass

    # ------------------------------------------------------------------------
    # Test 11:
    # Dictionary report generation.
    # ------------------------------------------------------------------------

    report = service.generate_report()

    assert isinstance(report, dict)
    assert "summary" in report
    assert "recent_activity" in report
    assert "total_records" in report

    assert report["total_records"] == 3

    # ------------------------------------------------------------------------
    # Test 12:
    # JSON report generation.
    # ------------------------------------------------------------------------

    json_report = service.generate_json()

    assert isinstance(json_report, str)
    assert '"summary"' in json_report
    assert '"recent_activity"' in json_report
    assert '"total_records"' in json_report

    # Ensure the returned JSON is actually valid JSON.
    parsed_report = json.loads(json_report)

    assert parsed_report["total_records"] == 3

    # ------------------------------------------------------------------------
    # Test 13:
    # Returned activity must be a copy.
    # ------------------------------------------------------------------------

    recent_copy = service.get_recent_activity()

    recent_copy.clear()

    assert service.history_size() == 3

    # ------------------------------------------------------------------------
    # Test 14:
    # clear_history() must remove everything.
    # ------------------------------------------------------------------------

    service.clear_history()

    assert service.history_size() == 0
    assert service.get_recent_activity() == []

    cleared_summary = service.get_summary()

    assert cleared_summary["alert_count"] == 0
    assert cleared_summary["escalation_count"] == 0
    assert cleared_summary["ignored_count"] == 0
    assert cleared_summary["total_records"] == 0
    assert cleared_summary["most_common_decision"] is None
    assert cleared_summary["last_result"] is None

    return True


# ============================================================================
# Module execution
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("EnterpriseGuard - Reporting Service Self-Test")
    print("=" * 60)

    try:
        self_test()

        print("Self-Test: PASS")
        print("Reporting Service is operational.")

    except AssertionError as exc:
        print("Self-Test: FAIL")
        print(f"Assertion error: {exc}")
        raise SystemExit(1)

    except Exception as exc:
        print("Self-Test: FAIL")
        print(f"Unexpected error: {exc}")
        raise SystemExit(1)