# NoWebsocketConnections

**Alert:** zero active websocket connections for 10 minutes. Severity: warning.

## What it means
No browsers are connected. That can be normal when nobody is using the app, but it can also mean the websocket route or the Kafka consumer has failed, so messages are not reaching users.

## How to check
1. Grafana > Chat Platform > WebSocket connections - did it drop suddenly, or has it been zero for a while?
2. Open the chat page in a browser and see whether it connects (browser dev tools > Network > WS).
3. Logs panel for websocket or consumer errors; confirm the Kafka consumer is running.

## How to fix
1. If the route or consumer has failed, restart the API container.
2. If traffic is simply zero (out of hours), no action is needed; consider tuning the alert.
3. Confirm connections return above zero and the alert clears.
