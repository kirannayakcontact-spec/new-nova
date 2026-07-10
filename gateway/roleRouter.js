"use strict";

// Runtime role-routing overlay for the existing monolithic Gateway.js.
// It intentionally does not write role targets into Firebase: Admin root PUT remains
// the source of truth, while these environment values act only at gateway runtime.

const crypto = require("crypto");

const ROUTER_ENABLED = String(process.env.ROLE_ROUTER_ENABLED || "1") !== "0";
const OVERLAY_META = Symbol("titanRoleRouterOverlay");
const recentDeliveries = new Map();

const MARKET_NAMES = [
  "SRIDEV DAY OPEN", "SRIDEV DAY CLOSE", "TIME BAZAR OPEN", "MADHUR DAY OPEN",
  "TIME BAZAR CLOSE", "MADHUR DAY CLOSE", "MILAN DAY OPEN", "RAJDHANI DAY OPEN",
  "SUPREME DAY OPEN", "KALYAN OPEN", "MILAN DAY CLOSE", "RAJDHANI DAY CLOSE",
  "SUPREME DAY CLOSE", "KALYAN CLOSE", "SRIDEVI NIGHT OPEN", "SRIDEVI NIGHT CLOSE",
  "MADHUR NIGHT OPEN", "SUPREME NIGHT OPEN", "MILAN NIGHT OPEN", "KALYAN NIGHT OPEN",
  "RAJDHANI NIGHT OPEN", "MAIN BAZAR OPEN", "MADHUR NIGHT CLOSE", "SUPREME NIGHT CLOSE",
  "MILAN NIGHT CLOSE", "KALYAN NIGHT CLOSE", "RAJDHANI NIGHT CLOSE", "MAIN BAZAR CLOSE"
];
const BASE_MARKET_NAMES = [
  "SRIDEV DAY", "TIME BAZAR", "MADHUR DAY", "MILAN DAY", "RAJDHANI DAY", "SUPREME DAY",
  "KALYAN", "SRIDEVI NIGHT", "MADHUR NIGHT", "SUPREME NIGHT", "MILAN NIGHT",
  "KALYAN NIGHT", "RAJDHANI NIGHT", "MAIN BAZAR"
];

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

function isKalyanMarket(value) {
  return baseMarket(value) === "KALYAN";
}

function injectScheduleTargets(state, changes) {
  if (!ROLE_TARGETS.schedule.length) return;
  const profiles = state && state.profiles && typeof state.profiles === "object" ? state.profiles : {};
  for (const [profileId, profile] of Object.entries(profiles)) {
    const dayRecords = profile && profile.dayRecords && typeof profile.dayRecords === "object" ? profile.dayRecords : {};
    for (const [date, day] of Object.entries(dayRecords)) {
      for (const [store, names] of [["data", MARKET_NAMES], ["pannelData", MARKET_NAMES], ["jodiData", BASE_MARKET_NAMES]]) {
        const records = day && day[store] && typeof day[store] === "object" ? day[store] : {};
        for (const [index, rec] of Object.entries(records)) {
          if (!rec || typeof rec !== "object" || !isKalyanMarket(names[Number(index)] || "")) continue;
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
    const resultTargets = uniqueTargets(state.resultTargets || [], state.resultSettings && state.resultSettings.targets, ROLE_TARGETS.result);
    setOverlay(state, ["resultTargets"], resultTargets, changes);
    setOverlay(state, ["resultSettings", "targets"], resultTargets, changes);
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
  setOverlay(state, ["marketRoleTargets", "KALYAN"], {
    entryTargets: ROLE_TARGETS.entry,
    bookieTargets: ROLE_TARGETS.bookie,
    scheduleTargets: ROLE_TARGETS.schedule,
    resultTargets: ROLE_TARGETS.result,
    forwardTargets: ROLE_TARGETS.forward
  }, changes);

  Object.defineProperty(state, OVERLAY_META, { value: changes, enumerable: false, configurable: true });
  return state;
}

function isFirebaseUrl(value) {
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
    if (isFirebaseUrl(url) && response && response.data && typeof response.data === "object") {
      injectRoleTargets(response.data);
    }
    return response;
  };
  axios.put = async function patchedPut(url, data, ...args) {
    if (isFirebaseUrl(url) && data && typeof data === "object" && data[OVERLAY_META]) {
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
  if (upper.includes("TITAN NOVA INTEL")) return { role: "schedule", kalyanOnly: true };
  if (upper.includes("TITAN NOVA RESULT")) return { role: "result", kalyanOnly: true };
  if (upper.includes("TITAN NOVA LOAD REPORT")) return { role: "forward", kalyanOnly: false };
  if (/WITHDRAW(?:AL)?\s+(?:REQUEST|ALERT)|PAYMENT\s+(?:NOTIFICATION|ALERT|RECEIVED)|ADMIN\s+ALERT|BOOKIE\s+ALERT/i.test(upper)) {
    return { role: "bookie", kalyanOnly: false };
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
      if (!route || !ROLE_TARGETS[route.role] || !ROLE_TARGETS[route.role].length) {
        return originalSendMessage(jid, payload, options);
      }

      const market = marketFromText(text);
      const kalyan = isKalyanMarket(market);
      const currentJid = normalizeJid(jid);
      const forcedTargets = ROLE_TARGETS[route.role];

      if (route.kalyanOnly && !kalyan) {
        if (forcedTargets.includes(currentJid)) return syntheticSendResult("ROLE_ROUTER_NON_KALYAN_SUPPRESSED");
        return originalSendMessage(jid, payload, options);
      }

      let firstResult = null;
      for (const target of forcedTargets) {
        if (wasRecentlyDelivered(target, text)) continue;
        const result = await originalSendMessage(target, payload, options);
        markDelivered(target, text);
        if (!firstResult) firstResult = result;
      }
      return firstResult || syntheticSendResult("ROLE_ROUTER_DEDUPED");
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
          const market = marketFromText(text);
          const remoteJid = normalizeJid(message && message.key && message.key.remoteJid);
          if (isEntryCard(text) && isKalyanMarket(market) && !ROLE_TARGETS.entry.includes(remoteJid)) {
            console.warn(`[roleRouter] KALYAN entry ignored outside configured Entry Target: ${remoteJid || "unknown_chat"}`);
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
