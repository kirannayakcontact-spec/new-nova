from __future__ import annotations

import json
import py_compile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ProjectStructureTests(unittest.TestCase):
    def test_required_files_exist(self) -> None:
        required = [
            "flask_app.py",
            "Gateway.js",
            "backend/wsgi.py",
            "bot/index.js",
            "scripts/start_web.sh",
            "scripts/start_bot.sh",
            "ecosystem.config.js",
            ".env.example",
        ]
        missing = [path for path in required if not (ROOT / path).is_file()]
        self.assertEqual(missing, [], f"Missing required files: {missing}")

    def test_python_entrypoints_compile(self) -> None:
        for relative in ("flask_app.py", "backend/wsgi.py", "scripts/health_check.py"):
            py_compile.compile(str(ROOT / relative), doraise=True)

    def test_package_scripts_exist(self) -> None:
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        scripts = package.get("scripts", {})
        for name in ("web", "bot", "check", "test", "pm2:start"):
            self.assertIn(name, scripts)

    def test_secrets_are_ignored(self) -> None:
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".env", ignore)
        self.assertIn("auth_info_baileys/", ignore)


if __name__ == "__main__":
    unittest.main()
