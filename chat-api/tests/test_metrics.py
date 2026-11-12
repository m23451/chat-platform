"""Tests for metrics.py, run against the real chat API routes (no database or Kafka needed)."""
import time

import pytest
from prometheus_client import REGISTRY

import app as app_module
import db
import metrics


@pytest.fixture(scope="module")
def client():
    return app_module.app.test_client()


@pytest.fixture(autouse=True)
def fake_backends(monkeypatch):
    saved = {"id": 1, "author": "mo", "text": "hi", "clientId": "c1",
             "createdAt": "2026-01-01T00:00:00+00:00"}
    monkeypatch.setattr(db, "load_history", lambda limit, before: [])
    monkeypatch.setattr(db, "save_message", lambda author, text, client_id: saved)
    monkeypatch.setattr(db, "is_healthy", lambda: True)
    monkeypatch.setattr(app_module, "publish_message", lambda message: None)


def sample(name, labels=None):
    return REGISTRY.get_sample_value(name, labels or {}) or 0


def scrape(client):
    return client.get("/actuator/metrics").get_data(as_text=True)


def good_post(client):
    return client.post("/api/messages", json={"author": "mo", "text": "hi", "clientId": "c1"})


def test_metrics_endpoint_serves_prometheus_text(client):
    client.get("/api/messages")
    text = scrape(client)
    assert "flask_http_request_duration_seconds_count" in text
    assert "process_start_time_seconds" in text
    assert "app_info" in text


def test_history_route_is_measured_by_route(client):
    client.get("/api/messages")
    assert 'url_rule="/api/messages"' in scrape(client)


def test_post_counts_received_and_saved(client):
    received = sample("chat_messages_received_total")
    saved = sample("chat_messages_saved_total")
    assert good_post(client).status_code == 201
    assert sample("chat_messages_received_total") == received + 1
    assert sample("chat_messages_saved_total") == saved + 1


def test_invalid_post_counts_validation_error(client):
    before = sample("chat_validation_errors_total")
    assert client.post("/api/messages", json={}).status_code == 400
    assert sample("chat_validation_errors_total") == before + 1


def test_kafka_failure_is_counted_and_api_still_succeeds(client, monkeypatch):
    def boom(message):
        raise RuntimeError("kafka down")

    monkeypatch.setattr(app_module, "publish_message", boom)
    before = sample("chat_kafka_publish_errors_total")
    assert good_post(client).status_code == 201
    assert sample("chat_kafka_publish_errors_total") == before + 1


def test_kubernetes_probes_are_not_counted(client):
    client.get("/kubernetes/liveness")
    client.get("/kubernetes/ready")
    assert "/kubernetes/" not in scrape(client)


def test_info_endpoint_returns_version_and_commit(client):
    assert set(client.get("/actuator/info").get_json()) == {"version", "commit"}


def test_track_websocket_counts_up_and_down():
    before = sample("websocket_connections")
    with metrics.track_websocket():
        assert sample("websocket_connections") == before + 1
    assert sample("websocket_connections") == before


def test_track_websocket_decrements_on_error():
    before = sample("websocket_connections")
    with pytest.raises(RuntimeError):
        with metrics.track_websocket():
            raise RuntimeError("dropped")
    assert sample("websocket_connections") == before


def test_observe_delivery_records_a_sample():
    before = sample("chat_message_delivery_seconds_count")
    metrics.observe_delivery(time.time() - 0.05)
    assert sample("chat_message_delivery_seconds_count") == before + 1


def test_timed_query_records_by_operation():
    labels = {"operation": "demo_operation"}
    before = sample("db_query_duration_seconds_count", labels)

    @metrics.timed_query("demo_operation")
    def run():
        return "ok"

    assert run() == "ok"
    assert sample("db_query_duration_seconds_count", labels) == before + 1


def test_observe_delivery_iso_records_a_sample():
    from datetime import datetime, timezone

    before = sample("chat_message_delivery_seconds_count")
    metrics.observe_delivery_iso(datetime.now(timezone.utc).isoformat())
    assert sample("chat_message_delivery_seconds_count") == before + 1


def test_observe_delivery_iso_ignores_bad_values():
    before = sample("chat_message_delivery_seconds_count")
    metrics.observe_delivery_iso(None)
    metrics.observe_delivery_iso("not a date")
    assert sample("chat_message_delivery_seconds_count") == before


def test_websocket_route_counts_the_connection():
    import threading

    from simple_websocket import Client
    from werkzeug.serving import make_server

    server = make_server("127.0.0.1", 0, app_module.app, threaded=True)
    port = server.server_port
    threading.Thread(target=server.serve_forever, daemon=True).start()

    def wait_for(expected):
        deadline = time.time() + 3
        while time.time() < deadline:
            if sample("websocket_connections") == expected:
                return True
            time.sleep(0.05)
        return False

    before = sample("websocket_connections")
    try:
        ws = Client.connect(f"ws://127.0.0.1:{port}/api/message-ws")
        assert wait_for(before + 1)     # counted when the browser connects
        ws.close()
        assert wait_for(before)         # and counted back down when it leaves
    finally:
        server.shutdown()
