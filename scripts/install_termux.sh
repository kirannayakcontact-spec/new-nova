#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if command -v pkg >/dev/null 2>&1; then
  pkg update -y
  pkg install -y git python nodejs
fi

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
npm install
chmod +x scripts/*.sh

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example. Edit FIREBASE_URL before production use."
fi

npm run check
npm test
bash scripts/install_nova_command.sh

echo "Titan Nova installation completed."
echo "From now on run: nova"
