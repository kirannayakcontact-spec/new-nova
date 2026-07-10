"use strict";

// Runtime WhatsApp role routing overlay for the existing monolithic Gateway.js.
// KALYAN_* values are WhatsApp group identifiers/names, not a market filter.
// Runtime target overlays are removed before Gateway root PUT writes so Manual
// Overwrite Mode remains the source of truth for the main Titan state.

const crypto = require("crypto");

const ROUTER_ENABLED = String(process.env.ROLE_ROUTER_ENABLED || "1") !== "0";
const OVERLAY_META = Symbol("titanRoleRouterOverlay");
const recentDeliveries = new Map();

function normalizeJid(value) {
  const raw = String(value || "").trim().replace(/[<>]/g, "");
  const match = raw.match(/([0-9A-Za-z._:-]+@g\.us)/i);
  return match ? match[1].replace(/:\d+(?=@)/, "") : "";
}

function envTargets(name) {
  const out = [];
  for (const item of String(process.env[name] || "").split(/[\n,]+/)) {
    const jid = normalizeJid(item);
    if (jid && !out.includes(jid)) out.push(jid);
  }
  return out;
}

// Arrays intentionally remain mutable. roleRouterUi.js updates these arrays live.
const ROLE_TARGETS = Object.freeze({
  entry: envTargets("KALYAN_ADMIN_GROUP"),
  bookie: envTargets("KALYAN_ADMIN_GROUP"),
  schedule: envTargets("KALYAN_INTEL_GROUP"),
  result: envTargets("KALYAN_RESULT_GROUP"),
  forward: envTargets("BOOKIE_LOAD_REPORT_GROUP")
});

function cloneJson(value) {
  if (value === undefined) return undefined;
  return JSON.parse(JSON.stringify(value));
}

function getAtPath(root, path) {
  let cur = root;
  for (const key of path) {
    if (cur == null || typeof cur !== "object") return { exists: false, value: undefined };
    if (!Object.prototype.hasOwnProperty.call(cur, key)) return { exists: false, value: undefined };
    cur = cur[key];
  }
  return { exists: true, value: cur };
}

function ensureParent(root, path) {
  let cur = root;
  for (let i = 0; i < path.length - 1; i += 1) {
    const key = path[i];
    if (!cur[key] || typeof cur[key] !== "object") cur[key] = {};
    cur = cur[key];
  }
  return cur;
}

function setOverlay(root, path, value, changes) {
  const old = getAtPath(root, path);
  const missingAncestors = [];
  for (let i = 1; i < path.length; i += 1) {
    const prefix = path.slice(0, i);
    if (!getAtPath(root, prefix).exists) missingAncestors.push(prefix);
  }
  changes.push({ path: path.slice(), existed: old.exists, value: cloneJson(old.value), missingAncestors });
  const parent = ensureParent(root, path);
  parent[path[path.length - 1]] = cloneJson(value);
}

function deleteEmptyCreatedAncestors(root, paths) {
  const ordered = [...paths].sort((a, b) => b.length - a.length);
  for (const path of ordered) {
    const found = getAtPath(root, path);
    if (!found.exists || !found.value || typeof found.value !== "object" || Object.keys(found.value).length) continue;
    const parentPath = path.slice(0, -1);
    const parent = parentPath.length ? getAtPath(root, parentPath).value : root;
    if (parent && typeof parent === "object") delete parent[path[path.length - 1]];
  }
}

function restoreOverlay(root, changes) {
  const createdAncestors = [];
  for (let i = changes.length - 1; i >= 0; i -= 1) {
    const change = changes[i];
    const parent = ensureParent(root, change.path);
    const key = change.path[change.path.length - 1];
    if (change.existed) parent[key] = cloneJson(change.value);
    else delete parent[key];
    createdAncestors.push(...(change.missingAncestors || []));
  }
  deleteEmptyCreatedAncestors(root, createdAncestors);
  return root;
}

