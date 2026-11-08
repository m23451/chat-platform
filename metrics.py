import os

from prometheus_client import Gauge, Histogram
from prometheus_flask_exporter import PrometheusMetrics

metrics = PrometheusMetrics.for_app_factory()


def setup_metrics(app):
    """Request count, latency and errors per endpoint, exposed at /metrics."""
    metrics.init_app(app)


APP_INFO = Gauge("app_info", "Application info", ["version", "commit"])
APP_INFO.labels(
    version=os.getenv("APP_VERSION", "unknown"),
    commit=os.getenv("GIT_COMMIT", "unknown"),
).set(1)
