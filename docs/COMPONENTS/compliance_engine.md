# Component: compliance_engine.py

**Path:** `tools/compliance_engine.py`
**Purpose:** Rules-based compliance engine for AI decision events.
**Status:** Working (used by aaac_cli.py)

---

## What It Does

Evaluates each AI agent event against a rules-based policy.
Supports priorities, AND/OR logic, numeric thresholds, regex,
and default-deny behavior.

Non-compliant events are flagged with a reason and stored.

## Inputs

- event (dict): the AI decision event to evaluate
- rules (list): from compliance_policy.json

## Outputs

- verdict (dict): {compliant: bool, reason: str, rule_matched: str}

## Key Functions

| Function | Purpose |
|----------|---------|
| load_policy() | Read compliance_policy.json |
| evaluate_event() | Apply rules to event |
| _matches_rule() | Check single rule |
| _evaluate_conditions() | AND/OR logic |
| _check_numeric() | Numeric threshold |
| _check_regex() | Regex pattern |

## Policy Structure (compliance_policy.json)

    {
      "rules": [
        {
          "id": "no_dangerous_commands",
          "priority": 1,
          "conditions": {
            "field": "action",
            "operator": "not_in",
            "values": ["rm -rf", "curl | bash"]
          },
          "verdict": "deny",
          "reason": "command_not_allowed"
        },
        {
          "id": "max_latency",
          "priority": 2,
          "conditions": {
            "field": "latency_ms",
            "operator": "gt",
            "value": 5000
          },
          "verdict": "flag",
          "reason": "high_latency"
        }
      ],
      "default": "deny"
    }

## Operators Supported

| Operator | Meaning |
|----------|---------|
| in | value in list |
| not_in | value not in list |
| eq / ne | equal / not equal |
| gt / gte | greater than / >= |
| lt / lte | less than / <= |
| regex | matches regex |
| and | all conditions |
| or | any condition |

## Security

- Default behavior: DENY (fail-secure)
- Rule priorities respected (highest first)
- Regex patterns escaped and validated
- No dynamic code execution
- Non-compliant events flagged, not silently dropped

## Failure Handling

| Scenario | Behavior |
|----------|----------|
| No policy file | Default deny all |
| Malformed rule | Skip rule, log warning |
| Unknown operator | Skip rule, log warning |
| No rule matches | Apply default verdict |

## Tests

- Tested via aaac_cli.py integration
- Manual tests: allowed command passes, forbidden denied, high-risk transfer denied

## Used By

- tools/aaac_cli.py (compliance enrichment before storage)

**End of Component Doc**
