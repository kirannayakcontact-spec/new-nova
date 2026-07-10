#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

export APP_TZ="${APP_TZ:-Asia/Kolkata}"
export PORT="${GATEWAY_PORT:-${PORT:-3000}}"

exec node --require ./gateway/roleRouter.js --require ./gateway/roleRouterUi.js Gateway.js
