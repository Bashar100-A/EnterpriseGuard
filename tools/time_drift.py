import json
import re
from collections import deque
from datetime import datetime, timedelta, timezone
from pathlib import Path

LOCAL_TZ_OFFSETS = {
    "EDT": -4,
    "EST": -5,
    "PDT": -7,
    "PST": -8,
    "CET": 1,
    "CEST": 2,
    "IST": 5,
    "JST": 9,
    "AEST": 10,
    "AEDT": 11,
}

TZ_ABBREV_PATTERN = "(?:EDT|EST|PDT|PST|CET|CEST|IST|JST|AEST|AEDT)"
AMBIGUOUS_TS_PATTERN = re.compile(r"(?<![A-Za-z0-9])\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}:\d{2})(?![A-Za-z0-9])")
STRICT_TS_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])"
    r"\d{4}-\d{2}-\d{2}"
    r"(?:[T ]\d{2}:\d{2}:\d{2})"
    r"(?:Z|[+-]\d{2}:\d{2}| UTC| GMT|"
    + TZ_ABBREV_PATTERN
    + r")"
    r"(?![A-Za-z0-9])",
    re.VERBOSE,
)


def _to_utc_datetime(raw: str) -> datetime:
    candidate = raw.strip()

    if candidate.endswith("Z"):
        for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%SZ"):
            try:
                return datetime.strptime(candidate, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue

    if re.search(r"[+-]\d{2}:\d{2}$", candidate):
        for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S%z"):
            try:
                dt = datetime.strptime(candidate, fmt)
                return dt.astimezone(timezone.utc)
            except ValueError:
                continue

    if candidate.endswith(" UTC") or candidate.endswith(" GMT"):
        base = candidate.rsplit(" ", 1)[0]
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(base, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue

    if " " in candidate:
        base, tz_token = candidate.rsplit(" ", 1)
    else:
        base = candidate[:-3]
        tz_token = candidate[-3:]
    if tz_token in LOCAL_TZ_OFFSETS:
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                dt = datetime.strptime(base, fmt)
                offset = timedelta(hours=LOCAL_TZ_OFFSETS[tz_token])
                return dt - offset
            except ValueError:
                continue
    raise ValueError(f"Unsupported timestamp format: {raw}")


def extract_timestamps_from_text(text: str, start_line: int = 1) -> list[dict]:
    matches: list[dict] = []
    for match in STRICT_TS_PATTERN.finditer(text):
        raw = match.group(0).strip()
        line_number = text.count("\n", 0, match.start()) + start_line
        matches.append({
            "raw": raw,
            "line": line_number,
            "match_start": match.start(),
            "match_end": match.end(),
        })
    return matches


def classify_timestamp(raw: str) -> str:
    value = str(raw).strip()
    if not value:
        return "INVALID"

    if re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}:\d{2})?", value):
        return "AMBIGUOUS"

    if STRICT_TS_PATTERN.fullmatch(value):
        if value.endswith("Z"):
            return "UTC_Z"
        if re.search(r"[+-]\d{2}:\d{2}$", value):
            return "UTC_OFFSET"
        if value.endswith(" UTC") or value.endswith(" GMT"):
            return "UTC_NAMED"
        if value.endswith(tuple(LOCAL_TZ_OFFSETS.keys())):
            return "LOCAL"
        return "INVALID"

    if re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}:\d{2})", value):
        return "AMBIGUOUS"

    if re.fullmatch(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}.*", value):
        return "AMBIGUOUS"

    return "INVALID"


def is_chronologically_consistent(ts_list: list[dict]) -> tuple[bool, str, list]:
    comparable: list[tuple[datetime, str]] = []
    skipped: list[str] = []

    for item in ts_list:
        raw = str(item.get("raw") if isinstance(item, dict) else item).strip()
        classification = classify_timestamp(raw)
        if classification in {"UTC_Z", "UTC_OFFSET", "UTC_NAMED"}:
            try:
                comparable.append((_to_utc_datetime(raw), raw))
            except ValueError:
                skipped.append(raw)
        elif classification == "LOCAL":
            try:
                raw_name = raw.rsplit(" ", 1)[-1] if " " in raw else raw[-3:]
                if raw_name in LOCAL_TZ_OFFSETS:
                    base = raw.rsplit(" ", 1)[0] if " " in raw else raw[:-3]
                    dt = datetime.strptime(base, "%Y-%m-%dT%H:%M:%S") if "T" in base else datetime.strptime(base, "%Y-%m-%d %H:%M:%S")
                    comparable.append((dt - timedelta(hours=LOCAL_TZ_OFFSETS[raw_name]), raw))
                else:
                    skipped.append(raw)
            except ValueError:
                skipped.append(raw)
        else:
            skipped.append(raw)

    if len(comparable) < 2:
        return True, "No comparable timestamps", skipped

    for index in range(1, len(comparable)):
        previous_dt, _ = comparable[index - 1]
        current_dt, _ = comparable[index]
        if current_dt < previous_dt:
            return False, "Out-of-order timestamp detected", []

    return True, "Chronological order consistent", skipped


