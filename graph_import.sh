#!/usr/bin/env bash
set -euo pipefail

ARGS=(
  database
  import
  full
  neo4j
  --overwrite-destination=true
)

# Nodes
for f in /import/node/*.csv; do
    label=$(basename "$f" .csv)
    ARGS+=(--nodes="${label}=${f}")
done

# Relationships
for f in /import/relationship/*.csv; do
    type=$(basename "$f" .csv)
    ARGS+=(--relationships="${type}=${f}")
done


exec neo4j-admin "${ARGS[@]}"