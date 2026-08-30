import hashlib
import json
import os
import py_compile
import re
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.audit_chain import append_activity, migrate_activity_log, verify_activity_chain
from tools.time_drift import analyze_time_drift

ROOT = Path(__file__).resolve().parent.parent
ROOT_DIR = ROOT
TOOLS_DIR = ROOT / "tools"
ACTIVITY_LOG_PATH = TOOLS_DIR / "activity_log.json"
ERROR_LOG_PATH = TOOLS_DIR / "errors.log"
ERRORS_LOG_PATH = ERROR_LOG_PATH
LATEST_CONTEXT_PATH = TOOLS_DIR / "latest_context.txt"
REPORT_PATH = LATEST_CONTEXT_PATH
PROTECTED_DIRS = {"adie", "intelligence"}
EXCLUDED_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}
RAG_CANDIDATES = [ROOT / "rag_system.py", TOOLS_DIR / "rag_system.py"]
RAG_SCRIPT_CANDIDATES = RAG_CANDIDATES
LAST_INTEGRITY_SNAPSHOT_TS = None


def iso_utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_utc_now_str() -> str:
    """Return the current UTC timestamp in ISO 8601 format."""
    return iso_utc_now()


def ensure_tools_dir() -> None:
    TOOLS_DIR.mkdir(exist_ok=True, parents=True)


def stderr_warn(message: str) -> None:
    print(f"[EnterpriseGuard] {message}", file=sys.stderr)


def read_json_file(path: Path, default):
    if not path.exists():
        return deepcopy(default)
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, (list, dict)):
            return data
        return deepcopy(default)
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        stderr_warn(f"Warning: corrupt or unreadable JSON file at {path}. Starting fresh. Error: {exc}")
        return deepcopy(default)


def write_json_file(path: Path, data) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(path.parent), delete=False) as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
            temp_path = Path(handle.name)
        os.replace(temp_path, path)
        return True
    except Exception as exc:
        stderr_warn(f"Failed to write JSON file {path}: {exc}")
        return False


def append_to_errors_log(message: str) -> None:
    ensure_tools_dir()
    try:
        with ERROR_LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(f"[{iso_utc_now()}] ERROR: {message}\n")
    except Exception as exc:
        stderr_warn(f"Failed to append to errors log: {exc}")


def append_to_activity_log(entry: dict) -> None:
    ensure_tools_dir()
    try:
        if not isinstance(entry, dict):
            entry = {"details": str(entry)}

        timestamp = entry.get("timestamp") or iso_utc_now()
        activity_type = entry.get("activity_type") or "command_center_action"
        status = entry.get("status") or "success"
        details = entry.get("details") or entry.get("status") or "n/a"

        data = {
            "timestamp": timestamp,
            "activity_type": activity_type,
            "status": status,
            "details": details,
        }
        for key, value in entry.items():
            if key not in {"timestamp", "activity_type", "status", "details"}:
                data[key] = value

        append_activity(data, ACTIVITY_LOG_PATH)
    except Exception as exc:
        stderr_warn(f"Failed to append activity log entry: {exc}")
        append_to_errors_log(f"Activity log write failed: {exc}")


def read_activity_entries() -> list:
    raw = read_json_file(ACTIVITY_LOG_PATH, [])
    if isinstance(raw, dict):
        entries = raw.get("activities", []) if isinstance(raw.get("activities"), list) else []
    elif isinstance(raw, list):
        entries = raw
    else:
        entries = []
    return entries


def get_activity_display_entries(limit: int = 50) -> list:
    entries = read_activity_entries()
    filtered = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if entry.get("activity_type") in {"app_started", "command_center_action"}:
            continue
        filtered.append(entry)
    return filtered[-limit:]


def get_last_activity_label() -> str:
    entries = read_activity_entries()
    filtered = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if entry.get("activity_type") in {"app_started", "command_center_action"}:
            continue
        filtered.append(entry)
    if not filtered:
        return "No activity recorded yet"
    last = filtered[-1]
    ts = last.get("timestamp", "unknown")
    activity_type = last.get("activity_type", "activity")
    details = last.get("details") or last.get("status") or "n/a"
    return f"{ts} :: {activity_type} :: {details}"


def get_latest_report_timestamp() -> str:
    if not LATEST_CONTEXT_PATH.exists():
        return "Never"
    try:
        text = LATEST_CONTEXT_PATH.read_text(encoding="utf-8")
    except Exception as exc:
        stderr_warn(f"Unable to read report file: {exc}")
        return "Never"
    marker = "Architectural Context Report — Generated at: "
    if marker in text:
        remainder = text.split(marker, 1)[1].splitlines()[0].strip()
        return remainder or "Never"
    return "Unknown report timestamp"


