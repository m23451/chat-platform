# WebsocketConnectionsNearLimit

**Alert:** 6 or more open websockets for 5 minutes. Severity: warning.

## What it means
Each open websocket holds one of the 8 gunicorn threads. At 8, normal requests and the liveness probe queue behind the connections, and Kubernetes may restart the pod.

## How to check
1. Grafana > Chat Platform > WebSocket connections panel.
2. Is traffic unusually high, or are connections leaking after browsers close?

## How to fix
1. Add API replicas, or raise the gunicorn thread count (owner of the Dockerfile and manifests).
2. If connections never drop after clients leave, report a connection leak to the API owner.
