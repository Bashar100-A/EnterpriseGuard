#!/usr/bin/env python3
"""
EnterpriseGuard Real-Time Monitor (Final Corrected)

Monitors both parent directories and individual files using inotify.
Uses centralized paths and handles overflow/ignored/unmount events.

Governed by DC-052.
"""

from __future__ import annotations

import sys

# Mandatory: prevent bytecode generation
sys.dont_write_bytecode = True

import ctypes
import json
import os
import select
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.paths_config import (
    REALTIME_EVENTS_PATH,
    ACTIVITY_LOG_PATH,
    INTEGRITY_BASELINE_PATH,
    HARDWARE_IDENTITY_PATH,
    INNOCENCE_CHAIN_PATH,
    RELATIONAL_MEMORY_PATH,
)

EVENT_LOG = REALTIME_EVENTS_PATH
ACTIVITY_LOG = ACTIVITY_LOG_PATH

# inotify constants
IN_MODIFY = 0x00000002
IN_ATTRIB = 0x00000004
IN_CLOSE_WRITE = 0x00000008
IN_MOVED_FROM = 0x00000040
IN_MOVED_TO = 0x00000080
IN_CREATE = 0x00000100
IN_DELETE = 0x00000200
IN_UNMOUNT = 0x00002000
IN_Q_OVERFLOW = 0x00004000
IN_IGNORED = 0x00008000
IN_ISDIR = 0x40000000

WATCH_MASK = (
    IN_MODIFY | IN_ATTRIB | IN_CLOSE_WRITE |
    IN_MOVED_FROM | IN_MOVED_TO | IN_CREATE | IN_DELETE
)


class Inotify:
    """Minimal inotify wrapper using ctypes."""

    def __init__(self):
        self._libc = ctypes.CDLL("libc.so.6", use_errno=True)
        self._libc.inotify_init1.argtypes = [ctypes.c_int]
        self._libc.inotify_init1.restype = ctypes.c_int
        self._libc.inotify_add_watch.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
        self._libc.inotify_add_watch.restype = ctypes.c_int
        self._libc.inotify_rm_watch.argtypes = [ctypes.c_int, ctypes.c_int]
        self._libc.inotify_rm_watch.restype = ctypes.c_int
        self._libc.close.argtypes = [ctypes.c_int]
        self._libc.close.restype = ctypes.c_int
        self._libc.read.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t]
        self._libc.read.restype = ctypes.c_ssize_t

        self.fd = self._libc.inotify_init1(0)
        if self.fd < 0:
            errno = ctypes.get_errno()
            raise OSError(f"inotify_init1 failed: {os.strerror(errno)}")

        self._wd_path = {}

    def add_watch(self, path: Path, mask: int = WATCH_MASK) -> int:
        path_bytes = str(path).encode("utf-8")
        wd = self._libc.inotify_add_watch(self.fd, path_bytes, ctypes.c_uint32(mask))
        if wd < 0:
            errno = ctypes.get_errno()
            raise OSError(f"inotify_add_watch failed for {path}: {os.strerror(errno)}")
        self._wd_path[wd] = str(path)
        return wd

    def rm_watch(self, wd: int) -> None:
        self._libc.inotify_rm_watch(self.fd, wd)
        self._wd_path.pop(wd, None)

    def read_events(self, timeout: float = 0.5) -> bytes:
        ready, _, _ = select.select([self.fd], [], [], timeout)
        if not ready:
            return b""
        buf_size = 4096
        buf = ctypes.create_string_buffer(buf_size)
        n = self._libc.read(self.fd, buf, buf_size)
        if n < 0:
            errno = ctypes.get_errno()
            raise OSError(f"inotify read failed: {os.strerror(errno)}")
        return buf.raw[:n]

    def close(self) -> None:
        if self.fd >= 0:
            self._libc.close(self.fd)
            self.fd = -1

    def get_inotify_fd(self) -> int:
        return self.fd


def parse_events(data: bytes, inotify: Inotify, allowed_files: set[str]):
    """
    Parse raw inotify data and yield (event_type, path) for allowed files only.
    Handles overflow and ignored/unmount events gracefully.
    """
    offset = 0
    while offset < len(data):
        wd, mask, cookie, name_len = struct.unpack('iIII', data[offset:offset+16])
        offset += 16
        raw_name = data[offset:offset+name_len]
        name = raw_name.rstrip(b'\x00').decode('utf-8', errors='ignore')
        offset += name_len

        # Handle overflow event (wd == -1)
        if wd == -1 and (mask & IN_Q_OVERFLOW):
            yield "OVERFLOW", "event queue overflow"
            continue

        # Skip ignored/unmount events
        if wd == -1 or (mask & (IN_IGNORED | IN_UNMOUNT)):
            continue

        base_path = inotify._wd_path.get(wd, "")
        full_path = os.path.join(base_path, name) if base_path and name else base_path

        # Only report events for files we actually monitor
        if full_path not in allowed_files:
            continue

        if mask & IN_CREATE:
            yield "CREATE", full_path
        if mask & IN_DELETE:
            yield "DELETE", full_path
        if mask & IN_MOVED_FROM:
            yield "MOVED_FROM", full_path
        if mask & IN_MOVED_TO:
            yield "MOVED_TO", full_path
        if mask & (IN_MODIFY | IN_ATTRIB | IN_CLOSE_WRITE):
            yield "MODIFY", full_path


def log_realtime_event(event_type: str, path: str) -> None:
    """Append event to realtime_events.jsonl and activity log."""
    from tools.time_utils import utc_now

    EVENT_LOG.parent.mkdir(parents=True, exist_ok=True)
    if not EVENT_LOG.exists():
        EVENT_LOG.touch(mode=0o600)
        os.chmod(EVENT_LOG, 0o600)

    record = {
        "timestamp": utc_now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event_type": event_type,
        "path": path,
        "process": "inotify",
    }

    with open(EVENT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")

    try:
        from tools.audit_chain import append_activity
        from tools.time_utils import utc_now

        append_activity(
            {
                "timestamp": utc_now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "activity_type": "realtime_monitor",
                "status": "success",
                "details": f"{event_type}: {path}",
            },
            ACTIVITY_LOG,
        )
    except Exception as exc:
        print(f"WARNING: failed to log realtime activity: {exc}", file=sys.stderr)


def run_monitor(paths: list[Path]) -> None:
    """Monitor both parent directories and individual files."""
    inotify = Inotify()
    allowed = {str(p) for p in paths}

    watched_dirs = set()

    for p in paths:
        parent = p.parent
        # Watch parent directory (if it exists) for create/delete events
        if parent.exists() and parent not in watched_dirs:
            inotify.add_watch(parent)
            watched_dirs.add(parent)

        # Watch the file itself (if it exists) for content modifications
        if p.exists():
            inotify.add_watch(p)
            allowed.add(str(p))

    print("Monitoring started. Press Ctrl+C to stop.", file=sys.stderr)
    try:
        while True:
            data = inotify.read_events(timeout=0.5)
            if data:
                for event_type, path in parse_events(data, inotify, allowed):
                    print(f"[{event_type}] {path}")
                    log_realtime_event(event_type, path)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.", file=sys.stderr)
    finally:
        inotify.close()


def main() -> int:
    monitored = [
        INTEGRITY_BASELINE_PATH,
        HARDWARE_IDENTITY_PATH,
        INNOCENCE_CHAIN_PATH,
        RELATIONAL_MEMORY_PATH,
    ]
    run_monitor(monitored)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
