#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${RILL_PROJECT_DIR:-/srv/project}"
PORT="${RILL_PORT:-9009}"

exec rill start "${PROJECT_DIR}" --port "${PORT}" --no-open