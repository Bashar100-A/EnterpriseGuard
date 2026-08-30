"""
EnterpriseGuard - Integration Test
===================================


Real integration test for the current EnterpriseGuard pipeline:


    DetectionService
          |
          v
    DecisionOrchestrator
          |
          v
    ReportingService
          |
          v
    DashboardService
          |
          v
    Final Snapshot


Important:


- This module does NOT modify any existing service.
- No model/training files are modified.
- No shell execution.
- No network operations.
- No security actions.
- No external system integrations.
- No hard-coded expected decision.
- No hard-coded probability/confidence assertions.


The test validates DATA CONSISTENCY between layers.


Example:


    Detection decision = ALERT
             |
             v
    Decision decision = ALERT
             |
             v
    Reporting last result = ALERT
             |
             v
    Dashboard activity = ALERT


The actual values produced by the running system are used.
"""


from __future__ import annotations


from dataclasses import asdict, is_dataclass
import inspect
import sys
import traceback
from typing import Any, Callable


from .detection_service import DetectionService
from .decision_orchestrator import (
    DecisionOrchestrator,
)
from .reporting_service import ReportingService
from .dashboard_service import DashboardService




# ============================================================================
# Test configuration
# ============================================================================


TEST_EVENT: dict[str, Any] = {
    "request_frequency": 4.0,
    "failure_ratio": 0.5,
    "unique_source_count": 3.0,
    "unique_user_count": 2.0,
    "failed_attempts": 2.0,
    "anomaly_score": 0.5,
    "outbound_data_volume": 1000.0,
}




# ============================================================================
# Result container
# ============================================================================


class StageResult:
    """
    Internal representation of one integration stage.
    """


    def __init__(
        self,
        name: str,
        passed: bool,
        reason: str | None = None,
        expected: Any = None,
        actual: Any = None,
    ) -> None:
        self.name = name
        self.passed = passed
        self.reason = reason
        self.expected = expected
        self.actual = actual


    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "reason": self.reason,
            "expected": _safe_value(self.expected),
            "actual": _safe_value(self.actual),
        }




# ============================================================================
# Integration Test
# ============================================================================


