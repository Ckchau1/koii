from __future__ import annotations

import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any


class EventStore:
    def __init__(self, backend: str = "memory", sqlite_path: str | None = None) -> None:
        self.backend = backend
        self._events: list[dict[str, Any]] = []
        self.sqlite_path = sqlite_path
        self._conn: sqlite3.Connection | None = None

        if backend == "sqlite":
            if not sqlite_path:
                raise ValueError("sqlite_path is required for sqlite backend")
            Path(sqlite_path).parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(sqlite_path)
            self._init_schema()

    def _init_schema(self) -> None:
        assert self._conn is not None
        cur = self._conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                ts REAL NOT NULL,
                topic TEXT NOT NULL,
                payload TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def append(self, topic: str, payload: dict[str, Any]) -> None:
        event = {
            "id": str(uuid.uuid4()),
            "ts": time.time(),
            "topic": topic,
            "payload": payload,
        }

        if self.backend == "sqlite":
            assert self._conn is not None
            cur = self._conn.cursor()
            cur.execute(
                "INSERT INTO events (id, ts, topic, payload) VALUES (?, ?, ?, ?)",
                (event["id"], event["ts"], event["topic"], json.dumps(event["payload"])),
            )
            self._conn.commit()
            return

        self._events.append(event)

    def recent(self, limit: int = 100) -> list[dict[str, Any]]:
        if self.backend == "sqlite":
            assert self._conn is not None
            cur = self._conn.cursor()
            cur.execute(
                "SELECT id, ts, topic, payload FROM events ORDER BY ts DESC LIMIT ?",
                (limit,),
            )
            rows = cur.fetchall()
            return [
                {
                    "id": row[0],
                    "ts": row[1],
                    "topic": row[2],
                    "payload": json.loads(row[3]),
                }
                for row in rows
            ]

        return list(reversed(self._events[-limit:]))

    def recover_pending_tasks(self) -> list[dict[str, Any]]:
        events = self.recent(limit=5000)
        submitted: dict[str, dict[str, Any]] = {}
        completed: set[str] = set()

        for evt in reversed(events):
            topic = evt["topic"]
            payload = evt["payload"]
            task_id = payload.get("task_id")
            if not task_id:
                continue
            if topic == "task.submitted":
                submitted[task_id] = payload
            elif topic == "task.completed":
                completed.add(task_id)

        return [payload for task_id, payload in submitted.items() if task_id not in completed]


def build_event_store(cfg: dict[str, Any]) -> EventStore:
    backend = cfg.get("backend", "memory")
    if backend == "sqlite":
        return EventStore(backend="sqlite", sqlite_path=cfg.get("sqlite_path", "./data/koii_events.db"))
    return EventStore(backend="memory")
