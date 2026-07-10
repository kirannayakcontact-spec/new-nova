# Titan Nova

Production-oriented Flask dashboard and WhatsApp gateway for Termux, Linux, or PM2.

## One-command deployment

After the command is installed, use only:

```bash
nova
```

That single command performs the complete workflow:

```text
Repository missing → clone
Repository present → pull latest main
Install/update Python and Node dependencies
Run syntax checks and tests
Start or reload titan-web and titan-gateway with PM2
Save PM2 process list
Show service and health status
```

Useful controls:

```bash
nova restart
nova status
nova logs
nova stop
```

## Install the `nova` command on an existing clone

```bash
cd ~/new-nova && git pull && bash scripts/install_nova_command.sh
```

After this one-time command, future clone/update/restart/deploy work requires only `nova`.

## Project structure

```text
new-nova/
├── flask_app.py
├── Gateway.js
├── backend/
│   ├── __init__.py
│   ├── run.py
│   ├── wsgi.py
│   └── README.md
├── bot/
│   ├── index.js
│   └── README.md
├── config/
│   └── README.md
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DEPLOYMENT_TERMUX.md
│   └── OPERATIONS.md
├── scripts/
│   ├── nova.sh
│   ├── install_nova_command.sh
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

The original runtime entrypoints remain available so existing Termux commands do not break.

## First installation without an existing clone

```bash
cd ~
git clone https://github.com/kirannayakcontact-spec/new-nova.git
cd new-nova
bash scripts/install_termux.sh
nova
```

The installer creates `.env` from `.env.example` when it is missing. Verify `FIREBASE_URL` before production use.

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
gunicorn --bind 0.0.0.0:5000 backend.wsgi:app
```
