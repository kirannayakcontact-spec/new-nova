# Titan Nova Setup Control Center

Git patch added for the existing Titan Nova repo.

## Files

Existing runtime files are preserved:

- `flask_app.py` — original Flask app.
- `Gateway.js` — original gateway file.

New add-on file:

- `setup_control_center.py` — imports the existing Flask app, adds Setup Control Center routes, then runs the same app.

Supporting files:

- `requirements.txt`
- `package.json`

## What this adds

- Setup Control Center page.
- Settings save/load through Firebase root data.
- Settings path inside Firebase data: `settings/setup`.
- Market add/save/delete.
- Market changes update runtime `MARKETS`, `BASE_MARKETS`, and `CHART_LINKS` while this add-on is running.
- Firebase test API.
- Gateway health check API.
- Scraping/result toggles.
- Forward settings.
- Ledger payout settings.
- Backup download/restore.

## Termux update

If repo already exists:

```bash
cd ~/new-nova
git pull
pip install -r requirements.txt
npm install
```

If fresh install:

```bash
pkg update -y
pkg install -y git python nodejs
git clone https://github.com/kirannayakcontact-spec/new-nova.git
cd new-nova
pip install -r requirements.txt
npm install
```

## Run with Setup Control Center

Use this instead of `python flask_app.py`:

```bash
cd ~/new-nova
python setup_control_center.py
```

Open app:

```text
http://127.0.0.1:5000
```

Open Setup Control Center:

```text
http://127.0.0.1:5000/setup-control
```

## Gateway

In second Termux session:

```bash
cd ~/new-nova
node Gateway.js
```

Gateway health:

```text
http://127.0.0.1:3000/health
```

## API routes added

```text
GET  /api/setup/load
POST /api/setup/save
POST /api/setup/test-firebase
GET  /api/setup/status
POST /api/setup/market/add
POST /api/setup/market/save
POST /api/setup/market/delete
GET  /api/setup/backup/download
POST /api/setup/backup/download
POST /api/setup/backup/restore
```

## Important

`flask_app.py` was not overwritten. The safe way to test this patch is to run `python setup_control_center.py`. If something goes wrong, run the old app with `python flask_app.py`.
