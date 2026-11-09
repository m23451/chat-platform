# ApiDown

**Alert:** Prometheus cannot scrape the chat API for 1 minute. Severity: critical.

## What it means
The API container has crashed, been stopped, or is not reachable on its metrics port.

## How to check
1. `docker ps -a | grep chat-api` - is the container running?
2. `docker logs --tail 50 <container>` - look for a crash or traceback.
3. `curl -s localhost:5000/metrics | head` - does it answer?
4. Grafana > Chat Platform > Uptime panel, and the Logs panel for the last errors.

## How to fix
1. Restart it: `docker compose restart <service>` (or `docker start <container>`).
2. If it keeps crashing, read the logs, then roll back to the previous version (the App version / commit panel shows what is deployed).
3. Confirm the alert clears and Uptime is counting again.
