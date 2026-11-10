"""
Database access for the chat API (Flask version).

Everything that talks to PostgreSQL lives here, so app.py never contains SQL.
The connection string comes from the DATABASE_URL environment variable.
"""
import os

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://chat:chat@localhost:5432/chat")

# timeout=5: if the database is down, give up after 5 seconds instead of hanging.
pool = ConnectionPool(DATABASE_URL, min_size=1, max_size=10, open=True, timeout=5,
                      kwargs={"row_factory": dict_row})


# sql
HISTORY_SQL = """
              SELECT m.id, u.username AS author, m.text, m.client_id, m.created_at
              FROM messages m
                       JOIN users u ON u.id = m.user_id
              WHERE (%(before)s::bigint IS NULL OR m.id < %(before)s)
              ORDER BY m.id DESC
                  LIMIT %(limit)s \
              """

SEND_SQL = """
           WITH u AS (
           INSERT INTO users (username) VALUES (%(author)s)
           ON CONFLICT (username) DO UPDATE SET username = EXCLUDED.username
                                         RETURNING id, username
                                         ), m AS (
                                     INSERT INTO messages (user_id, text, client_id)
                                     SELECT id, %(text)s, %(client_id)s FROM u
                                         RETURNING id, user_id, text, client_id, created_at
                                         )
           SELECT m.id, u.username AS author, m.text, m.client_id, m.created_at
           FROM m JOIN u ON u.id = m.user_id \
           """


# ---------- Turn a database row into what the website expects ----------
def to_json(r) -> dict:
    return {
        "id": r["id"],
        "author": r["author"],
        "text": r["text"],
        "clientId": r["client_id"],
        "createdAt": r["created_at"].isoformat(),
    }


#function and endpoint use
def load_history(limit: int, before: int | None) -> list[dict]:
    """Newest messages first; `before` loads older pages."""
    with pool.connection() as conn:
        rows = conn.execute(HISTORY_SQL, {"limit": limit, "before": before}).fetchall()
    return [to_json(r) for r in rows]


def save_message(author: str, text: str, client_id: str | None) -> dict:
    """Find or create the user, save the message, return it as stored."""
    with pool.connection() as conn:
        row = conn.execute(SEND_SQL, {"author": author, "text": text, "client_id": client_id}).fetchone()
    return to_json(row)


def is_healthy() -> bool:
    """Used by the readiness probe: can we reach the database?"""
    try:
        with pool.connection(timeout=2) as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False