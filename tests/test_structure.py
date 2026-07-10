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
            "gateway/roleRouter.js",
            "backend/run.py",
            "backend/wsgi.py",
            "bot/index.js",
            "scripts/nova.sh",
            "scripts/install_nova_command.sh",
            "scripts/start_web.sh",
            "scripts/start_bot.sh",
            "ecosystem.config.js",
            ".env.example",
        ]
        missing = [path for path in required if not (ROOT / path).is_file()]
        self.assertEqual(missing, [], f"Missing required files: {missing}")

    def test_python_entrypoints_compile(self) -> None:
        for relative in ("flask_app.py", "backend/run.py", "backend/wsgi.py", "scripts/health_check.py"):
            py_compile.compile(str(ROOT / relative), doraise=True)

    def test_package_scripts_exist(self) -> None:
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        scripts = package.get("scripts", {})
        for name in ("web", "bot", "check", "test", "pm2:start"):
            self.assertIn(name, scripts)
        self.assertIn("gateway/roleRouter.js", scripts.get("check:node", ""))

    def test_role_router_environment_keys_are_documented(self) -> None:
        env_example = (ROOT / ".env.example").read_text(encoding="utf-8")
        for key in (
            "ROLE_ROUTER_ENABLED",
            "KALYAN_ADMIN_GROUP",
            "KALYAN_INTEL_GROUP",
            "KALYAN_RESULT_GROUP",
            "BOOKIE_LOAD_REPORT_GROUP",
        ):
            self.assertIn(key, env_example)

    def test_nova_command_has_expected_actions(self) -> None:
        content = (ROOT / "scripts/nova.sh").read_text(encoding="utf-8")
        for action in ("deploy", "update", "restart", "status", "logs", "stop"):
            self.assertIn(action, content)
        self.assertIn("git clone", content)
        self.assertIn("pm2 startOrReload", content)

    def test_nova_opens_dashboard_after_deploy(self) -> None:
        content = (ROOT / "scripts/nova.sh").read_text(encoding="utf-8")
        self.assertIn("open_dashboard", content)
        self.assertIn("com.android.chrome", content)
        self.assertIn("termux-open-url", content)
        self.assertIn("http://127.0.0.1", content)

    def test_secrets_are_ignored(self) -> None:
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".env", ignore)
        self.assertIn("auth_info_baileys/", ignore)


if __name__ == "__main__":
    unittest.main()
