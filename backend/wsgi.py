"""WSGI entrypoint for Gunicorn and production servers."""

from __future__ import annotations

import os

import flask_app
from backend.role_router_proxy import register_role_router_proxy

firebase_url = os.getenv("FIREBASE_URL", "").strip()
if firebase_url:
    flask_app.FIREBASE_DB_URL = firebase_url

gateway_port = os.getenv("GATEWAY_PORT", "3000").strip() or "3000"
register_role_router_proxy(flask_app.app, f"http://127.0.0.1:{gateway_port}")

app = flask_app.app

__all__ = ["app"]
