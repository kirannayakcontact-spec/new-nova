#!/usr/bin/env bash
set -Eeuo pipefail

REPO_URL="${TITAN_NOVA_REPO_URL:-https://github.com/kirannayakcontact-spec/new-nova.git}"
REPO_DIR="${TITAN_NOVA_DIR:-$HOME/new-nova}"
BRANCH="${TITAN_NOVA_BRANCH:-main}"

if [[ -n "${PREFIX:-}" && -d "$PREFIX/bin" ]]; then
  BIN_DIR="$PREFIX/bin"
else
  BIN_DIR="$HOME/.local/bin"
  mkdir -p "$BIN_DIR"
fi

COMMAND_PATH="$BIN_DIR/nova"

cat > "$COMMAND_PATH" <<EOF
#!/usr/bin/env bash
set -Eeuo pipefail

REPO_URL="\${TITAN_NOVA_REPO_URL:-$REPO_URL}"
REPO_DIR="\${TITAN_NOVA_DIR:-$REPO_DIR}"
BRANCH="\${TITAN_NOVA_BRANCH:-$BRANCH}"

if ! command -v git >/dev/null 2>&1; then
  if command -v pkg >/dev/null 2>&1; then
    pkg update -y
    pkg install -y git python nodejs
  else
    echo "git is required" >&2
    exit 1
  fi
fi

if [[ ! -d "\$REPO_DIR/.git" ]]; then
  if [[ -e "\$REPO_DIR" ]]; then
    echo "\$REPO_DIR exists but is not a Git repository." >&2
    exit 1
  fi
  git clone --branch "\$BRANCH" "\$REPO_URL" "\$REPO_DIR"
fi

exec bash "\$REPO_DIR/scripts/nova.sh" "\$@"
EOF

chmod +x "$COMMAND_PATH"

printf '\nTitan Nova command installed: %s\n' "$COMMAND_PATH"
printf 'From now on run only:\n\n  nova\n\n'

if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
  printf 'Add this directory to PATH: %s\n' "$BIN_DIR"
fi
