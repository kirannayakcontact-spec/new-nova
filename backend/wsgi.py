"""WSGI entrypoint for Gunicorn and production servers."""

from __future__ import annotations

import os

import flask_app

firebase_url = os.getenv("FIREBASE_URL", "").strip()
if firebase_url:
    flask_app.FIREBASE_DB_URL = firebase_url

app = flask_app.app

__all__ = ["app"]