def read_tail_lines(path: Path, max_lines: int) -> tuple[list[str], int]:
    if max_lines <= 0:
        return [], 1
    from collections import deque

    buffer: deque[str] = deque(maxlen=max_lines)
    total_lines = 0
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            buffer.append(line)
            total_lines += 1

    if not buffer:
        return [], 1

    lines = list(buffer)
    start_line = max(1, total_lines - len(lines) + 1)
    return lines, start_line


def analyze_time_drift(paths: list[Path], max_lines_per_file: int = 2000) -> dict:
    report = {
        "files_analyzed": [],
        "total_timestamps_found": 0,
        "ambiguous_timestamps": [],
        "out_of_order_timestamps": [],
        "invalid_timestamps": [],
        "skipped_ambiguous_in_ordering": [],
        "files_missing": [],
        "files_empty": [],
        "overall_status": "PASS",
    }

    for raw_path in paths:
        file_path = Path(raw_path)
        report["files_analyzed"].append(str(file_path))

        if not file_path.exists():
            report["files_missing"].append(str(file_path))
            continue

        if file_path.stat().st_size == 0:
            report["files_empty"].append(str(file_path))
            continue

        if file_path.name == "activity_log.json":
            try:
                with file_path.open("r", encoding="utf-8") as handle:
                    payload = json.load(handle)
            except (json.JSONDecodeError, OSError, ValueError) as exc:
                report["invalid_timestamps"].append({
                    "file": str(file_path),
                    "line": 1,
                    "raw": f"Malformed JSON: {exc}",
                    "classification": "INVALID",
                })
                continue

            items = payload.get("activities", payload) if isinstance(payload, dict) else payload
            if not isinstance(items, list):
                report["files_empty"].append(str(file_path))
                continue

            timestamps: list[dict] = []
            for idx, entry in enumerate(items):
                if isinstance(entry, dict):
                    value = entry.get("timestamp")
                    if isinstance(value, str):
                        timestamps.append({
                            "file": str(file_path),
                            "line": idx + 1,
                            "raw": value,
                        })
            report["total_timestamps_found"] += len(timestamps)
            for ts in timestamps:
                classification = classify_timestamp(ts["raw"])
                if classification == "AMBIGUOUS":
                    report["ambiguous_timestamps"].append({**ts, "classification": classification})
                elif classification == "INVALID":
                    report["invalid_timestamps"].append({**ts, "classification": classification})

            comparable = []
            skipped: list[dict] = []
            for ts in timestamps:
                raw = ts["raw"]
                classification = classify_timestamp(raw)
                if classification in {"UTC_Z", "UTC_OFFSET", "UTC_NAMED"}:
                    try:
                        comparable.append({"raw": raw, "dt": _to_utc_datetime(raw)})
                    except ValueError:
                        skipped.append({"file": str(file_path), "raw": raw, "classification": classification})
                elif classification == "LOCAL":
                    try:
                        raw_name = raw.rsplit(" ", 1)[-1] if " " in raw else raw[-3:]
                        if raw_name in LOCAL_TZ_OFFSETS:
                            base = raw.rsplit(" ", 1)[0] if " " in raw else raw[:-3]
                            dt = datetime.strptime(base, "%Y-%m-%dT%H:%M:%S") if "T" in base else datetime.strptime(base, "%Y-%m-%d %H:%M:%S")
                            comparable.append({"raw": raw, "dt": dt - timedelta(hours=LOCAL_TZ_OFFSETS[raw_name])})
                        else:
                            skipped.append({"file": str(file_path), "raw": raw, "classification": classification})
                    except ValueError:
                        skipped.append({"file": str(file_path), "raw": raw, "classification": classification})
                elif classification == "AMBIGUOUS":
                    skipped.append({"file": str(file_path), "raw": raw, "classification": classification})
                elif classification == "INVALID":
                    report["invalid_timestamps"].append({**ts, "classification": classification})

            report["skipped_ambiguous_in_ordering"].extend(skipped)

            for index in range(1, len(comparable)):
                previous = comparable[index - 1]
                current = comparable[index]
                if current["dt"] < previous["dt"]:
                    report["out_of_order_timestamps"].append({
                        "file": str(file_path),
                        "previous": previous["raw"],
                        "current": current["raw"],
                    })
            continue

        lines, start_line = read_tail_lines(file_path, max_lines_per_file)
        if not lines:
            report["files_empty"].append(str(file_path))
            continue

        joined_text = "".join(lines)
        timestamps = extract_timestamps_from_text(joined_text, start_line=start_line)
        report["total_timestamps_found"] += len(timestamps)

        seen_ambiguous = set()
        for match in AMBIGUOUS_TS_PATTERN.finditer(joined_text):
            raw = match.group(0)
            remainder = joined_text[match.end() :].lstrip()
            if remainder.startswith(("UTC", "GMT", "EDT", "EST", "PDT", "PST", "CET", "CEST", "IST", "JST", "AEST", "AEDT", "Z", "+", "-")):
                continue
            if any(item["raw"] == raw for item in timestamps):
                continue
            seen_ambiguous.add(raw)
            line_number = joined_text.count("\n", 0, match.start()) + start_line
            report["ambiguous_timestamps"].append({
                "file": str(file_path),
                "line": line_number,
                "raw": raw,
                "classification": "AMBIGUOUS",
            })
            report["skipped_ambiguous_in_ordering"].append({
                "file": str(file_path),
                "line": line_number,
                "raw": raw,
                "classification": "AMBIGUOUS",
            })

        for item in timestamps:
            classification = classify_timestamp(item["raw"])
            if classification == "AMBIGUOUS":
                report["ambiguous_timestamps"].append({
                    "file": str(file_path),
                    "line": item["line"],
                    "raw": item["raw"],
                    "classification": classification,
                })
            elif classification == "INVALID":
                report["invalid_timestamps"].append({
                    "file": str(file_path),
                    "line": item["line"],
                    "raw": item["raw"],
                    "classification": classification,
                })

        sequence = []
        skipped = []
        for item in timestamps:
            raw = item["raw"]
            classification = classify_timestamp(raw)
            if classification in {"UTC_Z", "UTC_OFFSET", "UTC_NAMED"}:
                try:
                    sequence.append({"raw": raw, "dt": _to_utc_datetime(raw)})
                except ValueError:
                    skipped.append({"file": str(file_path), "raw": raw, "classification": classification})
            elif classification == "LOCAL":
                try:
                    raw_name = raw.rsplit(" ", 1)[-1] if " " in raw else raw[-3:]
                    base = raw.rsplit(" ", 1)[0] if " " in raw else raw[:-3]
                    dt = datetime.strptime(base, "%Y-%m-%dT%H:%M:%S") if "T" in base else datetime.strptime(base, "%Y-%m-%d %H:%M:%S")
                    sequence.append({"raw": raw, "dt": dt - timedelta(hours=LOCAL_TZ_OFFSETS[raw_name])})
                except ValueError:
                    skipped.append({"file": str(file_path), "raw": raw, "classification": classification})
            elif classification == "AMBIGUOUS":
                skipped.append({"file": str(file_path), "raw": raw, "classification": classification})
            elif classification == "INVALID":
                report["invalid_timestamps"].append({
                    "file": str(file_path),
                    "line": item["line"],
                    "raw": raw,
                    "classification": classification,
                })

        report["skipped_ambiguous_in_ordering"].extend(skipped)
        for index in range(1, len(sequence)):
            previous = sequence[index - 1]
            current = sequence[index]
            if current["dt"] < previous["dt"]:
                report["out_of_order_timestamps"].append({
                    "file": str(file_path),
                    "previous": previous["raw"],
                    "current": current["raw"],
                })

    has_invalid = bool(report["invalid_timestamps"]) or bool(report["out_of_order_timestamps"])
    has_warn = bool(report["ambiguous_timestamps"]) or bool(report["skipped_ambiguous_in_ordering"])
    if has_invalid:
        report["overall_status"] = "FAIL"
    elif has_warn:
        report["overall_status"] = "WARN"
    else:
        report["overall_status"] = "PASS"

    return report
