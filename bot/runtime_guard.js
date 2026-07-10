"use strict";

const crypto = require("crypto");
const axios = require("axios");
const express = require("express");

let prepared = false;
const firebaseEtags = new WeakMap();

function placeholder(value) {
  const v = String(value || "").trim().toLowerCase();
  return !v || ["your-project", "change-me", "changeme", "example.com", "replace_me", "placeholder"].some(x => v.includes(x));
}

function normalizeFirebaseUrl(raw) {
  let value = String(raw || "").trim().replace(/^['"]|['"]$/g, "").replace(/\/$/, "");
  if (placeholder(value)) throw new Error("FIREBASE_URL missing/placeholder. Set the real database URL in .env.");
  const parsed = new URL(value);
  if (parsed.protocol !== "https:") throw new Error("FIREBASE_URL must use https://");
  if (!value.endsWith(".json")) value += "/titan_master_data.json";
  return value;
}

function requireSecret(name, minLength) {
  const value = String(process.env[name] || "").trim();
  if (placeholder(value) || value.length < minLength) {
    throw new Error(`${name} missing or too short. Run: python scripts/ensure_runtime_env.py --prepare`);
  }
  return value;
}

function secureEqual(a, b) {
  const left = Buffer.from(String(a || ""));
  const right = Buffer.from(String(b || ""));
  return left.length === right.length && crypto.timingSafeEqual(left, right);
}

function isLoopback(req) {
  const address = String(req.socket?.remoteAddress || req.ip || "").replace(/^::ffff:/, "");
  return address === "127.0.0.1" || address === "::1";
}

function installAxiosFirebaseCas(firebaseUrl) {
  axios.interceptors.request.use(config => {
    const target = String(config.url || "").replace(/\/$/, "");
    if (target !== firebaseUrl) return config;
    config.headers = config.headers || {};
    const method = String(config.method || "get").toLowerCase();
    if (method === "get") {
      config.headers["X-Firebase-ETag"] = "true";
      config.headers["Cache-Control"] = "no-cache";
    }
    if (method === "put") {
      const etag = config.data && typeof config.data === "object" ? firebaseEtags.get(config.data) : "";
      if (!etag) {
        throw new Error("Unsafe Firebase full-state PUT blocked because no ETag was attached to this state snapshot.");
      }
      config.headers["If-Match"] = etag;
      config.headers["Cache-Control"] = "no-cache";
    }
    return config;
  });

  axios.interceptors.response.use(
    response => {
      const target = String(response.config?.url || "").replace(/\/$/, "");
      if (target === firebaseUrl && String(response.config?.method || "get").toLowerCase() === "get") {
        const etag = response.headers?.etag || response.headers?.ETag;
        if (etag && response.data && typeof response.data === "object") firebaseEtags.set(response.data, etag);
      }
      return response;
    },
    error => {
      if (error?.response?.status === 412) {
        error.message = "Firebase conflict: stale full-state overwrite was blocked. The next scheduler tick can retry safely.";
      }
      return Promise.reject(error);
    }
  );
}

function installExpressGuards(gatewayToken) {
  const host = String(process.env.GATEWAY_HOST || "127.0.0.1").trim() || "127.0.0.1";
  const allowLoopback = String(process.env.GATEWAY_ALLOW_LOOPBACK_WITHOUT_TOKEN || "1").toLowerCase() !== "0";
  const protectedPaths = new Set([
    "/wa_login_status", "/wa_reset_session", "/wa_qr_text", "/status", "/health", "/targets", "/chats",
    "/send", "/send_bulk", "/send_category", "/bot_schedule", "/load_report", "/load_forwarder_send",
    "/result_retry", "/results", "/scrape_results", "/spam_guard_status", "/send_hitmiss"
  ]);

  function gatewayAuth(req, res, next) {
    const supplied = req.get("X-Titan-Gateway-Token") || req.query?.token || "";
    if (secureEqual(supplied, gatewayToken) || (allowLoopback && isLoopback(req))) return next();
    return res.status(401).json({ status: "error", message: "Gateway authentication required" });
  }

  for (const method of ["get", "post", "put", "patch", "delete"]) {
    const original = express.application[method];
    express.application[method] = function patchedRoute(path, ...handlers) {
      if (typeof path === "string" && protectedPaths.has(path)) {
        return original.call(this, path, gatewayAuth, ...handlers);
      }
      return original.call(this, path, ...handlers);
    };
  }

  const originalListen = express.application.listen;
  express.application.listen = function patchedListen(port, ...args) {
    const callback = args.find(arg => typeof arg === "function");
    return originalListen.call(this, port, host, callback);
  };
}

function prepareGatewayRuntime() {
  if (prepared) return;
  const firebaseUrl = normalizeFirebaseUrl(process.env.FIREBASE_URL);
  const gatewayToken = requireSecret("GATEWAY_API_TOKEN", 24);
  process.env.FIREBASE_URL = firebaseUrl;
  installAxiosFirebaseCas(firebaseUrl);
  installExpressGuards(gatewayToken);
  prepared = true;
  console.log(`🔒 Gateway guard enabled on ${process.env.GATEWAY_HOST || "127.0.0.1"}`);
}

module.exports = { prepareGatewayRuntime, normalizeFirebaseUrl };
