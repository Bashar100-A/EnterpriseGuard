#!/usr/bin/env python3
"""In-memory event ring buffer with durable JSONL storage."""

import argparse
import json
import os
import sys
import threading
import time
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.paths_config import DATA_DIR


storage_path = DATA_DIR / "ring_storage.jsonl"
buffer: list[dict] = []
flush_interval = 10
max_buffer_size = 1000
_timer: threading.Timer | None = None
_running = False
_buffer_lock = threading.Lock()
_timer_lock = threading.Lock()


def add_event(event: dict) -> int:
    """Append an event to the buffer and flush when it reaches capacity."""
    if not isinstance(event, dict):
        raise TypeError("event must be a dictionary")

    with _buffer_lock:
        buffer.append(event)
        current_size = len(buffer)

    if current_size >= max_buffer_size:
        flush()
    return len(buffer)


def flush() -> int:
    """Append buffered events to disk, syncing before clearing the buffer."""
    with _buffer_lock:
        if not buffer:
            return 0
        events = list(buffer)

    path = Path(storage_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        for event in events:
            payload = (json.dumps(event, sort_keys=True) + "\n").encode("utf-8")
            offset = 0
            while offset < len(payload):
                offset += os.write(descriptor, payload[offset:])
        os.fsync(descriptor)
    finally:
        os.close(descriptor)

    with _buffer_lock:
        del buffer[: len(events)]
    return len(events)


def load_existing() -> list[dict]:
    """Load valid dictionary events from the JSONL storage file."""
    path = Path(storage_path)
    if not path.exists():
        return []

    events = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(event, dict):
                    events.append(event)
    except OSError:
        return []
    return events


def _schedule_timer() -> None:
    global _timer
    with _timer_lock:
        if not _running:
            return
        _timer = threading.Timer(flush_interval, _timer_flush)
        _timer.daemon = True
        _timer.start()


def _timer_flush() -> None:
    try:
        flush()
    finally:
        _schedule_timer()


def start() -> None:
    """Start periodic background flushing without blocking the caller."""
    global _running
    with _timer_lock:
        if _running:
            return
        _running = True
    _schedule_timer()


def stop() -> None:
    """Stop periodic flushing and synchronously flush pending events."""
    global _running, _timer
    with _timer_lock:
        _running = False
        timer = _timer
        _timer = None
    if timer is not None:
        timer.cancel()
    flush()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--flush", action="store_true", help="Flush buffered events")
    parser.add_argument("--load", action="store_true", help="Print stored events")
    parser.add_argument("--add", metavar="JSON", help="Add one event from a JSON object")
    args = parser.parse_args()

    if args.add is not None:
        event = json.loads(args.add)
        if not isinstance(event, dict):
            parser.error("--add must contain a JSON object")
        add_event(event)
    if args.flush:
        flush()
    if args.load:
        print(json.dumps(load_existing(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