def count_project_files_and_lines(root: Path) -> tuple[int, int]:
    file_count = 0
    total_lines = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames
            if d not in EXCLUDED_DIRS
            and not d.startswith(".")
            and d not in PROTECTED_DIRS
            and not any(part in PROTECTED_DIRS for part in Path(dirpath).joinpath(d).parts)
        ]
        for filename in filenames:
            if filename.startswith("."):
                continue
            file_path = Path(dirpath) / filename
            if file_path.is_dir():
                continue
            try:
                file_count += 1
                with file_path.open("r", encoding="utf-8", errors="ignore") as handle:
                    total_lines += sum(1 for _ in handle)
            except Exception:
                continue
    return file_count, total_lines


def generate_file_tree(root_path: Path) -> str:
    """Return a text tree for the repository without traversing protected directories."""
    lines: list[str] = []

    def walk(directory: Path, prefix: str = "") -> None:
        try:
            entries = sorted(
                directory.iterdir(),
                key=lambda item: (not item.is_dir(), item.name.lower()),
            )
        except OSError:
            return

        visible_entries = []
        for item in entries:
            if item.name in EXCLUDED_DIRS or item.name.startswith("."):
                continue
            if item.name in PROTECTED_DIRS:
                continue
            if any(part in PROTECTED_DIRS for part in item.parts):
                continue
            visible_entries.append(item)

        for index, item in enumerate(visible_entries):
            is_last = index == len(visible_entries) - 1
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{item.name}")
            if item.is_dir():
                child_prefix = prefix + ("    " if is_last else "│   ")
                walk(item, child_prefix)

    walk(root_path)
    return "\n".join(lines) if lines else "Root Repository is empty."


