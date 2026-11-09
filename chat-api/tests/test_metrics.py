import pytest
from flask import Flask
from prometheus_client import REGISTRY

import metrics


@pytest.fixture(scope="module")
def client():
    app = Flask(__name__)

    @app.get("/api/messages")
    def get_messages():
        return {"messages": []}

    @app.get("/actuator/health")
    def health():
        return {"status": "UP"}

    metrics.setup_metrics(app)
    return app.test_client()


def sample(name, labels=None):
    return REGISTRY.get_sample_value(name, labels or {}) or 0


def test_metrics_endpoint_serves_prometheus_text(client):
    client.get("/api/messages")
    resp = client.get("/actuator/metrics")
    assert resp.status_code == 200
    text = resp.get_data(as_text=True)
    assert "flask_http_request_total" in text
    assert "process_start_time_seconds" in text
    assert "app_info" in text


def test_requests_are_labelled_by_route(client):
    client.get("/api/messages")
    text = client.get("/actuator/metrics").get_data(as_text=True)
    assert 'url_rule="/api/messages"' in text


def test_actuator_probes_are_not_counted(client):
    client.get("/actuator/health")
    text = client.get("/actuator/metrics").get_data(as_text=True)
    assert 'url_rule="/actuator/health"' not in text


def test_info_endpoint_returns_version_and_commit(client):
    body = client.get("/actuator/info").get_json()
    assert set(body) == {"version", "commit"}


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
    import time
    before = sample("chat_message_delivery_seconds_count")
    metrics.observe_delivery(time.time() - 0.05)
    assert sample("chat_message_delivery_seconds_count") == before + 1


def test_timed_query_records_by_operation():
    labels = {"operation": "insert_message"}
    before = sample("db_query_duration_seconds_count", labels)

    @metrics.timed_query("insert_message")
    def insert():
        return "ok"

    assert insert() == "ok"
    assert sample("db_query_duration_seconds_count", labels) == before + 1
