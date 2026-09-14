import json
from tools.compliance_engine import evaluate_event, enrich_event_with_compliance

# حدث ممتثل
event_ok = {
    "timestamp": "2026-09-07T09:00:00Z",
    "agent_id": "agent-100",
    "trace_id": "t1",
    "command": "check_balance",
    "actor_type": "agent",
    "latency_ms": 1200
}

# حدث محظور (أمر خطير)
event_bad_command = {
    "timestamp": "2026-09-07T09:00:00Z",
    "agent_id": "agent-100",
    "trace_id": "t2",
    "command": "hack_system",
    "actor_type": "agent",
    "latency_ms": 100
}

# حدث تجاوز حد التحويل
event_high_amount = {
    "timestamp": "2026-09-07T09:00:00Z",
    "agent_id": "agent-100",
    "trace_id": "t3",
    "command": "transfer_funds",
    "actor_type": "agent",
    "latency_ms": 100,
    "amount": 250000
}

print("OK event:", evaluate_event(event_ok))
print("Bad command:", evaluate_event(event_bad_command))
print("High amount:", evaluate_event(event_high_amount))

print("Enriched bad command:", enrich_event_with_compliance(event_bad_command))
