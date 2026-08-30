"""
EnterpriseGuard - ADIE Decision Engine
======================================

Adaptive Defense Intelligence Engine (ADIE)

Decision Engine
---------------

Architectural chain:

    Enterprise State
          |
          v
    Prediction Engine
          |
          |  Future belief
          v
      Policy Engine
          |
          |  Constraint / permission evaluation
          v
     Decision Engine
          |
          |  Defensible control-plane intent
          v
      Response Layer
          |
          |  Execution
          v
        Action


Core semantic boundary
----------------------

Prediction = Future belief
Policy     = Constraint / permission evaluation
Decision   = Defensible control-plane intent
Response   = Execution


Responsibility
--------------

DecisionEngine transforms a Policy-derived DecisionEvaluation and its
associated DecisionRequest into one immutable Decision contract.

The engine does NOT:

- perform prediction
- evaluate policy
- calculate risk thresholds
- execute actions
- invoke response handlers
- mutate enterprise state
- access the filesystem
- access the network
- execute shell commands
- invoke dashboards
- invoke detectors
- invoke model managers
- invoke training services


Design principles
-----------------

- contract-first
- policy-authoritative
- provenance-preserving
- execution-free
- deterministic in resolution
- immutable output
- explicit error classification
- domain isolation
- no compatibility guessing
- no hidden fallback behavior
- auditable construction


Input boundary
--------------

    DecisionRequest
          +
    DecisionEvaluation

Output boundary
---------------

    Decision


Important distinction
---------------------

The DecisionEngine constructs intent.

It does not execute intent.

Therefore:

    decision.actionable == True

means:

    "the Decision may cross the downstream response boundary"

It does NOT mean:

    "the action has been executed"


Policy authority
----------------

DecisionEvaluation is assumed to be the already-produced result of Policy
evaluation.

The DecisionEngine therefore never re-evaluates Policy.

Policy-derived semantic fields are authoritative:

    evaluation.decision_type
    evaluation.priority
    evaluation.authorized
    evaluation.policy_compliant
    evaluation.rationale
    evaluation.constraints
    evaluation.policy_reference
    evaluation.prediction_reference

DecisionRequest values are treated as caller-side requested context.

When a requested type or priority is supplied, it MUST agree with the
Policy-derived evaluation.

The request cannot override Policy authority.

Lifecycle resolution
--------------------

    policy_compliant + authorized + non-DEFER
        -> APPROVED

    decision_type == DEFER
        -> DEFERRED

    policy_compliant + unauthorized
        -> BLOCKED

    non-policy-compliant
        -> REJECTED

No unauthorized or non-compliant Decision can become APPROVED.

No DEFER intent can become APPROVED.

Error model
-----------

DecisionEngineError
    |
    +-- DecisionInputError
    +-- DecisionConsistencyError
    +-- DecisionAuthorizationError
    +-- DecisionContractError

The engine does not swallow domain errors.

Higher layers may translate these exceptions into API responses.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from .contracts import (
    ARCHITECTURAL_CHAIN,
    DECISION_CONTRACT_VERSION,
    DECISION_DOMAIN,
    DECISION_SCHEMA_VERSION,
    DECISION_SEMANTIC_ROLE,
    POLICY_SEMANTIC_ROLE,
    PREDICTION_SEMANTIC_ROLE,
    RESPONSE_SEMANTIC_ROLE,
    Decision,
    DecisionEvaluation,
    DecisionPriority,
    DecisionRequest,
    DecisionStatus,
    DecisionType,
    decision_to_dict,
    validate_decision,
    validate_decision_evaluation,
    validate_decision_request,
)


# ============================================================================
# Public API
# ============================================================================

__all__ = [
    "DECISION_ENGINE_VERSION",
    "DECISION_ENGINE_DOMAIN",
    "DECISION_ENGINE_METADATA",
    "DecisionEngineError",
    "DecisionInputError",
    "DecisionConsistencyError",
    "DecisionAuthorizationError",
    "DecisionContractError",
    "DecisionEngine",
    "self_test",
]


# ============================================================================
# Engine metadata
# ============================================================================

DECISION_ENGINE_VERSION = "1.0.0"

DECISION_ENGINE_DOMAIN = DECISION_DOMAIN

DECISION_ENGINE_METADATA = {
    "engine": "adie-decision-engine",
    "version": DECISION_ENGINE_VERSION,
    "domain": DECISION_ENGINE_DOMAIN,
    "contract_version": DECISION_CONTRACT_VERSION,
    "schema_version": DECISION_SCHEMA_VERSION,
    "architecture": "prediction->policy->decision->response",
    "semantic_role": DECISION_SEMANTIC_ROLE,
    "execution_enabled": False,
    "policy_re_evaluation": False,
    "prediction_execution": False,
    "response_execution": False,
}


# ============================================================================
# Error model
# ============================================================================


class DecisionEngineError(Exception):
    """
    Base exception for all DecisionEngine domain errors.

    The exception is intentionally domain-specific so higher layers can
    distinguish Decision failures from infrastructure failures.
    """


class DecisionInputError(DecisionEngineError):
    """
    Raised when the DecisionEngine receives an invalid input type.

    Examples:

    - request is not a DecisionRequest
    - evaluation is not a DecisionEvaluation
    - decision_id is invalid
    """


class DecisionConsistencyError(DecisionEngineError):
    """
    Raised when valid contracts disagree semantically.

    Examples:

    - request type != Policy-derived decision type
    - request priority != Policy-derived priority
    - request policy reference != evaluation policy reference
    - request prediction reference != evaluation prediction reference
    """


class DecisionAuthorizationError(DecisionEngineError):
    """
    Raised when an explicitly requested or constructed approval violates
    Policy-derived authorization semantics.
    """


class DecisionContractError(DecisionEngineError):
    """
    Raised when a contract supplied to or produced by the engine violates
    its domain invariants.
    """


# ============================================================================
# Decision Engine
# ============================================================================


class DecisionEngine:
    """
    Pure-ish domain orchestration engine for ADIE Decision construction.

    The engine has no external integrations and no execution capability.

    Input:

        DecisionRequest
        DecisionEvaluation

    Output:

        Decision

    The engine's authority model is intentionally simple:

        Policy-derived evaluation
                    |
                    v
        Decision semantic resolution
                    |
                    v
              Decision

    The engine does not determine whether something is risky.

    The engine does not determine whether a Policy should authorize an
    operation.

    Those responsibilities belong upstream.
    """

    __slots__ = ()

    # ========================================================================
    # Metadata
    # ========================================================================

    @property
    def metadata(self) -> dict[str, Any]:
        """
        Return a defensive copy of engine metadata.

        Returning a new dictionary prevents callers from mutating the
        module-level metadata contract.
        """
        return dict(DECISION_ENGINE_METADATA)

    # ========================================================================
    # Public construction API
    # ========================================================================

    def build(
        self,
        *,
        decision_id: str,
        request: DecisionRequest,
        evaluation: DecisionEvaluation,
        expires_at: datetime | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> Decision:
        """
        Build one immutable Decision from a validated Policy-derived
        evaluation.

        Parameters
        ----------
        decision_id:
            Unique identifier of the resulting Decision.

        request:
            Immutable DecisionRequest entering the Decision domain.

        evaluation:
            Immutable Policy-derived DecisionEvaluation.

        expires_at:
            Optional absolute UTC expiration timestamp.

        metadata:
            Optional caller-provided metadata.

        Returns
        -------
        Decision
            Fully validated immutable Decision.

        Raises
        ------
        DecisionInputError
            Invalid top-level input.

        DecisionConsistencyError
            Request and Policy-derived evaluation disagree.

        DecisionAuthorizationError
            Approval semantics are inconsistent with authorization.

        DecisionContractError
            Input or output violates a Decision contract.
        """
        self._validate_inputs(
            decision_id=decision_id,
            request=request,
            evaluation=evaluation,
        )

        self._validate_request_evaluation_consistency(
            request=request,
            evaluation=evaluation,
        )

        resolved_status = self._resolve_status(
            evaluation=evaluation,
        )

        resolved_metadata = self._build_metadata(
            metadata=metadata,
        )

        try:
            decision = Decision.from_evaluation(
                decision_id=decision_id,
                request=request,
                evaluation=evaluation,
                status=resolved_status,
                expires_at=expires_at,
                metadata=resolved_metadata,
            )
        except ValueError as exc:
            raise DecisionContractError(
                "Decision construction failed because the "
                "resulting contract violated a Decision invariant."
            ) from exc
        except TypeError as exc:
            raise DecisionContractError(
                "Decision construction failed because the "
                "resulting contract received an invalid value."
            ) from exc

        try:
            validate_decision(decision)
        except (TypeError, ValueError) as exc:
            raise DecisionContractError(
                "Final Decision validation failed."
            ) from exc

        return decision

    # ========================================================================
    # Explicit resolution API
    # ========================================================================

    def resolve_status(
        self,
        evaluation: DecisionEvaluation,
    ) -> DecisionStatus:
        """
        Resolve lifecycle status from Policy-derived evaluation.

        This method is deterministic and contains no risk thresholds.

        Resolution:

            non-compliant
                -> REJECTED

            DEFER intent
                -> DEFERRED

            unauthorized
                -> BLOCKED

            authorized + compliant
                -> APPROVED

        Policy-derived evaluation remains the source of authority.
        """
        self._validate_evaluation(
            evaluation
        )

        return self._resolve_status(
            evaluation=evaluation,
        )

    # ========================================================================
    # Input validation
    # ========================================================================

    def _validate_inputs(
        self,
        *,
        decision_id: str,
        request: DecisionRequest,
        evaluation: DecisionEvaluation,
    ) -> None:
        """
        Validate top-level engine inputs.

        Validation is intentionally contract-first.

        There are no alternate signatures and no compatibility fallbacks.
        """
        if not isinstance(decision_id, str):
            raise DecisionInputError(
                "decision_id must be a string."
            )

        if not decision_id.strip():
            raise DecisionInputError(
                "decision_id must not be empty."
            )

        self._validate_request(
            request
        )

        self._validate_evaluation(
            evaluation
        )

    def _validate_request(
        self,
        request: DecisionRequest,
    ) -> None:
        """Validate a DecisionRequest using the canonical contract."""
        if not isinstance(request, DecisionRequest):
            raise DecisionInputError(
                "request must be a DecisionRequest."
            )

        try:
            validate_decision_request(
                request
            )
        except (TypeError, ValueError) as exc:
            raise DecisionContractError(
                "DecisionRequest violates its canonical contract."
            ) from exc

    def _validate_evaluation(
        self,
        evaluation: DecisionEvaluation,
    ) -> None:
        """Validate a DecisionEvaluation using the canonical contract."""
        if not isinstance(
            evaluation,
            DecisionEvaluation,
        ):
            raise DecisionInputError(
                "evaluation must be a DecisionEvaluation."
            )

        try:
            validate_decision_evaluation(
                evaluation
            )
        except (TypeError, ValueError) as exc:
            raise DecisionContractError(
                "DecisionEvaluation violates its canonical contract."
            ) from exc

    # ========================================================================
    # Cross-contract consistency
    # ========================================================================

    def _validate_request_evaluation_consistency(
        self,
        *,
        request: DecisionRequest,
        evaluation: DecisionEvaluation,
    ) -> None:
        """
        Validate semantic consistency between request and Policy evaluation.

        Policy-derived values remain authoritative.

        A caller cannot silently override them through DecisionRequest.
        """

        if (
            request.policy_evaluation_id
            != evaluation.policy_evaluation_id
        ):
            raise DecisionConsistencyError(
                "request.policy_evaluation_id must match "
                "evaluation.policy_evaluation_id."
            )

        if (
            request.policy_reference is not None
            and evaluation.policy_reference is not None
            and request.policy_reference
            != evaluation.policy_reference
        ):
            raise DecisionConsistencyError(
                "request.policy_reference must match "
                "evaluation.policy_reference when both are provided."
            )

        if (
            request.prediction_reference is not None
            and evaluation.prediction_reference is not None
            and request.prediction_reference
            != evaluation.prediction_reference
        ):
            raise DecisionConsistencyError(
                "request.prediction_reference must match "
                "evaluation.prediction_reference when both are provided."
            )

        if (
            request.requested_type is not None
            and request.requested_type
            != evaluation.decision_type
        ):
            raise DecisionConsistencyError(
                "request.requested_type must match the "
                "Policy-derived evaluation.decision_type."
            )

        if (
            request.requested_priority is not None
            and request.requested_priority
            != evaluation.priority
        ):
            raise DecisionConsistencyError(
                "request.requested_priority must match the "
                "Policy-derived evaluation.priority."
            )

    # ========================================================================
    # Status resolution
    # ========================================================================

    def _resolve_status(
        self,
        *,
        evaluation: DecisionEvaluation,
    ) -> DecisionStatus:
        """
        Resolve lifecycle state without introducing policy logic.

        The engine only interprets already-resolved Policy semantics.

        No score threshold is evaluated here.

        No risk classification occurs here.
        """

        if not evaluation.policy_compliant:
            return DecisionStatus.REJECTED

        if evaluation.decision_type == DecisionType.DEFER:
            return DecisionStatus.DEFERRED

        if not evaluation.authorized:
            return DecisionStatus.BLOCKED

        if evaluation.authorized and evaluation.policy_compliant:
            return DecisionStatus.APPROVED

        # Defensive unreachable boundary.
        raise DecisionAuthorizationError(
            "Decision status could not be resolved from the "
            "Policy-derived evaluation."
        )

    # ========================================================================
    # Metadata
    # ========================================================================

    def _build_metadata(
        self,
        *,
        metadata: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        """
        Build metadata without mutating caller-owned data.

        Engine metadata is authoritative for engine-level fields.

        Caller metadata may add additional audit context but cannot overwrite
        the engine's architectural declarations.
        """
        if metadata is None:
            caller_metadata: dict[str, Any] = {}
        elif isinstance(metadata, Mapping):
            caller_metadata = dict(metadata)
        else:
            raise DecisionInputError(
                "metadata must be a mapping or None."
            )

        protected_keys = set(
            DECISION_ENGINE_METADATA.keys()
        )

        for key in caller_metadata:
            if not isinstance(key, str):
                raise DecisionInputError(
                    "metadata keys must be strings."
                )

            if key in protected_keys:
                raise DecisionConsistencyError(
                    f"metadata key '{key}' is reserved by "
                    "DecisionEngine and cannot be overridden."
                )

        result = dict(
            DECISION_ENGINE_METADATA
        )

        result.update(
            caller_metadata
        )

        return result


# ============================================================================
# Self-Test
# ============================================================================


def self_test() -> bool:
    """
    Comprehensive isolated DecisionEngine self-test.

    The self-test deliberately exercises both successful construction and
    architectural rejection boundaries.

    Every assertion contains an explicit diagnostic message so failures
    identify the violated invariant immediately.
    """

    # ========================================================================
    # Test fixtures
    # ========================================================================

    from datetime import timedelta

    from .contracts import (
        DecisionConstraint,
        DecisionRationale,
    )

    engine = DecisionEngine()

    rationale = DecisionRationale(
        summary=(
            "Policy evaluation authorizes a containment intent "
            "for the evaluated security condition."
        ),
        basis=(
            "elevated_risk",
            "policy_match",
            "containment_required",
        ),
        policy_reference="policy.security.001",
        confidence=0.94,
    )

    constraint = DecisionConstraint(
        name="approval_required",
        value=True,
        mandatory=True,
        source="policy",
        description="Downstream handling requires approval.",
    )

    request = DecisionRequest(
        policy_evaluation_id="policy-eval-engine-001",
        subject="entity-engine-001",
        requested_type=DecisionType.CONTAIN,
        requested_priority=DecisionPriority.HIGH,
        policy_reference="policy.security.001",
        prediction_reference="prediction-engine-001",
        context={
            "origin": "policy",
            "risk_band": "high",
        },
        request_id="decision-request-engine-001",
    )

    evaluation = DecisionEvaluation(
        policy_evaluation_id="policy-eval-engine-001",
        authorized=True,
        decision_type=DecisionType.CONTAIN,
        priority=DecisionPriority.HIGH,
        rationale=rationale,
        constraints=(
            constraint,
        ),
        score=0.91,
        policy_compliant=True,
        policy_reference="policy.security.001",
        prediction_reference="prediction-engine-001",
        metadata={
            "policy_version": "1.0.0",
        },
    )

    # ========================================================================
    # 1. Engine initialization
    # ========================================================================

    assert isinstance(
        engine,
        DecisionEngine,
    ), (
        "DecisionEngine() must construct a valid DecisionEngine instance."
    )

    print("[PASS] Engine initialization")

    # ========================================================================
    # 2. Engine metadata
    # ========================================================================

    engine_metadata = engine.metadata

    assert isinstance(
        engine_metadata,
        dict,
    ), (
        "DecisionEngine.metadata must return a dictionary."
    )

    assert (
        engine_metadata["engine"]
        == "adie-decision-engine"
    ), (
        "Engine metadata must identify the ADIE Decision Engine."
    )

    assert (
        engine_metadata["domain"]
        == DECISION_ENGINE_DOMAIN
    ), (
        "Engine metadata domain must match the Decision domain."
    )

    assert (
        engine_metadata["contract_version"]
        == DECISION_CONTRACT_VERSION
    ), (
        "Engine metadata contract_version must match the canonical "
        "Decision contract version."
    )

    assert (
        engine_metadata["schema_version"]
        == DECISION_SCHEMA_VERSION
    ), (
        "Engine metadata schema_version must match the canonical "
        "Decision schema version."
    )

    print("[PASS] Metadata contract")

    # ========================================================================
    # 3. Execution-free metadata
    # ========================================================================

    assert (
        engine_metadata["execution_enabled"] is False
    ), (
        "DecisionEngine must explicitly declare execution_enabled=False."
    )

    assert (
        engine_metadata["policy_re_evaluation"] is False
    ), (
        "DecisionEngine must never re-evaluate Policy."
    )

    assert (
        engine_metadata["prediction_execution"] is False
    ), (
        "DecisionEngine must never execute Prediction."
    )

    assert (
        engine_metadata["response_execution"] is False
    ), (
        "DecisionEngine must never execute Response."
    )

    print("[PASS] Execution-free boundary")

    # ========================================================================
    # 4. Request validation
    # ========================================================================

    try:
        engine._validate_request(
            request
        )
    except DecisionEngineError as exc:
        raise AssertionError(
            "A valid DecisionRequest must pass DecisionEngine validation."
        ) from exc

    print("[PASS] Request validation")

    # ========================================================================
    # 5. Evaluation validation
    # ========================================================================

    try:
        engine._validate_evaluation(
            evaluation
        )
    except DecisionEngineError as exc:
        raise AssertionError(
            "A valid DecisionEvaluation must pass DecisionEngine validation."
        ) from exc

    print("[PASS] Evaluation validation")

    # ========================================================================
    # 6. Policy provenance
    # ========================================================================

    assert (
        request.policy_evaluation_id
        == evaluation.policy_evaluation_id
    ), (
        "Request and Policy evaluation must share the same evaluation ID."
    )

    assert (
        evaluation.policy_reference
        == "policy.security.001"
    ), (
        "Policy provenance must remain attached to the evaluation."
    )

    print("[PASS] Policy provenance")

    # ========================================================================
    # 7. Prediction provenance
    # ========================================================================

    assert (
        request.prediction_reference
        == evaluation.prediction_reference
    ), (
        "Prediction provenance must remain consistent between request "
        "and evaluation."
    )

    print("[PASS] Prediction provenance")

    # ========================================================================
    # 8. Type resolution
    # ========================================================================

    resolved_type = evaluation.decision_type

    assert (
        resolved_type == DecisionType.CONTAIN
    ), (
        "Decision type must be taken from the Policy-derived evaluation."
    )

    print("[PASS] Type resolution")

    # ========================================================================
    # 9. Priority resolution
    # ========================================================================

    resolved_priority = evaluation.priority

    assert (
        resolved_priority == DecisionPriority.HIGH
    ), (
        "Decision priority must be taken from the Policy-derived evaluation."
    )

    print("[PASS] Priority resolution")

    # ========================================================================
    # 10. Request cannot override type
    # ========================================================================

    conflicting_type_request = DecisionRequest(
        policy_evaluation_id="policy-eval-engine-001",
        subject="entity-engine-001",
        requested_type=DecisionType.BLOCK,
        requested_priority=DecisionPriority.HIGH,
        policy_reference="policy.security.001",
        prediction_reference="prediction-engine-001",
    )

    type_conflict_failed = False

    try:
        engine.build(
            decision_id="decision-type-conflict",
            request=conflicting_type_request,
            evaluation=evaluation,
        )
    except DecisionConsistencyError:
        type_conflict_failed = True

    assert type_conflict_failed is True, (
        "A request must not override a Policy-derived Decision type."
    )

    print("[PASS] Type authority boundary")

    # ========================================================================
    # 11. Request cannot override priority
    # ========================================================================

    conflicting_priority_request = DecisionRequest(
        policy_evaluation_id="policy-eval-engine-001",
        subject="entity-engine-001",
        requested_type=DecisionType.CONTAIN,
        requested_priority=DecisionPriority.CRITICAL,
        policy_reference="policy.security.001",
        prediction_reference="prediction-engine-001",
    )

    priority_conflict_failed = False

    try:
        engine.build(
            decision_id="decision-priority-conflict",
            request=conflicting_priority_request,
            evaluation=evaluation,
        )
    except DecisionConsistencyError:
        priority_conflict_failed = True

    assert priority_conflict_failed is True, (
        "A request must not elevate Policy-derived priority."
    )

    print("[PASS] Priority authority boundary")

    # ========================================================================
    # 12. Successful Decision construction
    # ========================================================================

    decision = engine.build(
        decision_id="decision-engine-001",
        request=request,
        evaluation=evaluation,
        metadata={
            "source": "decision-engine-self-test",
        },
    )

    assert isinstance(
        decision,
        Decision,
    ), (
        "DecisionEngine.build() must return a Decision contract."
    )

    print("[PASS] Decision construction")

    # ========================================================================
    # 13. Type preservation
    # ========================================================================

    assert (
        decision.decision_type
        == evaluation.decision_type
    ), (
        "Final Decision type must exactly preserve the "
        "Policy-derived evaluation type."
    )

    print("[PASS] Type preservation")

    # ========================================================================
    # 14. Priority preservation
    # ========================================================================

    assert (
        decision.priority
        == evaluation.priority
    ), (
        "Final Decision priority must exactly preserve the "
        "Policy-derived evaluation priority."
    )

    print("[PASS] Priority preservation")

    # ========================================================================
    # 15. Authorization preservation
    # ========================================================================

    assert (
        decision.authorized
        == evaluation.authorized
    ), (
        "Decision authorization must preserve Policy-derived authorization."
    )

    print("[PASS] Authorization preservation")

    # ========================================================================
    # 16. Policy compliance preservation
    # ========================================================================

    assert (
        decision.policy_compliant
        == evaluation.policy_compliant
    ), (
        "Decision policy_compliant must preserve the Policy-derived state."
    )

    print("[PASS] Policy compliance preservation")

    # ========================================================================
    # 17. Rationale preservation
    # ========================================================================

    assert (
        decision.rationale
        == evaluation.rationale
    ), (
        "Decision rationale must be preserved from the "
        "Policy-derived evaluation."
    )

    print("[PASS] Rationale preservation")

    # ========================================================================
    # 18. Constraint propagation
    # ========================================================================

    assert (
        decision.constraints
        == evaluation.constraints
    ), (
        "Decision constraints must exactly preserve Policy-derived "
        "constraints."
    )

    assert (
        decision.constraints[0].mandatory is True
    ), (
        "DecisionEngine must not remove or weaken mandatory constraints."
    )

    print("[PASS] Constraint propagation")

    # ========================================================================
    # 19. Policy evaluation provenance
    # ========================================================================

    assert (
        decision.policy_evaluation_id
        == "policy-eval-engine-001"
    ), (
        "Decision must preserve the upstream Policy evaluation ID."
    )

    print("[PASS] Policy evaluation provenance")

    # ========================================================================
    # 20. Prediction provenance
    # ========================================================================

    assert (
        decision.prediction_reference
        == "prediction-engine-001"
    ), (
        "Decision must preserve Prediction provenance without treating it "
        "as authorization."
    )

    print("[PASS] Prediction provenance propagation")

    # ========================================================================
    # 21. Rationale policy reference
    # ========================================================================

    assert (
        decision.rationale.policy_reference
        == "policy.security.001"
    ), (
        "Decision rationale must preserve its Policy reference."
    )

    print("[PASS] Rationale provenance")

    # ========================================================================
    # 22. Status resolution
    # ========================================================================

    assert (
        decision.status
        == DecisionStatus.APPROVED
    ), (
        "A compliant, authorized, non-DEFER evaluation must resolve to "
        "APPROVED."
    )

    print("[PASS] Approval resolution")

    # ========================================================================
    # 23. Actionable boundary
    # ========================================================================

    assert (
        decision.actionable is True
    ), (
        "An approved, authorized, compliant, non-expired Decision must "
        "be actionable."
    )

    print("[PASS] Actionable boundary")

    # ========================================================================
    # 24. Actionable is not execution
    # ========================================================================

    assert (
        engine_metadata["execution_enabled"] is False
    ), (
        "Actionable Decision must remain separate from execution capability."
    )

    print("[PASS] Actionable != execution")

    # ========================================================================
    # 25. Metadata propagation
    # ========================================================================

    serialized = decision_to_dict(
        decision
    )

    assert (
        serialized["metadata"]["engine"]
        == "adie-decision-engine"
    ), (
        "Decision metadata must identify the DecisionEngine."
    )

    assert (
        serialized["metadata"]["source"]
        == "decision-engine-self-test"
    ), (
        "Caller metadata must be preserved when it does not conflict "
        "with reserved engine metadata."
    )

    print("[PASS] Metadata propagation")

    # ========================================================================
    # 26. Metadata immutability boundary
    # ========================================================================

    external_metadata = {
        "external": {
            "source": "caller",
        }
    }

    metadata_decision = engine.build(
        decision_id="decision-metadata-001",
        request=request,
        evaluation=evaluation,
        metadata=external_metadata,
    )

    external_metadata["external"]["source"] = "mutated"

    serialized_metadata_decision = decision_to_dict(
        metadata_decision
    )

    assert (
        serialized_metadata_decision["metadata"]["external"]["source"]
        == "caller"
    ), (
        "Decision metadata must not depend on later mutation of "
        "caller-owned input mappings."
    )

    print("[PASS] Metadata input isolation")

    # ========================================================================
    # 27. Input request immutability
    # ========================================================================

    request_before = request.to_dict()

    input_immutability_decision = engine.build(
        decision_id="decision-input-immutability",
        request=request,
        evaluation=evaluation,
    )

    request_after = request.to_dict()

    assert (
        request_before == request_after
    ), (
        "DecisionEngine must not mutate DecisionRequest."
    )

    assert (
        input_immutability_decision.request == request
    ), (
        "Decision must preserve the original immutable DecisionRequest."
    )

    print("[PASS] Request immutability")

    # ========================================================================
    # 28. Evaluation immutability
    # ========================================================================

    evaluation_before = evaluation.to_dict()

    engine.build(
        decision_id="decision-evaluation-immutability",
        request=request,
        evaluation=evaluation,
    )

    evaluation_after = evaluation.to_dict()

    assert (
        evaluation_before == evaluation_after
    ), (
        "DecisionEngine must not mutate DecisionEvaluation."
    )

    print("[PASS] Evaluation immutability")

    # ========================================================================
    # 29. Unauthorized lifecycle
    # ========================================================================

    unauthorized_evaluation = DecisionEvaluation(
        policy_evaluation_id="policy-eval-unauthorized",
        authorized=False,
        decision_type=DecisionType.BLOCK,
        priority=DecisionPriority.HIGH,
        rationale=rationale,
        policy_compliant=True,
    )

    unauthorized_request = DecisionRequest(
        policy_evaluation_id="policy-eval-unauthorized",
        subject="entity-unauthorized",
        requested_type=DecisionType.BLOCK,
        requested_priority=DecisionPriority.HIGH,
    )

    unauthorized_decision = engine.build(
        decision_id="decision-unauthorized",
        request=unauthorized_request,
        evaluation=unauthorized_evaluation,
    )

    assert (
        unauthorized_decision.status
        == DecisionStatus.BLOCKED
    ), (
        "An unauthorized Policy evaluation must resolve to BLOCKED."
    )

    assert (
        unauthorized_decision.actionable is False
    ), (
        "An unauthorized Decision must never be actionable."
    )

    print("[PASS] Unauthorized lifecycle")

    # ========================================================================
    # 30. Non-compliant lifecycle
    # ========================================================================

    non_compliant_evaluation = DecisionEvaluation(
        policy_evaluation_id="policy-eval-noncompliant",
        authorized=False,
        decision_type=DecisionType.BLOCK,
        priority=DecisionPriority.CRITICAL,
        rationale=rationale,
        policy_compliant=False,
    )

    non_compliant_request = DecisionRequest(
        policy_evaluation_id="policy-eval-noncompliant",
        subject="entity-noncompliant",
        requested_type=DecisionType.BLOCK,
        requested_priority=DecisionPriority.CRITICAL,
    )

    non_compliant_decision = engine.build(
        decision_id="decision-noncompliant",
        request=non_compliant_request,
        evaluation=non_compliant_evaluation,
    )

    assert (
        non_compliant_decision.status
        == DecisionStatus.REJECTED
    ), (
        "A non-policy-compliant evaluation must resolve to REJECTED."
    )

    assert (
        non_compliant_decision.actionable is False
    ), (
        "A non-policy-compliant Decision must never be actionable."
    )

    print("[PASS] Policy compliance lifecycle")

    # ========================================================================
    # 31. Deferred lifecycle
    # ========================================================================

    defer_evaluation = DecisionEvaluation(
        policy_evaluation_id="policy-eval-defer",
        authorized=True,
        decision_type=DecisionType.DEFER,
        priority=DecisionPriority.MEDIUM,
        rationale=rationale,
        policy_compliant=True,
    )

    defer_request = DecisionRequest(
        policy_evaluation_id="policy-eval-defer",
        subject="entity-defer",
        requested_type=DecisionType.DEFER,
        requested_priority=DecisionPriority.MEDIUM,
    )

    defer_decision = engine.build(
        decision_id="decision-defer",
        request=defer_request,
        evaluation=defer_evaluation,
    )

    assert (
        defer_decision.status
        == DecisionStatus.DEFERRED
    ), (
        "A DEFER Policy-derived intent must resolve to DEFERRED."
    )

    assert (
        defer_decision.actionable is False
    ), (
        "A DEFERRED Decision must never be actionable."
    )

    print("[PASS] Deferred lifecycle")

    # ========================================================================
    # 32. DEFER cannot become APPROVED
    # ========================================================================

    assert (
        defer_decision.status
        != DecisionStatus.APPROVED
    ), (
        "DecisionEngine must never convert a DEFER intent into APPROVED."
    )

    print("[PASS] Deferred approval boundary")

    # ========================================================================
    # 33. Explicit status resolution
    # ========================================================================

    assert (
        engine.resolve_status(evaluation)
        == DecisionStatus.APPROVED
    ), (
        "resolve_status() must return APPROVED for a compliant authorized "
        "non-DEFER evaluation."
    )

    assert (
        engine.resolve_status(unauthorized_evaluation)
        == DecisionStatus.BLOCKED
    ), (
        "resolve_status() must return BLOCKED for an unauthorized "
        "evaluation."
    )

    assert (
        engine.resolve_status(non_compliant_evaluation)
        == DecisionStatus.REJECTED
    ), (
        "resolve_status() must return REJECTED for a non-compliant "
        "evaluation."
    )

    assert (
        engine.resolve_status(defer_evaluation)
        == DecisionStatus.DEFERRED
    ), (
        "resolve_status() must return DEFERRED for a DEFER intent."
    )

    print("[PASS] Lifecycle resolution API")

    # ========================================================================
    # 34. Expiration handling
    # ========================================================================

    expired_created_at = (
        evaluation.evaluated_at
        - timedelta(minutes=10)
    )

    expired_request = DecisionRequest(
        policy_evaluation_id="policy-eval-expired",
        subject="entity-expired",
        requested_type=DecisionType.CONTAIN,
        requested_priority=DecisionPriority.HIGH,
    )

    expired_evaluation = DecisionEvaluation(
        policy_evaluation_id="policy-eval-expired",
        authorized=True,
        decision_type=DecisionType.CONTAIN,
        priority=DecisionPriority.HIGH,
        rationale=rationale,
        policy_compliant=True,
        evaluated_at=expired_created_at,
    )

    expired_decision = engine.build(
        decision_id="decision-expired",
        request=expired_request,
        evaluation=expired_evaluation,
        expires_at=(
            expired_created_at
            + timedelta(minutes=1)
        ),
    )

    assert (
        expired_decision.status
        == DecisionStatus.APPROVED
    ), (
        "Expiration is temporal validity, not Policy authorization. "
        "Construction may still produce an approved Decision."
    )

    assert (
        expired_decision.actionable is False
    ), (
        "An expired Decision must not be actionable."
    )

    print("[PASS] Expiration boundary")

    # ========================================================================
    # 35. Policy evaluation mismatch
    # ========================================================================

    mismatch_request = DecisionRequest(
        policy_evaluation_id="policy-eval-A",
        subject="entity-mismatch",
        requested_type=DecisionType.CONTAIN,
        requested_priority=DecisionPriority.HIGH,
    )

    mismatch_failed = False

    try:
        engine.build(
            decision_id="decision-mismatch",
            request=mismatch_request,
            evaluation=evaluation,
        )
    except DecisionConsistencyError:
        mismatch_failed = True

    assert mismatch_failed is True, (
        "A request with a different Policy evaluation ID must be rejected."
    )

    print("[PASS] Policy evaluation consistency")

    # ========================================================================
    # 36. Policy reference mismatch
    # ========================================================================

    policy_reference_request = DecisionRequest(
        policy_evaluation_id="policy-eval-engine-001",
        subject="entity-policy-ref",
        requested_type=DecisionType.CONTAIN,
        requested_priority=DecisionPriority.HIGH,
        policy_reference="policy.other.999",
    )

    policy_reference_failed = False

    try:
        engine.build(
            decision_id="decision-policy-ref-mismatch",
            request=policy_reference_request,
            evaluation=evaluation,
        )
    except DecisionConsistencyError:
        policy_reference_failed = True

    assert policy_reference_failed is True, (
        "Conflicting Policy references must be rejected explicitly."
    )

    print("[PASS] Policy reference consistency")

    # ========================================================================
    # 37. Prediction reference mismatch
    # ========================================================================

    prediction_reference_request = DecisionRequest(
        policy_evaluation_id="policy-eval-engine-001",
        subject="entity-prediction-ref",
        requested_type=DecisionType.CONTAIN,
        requested_priority=DecisionPriority.HIGH,
        prediction_reference="prediction.other.999",
    )

    prediction_reference_failed = False

    try:
        engine.build(
            decision_id="decision-prediction-ref-mismatch",
            request=prediction_reference_request,
            evaluation=evaluation,
        )
    except DecisionConsistencyError:
        prediction_reference_failed = True

    assert prediction_reference_failed is True, (
        "Conflicting Prediction provenance must be rejected explicitly."
    )

    print("[PASS] Prediction provenance consistency")

    # ========================================================================
    # 38. Invalid request type
    # ========================================================================

    invalid_request_failed = False

    try:
        engine.build(
            decision_id="decision-invalid-request",
            request="not-a-request",  # type: ignore[arg-type]
            evaluation=evaluation,
        )
    except DecisionInputError:
        invalid_request_failed = True

    assert invalid_request_failed is True, (
        "DecisionEngine must reject non-DecisionRequest inputs explicitly."
    )

    print("[PASS] Input type classification")

    # ========================================================================
    # 39. Invalid evaluation type
    # ========================================================================

    invalid_evaluation_failed = False

    try:
        engine.build(
            decision_id="decision-invalid-evaluation",
            request=request,
            evaluation="not-an-evaluation",  # type: ignore[arg-type]
        )
    except DecisionInputError:
        invalid_evaluation_failed = True

    assert invalid_evaluation_failed is True, (
        "DecisionEngine must reject non-DecisionEvaluation inputs explicitly."
    )

    print("[PASS] Evaluation type classification")

    # ========================================================================
    # 40. Invalid decision ID
    # ========================================================================

    invalid_id_failed = False

    try:
        engine.build(
            decision_id="",
            request=request,
            evaluation=evaluation,
        )
    except DecisionInputError:
        invalid_id_failed = True

    assert invalid_id_failed is True, (
        "DecisionEngine must reject an empty decision_id."
    )

    print("[PASS] Decision ID validation")

    # ========================================================================
    # 41. Reserved metadata protection
    # ========================================================================

    reserved_metadata_failed = False

    try:
        engine.build(
            decision_id="decision-reserved-metadata",
            request=request,
            evaluation=evaluation,
            metadata={
                "execution_enabled": True,
            },
        )
    except DecisionConsistencyError:
        reserved_metadata_failed = True

    assert reserved_metadata_failed is True, (
        "Caller metadata must not override protected engine architecture "
        "metadata."
    )

    print("[PASS] Metadata authority boundary")

    # ========================================================================
    # 42. Invalid metadata type
    # ========================================================================

    invalid_metadata_failed = False

    try:
        engine.build(
            decision_id="decision-invalid-metadata",
            request=request,
            evaluation=evaluation,
            metadata="invalid",  # type: ignore[arg-type]
        )
    except DecisionInputError:
        invalid_metadata_failed = True

    assert invalid_metadata_failed is True, (
        "DecisionEngine must reject non-mapping metadata explicitly."
    )

    print("[PASS] Metadata validation")

    # ========================================================================
    # 43. Serialization
    # ========================================================================

    serialized_decision = decision_to_dict(
        decision
    )

    assert isinstance(
        serialized_decision,
        dict,
    ), (
        "DecisionEngine output must remain serialization-safe."
    )

    assert (
        serialized_decision["decision_id"]
        == "decision-engine-001"
    ), (
        "Serialized Decision must preserve its identifier."
    )

    assert (
        serialized_decision["status"]
        == "approved"
    ), (
        "Serialized Decision must preserve lifecycle status."
    )

    assert (
        serialized_decision["decision_type"]
        == "contain"
    ), (
        "Serialized Decision must preserve Policy-derived decision type."
    )

    assert (
        serialized_decision["priority"]
        == "high"
    ), (
        "Serialized Decision must preserve Policy-derived priority."
    )

    print("[PASS] Serialization")

    # ========================================================================
    # 44. Deterministic semantic resolution
    # ========================================================================

    decision_a = engine.build(
        decision_id="deterministic-A",
        request=request,
        evaluation=evaluation,
    )

    decision_b = engine.build(
        decision_id="deterministic-B",
        request=request,
        evaluation=evaluation,
    )

    assert (
        decision_a.decision_type
        == decision_b.decision_type
    ), (
        "Identical inputs must resolve to the same Decision type."
    )

    assert (
        decision_a.priority
        == decision_b.priority
    ), (
        "Identical inputs must resolve to the same Decision priority."
    )

    assert (
        decision_a.status
        == decision_b.status
    ), (
        "Identical inputs must resolve to the same lifecycle status."
    )

    assert (
        decision_a.rationale
        == decision_b.rationale
    ), (
        "Identical inputs must preserve the same rationale."
    )

    assert (
        decision_a.constraints
        == decision_b.constraints
    ), (
        "Identical inputs must preserve the same constraints."
    )

    print("[PASS] Deterministic resolution")

    # ========================================================================
    # 45. Contract validation of final output
    # ========================================================================

    try:
        validate_decision(
            decision
        )
    except (TypeError, ValueError) as exc:
        raise AssertionError(
            "DecisionEngine output must satisfy the canonical Decision "
            "contract."
        ) from exc

    print("[PASS] Final contract validation")

    # ========================================================================
    # 46. Architectural chain
    # ========================================================================

    assert (
        ARCHITECTURAL_CHAIN
        == (
            "prediction",
            "policy",
            "decision",
            "response",
        )
    ), (
        "DecisionEngine must preserve the canonical ADIE architectural chain."
    )

    assert (
        ARCHITECTURAL_CHAIN.index("policy")
        < ARCHITECTURAL_CHAIN.index("decision")
    ), (
        "Policy must precede Decision in the ADIE architecture."
    )

    assert (
        ARCHITECTURAL_CHAIN.index("decision")
        < ARCHITECTURAL_CHAIN.index("response")
    ), (
        "Decision must precede Response in the ADIE architecture."
    )

    print("[PASS] Architectural chain")

    # ========================================================================
    # 47. Semantic roles
    # ========================================================================

    assert (
        PREDICTION_SEMANTIC_ROLE
        == "future_belief"
    ), (
        "Prediction semantic role must remain future_belief."
    )

    assert (
        POLICY_SEMANTIC_ROLE
        == "constraint_permission_evaluation"
    ), (
        "Policy semantic role must remain constraint_permission_evaluation."
    )

    assert (
        DECISION_SEMANTIC_ROLE
        == "defensible_control_plane_intent"
    ), (
        "Decision semantic role must remain defensible_control_plane_intent."
    )

    assert (
        RESPONSE_SEMANTIC_ROLE
        == "execution"
    ), (
        "Response semantic role must remain execution."
    )

    print("[PASS] ADIE semantic roles")

    # ========================================================================
    # 48. No policy re-evaluation
    # ========================================================================

    assert (
        engine_metadata["policy_re_evaluation"] is False
    ), (
        "DecisionEngine must construct from Policy output and must not "
        "re-evaluate Policy."
    )

    print("[PASS] No Policy re-evaluation")

    # ========================================================================
    # 49. No prediction invocation
    # ========================================================================

    assert (
        engine_metadata["prediction_execution"] is False
    ), (
        "DecisionEngine must not invoke or execute Prediction."
    )

    print("[PASS] No Prediction invocation")

    # ========================================================================
    # 50. No response invocation
    # ========================================================================

    assert (
        engine_metadata["response_execution"] is False
    ), (
        "DecisionEngine must not invoke Response execution."
    )

    print("[PASS] No Response invocation")

    # ========================================================================
    # 51. Domain isolation
    # ========================================================================

    module_globals = globals()

    forbidden_names = (
        "DashboardAPI",
        "DashboardService",
        "Detector",
        "ModelManager",
        "TrainingService",
        "PolicyEngine",
        "PredictionEngine",
        "ResponseExecutor",
        "ShellExecutor",
        "subprocess",
        "requests",
        "socket",
        "os",
        "pathlib",
    )

    for name in forbidden_names:
        assert name not in module_globals, (
            "DecisionEngine must not directly depend on "
            f"{name}."
        )

    print("[PASS] Domain isolation")

    # ========================================================================
    # 52. No execution API
    # ========================================================================

    forbidden_engine_methods = (
        "execute",
        "run_command",
        "execute_action",
        "perform_action",
        "network_call",
        "shell",
    )

    for method_name in forbidden_engine_methods:
        assert not hasattr(
            engine,
            method_name,
        ), (
            "DecisionEngine must not expose an execution method: "
            f"{method_name}."
        )

    print("[PASS] Execution API isolation")

    # ========================================================================
    # 53. Engine metadata defensive copy
    # ========================================================================

    metadata_copy = engine.metadata

    metadata_copy["execution_enabled"] = True

    fresh_metadata = engine.metadata

    assert (
        fresh_metadata["execution_enabled"] is False
    ), (
        "Mutating returned engine metadata must not mutate the "
        "canonical metadata contract."
    )

    print("[PASS] Metadata immutability")

    # ========================================================================
    # 54. Final ADIE invariant
    # ========================================================================

    assert (
        decision.policy_evaluation_id
        == evaluation.policy_evaluation_id
    ), (
        "Every Decision must retain its Policy evaluation provenance."
    )

    assert (
        decision.prediction_reference
        == evaluation.prediction_reference
    ), (
        "Prediction provenance must remain traceable through Decision."
    )

    assert (
        decision.constraints
        == evaluation.constraints
    ), (
        "Policy constraints must propagate unchanged into Decision."
    )

    assert (
        decision.rationale
        == evaluation.rationale
    ), (
        "Policy-derived rationale must propagate unchanged into Decision."
    )

    assert (
        decision.actionable is True
    ), (
        "The canonical approved Decision must be actionable at the "
        "Response boundary."
    )

    assert (
        engine_metadata["execution_enabled"] is False
    ), (
        "Actionability must never imply execution capability."
    )

    print("[PASS] Final ADIE semantic invariant")

    return True


# ============================================================================
# Module execution
# ============================================================================


if __name__ == "__main__":
    print("=" * 70)
    print(
        "EnterpriseGuard - ADIE Decision Engine Self-Test"
    )
    print("=" * 70)

    try:
        self_test()

        print("=" * 70)
        print("SELF-TEST PASSED")
        print("=" * 70)

    except AssertionError as exc:
        print("[FAIL] Assertion error:")
        print(exc)
        raise SystemExit(1)

    except DecisionEngineError as exc:
        print("[FAIL] Decision engine error:")
        print(exc)
        raise SystemExit(1)

    except Exception as exc:
        print("[FAIL] Unexpected error:")
        print(exc)
        raise SystemExit(1)