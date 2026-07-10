#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

CURRENT_BRANCH="$(git branch --show-current)"
if [[ "$CURRENT_BRANCH" != "main" ]]; then
  echo "Warning: current branch is '$CURRENT_BRANCH', not 'main'."
fi

git fetch origin
git pull --ff-only origin "$CURRENT_BRANCH"
python -m pip install -r requirements.txt
npm install
chmod +x scripts/*.sh
npm run check

if command -v pm2 >/dev/null 2>&1; then
  pm2 startOrReload ecosystem.config.js --update-env
  pm2 save
  pm2 status
else
  echo "Update complete. PM2 is not installed."
  echo "Run web: bash scripts/start_web.sh"
  echo "Run bot: bash scripts/start_bot.sh"
fi
