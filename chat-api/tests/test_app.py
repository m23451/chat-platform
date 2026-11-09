"""test_app.py - unit tests for the chat API application"""

import sys
import os

import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

import pytest
from app import app

@pytest.fixture
def client():
    return app.test_client()

def test_home(client):
    response = client.get("/")
    assert response.status_code == 200

def test_get_messages(client):
    response = client.get("/api/messages")
    assert response.status_code == 200
