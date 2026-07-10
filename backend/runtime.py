"""Runtime safety layer for Titan Nova.

This module is deliberately kept outside the legacy single-file application so
security and data-integrity controls can be enabled without rewriting the
existing dashboard feature set.
"""

from __future__ import annotations

import datetime as _dt
import hmac
import html
import os
import threading
from collections import defaultdict, deque
from functools import wraps
from typing import Any
from urllib.parse import urlparse

import requests
from flask import Response, g, jsonify, redirect, request, session, url_for


class RuntimeConfigurationError(RuntimeError):
    """Raised when a required production setting is missing or unsafe."""


class FirebaseConflictError(RuntimeError):
    """Raised when Firebase rejects a stale conditional write."""


_FIREBASE_CONTEXT = threading.local()
_WRITE_LOCK = threading.RLock()
_LOGIN_LOCK = threading.Lock()
_LOGIN_ATTEMPTS: dict[str, deque[_dt.datetime]] = defaultdict(deque)
_CONFIGURED_APP_IDS: set[int] = set()


def _is_placeholder(value: str) -> bool:
    lowered = value.strip().lower()
    return not lowered or any(
        token in lowered
        for token in (
            "your-project",
            "change-me",
            "changeme",
            "example.com",
            "replace_me",
            "placeholder",
        )
    )


def normalize_firebase_url(raw: str) -> str:
    value = str(raw or "").strip().strip('"').strip("'").rstrip("/")
    if _is_placeholder(value):
        raise RuntimeConfigurationError(
            "FIREBASE_URL is missing or still contains a placeholder. "
            "Set the real Realtime Database URL in .env before starting Titan Nova."
        )
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise RuntimeConfigurationError("FIREBASE_URL must be a valid https:// URL.")
    if not value.endswith(".json"):
        value += "/titan_master_data.json"
    return value


def _require_secret(name: str, minimum: int = 16) -> str:
    value = str(os.getenv(name, "")).strip()
    if _is_placeholder(value) or len(value) < minimum:
        raise RuntimeConfigurationError(
            f"{name} is missing or too short. Run scripts/ensure_runtime_env.py --prepare."
        )
    return value


def validate_runtime_environment() -> dict[str, str]:
    return {
        "firebase_url": normalize_firebase_url(os.getenv("FIREBASE_URL", "")),
        "admin_password": _require_secret("ADMIN_PASSWORD", 10),
        "flask_secret_key": _require_secret("FLASK_SECRET_KEY", 32),
        "admin_api_token": _require_secret("ADMIN_API_TOKEN", 24),
    }


def _same_origin() -> bool:
    source = request.headers.get("Origin") or request.headers.get("Referer")
    if not source:
        return False
    try:
        source_parsed = urlparse(source)
        host_parsed = urlparse(request.host_url)
        return (
            source_parsed.scheme.lower(),
            source_parsed.netloc.lower(),
        ) == (
            host_parsed.scheme.lower(),
            host_parsed.netloc.lower(),
        )
    except Exception:
        return False


def _token_authorized(admin_api_token: str) -> bool:
    supplied = request.headers.get("X-Titan-Admin-Token", "")
    return bool(supplied) and hmac.compare_digest(supplied, admin_api_token)


def _admin_authorized(admin_api_token: str) -> bool:
    return bool(session.get("titan_admin")) or _token_authorized(admin_api_token)


def _login_rate_limited(ip: str) -> bool:
    now = _dt.datetime.now(_dt.timezone.utc)
    cutoff = now - _dt.timedelta(minutes=15)
    with _LOGIN_LOCK:
        attempts = _LOGIN_ATTEMPTS[ip]
        while attempts and attempts[0] < cutoff:
            attempts.popleft()
        return len(attempts) >= 8


def _record_login_failure(ip: str) -> None:
    with _LOGIN_LOCK:
        _LOGIN_ATTEMPTS[ip].append(_dt.datetime.now(_dt.timezone.utc))


