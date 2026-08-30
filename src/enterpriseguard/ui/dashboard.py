"""
EnterpriseGuard - ADIE Security Operations Dashboard
=====================================================

Presentation layer for the EnterpriseGuard / ADIE control plane.

Architecture
------------

    Browser
       |
       v
    Streamlit
       |
       v
    DashboardAPI
       |
       v
    DashboardService
       |
       +-------------------------+
       |                         |
       v                         v
ReportingService        DecisionOrchestrator


Design Principles
-----------------

This module is strictly a presentation layer.

It MUST NOT:

- perform threat detection
- access Detector directly
- access ModelManager
- access ModelLoader
- access ModelRegistry
- access training components
- execute security actions
- execute shell commands
- perform network operations
- modify security state
- make policy decisions
- bypass DashboardAPI
- access lower intelligence services directly

The UI consumes the public DashboardAPI boundary only.


Execution
---------

From the project ``src`` directory:

    streamlit run enterpriseguard\\ui\\dashboard.py

Self-test:

    python -m enterpriseguard.ui.dashboard


API Contract
------------

DashboardAPI methods return:

    {
        "success": bool,
        "data": Any,
        "timestamp": str,
    }

or:

    {
        "success": False,
        "error": str,
        "timestamp": str,
    }

Health specifically returns data similar to:

    {
        "success": True,
        "data": {
            "status": "healthy",
            "service": "dashboard_api",
            "version": "1.0.0",
        },
        "timestamp": "...",
    }


This module deliberately adapts to the API contract rather than
assuming implementation-specific internal structures.
"""

from __future__ import annotations

# ============================================================================
# Standard library
# ============================================================================

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping


# ============================================================================
# Import bootstrap
# ============================================================================

# Streamlit executes this file directly. Therefore the project source root
# must be explicitly available before importing enterpriseguard.
#
# dashboard.py
#     -> ui
#     -> enterpriseguard
#     -> src
#
# parents[2] = project src directory.

_PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


# ============================================================================
# Third-party
# ============================================================================

import streamlit as st


# ============================================================================
# Application boundary
# ============================================================================

from enterpriseguard.api.dashboard_api import DashboardAPI
from enterpriseguard.intelligence.dashboard_service import DashboardService
from enterpriseguard.intelligence.decision_orchestrator import (
    DecisionOrchestrator,
)
from enterpriseguard.intelligence.reporting_service import ReportingService


# ============================================================================
# Singleton ReportingService (مفتاح حل المشكلة)
# ============================================================================

_reporting_service = None

def get_reporting_service():
    global _reporting_service
    if _reporting_service is None:
        _reporting_service = ReportingService()
    return _reporting_service


# ============================================================================
# Application metadata
# ============================================================================

APP_NAME = "EnterpriseGuard"

APP_SHORT_NAME = "ADIE"

APP_PRODUCT = "Adaptive Defense Intelligence Engine"

APP_VERSION = "1.0.0"

APP_DESCRIPTION = (
    "Defensive security intelligence and decision-support control plane."
)


# ============================================================================
# Page configuration
# ============================================================================

