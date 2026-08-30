"""
EnterpriseGuard - Dashboard Service
====================================

Production Dashboard Aggregation Layer.

Purpose
-------

Prepare dashboard-ready intelligence data for future:

- Web UI
- REST API
- Security Operations Console
- Reporting interfaces


Architecture
------------


 ReportingService
        |
        |
        +----------------+
                         |
                         v
                DashboardService
                         |
        +----------------+----------------+
        |                |                |
        v                v                v

   Summary          Queues          Runtime


Responsibilities
----------------

DashboardService:

- aggregates existing intelligence outputs
- prepares UI/API compatible payloads
- exposes operational metrics
- exposes threat summaries
- exposes decision queues
- exposes runtime health


Non-responsibilities
--------------------

This service does NOT:

- detect threats
- execute decisions
- train models
- load models
- access model registry
- access filesystem
- execute commands
- perform security actions
- communicate externally


Dependency Direction
--------------------


ReportingService
        |
        v

DashboardService

DecisionOrchestrator
        |
        v

DashboardService


The dashboard is a consumer, not a controller.
"""


from __future__ import annotations


from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any


from .decision_orchestrator import (
    DecisionOrchestrator,
)

from .reporting_service import (
    ReportingService,
)





# ============================================================================
# Dashboard DTO Contracts
# ============================================================================


@dataclass(frozen=True)
class DashboardHealth:
    """
    Runtime health representation.
    """

    status: str

    reporting_service: str

    decision_orchestrator: str

    timestamp: str


    def to_dict(self) -> dict[str, Any]:

        return asdict(self)




@dataclass(frozen=True)
class ThreatMetrics:
    """
    Security metrics exposed to dashboard consumers.
    """

    total_events: int = 0

    alert_count: int = 0

    escalation_count: int = 0

    ignored_count: int = 0

    threat_rate: float = 0.0

    average_confidence: float | None = None

    average_latency_ms: float | None = None


    def to_dict(self) -> dict[str, Any]:

        return asdict(self)





@dataclass(frozen=True)
class DashboardSnapshot:
    """
    Complete dashboard payload contract.

    Designed for:

    - frontend rendering
    - API serialization
    - audit views
    """

    health: dict[str, Any]

    metrics: dict[str, Any]

    alerts: list[dict[str, Any]]

    escalations: list[dict[str, Any]]

    activity: list[dict[str, Any]]

    model: dict[str, Any]

    generated_at: str



    def to_dict(self) -> dict[str, Any]:

        return asdict(self)







# ============================================================================
# Dashboard Service
# ============================================================================


