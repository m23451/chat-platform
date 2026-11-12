# KafkaPublishFailing

**Alert:** publishing to Kafka has been failing for 5 minutes. Severity: critical.

## What it means
Messages are saved to the database and pushed to connected browsers, but never reach Kafka. The API still returns 201, so users do not see an error, and other pods do not receive the messages.

## How to check
1. Grafana > Chat Platform > Kafka publish errors panel, and the API logs for "Kafka publish failed".
2. Is Kafka running? `docker compose ps` in chat-api (or the Kafka pod in Kubernetes).
3. Is the broker address right? Check `KAFKA_BROKER_URL` for the API.

## How to fix
1. Start or restart Kafka and wait about 30 seconds (after a crash, ZooKeeper can hold a stale registration and Kafka fails once at startup).
2. If the logs show a code error, report it to the API owner.
3. Confirm the error rate returns to zero and the alert clears.
