"""
Unit Tests for EnterpriseGuard ADIE - Response Contracts Module
==============================================================
"""

import threading
from datetime import datetime, timedelta, timezone
from dataclasses import FrozenInstanceError
import pytest

from enterpriseguard.decision.contracts import (
    DecisionAction,
    DecisionContract,
    DecisionStatus,
)
from enterpriseguard.response.contracts import (
    ADIEResponse,
    EnforcementScope,
    ResponseConfig,
    ResponseContract,
    ResponseExecutionError,
    ResponseMode,
    ResponseStatus,
    ResponseValidationError,
    get_response_engine,
    self_test,
)


# ============================================================================
# Helpers & Mocks
# ============================================================================


def create_valid_decision_contract(
    action: DecisionAction = DecisionAction.ISOLATE_HOST,
    authorized: bool = True,
    status: DecisionStatus = DecisionStatus.AUTHORIZED,
    expired: bool = False,
) -> DecisionContract:
    now = datetime.now(timezone.utc)
    created_at = now - timedelta(seconds=600) if expired else now
    expires_at = now - timedelta(seconds=300) if expired else now + timedelta(seconds=300)

    return DecisionContract(
        decision_id="dec-valid-1234567890",
        evaluation_id="eval-valid-1234567890",
        policy_id="pol-sec-01",
        action=action,
        status=status,
        authorized=authorized,
        created_at=created_at,
        expires_at=expires_at,
        target_resource_id="srv-node-99",
    )


# ============================================================================
# Config & Data Model Validation Tests
# ============================================================================


def test_response_config_valid():
    config = ResponseConfig(
        engine_id="test-resp-engine",
        engine_version="1.0.0",
        default_mode=ResponseMode.DRY_RUN,
    )
    assert config.engine_id == "test-resp-engine"
    assert config.default_mode == ResponseMode.DRY_RUN


def test_response_contract_immutability():
    now = datetime.now(timezone.utc)
    contract = ResponseContract(
        response_id="resp-123456",
        decision_id="dec-123456",
        evaluation_id="eval-123456",
        target_resource_id="host-01",
        action=DecisionAction.ISOLATE_HOST,
        scope=EnforcementScope.NETWORK,
        mode=ResponseMode.ENFORCE,
        status=ResponseStatus.PENDING,
        created_at=now,
    )

    with pytest.raises(FrozenInstanceError):
        contract.status = ResponseStatus.COMPLETED  # type: ignore


def test_response_contract_non_utc_rejection():
    naive_dt = datetime.now()

    with pytest.raises(ResponseValidationError):
        ResponseContract(
            response_id="resp-123",
            decision_id="dec-123",
            evaluation_id="eval-123",
            target_resource_id="host-01",
            action=DecisionAction.DISPATCH_ALERT,
            scope=EnforcementScope.APPLICATION,
            mode=ResponseMode.ENFORCE,
            status=ResponseStatus.PENDING,
            created_at=naive_dt,
        )


def test_response_contract_provenance_hash():
    now = datetime.now(timezone.utc)
    contract = ResponseContract(
        response_id="resp-abc123456",
        decision_id="dec-abc123456",
        evaluation_id="eval-abc123456",
        target_resource_id="user-session-01",
        action=DecisionAction.CONTAIN_SESSION,
        scope=EnforcementScope.IDENTITY,
        mode=ResponseMode.ENFORCE,
        status=ResponseStatus.PENDING,
        created_at=now,
    )

    assert len(contract.provenance_hash) == 64
    assert contract.to_dict()["provenance_hash"] == contract.provenance_hash


# ============================================================================
# Fail-Closed Safety & Policy Integration Tests
# ============================================================================


def test_create_response_directive_success():
    engine = ADIEResponse()
    decision = create_valid_decision_contract(action=DecisionAction.ISOLATE_HOST)

    directive = engine.create_response_directive(decision)

    assert directive.decision_id == decision.decision_id
    assert directive.action == DecisionAction.ISOLATE_HOST
    assert directive.scope == EnforcementScope.NETWORK
    assert directive.status == ResponseStatus.PENDING
    assert directive.mode == ResponseMode.ENFORCE


def test_create_response_directive_rejects_unauthorized_decision():
    engine = ADIEResponse()
    decision = create_valid_decision_contract(
        authorized=False,
        status=DecisionStatus.DENIED,
    )

    with pytest.raises(ResponseExecutionError, match="Cannot create response directive for unauthorized decision"):
        engine.create_response_directive(decision)


def test_create_response_directive_rejects_expired_decision():
    engine = ADIEResponse()
    decision = create_valid_decision_contract(expired=True)

    with pytest.raises(ResponseExecutionError, match="Cannot execute expired decision contract"):
        engine.create_response_directive(decision)


def test_create_response_directive_override_mode():
    engine = ADIEResponse()
    decision = create_valid_decision_contract()

    directive = engine.create_response_directive(
        decision,
        override_mode=ResponseMode.DRY_RUN,
    )

    assert directive.mode == ResponseMode.DRY_RUN
    assert directive.status == ResponseStatus.SKIPPED  # DRY_RUN should result in SKIPPED status by default


def test_create_response_directive_disallowed_scope():
    restricted_config = ResponseConfig(
        engine_id="restricted-engine",
        engine_version="1.0.0",
        allowed_scopes=(EnforcementScope.APPLICATION, EnforcementScope.IDENTITY),
    )
    engine = ADIEResponse(config=restricted_config)
    decision = create_valid_decision_contract(action=DecisionAction.ISOLATE_HOST)  # Network scope

    with pytest.raises(ResponseExecutionError, match="Enforcement scope 'network' is disallowed"):
        engine.create_response_directive(decision)


# ============================================================================
# Thread Safety & Singleton Tests
# ============================================================================


def test_response_engine_thread_safety():
    engine = ADIEResponse()
    decision = create_valid_decision_contract()

    def worker():
        for _ in range(50):
            engine.create_response_directive(decision)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert engine.status()["responses_created"] == 500


def test_singleton_get_response_engine():
    engine1 = get_response_engine()
    engine2 = get_response_engine()
    assert engine1 is engine2


def test_module_self_test_execution():
    result = self_test()
    assert result["passed"] is True
    assert result["tests"]["directive_created"] is True
    assert result["tests"]["immutable_contract"] is True
