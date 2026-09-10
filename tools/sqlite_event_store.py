#!/usr/bin/env python3
"""SQLite event store as an optional scalable backend."""

import os
import sys
import sqlite3
import json
from pathlib import Path

sys.dont_write_bytecode = True

DB_PATH = Path(__file__).resolve().parent.parent / "tools" / "events.sqlite"


def get_connection(db_path: Path = DB_PATH):
    """Return SQLite connection with WAL mode."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def init_db(db_path: Path = DB_PATH):
    """Create events table if not exists."""
    conn = get_connection(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            agent_id TEXT,
            trace_id TEXT UNIQUE,
            run_id TEXT,
            command TEXT,
            actor_type TEXT,
            input_summary TEXT,
            output_summary TEXT,
            latency_ms REAL,
            raw_json TEXT
        )
    """)
    conn.commit()
    conn.close()


def insert_event(event: dict, db_path: Path = DB_PATH):
    """Insert or replace event by trace_id."""
    init_db(db_path)
    conn = get_connection(db_path)
    conn.execute("""
        INSERT OR REPLACE INTO events (timestamp, agent_id, trace_id, run_id, command, actor_type, input_summary, output_summary, latency_ms, raw_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event.get("timestamp"),
        event.get("agent_id"),
        event.get("trace_id"),
        event.get("run_id"),
        event.get("command"),
        event.get("actor_type"),
        event.get("input_summary"),
        event.get("output_summary"),
        event.get("latency_ms"),
        json.dumps(event, ensure_ascii=False)
    ))
    conn.commit()
    conn.close()


def query_events(limit=50, agent_filter=None, db_path: Path = DB_PATH):
    """Fetch recent events."""
    init_db(db_path)
    conn = get_connection(db_path)
    sql = "SELECT raw_json FROM events"
    params = []
    if agent_filter:
        sql += " WHERE agent_id = ?"
        params.append(agent_filter)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [json.loads(row["raw_json"]) for row in rows]