def generate_memory_snapshot(root_path: Path) -> dict:
    """Build a portable project-memory snapshot for handoff to another AI agent."""
    repo_root = root_path.resolve()
    repo_root = repo_root if repo_root.exists() else Path.cwd().resolve()

    def truncate_text(value: str, limit: int, suffix: str = "... [truncated]") -> str:
        if value is None:
            return "MISSING"
        if len(value) <= limit:
            return value
        return value[: limit - len(suffix)] + suffix

    def read_text_data(file_path: Path, limit: int, missing_value: str = "MISSING", empty_value: str | None = None) -> str:
        if not file_path.exists():
            return missing_value
        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            if missing_value == "MISSING":
                return f"ERROR: {exc}"
            return f"ERROR: {exc}"
        if empty_value is not None and not text.strip():
            return empty_value
        return truncate_text(text, limit)

    def build_tree(directory: Path, prefix: str = "") -> list[str]:
        entries: list[str] = []
        try:
            children = sorted(directory.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower()))
        except OSError:
            return entries

        visible = []
        for child in children:
            if child.name.startswith("."):
                continue
            if child.name in EXCLUDED_DIRS:
                continue
            if child.name in PROTECTED_DIRS:
                continue
            if any(part in PROTECTED_DIRS for part in child.parts):
                continue
            visible.append(child)

        for index, item in enumerate(visible):
            is_last = index == len(visible) - 1
            connector = "└── " if is_last else "├── "
            entries.append(f"{prefix}{connector}{item.name}")
            if item.is_dir():
                child_prefix = prefix + ("    " if is_last else "│   ")
                entries.extend(build_tree(item, child_prefix))
        return entries

    file_tree = "\n".join(build_tree(repo_root)) if (repo_root.exists() and repo_root.is_dir()) else "Root Repository is empty."

    decision_log_path = repo_root / "tools" / "DECISIONS_LOG.md"
    project_memory_path = repo_root / "PROJECT_MEMORY.md"
    contracts_path = repo_root / "CONTRACTS.md"
    governance_files = {
        "decision_log": read_text_data(decision_log_path, 20000),
        "project_memory": read_text_data(project_memory_path, 20000),
        "contracts": read_text_data(contracts_path, 20000),
    }

    errors_log_path = repo_root / "tools" / "errors.log"
    if not errors_log_path.exists():
        errors_log_value = "MISSING"
    else:
        try:
            text = errors_log_path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            errors_log_value = f"ERROR: {exc}"
        else:
            if not text.strip():
                errors_log_value = "EMPTY"
            else:
                errors_log_value = truncate_text(text, 10000)
    errors_log = errors_log_value

    activity_log_path = repo_root / "tools" / "activity_log.json"
    if not activity_log_path.exists():
        activity_log = "MISSING"
    else:
        try:
            raw = json.loads(activity_log_path.read_text(encoding="utf-8", errors="replace"))
        except (json.JSONDecodeError, OSError, ValueError) as exc:
            activity_log = f"ERROR: {exc}"
        else:
            if isinstance(raw, dict):
                entries = raw.get("activities", []) if isinstance(raw.get("activities"), list) else []
            elif isinstance(raw, list):
                entries = raw
            else:
                entries = []
            entries = [entry for entry in entries if isinstance(entry, dict)]
            last_entries = entries[-50:]
            activity_log = {
                "entries": last_entries,
                "older_entries_exist": len(entries) > 50,
            }

    checklist_path = repo_root / "tools" / "checklist.py"
    checklist_result = subprocess.run(
        [sys.executable, str(checklist_path)],
        capture_output=True,
        text=True,
        cwd=str(repo_root),
        timeout=180,
        check=False,
    )
    checklist_output = f"{checklist_result.stdout}\n{checklist_result.stderr}".strip() if checklist_result.stdout or checklist_result.stderr else "CHECKLIST_OK"
    checklist_output = truncate_text(checklist_output, 5000)

    latest_context_path = repo_root / "tools" / "latest_context.txt"
    latest_context = read_text_data(latest_context_path, 10000)

    def run_shell_command(command: list[str]) -> str:
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            output = (result.stdout or "").strip()
            if output:
                return output
            stderr = (result.stderr or "").strip()
            return stderr if stderr else "NOT_AVAILABLE"
        except Exception:
            return "NOT_AVAILABLE"

    python_version = run_shell_command(["python3", "--version"]).strip() or "NOT_INSTALLED"
    streamlit_version = "NOT_INSTALLED"
    try:
        streamlit_result = subprocess.run([sys.executable, "-c", "import streamlit; print(streamlit.__version__)"], capture_output=True, text=True, check=False)
        streamlit_version = (streamlit_result.stdout or "").strip() or "NOT_INSTALLED"
    except Exception:
        streamlit_version = "NOT_INSTALLED"

    requirements_path = repo_root / "requirements.txt"
    requirements_text = read_text_data(requirements_path, 2000)
    if requirements_text == "MISSING":
        requirements_text = "MISSING"

    recent_files: list[dict[str, str]] = []
    for dirpath, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = [
            d for d in dirnames
            if not d.startswith(".")
            and d not in EXCLUDED_DIRS
            and d not in PROTECTED_DIRS
            and d not in {"adie", "intelligence"}
        ]
        for filename in filenames:
            if filename.startswith("."):
                continue
            file_path = Path(dirpath) / filename
            if file_path.name in EXCLUDED_DIRS or file_path.name in PROTECTED_DIRS:
                continue
            if any(part in PROTECTED_DIRS for part in file_path.parts):
                continue
            try:
                stat = file_path.stat()
            except OSError:
                continue
            relative_path = file_path.relative_to(repo_root).as_posix()
            recent_files.append({
                "path": relative_path,
                "mtime": datetime.fromtimestamp(stat.st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            })
    recent_files = sorted(recent_files, key=lambda item: item["mtime"], reverse=True)[:100]

    protected_dirs_exist = {
        "adie": (repo_root / "adie").exists(),
        "intelligence": (repo_root / "intelligence").exists(),
    }

    git_info: object = "NOT_AVAILABLE"
    if shutil.which("git") and (repo_root / ".git").exists():
        branch = subprocess.run(["git", "-C", str(repo_root), "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=False)
        last_commit = subprocess.run(["git", "-C", str(repo_root), "log", "-1", "--pretty=format:%H|%an|%aI|%s"], capture_output=True, text=True, check=False)
        if branch.returncode == 0 and last_commit.returncode == 0:
            git_info = {
                "branch": (branch.stdout or "").strip() or "UNKNOWN",
                "last_commit": (last_commit.stdout or "").strip() or "UNKNOWN",
            }

    generated_at = iso_utc_now()
    notes = (
        "Snapshot generated with hidden files and directories, __pycache__, node_modules, and protected directories excluded. "
        "Checklist output and larger content blocks were truncated to maintain portability."
    )

    return {
        "generated_at": generated_at,
        "file_tree": file_tree,
        "governance_files": governance_files,
        "errors_log": errors_log,
        "activity_log": activity_log,
        "checklist_exit_code": int(checklist_result.returncode),
        "checklist_output": checklist_output,
        "latest_context": latest_context,
        "environment": {
            "python_version": python_version,
            "streamlit_version": streamlit_version,
            "requirements": requirements_text,
        },
        "recent_files": recent_files,
        "protected_dirs_exist": protected_dirs_exist,
        "git_info": git_info,
        "notes": notes,
    }


def build_project_tree(root: Path) -> dict:
    tree: dict = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames
            if d not in EXCLUDED_DIRS
            and not d.startswith(".")
            and d not in PROTECTED_DIRS
            and not any(part in PROTECTED_DIRS for part in Path(dirpath).joinpath(d).parts)
        ]
        current_rel = Path(dirpath).relative_to(root)
        pointer = tree
        if current_rel != Path("."):
            for part in current_rel.parts:
                pointer = pointer.setdefault(part, {})
        for filename in sorted(filenames):
            if filename.startswith("."):
                continue
            pointer[filename] = None
    return tree


def scan_project_tree() -> tuple[str, int, int]:
    """Return a display tree, visible file count, and text-line count."""
    tree_text = generate_file_tree(ROOT_DIR)
    file_count, line_count = count_project_files_and_lines(ROOT_DIR)
    return tree_text, file_count, line_count


def render_tree_lines(tree: dict, prefix: str = "") -> list[str]:
    lines = []
    keys = list(tree.keys())
    for index, key in enumerate(keys):
        is_last = index == len(keys) - 1
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{key}")
        value = tree[key]
        if isinstance(value, dict) and value:
            child_prefix = prefix + ("    " if is_last else "│   ")
            lines.extend(render_tree_lines(value, child_prefix))
    return lines


def find_rag_path() -> Path | None:
    for candidate in RAG_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def get_rag_status() -> str:
    return "Available" if find_rag_path() else "Not Found"


def read_error_lines() -> list[str]:
    ensure_tools_dir()
    if not ERROR_LOG_PATH.exists():
        return []
    try:
        with ERROR_LOG_PATH.open("r", encoding="utf-8") as handle:
            return [line.rstrip() for line in handle if line.strip()]
    except Exception as exc:
        stderr_warn(f"Failed to read errors log: {exc}")
        return []


def get_activity_summary(last_n: int = 20) -> str:
    entries = read_activity_entries()[-last_n:]
    if not entries:
        return "No activity recorded."
    lines = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        details = entry.get("details") or entry.get("status") or "n/a"
        lines.append(f"- {entry.get('timestamp', 'unknown')} :: {entry.get('activity_type', 'activity')} :: {details}")
    return "\n".join(lines)


def render_dashboard() -> None:
    st.title("Developer Command Center")
    st.subheader("Workspace Overview")
    st.markdown("---")
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    file_count, line_count = count_project_files_and_lines(ROOT)
    rag_status = get_rag_status()
    last_report = get_latest_report_timestamp()
    last_activity = get_last_activity_label()

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Current UTC", now_utc)
    with col2:
        st.metric("Files", file_count)
    with col3:
        st.metric("Lines", line_count)
    with col4:
        st.metric("RAG", rag_status)
    with col5:
        st.metric("Last report", last_report)

    st.divider()
    st.info(f"Last activity: {last_activity}")
    if rag_status == "Available":
        st.success("RAG system is available and ready for execution.")
    else:
        st.warning("RAG system not found — pending integration")


def render_file_tree() -> None:
    st.title("File Tree")
    st.subheader("Project Structure")
    st.caption("Hidden directories, node_modules, and protected core directories are excluded from the walk.")
    tree_text = generate_file_tree(ROOT)
    if not tree_text or tree_text == "Root Repository is empty.":
        st.warning("No files available to display.")
        return
    with st.expander("File Tree", expanded=True):
        st.code(tree_text, language="text")
    visible_file_count, _ = count_project_files_and_lines(ROOT)
    st.caption(f"Visible file count: {visible_file_count}")


def render_rag_console() -> None:
    st.title("RAG Console")
    rag_path = find_rag_path()
    if rag_path is None and (TOOLS_DIR / "rag_system.py").exists():
        rag_path = TOOLS_DIR / "rag_system.py"
    if rag_path is None:
        st.warning("RAG system not found — pending integration")
        return

    st.info(f"Source: {rag_path}")
    query = st.text_input("Query", placeholder="Enter a project context query")
    if st.button("Run RAG System"):
        if not query.strip():
            st.warning("Enter a query before running the RAG system.")
            return
        try:
            result = subprocess.run([sys.executable, str(rag_path), query], capture_output=True, text=True, cwd=str(ROOT), timeout=60, check=False)
            output = (result.stdout or "").strip() or (result.stderr or "").strip() or "RAG system executed successfully with no output."
            try:
                parsed_output = json.loads(output)
                st.session_state["rag_output"] = parsed_output
            except json.JSONDecodeError:
                st.session_state["rag_output"] = output
            status = "success" if result.returncode == 0 else "failed"
            append_to_activity_log({
                "activity_type": "rag_run",
                "status": status,
                "details": f"RAG execution returned code {result.returncode}",
            })
            if result.returncode != 0:
                append_to_errors_log(f"RAG execution failed with code {result.returncode}: {output[:500]}")
                st.error(f"RAG execution failed: {output}")
            else:
                st.success("RAG system completed successfully.")
        except subprocess.TimeoutExpired:
            msg = "RAG system timed out after 60 seconds."
            append_to_errors_log(msg)
            append_to_activity_log({"activity_type": "rag_run", "status": "failed", "details": msg})
            st.error(msg)
        except Exception as exc:
            msg = f"Unexpected RAG execution error: {exc}"
            append_to_errors_log(msg)
            append_to_activity_log({"activity_type": "rag_run", "status": "failed", "details": msg})
            st.error(msg)

    rag_output = st.session_state.get("rag_output", "")
    if rag_output:
        st.subheader("Output")
        if isinstance(rag_output, dict):
            st.json(rag_output)
        else:
            st.code(rag_output, language="text")
    else:
        st.info("No RAG output available yet.")


def render_activity_log() -> None:
    st.title("Activity Log")
    if st.button("Refresh log"):
        st.rerun()
    entries = get_activity_display_entries(limit=50)
    if not entries:
        st.warning("No activity recorded yet.")
        return
    rows = []
    for entry in entries:
        rows.append({
            "timestamp": entry.get("timestamp", "unknown"),
            "activity_type": entry.get("activity_type", "activity"),
            "details": entry.get("details") or entry.get("status") or "n/a",
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)


def render_memory_snapshot() -> None:
    st.title("Memory Snapshot")
    st.subheader("Project context export")
    st.caption("Generate a portable JSON snapshot suitable for restoring full context to another AI agent.")

    if st.button("Generate Memory Snapshot"):
        try:
            snapshot = generate_memory_snapshot(Path.cwd())
            snapshot_timestamp = iso_utc_now()
            snapshot_filename = f"memory_snapshot_{snapshot_timestamp}.json"
            snapshot_path = TOOLS_DIR / snapshot_filename
            snapshot_text = json.dumps(snapshot, indent=2, ensure_ascii=False)

            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(TOOLS_DIR), delete=False) as handle:
                handle.write(snapshot_text)
                tmp_path = Path(handle.name)
            os.replace(tmp_path, snapshot_path)

            if not snapshot_path.exists() or snapshot_path.stat().st_size <= 0:
                raise OSError(f"Snapshot file was not created or is empty: {snapshot_path}")

            st.session_state["memory_snapshot_data"] = snapshot
            st.session_state["memory_snapshot_filename"] = snapshot_filename
            st.session_state["memory_snapshot_content"] = snapshot_text
            st.success(f"Memory snapshot saved to {snapshot_path}")
            st.code(snapshot_text, language="json", height=600)
            st.download_button(
                label="Download Memory Snapshot",
                data=snapshot_text,
                file_name=snapshot_filename,
                mime="application/json",
            )
        except Exception as exc:
            msg = f"Memory snapshot generation failed: {exc}"
            append_to_errors_log(msg)
            st.error(msg)

    snapshot_data = st.session_state.get("memory_snapshot_data")
    if snapshot_data:
        st.subheader("Last Snapshot")
        st.code(json.dumps(snapshot_data, indent=2, ensure_ascii=False), language="json", height=600)
        st.download_button(
            label="Download Latest Snapshot",
            data=json.dumps(snapshot_data, indent=2, ensure_ascii=False),
            file_name=st.session_state.get("memory_snapshot_filename", "memory_snapshot_latest.json"),
            mime="application/json",
        )
    else:
        st.info("No snapshot has been generated in this session yet.")


def render_system_integrity() -> None:
    st.title("System Controls")
    st.subheader("System Integrity Check")
    st.caption("Validate the repository health and generate a review-only repair recommendation when needed.")

    if st.button("System Integrity Check"):
        try:
            result = run_system_integrity_check(Path.cwd())
            st.session_state["last_integrity_result"] = result
            st.session_state["last_integrity_timestamp"] = result.get("timestamp")
            global LAST_INTEGRITY_SNAPSHOT_TS
            LAST_INTEGRITY_SNAPSHOT_TS = result.get("timestamp")

            status = result.get("status", "WARN")
            if status == "OK":
                st.success("The operation was successful")
            elif status == "FAIL":
                st.error("System integrity check failed. See details below.")
            else:
                st.warning("System integrity check completed with warnings.")
            st.json(result)
        except Exception as exc:
            msg = f"System integrity check failed: {exc}"
            append_to_errors_log(msg)
            st.error(msg)

    last_result = st.session_state.get("last_integrity_result")
    if last_result:
        st.markdown("---")
        st.subheader("Last Integrity Result")
        st.json(last_result)

    can_generate = bool(st.session_state.get("last_integrity_result", {}).get("status") == "FAIL")
    if st.button("Generate Repair Recommendation", disabled=not can_generate):
        try:
            result = st.session_state.get("last_integrity_result")
            if not result:
                raise ValueError("No integrity result is available to generate a repair recommendation.")
            report_path = generate_repair_recommendation(result, Path.cwd())
            st.session_state["last_repair_report_path"] = str(report_path)
            st.success("Report generated for Architect Review")
            st.write(report_path)
            st.download_button(
                label="Download Repair Recommendation",
                data=report_path.read_text(encoding="utf-8"),
                file_name=report_path.name,
                mime="application/json",
            )
        except Exception as exc:
            msg = f"Repair recommendation generation failed: {exc}"
            append_to_errors_log(msg)
            st.error(msg)

    if st.session_state.get("last_repair_report_path"):
        st.caption(f"Generated report: {st.session_state['last_repair_report_path']}")


def run_system_integrity_check(root_path: Path) -> dict:
    """Run a safe repository health check without traversing protected directories."""
    repo_root = root_path.resolve() if root_path.exists() else Path.cwd().resolve()
    errors: list[str] = []
    warnings: list[str] = []
    checks: dict[str, object] = {
        "syntax_check": "SKIP",
        "import_check": "FAIL",
        "governance_check": "WARN",
        "log_check": "MISSING",
        "protected_dirs_check": "WARN",
        "audit_chain_check": "MISSING",
        "time_drift_check": {
            "status": "MISSING",
            "files_analyzed": 0,
            "total_timestamps_found": 0,
            "ambiguous_count": 0,
            "invalid_count": 0,
            "out_of_order_count": 0,
            "skipped_ambiguous_count": 0,
        },
    }

    protected_paths = [
        repo_root / "adie",
        repo_root / "intelligence",
        repo_root / "src" / "enterpriseguard" / "adie",
        repo_root / "src" / "enterpriseguard" / "intelligence",
    ]
    protected_exists = [path.exists() for path in protected_paths]
    checks["protected_dirs_check"] = "PASS" if any(protected_exists) else "WARN"

    py_files: list[Path] = []
    for base_dir in [repo_root / "tools", repo_root / "src"]:
        if base_dir.exists():
            py_files.extend([path for path in base_dir.rglob("*.py") if "adie" not in str(path).lower() and "intelligence" not in str(path).lower()])
    py_files.extend(
        path for path in repo_root.glob("*.py") if "adie" not in str(path).lower() and "intelligence" not in str(path).lower()
    )
    py_files = sorted(set(py_files), key=lambda path: str(path))

    if py_files:
        syntax_failures = []
        for file_path in py_files:
            try:
                py_compile.compile(str(file_path), doraise=True)
            except py_compile.PyCompileError as exc:
                syntax_failures.append(f"{file_path}: {exc}")
        if syntax_failures:
            errors.extend(syntax_failures)
            checks["syntax_check"] = "FAIL"
        else:
            checks["syntax_check"] = "PASS"
    else:
        checks["syntax_check"] = "SKIP"

    for module_name in ["tools.checklist", "tools.command_center", "tools.rag_system"]:
        command = ["python3", "-c", f"import sys; sys.path.insert(0, '.'); import {module_name}"]
        try:
            result = subprocess.run(command, cwd=str(repo_root), capture_output=True, text=True, timeout=15, check=False)
        except subprocess.TimeoutExpired as exc:
            errors.append(f"{module_name}: timeout while importing ({exc})")
            continue
        if result.returncode != 0:
            import_error = (result.stderr or result.stdout or "Unknown import error").strip()
            errors.append(f"{module_name}: {import_error}")
    checks["import_check"] = "PASS" if not any(error.startswith("tools.") for error in errors) else "FAIL"

    governance_paths = [
        repo_root / "CONTRACTS.md",
        repo_root / "tools" / "DECISIONS_LOG.md",
        repo_root / "tools" / "activity_log.json",
    ]
    missing_governance = []
    for path in governance_paths:
        if not path.exists():
            missing_governance.append(path.name)
            warnings.append(f"{path.name} missing")
    checks["governance_check"] = "PASS" if not missing_governance else "WARN"

    errors_log_path = repo_root / "tools" / "errors.log"
    if not errors_log_path.exists():
        warnings.append("tools/errors.log missing; log check skipped")
        checks["log_check"] = "MISSING"
    else:
        tail_lines: list[str] = []
        with errors_log_path.open("r", encoding="utf-8", errors="replace") as handle:
            line_buffer: list[str] = []
            for line in handle:
                line_buffer.append(line.rstrip())
                if len(line_buffer) > 1000:
                    line_buffer.pop(0)
            tail_lines = line_buffer
        matches = [line for line in tail_lines if any(token in line for token in ["AttributeError", "ModuleNotFoundError", "Traceback"])][:3]
        if matches:
            errors.extend(matches)
            checks["log_check"] = "FAIL"
        else:
            checks["log_check"] = "PASS"

    checklist_path = repo_root / "tools" / "checklist.py"
    if not checklist_path.exists():
        warnings.append("checklist.py missing; cannot run full validation")

    activity_log_path = repo_root / "tools" / "activity_log.json"
    if not activity_log_path.exists():
        warnings.append("tools/activity_log.json missing; audit chain check skipped")
        checks["audit_chain_check"] = "MISSING"
    else:
        is_valid, message = verify_activity_chain(activity_log_path)
        if is_valid:
            checks["audit_chain_check"] = "PASS"
        else:
            errors.append(message)
            checks["audit_chain_check"] = "FAIL"

    try:
        drift_paths = [
            repo_root / "tools" / "errors.log",
            repo_root / "tools" / "activity_log.json",
            repo_root / "tools" / "latest_context.txt",
        ]
        drift_result = analyze_time_drift(drift_paths)
        drift_status = str(drift_result.get("overall_status", "PASS"))
        checks["time_drift_check"] = {
            "status": drift_status,
            "files_analyzed": len(drift_result.get("files_analyzed", [])),
            "total_timestamps_found": int(drift_result.get("total_timestamps_found", 0)),
            "ambiguous_count": len(drift_result.get("ambiguous_timestamps", [])),
            "invalid_count": len(drift_result.get("invalid_timestamps", [])),
            "out_of_order_count": len(drift_result.get("out_of_order_timestamps", [])),
            "skipped_ambiguous_count": len(drift_result.get("skipped_ambiguous_in_ordering", [])),
        }
        if drift_status == "FAIL":
            errors.append("time_drift_check: invalid or out-of-order timestamps detected")
        elif drift_status == "WARN":
            warnings.append("time_drift_check: ambiguous timestamps detected; ordering skipped for ambiguous entries")
    except Exception as exc:
        checks["time_drift_check"] = {"status": "ERROR", "message": str(exc)}
        errors.append(f"time_drift_check: {exc}")
        warnings.append("time_drift_check: exception prevented drift analysis")

    status = "FAIL" if errors else ("WARN" if warnings else "OK")
    return {
        "timestamp": iso_utc_now(),
        "status": status,
        "checks": {
            "syntax_check": checks["syntax_check"],
            "import_check": checks["import_check"],
            "governance_check": checks["governance_check"],
            "log_check": checks["log_check"],
            "protected_dirs_check": checks["protected_dirs_check"],
            "audit_chain_check": checks["audit_chain_check"],
            "time_drift_check": checks["time_drift_check"],
        },
        "errors": errors,
        "warnings": warnings,
    }


def generate_repair_recommendation(error_details: dict, root_path: Path) -> Path:
    """Create a JSON repair recommendation report without performing any repair."""
    snapshot_timestamp = (
        getattr(sys.modules[__name__], "LAST_INTEGRITY_SNAPSHOT_TS", None)
        or error_details.get("timestamp")
        or iso_utc_now()
    )
    repo_root = root_path.resolve() if root_path.exists() else Path.cwd().resolve()
    tools_dir = repo_root / "tools"
    tools_dir.mkdir(exist_ok=True, parents=True)

    syntax_errors = []
    import_errors = []
    missing_governance = []
    log_errors = []

    for raw_error in error_details.get("errors", []):
        text = str(raw_error)
        if ".py" in text and ":" in text:
            file_part, error_part = text.split(":", 1)
            syntax_errors.append({"file": file_part.strip(), "error": error_part.strip()})
        elif text.startswith("tools.") or text.startswith("tools/"):
            module_name, _, error_part = text.partition(":")
            import_errors.append({"module": module_name.strip(), "error": error_part.strip() or "Import failed"})
        elif any(token in text for token in ["AttributeError", "ModuleNotFoundError", "Traceback"]):
            log_errors.append(text)

    for warning in error_details.get("warnings", []):
        if warning.endswith("missing") or "missing" in warning.lower():
            missing_governance.append(warning.split(" missing", 1)[0].strip())

    analysis = []
    if syntax_errors:
        analysis.append("syntax issues were detected in Python files; review the specific compile failures before any code changes.")
    if import_errors:
        analysis.append("module import failures were detected; verify module paths and dependency availability before re-running the app.")
    if missing_governance:
        analysis.append("governance files are missing or incomplete; restore the required documents before continuing.")
    if log_errors:
        analysis.append("runtime errors were found in the log tail; investigate the exact stack traces before attempting a repair.")
    if not analysis:
        analysis.append("No blocking failures were identified in the integrity check; confirm the status with a repository owner before any action.")

    report = {
        "timestamp": snapshot_timestamp,
        "status": "FAILED",
        "failed_checks": {
            "syntax_errors": syntax_errors,
            "import_errors": import_errors,
            "missing_governance": missing_governance,
            "log_errors": log_errors,
        },
        "repair_recommendation": "DO_NOT_EXECUTE - ARCHITECT_REVIEW_REQUIRED: " + " ".join(analysis),
    }

    report_path = tools_dir / f"integrity_report_{snapshot_timestamp}.json"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(tools_dir), delete=False) as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
        temp_path = Path(handle.name)
    os.replace(temp_path, report_path)
    return report_path


def render_report_generator() -> None:
    st.title("Report Generator")
    st.subheader("Export Architectural Report")
    if st.button("Export Architectural Report"):
        try:
            tree = build_project_tree(ROOT)
            tree_text = "\n".join(render_tree_lines(tree)) or "Project tree is empty."
            rag_output = st.session_state.get("rag_output", "RAG not run in this session")
            error_lines = read_error_lines()[-20:]
            error_text = "\n".join(error_lines) if error_lines else "No errors logged."
            activity_summary = get_activity_summary(last_n=20)

            report_lines = [
                f"Architectural Context Report — Generated at: {iso_utc_now()}",
                "",
                "--- File Tree ---",
                tree_text,
                "",
                "--- RAG Output ---",
                str(rag_output),
                "",
                "--- Latest Errors ---",
                error_text,
                "",
                "--- Recent Activity ---",
                activity_summary,
            ]
            report_text = "\n".join(report_lines)
            LATEST_CONTEXT_PATH.write_text(report_text, encoding="utf-8")
            append_to_activity_log({
                "activity_type": "report_export",
                "status": "success",
                "details": f"Report saved to {LATEST_CONTEXT_PATH}",
            })
            st.success(f"Architectural report exported to {LATEST_CONTEXT_PATH}")
        except Exception as exc:
            msg = f"Report export failed: {exc}"
            append_to_errors_log(msg)
            append_to_activity_log({"activity_type": "report_export", "status": "failed", "details": msg})
            st.error(msg)

    if LATEST_CONTEXT_PATH.exists():
        st.caption(f"Latest report exists at: {LATEST_CONTEXT_PATH}")
        with LATEST_CONTEXT_PATH.open("r", encoding="utf-8") as handle:
            st.code(handle.read(), language="text")
    else:
        st.info("No report generated yet.")


def initialize_session_state() -> None:
    if "rag_output" not in st.session_state:
        st.session_state["rag_output"] = ""
    if "memory_snapshot_data" not in st.session_state:
        st.session_state["memory_snapshot_data"] = None
    if "memory_snapshot_filename" not in st.session_state:
        st.session_state["memory_snapshot_filename"] = "memory_snapshot_latest.json"
    if "memory_snapshot_content" not in st.session_state:
        st.session_state["memory_snapshot_content"] = ""
    if "last_integrity_result" not in st.session_state:
        st.session_state["last_integrity_result"] = {}
    if "last_integrity_timestamp" not in st.session_state:
        st.session_state["last_integrity_timestamp"] = ""
    if "last_repair_report_path" not in st.session_state:
        st.session_state["last_repair_report_path"] = ""
    if "app_started_logged" not in st.session_state:
        append_to_activity_log({
            "activity_type": "app_started",
            "status": "success",
            "details": "Application started",
        })
        st.session_state["app_started_logged"] = True
    if "lockdown_active" not in st.session_state:
        st.session_state["lockdown_active"] = False


def main() -> None:
    st.set_page_config(
        page_title="Developer Command Center",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    initialize_session_state()
    ensure_tools_dir()

    if not ACTIVITY_LOG_PATH.exists():
        write_json_file(ACTIVITY_LOG_PATH, [])
    if not ERROR_LOG_PATH.exists():
        ERROR_LOG_PATH.touch()

    if st.session_state.get("lockdown_active"):
        st.error("Emergency stop active. Safe lockdown engaged.")
        st.title("Operational Safety Lockdown")
        st.markdown("Runtime action has been suspended after a circuit-breaker event.")
        st.button("Emergency lock engaged", disabled=True)
        return

    st.sidebar.title("Developer Command Center")
    st.sidebar.caption("Governance, monitoring, and system control")
    st.sidebar.markdown("---")
    st.sidebar.info("EnterpriseGuard Governance Layer Active\n\nProtected areas (adie/, intelligence/) are strictly isolated.")
    st.sidebar.markdown("---")
    page = st.sidebar.radio("Navigation", ["Dashboard", "File Tree", "RAG Console", "Activity Log", "Report Generator", "Memory Snapshot", "System Controls"])
    st.sidebar.markdown("---")
    if st.sidebar.button("EMERGENCY STOP / CIRCUIT BREAKER"):
        append_to_activity_log({
            "activity_type": "command_center_action",
            "status": "emergency_stop",
            "details": "Circuit breaker triggered",
        })
        append_to_errors_log("EMERGENCY STOP / CIRCUIT BREAKER activated from Developer Command Center")
        st.session_state["lockdown_active"] = True
        st.rerun()

    if page == "Dashboard":
        render_dashboard()
    elif page == "File Tree":
        render_file_tree()
    elif page == "RAG Console":
        render_rag_console()
    elif page == "Activity Log":
        render_activity_log()
    elif page == "Report Generator":
        render_report_generator()
    elif page == "Memory Snapshot":
        render_memory_snapshot()
    elif page == "System Controls":
        render_system_integrity()

    st.markdown("---")
    st.caption("Developer Command Center v1.0 • Governance enforced • Protected directories remain outside scope.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        append_to_errors_log(f"Unhandled internal application error: {exc}")
        st.error("An unexpected internal error occurred. Details were written to the errors log.")
        st.code(traceback.format_exc(), language="text")
