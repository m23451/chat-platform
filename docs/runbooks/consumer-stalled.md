# ConsumerStalled

**Alert:** messages are being saved but none have been consumed for 5 minutes. Severity: critical.

## What it means
The consumer thread is not delivering messages from Kafka. Browsers on this pod only receive the direct push, and other pods receive nothing.

## How to check
1. Grafana > Chat Platform > saved vs consumed panel.
2. API logs for "Kafka consumer connected" or repeated errors.
3. Is the `chat-messages` topic present, and is publishing working?

## How to fix
1. Restart the API so the consumer thread starts again.
2. Fix any Kafka problems first.
3. Confirm consumed messages start rising again and the alert clears.
