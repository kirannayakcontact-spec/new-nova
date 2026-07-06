# Titan Nova Setup Control Center

This repo contains a clean Git starter for Titan Nova with **2 runtime files**:

1. `flask_app.py` — Flask dashboard + Setup Tab Control Center + Firebase REST API.
2. `Gateway.js` — WhatsApp Gateway HTTP shell for health/sync/send endpoints.

Supporting install files:

- `requirements.txt`
- `package.json`
- `.gitignore`

## What this upgrade adds

- Setup tab no longer opens blank.
- Settings load with safe defaults.
- Settings save to Firebase path: `settings/setup`.
- Refresh/restart keeps saved values.
- Market add/save/delete.
- Firebase connection test.
- Gateway URL status check.
- Scraping/result toggles.
- Forward settings.
- Ledger payout settings.
- Backup download/restore.

## Termux install

```bash
pkg update -y
pkg install -y git python nodejs
git clone https://github.com/kirannayakcontact-spec/new-nova.git
cd new-nova
pip install -r requirements.txt
npm install
```

## Set Firebase URL

Use your own Firebase Realtime Database URL:

```bash
export FIREBASE_URL="https://YOUR-PROJECT-default-rtdb.firebaseio.com"
```

To make it permanent in Termux:

```bash
echo 'export FIREBASE_URL="https://YOUR-PROJECT-default-rtdb.firebaseio.com"' >> ~/.bashrc
source ~/.bashrc
```

## Run dashboard

Terminal 1:

```bash
cd ~/new-nova
python flask_app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Run gateway

Terminal 2:

```bash
cd ~/new-nova
npm start
```

Gateway health:

```text
http://127.0.0.1:3000/health
```

## Easy update command

After future Git updates, run:

```bash
cd ~/new-nova && git pull && pip install -r requirements.txt && npm install
```

## API routes

```text
GET  /api/setup/load
POST /api/setup/save
POST /api/setup/test-firebase
POST /api/setup/market/add
POST /api/setup/market/save
POST /api/setup/market/delete
GET  /api/setup/status
GET  /api/setup/backup/download
POST /api/setup/backup/download
POST /api/setup/backup/restore
```

## Important

`Gateway.js` is currently a stable HTTP control shell. Your existing Baileys WhatsApp logic can be merged into the marked adapter functions without changing the Flask Setup tab API.