st.set_page_config(
    page_title=f"{APP_NAME} — {APP_SHORT_NAME}",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================================
# Visual system
# ============================================================================

DASHBOARD_CSS = """
<style>

    /* ================================================================ */
    /* Global                                                          */
    /* ================================================================ */

    .block-container {
        max-width: 1500px;
        padding-top: 1.4rem;
        padding-bottom: 3rem;
    }

    [data-testid="stMetric"] {
        border: 1px solid rgba(128, 128, 128, 0.20);
        border-radius: 14px;
        padding: 0.85rem;
    }

    /* ================================================================ */
    /* Hero                                                            */
    /* ================================================================ */

    .eg-hero {
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 18px;
        padding: 1.6rem 1.8rem;
        margin-bottom: 1.2rem;
    }

    .eg-brand {
        font-size: 2.1rem;
        font-weight: 750;
        letter-spacing: -0.03em;
        margin: 0;
    }

    .eg-product {
        font-size: 1rem;
        opacity: 0.78;
        margin-top: 0.35rem;
    }

    .eg-description {
        font-size: 0.86rem;
        opacity: 0.65;
        margin-top: 0.65rem;
    }

    .eg-badge {
        display: inline-block;
        margin-top: 0.9rem;
        padding: 0.3rem 0.65rem;
        border-radius: 999px;
        border: 1px solid rgba(128, 128, 128, 0.25);
        font-size: 0.72rem;
        font-weight: 600;
    }

    /* ================================================================ */
    /* Sections                                                        */
    /* ================================================================ */

    .eg-section {
        font-size: 1.15rem;
        font-weight: 700;
        margin-top: 0.7rem;
        margin-bottom: 0.7rem;
    }

    .eg-section-subtitle {
        font-size: 0.78rem;
        opacity: 0.62;
        margin-top: -0.35rem;
        margin-bottom: 0.8rem;
    }

    /* ================================================================ */
    /* Operational cards                                                */
    /* ================================================================ */

    .eg-operational {
        border: 1px solid rgba(128, 128, 128, 0.20);
        border-radius: 14px;
        padding: 0.9rem;
        min-height: 100px;
    }

    .eg-operational-label {
        font-size: 0.72rem;
        opacity: 0.62;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    .eg-operational-value {
        font-size: 1.2rem;
        font-weight: 700;
        margin-top: 0.35rem;
    }

    /* ================================================================ */
    /* Queue items                                                     */
    /* ================================================================ */

    .eg-queue {
        border: 1px solid rgba(128, 128, 128, 0.20);
        border-radius: 12px;
        padding: 0.85rem;
        margin-bottom: 0.55rem;
    }

    .eg-queue-title {
        font-weight: 650;
        font-size: 0.9rem;
    }

    .eg-queue-meta {
        font-size: 0.74rem;
        opacity: 0.65;
        margin-top: 0.25rem;
    }

    /* ================================================================ */
    /* Footer                                                          */
    /* ================================================================ */

    .eg-footer {
        margin-top: 2.2rem;
        padding-top: 1rem;
        border-top: 1px solid rgba(128, 128, 128, 0.18);
        text-align: center;
        font-size: 0.72rem;
        opacity: 0.58;
    }

</style>
"""


# ============================================================================
# Utility functions
# ============================================================================


def _utc_now() -> str:
    """Return the current UTC timestamp."""

    return datetime.now(
        timezone.utc
    ).isoformat()


def _safe_int(
    value: Any,
    default: int = 0,
) -> int:
    """Safely convert a value to int."""

    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """Safely convert a value to float."""

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_mapping(
    value: Any,
) -> dict[str, Any]:
    """Return a plain dictionary when value is mapping-like."""

    if isinstance(value, Mapping):
        return dict(value)

    return {}


def _safe_list(
    value: Any,
) -> list[Any]:
    """Return a safe list representation."""

    if isinstance(value, list):
        return list(value)

    if isinstance(value, tuple):
        return list(value)

    return []


def _humanize(
    value: Any,
) -> str:
    """Convert internal identifiers into readable labels."""

    if value is None:
        return "Unknown"

    text = str(value).strip()

    if not text:
        return "Unknown"

    return text.replace(
        "_",
        " ",
    ).replace(
        "-",
        " ",
    ).title()


def _format_number(
    value: Any,
) -> str:
    """Format a numeric dashboard value."""

    try:
        number = float(value)
    except (TypeError, ValueError):
        return "0"

    if number.is_integer():
        return f"{int(number):,}"

    return f"{number:,.2f}"


def _format_timestamp(
    value: Any,
) -> str:
    """Return a compact human-readable timestamp."""

    if value is None:
        return "—"

    text = str(value)

    if len(text) > 34:
        return text[:34] + "…"

    return text


def _format_percentage(
    value: Any,
) -> str:
    """Format normalized or percentage values."""

    try:
        number = float(value)
    except (TypeError, ValueError):
        return "—"

    if 0.0 <= number <= 1.0:
        return f"{number * 100:.1f}%"

    if 1.0 < number <= 100.0:
        return f"{number:.1f}%"

    return "—"


# ============================================================================
# Dashboard API construction (معدل)
# ============================================================================


@st.cache_resource
def build_dashboard_api() -> DashboardAPI:
    """
    Construct the canonical dashboard dependency graph.

    UI
     |
     v
    DashboardAPI
     |
     v
    DashboardService
     |
     +--> ReportingService
     |
     +--> DecisionOrchestrator
    """

    reporting_service = get_reporting_service()

    decision_orchestrator = DecisionOrchestrator()

    dashboard_service = DashboardService(
        reporting_service=reporting_service,
        decision_orchestrator=decision_orchestrator,
    )

    return DashboardAPI(
        dashboard_service=dashboard_service,
    )


# ============================================================================
# API contract helpers
# ============================================================================


def _api_success(
    response: Any,
) -> bool:
    """Return whether a DashboardAPI response is successful."""

    return (
        isinstance(response, Mapping)
        and response.get("success") is True
    )


def _api_data(
    response: Any,
    default: Any = None,
) -> Any:
    """
    Extract data from the DashboardAPI envelope.

    Contract:

        {
            "success": True,
            "data": ...,
            "timestamp": ...
        }
    """

    if not _api_success(response):
        return default

    return response.get(
        "data",
        default,
    )


def _api_error(
    response: Any,
) -> str | None:
    """Extract an API error safely."""

    if not isinstance(response, Mapping):
        return "Invalid DashboardAPI response."

    error = response.get("error")

    if error is None:
        return None

    return str(error)


def _execute_api_call(
    operation: Callable[[], Any],
    *,
    default: Any,
) -> tuple[Any, str | None]:
    """
    Execute one DashboardAPI operation.

    The presentation layer never allows service exceptions
    to terminate the complete dashboard.
    """

    try:
        response = operation()

    except Exception as exc:
        return default, str(exc)

    if not _api_success(response):
        return default, _api_error(response)

    return _api_data(
        response,
        default,
    ), None


# ============================================================================
# Health contract
# ============================================================================


def _extract_health_contract(
    health_response: Any,
) -> dict[str, Any]:
    """
    Normalize DashboardAPI.health().

    The API health response is an envelope:

        {
            "success": True,
            "data": {
                "status": "...",
                "service": "...",
                "version": "..."
            }
        }

    This function intentionally validates the real public contract.
    """

    data = _safe_mapping(
        _api_data(
            health_response,
            {},
        )
    )

    return {
        "status": data.get(
            "status",
            "unknown",
        ),
        "service": data.get(
            "service",
            "unknown",
        ),
        "version": data.get(
            "version",
            "unknown",
        ),
    }


# ============================================================================
# Header
# ============================================================================


def render_header() -> None:
    """Render the primary ADIE dashboard header."""

    st.markdown(
        DASHBOARD_CSS,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="eg-hero">

            <div class="eg-brand">
                🛡️ {APP_NAME}
            </div>

            <div class="eg-product">
                {APP_PRODUCT} ({APP_SHORT_NAME})
            </div>

            <div class="eg-description">
                {APP_DESCRIPTION}
            </div>

            <div class="eg-badge">
                CONTROL PLANE · v{APP_VERSION}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================================
# Sidebar
# ============================================================================


def render_sidebar(
    api: DashboardAPI,
) -> bool:
    """
    Render dashboard controls.

    Returns:
        True when manual refresh was requested.
    """

    with st.sidebar:

        st.markdown(
            "## 🛡️ EnterpriseGuard"
        )

        st.caption(
            "Adaptive Defense Intelligence Engine"
        )

        st.divider()

        st.markdown(
            "### Operations"
        )

        refresh_requested = st.button(
            "↻ Refresh dashboard",
            use_container_width=True,
        )

        st.divider()

        st.markdown(
            "### API Boundary"
        )

        st.caption(
            "DashboardAPI"
        )

        st.caption(
            f"Contract v{APP_VERSION}"
        )

        st.divider()

        st.markdown(
            "### Runtime"
        )

        st.caption(
            f"UTC: {_utc_now()}"
        )

        st.divider()

        st.markdown(
            "### Architecture"
        )

        st.code(
            "Browser\n"
            "   ↓\n"
            "Streamlit UI\n"
            "   ↓\n"
            "DashboardAPI\n"
            "   ↓\n"
            "DashboardService\n"
            "   ↓\n"
            "Reporting / Decision",
            language="text",
        )

    return refresh_requested


# ============================================================================
# System status
# ============================================================================


def render_system_status(
    status: Mapping[str, Any],
) -> None:
    """Render operational system status."""

    st.markdown(
        '<div class="eg-section">Operational State</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="eg-section-subtitle">'
        "Current state exposed by the dashboard control boundary."
        "</div>",
        unsafe_allow_html=True,
    )

    platform_status = status.get(
        "status",
        "unknown",
    )

    reporting_status = status.get(
        "reporting_service",
        status.get(
            "reporting",
            "unknown",
        ),
    )

    decision_status = status.get(
        "decision_orchestrator",
        status.get(
            "decision",
            "unknown",
        ),
    )

    timestamp = status.get(
        "last_refresh",
        status.get(
            "timestamp",
        ),
    )

    cols = st.columns(4)

    with cols[0]:
        st.metric(
            "Platform",
            _humanize(platform_status),
        )

    with cols[1]:
        st.metric(
            "Reporting",
            _humanize(reporting_status),
        )

    with cols[2]:
        st.metric(
            "Decision Engine",
            _humanize(decision_status),
        )

    with cols[3]:
        st.metric(
            "Last Refresh",
            _format_timestamp(timestamp),
        )


# ============================================================================
# Summary metrics
# ============================================================================


def render_summary_metrics(
    metrics: Mapping[str, Any],
) -> None:
    """Render high-level security metrics."""

    st.markdown(
        '<div class="eg-section">Security Overview</div>',
        unsafe_allow_html=True,
    )

    alert_count = _safe_int(
        metrics.get("alert_count")
    )

    escalation_count = _safe_int(
        metrics.get("escalation_count")
    )

    ignored_count = _safe_int(
        metrics.get("ignored_count")
    )

    total_records = _safe_int(
        metrics.get("total_records")
    )

    common_decision = metrics.get(
        "most_common_decision",
        metrics.get(
            "common_decision",
            "unknown",
        ),
    )

    cols = st.columns(5)

    with cols[0]:
        st.metric(
            "Alerts",
            _format_number(alert_count),
        )

    with cols[1]:
        st.metric(
            "Escalations",
            _format_number(escalation_count),
        )

    with cols[2]:
        st.metric(
            "Ignored",
            _format_number(ignored_count),
        )

    with cols[3]:
        st.metric(
            "Total Records",
            _format_number(total_records),
        )

    with cols[4]:
        st.metric(
            "Common Decision",
            _humanize(common_decision),
        )


# ============================================================================
# Queue helpers
# ============================================================================


def _extract_decision(
    item: Any,
) -> str:
    """Extract decision/action from a queue record."""

    if not isinstance(item, Mapping):
        return "unknown"

    return str(
        item.get(
            "decision",
            item.get(
                "action",
                "unknown",
            ),
        )
    )


def _extract_queue_type(
    item: Any,
) -> str:
    """Extract queue type."""

    if not isinstance(item, Mapping):
        return "unknown"

    return str(
        item.get(
            "queue_type",
            "unknown",
        )
    )


def render_queue(
    title: str,
    items: list[Any],
    *,
    empty_message: str,
) -> None:
    """Render a queue of dashboard decisions."""

    st.markdown(
        f'<div class="eg-section">{title}</div>',
        unsafe_allow_html=True,
    )

    if not items:
        st.info(
            empty_message
        )
        return

    for index, item in enumerate(
        items,
        start=1,
    ):

        data = (
            dict(item)
            if isinstance(item, Mapping)
            else {"value": str(item)}
        )

        decision = _extract_decision(
            data
        )

        queue_type = _extract_queue_type(
            data
        )

        with st.container(
            border=True,
        ):

            cols = st.columns(
                [0.55, 2.0, 2.0, 1.2]
            )

            with cols[0]:
                st.caption(
                    f"#{index}"
                )

            with cols[1]:
                st.write(
                    f"**Decision:** {_humanize(decision)}"
                )

            with cols[2]:
                st.write(
                    f"**Queue:** {_humanize(queue_type)}"
                )

            with cols[3]:

                queued = data.get(
                    "queued"
                )

                if queued is True:
                    st.success(
                        "Queued"
                    )

                elif queued is False:
                    st.caption(
                        "Not queued"
                    )

                else:
                    st.caption(
                        "State unknown"
                    )

            additional = {
                key: value
                for key, value in data.items()
                if key not in {
                    "decision",
                    "action",
                    "queue_type",
                    "queued",
                }
            }

            if additional:

                with st.expander(
                    "Record details",
                    expanded=False,
                ):
                    st.json(
                        additional
                    )


# ============================================================================
# Recent activity
# ============================================================================


def render_recent_activity(
    activity: list[Any],
) -> None:
    """Render recent dashboard activity."""

    st.markdown(
        '<div class="eg-section">Recent Activity</div>',
        unsafe_allow_html=True,
    )

    if not activity:
        st.info(
            "No recent activity is currently available."
        )
        return

    for index, item in enumerate(
        activity,
        start=1,
    ):

        data = (
            dict(item)
            if isinstance(item, Mapping)
            else {"value": str(item)}
        )

        decision = data.get(
            "decision",
            data.get(
                "action",
                "unknown",
            ),
        )

        timestamp = data.get(
            "timestamp",
            data.get(
                "created_at",
                data.get(
                    "time"
                ),
            ),
        )

        with st.container(
            border=True,
        ):

            cols = st.columns(
                [0.55, 2.0, 2.0, 4.0]
            )

            with cols[0]:
                st.caption(
                    str(index)
                )

            with cols[1]:
                st.write(
                    f"**{_humanize(decision)}**"
                )

            with cols[2]:
                st.caption(
                    _format_timestamp(
                        timestamp
                    )
                )

            with cols[3]:

                details = {
                    key: value
                    for key, value in data.items()
                    if key not in {
                        "decision",
                        "action",
                        "timestamp",
                        "created_at",
                        "time",
                    }
                }

                if details:
                    st.json(
                        details
                    )
                else:
                    st.caption(
                        "No additional metadata."
                    )


# ============================================================================
# Latest decision
# ============================================================================


def render_latest_decision(
    metrics: Mapping[str, Any],
) -> None:
    """Render the latest available decision."""

    last_result = metrics.get(
        "last_result"
    )

    if not isinstance(
        last_result,
        Mapping,
    ):
        return

    st.markdown(
        '<div class="eg-section">Latest Decision</div>',
        unsafe_allow_html=True,
    )

    decision = last_result.get(
        "decision",
        "unknown",
    )

    queued = last_result.get(
        "queued"
    )

    queue_type = last_result.get(
        "queue_type",
        "unknown",
    )

    confidence = last_result.get(
        "confidence"
    )

    cols = st.columns(4)

    with cols[0]:
        st.metric(
            "Decision",
            _humanize(decision),
        )

    with cols[1]:

        if queued is True:
            queued_value = "YES"
        elif queued is False:
            queued_value = "NO"
        else:
            queued_value = "—"

        st.metric(
            "Queued",
            queued_value,
        )

    with cols[2]:
        st.metric(
            "Queue",
            _humanize(queue_type),
        )

    with cols[3]:

        if confidence is not None:
            st.metric(
                "Confidence",
                _format_percentage(
                    confidence
                ),
            )
        else:
            st.metric(
                "Confidence",
                "—",
            )

    with st.expander(
        "Latest decision details",
        expanded=False,
    ):
        st.json(
            dict(last_result)
        )


# ============================================================================
# Telemetry
# ============================================================================


def _find_latency_values(
    source: Any,
) -> list[float]:
    """
    Recursively locate latency/duration/elapsed telemetry.

    This function is presentation-only.
    """

    values: list[float] = []

    if isinstance(source, Mapping):

        for key, value in source.items():

            normalized = str(
                key
            ).lower()

            if any(
                token in normalized
                for token in (
                    "latency",
                    "duration",
                    "elapsed",
                )
            ):

                try:
                    values.append(
                        float(value)
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    pass

            else:

                values.extend(
                    _find_latency_values(
                        value
                    )
                )

    elif isinstance(source, list):

        for item in source:

            values.extend(
                _find_latency_values(
                    item
                )
            )

    elif isinstance(source, tuple):

        for item in source:

            values.extend(
                _find_latency_values(
                    item
                )
            )

    return values


def render_telemetry(
    snapshot: Mapping[str, Any],
) -> None:
    """Render runtime telemetry exposed by the API snapshot."""

    st.markdown(
        '<div class="eg-section">Runtime Telemetry</div>',
        unsafe_allow_html=True,
    )

    latencies = _find_latency_values(
        snapshot
    )

    if not latencies:

        st.caption(
            "No latency telemetry is currently exposed."
        )

        return

    average = (
        sum(latencies)
        / len(latencies)
    )

    minimum = min(
        latencies
    )

    maximum = max(
        latencies
    )

    cols = st.columns(4)

    with cols[0]:
        st.metric(
            "Samples",
            _format_number(
                len(latencies)
            ),
        )

    with cols[1]:
        st.metric(
            "Average",
            f"{average:.3f}",
        )

    with cols[2]:
        st.metric(
            "Minimum",
            f"{minimum:.3f}",
        )

    with cols[3]:
        st.metric(
            "Maximum",
            f"{maximum:.3f}",
        )


# ============================================================================
# Snapshot
# ============================================================================


def render_raw_snapshot(
    snapshot: Mapping[str, Any],
) -> None:
    """Render the raw dashboard snapshot for diagnostics."""

    with st.expander(
        "Developer Diagnostics",
        expanded=False,
    ):

        if snapshot:
            st.json(
                dict(snapshot)
            )
        else:
            st.caption(
                "Snapshot is empty."
            )


# ============================================================================
# Data loading
# ============================================================================


def load_dashboard_data(
    api: DashboardAPI,
) -> dict[str, Any]:
    """
    Load all dashboard information exclusively through DashboardAPI.
    """

    status, status_error = _execute_api_call(
        api.get_system_status,
        default={},
    )

    alerts, alerts_error = _execute_api_call(
        api.get_alerts,
        default=[],
    )

    escalations, escalations_error = _execute_api_call(
        api.get_escalations,
        default=[],
    )

    activity, activity_error = _execute_api_call(
        lambda: api.get_recent_activity(
            limit=10
        ),
        default=[],
    )

    summary, summary_error = _execute_api_call(
        api.get_summary_metrics,
        default={},
    )

    snapshot, snapshot_error = _execute_api_call(
        api.get_snapshot,
        default={},
    )

    errors = [
        error
        for error in (
            status_error,
            alerts_error,
            escalations_error,
            activity_error,
            summary_error,
            snapshot_error,
        )
        if error
    ]

    return {
        "system_status": _safe_mapping(
            status
        ),
        "alerts": _safe_list(
            alerts
        ),
        "escalations": _safe_list(
            escalations
        ),
        "recent_activity": _safe_list(
            activity
        ),
        "summary_metrics": _safe_mapping(
            summary
        ),
        "snapshot": _safe_mapping(
            snapshot
        ),
        "errors": errors,
    }


# ============================================================================
# Main application
# ============================================================================


def main() -> None:
    """Run the Streamlit dashboard."""

    render_header()

    # ------------------------------------------------------------------------
    # API initialization
    # ------------------------------------------------------------------------

    try:

        api = build_dashboard_api()

    except Exception as exc:

        st.error(
            "Dashboard API initialization failed."
        )

        with st.expander(
            "Initialization diagnostics",
            expanded=True,
        ):
            st.exception(
                exc
            )

        return

    # ------------------------------------------------------------------------
    # Sidebar
    # ------------------------------------------------------------------------

    refresh_requested = render_sidebar(
        api
    )

    if refresh_requested:

        st.cache_resource.clear()

        st.rerun()

    # ------------------------------------------------------------------------
    # API health
    # ------------------------------------------------------------------------

    health_response = api.health()

    health = _extract_health_contract(
        health_response
    )

    health_ok = _api_success(
        health_response
    )

    if health_ok:

        health_status = str(
            health.get(
                "status",
                "unknown",
            )
        )

        health_service = str(
            health.get(
                "service",
                "unknown",
            )
        )

        health_version = str(
            health.get(
                "version",
                "unknown",
            )
        )

        st.caption(
            "API "
            f"● {_humanize(health_status)}"
            " · "
            f"{health_service}"
            " · "
            f"v{health_version}"
        )

    else:

        st.warning(
            "Dashboard API health contract reported an error."
        )

    # ------------------------------------------------------------------------
    # Dashboard data
    # ------------------------------------------------------------------------

    data = load_dashboard_data(
        api
    )

    errors = data[
        "errors"
    ]

    if errors:

        with st.expander(
            "Dashboard API warnings",
            expanded=False,
        ):

            for error in errors:

                st.warning(
                    str(error)
                )

    # ------------------------------------------------------------------------
    # Extract data
    # ------------------------------------------------------------------------

    status = data[
        "system_status"
    ]

    alerts = data[
        "alerts"
    ]

    escalations = data[
        "escalations"
    ]

    activity = data[
        "recent_activity"
    ]

    summary = data[
        "summary_metrics"
    ]

    snapshot = data[
        "snapshot"
    ]

    # ------------------------------------------------------------------------
    # Operational state
    # ------------------------------------------------------------------------

    render_system_status(
        status
    )

    st.divider()

    # ------------------------------------------------------------------------
    # Security overview
    # ------------------------------------------------------------------------

    render_summary_metrics(
        summary
    )

    st.divider()

    # ------------------------------------------------------------------------
    # Queues
    # ------------------------------------------------------------------------

    left, right = st.columns(
        2
    )

    with left:

        render_queue(
            "Alert Queue",
            alerts,
            empty_message=(
                "No alert decisions are currently queued."
            ),
        )

    with right:

        render_queue(
            "Escalation Queue",
            escalations,
            empty_message=(
                "No escalation decisions are currently queued."
            ),
        )

    st.divider()

    # ------------------------------------------------------------------------
    # Latest decision
    # ------------------------------------------------------------------------

    render_latest_decision(
        summary
    )

    # ------------------------------------------------------------------------
    # Activity
    # ------------------------------------------------------------------------

    render_recent_activity(
        activity
    )

    st.divider()

    # ------------------------------------------------------------------------
    # Telemetry
    # ------------------------------------------------------------------------

    render_telemetry(
        snapshot
    )

    # ------------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------------

    render_raw_snapshot(
        snapshot
    )

    # ------------------------------------------------------------------------
    # Footer
    # ------------------------------------------------------------------------

    st.markdown(
        f"""
        <div class="eg-footer">
            {APP_NAME}
            · {APP_SHORT_NAME}
            · Security Operations Dashboard
            · API v{APP_VERSION}
            · {datetime.now(timezone.utc).year}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================================
# Self-test
# ============================================================================


def self_test() -> bool:
    """
    Validate the presentation layer and DashboardAPI contract.

    Important:
        The self-test validates the real API envelope.

    It does NOT assume that DashboardService returns a particular
    implementation-specific status such as "OPERATIONAL".
    """

    # ------------------------------------------------------------------------
    # Test 1: project root
    # ------------------------------------------------------------------------

    assert _PROJECT_ROOT.exists(), (
        "Project root does not exist."
    )

    assert str(
        _PROJECT_ROOT
    ) in sys.path, (
        "Project root is not available in sys.path."
    )

    # ------------------------------------------------------------------------
    # Test 2: API construction
    # ------------------------------------------------------------------------

    api = build_dashboard_api()

    assert isinstance(
        api,
        DashboardAPI,
    ), (
        "Dashboard API construction failed."
    )

    # ------------------------------------------------------------------------
    # Test 3: health contract
    # ------------------------------------------------------------------------

    health_response = api.health()

    assert isinstance(
        health_response,
        dict,
    ), (
        "DashboardAPI health response must be a dictionary."
    )

    assert health_response.get(
        "success"
    ) is True, (
        "DashboardAPI health success contract failed."
    )

    health_data = health_response.get(
        "data"
    )

    assert isinstance(
        health_data,
        dict,
    ), (
        "DashboardAPI health data contract failed."
    )

    assert isinstance(
        health_data.get("status"),
        str,
    ), (
        "DashboardAPI health status contract failed."
    )

    assert isinstance(
        health_data.get("service"),
        str,
    ), (
        "DashboardAPI health service contract failed."
    )

    assert isinstance(
        health_data.get("version"),
        str,
    ), (
        "DashboardAPI health version contract failed."
    )

    # ------------------------------------------------------------------------
    # Test 4: system status
    # ------------------------------------------------------------------------

    status_response = api.get_system_status()

    assert isinstance(
        status_response,
        dict,
    ), (
        "System status response is not a dictionary."
    )

    assert status_response.get(
        "success"
    ) is True, (
        "System status API contract failed."
    )

    assert isinstance(
        status_response.get("data"),
        dict,
    ), (
        "System status data contract failed."
    )

    # ------------------------------------------------------------------------
    # Test 5: alerts
    # ------------------------------------------------------------------------

    alerts_response = api.get_alerts()

    assert isinstance(
        alerts_response,
        dict,
    ), (
        "Alerts response is not a dictionary."
    )

    assert alerts_response.get(
        "success"
    ) is True, (
        "Alerts API contract failed."
    )

    assert isinstance(
        alerts_response.get("data"),
        list,
    ), (
        "Alerts data contract failed."
    )

    # ------------------------------------------------------------------------
    # Test 6: escalations
    # ------------------------------------------------------------------------

    escalations_response = api.get_escalations()

    assert isinstance(
        escalations_response,
        dict,
    ), (
        "Escalations response is not a dictionary."
    )

    assert escalations_response.get(
        "success"
    ) is True, (
        "Escalations API contract failed."
    )

    assert isinstance(
        escalations_response.get("data"),
        list,
    ), (
        "Escalations data contract failed."
    )

    # ------------------------------------------------------------------------
    # Test 7: activity
    # ------------------------------------------------------------------------

    activity_response = api.get_recent_activity(
        limit=10
    )

    assert isinstance(
        activity_response,
        dict,
    ), (
        "Activity response is not a dictionary."
    )

    assert activity_response.get(
        "success"
    ) is True, (
        "Activity API contract failed."
    )

    assert isinstance(
        activity_response.get("data"),
        list,
    ), (
        "Activity data contract failed."
    )

    # ------------------------------------------------------------------------
    # Test 8: summary
    # ------------------------------------------------------------------------

    summary_response = api.get_summary_metrics()

    assert isinstance(
        summary_response,
        dict,
    ), (
        "Summary response is not a dictionary."
    )

    assert summary_response.get(
        "success"
    ) is True, (
        "Summary API contract failed."
    )

    assert isinstance(
        summary_response.get("data"),
        dict,
    ), (
        "Summary data contract failed."
    )

    # ------------------------------------------------------------------------
    # Test 9: snapshot
    # ------------------------------------------------------------------------

    snapshot_response = api.get_snapshot()

    assert isinstance(
        snapshot_response,
        dict,
    ), (
        "Snapshot response is not a dictionary."
    )

    assert snapshot_response.get(
        "success"
    ) is True, (
        "Snapshot API contract failed."
    )

    assert isinstance(
        snapshot_response.get("data"),
        dict,
    ), (
        "Snapshot data contract failed."
    )

    # ------------------------------------------------------------------------
    # Test 10: response helpers
    # ------------------------------------------------------------------------

    fake_success = {
        "success": True,
        "data": {
            "test": True,
        },
        "timestamp": _utc_now(),
    }

    assert _api_success(
        fake_success
    ) is True

    assert _api_data(
        fake_success
    ) == {
        "test": True,
    }

    fake_error = {
        "success": False,
        "error": "test failure",
        "timestamp": _utc_now(),
    }

    assert _api_success(
        fake_error
    ) is False

    assert _api_error(
        fake_error
    ) == "test failure"

    # ------------------------------------------------------------------------
    # Test 11: conversion helpers
    # ------------------------------------------------------------------------

    assert _safe_int(
        "10"
    ) == 10

    assert _safe_int(
        "invalid"
    ) == 0

    assert _safe_float(
        "1.25"
    ) == 1.25

    assert _safe_mapping(
        {"a": 1}
    ) == {
        "a": 1,
    }

    assert _safe_list(
        [1, 2, 3]
    ) == [
        1,
        2,
        3,
    ]

    assert _humanize(
        "security_alert"
    ) == "Security Alert"

    assert _format_percentage(
        0.91
    ) == "91.0%"

    assert _format_percentage(
        91.0
    ) == "91.0%"

    # ------------------------------------------------------------------------
    # Test 12: health normalization
    # ------------------------------------------------------------------------

    normalized_health = _extract_health_contract(
        health_response
    )

    assert isinstance(
        normalized_health,
        dict,
    )

    assert isinstance(
        normalized_health.get("status"),
        str,
    )

    assert isinstance(
        normalized_health.get("service"),
        str,
    )

    assert isinstance(
        normalized_health.get("version"),
        str,
    )

    # ------------------------------------------------------------------------
    # Test 13: latency extraction
    # ------------------------------------------------------------------------

    latency_source = {
        "prediction_latency_ms": 12.5,
        "nested": {
            "processing_latency": 4.0,
        },
    }

    latency_values = _find_latency_values(
        latency_source
    )

    assert 12.5 in latency_values, (
        "Prediction latency extraction failed."
    )

    assert 4.0 in latency_values, (
        "Nested latency extraction failed."
    )

    # ------------------------------------------------------------------------
    # Test 14: complete data loading
    # ------------------------------------------------------------------------

    loaded = load_dashboard_data(
        api
    )

    assert isinstance(
        loaded,
        dict,
    )

    required_keys = {
        "system_status",
        "alerts",
        "escalations",
        "recent_activity",
        "summary_metrics",
        "snapshot",
        "errors",
    }

    assert required_keys.issubset(
        loaded.keys()
    ), (
        "Dashboard data contract is incomplete."
    )

    # ------------------------------------------------------------------------
    # Test 15: data types
    # ------------------------------------------------------------------------

    assert isinstance(
        loaded["system_status"],
        dict,
    )

    assert isinstance(
        loaded["alerts"],
        list,
    )

    assert isinstance(
        loaded["escalations"],
        list,
    )

    assert isinstance(
        loaded["recent_activity"],
        list,
    )

    assert isinstance(
        loaded["summary_metrics"],
        dict,
    )

    assert isinstance(
        loaded["snapshot"],
        dict,
    )

    assert isinstance(
        loaded["errors"],
        list,
    )

    # ------------------------------------------------------------------------
    # Test 16: presentation boundary
    # ------------------------------------------------------------------------

    # The UI module must expose DashboardAPI as its application boundary.
    assert DashboardAPI is not None

    return True


# ============================================================================
# Module execution
# ============================================================================


if __name__ == "__main__":

    print("=" * 70)

    print(
        "EnterpriseGuard - ADIE Dashboard UI Self-Test"
    )

    print("=" * 70)

    try:

        self_test()

        print(
            "[PASS] Import bootstrap"
        )

        print(
            "[PASS] Dashboard API construction"
        )

        print(
            "[PASS] API health contract"
        )

        print(
            "[PASS] Dashboard forwarding"
        )

        print(
            "[PASS] Response normalization"
        )

        print(
            "[PASS] Telemetry extraction"
        )

        print(
            "[PASS] UI data contract"
        )

        print(
            "[PASS] Presentation boundary"
        )

        print("=" * 70)

        print(
            "SELF-TEST PASSED"
        )

        print("=" * 70)

    except AssertionError as exc:

        print(
            "[FAIL] Assertion error:"
        )

        print(
            str(exc)
        )

        raise SystemExit(1)

    except Exception as exc:

        print(
            "[FAIL] Unexpected error:"
        )

        print(
            str(exc)
        )

        raise SystemExit(1)

else:

    # Streamlit imports this file as the application script.
    # Therefore main() is intentionally executed here.
    main()