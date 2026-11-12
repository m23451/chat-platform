# ConsumerErrors

**Alert:** the Kafka consumer has been hitting errors for 5 minutes. Severity: warning.

## What it means
The consumer loop is failing and retrying every 5 seconds, usually because Kafka is unreachable.

## How to check
1. Grafana > Chat Platform > consumer errors panel.
2. API logs: "Kafka consumer error, retrying".
3. Is Kafka up and reachable from the API?

## How to fix
1. Restore Kafka (see the KafkaPublishFailing runbook).
2. The consumer reconnects by itself within about 5 seconds.
3. Confirm the error counter stops rising and the alert clears.
