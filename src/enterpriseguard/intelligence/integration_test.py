"""
EnterpriseGuard - Real Integration Test
========================================


Real pipeline:


    Raw Events
        |
        v
    DetectionService
        |
        v
    DetectionServiceResult
        |
        v
    DecisionOrchestrator
        |
        v
    OrchestrationResult
        |
        v
    ReportingService
        |
        v
    DashboardService
        |
        v
    Final Snapshot


This file is an integration test only.


It does NOT modify:
- training files
- model files
- detector.py
- detection_service.py
- decision_orchestrator.py
- reporting_service.py
- dashboard_service.py


It also does not:
- execute shell commands
- perform network operations
- perform security actions
- activate/deactivate models
- manipulate model storage
"""


from __future__ import annotations


import sys
from typing import Any


from .training.model_manager import ModelManager
from .detector import Detector
from .detection_service import DetectionService
from .decision_orchestrator import DecisionOrchestrator
from .reporting_service import ReportingService
from .dashboard_service import DashboardService




# ============================================================================
# Test Events
# ============================================================================


TEST_EVENTS: list[dict[str, Any]] = [
    {
        "source": "10.0.0.10",
        "user": "alice",
        "success": True,
        "failed": False,
        "outbound_data_volume": 200.0,
        "anomaly_score": 0.10,
    },
    {
        "source": "10.0.0.10",
        "user": "alice",
        "success": False,
        "failed": True,
        "outbound_data_volume": 300.0,
        "anomaly_score": 0.50,
    },
    {
        "source": "10.0.0.20",
        "user": "bob",
        "success": False,
        "failed": True,
        "outbound_data_volume": 500.0,
        "anomaly_score": 0.90,
    },
    {
        "source": "10.0.0.30",
        "user": "alice",
        "success": True,
        "failed": False,
        "outbound_data_volume": 100.0,
        "anomaly_score": 0.30,
    },
]




# ============================================================================
# Expected canonical features
# ============================================================================


EXPECTED_FEATURES = {
    "request_frequency",
    "failure_ratio",
    "unique_source_count",
    "unique_user_count",
    "failed_attempts",
    "anomaly_score",
    "outbound_data_volume",
}




# ============================================================================
# Helpers
# ============================================================================


def get_value(
    obj: Any,
    name: str,
    default: Any = None,
) -> Any:
    """Safely read a value from an object or dictionary."""


    if obj is None:
        return default


    if isinstance(obj, dict):
        return obj.get(name, default)


    return getattr(obj, name, default)




def safe_dict(obj: Any) -> dict[str, Any]:
    """Convert supported result objects to dictionaries."""


    if obj is None:
        return {}


    if isinstance(obj, dict):
        return dict(obj)


    if hasattr(obj, "to_dict"):
        result = obj.to_dict()


        if isinstance(result, dict):
            return result


    result: dict[str, Any] = {}


    for name in (
        "decision",
        "predicted_class",
        "threat_probability",
        "benign_probability",
        "anomaly_score",
        "confidence",
        "model_version",
        "error",
        "queued",
        "queue_type",
    ):
        if hasattr(obj, name):
            result[name] = getattr(obj, name)


    return result




def print_stage_failure(
    stage: str,
    error: Exception | str,
) -> None:
    """Print a structured integration failure."""


    print()
    print(f"[FAIL] {stage}")
    print()
    print("Reason:")


    if isinstance(error, Exception):
        print(
            f"  {type(error).__name__}: {error}"
        )
    else:
        print(f"  {error}")




# ============================================================================
# Integration Test
# ============================================================================


