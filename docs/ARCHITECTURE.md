# Titan Nova Architecture

## Runtime services

### Flask dashboard/API

- Entrypoint: `flask_app.py`
- Production WSGI import: `backend.wsgi:app`
- Default port: `5000`
- Responsibilities: dashboard UI, REST APIs, Firebase state management, ledger, wallet, payments, results, setup, backup, and health controls.

### WhatsApp gateway

- Entrypoint: `Gateway.js`
- Structured alias: `bot/index.js`
- Default port: `3000`
- Responsibilities: Baileys session, group/contact synchronization, scheduled delivery, result forwarding, message parsing, and gateway health.

## Data flow

```text
Browser/Admin
    |
    v
Flask dashboard/API ---- Firebase Realtime Database
    |
    | localhost HTTP
    v
WhatsApp Gateway ------- WhatsApp/Baileys
```

## Compatibility policy

The root runtime files are intentionally preserved during this migration. This avoids breaking existing Termux commands and preserves the gateway authentication directory location.

## Refactor boundaries

Future code extraction should follow these boundaries:

1. `backend/routes/` for Flask blueprints.
2. `backend/services/` for ledger, wallet, result, payment, and setup services.
3. `backend/infrastructure/` for Firebase and HTTP clients.
4. `bot/services/` for WhatsApp delivery, scraping, schedules, and guard logic.
5. `shared/` for documented cross-runtime message contracts.

Each extraction should be delivered as a separate tested pull request rather than rewriting all business logic at once.
