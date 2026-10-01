#!/usr/bin/env python3
"""C2 Benchmark: SQLiteEventStore under concurrent writers.

Measures p50/p95/p99/p999 latency for N events across W threads.
Writes raw timing data to JSONL for independent verification.

Usage:
    python3 scripts/benchmarks/c2_sqlite_store/run_benchmark.py \
        --n 100000 --writers 10
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from pathlib import Path
from queue import Queue, Empty

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.sqlite_event_store import SQLiteEventStore


def _writer(
    thread_id: int,
    store: SQLiteEventStore,
    queue: Queue,
    timings: list,
    errors: list,
) -> None:
    while True:
        try:
            seq, event_id = queue.get_nowait()
        except Empty:
            break

        t0 = time.perf_counter_ns()
        ok = False
        err_msg = None
        try:
            ok = store.append_event(
                event_id=event_id,
                timestamp=time.time(),
                event_type="bench",
                payload="x" * 200,
                prev_hash=f"prev_{seq:08d}",
                curr_hash=f"curr_{seq:08d}",
            )
        except Exception as exc:
            err_msg = f"{type(exc).__name__}: {exc}"
        t1 = time.perf_counter_ns()

        timings.append({
            "thread": thread_id,
            "seq": seq,
            "event_id": event_id,
            "latency_ns": t1 - t0,
            "success": bool(ok),
        })
        if not ok:
            errors.append({"thread": thread_id, "seq": seq, "error": err_msg or "append returned False"})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100000)
    ap.add_argument("--writers", type=int, default=10)
    ap.add_argument("--db", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    db_path = args.db or f"/tmp/c2_bench_{ts}.db"
    out_path = args.out or f"/tmp/c2_run_{ts}.jsonl"

    print(f"[C2] N={args.n} writers={args.writers}")
    print(f"[C2] DB: {db_path}")
    print(f"[C2] Out: {out_path}")

    if os.path.exists(db_path):
        os.unlink(db_path)

    store = SQLiteEventStore(db_path=db_path)

    queue: Queue = Queue()
    for i in range(args.n):
        queue.put((i, f"evt-{i:08d}"))
    print(f"[C2] Queue loaded: {queue.qsize()} events")

    timings: list = []
    errors: list = []

    t_start = time.perf_counter_ns()
    threads = []
    for tid in range(args.writers):
        t = threading.Thread(
            target=_writer,
            args=(tid, store, queue, timings, errors),
            daemon=False,
        )
        t.start()
        threads.append(t)

    for t in threads:
        t.join()
    t_end = time.perf_counter_ns()

    wall_ns = t_end - t_start
    wall_s = wall_ns / 1e9
    throughput = args.n / wall_s if wall_s > 0 else 0.0

    # Verify insertion count
    import sqlite3
    conn = sqlite3.connect(db_path)
    db_count = conn.execute("SELECT COUNT(*) FROM event_store").fetchone()[0]
    conn.close()

    print(f"[C2] Wall: {wall_s:.2f}s")
    print(f"[C2] Throughput: {throughput:.2f} ev/s")
    print(f"[C2] Inserted: {db_count} / {args.n}")
    print(f"[C2] Errors: {len(errors)}")
    print(f"[C2] Timings: {len(timings)}")

    with open(out_path, "w", encoding="utf-8") as f:
        for row in timings:
            f.write(json.dumps(row) + "\n")
        for err in errors:
            f.write(json.dumps({"error": err}) + "\n")

    print(f"[C2] Wrote {out_path}")
    store.close()

    if db_count != args.n:
        print(f"[C2] WARNING: expected {args.n}, got {db_count}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