def _clear_login_failures(ip: str) -> None:
    with _LOGIN_LOCK:
        _LOGIN_ATTEMPTS.pop(ip, None)


def _login_page(error: str = "") -> str:
    safe_error = html.escape(error)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Titan Nova Login</title><style>
body{{margin:0;min-height:100vh;display:grid;place-items:center;background:#17212b;color:#fff;font-family:Arial,sans-serif}}
.card{{width:min(390px,calc(100% - 34px));background:#232e3c;border:1px solid #33465b;border-radius:20px;padding:26px;box-sizing:border-box;box-shadow:0 20px 60px #0008}}
h1{{margin:0 0 8px;font-size:24px}}p{{color:#8facbf;font-size:13px;line-height:1.5}}input{{width:100%;box-sizing:border-box;padding:14px;border-radius:12px;border:1px solid #40546b;background:#17212b;color:#fff;font-size:16px;margin:12px 0}}
button{{width:100%;padding:14px;border:0;border-radius:12px;background:#2aabee;color:#fff;font-weight:800;font-size:14px}}.error{{color:#ff7777;min-height:18px}}
</style></head><body><form class="card" method="post" action="/login">
<h1>🔐 Titan Nova Admin</h1><p>Admin dashboard kholne ke liye password enter karein.</p>
<div class="error">{safe_error}</div><input type="password" name="password" autocomplete="current-password" required autofocus placeholder="Admin password">
<button type="submit">LOGIN</button></form></body></html>"""


def _isolated_vip_state(full_state: dict[str, Any], vip_id: str, module: Any) -> dict[str, Any]:
    profile = (full_state.get("profiles") or {}).get(vip_id)
    if not isinstance(profile, dict):
        raise KeyError(vip_id)

    default_wallet = getattr(module, "_default_wallet_settings", lambda: {})
    default_entry = getattr(module, "_default_entry_settings", lambda: {})
    default_settlement = getattr(module, "_default_settlement_settings", lambda: {})
    default_payment = getattr(module, "_default_payment_settings", lambda: {})
    default_forwarder = getattr(module, "_default_load_forwarder_settings", lambda: {})
    default_guard = getattr(module, "_default_spam_guard_settings", lambda: {})

    user_payments = [p for p in full_state.get("payments", []) if p.get("userId") == vip_id]
    user_entries = [e for e in full_state.get("entries", []) if e.get("userId") == vip_id]
    return {
        "activeId": vip_id,
        "broadcasts": full_state.get("broadcasts", []),
        "profiles": {vip_id: profile},
        "paymentMethods": full_state.get("paymentMethods", {"upi": "", "phone": "", "qr": ""}),
        "payments": user_payments,
        "resultRecords": full_state.get("resultRecords", {}),
        "resultTargets": [],
        "resultSettings": full_state.get("resultSettings", {"autoScrapeEnabled": True, "useForwardTargetsForResults": True}),
        "wallets": {vip_id: (full_state.get("wallets") or {}).get(vip_id, {})},
        "walletSettings": full_state.get("walletSettings", default_wallet()),
        "entrySettings": full_state.get("entrySettings", default_entry()),
        "entries": user_entries,
        "settlementRecords": full_state.get("settlementRecords", {}),
        "settlementSettings": full_state.get("settlementSettings", default_settlement()),
        "paymentSettings": full_state.get("paymentSettings", default_payment()),
        "loadForwarder": full_state.get("loadForwarder", default_forwarder()),
        "loadForwarderOutbox": [],
        "spamGuardSettings": full_state.get("spamGuardSettings", default_guard()),
        "spamGuardEvents": [],
        "settings": full_state.get("settings", {}),
        "deletedMarkets": full_state.get("deletedMarkets", []),
    }


def _install_firebase_guards(module: Any, firebase_url: str) -> None:
    module.FIREBASE_DB_URL = firebase_url

    def guarded_load_from_firebase() -> dict[str, Any] | None:
        response = requests.get(
            firebase_url,
            timeout=15,
            headers={"X-Firebase-ETag": "true", "Cache-Control": "no-cache"},
        )
        response.raise_for_status()
        _FIREBASE_CONTEXT.etag = response.headers.get("ETag") or response.headers.get("etag")
        _FIREBASE_CONTEXT.url = firebase_url
        payload = response.json()
        return payload if payload else None

    def guarded_save_to_firebase(data: Any) -> bool:
        etag = getattr(_FIREBASE_CONTEXT, "etag", "")
        if getattr(_FIREBASE_CONTEXT, "url", "") != firebase_url:
            etag = ""
        if not etag:
            current = requests.get(
                firebase_url,
                timeout=15,
                headers={"X-Firebase-ETag": "true", "Cache-Control": "no-cache"},
            )
            current.raise_for_status()
            etag = current.headers.get("ETag") or current.headers.get("etag")
        headers = {"Cache-Control": "no-cache"}
        if etag:
            headers["If-Match"] = etag
        response = requests.put(firebase_url, json=data, timeout=20, headers=headers)
        if response.status_code == 412:
            raise FirebaseConflictError(
                "Firebase data changed in another process. The stale write was blocked; refresh and retry."
            )
        response.raise_for_status()
        _FIREBASE_CONTEXT.etag = response.headers.get("ETag") or response.headers.get("etag") or ""
        _FIREBASE_CONTEXT.url = firebase_url
        return True

    module.load_from_firebase = guarded_load_from_firebase
    module.save_to_firebase = guarded_save_to_firebase


def _replace_api_views(app: Any, module: Any, admin_api_token: str) -> None:
    rules = {rule.rule: rule.endpoint for rule in app.url_map.iter_rules()}

    state_endpoint = rules.get("/api/state")
    if state_endpoint:
        original_state_view = app.view_functions[state_endpoint]

        @wraps(original_state_view)
        def protected_state_view() -> Response:
            if _admin_authorized(admin_api_token):
                return original_state_view()
            vip_id = str(session.get("titan_vip_id") or "")
            if not vip_id:
                return jsonify({"status": "error", "message": "Authentication required"}), 401
            full_state = module.migrate_and_get_state()
            try:
                return jsonify(_isolated_vip_state(full_state, vip_id, module))
            except KeyError:
                session.pop("titan_vip_id", None)
                return jsonify({"status": "error", "message": "VIP access is no longer valid"}), 403

        app.view_functions[state_endpoint] = protected_state_view

    payments_endpoint = rules.get("/api/payments")
    if payments_endpoint:
        original_payments_view = app.view_functions[payments_endpoint]

        @wraps(original_payments_view)
        def protected_payments_view() -> Response:
            if _admin_authorized(admin_api_token):
                return original_payments_view()
            vip_id = str(session.get("titan_vip_id") or "")
            if not vip_id:
                return jsonify({"status": "error", "message": "Authentication required"}), 401
            full_state = module.migrate_and_get_state()
            payments = [p for p in full_state.get("payments", []) if p.get("userId") == vip_id]
            return jsonify(
                {
                    "status": "success",
                    "payments": payments,
                    "paymentSettings": full_state.get("paymentSettings", {}),
                    "wallets": {vip_id: (full_state.get("wallets") or {}).get(vip_id, {})},
                    "paymentOutbox": [],
                }
            )

        app.view_functions[payments_endpoint] = protected_payments_view


def configure_application(module: Any) -> Any:
    """Validate configuration and attach security/integrity controls once."""

    app = module.app
    if id(app) in _CONFIGURED_APP_IDS:
        return app

    settings = validate_runtime_environment()
    admin_password = settings["admin_password"]
    admin_api_token = settings["admin_api_token"]
    firebase_url = settings["firebase_url"]

    app.secret_key = settings["flask_secret_key"]
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=str(os.getenv("SESSION_COOKIE_SECURE", "0")).lower() in {"1", "true", "yes"},
        PERMANENT_SESSION_LIFETIME=_dt.timedelta(hours=12),
        MAX_CONTENT_LENGTH=int(os.getenv("MAX_REQUEST_BYTES", str(4 * 1024 * 1024))),
    )

    _install_firebase_guards(module, firebase_url)

    @app.route("/login", methods=["GET", "POST"], endpoint="titan_security_login")
    def titan_security_login() -> Response | str:
        if request.method == "GET":
            if _admin_authorized(admin_api_token):
                return redirect(url_for("index"))
            return _login_page()
        ip = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",")[0].strip()
        if _login_rate_limited(ip):
            return _login_page("Too many failed attempts. 15 minutes baad retry karein."), 429
        supplied = str(request.form.get("password", ""))
        if not hmac.compare_digest(supplied, admin_password):
            _record_login_failure(ip)
            return _login_page("Wrong password."), 401
        _clear_login_failures(ip)
        session.clear()
        session["titan_admin"] = True
        session.permanent = True
        return redirect(url_for("index"))

    @app.route("/logout", methods=["POST"], endpoint="titan_security_logout")
    def titan_security_logout() -> Response:
        session.clear()
        return redirect(url_for("titan_security_login"))

    @app.route("/api/security/status", methods=["GET"], endpoint="titan_security_status")
    def titan_security_status() -> Response:
        return jsonify(
            {
                "status": "success",
                "authenticated": _admin_authorized(admin_api_token),
                "firebaseConditionalWrites": True,
                "adminSession": bool(session.get("titan_admin")),
            }
        )

    @app.before_request
    def titan_security_before_request() -> Response | None:
        path = request.path
        if request.method == "OPTIONS":
            return None
        if path in {"/login", "/sw.js", "/icon.svg", "/manifest.json"}:
            return None

        token_ok = _token_authorized(admin_api_token)
        admin_ok = bool(session.get("titan_admin")) or token_ok

        if path == "/" and request.args.get("vip"):
            session["titan_vip_id"] = str(request.args.get("vip"))
            return None

        if path == "/" and not admin_ok:
            return redirect(url_for("titan_security_login"))

        if path in {"/api/state", "/api/payments"}:
            if admin_ok or session.get("titan_vip_id"):
                return None
            return jsonify({"status": "error", "message": "Authentication required"}), 401

        if path == "/api/submit_payment":
            if admin_ok:
                pass
            else:
                vip_id = str(session.get("titan_vip_id") or "")
                body = request.get_json(silent=True) or {}
                if not vip_id or str(body.get("userId") or "") != vip_id:
                    return jsonify({"status": "error", "message": "VIP session mismatch"}), 403
        elif not admin_ok:
            if path.startswith("/api/") or path == "/save" or request.method in {"POST", "PUT", "PATCH", "DELETE"}:
                return jsonify({"status": "error", "message": "Admin authentication required"}), 401
            return redirect(url_for("titan_security_login"))

        if request.method in {"POST", "PUT", "PATCH", "DELETE"} and path != "/login":
            if not token_ok and not _same_origin():
                return jsonify({"status": "error", "message": "Cross-site request blocked"}), 403
            _WRITE_LOCK.acquire()
            g.titan_write_lock = True
        return None

    def _release_request_lock() -> None:
        if getattr(g, "titan_write_lock", False):
            g.titan_write_lock = False
            _WRITE_LOCK.release()

    @app.after_request
    def titan_security_after_request(response: Response) -> Response:
        _release_request_lock()
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        if request.path.startswith("/api/") or request.path == "/":
            response.headers["Cache-Control"] = "no-store, max-age=0"
        return response

    @app.teardown_request
    def titan_security_teardown_request(_error: BaseException | None) -> None:
        _release_request_lock()

    @app.errorhandler(FirebaseConflictError)
    def titan_firebase_conflict(_error: FirebaseConflictError) -> tuple[Response, int]:
        return (
            jsonify(
                {
                    "status": "conflict",
                    "message": "Another process updated Firebase first. Stale overwrite blocked; refresh and retry.",
                }
            ),
            409,
        )

    _replace_api_views(app, module, admin_api_token)
    _CONFIGURED_APP_IDS.add(id(app))
    return app
