# Titan Nova

Strict two-runtime-file mode:

1. `flask_app.py` — Flask dashboard/API.
2. `Gateway.js` — WhatsApp gateway.

No extra Python runtime file is required.

## Termux update

```bash
cd ~/new-nova
git pull
pip install -r requirements.txt
npm install
```

## Run web app

```bash
cd ~/new-nova
npm run web
```

This runs:

```bash
python flask_app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Run WhatsApp gateway

Open a second Termux session:

```bash
cd ~/new-nova
npm run bot
```

This runs:

```bash
node Gateway.js
```

## Setup Control Center target

The final Setup tab must live inside `flask_app.py`, not in a separate Python runtime file.

Required Firebase path:

```text
settings/setup
```

Required API routes:

```text
GET  /api/setup/load
POST /api/setup/save
POST /api/setup/test-firebase
POST /api/setup/market/add
POST /api/setup/market/save
POST /api/setup/market/delete
POST /api/setup/backup/download
POST /api/setup/backup/restore
GET  /api/setup/status
```

## Current repo cleanup

- Removed the extra `setup_control_center.py` runtime file.
- `npm run web` now points to `python flask_app.py`.
- `npm run bot` points to `node Gateway.js`.

## Important

Keep future upgrades inside the two runtime files only:

- Python changes go into `flask_app.py`.
- WhatsApp changes go into `Gateway.js`.
