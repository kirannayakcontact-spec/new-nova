# Configuration

Runtime secrets must be stored in the root `.env` file, which is excluded from Git.

Create it from the template:

```bash
cp .env.example .env
```

Never commit Firebase credentials, service-account JSON, WhatsApp session data, tokens, or private keys.
