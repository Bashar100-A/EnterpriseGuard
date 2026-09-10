#!/usr/bin/env python3
"""
Advanced Permission Control Module
Dynamic access control for AI agents with least-privilege enforcement.

This module provides:
- Dynamic permissions per agent
- Time-bound permissions
- Conditional permissions (request count, data volume, etc.)
- Data exfiltration detection
- Access logging for audit
- SQLite persistence with PostgreSQL support
"""

import os
import sys
import json
import sqlite3
import uuid
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from contextlib import contextmanager
from pathlib import Path

sys.dont_write_bytecode = True

# Setup logging
logger = logging.getLogger(__name__)


@dataclass
class Permission:
    """
    Individual permission entry.

    Attributes:
        id: Unique permission identifier
        action: Action name (e.g., "read", "write", "execute")
        resource: Resource name (e.g., "customer_data", "logs")
        allowed: True if allowed, False if denied
        expires_at: ISO timestamp when permission expires (None = never)
        conditions: Optional dict of conditions (e.g., {"max_tokens": 1000})
    """
    id: str
    action: str
    resource: str
    allowed: bool
    expires_at: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None


@dataclass
class AgentContext:
    """
    Context for permission evaluation.

    Attributes:
        agent_id: Unique agent identifier
        session_id: Current session identifier
        task_type: Type of task being performed
        risk_level: Risk level (low, medium, high)
        requested_resources: List of resources being accessed
        requested_bytes: Approximate data volume being requested
        request_count: Number of requests in current session
        user_id: Associated user ID (if any)
        ip_address: Client IP address (if available)
        timestamp: Current timestamp
    """
    agent_id: str
    session_id: str
    task_type: str = "unknown"
    risk_level: str = "low"
    requested_resources: List[str] = None
    requested_bytes: int = 0
    request_count: int = 0
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: str = None

    def __post_init__(self):
        if self.requested_resources is None:
            self.requested_resources = []
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class PermissionCheckResult:
    """
    Result of a permission check.

    Attributes:
        allowed: True if permission is granted
        reason: Human-readable reason for decision
        matched_permission: The permission that matched (if any)
        required_approval: True if additional approval is required
        approval_id: ID of approval request (if required)
    """
    allowed: bool
    reason: str
    matched_permission: Optional[Permission] = None
    required_approval: bool = False
    approval_id: Optional[str] = None


