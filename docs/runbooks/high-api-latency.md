# HighApiLatency

**Alert:** API p95 latency above 500ms for 5 minutes. Severity: warning.

## What it means
Requests are slow. Usually a slow database, a CPU-starved host, or an unusual spike in traffic.

## How to check
1. Grafana > Chat Platform > API p95 latency and Request rate per endpoint - which path, and did traffic jump?
2. DB query p95 panel - is the database the slow part?
3. Host load: `docker stats --no-stream` and `uptime`.

## How to fix
1. If the database is slow, follow the SlowDatabaseQueries runbook.
2. If it is traffic or CPU, scale up the host or reduce load.
3. Confirm p95 is back under 500ms and the alert clears.
