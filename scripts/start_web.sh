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
export WEB_PORT="${WEB_PORT:-${PORT:-5000}}"

exec python -m backend.run