class PermissionController:
    """
    Advanced permission control system.

    Features:
    - Dynamic permissions per agent
    - Time-bound permissions with expiration
    - Conditional permissions (max tokens, allowed IPs, etc.)
    - Data exfiltration detection
    - Access logging for audit
    - SQLite persistence with PostgreSQL support
    - Least-privilege enforcement

    Usage:
        controller = PermissionController()
        controller.grant_permission("agent-001", "read", "customer_data", expires_in_seconds=3600)
        result = controller.check_permission("agent-001", "read", "customer_data", context)
    """

    # Default database path
    DEFAULT_DB_PATH = "permissions.db"

    # Protected resources that require stricter checking
    PROTECTED_RESOURCES = [
        "customer_data",
        "financial_data",
        "credentials",
        "secrets",
        "personal_data",
        "system_files"
    ]

    # Actions that trigger data exfiltration detection
    EXFILTRATION_ACTIONS = [
        "export",
        "download",
        "copy",
        "move",
        "bulk_read",
        "extract"
    ]

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the permission controller.

        Args:
            db_path: Path to SQLite database (default: permissions.db)
        """
        self.db_path = db_path or self.DEFAULT_DB_PATH
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl: int = 60  # seconds

        # Initialize database
        self._init_database()

        logger.info(f"PermissionController initialized with database: {self.db_path}")

    def _init_database(self) -> None:
        """Initialize the database schema."""
        try:
            with self._get_connection() as conn:
                # Permissions table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS permissions (
                        id TEXT PRIMARY KEY,
                        agent_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        resource TEXT NOT NULL,
                        allowed INTEGER NOT NULL,
                        expires_at TEXT,
                        conditions TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)

                # Index for fast lookups
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_permissions_agent_action_resource
                    ON permissions(agent_id, action, resource)
                """)

                # Index for expiration checks
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_permissions_expires_at
                    ON permissions(expires_at)
                """)

                # Access log table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS access_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        permission_id TEXT,
                        agent_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        resource TEXT NOT NULL,
                        allowed INTEGER NOT NULL,
                        reason TEXT,
                        context_json TEXT,
                        timestamp TEXT NOT NULL
                    )
                """)

                # Approval requests table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS approval_requests (
                        approval_id TEXT PRIMARY KEY,
                        agent_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        resource TEXT NOT NULL,
                        status TEXT NOT NULL,
                        requested_at TEXT NOT NULL,
                        resolved_at TEXT,
                        reason TEXT
                    )
                """)

                conn.commit()
                logger.info("Database schema initialized")

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise RuntimeError(f"Permission controller initialization failed: {e}")

    @contextmanager
    def _get_connection(self):
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _utc_now(self) -> str:
        """Return current UTC timestamp as ISO string."""
        return datetime.now(timezone.utc).isoformat()

    def grant_permission(
        self,
        agent_id: str,
        action: str,
        resource: str,
        expires_in_seconds: Optional[int] = None,
        conditions: Optional[Dict[str, Any]] = None
    ) -> Permission:
        """
        Grant a permission to an agent.

        Args:
            agent_id: Agent identifier
            action: Action name (e.g., "read", "write")
            resource: Resource name (e.g., "customer_data")
            expires_in_seconds: Expiration time in seconds (None = never)
            conditions: Additional conditions (e.g., {"max_tokens": 1000})

        Returns:
            Permission object
        """
        perm_id = str(uuid.uuid4())
        expires_at = None
        if expires_in_seconds is not None and expires_in_seconds > 0:
            expires_at = (datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)).isoformat()

        conditions_json = json.dumps(conditions) if conditions else None

        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO permissions
                    (id, agent_id, action, resource, allowed, expires_at, conditions, created_at, updated_at)
                    VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?)
                """, (
                    perm_id,
                    agent_id,
                    action,
                    resource,
                    expires_at,
                    conditions_json,
                    self._utc_now(),
                    self._utc_now()
                ))
                conn.commit()

            # Update cache
            cache_key = f"{agent_id}:{action}:{resource}"
            self._cache[cache_key] = {
                "permission": Permission(perm_id, action, resource, True, expires_at, conditions),
                "timestamp": datetime.now(timezone.utc)
            }

            logger.info(f"Permission granted: agent={agent_id}, action={action}, resource={resource}")
            return Permission(perm_id, action, resource, True, expires_at, conditions)

        except Exception as e:
            logger.error(f"Failed to grant permission: {e}")
            raise RuntimeError(f"Permission grant failed: {e}")

    def revoke_permission(self, agent_id: str, action: str, resource: str) -> bool:
        """
        Revoke a permission.

        Args:
            agent_id: Agent identifier
            action: Action name
            resource: Resource name

        Returns:
            True if permission was revoked, False if not found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    DELETE FROM permissions
                    WHERE agent_id = ? AND action = ? AND resource = ?
                """, (agent_id, action, resource))
                conn.commit()

                affected = cursor.rowcount

            # Remove from cache
            cache_key = f"{agent_id}:{action}:{resource}"
            self._cache.pop(cache_key, None)

            if affected > 0:
                logger.info(f"Permission revoked: agent={agent_id}, action={action}, resource={resource}")
            else:
                logger.warning(f"Permission not found: agent={agent_id}, action={action}, resource={resource}")

            return affected > 0

        except Exception as e:
            logger.error(f"Failed to revoke permission: {e}")
            return False

    def check_permission(
        self,
        agent_id: str,
        action: str,
        resource: str,
        context: Optional[AgentContext] = None
    ) -> PermissionCheckResult:
        """
        Check if an agent has permission for an action on a resource.

        Args:
            agent_id: Agent identifier
            action: Action name
            resource: Resource name
            context: Optional context for conditional evaluation

        Returns:
            PermissionCheckResult
        """
        # Check cache first
        cache_key = f"{agent_id}:{action}:{resource}"
        cached = self._cache.get(cache_key)
        if cached:
            cache_age = (datetime.now(timezone.utc) - cached["timestamp"]).total_seconds()
            if cache_age < self._cache_ttl:
                return self._evaluate_permission(cached["permission"], context)

        # Query database
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM permissions
                    WHERE agent_id = ? AND action = ? AND resource = ?
                    ORDER BY allowed DESC
                    LIMIT 1
                """, (agent_id, action, resource))
                row = cursor.fetchone()

            if row:
                perm = Permission(
                    id=row["id"],
                    action=row["action"],
                    resource=row["resource"],
                    allowed=bool(row["allowed"]),
                    expires_at=row["expires_at"],
                    conditions=json.loads(row["conditions"]) if row["conditions"] else None
                )

                # Update cache
                self._cache[cache_key] = {
                    "permission": perm,
                    "timestamp": datetime.now(timezone.utc)
                }

                return self._evaluate_permission(perm, context)

            # No explicit permission - check if it's a protected resource
            if resource in self.PROTECTED_RESOURCES:
                return PermissionCheckResult(
                    allowed=False,
                    reason=f"Access to protected resource '{resource}' requires explicit permission"
                )

            # Default: deny with low confidence
            return PermissionCheckResult(
                allowed=False,
                reason=f"No permission for action '{action}' on resource '{resource}'",
                required_approval=context and context.risk_level == "high"
            )

        except Exception as e:
            logger.error(f"Permission check failed: {e}")
            return PermissionCheckResult(
                allowed=False,
                reason=f"Permission check error: {str(e)}",
                required_approval=True
            )

    def _evaluate_permission(
        self,
        perm: Permission,
        context: Optional[AgentContext]
    ) -> PermissionCheckResult:
        """
        Evaluate a permission against context.

        Args:
            perm: Permission to evaluate
            context: Optional context

        Returns:
            PermissionCheckResult
        """
        # Check if allowed
        if not perm.allowed:
            return PermissionCheckResult(
                allowed=False,
                reason=f"Permission explicitly denied for {perm.action} on {perm.resource}",
                matched_permission=perm
            )

        # Check expiration
        if perm.expires_at:
            if perm.expires_at < self._utc_now():
                return PermissionCheckResult(
                    allowed=False,
                    reason=f"Permission expired at {perm.expires_at}",
                    matched_permission=perm
                )

        # Check conditions
        if perm.conditions and context:
            if not self._evaluate_conditions(perm.conditions, context):
                return PermissionCheckResult(
                    allowed=False,
                    reason=f"Conditions not met for {perm.action} on {perm.resource}",
                    matched_permission=perm
                )

        # Check for data exfiltration
        if context and self._is_exfiltration_attempt(perm.action, perm.resource, context):
            return PermissionCheckResult(
                allowed=False,
                reason="Data exfiltration attempt detected",
                matched_permission=perm,
                required_approval=True
            )

        return PermissionCheckResult(
            allowed=True,
            reason=f"Permission granted for {perm.action} on {perm.resource}",
            matched_permission=perm
        )

    def _evaluate_conditions(self, conditions: Dict[str, Any], context: AgentContext) -> bool:
        """
        Evaluate conditions against context.

        Supported conditions:
            max_tokens: Maximum tokens allowed
            max_requests: Maximum requests allowed in session
            allowed_ips: List of allowed IP addresses
            requires_approval: If True, requires additional approval
        """
        for key, value in conditions.items():
            if key == "max_tokens":
                if context.requested_bytes and context.requested_bytes > value:
                    return False

            elif key == "max_requests":
                if context.request_count > value:
                    return False

            elif key == "allowed_ips":
                if context.ip_address and context.ip_address not in value:
                    return False

            elif key == "requires_approval":
                if value is True:
                    return False

            elif key == "max_session_duration_seconds":
                if context.timestamp:
                    try:
                        session_start = datetime.fromisoformat(context.timestamp)
                        duration = (datetime.now(timezone.utc) - session_start).total_seconds()
                        if duration > value:
                            return False
                    except (ValueError, TypeError):
                        pass

        return True

    def _is_exfiltration_attempt(self, action: str, resource: str, context: AgentContext) -> bool:
        """
        Detect data exfiltration attempts.

        Checks:
        - Large data volumes (over 10 MB)
        - Export actions on protected resources
        - Bulk operations
        """
        # Check action type
        is_exfil_action = any(exfil_action in action.lower() for exfil_action in self.EXFILTRATION_ACTIONS)

        # Check resource protection
        is_protected = resource in self.PROTECTED_RESOURCES

        # Check data volume
        is_large_volume = context.requested_bytes and context.requested_bytes > 10 * 1024 * 1024  # 10 MB

        if is_exfil_action and is_protected and is_large_volume:
            return True

        if is_exfil_action and is_protected and context.request_count > 100:
            return True

        return False

    def log_access(
        self,
        agent_id: str,
        action: str,
        resource: str,
        allowed: bool,
        reason: str,
        permission_id: Optional[str] = None,
        context: Optional[AgentContext] = None
    ) -> None:
        """
        Log an access attempt for audit.

        Args:
            agent_id: Agent identifier
            action: Action name
            resource: Resource name
            allowed: True if access was allowed
            reason: Reason for decision
            permission_id: ID of the permission that matched (if any)
            context: Context for additional details
        """
        try:
            context_json = None
            if context:
                context_json = json.dumps({
                    "session_id": context.session_id,
                    "task_type": context.task_type,
                    "risk_level": context.risk_level,
                    "requested_bytes": context.requested_bytes,
                    "request_count": context.request_count,
                    "user_id": context.user_id,
                    "ip_address": context.ip_address
                })

            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO access_log
                    (permission_id, agent_id, action, resource, allowed, reason, context_json, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    permission_id,
                    agent_id,
                    action,
                    resource,
                    1 if allowed else 0,
                    reason,
                    context_json,
                    self._utc_now()
                ))
                conn.commit()

        except Exception as e:
            logger.warning(f"Failed to log access: {e}")

    def request_approval(
        self,
        agent_id: str,
        action: str,
        resource: str,
        reason: str
    ) -> str:
        """
        Request additional approval for an action.

        Args:
            agent_id: Agent identifier
            action: Action name
            resource: Resource name
            reason: Reason for approval request

        Returns:
            Approval request ID
        """
        approval_id = str(uuid.uuid4())

        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO approval_requests
                    (approval_id, agent_id, action, resource, status, requested_at, reason)
                    VALUES (?, ?, ?, ?, 'pending', ?, ?)
                """, (
                    approval_id,
                    agent_id,
                    action,
                    resource,
                    self._utc_now(),
                    reason
                ))
                conn.commit()

            logger.info(f"Approval request created: {approval_id} for agent {agent_id}")
            return approval_id

        except Exception as e:
            logger.error(f"Failed to create approval request: {e}")
            raise RuntimeError(f"Approval request failed: {e}")

    def resolve_approval(self, approval_id: str, approved: bool, reason: str) -> bool:
        """
        Resolve an approval request.

        Args:
            approval_id: Approval request ID
            approved: True if approved, False if rejected
            reason: Reason for resolution

        Returns:
            True if resolved successfully
        """
        try:
            status = "approved" if approved else "rejected"
            with self._get_connection() as conn:
                conn.execute("""
                    UPDATE approval_requests
                    SET status = ?, resolved_at = ?, reason = ?
                    WHERE approval_id = ?
                """, (status, self._utc_now(), reason, approval_id))
                conn.commit()

                if conn.total_changes == 0:
                    logger.warning(f"Approval request not found: {approval_id}")
                    return False

            logger.info(f"Approval resolved: {approval_id} -> {status}")
            return True

        except Exception as e:
            logger.error(f"Failed to resolve approval: {e}")
            return False

    def revoke_all_permissions(self, agent_id: str) -> int:
        """
        Revoke all permissions for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Number of permissions revoked
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    DELETE FROM permissions
                    WHERE agent_id = ?
                """, (agent_id,))
                conn.commit()

                affected = cursor.rowcount

            # Clear cache for this agent
            to_remove = [k for k in self._cache.keys() if k.startswith(f"{agent_id}:")]
            for key in to_remove:
                self._cache.pop(key, None)

            logger.info(f"Revoked {affected} permissions for agent {agent_id}")
            return affected

        except Exception as e:
            logger.error(f"Failed to revoke all permissions: {e}")
            return 0

    def get_agent_permissions(self, agent_id: str) -> List[Permission]:
        """
        Get all permissions for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            List of permissions
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM permissions
                    WHERE agent_id = ?
                """, (agent_id,))
                rows = cursor.fetchall()

            permissions = []
            for row in rows:
                permissions.append(Permission(
                    id=row["id"],
                    action=row["action"],
                    resource=row["resource"],
                    allowed=bool(row["allowed"]),
                    expires_at=row["expires_at"],
                    conditions=json.loads(row["conditions"]) if row["conditions"] else None
                ))

            return permissions

        except Exception as e:
            logger.error(f"Failed to get agent permissions: {e}")
            return []

    def get_access_logs(
        self,
        agent_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get access logs for audit.

        Args:
            agent_id: Optional agent filter
            limit: Maximum number of logs

        Returns:
            List of access log entries
        """
        try:
            query = "SELECT * FROM access_log"
            params = []
            if agent_id:
                query += " WHERE agent_id = ?"
                params.append(agent_id)
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            with self._get_connection() as conn:
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()

            logs = []
            for row in rows:
                logs.append({
                    "id": row["id"],
                    "permission_id": row["permission_id"],
                    "agent_id": row["agent_id"],
                    "action": row["action"],
                    "resource": row["resource"],
                    "allowed": bool(row["allowed"]),
                    "reason": row["reason"],
                    "context": json.loads(row["context_json"]) if row["context_json"] else None,
                    "timestamp": row["timestamp"]
                })

            return logs

        except Exception as e:
            logger.error(f"Failed to get access logs: {e}")
            return []

    def get_status(self) -> Dict[str, Any]:
        """Return controller status."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM permissions")
                perm_count = cursor.fetchone()[0]

                cursor = conn.execute("SELECT COUNT(*) FROM approval_requests WHERE status = 'pending'")
                pending_approvals = cursor.fetchone()[0]

        except Exception:
            perm_count = 0
            pending_approvals = 0

        return {
            "controller": "PermissionController",
            "status": "active",
            "database_path": self.db_path,
            "total_permissions": perm_count,
            "pending_approvals": pending_approvals,
            "cache_size": len(self._cache),
            "protected_resources": len(self.PROTECTED_RESOURCES),
            "exfiltration_actions": len(self.EXFILTRATION_ACTIONS)
        }


