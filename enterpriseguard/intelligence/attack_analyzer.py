import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.time_utils import utc_now


class AttackAnalyzer:
    """Lightweight analyzer for identifying suspicious activity and errors."""

    def __init__(self, root_path: Path):
        self.root_path = Path(root_path)

    def _safe_read_text(self, file_path: Path) -> str:
        try:
            return file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""

    def _iter_candidate_files(self):
        candidates = []
        for directory in (self.root_path / "logs", self.root_path / "tools", self.root_path / "src"):
            if not directory.exists() or not directory.is_dir():
                continue
            for path in sorted(directory.rglob("*")):
                if path.is_file() and path.suffix.lower() in {".log", ".json", ".jsonl", ".txt"}:
                    candidates.append(path)
        seen = set()
        unique_files = []
        for path in candidates:
            resolved = str(path.resolve())
            if resolved not in seen:
                seen.add(resolved)
                unique_files.append(path)
        return unique_files

    def analyze_errors(self, limit=200) -> list[dict]:
        findings = []
        patterns = [
            r"ERROR",
            r"CRITICAL",
            r"Exception",
            r"Traceback",
            r"DENIED",
            r"blocked",
            r"failed",
            r"attack",
            r"suspicious",
            r"malware",
            r"untrusted",
        ]
        combined_pattern = re.compile("|".join(patterns), re.IGNORECASE)

        for file_path in self._iter_candidate_files():
            text = self._safe_read_text(file_path)
            if not text:
                continue
            for line_number, line in enumerate(text.splitlines(), start=1):
                if not combined_pattern.search(line):
                    continue
                timestamp = self._extract_timestamp(line)
                findings.append(
                    {
                        "timestamp": timestamp,
                        "source": str(file_path),
                        "line": line_number,
                        "severity": self._severity_from_line(line),
                        "message": line.strip(),
                    }
                )
                if len(findings) >= limit:
                    return findings
        return findings

    def analyze_activity(self, limit=200) -> list[dict]:
        findings = []
        seen = set()
        source_counts = Counter()

        for file_path in self._iter_candidate_files():
            text = self._safe_read_text(file_path)
            if not text:
                continue
            if file_path.suffix.lower() == ".json":
                try:
                    payload = json.loads(text)
                    records = payload if isinstance(payload, list) else [payload]
                except json.JSONDecodeError:
                    records = []
            elif file_path.suffix.lower() == ".jsonl":
                records = []
                for raw_line in text.splitlines():
                    if not raw_line.strip():
                        continue
                    try:
                        records.append(json.loads(raw_line))
                    except json.JSONDecodeError:
                        continue
            else:
                records = []

            for item in records:
                if not isinstance(item, dict):
                    continue
                event_type = str(item.get("event_type") or item.get("activity_type") or item.get("type") or "activity")
                message = str(item.get("message") or item.get("summary") or item.get("details") or json.dumps(item, sort_keys=True)[:200])
                timestamp = item.get("timestamp") or item.get("time") or item.get("created_at") or item.get("when")
                source = str(item.get("source") or file_path)
                key = (event_type, source, message)
                if key in seen:
                    continue
                seen.add(key)
                source_counts[event_type] += 1
                findings.append(
                    {
                        "timestamp": timestamp,
                        "event_type": event_type,
                        "source": source,
                        "severity": item.get("severity") or "info",
                        "message": message,
                    }
                )
                if len(findings) >= limit:
                    return findings

        if not findings:
            for file_path in self._iter_candidate_files():
                text = self._safe_read_text(file_path)
                if not text:
                    continue
                for line in text.splitlines():
                    if len(findings) >= limit:
                        return findings
                    if not line.strip():
                        continue
                    if re.search(r"(login|logout|access|review|scan|alert|update|deploy)", line, re.IGNORECASE):
                        findings.append(
                            {
                                "timestamp": self._extract_timestamp(line),
                                "event_type": "activity",
                                "source": str(file_path),
                                "severity": "info",
                                "message": line.strip(),
                            }
                        )
        return findings

    def generate_proposals(self, observations: list[dict]) -> list[dict]:
        proposals = []
        issue_counts = Counter()
        for observation in observations:
            message = str(observation.get("message") or "").lower()
            if re.search(r"error|failed|exception|traceback|denied|blocked|attack|alert|critical|malware|suspicious", message):
                issue_counts["incident_review"] += 1
            if re.search(r"login|access|auth|permission|authorization", message):
                issue_counts["access_audit"] += 1
            if re.search(r"scan|monitor|intelligence|baseline|integrity|validation", message):
                issue_counts["baseline_validation"] += 1

        if issue_counts.get("incident_review"):
            proposals.append(
                {
                    "priority": "high",
                    "title": "Review recent incident indicators",
                    "details": "Investigate repeated failures, denied actions, and suspicious events to confirm whether they represent a coordinated attack pattern.",
                }
            )
        if issue_counts.get("access_audit"):
            proposals.append(
                {
                    "priority": "medium",
                    "title": "Audit access and authorization events",
                    "details": "Verify login and authorization records for anomalies, stale permissions, or policy violations that could expose a broader attack path.",
                }
            )
        if issue_counts.get("baseline_validation"):
            proposals.append(
                {
                    "priority": "medium",
                    "title": "Validate integrity baseline checks",
                    "details": "Review baseline or integrity validation records to ensure safe states are still consistent and no drift has gone undetected.",
                }
            )
        if not proposals:
            proposals.append(
                {
                    "priority": "low",
                    "title": "Continue routine monitoring",
                    "details": "No immediate anomalies were identified, but periodic review of events and logs should continue to catch emerging trends early.",
                }
            )
        return proposals

    def analyze(self) -> dict:
        errors = self.analyze_errors(limit=200)
        activities = self.analyze_activity(limit=200)
        observations = errors + activities
        proposals = self.generate_proposals(observations)
        return {
            "generated_at": utc_now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "errors": errors,
            "activity": activities,
            "proposals": proposals,
        }

    def _extract_timestamp(self, text: str):
        match = re.search(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:?\d{2})?)", text)
        if match:
            return match.group(1)
        match = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", text)
        if match:
            return match.group(1)
        return None

    def _severity_from_line(self, line: str) -> str:
        lower = line.lower()
        if re.search(r"critical|attack|malware|breach|intrusion|alert", lower):
            return "critical"
        if re.search(r"error|denied|failed|exception|traceback|blocked", lower):
            return "high"
        if re.search(r"warn|warning|suspicious|retry|timeout", lower):
            return "medium"
        return "low"


def _build_parser():
    parser = argparse.ArgumentParser(description="Analyze activity logs for suspicious behavior and potential mitigation needs.")
    parser.add_argument("--propose", action="store_true", help="Include recommendation proposals in the output.")
    parser.add_argument("--output", default="-", help="Write output to a file path or '-' for stdout.")
    return parser


def main(argv=None):
    parser = _build_parser()
    args = parser.parse_args(argv)
    root_path = Path(__file__).resolve().parent.parent
    analyzer = AttackAnalyzer(root_path)
    report = analyzer.analyze()
    if not args.propose:
        report = {
            "generated_at": report["generated_at"],
            "errors": report["errors"],
            "activity": report["activity"],
        }
    payload = json.dumps(report, indent=2, sort_keys=True)
    if args.output == "-":
        sys.stdout.write(payload + "\n")
        return 0
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(payload + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
