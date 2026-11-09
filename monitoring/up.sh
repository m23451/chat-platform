#!/usr/bin/env bash
# Runs docker compose with every docker-compose.*.yml in this folder.
cd "$(dirname "$0")"
args=()
for f in docker-compose.*.yml; do args+=(-f "$f"); done
docker compose "${args[@]}" "$@"