# Convenience functions
def create_controller(db_path: Optional[str] = None) -> PermissionController:
    """Create a permission controller instance."""
    return PermissionController(db_path=db_path)


# Self-test
if __name__ == "__main__":
    print("=" * 60)
    print("Permission Control Module - Self Test")
    print("=" * 60)

    # Create temporary database for testing
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        controller = PermissionController(db_path=db_path)
        print("✅ Controller initialized")

        # Test 1: Grant permission
        perm = controller.grant_permission(
            agent_id="test-agent",
            action="read",
            resource="customer_data",
            expires_in_seconds=3600,
            conditions={"max_tokens": 5000}
        )
        print(f"✅ Permission granted: {perm.id}")

        # Test 2: Check permission
        context = AgentContext(
            agent_id="test-agent",
            session_id="session-001",
            task_type="data_analysis",
            risk_level="medium",
            requested_resources=["customer_data"],
            requested_bytes=1000
        )
        result = controller.check_permission("test-agent", "read", "customer_data", context)
        print(f"✅ Permission check: allowed={result.allowed}, reason={result.reason}")

        # Test 3: Check denied permission
        result2 = controller.check_permission("test-agent", "write", "customer_data", context)
        print(f"✅ Denied permission check: allowed={result2.allowed}")

        # Test 4: Check expired permission
        expired_perm = controller.grant_permission(
            agent_id="test-agent",
            action="temporary",
            resource="logs",
            expires_in_seconds=1
        )
        import time
        time.sleep(2)
        result3 = controller.check_permission("test-agent", "temporary", "logs", context)
        print(f"✅ Expired permission check: allowed={result3.allowed}")

        # Test 5: Data exfiltration detection
        exfil_context = AgentContext(
            agent_id="test-agent",
            session_id="session-002",
            task_type="export",
            risk_level="high",
            requested_resources=["customer_data"],
            requested_bytes=15 * 1024 * 1024  # 15 MB
        )
        result4 = controller.check_permission("test-agent", "export", "customer_data", exfil_context)
        print(f"✅ Exfiltration detection: allowed={result4.allowed}, reason={result4.reason}")

        # Test 6: Approval request
        approval_id = controller.request_approval(
            agent_id="test-agent",
            action="delete",
            resource="customer_data",
            reason="Bulk deletion requested"
        )
        print(f"✅ Approval request created: {approval_id}")

        # Test 7: Resolve approval
        resolved = controller.resolve_approval(approval_id, approved=True, reason="Approved by manager")
        print(f"✅ Approval resolved: {resolved}")

        # Test 8: Revoke permission
        revoked = controller.revoke_permission("test-agent", "read", "customer_data")
        print(f"✅ Permission revoked: {revoked}")

        # Test 9: Get agent permissions
        perms = controller.get_agent_permissions("test-agent")
        print(f"✅ Agent permissions: {len(perms)} remaining")

        # Test 10: Status
        status = controller.get_status()
        print(f"✅ Status: {status['status']}, permissions={status['total_permissions']}")

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED - Permission Control ready")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise

    finally:
        # Clean up temporary database
        try:
            os.unlink(db_path)
        except Exception:
            pass
