import os
import asyncpg

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://chat:chat@localhost:5432/chat")

pool: asyncpg.Pool | None = None


#sql
HISTORY_SQL = """
              SELECT m.id, u.username AS author, m.text, m.client_id, m.created_at
              FROM messages m
              JOIN users u ON u.id = m.user_id
              WHERE ($1::bigint IS NULL OR m.id < $1)
              ORDER BY m.id DESC
              LIMIT $2
              """

SEND_SQL = """
           WITH u AS (
             INSERT INTO users (username) VALUES ($1)
               ON CONFLICT (username) DO UPDATE SET username = EXCLUDED.username
               RETURNING id, username
           ), m AS (
                INSERT INTO messages (user_id, text, client_id)
                SELECT id, $2, $3 FROM u
                RETURNING id, user_id, text, client_id, created_at
           )
           SELECT m.id, u.username AS author, m.text, m.client_id, m.created_at
           FROM m JOIN u ON u.id = m.user_id
           """


#connection pool
async def connect():
    """Open a pool of connections when the app starts."""
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)


async def disconnect():
    """Close the pool when the app shuts down."""
    if pool:
        await pool.close()


# turns query into json, returns it
def to_json(id, author, text, client_id, created_at):
    return {
        "id": id,
        "author": author,
        "text": text,
        "clientId": client_id,
        "createdAt": created_at.isoformat(),
    }


#functions endpoints will use
async def load_history(limit: int, before: int | None) -> list[dict]:
    """Newest messages first; `before` loads older pages."""
    rows = await pool.fetch(HISTORY_SQL, before, limit)
    return [
        to_json(r["id"], r["author"], r["text"], r["client_id"], r["created_at"])
        for r in rows
    ]


async def save_message(author: str, text: str, client_id: str | None) -> dict:
    """Find or create the user, save the message, return it."""
    row = await pool.fetchrow(SEND_SQL, author, text, client_id)
    return to_json(row["id"], author, text, client_id, row["created_at"])


async def is_healthy() -> bool:
    """Used by the readiness probe: can we reach the database?"""
    try:
        await pool.fetchval("SELECT 1")
        return True
    except Exception:
        return False