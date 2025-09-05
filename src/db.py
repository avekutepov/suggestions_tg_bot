import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "suggestions.db"

def _conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)

def _column_exists(cur: sqlite3.Cursor, table: str, col: str) -> bool:
    cur.execute(f"PRAGMA table_info({table})")
    return any(r[1] == col for r in cur.fetchall())

def init_db():
    with _conn() as conn:
        cur = conn.cursor()
        # базовая таблица
        cur.execute("""
        CREATE TABLE IF NOT EXISTS suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            text TEXT,
            category TEXT,
            media_type TEXT,         -- photo | document | video | voice | NULL
            media_file_id TEXT,
            status TEXT DEFAULT 'pending',  -- pending | approved | rejected
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        # миграции: добавляем недостающие колонки
        for col, ddl in [
            ("user_username",    "ALTER TABLE suggestions ADD COLUMN user_username TEXT"),
            ("user_first_name",  "ALTER TABLE suggestions ADD COLUMN user_first_name TEXT"),
            ("user_last_name",   "ALTER TABLE suggestions ADD COLUMN user_last_name TEXT"),
        ]:
            if not _column_exists(cur, "suggestions", col):
                cur.execute(ddl)

        conn.commit()

def add_suggestion(
    user_id: int,
    text: str,
    category: Optional[str] = None,
    media_type: Optional[str] = None,
    media_file_id: Optional[str] = None,
    user_username: Optional[str] = None,
    user_first_name: Optional[str] = None,
    user_last_name: Optional[str] = None,
) -> int:
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO suggestions (
                user_id, text, category, media_type, media_file_id,
                user_username, user_first_name, user_last_name
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, text, category, media_type, media_file_id,
            user_username, user_first_name, user_last_name
        ))
        conn.commit()
        return cur.lastrowid

def update_status(sugg_id: int, status: str):
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE suggestions SET status = ? WHERE id = ?", (status, sugg_id))
        conn.commit()

def get_suggestion(sugg_id: int) -> Optional[Dict[str, Any]]:
    with _conn() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM suggestions WHERE id = ?", (sugg_id,))
        row = cur.fetchone()
        return dict(row) if row else None
