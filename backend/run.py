"""Development/Termux launcher with environment-backed configuration."""

from __future__ import annotations

import os

import flask_app


def configure() -> None:
    firebase_url = os.getenv("FIREBASE_URL", "").strip()
    if firebase_url:
        flask_app.FIREBASE_DB_URL = firebase_url


def main() -> None:
    configure()
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("WEB_PORT", os.getenv("PORT", "5000")))
    debug = os.getenv("FLASK_DEBUG", "0").strip().lower() in {"1", "true", "yes", "on"}
    flask_app.app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
