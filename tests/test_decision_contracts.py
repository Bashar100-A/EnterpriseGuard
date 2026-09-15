"""
Unit Tests for EnterpriseGuard ADIE - Decision Contracts Module
==============================================================
"""

import threading
from datetime import datetime, timedelta, timezone
from dataclasses import FrozenInstanceError
import pytest

from enterpriseguard.decision.contracts import (
    ADIEDecision,
    DecisionAction,
    DecisionConfig,
    DecisionContract,
    DecisionEvaluationError,
    DecisionStatus,
    DecisionValidationError,
    get_decision_engine,
    self_test,
)


class DummyPolicyEvaluation:
    """Mock PolicyEvaluation object mimicking policy domain output."""

    def __init__(
        self,
        evaluation_id: str = "peval-999988887777666655554444",
        policy_id: str = "policy-sec-01",
        intent: str = "contain",
        allowed: bool = True,
        decision_score: float = 0.92,
    ):
        self.evaluation_id = evaluation_id
        self.policy_id = policy_id
        self.intent = intent
        self.allowed = allowed
        self.decision_score = decision_score


# ============================================================================
# Config & Validation Tests
# ============================================================================


def test_decision_config_valid():
    config = DecisionConfig(
        engine_id="test-engine",
        engine_version="1.2.0",
        ttl_seconds=600,
    )
    assert config.engine_id == "test-engine"
    assert config.ttl_seconds == 600


def test_decision_config_invalid_ttl():
    with pytest.raises(DecisionValidationError):
        DecisionConfig(engine_id="engine", engine_version="1.0", ttl_seconds=0)

    with pytest.raises(DecisionValidationError):
        DecisionConfig(engine_id="engine", engine_version="1.0", ttl_seconds=7200)


# ============================================================================
# Contract Integrity & Immutability Tests
# ============================================================================


def test_decision_contract_immutability():
    now = datetime.now(timezone.utc)
    contract = DecisionContract(
        decision_id="dec-12345",
        evaluation_id="eval-12345",
        policy_id="pol-12345",
        action=DecisionAction.DISPATCH_ALERT,
        status=DecisionStatus.AUTHORIZED,
        authorized=True,
        created_at=now,
        expires_at=now + timedelta(seconds=300),
        target_resource_id="host-01",
    )

    with pytest.raises(FrozenInstanceError):
        contract.authorized = False  # type: ignore


def test_decision_contract_non_utc_rejection():
    naive_dt = datetime.now()
    valid_dt = datetime.now(timezone.utc)

    with pytest.raises(DecisionValidationError):
        DecisionContract(
            decision_id="dec-123",
            evaluation_id="eval-123",
            policy_id="pol-123",
            action=DecisionAction.NO_ACTION,
            status=DecisionStatus.AUTHORIZED,
            authorized=True,
            created_at=naive_dt,  # Naive timezone
            expires_at=valid_dt,
            target_resource_id="host-01",
        )


def test_decision_contract_provenance_hash_generation():
    now = datetime.now(timezone.utc)
    contract = DecisionContract(
        decision_id="dec-abc1234567890",
        evaluation_id="eval-abc1234567890",
        policy_id="pol-sec-01",
        action=DecisionAction.CONTAIN_SESSION,
        status=DecisionStatus.AUTHORIZED,
        authorized=True,
        created_at=now,
        expires_at=now + timedelta(seconds=300),
        target_resource_id="user-session-99",
    )

    assert len(contract.provenance_hash) == 64  # Valid SHA-256 length
    assert contract.to_dict()["provenance_hash"] == contract.provenance_hash


def test_decision_contract_expiration_check():
    now = datetime.now(timezone.utc)
    past_created = now - timedelta(seconds=600)
    past_expires = now - timedelta(seconds=300)

    contract = DecisionContract(
        decision_id="dec-exp-123",
        evaluation_id="eval-exp-123",
        policy_id="pol-exp-123",
        action=DecisionAction.REJECT_REQUEST,
        status=DecisionStatus.EXPIRED,
        authorized=False,
        created_at=past_created,
        expires_at=past_expires,
        target_resource_id="api-endpoint",
    )

    assert contract.is_expired(current_time=now) is True


# ============================================================================
# Engine Evaluation & Fail-Closed Safety Tests
# ============================================================================


def test_evaluate_policy_result_success():
    engine = ADIEDecision()
    mock_eval = DummyPolicyEvaluation(intent="isolate", allowed=True)

    contract = engine.evaluate_policy_result(
        policy_evaluation=mock_eval,
        target_resource_id="server-node-04",
    )

    assert contract.authorized is True
    assert contract.status == DecisionStatus.AUTHORIZED
    assert contract.action == DecisionAction.ISOLATE_HOST
    assert contract.parameters["mapped_intent"] == "isolate"


def test_evaluate_policy_result_disallowed_policy():
    engine = ADIEDecision()
    mock_eval = DummyPolicyEvaluation(intent="isolate", allowed=False)

    contract = engine.evaluate_policy_result(
        policy_evaluation=mock_eval,
        target_resource_id="server-node-04",
    )

    assert contract.authorized is False
    assert contract.status == DecisionStatus.DENIED
    assert contract.action == DecisionAction.NO_ACTION


def test_map_intent_fail_closed_on_unknown():
    engine = ADIEDecision()
    mock_eval = DummyPolicyEvaluation(intent="MALICIOUS_CUSTOM_INTENT", allowed=True)

    with pytest.raises(DecisionEvaluationError, match="Unrecognized policy evaluation intent"):
        engine.evaluate_policy_result(
            policy_evaluation=mock_eval,
            target_resource_id="server-01",
        )


# ============================================================================
# Concurrency & Module Self-Test
# ============================================================================


def test_thread_safety_counter():
    engine = ADIEDecision()
    mock_eval = DummyPolicyEvaluation()

    def worker():
        for _ in range(50):
            engine.evaluate_policy_result(mock_eval, target_resource_id="res-1")

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert engine.status()["decisions_evaluated"] == 500


def test_singleton_get_engine():
    engine1 = get_decision_engine()
    engine2 = get_decision_engine()
    assert engine1 is engine2


def test_module_self_test_execution():
    result = self_test()
    assert result["passed"] is True
    assert result["tests"]["contract_created"] is True
    assert result["tests"]["immutable_contract"] is True