class EnterpriseGuardIntegrationTest:
    """
    Coordinates the real service chain without modifying any service.
    """


    def __init__(self) -> None:
        self.stages: list[StageResult] = []


        self.detection_result: Any = None
        self.orchestration_result: Any = None


        self.reporting_summary: dict[str, Any] = {}
        self.dashboard_snapshot: dict[str, Any] = {}


        self.detection_service: DetectionService | None = None
        self.decision_orchestrator: DecisionOrchestrator | None = None
        self.reporting_service: ReportingService | None = None
        self.dashboard_service: DashboardService | None = None


    # ------------------------------------------------------------------------
    # Public runner
    # ------------------------------------------------------------------------


    def run(self) -> bool:
        """
        Execute the complete integration pipeline.
        """


        self._print_header()


        detection_ok = self._run_detection()


        if not detection_ok:
            self._print_final_result()
            return False


        decision_ok = self._run_decision()


        if not decision_ok:
            self._print_final_result()
            return False


        reporting_ok = self._run_reporting()


        if not reporting_ok:
            self._print_final_result()
            return False


        dashboard_ok = self._run_dashboard()


        if not dashboard_ok:
            self._print_final_result()
            return False


        self._print_final_result()


        return self._full_pipeline_passed()


    # ------------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------------


    def _run_detection(self) -> bool:
        """
        Execute DetectionService using the actual service.


        No expected decision is hard-coded.
        """


        print()
        print("[1] Detection")
        print("-" * 60)


        try:
            self.detection_service = (
                self._create_detection_service()
            )


            self.detection_result = (
                self._invoke_detection(
                    self.detection_service
                )
            )


            if self.detection_result is None:
                self._record_failure(
                    "Detection",
                    "DetectionService returned None.",
                    expected="DetectionServiceResult",
                    actual=None,
                )


                return False


            decision = _extract(
                self.detection_result,
                "decision",
            )


            error = _extract(
                self.detection_result,
                "error",
            )


            predicted_class = _extract_first(
                self.detection_result,
                (
                    "predicted_class",
                    "prediction",
                    "predicted_label",
                ),
            )


            threat_probability = _extract_first(
                self.detection_result,
                (
                    "threat_probability",
                    "probability",
                    "threat_prob",
                ),
            )


            confidence = _extract(
                self.detection_result,
                "confidence",
            )


            print(
                f"    status: "
                f"{'ERROR' if error else 'PASS'}"
            )


            print(
                f"    decision: {decision}"
            )


            print(
                f"    predicted_class: "
                f"{predicted_class}"
            )


            print(
                f"    threat_probability: "
                f"{threat_probability}"
            )


            print(
                f"    confidence: "
                f"{confidence}"
            )


            print(
                f"    error: {error}"
            )


            if error:
                self._record_failure(
                    "Detection",
                    "DetectionService returned an error.",
                    expected="error is None",
                    actual=error,
                )


                return False


            if decision is None:
                self._record_failure(
                    "Detection",
                    "Detection result does not contain a decision.",
                    expected="non-None decision",
                    actual=None,
                )


                return False


            self.stages.append(
                StageResult(
                    name="Detection",
                    passed=True,
                    reason="DetectionService produced a valid result.",
                    expected="valid detection result",
                    actual={
                        "decision": decision,
                        "predicted_class": predicted_class,
                        "threat_probability": threat_probability,
                        "confidence": confidence,
                        "error": error,
                    },
                )
            )


            return True


        except Exception as exc:
            self._record_exception(
                "Detection",
                exc,
            )


            return False


    # ------------------------------------------------------------------------
    # Decision
    # ------------------------------------------------------------------------


    def _run_decision(self) -> bool:
        """
        Pass the actual DetectionServiceResult to DecisionOrchestrator.
        """


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
                self._record_failure(
                    "Decision",
                    "DecisionOrchestrator.handle() returned None.",
                    expected="OrchestrationResult",
                    actual=None,
                )


                return False


            detection_decision = _extract(
                self.detection_result,
                "decision",
            )


            decision = _extract(
                self.orchestration_result,
                "decision",
            )


            queued = _extract(
                self.orchestration_result,
                "queued",
            )


            queue_type = _extract(
                self.orchestration_result,
                "queue_type",
            )


            error = _extract(
                self.orchestration_result,
                "error",
            )


            success = _extract(
                self.orchestration_result,
                "success",
            )


            print(
                f"    decision: {decision}"
            )


            print(
                f"    queued: {queued}"
            )


            print(
                f"    queue_type: {queue_type}"
            )


            print(
                f"    error: {error}"
            )


            if success is not None:
                print(
                    f"    success: {success}"
                )


            # --------------------------------------------------------------
            # Core integration invariant:
            #
            # Detection decision MUST be preserved by DecisionOrchestrator.
            # --------------------------------------------------------------


            if decision != detection_decision:
                self._record_failure(
                    "Detection → Decision",
                    "DecisionOrchestrator did not preserve the detection decision.",
                    expected=detection_decision,
                    actual=decision,
                )


                return False


            if error:
                self._record_failure(
                    "Decision",
                    "DecisionOrchestrator returned an error.",
                    expected="error is None",
                    actual=error,
                )


                return False


            self.stages.append(
                StageResult(
                    name="Detection → Decision",
                    passed=True,
                    reason=(
                        "Detection decision was preserved "
                        "by DecisionOrchestrator."
                    ),
                    expected=detection_decision,
                    actual=decision,
                )
            )


            print(
                "    integration check: PASS"
            )


            return True


        except Exception as exc:
            self._record_exception(
                "Detection → Decision",
                exc,
            )


            return False


    # ------------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------------


    def _run_reporting(self) -> bool:
        """
        Record the actual orchestration result.
        """


        print()
        print("[3] Reporting")
        print("-" * 60)


        try:
            self.reporting_service = (
                ReportingService()
            )


            self.reporting_service.record(
                self.orchestration_result
            )


            self.reporting_summary = (
                self.reporting_service.get_summary()
            )


            detection_decision = _extract(
                self.detection_result,
                "decision",
            )


            orchestration_decision = _extract(
                self.orchestration_result,
                "decision",
            )


            last_result = self.reporting_summary.get(
                "last_result"
            )


            reported_decision = _extract(
                last_result,
                "decision",
            )


            print(
                f"    total_records: "
                f"{self.reporting_summary.get('total_records')}"
            )


            print(
                f"    alert_count: "
                f"{self.reporting_summary.get('alert_count')}"
            )


            print(
                f"    escalation_count: "
                f"{self.reporting_summary.get('escalation_count')}"
            )


            print(
                f"    ignored_count: "
                f"{self.reporting_summary.get('ignored_count')}"
            )


            print(
                f"    last_result: "
                f"{_safe_value(last_result)}"
            )


            # --------------------------------------------------------------
            # Core invariant:
            #
            # Reporting must preserve the decision generated by the
            # DecisionOrchestrator.
            # --------------------------------------------------------------


            if reported_decision != orchestration_decision:
                self._record_failure(
                    "Decision → Reporting",
                    "ReportingService did not preserve the decision.",
                    expected=orchestration_decision,
                    actual=reported_decision,
                )


                return False


            if reported_decision != detection_decision:
                self._record_failure(
                    "Decision → Reporting",
                    "Reporting result differs from original detection decision.",
                    expected=detection_decision,
                    actual=reported_decision,
                )


                return False


            self.stages.append(
                StageResult(
                    name="Decision → Reporting",
                    passed=True,
                    reason=(
                        "ReportingService preserved the decision "
                        "produced by DecisionOrchestrator."
                    ),
                    expected=orchestration_decision,
                    actual=reported_decision,
                )
            )


            print(
                "    integration check: PASS"
            )


            return True


        except Exception as exc:
            self._record_exception(
                "Decision → Reporting",
                exc,
            )


            return False


    # ------------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------------


    def _run_dashboard(self) -> bool:
        """
        Build and validate the final dashboard snapshot.
        """


        print()
        print("[4] Dashboard")
        print("-" * 60)


        try:
            self.dashboard_service = (
                DashboardService(
                    reporting_service=self.reporting_service,
                    decision_orchestrator=(
                        self.decision_orchestrator
                    ),
                )
            )


            self.dashboard_service.refresh()


            self.dashboard_snapshot = (
                self.dashboard_service.get_snapshot()
            )


            alerts = self.dashboard_snapshot.get(
                "alerts",
                [],
            )


            escalations = self.dashboard_snapshot.get(
                "escalations",
                [],
            )


            recent_activity = (
                self.dashboard_snapshot.get(
                    "recent_activity",
                    [],
                )
            )


            summary_metrics = (
                self.dashboard_snapshot.get(
                    "summary_metrics",
                    {},
                )
            )


            print(
                f"    alerts: "
                f"{_safe_value(alerts)}"
            )


            print(
                f"    escalations: "
                f"{_safe_value(escalations)}"
            )


            print(
                f"    recent_activity: "
                f"{_safe_value(recent_activity)}"
            )


            print(
                f"    summary_metrics: "
                f"{_safe_value(summary_metrics)}"
            )


            # --------------------------------------------------------------
            # Original decision.
            # --------------------------------------------------------------


            detection_decision = _extract(
                self.detection_result,
                "decision",
            )


            # --------------------------------------------------------------
            # Find the decision inside dashboard activity.
            # --------------------------------------------------------------


            dashboard_decisions = (
                _collect_decisions(
                    alerts
                )
                + _collect_decisions(
                    escalations
                )
                + _collect_decisions(
                    recent_activity
                )
            )


            if detection_decision not in dashboard_decisions:
                self._record_failure(
                    "Reporting → Dashboard",
                    (
                        "Dashboard snapshot does not expose "
                        "the decision produced by the pipeline."
                    ),
                    expected=detection_decision,
                    actual=dashboard_decisions,
                )


                return False


            # --------------------------------------------------------------
            # Validate summary against the reporting layer.
            #
            # We compare values produced by the same execution instead
            # of expecting fixed numbers.
            # --------------------------------------------------------------


            for key in (
                "alert_count",
                "escalation_count",
                "ignored_count",
                "total_records",
            ):
                reporting_value = (
                    self.reporting_summary.get(key)
                )


                dashboard_value = (
                    summary_metrics.get(key)
                )


                if reporting_value != dashboard_value:
                    self._record_failure(
                        "Reporting → Dashboard",
                        (
                            "Dashboard summary does not preserve "
                            f"ReportingService.{key}."
                        ),
                        expected=reporting_value,
                        actual=dashboard_value,
                    )


                    return False


            dashboard_last_result = (
                summary_metrics.get(
                    "last_result"
                )
            )


            reporting_last_result = (
                self.reporting_summary.get(
                    "last_result"
                )
            )


            reporting_last_decision = _extract(
                reporting_last_result,
                "decision",
            )


            dashboard_last_decision = _extract(
                dashboard_last_result,
                "decision",
            )


            if (
                reporting_last_decision
                != dashboard_last_decision
            ):
                self._record_failure(
                    "Reporting → Dashboard",
                    (
                        "Dashboard did not preserve "
                        "ReportingService.last_result."
                    ),
                    expected=reporting_last_decision,
                    actual=dashboard_last_decision,
                )


                return False


            self.stages.append(
                StageResult(
                    name="Reporting → Dashboard",
                    passed=True,
                    reason=(
                        "Dashboard snapshot preserved the "
                        "reporting information."
                    ),
                    expected=reporting_last_decision,
                    actual=dashboard_last_decision,
                )
            )


            print(
                "    integration check: PASS"
            )


            return True


        except Exception as exc:
            self._record_exception(
                "Reporting → Dashboard",
                exc,
            )


            return False


    # ------------------------------------------------------------------------
    # DetectionService construction
    # ------------------------------------------------------------------------


    @staticmethod
    def _create_detection_service() -> DetectionService:
        """
        Create DetectionService.


        The normal architecture expects a zero-argument service.


        If the existing implementation requires dependencies, the test
        reports that explicitly instead of modifying the service.
        """


        try:
            return DetectionService()


        except TypeError as exc:
            raise RuntimeError(
                "DetectionService could not be constructed with "
                "DetectionService(). Its constructor requires "
                "additional dependencies. "
                f"Original error: {exc}"
            ) from exc


    # ------------------------------------------------------------------------
    # Detection invocation
    # ------------------------------------------------------------------------


    @staticmethod
    def _invoke_detection(
        service: DetectionService,
    ) -> Any:
        """
        Invoke the existing DetectionService.


        The test supports common detection interfaces without changing
        DetectionService itself.


        Preferred interface:


            detect(TEST_EVENT)


        Supported fallbacks:


            detect(features=TEST_EVENT)
            detect(event=TEST_EVENT)
            process(TEST_EVENT)
            analyze(TEST_EVENT)


        If none exists, the test fails clearly.
        """


        candidates: list[
            tuple[str, Callable[..., Any]]
        ] = []


        for method_name in (
            "detect",
            "process",
            "analyze",
        ):
            method = getattr(
                service,
                method_name,
                None,
            )


            if callable(method):
                candidates.append(
                    (
                        method_name,
                        method,
                    )
                )


        if not candidates:
            raise RuntimeError(
                "DetectionService exposes none of the supported "
                "entry points: detect(), process(), analyze(). "
                "The exact public DetectionService API must be "
                "mapped before an integration test can invoke it."
            )


        last_error: Exception | None = None


        for method_name, method in candidates:
            try:
                return _call_detection_method(
                    method_name,
                    method,
                )


            except TypeError as exc:
                last_error = exc


        raise RuntimeError(
            "A DetectionService entry point was found, but none "
            "accepted the integration test input. "
            f"Last error: {last_error}"
        )


    # ------------------------------------------------------------------------
    # Reporting helpers
    # ------------------------------------------------------------------------


    def _record_failure(
        self,
        name: str,
        reason: str,
        expected: Any,
        actual: Any,
    ) -> None:
        """
        Record and print a structured failure.
        """


        result = StageResult(
            name=name,
            passed=False,
            reason=reason,
            expected=expected,
            actual=actual,
        )


        self.stages.append(result)


        print()
        print(f"[FAIL] {name}")
        print()
        print("Reason:")
        print(f"  {reason}")
        print()
        print("Expected:")
        print(f"  {_safe_value(expected)}")
        print()
        print("Actual:")
        print(f"  {_safe_value(actual)}")


    def _record_exception(
        self,
        name: str,
        exc: Exception,
    ) -> None:
        """
        Record an unexpected integration exception.
        """


        reason = (
            f"{type(exc).__name__}: {exc}"
        )


        self.stages.append(
            StageResult(
                name=name,
                passed=False,
                reason=reason,
                expected="successful execution",
                actual="exception",
            )
        )


        print()
        print(f"[FAIL] {name}")
        print()
        print("Reason:")
        print(f"  {reason}")


    # ------------------------------------------------------------------------
    # Final report
    # ------------------------------------------------------------------------


    def _full_pipeline_passed(self) -> bool:
        """
        Determine whether every required transition passed.
        """


        required = {
            "Detection",
            "Detection → Decision",
            "Decision → Reporting",
            "Reporting → Dashboard",
        }


        passed_names = {
            stage.name
            for stage in self.stages
            if stage.passed
        }


        return required.issubset(
            passed_names
        )


    def _print_header(self) -> None:
        print("=" * 60)
        print("EnterpriseGuard - Integration Test")
        print("=" * 60)
        print()
        print(
            "Pipeline:"
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


    def _print_final_result(self) -> None:
        """
        Print final structured integration report.
        """


        print()
        print("=" * 60)
        print("[5] INTEGRATION RESULT")
        print("=" * 60)


        checks = (
            "Detection → Decision",
            "Decision → Reporting",
            "Reporting → Dashboard",
        )


        for check in checks:
            stage = _find_stage(
                self.stages,
                check,
            )


            status = (
                "PASS"
                if stage is not None
                and stage.passed
                else "FAIL"
            )


            print(
                f"{check:<28} {status}"
            )


        full_status = (
            "PASS"
            if self._full_pipeline_passed()
            else "FAIL"
        )


        print(
            f"{'Full Pipeline':<28} "
            f"{full_status}"
        )


        print()


        failed_stages = [
            stage
            for stage in self.stages
            if not stage.passed
        ]


        if failed_stages:
            print(
                "Failure Details"
            )
            print(
                "-" * 60
            )


            for stage in failed_stages:
                print()
                print(
                    f"[FAIL] {stage.name}"
                )


                if stage.reason:
                    print(
                        f"Reason: {stage.reason}"
                    )


                print(
                    f"Expected: "
                    f"{_safe_value(stage.expected)}"
                )


                print(
                    f"Actual: "
                    f"{_safe_value(stage.actual)}"
                )


        print()
        print("=" * 60)


        if full_status == "PASS":
            print(
                "INTEGRATION TEST: PASS"
            )
            print(
                "The complete pipeline preserved "
                "the runtime result."
            )
        else:
            print(
                "INTEGRATION TEST: FAIL"
            )


        print("=" * 60)




# ============================================================================
# Generic helpers
# ============================================================================


def _call_detection_method(
    method_name: str,
    method: Callable[..., Any],
) -> Any:
    """
    Call a detection method using its actual signature.


    This avoids assuming a particular parameter name when the existing
    DetectionService uses a slightly different public signature.
    """


    try:
        signature = inspect.signature(method)
    except (TypeError, ValueError):
        signature = None


    if signature is None:
        return method(TEST_EVENT)


    parameters = list(
        signature.parameters.values()
    )


    positional = [
        parameter
        for parameter in parameters
        if parameter.kind
        in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )
    ]


    keyword_names = {
        parameter.name
        for parameter in parameters
        if parameter.kind
        in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        )
    }


    if "features" in keyword_names:
        return method(
            features=TEST_EVENT
        )


    if "event" in keyword_names:
        return method(
            event=TEST_EVENT
        )


    if "data" in keyword_names:
        return method(
            data=TEST_EVENT
        )


    if "record" in keyword_names:
        return method(
            record=TEST_EVENT
        )


    if positional:
        return method(TEST_EVENT)


    if not positional and not keyword_names:
        return method()


    raise TypeError(
        f"Unsupported signature for "
        f"{method_name}(): {signature}"
    )




