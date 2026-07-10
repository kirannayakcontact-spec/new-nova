# Titan Nova

Production-oriented Flask dashboard and WhatsApp gateway for Termux, Linux, or PM2.

## Phase 1 security and stability

The official launchers now enable these protections automatically:

- Admin password login with secure Flask session cookies.
- Admin API token support through `X-Titan-Admin-Token`.
- VIP-scoped `/api/state` and `/api/payments` responses instead of exposing master data.
- Same-origin protection for dashboard write requests.
- Serialized Flask writes and Firebase ETag conditional writes.
- Gateway ETag protection that blocks stale full-state overwrites.
- Gateway binds to `127.0.0.1` by default.
- Gateway API token protection when non-loopback access is intentionally enabled.
- Missing/placeholder Firebase configuration blocks startup.
- Payment approval requests are serialized, preserving the existing idempotency checks.

Secrets are generated locally in `.env`; they are never committed to Git.

## One-command deployment

After the command is installed, use only:

```bash
nova
```

That command updates dependencies, runs checks, reloads PM2 services, performs health checks, and opens the dashboard.

Useful controls:

```bash
nova restart
nova status
nova logs
nova stop
```

To disable automatic browser opening for one run:

```bash
NOVA_OPEN_BROWSER=0 nova
```

## First secure setup

```bash
cd ~
git clone https://github.com/kirannayakcontact-spec/new-nova.git
cd new-nova
bash scripts/install_termux.sh
nano .env
```

Set the real Firebase URL:

```env
FIREBASE_URL=https://YOUR-PROJECT-default-rtdb.firebaseio.com/titan_master_data.json
```

The installer prints the generated admin password once. It is also stored locally in `.env` as `ADMIN_PASSWORD`.

Then start:

```bash
nova
```

Open `http://127.0.0.1:5000` and log in with that password.

## Existing installation

```bash
cd ~/new-nova
git pull
bash scripts/install_nova_command.sh
nova
```

On the first secure start, missing secrets are generated automatically. Check the terminal or `pm2 logs titan-web` for the generated admin password if it was newly created.

## Project structure

```text
new-nova/
├── flask_app.py                 # legacy feature core
├── Gateway.js                   # legacy gateway feature core
├── sitecustomize.py             # secures legacy direct Python start
├── backend/
│   ├── run.py
│   ├── wsgi.py
│   └── runtime.py               # login, authorization, Firebase CAS
├── bot/
│   ├── index.js
│   └── runtime_guard.js         # loopback/API auth, Firebase CAS
├── scripts/
│   ├── nova.sh
│   ├── ensure_runtime_env.py
│   ├── install_termux.sh
│   ├── start_web.sh
│   └── start_bot.sh
├── tests/
│   ├── test_structure.py
│   └── test_runtime_security.py
├── .github/workflows/ci.yml
├── .env.example
├── ecosystem.config.js
├── package.json
└── requirements.txt
```

The root feature files remain available for compatibility. Use the official scripts or `nova` so the runtime guards are active.

## Network policy

The web dashboard and gateway bind to loopback by default:

```env
HOST=127.0.0.1
GATEWAY_HOST=127.0.0.1
```

For deliberate LAN access, change `HOST=0.0.0.0`; admin login still protects the dashboard. Keep the gateway on loopback unless a trusted reverse proxy supplies `X-Titan-Gateway-Token`.

## Manual start

Session 1:

```bash
cd ~/new-nova
bash scripts/start_web.sh
```

Session 2:

```bash
cd ~/new-nova
bash scripts/start_bot.sh
```

Dashboard: `http://127.0.0.1:5000`

Gateway health: `http://127.0.0.1:3000/health`

## Validation

```bash
npm run check
npm test
python scripts/health_check.py
```

## Production entrypoint

```bash
gunicorn --bind 127.0.0.1:5000 backend.wsgi:app
```
