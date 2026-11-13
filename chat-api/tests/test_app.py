"""test_app.py - unit tests for the chat API application"""

import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)
import db
import pytest
from app import app

@pytest.fixture
def client():
    return app.test_client()

def test_home(client):
    response = client.get("/")
    assert response.status_code == 200

def test_get_messages(client, monkeypatch):                              # ← added monkeypatch
    monkeypatch.setattr(db, "load_history", lambda limit, before: [])
    response = client.get("/api/messages")
    assert response.status_code == 200

#test valid messages
def test_post_valid_message(client, monkeypatch):
    monkeypatch.setattr(db, "save_message", 
                        lambda author, text, client_id: {
                            "id":1,
                            "author":author,
                            "text":text,
                            "client_id":client_id,
                            "created_at":"2026-01-01T00:00:00"
                        }
                    )

    response = client.post("/api/messages",
                           json={
                               "author":"Nigel",
                               "text":"Hello",
                               "clientId":"12"
                           })
    assert response.status_code in [200, 201]


def test_post_missing_author(client):
    response = client.post("/api/messages", 
                           json={
                               "text": "Hi!"
                           })
    assert response.status_code == 400

def test_post_missing_text(client):
    response = client.post("/api/messages", 
                           json={
                               "author": "Nigel"
                           })
    assert response.status_code == 400

def test_post_empty_author(client):
# 400 status code returned if no author is written but text is present
    response = client.post(
        "/api/messages",
        json={
            "author": "",
            "text": "Hello"
        })

    assert response.status_code == 400


def test_post_empty_text(client):
# 400 status code returned if no text is written but author present
    response = client.post(
        "/api/messages",
        json={
            "author": "Nigel",
            "text": ""
        })
    assert response.status_code == 400

def test_liveness(client):
    #kubernetes liveness probe

    response = client.get("/kubernetes/liveness")

    assert response.status_code == 200
    assert response.json == {"status": "UP"}

def test_readiness(client, monkeypatch):
    #kuberenetes readiness
    monkeypatch.setattr(
        db,
        "is_healthy",
        lambda: True
    )

    response = client.get("/kubernetes/ready")

    assert response.status_code == 200
    assert response.json == {"status": "UP"}