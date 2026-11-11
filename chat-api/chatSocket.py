import json
import threading

clients= set()
lock = threading.Lock()


def add(ws):
    with lock:
        clients.add(ws)

def remove(ws):
    with lock:
        clients.discard(ws)

def broadcast(message: dict):
    data = json.dumps(message)
    with lock:
        current = list(clients)
    for ws in current:
        try:
            ws.send(data)
        except Exception:
            remove(ws)