function uniqueTargets(...values) {
  const out = [];
  const add = (value) => {
    if (Array.isArray(value)) return value.forEach(add);
    const jid = normalizeJid(value && typeof value === "object" ? (value.id || value.jid || value.target) : value);
    if (jid && !out.includes(jid)) out.push(jid);
  };
  values.forEach(add);
  return out;
}

function normalizeMarket(value) {
  return String(value || "")
    .toUpperCase()
    .replace(/\*/g, "")
    .replace(/SRIDEVI\s+DAY/g, "SRIDEV DAY")
    .replace(/[^A-Z0-9]+/g, " ")
    .trim()
    .replace(/\s+/g, " ");
}

function baseMarket(value) {
  return normalizeMarket(value).replace(/\s+(OPEN|CLOSE)$/i, "").trim();
}

// Kept for backwards compatibility with callers/tests. It is no longer used to
// decide role routing because KALYAN_* is a group name, not a market scope.
function isKalyanMarket(value) {
  return baseMarket(value) === "KALYAN";
}

function injectScheduleTargets(state, changes) {
  if (!ROLE_TARGETS.schedule.length) return;
  const profiles = state && state.profiles && typeof state.profiles === "object" ? state.profiles : {};
  for (const [profileId, profile] of Object.entries(profiles)) {
    const dayRecords = profile && profile.dayRecords && typeof profile.dayRecords === "object" ? profile.dayRecords : {};
    for (const [date, day] of Object.entries(dayRecords)) {
      for (const store of ["data", "pannelData", "jodiData"]) {
        const records = day && day[store] && typeof day[store] === "object" ? day[store] : {};
        for (const [index, rec] of Object.entries(records)) {
          if (!rec || typeof rec !== "object") continue;
          setOverlay(state, ["profiles", profileId, "dayRecords", date, store, index, "schTargets"], ROLE_TARGETS.schedule, changes);
          setOverlay(state, ["profiles", profileId, "dayRecords", date, store, index, "targets"], ROLE_TARGETS.schedule, changes);
        }
      }
    }
  }
}

function injectRoleTargets(state) {
  if (!ROUTER_ENABLED || !state || typeof state !== "object") return state;
  const changes = [];

  if (ROLE_TARGETS.entry.length) {
    setOverlay(state, ["entrySettings", "entryTargets"], ROLE_TARGETS.entry, changes);
  }
  if (ROLE_TARGETS.bookie.length) {
    setOverlay(state, ["bookieTargets"], ROLE_TARGETS.bookie, changes);
    setOverlay(state, ["paymentSettings", "bookieTargets"], ROLE_TARGETS.bookie, changes);
    setOverlay(state, ["withdrawalSettings", "bookieTargets"], ROLE_TARGETS.bookie, changes);
    setOverlay(state, ["adminAlertTargets"], ROLE_TARGETS.bookie, changes);
  }
  if (ROLE_TARGETS.result.length) {
    setOverlay(state, ["resultTargets"], ROLE_TARGETS.result, changes);
    setOverlay(state, ["resultSettings", "targets"], ROLE_TARGETS.result, changes);
    setOverlay(state, ["resultSettings", "useForwardTargetsForResults"], false, changes);
  }
  if (ROLE_TARGETS.forward.length) {
    setOverlay(state, ["loadForwarder", "targets"], ROLE_TARGETS.forward, changes);
    const outbox = Array.isArray(state.loadForwarderOutbox) ? state.loadForwarderOutbox : [];
    for (let i = 0; i < outbox.length; i += 1) {
      if (!outbox[i] || outbox[i].status !== "pending") continue;
      setOverlay(state, ["loadForwarderOutbox", i, "targets"], ROLE_TARGETS.forward, changes);
    }
  }

  injectScheduleTargets(state, changes);
  setOverlay(state, ["roleRouterRuntime"], {
    entryTargets: ROLE_TARGETS.entry,
    bookieTargets: ROLE_TARGETS.bookie,
    scheduleTargets: ROLE_TARGETS.schedule,
    resultTargets: ROLE_TARGETS.result,
    forwardTargets: ROLE_TARGETS.forward
  }, changes);

  Object.defineProperty(state, OVERLAY_META, { value: changes, enumerable: false, configurable: true });
  return state;
}

