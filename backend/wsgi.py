"""WSGI entrypoint for Gunicorn and production servers."""

from flask_app import app

__all__ = ["app"]
