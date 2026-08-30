"""
EnterpriseGuard - Dashboard API Boundary
=========================================

Purpose
-------

Stable API-facing boundary for dashboard consumers.

Architecture
------------

    UI / API Client
          |
          v
    DashboardAPI
          |
          v
    DashboardService
          |
          v
    Intelligence Layer


Responsibilities
-----------------

DashboardAPI provides:

- stable response contracts
- dashboard data exposure
- exception isolation
- latency telemetry
- service metadata
- future REST/WebSocket compatibility


Non-responsibilities
--------------------

DashboardAPI does NOT:

- detect threats
- execute models
- access Detector
- access ModelManager
- access training pipeline
- modify security state
- execute actions
- access filesystem
- perform networking


Dependency direction
--------------------

DashboardAPI
      |
      v
DashboardService
"""


from __future__ import annotations


import time

from datetime import datetime, timezone

from typing import Any, Callable


from ..intelligence.dashboard_service import (
    DashboardService,
)



# ============================================================================
# Constants
# ============================================================================


API_NAME = "EnterpriseGuard Dashboard API"

API_VERSION = "1.0.0"



# ============================================================================
# Dashboard API
# ============================================================================


class DashboardAPI:
    """
    Presentation/API boundary for dashboard data.

    This layer intentionally remains framework independent.

    It can later be wrapped by:

        FastAPI
        Flask
        WebSocket gateway
        Frontend adapters
    """


    def __init__(
        self,
        dashboard_service: DashboardService,
    ) -> None:
        """
        Initialize Dashboard API.

        The dependency is injected externally.

        DashboardAPI does not create DashboardService.
        """


        if dashboard_service is None:

            raise TypeError(
                "dashboard_service must not be None"
            )


        # Do not enforce strict isinstance here.
        #
        # Reason:
        #
        # Future testing and API adapters may provide
        # compatible service implementations.
        #
        # The required contract is behavior,
        # not inheritance.

        required_methods = (
            "get_system_status",
            "get_alerts",
            "get_escalations",
            "get_recent_activity",
            "get_summary_metrics",
            "get_snapshot",
        )


        for method in required_methods:

            if not callable(
                getattr(
                    dashboard_service,
                    method,
                    None,
                )
            ):

                raise TypeError(
                    "dashboard_service missing required method: "
                    + method
                )


        self._dashboard_service = (
            dashboard_service
        )



    # ------------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------------


    def metadata(
        self,
    ) -> dict[str, Any]:
        """
        Return API metadata.
        """


        return self._success(
            {
                "name": API_NAME,
                "version": API_VERSION,
                "component": "dashboard_api",
            }
        )



    # ------------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------------


    def health(
        self,
    ) -> dict[str, Any]:
        """
        Return API health state.
        """


        return {

            "success": True,

            "data":
            {
                "status": "healthy",

                "service":
                "dashboard_api",

                "version":
                API_VERSION,
            },

            "timestamp":
            self._timestamp(),

        }



    # ------------------------------------------------------------------------
    # System Status
    # ------------------------------------------------------------------------


    def get_system_status(
        self,
    ) -> dict[str, Any]:
        """
        Return dashboard system status.
        """


        return self._execute(
            self._dashboard_service
            .get_system_status
        )
    # ------------------------------------------------------------------------
    # Alerts
    # ------------------------------------------------------------------------

    def get_alerts(
        self,
    ) -> dict[str, Any]:
        """
        Return queued alerts.

        No alert processing is performed here.
        """

        return self._execute(
            self._dashboard_service
            .get_alerts
        )


    # ------------------------------------------------------------------------
    # Escalations
    # ------------------------------------------------------------------------

    def get_escalations(
        self,
    ) -> dict[str, Any]:
        """
        Return queued escalation decisions.
        """

        return self._execute(
            self._dashboard_service
            .get_escalations
        )


    # ------------------------------------------------------------------------
    # Recent Activity
    # ------------------------------------------------------------------------

    def get_recent_activity(
        self,
        limit: int = 10,
    ) -> dict[str, Any]:
        """
        Return recent security activity.
        """

        if not isinstance(
            limit,
            int,
        ):
            return self._error(
                "limit must be integer"
            )


        if limit < 0:

            return self._error(
                "limit must not be negative"
            )


        return self._execute(
            lambda:
            self._dashboard_service
            .get_recent_activity(
                limit=limit
            )
        )


    # ------------------------------------------------------------------------
    # Summary Metrics
    # ------------------------------------------------------------------------

    def get_summary_metrics(
        self,
    ) -> dict[str, Any]:
        """
        Return dashboard summary metrics.
        """

        return self._execute(
            self._dashboard_service
            .get_summary_metrics
        )


    # ------------------------------------------------------------------------
    # Full Snapshot
    # ------------------------------------------------------------------------

    def get_snapshot(
        self,
    ) -> dict[str, Any]:
        """
        Return complete dashboard state.

        This is the main payload expected
        by future frontend dashboards.
        """

        return self._execute(
            self._dashboard_service
            .get_snapshot
        )


    # ------------------------------------------------------------------------
    # Internal Execution Boundary
    # ------------------------------------------------------------------------

    def _execute(
        self,
        operation: Callable[[], Any],
    ) -> dict[str, Any]:
        """
        Execute dashboard operation safely.

        Adds:

        - latency measurement
        - timestamp
        - normalized response
        - exception isolation
        """


        start_time = time.perf_counter()


        try:

            result = operation()


            latency_ms = (
                time.perf_counter()
                -
                start_time
            ) * 1000


            return self._success(
                data=result,
                latency_ms=latency_ms,
            )


        except Exception as exc:


            latency_ms = (
                time.perf_counter()
                -
                start_time
            ) * 1000


            return self._error(
                message=str(exc),
                latency_ms=latency_ms,
            )



    # ------------------------------------------------------------------------
    # Response Builders
    # ------------------------------------------------------------------------

    @classmethod
    def _success(
        cls,
        data: Any,
        latency_ms: float | None = None,
    ) -> dict[str, Any]:
        """
        Create successful API response.
        """

        response = {

            "success": True,

            "data": data,

            "timestamp":
            cls._timestamp(),

        }


        if latency_ms is not None:

            response["latency_ms"] = round(
                latency_ms,
                3,
            )


        return response



    @classmethod
    def _error(
        cls,
        message: str,
        latency_ms: float | None = None,
    ) -> dict[str, Any]:
        """
        Create standardized API error response.
        """

        response = {

            "success": False,

            "error":
            message,

            "timestamp":
            cls._timestamp(),

        }


        if latency_ms is not None:

            response["latency_ms"] = round(
                latency_ms,
                3,
            )


        return response



    # ------------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------------

    @staticmethod
    def _timestamp() -> str:
        """
        Generate UTC timestamp.
        """

        return datetime.now(
            timezone.utc
        ).isoformat()
        
        
