"""SQLite diagnostic history for FieldLens reports.

Stores one row per generated report (plot geometry, crop, trend, timestamp).
Keeps the last 10 entries retrievable via GET /api/history.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "fieldlens.db"


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            crop TEXT NOT NULL,
            trend TEXT NOT NULL,
            geojson TEXT NOT NULL,
            scenes INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    return conn


def save_report(geojson: dict, crop: str, trend: str, scenes: int) -> None:
    """Persist one report run; failures are swallowed (diagnostics only)."""
    try:
        with _conn() as conn:
            conn.execute(
                "INSERT INTO reports (ts, crop, trend, geojson, scenes) VALUES (?, ?, ?, ?, ?)",
                (datetime.utcnow().isoformat(timespec="seconds"), crop, trend, json.dumps(geojson), scenes),
            )
    except Exception:  # noqa: BLE001 - history must never break the main flow
        pass


def recent_reports(limit: int = 10) -> list:
    """Return the most recent report rows, newest first."""
    try:
        with _conn() as conn:
            rows = conn.execute(
                "SELECT id, ts, crop, trend, scenes FROM reports ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            {"id": r[0], "ts": r[1], "crop": r[2], "trend": r[3], "scenes": r[4]}
            for r in rows
        ]
    except Exception:  # noqa: BLE001
        return []