def _extract(
    obj: Any,
    key: str,
) -> Any:
    """
    Extract a value from:


        - dict
        - dataclass
        - object attribute


    Returns None if unavailable.
    """


    if obj is None:
        return None


    if isinstance(obj, dict):
        return obj.get(key)


    if is_dataclass(obj):
        try:
            data = asdict(obj)
            return data.get(key)
        except Exception:
            pass


    return getattr(
        obj,
        key,
        None,
    )




def _extract_first(
    obj: Any,
    keys: tuple[str, ...],
) -> Any:
    """
    Return the first available non-None field.
    """


    for key in keys:
        value = _extract(
            obj,
            key,
        )


        if value is not None:
            return value


    return None




def _collect_decisions(
    values: Any,
) -> list[Any]:
    """
    Collect decision values from a list of result dictionaries/objects.
    """


    if not isinstance(values, list):
        return []


    decisions: list[Any] = []


    for value in values:
        decision = _extract(
            value,
            "decision",
        )


        if decision is not None:
            decisions.append(
                decision
            )


    return decisions




def _find_stage(
    stages: list[StageResult],
    name: str,
) -> StageResult | None:
    """
    Find a stage by name.
    """


    for stage in stages:
        if stage.name == name:
            return stage


    return None




def _safe_value(
    value: Any,
) -> Any:
    """
    Convert objects to safe printable structures.
    """


    if value is None:
        return None


    if isinstance(value, (str, int, float, bool)):
        return value


    if isinstance(value, dict):
        return {
            str(key): _safe_value(item)
            for key, item in value.items()
        }


    if isinstance(value, list):
        return [
            _safe_value(item)
            for item in value
        ]


    if isinstance(value, tuple):
        return [
            _safe_value(item)
            for item in value
        ]


    if is_dataclass(value):
        try:
            return _safe_value(
                asdict(value)
            )
        except Exception:
            pass


    if hasattr(value, "to_dict"):
        try:
            converted = value.to_dict()


            if isinstance(converted, dict):
                return _safe_value(
                    converted
                )
        except Exception:
            pass


    return repr(value)




