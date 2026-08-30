## 0. STARTUP PROCEDURE (MANDATORY)
Before executing any task, you MUST:
- Read `.claude/instructions.md` if present, and confirm internally that you are operating under this protocol.
- If the file is missing or unreadable, STOP and ask the developer to provide it.
- Do NOT rely on memory. Re-read the file at the start of each new session.
# EnterpriseGuard – Mandatory Execution Protocol for Claude Code

You are operating in a defense-grade workspace. Before executing any command or modifying any file, you MUST apply ALL of the following layers:

## 1. Security
- Never touch `adie/` or `intelligence/` (no reading, writing, or traversal).
- No hardcoded secrets, no unsafe execution (`eval`, `exec`, unvalidated subprocess).
- Use atomic writes (write to temp file then `os.replace`) for any file modification.

## 2. Governance
- Any new tool or modification must be registered in `tools/checklist.py`.
- All decisions must be documented in `tools/DECISIONS_LOG.md` after successful execution.

## 3. Error Handling
- Test against missing files, malformed JSON, denied permissions, timeouts.
- Stop immediately on any unexpected condition and return a non-zero exit code with a clear error message.
- Never crash silently.

## 4. Performance
- For large logs (100k+ entries), use streaming or lazy loading; avoid loading entire files into memory unnecessarily.

## 5. Syntax
- Run a mental `compile()` check for any Python code you produce or modify.
- Ensure all variables are defined before use, functions return documented types.

## 6. Integration
- Do not introduce new dependencies unless explicitly approved.
- Ensure compatibility with existing tools (`checklist.py`, `command_center.py`, `alerts_monitor.py`).
- Use correct exit codes: 0=HEALTHY, 1=NOTICE, 2=ALERT.

## 7. SIEM Compatibility
- All timestamps must be UTC ISO 8601 (`YYYY-MM-DDTHH:MM:SSZ`).
- JSON outputs must include fields: `timestamp`, `event_type`, `severity`, `source`, `message`, `metadata`, `siem_compatible: true`.

## 8. Loop Prevention
- When logging to `tools/activity_log.json`, tag entries with correct `activity_type`.
- Exclude your own generated entries from analysis in the same session to prevent infinite loops.

## 9. Documentation
- Include docstrings and inline comments for complex logic.
- Provide a concise accomplishment report after completing a task.

## 10. No Regression
- Do not break existing functionality.
- Check for name collisions or changed signatures before modifying files.
- If modifying an existing file, verify all previous features remain intact.

## Additional Mandatory Practices:
- Perform Threat Modeling and Failure Analysis before implementing any change.
- Provide Trade-off Justification (why your approach is better than alternatives).
- Align with compliance frameworks (SOC 2, ISO 27001) where relevant.

## Output Format:
After completing a task, output a JSON summary with textual proofs for each layer:

```json
{
  "action": "what was done",
  "files_modified": [],
  "checklist_exit_code": 0,
  "protected_dirs_untouched": true,
  "errors": [],
  "validation_summary": {
    "security": "explain how security is ensured",
    "governance": "explain governance compliance",
    "error_handling": "explain error handling",
    "performance": "explain performance considerations",
    "syntax": "explain syntax verification",
    "integration": "explain integration",
    "siem": "explain SIEM compliance",
    "loop_prevention": "explain loop prevention",
    "documentation": "explain documentation",
    "no_regression": "explain no regression"
  }
}
