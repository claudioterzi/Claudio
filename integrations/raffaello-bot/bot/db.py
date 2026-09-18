"""Persistenza SQLite. Le possibilità restano IPOTESI; le azioni sono dati tecnici."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

from bot.config import DATABASE_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    telegram_id     INTEGER PRIMARY KEY,
    username        TEXT,
    first_name      TEXT,
    created_at      TEXT NOT NULL,
    last_seen       TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS open_possibilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    layer TEXT NOT NULL DEFAULT 'IPOTESI',
    status TEXT NOT NULL DEFAULT 'APERTA',
    how_falls TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    how_verifiable TEXT NOT NULL,
    layer TEXT NOT NULL DEFAULT 'TECNICO',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS testimoni (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL,
    chi TEXT NOT NULL,
    atto TEXT NOT NULL,
    esito TEXT,
    created_at TEXT NOT NULL,
    esito_at TEXT
);
CREATE TABLE IF NOT EXISTS sanctuary_visits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL,
    completed INTEGER NOT NULL DEFAULT 0,
    started_at TEXT NOT NULL,
    completed_at TEXT
);
CREATE TABLE IF NOT EXISTS veil_dissolutions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL,
    veil_id INTEGER NOT NULL,
    note TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS labeled_statements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL,
    statement TEXT NOT NULL,
    suggested_layer TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS epistemic_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL,
    layer TEXT NOT NULL,
    text TEXT NOT NULL,
    how_falls TEXT,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _migrate(conn: sqlite3.Connection) -> None:
    cols = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(open_possibilities)").fetchall()
    }
    if cols and "how_falls" not in cols:
        conn.execute("ALTER TABLE open_possibilities ADD COLUMN how_falls TEXT")


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)
        _migrate(conn)


def upsert_user(telegram_id: int, username: str | None, first_name: str | None) -> None:
    now = _now()
    with connect() as conn:
        existing = conn.execute(
            "SELECT telegram_id FROM users WHERE telegram_id = ?", (telegram_id,)
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE users SET username = ?, first_name = ?, last_seen = ? WHERE telegram_id = ?",
                (username, first_name, now, telegram_id),
            )
        else:
            conn.execute(
                "INSERT INTO users (telegram_id, username, first_name, created_at, last_seen) VALUES (?, ?, ?, ?, ?)",
                (telegram_id, username, first_name, now, now),
            )


def add_possibility(telegram_id: int, text: str, how_falls: str | None = None) -> int:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO open_possibilities (telegram_id, text, layer, status, how_falls, created_at) VALUES (?, ?, 'IPOTESI', 'APERTA', ?, ?)",
            (telegram_id, text.strip(), (how_falls or "").strip() or None, _now()),
        )
        return int(cur.lastrowid)


def list_possibilities(telegram_id: int) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, text, layer, status, how_falls, created_at FROM open_possibilities WHERE telegram_id = ? ORDER BY id DESC",
            (telegram_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def add_action(telegram_id: int, description: str, how_verifiable: str | None = None) -> int:
    verify = (how_verifiable or "dichiarato dall'utente; verifica esterna non specificata").strip()
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO actions (telegram_id, description, how_verifiable, layer, created_at) VALUES (?, ?, ?, 'TECNICO', ?)",
            (telegram_id, description.strip(), verify, _now()),
        )
        return int(cur.lastrowid)


def list_actions(telegram_id: int, limit: int = 20) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, description, how_verifiable, layer, created_at FROM actions WHERE telegram_id = ? ORDER BY id DESC LIMIT ?",
            (telegram_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def add_testimone(telegram_id: int, chi: str, atto: str) -> int:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO testimoni (telegram_id, chi, atto, created_at) VALUES (?, ?, ?, ?)",
            (telegram_id, chi.strip(), atto.strip(), _now()),
        )
        return int(cur.lastrowid)


def get_testimone(telegram_id: int, testimone_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM testimoni WHERE id = ? AND telegram_id = ?",
            (testimone_id, telegram_id),
        ).fetchone()
    return dict(row) if row else None


def set_esito_testimone(telegram_id: int, testimone_id: int, esito: str) -> bool:
    with connect() as conn:
        cur = conn.execute(
            "UPDATE testimoni SET esito = ?, esito_at = ? WHERE id = ? AND telegram_id = ? AND esito IS NULL",
            (esito, _now(), testimone_id, telegram_id),
        )
        return cur.rowcount > 0


def list_testimoni(telegram_id: int, solo_aperti: bool = False, limit: int = 20) -> list[dict[str, Any]]:
    query = "SELECT * FROM testimoni WHERE telegram_id = ?"
    if solo_aperti:
        query += " AND esito IS NULL"
    query += " ORDER BY id DESC LIMIT ?"
    with connect() as conn:
        rows = conn.execute(query, (telegram_id, limit)).fetchall()
    return [dict(r) for r in rows]


def start_sanctuary(telegram_id: int) -> int:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO sanctuary_visits (telegram_id, completed, started_at) VALUES (?, 0, ?)",
            (telegram_id, _now()),
        )
        return int(cur.lastrowid)


def complete_sanctuary(visit_id: int) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE sanctuary_visits SET completed = 1, completed_at = ? WHERE id = ?",
            (_now(), visit_id),
        )


def add_veil(telegram_id: int, veil_id: int, note: str | None) -> int:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO veil_dissolutions (telegram_id, veil_id, note, created_at) VALUES (?, ?, ?, ?)",
            (telegram_id, veil_id, (note or "").strip() or None, _now()),
        )
        return int(cur.lastrowid)


def add_labeled(telegram_id: int, statement: str, suggested_layer: str) -> int:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO labeled_statements (telegram_id, statement, suggested_layer, created_at) VALUES (?, ?, ?, ?)",
            (telegram_id, statement.strip(), suggested_layer, _now()),
        )
        return int(cur.lastrowid)


def add_epistemic(telegram_id: int, layer: str, text: str, source: str, how_falls: str | None = None) -> int:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO epistemic_records (telegram_id, layer, text, how_falls, source, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (telegram_id, layer, text.strip(), (how_falls or "").strip() or None, source, _now()),
        )
        return int(cur.lastrowid)


def list_epistemic(telegram_id: int, limit: int = 20) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, layer, text, how_falls, source, created_at FROM epistemic_records WHERE telegram_id = ? ORDER BY id DESC LIMIT ?",
            (telegram_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def set_possibility_how_falls(telegram_id: int, possibility_id: int, how_falls: str) -> bool:
    note = how_falls.strip()
    if not note:
        return False
    with connect() as conn:
        cur = conn.execute(
            "UPDATE open_possibilities SET how_falls = ? WHERE id = ? AND telegram_id = ?",
            (note, possibility_id, telegram_id),
        )
        if not cur.rowcount:
            return False
        conn.execute(
            """
            UPDATE epistemic_records
            SET how_falls = ?
            WHERE id = (
                SELECT id FROM epistemic_records
                WHERE telegram_id = ? AND source = 'tieni_aperto'
                ORDER BY id DESC LIMIT 1
            )
            """,
            (note, telegram_id),
        )
        return True


def user_counts(telegram_id: int) -> dict[str, int]:
    with connect() as conn:
        poss = conn.execute(
            "SELECT COUNT(*) AS n FROM open_possibilities WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchone()["n"]
        acts = conn.execute(
            "SELECT COUNT(*) AS n FROM actions WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchone()["n"]
        visits = conn.execute(
            "SELECT COUNT(*) AS n FROM sanctuary_visits WHERE telegram_id = ? AND completed = 1",
            (telegram_id,),
        ).fetchone()["n"]
        recs = conn.execute(
            "SELECT COUNT(*) AS n FROM epistemic_records WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchone()["n"]
    return {
        "possibilities": int(poss),
        "actions": int(acts),
        "sanctuary_completed": int(visits),
        "epistemic": int(recs),
    }


async def ensure_user(telegram_id: int, username: str | None, first_name: str | None) -> None:
    upsert_user(telegram_id, username, first_name)


async def log_sanctuary_visit(telegram_id: int, completed: bool = False) -> int:
    if completed:
        with connect() as conn:
            row = conn.execute(
                "SELECT id FROM sanctuary_visits WHERE telegram_id = ? AND completed = 0 ORDER BY id DESC LIMIT 1",
                (telegram_id,),
            ).fetchone()
            if row:
                complete_sanctuary(int(row["id"]))
                return int(row["id"])
        visit_id = start_sanctuary(telegram_id)
        complete_sanctuary(visit_id)
        return visit_id
    return start_sanctuary(telegram_id)
