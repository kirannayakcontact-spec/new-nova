#!/usr/bin/env bash
set -Eeuo pipefail

REPO_URL="${TITAN_NOVA_REPO_URL:-https://github.com/kirannayakcontact-spec/new-nova.git}"
REPO_DIR="${TITAN_NOVA_DIR:-$HOME/new-nova}"
BRANCH="${TITAN_NOVA_BRANCH:-main}"
ACTION="${1:-deploy}"

log() {
  printf '\n[ NOVA ] %s\n' "$*"
}

warn() {
  printf '\n[ WARN ] %s\n' "$*" >&2
}

fail() {
  printf '\n[ ERROR ] %s\n' "$*" >&2
  exit 1
}

install_system_tools() {
  if command -v pkg >/dev/null 2>&1; then
    local missing=()
    command -v git >/dev/null 2>&1 || missing+=(git)
    command -v python >/dev/null 2>&1 || missing+=(python)
    command -v node >/dev/null 2>&1 || missing+=(nodejs)
    if ((${#missing[@]})); then
      log "Installing Termux tools: ${missing[*]}"
      pkg update -y
      pkg install -y "${missing[@]}"
    fi
  fi

  command -v git >/dev/null 2>&1 || fail "git is not installed"
  command -v python >/dev/null 2>&1 || fail "python is not installed"
  command -v node >/dev/null 2>&1 || fail "node is not installed"
  command -v npm >/dev/null 2>&1 || fail "npm is not installed"
}

ensure_repository() {
  if [[ -d "$REPO_DIR/.git" ]]; then
    return
  fi

  if [[ -e "$REPO_DIR" ]]; then
    fail "$REPO_DIR exists but is not a Git repository. Rename or remove it first."
  fi

  log "Repository not found. Cloning $REPO_URL"
  git clone --branch "$BRANCH" "$REPO_URL" "$REPO_DIR"
}

load_env() {
  cd "$REPO_DIR"
  if [[ ! -f .env && -f .env.example ]]; then
    cp .env.example .env
    warn ".env created from .env.example. Verify FIREBASE_URL when needed."
  fi

  if [[ -f .env ]]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
  fi
}

update_repository() {
  cd "$REPO_DIR"

  if [[ -n "$(git status --porcelain --untracked-files=normal)" ]]; then
    local stash_name="nova-auto-stash-$(date +%Y%m%d-%H%M%S)"
    warn "Local changes found. Saving them as Git stash: $stash_name"
    git stash push -u -m "$stash_name" >/dev/null
  fi

  log "Updating repository from origin/$BRANCH"
  git fetch origin "$BRANCH"

  if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
    git checkout "$BRANCH"
  else
    git checkout -b "$BRANCH" "origin/$BRANCH"
  fi

  git pull --ff-only origin "$BRANCH"
}

install_dependencies() {
  cd "$REPO_DIR"
  log "Installing Python dependencies"
  python -m pip install -r requirements.txt

  log "Installing Node dependencies"
  npm install
}

validate_project() {
  cd "$REPO_DIR"
  log "Running Python and Node checks"
  npm run check
  npm test
}

ensure_pm2() {
  if ! command -v pm2 >/dev/null 2>&1; then
    log "Installing PM2"
    npm install -g pm2
  fi
}

deploy_services() {
  cd "$REPO_DIR"
  ensure_pm2

  log "Starting or reloading Titan Nova services"
  pm2 startOrReload ecosystem.config.js --update-env
  pm2 save
  sleep 2
  pm2 status

  log "Runtime health check"
  python scripts/health_check.py || warn "A service may still be starting, or WhatsApp may need QR login."
}

show_status() {
  ensure_pm2
  pm2 status
  cd "$REPO_DIR"
  python scripts/health_check.py || true
}

show_logs() {
  ensure_pm2
  pm2 logs --lines "${2:-80}"
}

restart_services() {
  cd "$REPO_DIR"
  ensure_pm2
  pm2 startOrReload ecosystem.config.js --update-env
  pm2 save
  pm2 status
}

stop_services() {
  ensure_pm2
  pm2 stop titan-web titan-gateway || true
  pm2 status
}

install_system_tools
ensure_repository
load_env

case "$ACTION" in
  deploy|update|"")
    update_repository
    load_env
    install_dependencies
    validate_project
    deploy_services
    log "Complete: clone/update/install/check/restart/deploy finished"
    ;;
  restart)
    restart_services
    ;;
  status)
    show_status
    ;;
  logs)
    show_logs "$@"
    ;;
  stop)
    stop_services
    ;;
  *)
    cat <<'EOF'
Usage:
  nova          Clone/update/install/check/restart/deploy
  nova update   Same as nova
  nova restart  Restart PM2 services
  nova status   Show services and health
  nova logs     Show PM2 logs
  nova stop     Stop both services
EOF
    exit 2
    ;;
esac
