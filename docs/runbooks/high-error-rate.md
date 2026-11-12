# HighErrorRate

**Alert:** more than 5% of API requests returned 5xx for 5 minutes. Severity: critical.

## What it means
Users are getting server errors. Usually a bad deploy, or a dependency (database, Kafka) failing.

## How to check
1. Grafana > Chat Platform > Error rate and Request rate per endpoint - which path is failing?
2. Logs panel, or in Explore: `{container=~"chat-api.*"} |= "ERROR"`.
3. Check the dependencies are up: `docker ps` for the database and Kafka.
4. Was there a recent deploy? Compare the App version / commit panel with the time the errors started.

## How to fix
1. If a dependency is down, restart it and watch the error rate fall.
2. If it started after a deploy, roll back to the previous version.
3. Confirm the error rate is back under 5% and the alert clears.
