import os
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any, List

_DB_ENV = os.getenv("DB_PATH")
if _DB_ENV:
    DB_PATH = Path(_DB_ENV)
else:
    DB_PATH = Path(__file__).resolve().parents[1] / "data" / "suggestions.db"


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def _column_exists(cur: sqlite3.Cursor, table: str, col: str) -> bool:
    cur.execute(f"PRAGMA table_info({table})")
    return any(r[1] == col for r in cur.fetchall())


def init_db() -> None:
    with _conn() as conn:
        cur = conn.cursor()

        # Базовая таблица
        cur.execute("""
        CREATE TABLE IF NOT EXISTS suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            text TEXT,
            category TEXT,
            media_type TEXT,           -- photo | document | video | voice | NULL
            media_file_id TEXT,
            status TEXT DEFAULT 'pending',  -- pending | in_process | approved | rejected
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Миграции (добавочные поля)
        migrations = [
            ("user_username",   "ALTER TABLE suggestions ADD COLUMN user_username TEXT"),
            ("user_first_name", "ALTER TABLE suggestions ADD COLUMN user_first_name TEXT"),
            ("user_last_name",  "ALTER TABLE suggestions ADD COLUMN user_last_name TEXT"),
            ("updated_at",      "ALTER TABLE suggestions ADD COLUMN updated_at TIMESTAMP"),
        ]
        for col, ddl in migrations:
            if not _column_exists(cur, "suggestions", col):
                cur.execute(ddl)

        # Индексы
        cur.execute("CREATE INDEX IF NOT EXISTS idx_suggestions_status ON suggestions(status)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_suggestions_created_at ON suggestions(created_at)")

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


def get_suggestion(sugg_id: int) -> Optional[Dict[str, Any]]:
    with _conn() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM suggestions WHERE id = ?", (sugg_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def set_status(sugg_id: int, status: str) -> None:
    """Обновляет статус и updated_at (используется в модерации)."""
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE suggestions SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, sugg_id),
        )
        conn.commit()


def update_status(sugg_id: int, status: str) -> None:
    # совместимость со старым кодом
    set_status(sugg_id, status)


def list_suggestions(
    status: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 200
) -> List[Dict[str, Any]]:
    """
    Возвращает список заявок в виде dict-ов.
    Параметры:
      - status: фильтр по статусу (например, 'in_process')
      - start, end: границы по created_at включительно, строки '%Y-%m-%d %H:%M:%S'
      - limit: максимум строк
    """
    conn = _conn()
    try:
        q = (
            "SELECT id, user_id, text, category, media_type, media_file_id, status, "
            "created_at, user_username, user_first_name, user_last_name "
            "FROM suggestions WHERE 1=1"
        )
        args = []
        if status:
            q += " AND status = ?"
            args.append(status)
        if start:
            q += " AND created_at >= ?"
            args.append(start)
        if end:
            q += " AND created_at <= ?"
            args.append(end)
        q += " ORDER BY created_at DESC"
        if limit:
            q += " LIMIT ?"
            args.append(int(limit))

        cur = conn.execute(q, args)
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]
    finally:
        conn.close()
