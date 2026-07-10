from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RuntimeSecurityTests(unittest.TestCase):
    def test_python_runtime_has_auth_and_conditional_writes(self) -> None:
        content = (ROOT / "backend/runtime.py").read_text(encoding="utf-8")
        for marker in ("/login", "ADMIN_PASSWORD", "If-Match", "FirebaseConflictError", "SESSION_COOKIE_HTTPONLY"):
            self.assertIn(marker, content)

    def test_gateway_is_loopback_first_and_uses_etags(self) -> None:
        content = (ROOT / "bot/runtime_guard.js").read_text(encoding="utf-8")
        for marker in ("127.0.0.1", "GATEWAY_API_TOKEN", "If-Match", "X-Firebase-ETag", "timingSafeEqual"):
            self.assertIn(marker, content)

    def test_official_launchers_validate_environment(self) -> None:
        web = (ROOT / "scripts/start_web.sh").read_text(encoding="utf-8")
        bot = (ROOT / "scripts/start_bot.sh").read_text(encoding="utf-8")
        self.assertIn("ensure_runtime_env.py --prepare --validate", web)
        self.assertIn("ensure_runtime_env.py --prepare --validate", bot)
        self.assertIn("node bot/index.js", bot)

    def test_env_helpers_detect_placeholders(self) -> None:
        path = ROOT / "scripts/ensure_runtime_env.py"
        spec = importlib.util.spec_from_file_location("ensure_runtime_env", path)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        self.assertTrue(module.placeholder("https://your-project.firebaseio.com"))
        self.assertFalse(module.placeholder("https://real-project-default-rtdb.firebaseio.com"))
        parsed = module.parse_env("A=1\n# comment\nB='two'\n")
        self.assertEqual(parsed, {"A": "1", "B": "two"})


if __name__ == "__main__":
    unittest.main()