function isFirebaseRootUrl(value) {
  const url = String(value || "");
  return /firebaseio\.com/i.test(url) && /(?:titan_master_data)?\.json(?:[?#]|$)/i.test(url);
}

function patchAxios() {
  let axios;
  try {
    axios = require("axios");
  } catch (error) {
    console.error("[roleRouter] axios preload failed:", error.message || error);
    return;
  }
  if (axios.__titanRoleRouterPatched) return;

  const originalGet = axios.get.bind(axios);
  const originalPut = axios.put.bind(axios);
  axios.get = async function patchedGet(url, ...args) {
    const response = await originalGet(url, ...args);
    if (isFirebaseRootUrl(url) && response && response.data && typeof response.data === "object") {
      injectRoleTargets(response.data);
    }
    return response;
  };
  axios.put = async function patchedPut(url, data, ...args) {
    if (isFirebaseRootUrl(url) && data && typeof data === "object" && data[OVERLAY_META]) {
      const clean = cloneJson(data);
      restoreOverlay(clean, data[OVERLAY_META]);
      return originalPut(url, clean, ...args);
    }
    return originalPut(url, data, ...args);
  };
  Object.defineProperty(axios, "__titanRoleRouterPatched", { value: true, enumerable: false });
}

function messageText(message) {
  const msg = message && message.message ? message.message : {};
  const direct = [
    msg.conversation,
    msg.extendedTextMessage && msg.extendedTextMessage.text,
    msg.imageMessage && msg.imageMessage.caption,
    msg.videoMessage && msg.videoMessage.caption,
    msg.documentMessage && msg.documentMessage.caption,
    msg.buttonsResponseMessage && msg.buttonsResponseMessage.selectedDisplayText,
    msg.listResponseMessage && msg.listResponseMessage.title
  ];
  for (const value of direct) if (value) return String(value);
  const nested = msg.viewOnceMessage && msg.viewOnceMessage.message;
  if (nested) return messageText({ message: nested });
  const nestedV2 = msg.viewOnceMessageV2 && msg.viewOnceMessageV2.message;
  if (nestedV2) return messageText({ message: nestedV2 });
  return "";
}

function payloadText(payload) {
  if (!payload || typeof payload !== "object") return "";
  return String(payload.text || payload.caption || "");
}

function marketFromText(text) {
  const match = String(text || "").match(/(?:^|\n)\s*(?:🔥\s*)?\*?MARKET\*?\s*:\s*([^\n]+)/i);
  return match ? normalizeMarket(match[1]) : "";
}

function isEntryCard(text) {
  const value = String(text || "");
  return /\bMARKET\s*:/i.test(value) && /\bDIGITS?\s*:/i.test(value);
}

function classifyOutbound(text) {
  const upper = String(text || "").toUpperCase();
  if (upper.includes("TITAN NOVA INTEL")) return { role: "schedule" };
  if (upper.includes("TITAN NOVA RESULT")) return { role: "result" };
  if (upper.includes("TITAN NOVA LOAD REPORT")) return { role: "forward" };
  if (/WITHDRAW(?:AL)?\s+(?:REQUEST|ALERT)|PAYMENT\s+(?:NOTIFICATION|ALERT|RECEIVED)|ADMIN\s+ALERT|BOOKIE\s+ALERT/i.test(upper)) {
    return { role: "bookie" };
  }
  return null;
}

function deliveryKey(target, text) {
  const hash = crypto.createHash("sha1").update(String(text || "")).digest("hex").slice(0, 16);
  return `${normalizeJid(target)}|${hash}`;
}

function wasRecentlyDelivered(target, text) {
  const now = Date.now();
  const old = Number(recentDeliveries.get(deliveryKey(target, text)) || 0);
  for (const [entry, at] of recentDeliveries) if (now - at > 120000) recentDeliveries.delete(entry);
  return old > 0 && now - old < 30000;
}

function markDelivered(target, text) {
  recentDeliveries.set(deliveryKey(target, text), Date.now());
}

function syntheticSendResult(id) {
  return { key: { id: id || "ROLE_ROUTER_SUPPRESSED", fromMe: true } };
}

function patchSocket(socket) {
  if (!socket || socket.__titanRoleRouterPatched) return socket;
  const originalSendMessage = typeof socket.sendMessage === "function" ? socket.sendMessage.bind(socket) : null;

  if (originalSendMessage) {
    socket.sendMessage = async function routedSendMessage(jid, payload, options) {
      const text = payloadText(payload);
      const route = classifyOutbound(text);
      const forcedTargets = route && ROLE_TARGETS[route.role];
      if (!route || !Array.isArray(forcedTargets) || !forcedTargets.length) {
        return originalSendMessage(jid, payload, options);
      }

      let firstResult = null;
      let firstError = null;
      for (const target of forcedTargets) {
        if (wasRecentlyDelivered(target, text)) continue;
        try {
          const result = await originalSendMessage(target, payload, options);
          markDelivered(target, text);
          if (!firstResult) firstResult = result;
        } catch (error) {
          if (!firstError) firstError = error;
        }
      }
      if (firstResult) return firstResult;
      if (firstError) throw firstError;
      return syntheticSendResult("ROLE_ROUTER_DEDUPED");
    };
  }

  if (socket.ev && typeof socket.ev.on === "function") {
    const originalOn = socket.ev.on.bind(socket.ev);
    socket.ev.on = function routedEventOn(event, handler) {
      if (event !== "messages.upsert" || typeof handler !== "function" || !ROLE_TARGETS.entry.length) {
        return originalOn(event, handler);
      }
      return originalOn(event, async (packet) => {
        const accepted = [];
        for (const message of (packet && packet.messages) || []) {
          const text = messageText(message);
          const remoteJid = normalizeJid(message && message.key && message.key.remoteJid);
          if (isEntryCard(text) && !ROLE_TARGETS.entry.includes(remoteJid)) {
            console.warn(`[roleRouter] Entry card ignored outside configured Entry Target: ${remoteJid || "unknown_chat"}`);
            continue;
          }
          accepted.push(message);
        }
        if (accepted.length) return handler({ ...packet, messages: accepted });
        return undefined;
      });
    };
  }

  Object.defineProperty(socket, "__titanRoleRouterPatched", { value: true, enumerable: false });
  return socket;
}

function patchBaileys() {
  let baileys;
  try {
    baileys = require("@whiskeysockets/baileys");
  } catch (error) {
    console.error("[roleRouter] Baileys preload failed:", error.message || error);
    return;
  }
  if (baileys.__titanRoleRouterPatched) return;
  const originalMakeWASocket = baileys.default;
  if (typeof originalMakeWASocket !== "function") {
    console.error("[roleRouter] Baileys default makeWASocket export was not found.");
    return;
  }
  const wrapped = function roleRoutedMakeWASocket(...args) {
    return patchSocket(originalMakeWASocket(...args));
  };
  try {
    baileys.default = wrapped;
    if (baileys.default !== wrapped) {
      Object.defineProperty(baileys, "default", { value: wrapped, writable: true, configurable: true });
    }
    Object.defineProperty(baileys, "__titanRoleRouterPatched", { value: true, enumerable: false });
  } catch (error) {
    console.error("[roleRouter] Could not patch Baileys makeWASocket:", error.message || error);
  }
}

function roleSummary() {
  return Object.fromEntries(Object.entries(ROLE_TARGETS).map(([role, targets]) => [role, targets.length]));
}

if (ROUTER_ENABLED) {
  patchAxios();
  patchBaileys();
  console.log("[roleRouter] Runtime role routing enabled:", roleSummary());
} else {
  console.log("[roleRouter] Disabled by ROLE_ROUTER_ENABLED=0");
}

module.exports = {
  ROLE_TARGETS,
  normalizeJid,
  normalizeMarket,
  baseMarket,
  isKalyanMarket,
  marketFromText,
  classifyOutbound,
  injectRoleTargets,
  restoreOverlay,
  roleSummary
};
