"""Development/Termux launcher with validated runtime security."""

from __future__ import annotations

import os

import flask_app
from backend.runtime import configure_application


def main() -> None:
    app = configure_application(flask_app)
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("WEB_PORT", os.getenv("PORT", "5000")))
    debug = os.getenv("FLASK_DEBUG", "0").strip().lower() in {"1", "true", "yes", "on"}
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
