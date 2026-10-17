"""website/db.py — SQLite storage (users, sessions, cases, appointments, audit, chat)."""
from __future__ import annotations

import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

STORAGE = Path(__file__).resolve().parents[2] / "outputs" / "portal"
STORAGE.mkdir(parents=True, exist_ok=True)
DB_PATH = STORAGE / "hospital.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('patient','doctor','admin')),
  password_hash TEXT NOT NULL,
  department TEXT, specialty TEXT, bio TEXT,
  active INTEGER NOT NULL DEFAULT 1,
  failed_attempts INTEGER NOT NULL DEFAULT 0,
  locked_until REAL NOT NULL DEFAULT 0,
  created REAL NOT NULL,
  last_login REAL
);
CREATE TABLE IF NOT EXISTS sessions (
  token_hash TEXT PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created REAL NOT NULL, expires REAL NOT NULL, ip TEXT, ua TEXT
);
CREATE TABLE IF NOT EXISTS cases (
  id TEXT PRIMARY KEY,
  owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  doctor_id INTEGER REFERENCES users(id),
  created REAL NOT NULL,
  source TEXT NOT NULL, truth TEXT, has_image INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'ai_only',   -- ai_only | pending_review | reviewed
  inputs TEXT NOT NULL, result TEXT NOT NULL, agents TEXT,
  review TEXT
);
CREATE INDEX IF NOT EXISTS ix_cases_owner ON cases(owner_id, created DESC);
CREATE INDEX IF NOT EXISTS ix_cases_doctor ON cases(doctor_id, status);
CREATE TABLE IF NOT EXISTS appointments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  patient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  doctor_id INTEGER NOT NULL REFERENCES users(id),
  slot TEXT NOT NULL,                       -- ISO 'YYYY-MM-DDTHH:MM'
  reason TEXT, case_id TEXT, status TEXT NOT NULL DEFAULT 'booked',
  doctor_note TEXT, created REAL NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_appt_slot ON appointments(doctor_id, slot) WHERE status IN ('booked','confirmed');
CREATE TABLE IF NOT EXISTS audit (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts REAL NOT NULL, user_id INTEGER, email TEXT, action TEXT NOT NULL,
  target TEXT, ip TEXT, detail TEXT
);
CREATE TABLE IF NOT EXISTS lesions (
  id TEXT PRIMARY KEY,
  owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  label TEXT NOT NULL, body_site TEXT, created REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS stress_runs (
  id TEXT PRIMARY KEY, created REAL NOT NULL, user_id INTEGER, status TEXT NOT NULL,
  progress REAL NOT NULL DEFAULT 0, params TEXT, results TEXT, error TEXT
);
CREATE TABLE IF NOT EXISTS chat (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  ts REAL NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL, meta TEXT
);
"""


@contextmanager
def conn():
    c = sqlite3.connect(DB_PATH, timeout=15)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    c.execute("PRAGMA journal_mode = WAL")
    try:
        yield c
        c.commit()
    finally:
        c.close()


_CASE_COLUMNS = {"lesion_id": "TEXT", "observed_at": "REAL", "simulated": "INTEGER NOT NULL DEFAULT 0"}


def init() -> None:
    with conn() as c:
        c.executescript(SCHEMA)
        have = {r["name"] for r in c.execute("PRAGMA table_info(cases)").fetchall()}
        for col, typ in _CASE_COLUMNS.items():          # lightweight forward migration
            if col not in have:
                c.execute(f"ALTER TABLE cases ADD COLUMN {col} {typ}")
        c.execute("CREATE INDEX IF NOT EXISTS ix_cases_lesion ON cases(lesion_id, observed_at)")
        have_s = {r["name"] for r in c.execute("PRAGMA table_info(sessions)").fetchall()}
        if "origin_id" not in have_s:                   # patient account a session was created for (role switching)
            c.execute("ALTER TABLE sessions ADD COLUMN origin_id INTEGER")


def one(sql: str, args: Iterable[Any] = ()) -> Optional[Dict[str, Any]]:
    with conn() as c:
        r = c.execute(sql, tuple(args)).fetchone()
    return dict(r) if r else None


def all_(sql: str, args: Iterable[Any] = ()) -> List[Dict[str, Any]]:
    with conn() as c:
        return [dict(r) for r in c.execute(sql, tuple(args)).fetchall()]


def run(sql: str, args: Iterable[Any] = ()) -> int:
    with conn() as c:
        cur = c.execute(sql, tuple(args))
        return cur.lastrowid or cur.rowcount


def audit(user: Optional[Dict[str, Any]], action: str, target: str = "", ip: str = "", detail: str = "") -> None:
    run("INSERT INTO audit(ts,user_id,email,action,target,ip,detail) VALUES (?,?,?,?,?,?,?)",
        (time.time(), user["id"] if user else None, user["email"] if user else None, action, target, ip, detail[:500]))


def jdump(o: Any) -> str:
    return json.dumps(o, separators=(",", ":"))


def jload(s: Optional[str], default: Any = None) -> Any:
    if not s:
        return default
    try:
        return json.loads(s)
    except Exception:
        return default
