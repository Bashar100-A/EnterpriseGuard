# Internal Attack Simulator — Architectural Draft

Status: DRAFT — NOT FOR IMPLEMENTATION

Date: 2026-08-31T10:11:58Z

## 1. Purpose

This simulator is a conceptual future capability intended to emulate internal attack patterns in a controlled and non-operational manner so that isolation, detection, and response readiness can be reviewed without disturbing the live production surface. It is designed to help teams reason about how adversarial behaviors might be observed, classified, and limited before any stronger control posture is applied. The design intentionally avoids touching ADIE core and keeps all planning activity in the governed tooling layer rather than inside protected runtime logic. The goal is to improve detection discipline, prove the safety of control boundaries, and provide a reviewable model for how internal risk might be understood. For example, a team could examine a hypothetical scenario in which a compromised internal process begins generating irregular access patterns and observe how the system would escalate review without acting destructively.

## 2. Scope

This document is a draft only and is not a specification for active implementation. It exists to frame a future design discussion, not to authorize code changes, deployment steps, or operational actions. No implementation is permitted without separate owner approval, and no engineering work may begin on the basis of this draft alone. The scope is limited to architectural review, governance alignment, and risk framing for future planning. The document is explicitly designed to remain outside the protected runtime areas and to avoid exposing internal details of the protected core. A practical scenario is a governance review in which the organization discusses the difference between a passive simulation and a real enforcement decision before any further action is authorized.

## 3. Design principles

The first design principle is separation of simulation and production, which ensures that attacker models remain distinct from real operational flow and impossible to confuse with live runtime behavior. The second principle is read-only observation, which means the simulator should learn from signals and scenarios without pushing changes into protected logic or sensitive data paths. The third principle is fail-closed reasoning, which favors safety when evidence is incomplete, stale, or contradictory. The fourth principle is gradual trust, meaning a system should increase scrutiny and limit exposure in measured steps rather than by abrupt interruption. A practical example is a staff review in which a suspicious pattern is modeled in the simulation environment first, and only then does the review consider whether a more conservative posture is justified.

## 4. Proposed components

### (a) Attack Scenario Bank

The Attack Scenario Bank would hold passive descriptions of common internal attack patterns, misuse sequences, and trust-erosion behaviors that are useful for review and readiness testing. It would catalog likely entry points, attacker behaviors, and escalation patterns without attempting to create live execution paths. The scenario bank is intended to be descriptive, explainable, and governance-friendly so reviewers can understand why a pattern matters without needing operational access to sensitive internals. A theoretical example is a malicious internal workflow that tries to accumulate permissions over time through repeated low-signal actions, creating a pattern that is easy to detect once isolated in a simulation environment.

### (b) Attack Emitter

The Attack Emitter is a future component that would represent the external stimulus side of the simulation model rather than the protected runtime itself. It would be responsible for producing the conceptual scenarios that are later observed, recorded, and classified by the rest of the design. This component would remain intentionally separate from real execution surfaces so that the simulation remains clearly labeled and non-destructive. A theoretical example is a controlled scenario in which the emitter stages a sequence of suspicious internal actions that are designed to test whether detection and response logic can recognize the early warning signals without acting on live data.

### (c) Detection Observer

The Detection Observer would function as a passive analyst that watches the system under review and notes how simulated behaviors appear under the project’s governance and control model. It would record whether suspicious patterns are recognized, delayed, or misclassified, and would help determine whether current detection assumptions remain sound. This component would avoid taking action on its own and would purposely remain a review and learning layer, not an execution engine. An example is a scenario in which a repeated credential anomaly is visible to the observer but does not yet meet the threshold for intervention, prompting the system to increase surveillance instead of forcing a hard stop.

### (d) Evaluation and Reporting

The Evaluation and Reporting component would summarize the result of each simulation in a human-readable review format that focuses on detection quality, response alignment, and residual risk. It would compare expected signals with observed signals and highlight whether the control model seems sufficiently conservative or whether more review is required. The reporting function would make the simulation useful for governance review and future design decisions without creating a hidden execution path. A theoretical example is a final report that shows the simulation detected a gradual privilege drift pattern early, recommended stronger observability, and exposed where response workflows could be improved before a real incident occurs.

## 5. Invariants

No direct execution should occur inside ADIE as part of the simulation design. No hidden writes should be introduced during scenario review, detection observation, or reporting. All simulated attacks must be clearly labeled as non-operational and isolated from production decision paths. No destructive actions should be permitted against real data, configuration, or service state. The design must also maintain a clear separation between observation, recommendation, and any future enforcement boundary so that the review process stays explainable and auditable. A practical example is a simulation that demonstrates abnormal access patterns without changing any live policy, record, or service behavior.

## 6. Future triggers

Future triggers are conceptual only and are intended to frame how a more advanced simulation capability might be evaluated, not to define implementation details. They may include repeated anomalous behavior, suspicious privilege drift, unusual access timing, inconsistent correlation signals, or a pattern that suggests an actor is learning the control model. They may also include cases where the organization wants to review what happens when trust degrades gradually over time rather than through a single event. This section intentionally avoids implementation details and instead focuses on the type of conditions that would warrant deeper review under a later governance milestone. An example is a review scenario in which a subsystem begins to show low-confidence yet repeated deviations from its expected activity baseline, prompting a governance conversation instead of direct action.

## 7. Open questions

The first question is whether the owner wants this capability to remain advisory and review-only, or whether a separate external enforcement boundary should eventually be considered. The second question is how much evidence should be required before a scenario moves from passive analysis to a higher-risk review tier. The third question is which telemetry sources are trustworthy enough to support a simulation baseline without introducing false confidence. The fourth question is how human approval should be integrated into any future escalation path when a scenario reaches a threshold of concern. The fifth question is whether the system should express trust states as discrete tiers or a more continuous model that can be reviewed more easily by governance stakeholders. A broader example is a future architecture review in which the owner decides whether this simulation should remain a planning tool or become part of a broader external control framework.

## 8. Acceptance criteria

Before any future implementation can start, the architecture must clearly separate simulation activity from real operational control flows and must demonstrate that protected runtime logic is outside the design scope. A future implementation must preserve the rule that no destructive action is permitted against live data or configuration, and any scenario must remain clearly labeled as simulated rather than real. The design must include reviewable evidence for how a suspicious pattern is observed, classified, and reported, and it must define a governance gate for any transition toward stronger controls. The design must also show how the system remains non-invasive when evidence is incomplete or ambiguous, which reduces the risk of overreaction. A practical example is a prospective milestone in which the owner approves the draft, asks for a real specification, and requires review of all scenario boundaries before any further implementation begins.
