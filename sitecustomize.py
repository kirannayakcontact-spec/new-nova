"""Auto-enable Titan Nova runtime guards for the legacy `python flask_app.py` command."""

from __future__ import annotations

import sys

try:
    from flask import Flask
except Exception:  # Dependencies may not be installed during bootstrap commands.
    Flask = None


if Flask is not None and not getattr(Flask, "_titan_runtime_guard_installed", False):
    _original_run = Flask.run

    def _guarded_run(self, *args, **kwargs):
        module = sys.modules.get("__main__")
        if module is not None and getattr(module, "app", None) is self:
            from backend.runtime import configure_application

            configure_application(module)
        return _original_run(self, *args, **kwargs)

    Flask.run = _guarded_run
    Flask._titan_runtime_guard_installed = True