# ============================================================================
# Self-Test of the integration-test framework itself
# ============================================================================


def self_test() -> bool:
    """
    Lightweight test for the reporting machinery of this file.


    It does NOT run the real EnterpriseGuard pipeline.
    The real pipeline is executed by main().
    """


    stage = StageResult(
        name="Example",
        passed=True,
        reason="test",
        expected="A",
        actual="A",
    )


    data = stage.to_dict()


    assert data["name"] == "Example"
    assert data["passed"] is True
    assert data["expected"] == "A"
    assert data["actual"] == "A"


    assert _safe_value(
        {"a": [1, 2, 3]}
    ) == {
        "a": [1, 2, 3]
    }


    assert _extract(
        {"decision": "ALERT"},
        "decision",
    ) == "ALERT"


    assert _extract_first(
        {"confidence": 0.8},
        (
            "missing",
            "confidence",
        ),
    ) == 0.8


    return True




# ============================================================================
# Main
# ============================================================================


def main() -> int:
    """
    Run the actual integration test.
    """


    try:
        self_test()


    except Exception as exc:
        print(
            "Integration test framework Self-Test: FAIL"
        )
        print(
            f"{type(exc).__name__}: {exc}"
        )


        return 2


    test = (
        EnterpriseGuardIntegrationTest()
    )


    try:
        passed = test.run()


    except Exception as exc:
        print()
        print(
            "Unexpected Integration Test failure:"
        )
        print(
            f"{type(exc).__name__}: {exc}"
        )
        print()


        traceback.print_exc()


        return 1


    return 0 if passed else 1




if __name__ == "__main__":
    sys.exit(
        main()
    )