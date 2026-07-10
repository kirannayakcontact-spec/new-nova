# Titan Nova

Production-oriented Flask dashboard and WhatsApp gateway for Termux, Linux, or PM2.

## Project structure

```text
new-nova/
├── flask_app.py                 # Flask dashboard/API runtime (compatibility entrypoint)
├── Gateway.js                  # WhatsApp gateway runtime (compatibility entrypoint)
├── backend/
│   ├── __init__.py
│   ├── wsgi.py                 # Gunicorn/WSGI entrypoint
│   └── README.md
├── bot/
│   ├── index.js                # Structured Node entrypoint
│   └── README.md
├── config/
│   └── README.md
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DEPLOYMENT_TERMUX.md
│   └── OPERATIONS.md
├── scripts/
│   ├── install_termux.sh
│   ├── update_termux.sh
│   ├── start_web.sh
│   ├── start_bot.sh
│   └── health_check.py
├── tests/
│   └── test_structure.py
├── .github/workflows/ci.yml
├── .env.example
├── .gitignore
├── ecosystem.config.js
├── package.json
├── requirements.txt
└── Procfile
```

The two original runtime entrypoints remain available so existing Termux commands do not break. New operational files are separated into clear backend, bot, configuration, deployment, documentation, and test layers.

## First installation in Termux

```bash
cd ~
git clone https://github.com/kirannayakcontact-spec/new-nova.git
cd new-nova
bash scripts/install_termux.sh
cp .env.example .env
```

Edit `.env` with your Firebase URL and runtime settings.

## Start manually

Open two Termux sessions.

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

## Update with one command

```bash
cd ~/new-nova && bash scripts/update_termux.sh
```

The script pulls the latest `main`, refreshes Python and Node dependencies, and reloads PM2 when PM2 is installed.

## PM2 mode

```bash
npm install -g pm2
pm run pm2:start
pm2 save
```

Useful commands:

```bash
npm run pm2:status
npm run pm2:logs
npm run pm2:restart
```

## Validation

```bash
npm run check
python -m unittest discover -s tests -v
python scripts/health_check.py
```

## Production entrypoint

For a Linux server with Gunicorn:

```bash
gunicorn --bind 0.0.0.0:5000 backend.wsgi:app
```

See `docs/ARCHITECTURE.md`, `docs/DEPLOYMENT_TERMUX.md`, and `docs/OPERATIONS.md` for details.
