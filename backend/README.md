# Backend

`flask_app.py` remains the compatibility runtime so existing Termux commands continue to work.

Use `backend.wsgi:app` for Gunicorn or another WSGI server:

```bash
gunicorn --bind 0.0.0.0:5000 backend.wsgi:app
```

Future backend extraction should place domain services, Firebase adapters, routes, and schemas in this package while preserving API compatibility.
