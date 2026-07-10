#!/usr/bin/env python3
"""Prepare and validate Titan Nova's .env without exposing secrets to Git."""

from __future__ import annotations

import argparse
import secrets
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
EXAMPLE_PATH = ROOT / ".env.example"

GENERATED = {
    "ADMIN_PASSWORD": lambda: secrets.token_urlsafe(14),
    "FLASK_SECRET_KEY": lambda: secrets.token_urlsafe(48),
    "ADMIN_API_TOKEN": lambda: secrets.token_urlsafe(36),
    "GATEWAY_API_TOKEN": lambda: secrets.token_urlsafe(36),
}


def parse_env(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def placeholder(value: str) -> bool:
    lowered = str(value or "").lower()
    return not lowered or any(x in lowered for x in ("your-project", "change-me", "changeme", "replace_me", "placeholder", "example.com"))


def append_value(path: Path, key: str, value: str) -> None:
    with path.open("a", encoding="utf-8") as handle:
        if path.stat().st_size:
            handle.write("\n")
        handle.write(f"{key}={value}\n")


def prepare() -> dict[str, str]:
    if not ENV_PATH.exists():
        if not EXAMPLE_PATH.exists():
            raise SystemExit(".env.example is missing")
        ENV_PATH.write_text(EXAMPLE_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        print("Created .env from .env.example")

    values = parse_env(ENV_PATH.read_text(encoding="utf-8"))
    generated_now: dict[str, str] = {}
    for key, factory in GENERATED.items():
        current = values.get(key, "")
        minimum = 10 if key == "ADMIN_PASSWORD" else 24
        if placeholder(current) or len(current) < minimum:
            value = factory()
            append_value(ENV_PATH, key, value)
            values[key] = value
            generated_now[key] = value

    if "ADMIN_PASSWORD" in generated_now:
        print("\nIMPORTANT — Titan Nova admin password generated:")
        print(generated_now["ADMIN_PASSWORD"])
        print("Save this password securely. It is stored only in your local .env.\n")
    return values


def validate(values: dict[str, str]) -> None:
    errors: list[str] = []
    firebase = values.get("FIREBASE_URL", "").strip().rstrip("/")
    if placeholder(firebase):
        errors.append("FIREBASE_URL is missing or still a placeholder")
    else:
        parsed = urlparse(firebase)
        if parsed.scheme != "https" or not parsed.netloc:
            errors.append("FIREBASE_URL must be a valid https:// URL")
    for key in GENERATED:
        minimum = 10 if key == "ADMIN_PASSWORD" else 24
        if placeholder(values.get(key, "")) or len(values.get(key, "")) < minimum:
            errors.append(f"{key} is missing or too short")
    if errors:
        raise SystemExit("Runtime configuration invalid:\n- " + "\n- ".join(errors))
    print("Runtime environment validation: OK")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true", help="Create .env and generate missing secrets")
    parser.add_argument("--validate", action="store_true", help="Validate Firebase and generated secrets")
    args = parser.parse_args()
    values = prepare() if args.prepare or not ENV_PATH.exists() else parse_env(ENV_PATH.read_text(encoding="utf-8"))
    if args.validate:
        validate(values)


if __name__ == "__main__":
    main()
