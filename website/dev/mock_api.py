"""
Mock chat API for frontend development - no Kafka or database needed.

Implements the same contract as the real API, keeping messages in memory and
broadcasting directly to connected WebSockets.

Run from the website folder, either:
    python dev/mock_api.py
or:
    uvicorn dev.mock_api:app --reload --port 8000
Then open http://localhost:8000 (or the frontend container on http://localhost:8081)
"""
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Mock chat API")
messages: list[dict] = []
clients: set[WebSocket] = set()


class MessageIn(BaseModel):
    author: str
    text: str


@app.get("/api/messages")
async def history(limit: int = Query(50, ge=1, le=200), before: int | None = None):
    pool = [m for m in messages if before is None or m["id"] < before]
    return list(reversed(pool[-limit:]))  # newest first


@app.post("/api/messages", status_code=201)
async def send(msg: MessageIn):
    author, text = msg.author.strip(), msg.text.strip()
    if not author or not text or len(text) > 500 or len(author) > 30:
        raise HTTPException(400, "Invalid message")
    saved = {
        "id": len(messages) + 1,
        "author": author,
        "text": text,
        "createdAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    messages.append(saved)
    for ws in list(clients):
        try:
            await ws.send_json(saved)
        except Exception:
            clients.discard(ws)
    return saved


@app.websocket("/api/message-ws")
async def message_ws(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    try:
        while True:
            await ws.receive_text()  # client pings; nothing to do
    except WebSocketDisconnect:
        pass
    finally:
        clients.discard(ws)


# Serve the static site last so /api routes take priority
app.mount("/", StaticFiles(directory=Path(__file__).parent.parent / "public", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)