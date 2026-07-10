"""Expose the Gateway role-router UI through the main Flask dashboard."""

from __future__ import annotations

from typing import Any

import requests
from flask import Response, jsonify, request


GATEWAY_BASE = "http://127.0.0.1:3000"


def _gateway_url(path: str) -> str:
    return GATEWAY_BASE.rstrip("/") + "/" + path.lstrip("/")


def _gateway_offline_page(message: str) -> str:
    safe = str(message or "Gateway offline").replace("<", "&lt;").replace(">", "&gt;")
    return f"""<!doctype html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'>
    <title>Role Router Offline</title></head><body style='margin:0;background:#17212B;color:white;font-family:Arial,sans-serif;padding:24px'>
    <div style='max-width:560px;margin:auto;background:#232E3C;border:1px solid rgba(255,93,93,.35);border-radius:16px;padding:20px'>
    <h2 style='color:#FF5D5D;margin-top:0'>Gateway Offline</h2><p>{safe}</p>
    <p style='color:#7A9CB8'>Termux me <b>nova restart</b> run karke phir Refresh karein.</p>
    <a href='/' style='display:block;text-align:center;background:#2AABEE;color:white;text-decoration:none;padding:13px;border-radius:12px;font-weight:800'>Back to Dashboard</a>
    </div></body></html>"""


def register_role_router_proxy(app: Any, gateway_base: str | None = None) -> None:
    """Register dashboard-visible proxy routes exactly once."""

    global GATEWAY_BASE
    if gateway_base:
        GATEWAY_BASE = gateway_base.rstrip("/")
    if getattr(app, "_titan_role_router_proxy_registered", False):
        return

    @app.get("/role_router")
    def role_router_page_proxy() -> Response:
        try:
            upstream = requests.get(_gateway_url("/role_router"), timeout=8)
            return Response(
                upstream.content,
                status=upstream.status_code,
                content_type=upstream.headers.get("Content-Type", "text/html; charset=utf-8"),
            )
        except Exception as exc:  # pragma: no cover - network/runtime dependent
            return Response(_gateway_offline_page(str(exc)), status=503, content_type="text/html; charset=utf-8")

    @app.route("/api/role_router", methods=["GET", "POST"])
    def role_router_api_proxy() -> Response:
        try:
            if request.method == "POST":
                upstream = requests.post(
                    _gateway_url("/api/role_router"),
                    json=request.get_json(silent=True) or {},
                    timeout=12,
                )
            else:
                upstream = requests.get(_gateway_url("/api/role_router"), timeout=8)
            try:
                payload = upstream.json()
            except Exception:
                payload = {"status": "error", "message": upstream.text or "Invalid Gateway response"}
            return jsonify(payload), upstream.status_code
        except Exception as exc:  # pragma: no cover - network/runtime dependent
            return jsonify({"status": "offline", "message": str(exc)}), 503

    @app.after_request
    def inject_role_router_control(response: Response) -> Response:
        """Add a visible master-dashboard control without editing the monolith template."""

        try:
            if request.path != "/" or request.args.get("vip") or response.status_code != 200:
                return response
            if not response.content_type or "text/html" not in response.content_type:
                return response
            html = response.get_data(as_text=True)
            if "id=\"role-router-control\"" in html or "</body>" not in html:
                return response
            control = """
            <a id="role-router-control" href="/role_router" title="WhatsApp Role Targets"
               style="position:fixed;right:14px;bottom:96px;z-index:998;background:#2AABEE;color:#fff;
               width:52px;height:52px;border-radius:16px;display:flex;align-items:center;justify-content:center;
               text-decoration:none;font:900 21px Arial,sans-serif;box-shadow:0 8px 24px rgba(42,171,238,.35);
               border:1px solid rgba(255,255,255,.18)">⚙</a>
            """
            response.set_data(html.replace("</body>", control + "</body>", 1))
            response.headers.pop("Content-Length", None)
        except Exception:
            pass
        return response

    app._titan_role_router_proxy_registered = True


__all__ = ["register_role_router_proxy"]
