# Monitoring stack

Run from the `monitoring/` folder:

    cd monitoring
    ./up.sh up -d

Prometheus: http://localhost:9090 (scrapes the chat API on port 5000 via host.docker.internal)

Alloy ships all Docker container logs to Loki. Query them in Grafana Explore with `{container="<name>"}`.

Grafana: http://localhost:3000 (user `admin`; password comes from `monitoring/.env`, created by copying `monitoring/.env.example`).

## Dashboard
`monitoring/grafana/dashboards/chat-platform.json` is loaded automatically by Grafana provisioning.
If you edit the dashboard in the UI, re-export it (from `monitoring/`, with `.env` loaded):

    curl -s -u admin:$GRAFANA_ADMIN_PASSWORD localhost:3000/api/dashboards/uid/chat-platform \
      | jq '.dashboard | .id = null' > grafana/dashboards/chat-platform.json

then commit the changed file.

## Alerts
Rules are in `monitoring/prometheus/alerts.yml` (loaded via `rule_files`). Each has a runbook in `docs/runbooks/`.
Validate after editing: `./up.sh exec prometheus promtool check rules /etc/prometheus/alerts.yml`, then `./up.sh restart prometheus`.
See current alerts at http://localhost:9090/alerts.
