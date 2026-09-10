import hashlib
import json
import os
import re
import sys
import tempfile
from collections import Counter, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.time_utils import utc_now

from tools.time_utils import utc_now

class GovernanceRuleGenerator:
    """Create proposal-only governance rules from repository observations."""

    def _utc_now(self) -> str:
        return utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")

    def _normalize(self, text: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()

    def _read_json_or_empty(self, path: Path):
        if not path.exists():
            return []
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return []
        if isinstance(payload, dict):
            return payload.get("activities", []) if isinstance(payload.get("activities", []), list) else []
        if isinstance(payload, list):
            return payload
        return []

    def _read_activity_entries(self, activity_log_path: Path, limit: int = 100) -> list[dict]:
        entries = self._read_json_or_empty(activity_log_path)
        if not entries:
            return []
        filtered = [entry for entry in entries if isinstance(entry, dict)]
        return filtered[-limit:]

    def analyze_recent_activity(self, activity_log_path: Path, limit: int = 100) -> list[str]:
        """Read and summarize recent activity types and anomalies."""
        entries = self._read_activity_entries(activity_log_path, limit)
        if not entries:
            return ["No recent activity entries were available for governance review."]

        counts = Counter()
        for entry in entries:
            activity_type = str(entry.get("activity_type") or entry.get("event") or "unknown").strip()
            if activity_type:
                counts[activity_type] += 1

        observations: list[str] = []
        for activity_type, count in counts.most_common(5):
            if count > 1:
                observations.append(
                    f"Recurring activity type '{activity_type}' appeared {count} times in the latest {len(entries)} activity records."
                )

        if not observations:
            observations.append(
                "Recent activity was sparse and did not show repeated operational spikes; maintain routine governance review."
            )

        return observations[:5]

    def analyze_error_log(self, errors_log_path: Path, limit: int = 200) -> list[str]:
        """Read error-tail evidence and identify recurring issue classes."""
        if not errors_log_path.exists():
            return ["No errors log was available for analysis."]

        tail: deque[str] = deque(maxlen=limit)
        with errors_log_path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                tail.append(line.rstrip())

        if not tail:
            return ["The errors log was empty; no recurring error patterns were detected."]

        counts = Counter()
        for line in tail:
            for error_name in [
                "AttributeError",
                "ModuleNotFoundError",
                "SyntaxError",
                "Traceback",
                "PermissionError",
                "TypeError",
                "ValueError",
            ]:
                if error_name in line:
                    counts[error_name] += 1

        observations: list[str] = []
        for name, count in counts.most_common(5):
            if count:
                observations.append(f"Recurring error pattern '{name}' appeared {count} times in the recent error log tail.")

        if not observations:
            observations.append("Recent errors did not show repeated failure signatures; continue normal governance review.")

        return observations[:5]

    def analyze_decision_log(self, decision_log_path: Path) -> list[str]:
        """Review the decision log for governance coverage gaps."""
        if not decision_log_path.exists():
            return ["Decision log is missing; governance coverage should be re-established before policy activation."]

        text = decision_log_path.read_text(encoding="utf-8", errors="replace")
        observations: list[str] = []
        if re.search(r"DC-\d+.*approval|approval.*DC-\d+", text, flags=re.IGNORECASE):
            observations.append("The decision log already references approval and review workflows; governance proposals should align with that pattern.")
        else:
            observations.append("No explicit approval gate text was found in the recent decision log; a review-approval rule may be warranted.")

        if re.search(r"protected|adie|intelligence|safety|lockdown", text, flags=re.IGNORECASE):
            observations.append("The project already includes protected-area safety concepts; governance proposals should preserve non-invasive review-only enforcement.")
        else:
            observations.append("The decision log does not explicitly call out protected-area policy gaps; a policy review can address this risk.")

        return observations[:5]

    def _proposal_seed(self, title: str, description: str) -> str:
        return f"{title}|{description}"

    def generate_proposals(self, observations: list[str]) -> list[dict]:
        """Build proposal records that are review-only and never auto-activated."""
        if not observations:
            observations = ["No repository evidence was available; governance review should remain manual and owner-approved."]

        existing = self._load_existing_proposals(Path(__file__).resolve().parent)
        proposals: list[dict] = []
        keyword_map = {
            "repeat": "Operational Review and Triage",
            "error": "Error Review and Response",
            "approval": "Owner Approval Gate",
            "protected": "Protected Area Review",
            "governance": "Governance Coverage Review",
            "activity": "Activity Pattern Review",
        }

        for observation in observations:
            lowered = observation.lower()
            for keyword, title in keyword_map.items():
                if keyword in lowered:
                    description = (
                        "Review repository telemetry and corrective actions before any policy or automation change is approved. "
                        "The project owner must confirm the scope, expected safeguards, and rollback path before activation."
                    )
                    rationale = (
                        f"Evidence from repository analysis indicates a governance need related to '{observation}'. "
                        "The rule is intended to support reviewability and traceability without automatically enforcing controls."
                    )
                    priority = "high" if any(token in lowered for token in ["error", "approval", "protected", "missing"]) else "medium"
                    proposal = {
                        "proposal_id": hashlib.sha256(self._proposal_seed(title, description).encode("utf-8")).hexdigest()[:16],
                        "title": title,
                        "description": description,
                        "rationale": rationale,
                        "priority": priority,
                        "status": "PROPOSED",
                        "requires_owner_approval": True,
                    }
                    proposals.append(proposal)
                    break

        if not proposals:
            proposals.append(
                {
                    "proposal_id": hashlib.sha256(b"Governance Coverage Review|Review repository evidence before any policy change.").hexdigest()[:16],
                    "title": "Governance Coverage Review",
                    "description": "Review repository telemetry, error signals, and decision traceability before any policy or automation change is approved by the owner.",
                    "rationale": "Repository evidence suggests a need for explicit review and owner confirmation when governance changes are considered.",
                    "priority": "medium",
                    "status": "PROPOSED",
                    "requires_owner_approval": True,
                }
            )

        proposals = self.deduplicate_proposals(proposals, existing)
        return sorted(proposals, key=lambda item: (0 if item.get("priority") == "high" else 1 if item.get("priority") == "medium" else 2, str(item.get("title"))))[:10]

    def _load_existing_proposals(self, tools_dir: Path) -> list[dict]:
        proposals: list[dict] = []
        if not tools_dir.exists():
            return proposals
        for path in sorted(tools_dir.glob("governance_proposals_*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                continue
            if isinstance(payload, dict):
                nested = payload.get("proposals", []) if isinstance(payload.get("proposals", []), list) else []
                proposals.extend(nested)
            elif isinstance(payload, list):
                proposals.extend(payload)
        return [item for item in proposals if isinstance(item, dict)]

    def deduplicate_proposals(self, proposals: list[dict], existing_proposals: list[dict]) -> list[dict]:
        """Remove proposals that duplicate an already seen title or description."""
        seen: set[str] = set()
        for item in existing_proposals:
            if not isinstance(item, dict):
                continue
            title = self._normalize(str(item.get("title", "")))
            description = self._normalize(str(item.get("description", "")))
            if title:
                seen.add(title)
            if description:
                seen.add(description)

        unique: list[dict] = []
        for proposal in proposals:
            if not isinstance(proposal, dict):
                continue
            normalized_title = self._normalize(str(proposal.get("title", "")))
            normalized_description = self._normalize(str(proposal.get("description", "")))
            if normalized_title in seen or normalized_description in seen:
                continue
            unique.append(proposal)
            seen.add(normalized_title)
            seen.add(normalized_description)
        return unique

    def save_proposals(self, proposals: list[dict], output_path: Path) -> Path:
        """Write proposal JSON atomically to the specified tool path."""
        output_path.parent.mkdir(exist_ok=True, parents=True)
        payload = {"generated_at": self._utc_now(), "proposals": proposals}
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(output_path.parent), delete=False) as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            temp_path = Path(handle.name)
        os.replace(temp_path, output_path)
        return output_path

if __name__ == "__main__":
    generator = GovernanceRuleGenerator()
    proposals = generator.generate_proposals([
        "Recurring activity type 'rag_run' appeared 3 times in the latest activity records.",
        "Recurring error pattern 'AttributeError' appeared 2 times in the recent error log tail.",
        "No explicit approval gate text was found in the recent decision log.",
    ])
    print(json.dumps({"proposals": proposals}, indent=2, ensure_ascii=False))