class EnterpriseGuardIntegrationTest:
    """Execute the real EnterpriseGuard pipeline."""


    def __init__(self) -> None:
        self.model_manager: ModelManager | None = None
        self.detector: Detector | None = None
        self.detection_service: DetectionService | None = None


        self.decision_orchestrator: (
            DecisionOrchestrator | None
        ) = None


        self.reporting_service: (
            ReportingService | None
        ) = None


        self.dashboard_service: (
            DashboardService | None
        ) = None


        self.detection_result: Any = None
        self.orchestration_result: Any = None


        self.detection_features: dict[str, float] = {}


        self.integration_status = {
            "Detection → Decision": False,
            "Decision → Reporting": False,
            "Reporting → Dashboard": False,
        }


    # ------------------------------------------------------------------------
    # Main execution
    # ------------------------------------------------------------------------


    def run(self) -> bool:
        self._print_header()


        if not self._validate_test_events():
            self._print_final_result()
            return False


        if not self._run_detection():
            self._print_final_result()
            return False


        if not self._run_decision():
            self._print_final_result()
            return False


        if not self._run_reporting():
            self._print_final_result()
            return False


        if not self._run_dashboard():
            self._print_final_result()
            return False


        self._print_final_result()


        return all(
            self.integration_status.values()
        )


    # ------------------------------------------------------------------------
    # Validate input
    # ------------------------------------------------------------------------


    def _validate_test_events(self) -> bool:
        print()
        print("[0] Input Validation")
        print("-" * 60)


        try:
            if not isinstance(TEST_EVENTS, list):
                raise TypeError(
                    "TEST_EVENTS must be a list"
                )


            if not TEST_EVENTS:
                raise ValueError(
                    "TEST_EVENTS must not be empty"
                )


            for index, event in enumerate(TEST_EVENTS):
                if not isinstance(event, dict):
                    raise TypeError(
                        f"Event {index} is not a mapping"
                    )


            print(
                f"    events: {len(TEST_EVENTS)}"
            )


            print(
                "    input validation: PASS"
            )


            return True


        except Exception as exc:
            print_stage_failure(
                "Input Validation",
                exc,
            )
            return False


    # ------------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------------


    def _run_detection(self) -> bool:
        print()
        print("[1] Detection")
        print("-" * 60)


        try:
            # --------------------------------------------------------------
            # Create the real ModelManager.
            #
            # We intentionally do NOT activate or modify the model state.
            # --------------------------------------------------------------


            self.model_manager = ModelManager()


            print(
                "    model_active:",
                self.model_manager.is_active(),
            )


            print(
                "    active_version:",
                self.model_manager.active_version(),
            )


            # --------------------------------------------------------------
            # Create real Detector.
            # --------------------------------------------------------------


            self.detector = Detector(
                self.model_manager
            )


            # --------------------------------------------------------------
            # Create real DetectionService.
            # --------------------------------------------------------------


            self.detection_service = DetectionService(
                self.detector
            )


            # --------------------------------------------------------------
            # Verify the feature extraction contract independently.
            # --------------------------------------------------------------


            self.detection_features = (
                self.detection_service.extract_features(
                    TEST_EVENTS
                )
            )


            print()
            print(
                "    extracted_features:"
            )


            for name, value in (
                self.detection_features.items()
            ):
                print(
                    f"      {name}: {value}"
                )


            if set(
                self.detection_features.keys()
            ) != EXPECTED_FEATURES:
                raise AssertionError(
                    "DetectionService did not produce "
                    "the canonical seven features."
                )


            # --------------------------------------------------------------
            # IMPORTANT:
            # The real DetectionService interface is analyze(events).
            # --------------------------------------------------------------


            self.detection_result = (
                self.detection_service.analyze(
                    TEST_EVENTS
                )
            )


            if self.detection_result is None:
                raise RuntimeError(
                    "DetectionService.analyze() returned None."
                )


            print()
            print(
                "    DetectionServiceResult:"
            )


            result_dict = safe_dict(
                self.detection_result
            )


            for name, value in result_dict.items():
                print(
                    f"      {name}: {value}"
                )


            error = get_value(
                self.detection_result,
                "error",
            )


            decision = get_value(
                self.detection_result,
                "decision",
            )


            if error:
                raise RuntimeError(
                    f"DetectionService returned error: {error}"
                )


            if not decision:
                raise RuntimeError(
                    "DetectionService returned no decision."
                )


            return True


        except Exception as exc:
            print_stage_failure(
                "Detection",
                exc,
            )
            return False


    # ------------------------------------------------------------------------
    # Decision
    # ------------------------------------------------------------------------


    def _run_decision(self) -> bool:
        print()
        print("[2] Decision")
        print("-" * 60)


        try:
            self.decision_orchestrator = (
                DecisionOrchestrator()
            )


            self.orchestration_result = (
                self.decision_orchestrator.handle(
                    self.detection_result
                )
            )


            if self.orchestration_result is None:
                raise RuntimeError(
                    "DecisionOrchestrator.handle() "
                    "returned None."
                )


            detection_decision = get_value(
                self.detection_result,
                "decision",
            )


            orchestration_decision = get_value(
                self.orchestration_result,
                "decision",
            )


            queued = get_value(
                self.orchestration_result,
                "queued",
            )


            queue_type = get_value(
                self.orchestration_result,
                "queue_type",
            )


            error = get_value(
                self.orchestration_result,
                "error",
            )


            print(
                "    detection_decision:",
                detection_decision,
            )


            print(
                "    orchestration_decision:",
                orchestration_decision,
            )


            print(
                "    queued:",
                queued,
            )


            print(
                "    queue_type:",
                queue_type,
            )


            print(
                "    error:",
                error,
            )


            # --------------------------------------------------------------
            # The orchestrator must preserve the decision.
            # --------------------------------------------------------------


            if orchestration_decision != detection_decision:
                raise AssertionError(
                    "DecisionOrchestrator changed the "
                    "decision produced by DetectionService."
                )


            if error:
                raise RuntimeError(
                    f"DecisionOrchestrator returned error: {error}"
                )


            self.integration_status[
                "Detection → Decision"
            ] = True


            print()
            print(
                "    Detection → Decision: PASS"
            )


            return True


        except Exception as exc:
            print_stage_failure(
                "Decision",
                exc,
            )
            return False


    # ------------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------------


    def _run_reporting(self) -> bool:
        print()
        print("[3] Reporting")
        print("-" * 60)


        try:
            self.reporting_service = (
                ReportingService()
            )


            # --------------------------------------------------------------
            # Record the real orchestration result.
            # --------------------------------------------------------------


            self.reporting_service.record(
                self.orchestration_result
            )


            summary = (
                self.reporting_service.get_summary()
            )


            print(
                "    total_records:",
                summary.get(
                    "total_records"
                ),
            )


            print(
                "    alert_count:",
                summary.get(
                    "alert_count"
                ),
            )


            print(
                "    escalation_count:",
                summary.get(
                    "escalation_count"
                ),
            )


            print(
                "    ignored_count:",
                summary.get(
                    "ignored_count"
                ),
            )


            print(
                "    last_result:",
                summary.get(
                    "last_result"
                ),
            )


            # --------------------------------------------------------------
            # Validate that ReportingService preserved the decision.
            # --------------------------------------------------------------


            original_decision = get_value(
                self.orchestration_result,
                "decision",
            )


            last_result = summary.get(
                "last_result"
            )


            recorded_decision = get_value(
                last_result,
                "decision",
            )


            print(
                "    original_decision:",
                original_decision,
            )


            print(
                "    recorded_decision:",
                recorded_decision,
            )


            if recorded_decision != original_decision:
                raise AssertionError(
                    "ReportingService did not preserve "
                    "the orchestration decision."
                )


            self.integration_status[
                "Decision → Reporting"
            ] = True


            print()
            print(
                "    Decision → Reporting: PASS"
            )


            return True


        except Exception as exc:
            print_stage_failure(
                "Reporting",
                exc,
            )
            return False


    # ------------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------------


    def _run_dashboard(self) -> bool:
        print()
        print("[4] Dashboard")
        print("-" * 60)


        try:
            self.dashboard_service = (
                DashboardService(
                    reporting_service=(
                        self.reporting_service
                    ),
                    decision_orchestrator=(
                        self.decision_orchestrator
                    ),
                )
            )


            self.dashboard_service.refresh()


            system_status = (
                self.dashboard_service
                .get_system_status()
            )


            alerts = (
                self.dashboard_service
                .get_alerts()
            )


            escalations = (
                self.dashboard_service
                .get_escalations()
            )


            recent_activity = (
                self.dashboard_service
                .get_recent_activity()
            )


            summary_metrics = (
                self.dashboard_service
                .get_summary_metrics()
            )


            final_snapshot = (
                self.dashboard_service
                .get_snapshot()
            )


            print(
                "    system_status:"
            )
            print(
                f"      {system_status}"
            )


            print()
            print(
                "    alerts:"
            )
            print(
                f"      {alerts}"
            )


            print()
            print(
                "    escalations:"
            )
            print(
                f"      {escalations}"
            )


            print()
            print(
                "    recent_activity:"
            )
            print(
                f"      {recent_activity}"
            )


            print()
            print(
                "    summary_metrics:"
            )
            print(
                f"      {summary_metrics}"
            )


            print()
            print(
                "    final_snapshot:"
            )
            print(
                f"      {final_snapshot}"
            )


            # --------------------------------------------------------------
            # Reporting summary must match dashboard summary.
            # --------------------------------------------------------------


            reporting_summary = (
                self.reporting_service.get_summary()
            )


            for metric in (
                "total_records",
                "alert_count",
                "escalation_count",
                "ignored_count",
            ):
                reporting_value = (
                    reporting_summary.get(
                        metric
                    )
                )


                dashboard_value = (
                    summary_metrics.get(
                        metric
                    )
                )


                if (
                    reporting_value
                    != dashboard_value
                ):
                    raise AssertionError(
                        f"Dashboard metric '{metric}' "
                        f"does not match ReportingService. "
                        f"Reporting={reporting_value}, "
                        f"Dashboard={dashboard_value}"
                    )


            # --------------------------------------------------------------
            # The Dashboard must contain the recorded activity.
            # --------------------------------------------------------------


            original_decision = get_value(
                self.orchestration_result,
                "decision",
            )


            activity_decisions: list[Any] = []


            if isinstance(
                recent_activity,
                list,
            ):
                for item in recent_activity:
                    decision = get_value(
                        item,
                        "decision",
                    )


                    if decision is not None:
                        activity_decisions.append(
                            decision
                        )


            if (
                original_decision
                not in activity_decisions
            ):
                raise AssertionError(
                    "Dashboard recent activity does not "
                    "contain the decision recorded by "
                    "ReportingService."
                )


            self.integration_status[
                "Reporting → Dashboard"
            ] = True


            print()
            print(
                "    Reporting → Dashboard: PASS"
            )


            return True


        except Exception as exc:
            print_stage_failure(
                "Dashboard",
                exc,
            )
            return False


    # ------------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------------


    @staticmethod
    def _print_header() -> None:
        print("=" * 60)
        print(
            "EnterpriseGuard - Real Integration Test"
        )
        print("=" * 60)
        print()
        print(
            "Pipeline:"
        )
        print(
            "Raw Events"
        )
        print(
            "      ↓"
        )
        print(
            "DetectionService"
        )
        print(
            "      ↓"
        )
        print(
            "DecisionOrchestrator"
        )
        print(
            "      ↓"
        )
        print(
            "ReportingService"
        )
        print(
            "      ↓"
        )
        print(
            "DashboardService"
        )
        print(
            "      ↓"
        )
        print(
            "Final Snapshot"
        )


    # ------------------------------------------------------------------------
    # Final result
    # ------------------------------------------------------------------------


    def _print_final_result(self) -> None:
        print()
        print("=" * 60)
        print(
            "[5] INTEGRATION RESULT"
        )
        print("=" * 60)


        for stage, passed in (
            self.integration_status.items()
        ):
            print(
                f"{stage:<28}"
                f"{'PASS' if passed else 'FAIL'}"
            )


        full_pipeline = all(
            self.integration_status.values()
        )


        print(
            f"{'Full Pipeline':<28}"
            f"{'PASS' if full_pipeline else 'FAIL'}"
        )


        print()


        if full_pipeline:
            print(
                "INTEGRATION TEST: PASS"
            )
        else:
            print(
                "INTEGRATION TEST: FAIL"
            )


        print("=" * 60)




