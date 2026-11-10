"""
╔══════════════════════════════════════════╗
║    MULTI-CHECKER BOT — DATABASE LAYER   ║
║          MADE BY - @NUTFRR              ║
╚══════════════════════════════════════════╝
"""
import os
import sqlite3
import uuid
import hashlib
from contextlib import contextmanager
from datetime import datetime, timedelta

DB_PATH = os.environ.get("DB_PATH", "/tmp/multichkr.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA synchronous=NORMAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id       INTEGER PRIMARY KEY,
            username      TEXT DEFAULT '',
            first_name    TEXT DEFAULT '',
            premium_until TEXT,
            is_banned     INTEGER DEFAULT 0,
            total_checks  INTEGER DEFAULT 0,
            joined_at     TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS codes (
            code        TEXT PRIMARY KEY,
            created_by  INTEGER,
            days        INTEGER,
            uses_total  INTEGER,
            uses_left   INTEGER,
            is_revoked  INTEGER DEFAULT 0,
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS redemptions (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            code       TEXT REFERENCES codes(code),
            user_id    INTEGER,
            redeemed_at TEXT DEFAULT (datetime('now')),
            UNIQUE(code, user_id)
        );

        CREATE TABLE IF NOT EXISTS check_sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER,
            checker     TEXT DEFAULT 'unknown',
            total       INTEGER DEFAULT 0,
            hits        INTEGER DEFAULT 0,
            bad         INTEGER DEFAULT 0,
            twofa       INTEGER DEFAULT 0,
            locked      INTEGER DEFAULT 0,
            status      TEXT DEFAULT 'running',
            started_at  TEXT DEFAULT (datetime('now')),
            finished_at TEXT
        );

        CREATE TABLE IF NOT EXISTS hits (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id   INTEGER REFERENCES check_sessions(id),
            user_id      INTEGER,
            checker      TEXT,
            email        TEXT,
            password     TEXT,
            data_json    TEXT,
            captured_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_hits_user   ON hits(user_id);
        CREATE INDEX IF NOT EXISTS idx_hits_checker ON hits(checker);
        CREATE INDEX IF NOT EXISTS idx_sessions_user ON check_sessions(user_id);
        """)


# ── users ─────────────────────────────────────────────────────────────────────

def upsert_user(user_id: int, username: str, first_name: str):
    with get_conn() as c:
        c.execute("""
            INSERT INTO users(user_id, username, first_name)
            VALUES(?,?,?)
            ON CONFLICT(user_id) DO UPDATE SET
                username   = excluded.username,
                first_name = excluded.first_name
        """, (user_id, username, first_name))


def get_user(user_id: int):
    with get_conn() as c:
        return c.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()


def is_premium(user_id: int) -> bool:
    row = get_user(user_id)
    if not row or not row["premium_until"]:
        return False
    return datetime.fromisoformat(row["premium_until"]) > datetime.utcnow()


def get_premium_expiry(user_id: int):
    row = get_user(user_id)
    if not row or not row["premium_until"]:
        return None
    dt = datetime.fromisoformat(row["premium_until"])
    return dt if dt > datetime.utcnow() else None


def set_premium(user_id: int, days: int) -> datetime:
    row = get_user(user_id)
    if row and row["premium_until"]:
        try:
            base = max(datetime.fromisoformat(row["premium_until"]), datetime.utcnow())
        except Exception:
            base = datetime.utcnow()
    else:
        base = datetime.utcnow()
    exp = base + timedelta(days=days)
    with get_conn() as c:
        c.execute("UPDATE users SET premium_until=? WHERE user_id=?",
                  (exp.isoformat(), user_id))
    return exp


def is_banned(user_id: int) -> bool:
    row = get_user(user_id)
    return bool(row and row["is_banned"])


def ban_user(user_id: int):
    with get_conn() as c:
        c.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (user_id,))


def unban_user(user_id: int):
    with get_conn() as c:
        c.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (user_id,))


def get_all_users(limit: int = 100):
    with get_conn() as c:
        return c.execute(
            "SELECT * FROM users ORDER BY joined_at DESC LIMIT ?", (limit,)
        ).fetchall()


def increment_user_checks(user_id: int, n: int = 1):
    with get_conn() as c:
        c.execute("UPDATE users SET total_checks = total_checks + ? WHERE user_id=?",
                  (n, user_id))


# ── codes ─────────────────────────────────────────────────────────────────────

def generate_code(created_by: int, uses: int, days: int) -> str:
    raw  = f"{created_by}-{uuid.uuid4().hex}-{days}"
    code = hashlib.md5(raw.encode()).hexdigest()[:16].upper()
    code = f"NUTFRR-{code[:4]}-{code[4:8]}-{code[8:12]}"
    with get_conn() as c:
        c.execute("""
            INSERT OR IGNORE INTO codes(code, created_by, days, uses_total, uses_left)
            VALUES(?,?,?,?,?)
        """, (code, created_by, days, uses, uses))
    return code


def redeem_code(user_id: int, code: str) -> dict:
    code = code.strip().upper()
    with get_conn() as c:
        row = c.execute("SELECT * FROM codes WHERE code=?", (code,)).fetchone()
        if not row:
            return {"ok": False, "error": "❌ Invalid code."}
        if row["is_revoked"]:
            return {"ok": False, "error": "❌ Code has been revoked."}
        if row["uses_left"] <= 0:
            return {"ok": False, "error": "❌ Code is fully used."}
        dup = c.execute(
            "SELECT 1 FROM redemptions WHERE code=? AND user_id=?", (code, user_id)
        ).fetchone()
        if dup:
            return {"ok": False, "error": "❌ You already redeemed this code."}
        c.execute("UPDATE codes SET uses_left = uses_left - 1 WHERE code=?", (code,))
        c.execute("INSERT INTO redemptions(code, user_id) VALUES(?,?)", (code, user_id))
    exp = set_premium(user_id, row["days"])
    return {"ok": True, "days": row["days"], "expires_at": exp}


def revoke_code(code: str) -> bool:
    with get_conn() as c:
        cur = c.execute("UPDATE codes SET is_revoked=1 WHERE code=?", (code.upper(),))
        return cur.rowcount > 0


def list_codes(limit: int = 20):
    with get_conn() as c:
        return c.execute(
            "SELECT * FROM codes ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()


# ── sessions & hits ───────────────────────────────────────────────────────────

def create_session(user_id: int, checker: str) -> int:
    with get_conn() as c:
        cur = c.execute(
            "INSERT INTO check_sessions(user_id, checker) VALUES(?,?)",
            (user_id, checker)
        )
        return cur.lastrowid


def update_session(session_id: int, **kw):
    allowed = {"total", "hits", "bad", "twofa", "locked", "status", "finished_at"}
    sets = ", ".join(f"{k}=?" for k in kw if k in allowed)
    vals = [v for k, v in kw.items() if k in allowed]
    if not sets:
        return
    if kw.get("status") in ("done", "stopped"):
        sets += ", finished_at=datetime('now')"
    with get_conn() as c:
        c.execute(f"UPDATE check_sessions SET {sets} WHERE id=?", (*vals, session_id))


def save_hit(session_id: int, user_id: int, checker: str, result: dict):
    import json
    with get_conn() as c:
        c.execute("""
            INSERT INTO hits(session_id, user_id, checker, email, password, data_json)
            VALUES(?,?,?,?,?,?)
        """, (
            session_id, user_id, checker,
            result.get("email", ""),
            result.get("password", ""),
            json.dumps(result),
        ))


def get_session_hits(session_id: int):
    with get_conn() as c:
        return c.execute(
            "SELECT * FROM hits WHERE session_id=? ORDER BY captured_at",
            (session_id,)
        ).fetchall()


def get_stats() -> dict:
    with get_conn() as c:
        users  = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        checks = c.execute("SELECT COALESCE(SUM(total_checks),0) FROM users").fetchone()[0]
        hits   = c.execute("SELECT COUNT(*) FROM hits").fetchone()[0]
        prem   = c.execute(
            "SELECT COUNT(*) FROM users WHERE premium_until > datetime('now')"
        ).fetchone()[0]
        return {"total_users": users, "total_checks": checks,
                "total_hits": hits, "premium_users": prem}
