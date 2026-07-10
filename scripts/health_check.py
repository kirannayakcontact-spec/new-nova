#!/usr/bin/env python3
"""Small dependency-free health checker for both Titan Nova runtimes."""

from __future__ import annotations

import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def fetch(url: str) -> tuple[bool, str]:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "Titan-Nova-Health/2.0"})
    try:
        with urlopen(request, timeout=5) as response:
            body = response.read(2048).decode("utf-8", errors="replace")
            return 200 <= response.status < 400, body
    except HTTPError as exc:
        return False, f"HTTP {exc.code}: {exc.reason}"
    except URLError as exc:
        return False, str(exc.reason)
    except Exception as exc:  # defensive CLI reporting
        return False, str(exc)


def compact(body: str) -> str:
    try:
        value = json.loads(body)
        return json.dumps(value, ensure_ascii=False)[:300]
    except Exception:
        return " ".join(body.split())[:300]


def main() -> int:
    web_port = os.getenv("WEB_PORT", "5000")
    gateway_port = os.getenv("GATEWAY_PORT", "3000")
    checks = [
        ("Flask", f"http://127.0.0.1:{web_port}/"),
        ("Gateway", f"http://127.0.0.1:{gateway_port}/health"),
    ]

    failed = False
    for name, url in checks:
        ok, body = fetch(url)
        marker = "OK" if ok else "FAIL"
        print(f"[{marker}] {name}: {url}")
        print(f"       {compact(body)}")
        failed = failed or not ok
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