# ============================================================================
# Self-Test
# ============================================================================


def self_test() -> bool:
    """
    Lightweight self-test for the integration-test module itself.
    """


    assert isinstance(
        TEST_EVENTS,
        list,
    )


    assert len(
        TEST_EVENTS
    ) > 0


    for event in TEST_EVENTS:
        assert isinstance(
            event,
            dict,
        )


    assert EXPECTED_FEATURES == {
        "request_frequency",
        "failure_ratio",
        "unique_source_count",
        "unique_user_count",
        "failed_attempts",
        "anomaly_score",
        "outbound_data_volume",
    }


    return True




# ============================================================================
# Entry Point
# ============================================================================


def main() -> int:
    print()
    print(
        "EnterpriseGuard - Integration Test Self-Test"
    )


    try:
        self_test()


    except Exception as exc:
        print(
            "Integration Test Self-Test: FAIL"
        )
        print(
            f"{type(exc).__name__}: {exc}"
        )
        return 2


    print(
        "Integration Test Self-Test: PASS"
    )


    print()


    test = (
        EnterpriseGuardIntegrationTest()
    )


    try:
        passed = test.run()


    except Exception as exc:
        print()
        print(
            "Unexpected Integration Test Error:"
        )
        print(
            f"{type(exc).__name__}: {exc}"
        )
        return 1


    return 0 if passed else 1




if __name__ == "__main__":
    sys.exit(
        main()
    )