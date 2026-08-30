"""
EnterpriseGuard ADIE
Adaptive Defense Intelligence Engine
====================================

Canonical Public API Package Initialization.
"""

from __future__ import annotations

from typing import Any

# ============================================================================
# Imports from Prediction Domain
# ============================================================================
from .prediction import (
    MODULE_NAME as PREDICTION_MODULE_NAME,
    MODULE_VERSION as PREDICTION_MODULE_VERSION,
    DEFAULT_PROBABILITY_THRESHOLD,
    DEFAULT_PREDICTION_HORIZON_SECONDS,
    MAX_PREDICTION_HORIZON_SECONDS,
    PredictionError,
    PredictionValidationError,
    PredictionContractError,
    PredictionType,
    PredictionStatus,
    PredictionResult,
    PredictionBuilder,
    Predictor,
    BaselinePredictor,
    PredictionService,
    get_prediction_service,
    self_test as prediction_self_test,
)

# ============================================================================
# Imports from Policy Domain
# ============================================================================
from .policy import (
    MODULE_NAME as POLICY_MODULE_NAME,
    MODULE_VERSION as POLICY_MODULE_VERSION,
    MIN_SCORE,
    MAX_SCORE,
    PolicyError,
    PolicyValidationError,
    PolicyEvaluationError,
    PolicyIntent,
    PolicyLifecycle,
    PolicyConfig,
    PolicyEvidence,
    PolicyEvaluation,
    ADIEPolicy,
    get_policy,
    self_test as policy_self_test,
)

# ============================================================================
# Imports from Decision Domain
# ============================================================================
from .decision import (
    MODULE_NAME as DECISION_MODULE_NAME,
    MODULE_VERSION as DECISION_MODULE_VERSION,
    DecisionError,
    DecisionValidationError,
    DecisionContractError,
    DecisionIntent,
    DecisionLifecycle,
    DecisionEvidence,
    DecisionContract,
    DecisionEngine,
    get_decision_engine,
)

# ============================================================================
# Package Metadata & Combined Self-Test
# ============================================================================
MODULE_NAME = "enterpriseguard.adie"
MODULE_VERSION = "2.0.0"


def self_test() -> dict[str, Any]:
    """Run self-tests across all ADIE sub-modules."""
    pred_res = prediction_self_test()
    policy_res = policy_self_test()
    
    # Decision engine self_test
    decision_res = DecisionEngine().self_test()

    passed = all(
        [
            pred_res.get("passed", False),
            policy_res.get("passed", False),
            decision_res.get("passed", False),
        ]
    )

    return {
        "passed": passed,
        "module": MODULE_NAME,
        "version": MODULE_VERSION,
        "prediction": pred_res,
        "policy": policy_res,
        "decision": decision_res,
        "executes_security_actions": False,
    }


# ============================================================================
# Public API Exports (__all__)
# ============================================================================
__all__ = [
    # Package Info & Tests
    "MODULE_NAME",
    "MODULE_VERSION",
    "self_test",
    
    # Prediction Exports
    "PREDICTION_MODULE_NAME",
    "PREDICTION_MODULE_VERSION",
    "DEFAULT_PROBABILITY_THRESHOLD",
    "DEFAULT_PREDICTION_HORIZON_SECONDS",
    "MAX_PREDICTION_HORIZON_SECONDS",
    "PredictionError",
    "PredictionValidationError",
    "PredictionContractError",
    "PredictionType",
    "PredictionStatus",
    "PredictionResult",
    "PredictionBuilder",
    "Predictor",
    "BaselinePredictor",
    "PredictionService",
    "get_prediction_service",
    "prediction_self_test",
    
    # Policy Exports
    "POLICY_MODULE_NAME",
    "POLICY_MODULE_VERSION",
    "MIN_SCORE",
    "MAX_SCORE",
    "PolicyError",
    "PolicyValidationError",
    "PolicyEvaluationError",
    "PolicyIntent",
    "PolicyLifecycle",
    "PolicyConfig",
    "PolicyEvidence",
    "PolicyEvaluation",
    "ADIEPolicy",
    "get_policy",
    "policy_self_test",
    
    # Decision Exports
    "DECISION_MODULE_NAME",
    "DECISION_MODULE_VERSION",
    "DecisionError",
    "DecisionValidationError",
    "DecisionContractError",
    "DecisionIntent",
    "DecisionLifecycle",
    "DecisionEvidence",
    "DecisionContract",
    "DecisionEngine",
    "get_decision_engine",
]
