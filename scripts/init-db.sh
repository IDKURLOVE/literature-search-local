#!/usr/bin/env bash
set -euo pipefail
# Optional helper for bare-metal Postgres bootstrap (Compose already creates the DB).
echo "LitScope uses Docker Compose by default. Prefer: docker compose up -d --build"
