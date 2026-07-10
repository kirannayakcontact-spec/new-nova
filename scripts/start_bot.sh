#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

python scripts/ensure_runtime_env.py --prepare --validate

set -a
# shellcheck disable=SC1091
source .env
set +a

export APP_TZ="${APP_TZ:-Asia/Kolkata}"
export GATEWAY_HOST="${GATEWAY_HOST:-127.0.0.1}"
export PORT="${GATEWAY_PORT:-${PORT:-3000}}"

exec node bot/index.js
