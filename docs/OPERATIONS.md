# Operations Runbook

## Daily checks

```bash
cd ~/new-nova
python scripts/health_check.py
pm2 status
```

Confirm:

- Flask responds on port 5000.
- Gateway responds on port 3000.
- WhatsApp is connected.
- Firebase reads and writes are healthy.
- Scheduled queues are not continuously growing.

## Logs

```bash
pm2 logs titan-web --lines 100
pm2 logs titan-gateway --lines 100
```

## WhatsApp relogin

1. Stop the gateway.
2. Back up the current auth directory if needed.
3. Remove `auth_info_baileys` only when the session is invalid.
4. Start the gateway and scan the new QR.

## Safe Git workflow

1. Make changes on a feature branch.
2. Run `npm run check` and `npm test`.
3. Open a pull request.
4. Review changed files and CI.
5. Merge to `main`.
6. Run `bash scripts/update_termux.sh` on the phone.
