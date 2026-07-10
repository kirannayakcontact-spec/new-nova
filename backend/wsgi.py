"""Validated WSGI entrypoint for Gunicorn and production servers."""

from __future__ import annotations

import flask_app
from backend.runtime import configure_application

app = configure_application(flask_app)

__all__ = ["app"]