# ============================================================================
# Self-Test
# ============================================================================


def self_test() -> bool:
    """
    Lightweight isolated DashboardAPI self-test.

    Validates:

    - initialization
    - API metadata
    - health response
    - dashboard forwarding
    - response contract
    - latency telemetry
    - error isolation


    No:

    - model
    - detector
    - training
    - filesystem
    - network
    - security actions

    are used.
    """


    from ..intelligence.reporting_service import (
        ReportingService,
    )

    from ..intelligence.decision_orchestrator import (
        DecisionOrchestrator,
    )

    from ..intelligence.dashboard_service import (
        DashboardService,
    )


    # ------------------------------------------------------------------------
    # Build dependency chain
    # ------------------------------------------------------------------------

    reporting_service = ReportingService()

    decision_orchestrator = (
        DecisionOrchestrator()
    )


    dashboard_service = DashboardService(
        reporting_service=
        reporting_service,

        decision_orchestrator=
        decision_orchestrator,
    )


    api = DashboardAPI(
        dashboard_service
    )


    # ------------------------------------------------------------------------
    # Test 1
    # Initialization
    # ------------------------------------------------------------------------

    assert isinstance(
        api,
        DashboardAPI,
    )


    # ------------------------------------------------------------------------
    # Test 2
    # Metadata
    # ------------------------------------------------------------------------

    metadata = api.metadata()


    assert metadata["success"] is True

    assert (
        metadata["data"]["component"]
        ==
        "dashboard_api"
    )


    assert (
        metadata["data"]["version"]
        ==
        API_VERSION
    )


    # ------------------------------------------------------------------------
    # Test 3
    # Health
    # ------------------------------------------------------------------------

    health = api.health()


    assert health["success"] is True

    assert (
        health["data"]["status"]
        ==
        "healthy"
    )


    # ------------------------------------------------------------------------
    # Test 4
    # System status
    # ------------------------------------------------------------------------

    status = (
        api.get_system_status()
    )


    assert status["success"] is True

    assert isinstance(
        status["data"],
        dict,
    )


    assert isinstance(
        status["data"],
        dict,
    )


    assert (
        "status"
        in status["data"]
    )

    assert (
        "latency_ms"
        in status
    )


    # ------------------------------------------------------------------------
    # Test 5
    # Alerts
    # ------------------------------------------------------------------------

    alerts = (
        api.get_alerts()
    )


    assert alerts["success"] is True

    assert isinstance(
        alerts["data"],
        list,
    )


    # ------------------------------------------------------------------------
    # Test 6
    # Escalations
    # ------------------------------------------------------------------------

    escalations = (
        api.get_escalations()
    )


    assert escalations["success"] is True

    assert isinstance(
        escalations["data"],
        list,
    )


    # ------------------------------------------------------------------------
    # Test 7
    # Activity
    # ------------------------------------------------------------------------

    activity = (
        api.get_recent_activity(
            limit=5
        )
    )


    assert activity["success"] is True

    assert isinstance(
        activity["data"],
        list,
    )


    # ------------------------------------------------------------------------
    # Test 8
    # Summary
    # ------------------------------------------------------------------------

    summary = (
        api.get_summary_metrics()
    )


    assert summary["success"] is True

    assert isinstance(
        summary["data"],
        dict,
    )


    # ------------------------------------------------------------------------
    # Test 9
    # Snapshot
    # ------------------------------------------------------------------------

    snapshot = (
        api.get_snapshot()
    )


    assert snapshot["success"] is True

    assert isinstance(
        snapshot["data"],
        dict,
    )


    # ------------------------------------------------------------------------
    # Test 10
    # Invalid input
    # ------------------------------------------------------------------------

    invalid = (
        api.get_recent_activity(
            limit=-1
        )
    )


    assert invalid["success"] is False

    assert (
        "negative"
        in invalid["error"]
    )


    # ------------------------------------------------------------------------
    # Test 11
    # Exception isolation
    # ------------------------------------------------------------------------

    class BrokenDashboardService:

        def get_snapshot(self):

            raise RuntimeError(
                "internal failure"
            )


        def get_system_status(self):
            return {}


        def get_alerts(self):
            return []


        def get_escalations(self):
            return []


        def get_recent_activity(
            self,
            limit=10,
        ):
            return []


        def get_summary_metrics(self):
            return {}



    broken_api = DashboardAPI(
        BrokenDashboardService()
    )


    result = (
        broken_api.get_snapshot()
    )


    assert result["success"] is False


    assert (
        "internal failure"
        in result["error"]
    )


    return True



# ============================================================================
# Module Execution
# ============================================================================


if __name__ == "__main__":

    print("=" * 70)

    print(
        "EnterpriseGuard - Dashboard API Self-Test"
    )

    print("=" * 70)


    try:

        self_test()


        print(
            "[PASS] Dashboard API operational"
        )

        print(
            "[PASS] Metadata contract"
        )

        print(
            "[PASS] Health boundary"
        )

        print(
            "[PASS] Dashboard forwarding"
        )

        print(
            "[PASS] Latency telemetry"
        )

        print(
            "[PASS] Error isolation"
        )


        print("=" * 70)

        print(
            "SELF-TEST PASSED"
        )

        print("=" * 70)



    except AssertionError as exc:


        import traceback


        print(
            "[FAIL] Assertion error:"
        )


        print(exc)


        traceback.print_exc()


        raise SystemExit(1)