class DashboardService:
    """
    EnterpriseGuard dashboard aggregation service.

    The service only reads already-produced intelligence.

    It does not create intelligence.
    """


    def __init__(
        self,
        reporting_service: ReportingService,
        decision_orchestrator: DecisionOrchestrator,
    ) -> None:


        if reporting_service is None:

            raise TypeError(
                "reporting_service must not be None"
            )


        if decision_orchestrator is None:

            raise TypeError(
                "decision_orchestrator must not be None"
            )


        if not isinstance(
            reporting_service,
            ReportingService,
        ):

            raise TypeError(
                "reporting_service must be ReportingService"
            )


        if not isinstance(
            decision_orchestrator,
            DecisionOrchestrator,
        ):

            raise TypeError(
                "decision_orchestrator must be DecisionOrchestrator"
            )



        self._reporting_service = reporting_service

        self._decision_orchestrator = decision_orchestrator



        self._last_snapshot: dict[str, Any] = {}

        self._last_refresh: str | None = None



    # ========================================================================
    # Health
    # ========================================================================


    def get_health(
        self,
    ) -> dict[str, Any]:
        """
        Return dashboard runtime health.
        """


        health = DashboardHealth(

            status="HEALTHY",

            reporting_service="AVAILABLE",

            decision_orchestrator="AVAILABLE",

            timestamp=self._utc_now(),

        )


        return health.to_dict()






    # ========================================================================
    # Summary Metrics
    # ========================================================================


    def get_metrics(
        self,
    ) -> dict[str, Any]:
        """
        Produce dashboard security metrics.
        """


        summary = (
            self._reporting_service
            .get_summary()
        )



        total = self._safe_int(
            summary.get(
                "total_records"
            )
        )


        alerts = self._safe_int(
            summary.get(
                "alert_count"
            )
        )


        escalations = self._safe_int(
            summary.get(
                "escalation_count"
            )
        )


        ignored = self._safe_int(
            summary.get(
                "ignored_count"
            )
        )


        threat_rate = 0.0


        if total > 0:

            threat_rate = (
                alerts + escalations
            ) / total



        metrics = ThreatMetrics(

            total_events=total,

            alert_count=alerts,

            escalation_count=escalations,

            ignored_count=ignored,

            threat_rate=round(
                threat_rate,
                4,
            ),

            average_confidence=None,

            average_latency_ms=None,

        )


        return metrics.to_dict()
    # ========================================================================
    # Alert Queue
    # ========================================================================

    def get_alerts(
        self,
    ) -> list[dict[str, Any]]:
        """
        Return queued alert decisions.

        The dashboard only displays decisions.
        It never executes them.
        """

        queue = (
            self._decision_orchestrator
            .get_alert_queue()
        )

        return [
            self._result_to_dict(item)
            for item in queue
        ]



    # ========================================================================
    # Escalation Queue
    # ========================================================================

    def get_escalations(
        self,
    ) -> list[dict[str, Any]]:
        """
        Return queued escalation decisions.
        """

        queue = (
            self._decision_orchestrator
            .get_escalation_queue()
        )


        return [
            self._result_to_dict(item)
            for item in queue
        ]



    # ========================================================================
    # Recent Activity
    # ========================================================================

    def get_activity(
        self,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Return recent intelligence activity.
        """


        if not isinstance(limit, int):

            raise TypeError(
                "limit must be integer"
            )


        if limit < 0:

            raise ValueError(
                "limit cannot be negative"
            )


        return (
            self._reporting_service
            .get_recent_activity(
                limit=limit
            )
        )



    # ========================================================================
    # Model Information
    # ========================================================================

    def get_model_status(
        self,
    ) -> dict[str, Any]:
        """
        Return model visibility information.

        This is intentionally generic because
        DashboardService does not access ModelManager.
        """

        return {

            "available": None,

            "version": None,

            "explainability_available": False,

            "metadata_available": False,

            "latency_available": False,

        }



    # ========================================================================
    # Dashboard Snapshot
    # ========================================================================

    def refresh(
        self,
    ) -> dict[str, Any]:
        """
        Build a complete dashboard snapshot.
        """


        generated = self._utc_now()


        snapshot = DashboardSnapshot(

            health=self.get_health(),

            metrics=self.get_metrics(),

            alerts=self.get_alerts(),

            escalations=self.get_escalations(),

            activity=self.get_activity(),

            model=self.get_model_status(),

            generated_at=generated,

        )


        self._last_refresh = generated


        self._last_snapshot = (
            snapshot.to_dict()
        )


        return self.get_snapshot()



    def get_snapshot(
        self,
    ) -> dict[str, Any]:
        """
        Return protected dashboard snapshot.
        """

        return _clone_data(
            self._last_snapshot
        )



    # ========================================================================
    # Compatibility Layer
    # ========================================================================

    def get_system_status(
        self,
    ) -> dict[str, Any]:
        """
        Backward-compatible method.

        Keeps compatibility with previous
        DashboardService consumers.
        """

        return self.get_health()



    def get_summary_metrics(
        self,
    ) -> dict[str, Any]:
        """
        Backward-compatible metrics accessor.
        """

        return self.get_metrics()



    def get_recent_activity(
        self,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Backward-compatible alias.
        """

        return self.get_activity(
            limit
        )



    # ========================================================================
    # Internal Helpers
    # ========================================================================


    @staticmethod
    def _result_to_dict(
        result: Any,
    ) -> dict[str, Any]:
        """
        Convert orchestration objects
        into UI/API compatible dictionaries.
        """


        if hasattr(
            result,
            "to_dict",
        ):

            data = result.to_dict()

            if isinstance(
                data,
                dict,
            ):

                return dict(data)



        return {

            "decision": getattr(
                result,
                "decision",
                None,
            ),

            "queued": getattr(
                result,
                "queued",
                False,
            ),

            "queue_type": getattr(
                result,
                "queue_type",
                None,
            ),

            "error": getattr(
                result,
                "error",
                None,
            ),

        }



    @staticmethod
    def _safe_int(
        value: Any,
    ) -> int:
        """
        Safe integer conversion.
        """

        try:

            return max(
                0,
                int(value),
            )


        except (
            TypeError,
            ValueError,
        ):

            return 0



    @staticmethod
    def _utc_now() -> str:
        """
        UTC timestamp.
        """

        return datetime.now(
            timezone.utc
        ).isoformat()
# ============================================================================
# Data Isolation Helper
# ============================================================================


def _clone_data(
    data: Any,
) -> Any:
    """
    Create a safe recursive copy.

    Prevents external consumers such as UI/API
    from mutating internal dashboard state.
    """


    if isinstance(
        data,
        dict,
    ):

        return {
            key: _clone_data(value)
            for key, value in data.items()
        }


    if isinstance(
        data,
        list,
    ):

        return [
            _clone_data(item)
            for item in data
        ]


    return data





# ============================================================================
# Self Test
# ============================================================================


def self_test() -> bool:
    """
    DashboardService isolated verification.

    Validates:

    - initialization
    - health contract
    - metrics contract
    - snapshot generation
    - queue exposure
    - compatibility methods
    - data isolation


    No:

    - model
    - detector
    - filesystem
    - network
    - shell
    - security action

    is used.
    """



    reporting_service = ReportingService()

    decision_orchestrator = DecisionOrchestrator()



    dashboard = DashboardService(

        reporting_service=

            reporting_service,

        decision_orchestrator=

            decision_orchestrator,

    )



    # ------------------------------------------------------------------------
    # Test 1
    # Initialization
    # ------------------------------------------------------------------------


    assert isinstance(
        dashboard,
        DashboardService,
    )



    # ------------------------------------------------------------------------
    # Test 2
    # Health
    # ------------------------------------------------------------------------


    health = dashboard.get_health()


    assert health["status"] == "HEALTHY"

    assert (
        health["reporting_service"]
        == "AVAILABLE"
    )


    assert (
        health["decision_orchestrator"]
        == "AVAILABLE"
    )


    assert (
        health["timestamp"]
        is not None
    )



    # ------------------------------------------------------------------------
    # Test 3
    # Empty metrics
    # ------------------------------------------------------------------------


    metrics = dashboard.get_metrics()


    assert metrics["total_events"] == 0

    assert metrics["alert_count"] == 0



    # ------------------------------------------------------------------------
    # Test 4
    # Model contract
    # ------------------------------------------------------------------------


    model = dashboard.get_model_status()


    assert (
        "explainability_available"
        in model
    )


    assert (
        "metadata_available"
        in model
    )


    assert (
        "latency_available"
        in model
    )



    # ------------------------------------------------------------------------
    # Test 5
    # Snapshot generation
    # ------------------------------------------------------------------------


    snapshot = dashboard.refresh()



    assert isinstance(
        snapshot,
        dict,
    )


    assert "health" in snapshot

    assert "metrics" in snapshot

    assert "alerts" in snapshot

    assert "escalations" in snapshot

    assert "activity" in snapshot

    assert "model" in snapshot



    # ------------------------------------------------------------------------
    # Test 6
    # Compatibility methods
    # ------------------------------------------------------------------------


    assert (
        dashboard.get_system_status()
        ["status"]
        == "HEALTHY"
    )


    assert isinstance(
        dashboard.get_summary_metrics(),
        dict,
    )


    assert isinstance(
        dashboard.get_recent_activity(),
        list,
    )



    # ------------------------------------------------------------------------
    # Test 7
    # Snapshot isolation
    # ------------------------------------------------------------------------


    external = dashboard.get_snapshot()



    external["alerts"].append(
        {
            "fake": True
        }
    )



    internal = dashboard.get_snapshot()



    assert (
        len(internal["alerts"])
        == 0
    )



    # ------------------------------------------------------------------------
    # Test 8
    # Invalid dependencies
    # ------------------------------------------------------------------------


    try:

        DashboardService(
            None,
            decision_orchestrator,
        )


        raise AssertionError(
            "None reporting service accepted"
        )


    except TypeError:

        pass



    try:

        DashboardService(
            reporting_service,
            None,
        )


        raise AssertionError(
            "None orchestrator accepted"
        )


    except TypeError:

        pass



    # ------------------------------------------------------------------------
    # Test 9
    # Activity validation
    # ------------------------------------------------------------------------


    try:

        dashboard.get_activity(
            limit=-1
        )


        raise AssertionError(
            "Negative limit accepted"
        )


    except ValueError:

        pass



    return True





# ============================================================================
# Module Execution
# ============================================================================


if __name__ == "__main__":


    print("=" * 70)

    print(
        "EnterpriseGuard - Dashboard Service Self-Test"
    )

    print("=" * 70)



    try:

        self_test()


        print(
            "[PASS] Dashboard initialization"
        )

        print(
            "[PASS] Health contract"
        )

        print(
            "[PASS] Metrics contract"
        )

        print(
            "[PASS] Snapshot generation"
        )

        print(
            "[PASS] UI payload compatibility"
        )

        print(
            "[PASS] Data isolation"
        )


        print("=" * 70)

        print(
            "SELF-TEST PASSED"
        )

        print("=" * 70)



    except AssertionError as exc:


        print(
            "SELF-TEST FAILED"
        )

        print(
            f"Assertion error: {exc}"
        )

        raise SystemExit(1)



    except Exception as exc:


        print(
            "SELF-TEST FAILED"
        )

        print(
            f"Unexpected error: {exc}"
        )

        raise SystemExit(1)