"""Prometheus metrics for the chat API.

Endpoints (from the project brief):
  GET/POST /api/messages, WS /api/message-ws
  GET /actuator/liveness, /readiness, /health, /info, /metrics
"""
import os
import time
from contextlib import contextmanager
from functools import wraps

from flask import jsonify
from prometheus_client import Gauge, Histogram
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Counter

METRICS_PATH = "/actuator/metrics"

# Not user traffic: k8s probes, the metrics scrape itself, the websocket upgrade.
EXCLUDED_PATHS = [r"^/actuator/.*", r"^/kubernetes/.*", r"^/api/message-ws$"]

LATENCY_BUCKETS = (0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10)

# Request count per endpoint, latency histogram (for p95) and error rate come from
# flask_http_request_total and flask_http_request_duration_seconds.
# process_start_time_seconds (uptime) comes from prometheus_client automatically.
prom_metrics = PrometheusMetrics.for_app_factory(
    path=METRICS_PATH,
    group_by="url_rule",          # label by route, not raw URL, to keep cardinality low
    buckets=LATENCY_BUCKETS,
    excluded_paths=EXCLUDED_PATHS,
)

APP_VERSION = os.getenv("APP_VERSION", "unknown")
GIT_COMMIT = os.getenv("GIT_COMMIT", "unknown")

APP_INFO = Gauge("app_info", "Application info", ["version", "commit"])
APP_INFO.labels(version=APP_VERSION, commit=GIT_COMMIT).set(1)

WS_CONNECTIONS = Gauge("websocket_connections", "Active WebSocket connections")

DELIVERY_LATENCY = Histogram(
    "chat_message_delivery_seconds",
    "Time from message creation to push to browser",
    buckets=LATENCY_BUCKETS,
)

DB_QUERY_DURATION = Histogram(
    "db_query_duration_seconds",
    "Database query duration",
    ["operation"],
    buckets=LATENCY_BUCKETS,
)

MESSAGES_RECEIVED = Counter(
    "chat_messages_received_total",
    "Total messages received by the API"
)

MESSAGES_SAVED = Counter(
    "chat_messages_saved_total",
    "Total messages successfully saved to the database"
)

VALIDATION_ERRORS = Counter(
    "chat_validation_errors_total",
    "Total message validation failures"
)

# Kafka consumer metrics
MESSAGES_CONSUMED = Counter(
    "chat_messages_consumed_total",
    "Total messages consumed from Kafka"
)

CONSUMER_ERRORS = Counter(
    "chat_consumer_errors_total",
    "Total Kafka consumer processing errors"
)

MESSAGE_PROCESSING_DURATION = Histogram(
    "chat_message_processing_seconds",
    "Time taken to process a Kafka message",
    buckets=LATENCY_BUCKETS
)

def setup_metrics(app, info_endpoint=True):
    """Expose /actuator/metrics and track request metrics; optionally add /actuator/info."""
    prom_metrics.init_app(app)
    if info_endpoint:
        app.add_url_rule("/actuator/info", "actuator_info", _info)


def _info():
    return jsonify(version=APP_VERSION, commit=GIT_COMMIT)


@contextmanager
def track_websocket():
    """Wrap a websocket handler body: counts the connection up, and down on any exit."""
    WS_CONNECTIONS.inc()
    try:
        yield
    finally:
        WS_CONNECTIONS.dec()


def observe_delivery(created_at):
    """Call just before pushing a message to browsers. created_at is epoch seconds,
    stamped when the message was posted."""
    DELIVERY_LATENCY.observe(max(0.0, time.time() - created_at))


def timed_query(operation):
    """Decorator: time a database function, e.g. @timed_query("select_history")."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            with DB_QUERY_DURATION.labels(operation).time():
                return fn(*args, **kwargs)
        return wrapper
    return decorator


KAFKA_PUBLISH_ERRORS = Counter(
    "chat_kafka_publish_errors_total",
    "Messages saved to the database but not published to Kafka",
)
