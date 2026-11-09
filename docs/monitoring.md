# Monitoring stack

Run from the `monitoring/` folder:

    cd monitoring
    ./up.sh up -d

Prometheus: http://localhost:9090 (scrapes the chat API on port 5000 via host.docker.internal)

Alloy ships all Docker container logs to Loki. Query them in Grafana Explore with `{container="<name>"}`.
