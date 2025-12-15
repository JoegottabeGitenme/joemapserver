#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Follow logs for specified service or all services
if [ -n "$1" ]; then
    docker compose logs -f "$1"
else
    docker compose logs -f
fi
