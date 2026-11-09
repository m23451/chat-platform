# SlowDatabaseQueries

**Alert:** database query p95 above 500ms for 5 minutes. Severity: warning.

## What it means
Queries are taking too long, which will also slow the API and message history.

## How to check
1. Grafana > Chat Platform > DB query p95 - which `operation` is slow?
2. `docker logs --tail 50 <database container>` for errors or lock warnings.
3. `docker stats --no-stream` - is the database short of CPU or memory?
4. Check connection counts in the database itself.

## How to fix
1. Restart the database container if it is unhealthy.
2. If one query is slow, look for a missing index or an unusually large result set.
3. Confirm DB p95 drops under 500ms and the alert clears.
