#!/usr/bin/env python3
"""Advanced compliance rule engine for AAAC events."""

import os
import sys
import json
import re
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_POLICY_PATH = ROOT / "tools" / "compliance_policy.json"


def load_policy(policy_path: Path = DEFAULT_POLICY_PATH) -> dict:
    """Load compliance policy from JSON file."""
    if not policy_path.exists():
        return {}
    try:
        with open(policy_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def _field_exists(event: dict, field: str) -> bool:
    """Check if field exists and is not None or empty string."""
    return field in event and event[field] not in (None, "")


def _get_value(event: dict, field: str):
    """Get value from event, supporting nested fields with dot notation."""
    if "." in field:
        parts = field.split(".")
        value = event
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        return value
    return event.get(field)


def _evaluate_condition(event: dict, condition: dict) -> bool:
    """Evaluate a single condition."""
    field = condition.get("field")
    operator = condition.get("operator")
    value = condition.get("value")

    if operator == "exists":
        return _field_exists(event, field)

    actual = _get_value(event, field)

    if operator == "==":
        return actual == value
    elif operator == "!=":
        return actual != value
    elif operator == ">":
        if actual is None or value is None:
            return False
        try:
            return float(actual) > float(value)
        except (ValueError, TypeError):
            return False
    elif operator == "<":
        if actual is None or value is None:
            return False
        try:
            return float(actual) < float(value)
        except (ValueError, TypeError):
            return False
    elif operator == ">=":
        if actual is None or value is None:
            return False
        try:
            return float(actual) >= float(value)
        except (ValueError, TypeError):
            return False
    elif operator == "<=":
        if actual is None or value is None:
            return False
        try:
            return float(actual) <= float(value)
        except (ValueError, TypeError):
            return False
    elif operator == "in":
        if actual is None or not isinstance(value, list):
            return False
        return actual in value
    elif operator == "not_in":
        if actual is None or not isinstance(value, list):
            return False
        return actual not in value
    elif operator == "matches_regex":
        if actual is None or not isinstance(actual, str):
            return False
        try:
            return re.match(value, actual) is not None
        except re.error:
            return False
    elif operator == "contains":
        if actual is None:
            return False
        return value in str(actual)
    else:
        return False


def _evaluate_rule(event: dict, rule: dict) -> tuple[bool, str]:
    """Evaluate a single rule, return (passed, reason)."""
    conditions = rule.get("conditions", [])
    logic = rule.get("logic", "AND").upper()

    if not conditions:
        return True, "no_conditions"

    results = []
    for cond in conditions:
        results.append(_evaluate_condition(event, cond))

    if logic == "AND":
        passed = all(results)
    elif logic == "OR":
        passed = any(results)
    else:
        passed = all(results)

    if passed:
        return True, rule.get("name", "rule")
    else:
        return False, rule.get("name", "rule")


def evaluate_event(event: dict, policy: dict = None) -> tuple[bool, str]:
    """
    Evaluate an event against full policy.
    Returns (compliant, reason).
    """
    if policy is None:
        policy = load_policy()

    if not policy:
        return True, "no_policy"

    default_action = policy.get("default_action", "deny")
    rules = policy.get("rules", [])

    # Sort by priority (higher first)
    rules_sorted = sorted(rules, key=lambda r: r.get("priority", 0), reverse=True)

    deny_reason = None

    for rule in rules_sorted:
        passed, reason = _evaluate_rule(event, rule)
        rule_type = rule.get("type")

        if rule_type == "allow":
            if passed:
                return True, reason
        elif rule_type == "require":
            if not passed:
                return False, f"required_fields_missing:{reason}"
        elif rule_type == "deny" or rule_type == "deny_if_match":
            if passed:
                deny_reason = f"denied_by_rule:{reason}"
                # Continue checking higher priority rules, but deny is strong
                return False, deny_reason
        elif rule_type == "deny_if_exceed":
            if passed:
                return False, f"threshold_exceeded:{reason}"
        # other types can be added

    if deny_reason:
        return False, deny_reason

    if default_action == "deny":
        return False, "not_allowed_by_default"
    else:
        return True, "default_allow"


def enrich_event_with_compliance(event: dict, policy: dict = None) -> dict:
    """Add compliance_status and compliance_reason to event."""
    compliant, reason = evaluate_event(event, policy)
    event["compliance_status"] = "passed" if compliant else "failed"
    event["compliance_reason"] = reason
    return event
