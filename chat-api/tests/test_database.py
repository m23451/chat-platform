""" test_database.py
unit tests for the database access functions 
(mock connections w/o connection to real database)"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
import db


# uses fake pool and connection with MagicMock so tests don't need PostgreSQL server.
@pytest.fixture
def db_connection(monkeypatch):
    connection = Mock()
    pool = MagicMock()
    pool.connection.return_value.__enter__.return_value = connection
    monkeypatch.setattr(db, "pool", pool)
    return connection, pool


# checks that save_message passes expected SQL and parameters, 
# converts mocked database row into the API's JSON-style field names and values.
def test_save_message_returns_api_record(db_connection):
    connection, pool = db_connection
    created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    connection.execute.return_value.fetchone.return_value = {
        "id": 1,
        "author": "Nigel",
        "text": "Hello",
        "client_id": "client-1",
        "created_at": created_at,
    }

    message = db.save_message("Nigel", "Hello", "client-1")

    assert message == {
        "id": 1,
        "author": "Nigel",
        "text": "Hello",
        "clientId": "client-1",
        "createdAt": "2026-01-01T00:00:00+00:00",
    }
    pool.connection.assert_called_once_with()
    connection.execute.assert_called_once_with(
        db.SEND_SQL,
        {"author": "Nigel", "text": "Hello", "client_id": "client-1"},
    )

#checks load history passes and converts the created mock rows into api records
def test_load_history_maps_rows_and_passes_pagination(db_connection):
    connection, pool = db_connection
    created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    connection.execute.return_value.fetchall.return_value = [
        {
            "id": 2,
            "author": "Nigel",
            "text": "Second",
            "client_id": None,
            "created_at": created_at,
        },
        {
            "id": 1,
            "author": "Nigel",
            "text": "First",
            "client_id": "client-1",
            "created_at": created_at,
        },
    ]

    history = db.load_history(limit=2, before=3)

    assert [message["id"] for message in history] == [2, 1]
    assert history[0]["clientId"] is None
    assert history[1]["createdAt"] == "2026-01-01T00:00:00+00:00"
    pool.connection.assert_called_once_with()
    connection.execute.assert_called_once_with(
        db.HISTORY_SQL, {"limit": 2, "before": 3}
    )


# if the querys successful, db is healthy should return true
def test_is_healthy_returns_true_when_query_succeeds(db_connection):
    connection, pool = db_connection

    assert db.is_healthy() is True

    pool.connection.assert_called_once_with(timeout=2)
    connection.execute.assert_called_once_with("SELECT 1")


# simulates a database error and check that is_healthy catches it and returns false
def test_is_healthy_returns_false_when_query_fails(db_connection):
    connection, _ = db_connection
    connection.execute.side_effect = RuntimeError("database unavailable")

    assert db.is_healthy() is False
