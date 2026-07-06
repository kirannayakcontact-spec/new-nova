"use strict";

// ============================================================
// TITAN NOVA SINGLE GATEWAY BOT — WhatsApp Sync + Bulk + Auto Schedule
// RUN IN TERMUX:
//   npm install express axios qrcode-terminal pino @whiskeysockets/baileys
//   node Gateway.js
// Install deps without package.json:
//   npm install express axios qrcode-terminal pino @whiskeysockets/baileys
// Run:
//   node Gateway.js
// Optional:
//   FIREBASE_URL="https://your-db.firebaseio.com/titan_master_data.json" APP_TZ="Asia/Kolkata" node Gateway.js
// ============================================================

const fs = require("fs");
const path = require("path");
const express = require("express");
const axios = require("axios");
const qrcode = require("qrcode-terminal");
const pino = require("pino");
const {
  default: makeWASocket,
  useMultiFileAuthState,
  DisconnectReason,
  fetchLatestBaileysVersion,
  Browsers
} = require("@whiskeysockets/baileys");

const PORT = Number(process.env.PORT || 3000);
const FIREBASE_URL = (process.env.FIREBASE_URL || "https://titan-bbbc4-default-rtdb.firebaseio.com/titan_master_data.json").replace(/\/$/, "");
const AUTH_DIR = path.join(__dirname, "auth_info_baileys");
const TARGET_CACHE_FILE = path.join(process.cwd(), "whatsapp_targets_cache.json");
const SENT_LOG_FILE = path.join(process.cwd(), "titan_schedule_sent_log.json");
const SPAM_GUARD_STATE_FILE = path.join(process.cwd(), "titan_spam_guard_state.json");
const SCRAPE_CONFIRM_FILE = path.join(process.cwd(), "titan_result_scrape_confirm.json");
const LIVE_RESULT_STATE_FILE = path.join(process.cwd(), "titan_live_result_state.json");
// Schedule timezone: keep Python UI and Node gateway on the same date/time.
const APP_TZ = process.env.APP_TZ || "Asia/Kolkata";
// Auto result scraper: set RESULT_SCRAPE_ENABLED=0 to disable.
// RESULT_SCRAPE_URLS can be comma-separated fallback live result pages.
const RESULT_SCRAPE_ENABLED = String(process.env.RESULT_SCRAPE_ENABLED || "1") !== "0";
const RESULT_SCRAPE_INTERVAL_MS = Math.max(Number(process.env.RESULT_SCRAPE_INTERVAL_MS || 5000), 3000);
const RESULT_SCRAPE_URLS = String(process.env.RESULT_SCRAPE_URLS || "https://dpbosse.net/")
  .split(",")
  .map(x => x.trim())
  .filter(Boolean);
// Wrong-result protection: same market+stage+result must be seen in repeated scrapes before it is saved/sent.
const RESULT_SCRAPE_CONFIRM_COUNT = Math.max(Number(process.env.RESULT_SCRAPE_CONFIRM_COUNT || 1), 1);

const MARKETS = [
  {n:"SRIDEV DAY OPEN",hr:11,min:35},{n:"SRIDEV DAY CLOSE",hr:12,min:35},{n:"TIME BAZAR OPEN",hr:13,min:0},{n:"MADHUR DAY OPEN",hr:13,min:15},
  {n:"TIME BAZAR CLOSE",hr:14,min:0},{n:"MADHUR DAY CLOSE",hr:14,min:15},{n:"MILAN DAY OPEN",hr:15,min:0},{n:"RAJDHANI DAY OPEN",hr:15,min:5},
  {n:"SUPREME DAY OPEN",hr:15,min:35},{n:"KALYAN OPEN",hr:15,min:50},{n:"MILAN DAY CLOSE",hr:17,min:0},{n:"RAJDHANI DAY CLOSE",hr:17,min:5},
  {n:"SUPREME DAY CLOSE",hr:17,min:35},{n:"KALYAN CLOSE",hr:17,min:50},{n:"SRIDEVI NIGHT OPEN",hr:19,min:0},{n:"SRIDEVI NIGHT CLOSE",hr:20,min:0},
  {n:"MADHUR NIGHT OPEN",hr:20,min:30},{n:"SUPREME NIGHT OPEN",hr:20,min:45},{n:"MILAN NIGHT OPEN",hr:21,min:0},{n:"KALYAN NIGHT OPEN",hr:21,min:25},
  {n:"RAJDHANI NIGHT OPEN",hr:21,min:35},{n:"MAIN BAZAR OPEN",hr:21,min:40},{n:"MADHUR NIGHT CLOSE",hr:22,min:30},{n:"SUPREME NIGHT CLOSE",hr:22,min:45},
  {n:"MILAN NIGHT CLOSE",hr:23,min:0},{n:"KALYAN NIGHT CLOSE",hr:23,min:35},{n:"RAJDHANI NIGHT CLOSE",hr:23,min:45},{n:"MAIN BAZAR CLOSE",hr:0,min:5}
];
const BASE_MARKETS = ["SRIDEV DAY","TIME BAZAR","MADHUR DAY","MILAN DAY","RAJDHANI DAY","SUPREME DAY","KALYAN","SRIDEVI NIGHT","MADHUR NIGHT","SUPREME NIGHT","MILAN NIGHT","KALYAN NIGHT","RAJDHANI NIGHT","MAIN BAZAR"].map(n=>({n}));

const DEFAULT_MARKET_CLOSE_TIMES = (() => {
  const out = {};
  for(const m of MARKETS) out[m.n] = `${pad(m.hr)}:${pad(m.min)}`;
  for(const b of BASE_MARKETS){
    const name = b.n;
    const close = MARKETS.find(x => x.n === name + " CLOSE");
    const open = MARKETS.find(x => x.n === name + " OPEN");
    if(close) out[name] = `${pad(close.hr)}:${pad(close.min)}`;
    else if(open) out[name] = `${pad(open.hr)}:${pad(open.min)}`;
  }
  if(out["SRIDEVI DAY"] && !out["SRIDEV DAY"]) out["SRIDEV DAY"] = out["SRIDEVI DAY"];
  if(out["SRIDEV DAY"] && !out["SRIDEVI DAY"]) out["SRIDEVI DAY"] = out["SRIDEV DAY"];
  return out;
})();

let sock = null;
let connected = false;
let lastQR = "";
let lastQRAt = "";
let whatsappStartInProgress = false;
let whatsappResetCount = 0;
let lastSessionResetAt = "";
let targetsCache = loadJson(TARGET_CACHE_FILE, { contacts: [], groups: [], updatedAt: null, lastSyncError: "" });
let sentLog = loadJson(SENT_LOG_FILE, {});
let spamGuardLocalState = loadJson(SPAM_GUARD_STATE_FILE, { strikes:{}, events:[] });
let scrapeConfirm = loadJson(SCRAPE_CONFIRM_FILE, {});
let liveResultState = loadJson(LIVE_RESULT_STATE_FILE, {});
let resultTickRunning = false;
let resultScrapeTickRunning = false;
let paymentOutboxTickRunning = false;
let loadForwarderTickRunning = false;
let gatewayHealth = {
  startedAt: new Date().toISOString(),
  lastWhatsAppEvent: "starting",
  lastDisconnectCode: "",
  lastScheduleTickAt: "",
  lastScheduleError: "",
  lastResultTickAt: "",
  lastResultError: "",
  lastResultSendAt: "",
  lastResultSendSummary: "",
  lastResultScrapeTickAt: "",
  lastResultScrapeStatus: "never",
  lastResultScrapeUpdates: [],
  lastResultScrapeSkipped: [],
  lastResultScrapeError: "",
  lastPaymentOutboxTickAt: "",
  lastPaymentOutboxError: "",
  lastLoadForwarderTickAt: "",
  lastLoadForwarderError: "",
  lastLoadForwarderSendAt: "",
  lastSendAt: "",
  lastSendOk: null,
  lastSendTarget: "",
  lastSendError: "",
  lastTargetSyncAt: targetsCache.updatedAt || "",
  lastTargetSyncGroups: Array.isArray(targetsCache.groups) ? targetsCache.groups.length : 0,
  lastTargetSyncContacts: Array.isArray(targetsCache.contacts) ? targetsCache.contacts.length : 0,
  lastTargetSyncError: targetsCache.lastSyncError || ""
};

function loadJson(file, fallback){ try { return JSON.parse(fs.readFileSync(file,"utf8")); } catch { return fallback; } }
function saveJson(file, obj){ try { fs.writeFileSync(file, JSON.stringify(obj,null,2)); } catch(e) { console.log("Save error", file, e.message); } }
function pad(n){ return String(n).padStart(2,"0"); }
function nowParts(){
  const out = {};
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: APP_TZ, year:"numeric", month:"2-digit", day:"2-digit",
    hour:"2-digit", minute:"2-digit", hourCycle:"h23"
  }).formatToParts(new Date());
  for(const p of parts) if(p.type !== "literal") out[p.type] = p.value;
  return { date:`${out.year}-${out.month}-${out.day}`, hhmm:`${out.hour}:${out.minute}` };
}
function todayISO(){ return nowParts().date; }
function nowHHMM(){ return nowParts().hhmm; }
function normalizeTime(v){
  const m = String(v || "").trim().match(/^(\d{1,2}):(\d{2})(?::\d{2})?$/);
  if(!m) return "";
  const h = Number(m[1]), min = Number(m[2]);
  if(h < 0 || h > 23 || min < 0 || min > 59) return "";
  return `${pad(h)}:${pad(min)}`;
}
function hhmmToMinutes(v){ const t=normalizeTime(v); if(!t) return -1; const [h,m]=t.split(":").map(Number); return h*60+m; }
function isDueNow(jobTime, nowTime){
  const j = hhmmToMinutes(jobTime), n = hhmmToMinutes(nowTime);
  if(j < 0 || n < 0) return false;
  const diff = n - j;
  // 0 = exact minute. 1-2 = small recovery window if Termux/phone slept briefly.
  return diff >= 0 && diff <= 2;
}
function cleanDigits(v){ return String(v || "").replace(/[^0-9, ]/g, "").split(/[, ]+/).filter(Boolean).join(","); }
function formatMessage(date, market, digits){ return `🚀 *TITAN NOVA INTEL* [${date}]\n━━━━━━━━━━━━━━━━━━━━\n🔥 *MARKET:* ${market}\n🔢 *DIGITS:* [${cleanDigits(digits)}]\n━━━━━━━━━━━━━━━━━━━━`; }
function arr(v){ if(!v) return []; if(Array.isArray(v)) return v.filter(Boolean); return String(v).split(/[\n,]+/).map(x=>x.trim()).filter(Boolean); }

// Result/load/forward target helper: accepts plain numbers, wa.me links, group JIDs,
// WhatsApp invite links, and UI option objects like {id,name,type}. This prevents
// auto-result sends from failing when targets came from the Forward tab or sync list.
function targetValue(raw){
  if(raw == null) return "";
  if(typeof raw === "object"){
    return String(raw.id || raw.jid || raw.target || raw.to || raw.value || raw.phone || raw.number || raw.link || "").trim();
  }
  return String(raw || "").trim();
}
function targetList(input){
  const out = [];
  const pushOne = (x) => {
    let t = targetValue(x);
    if(!t) return;
    // If a label was accidentally pasted with a JID, extract the JID first.
    const jidMatch = t.match(/([0-9A-Za-z._:-]+@(?:g\.us|s\.whatsapp\.net))/i);
    if(jidMatch) t = jidMatch[1];
    // If several values are pasted in one field, split them safely.
    for(const part of String(t).split(/[\n,]+/).map(v=>v.trim()).filter(Boolean)){
      if(!out.includes(part)) out.push(part);
    }
  };
  if(Array.isArray(input)) input.forEach(pushOne); else pushOne(input);
  return out;
}
function collectResultTargets(state){
  const out = [];
  const add = (items) => targetList(items).forEach(t => { if(t && !out.includes(t)) out.push(t); });
  add(state?.resultTargets || []);
  add(state?.resultSettings?.targets || []);
  // Practical fallback: many admins select WhatsApp targets in Forward tab and expect
  // result declarations to use the same group/private chats. Keep it ON by default.
  if(state?.resultSettings?.useForwardTargetsForResults !== false){
    add(state?.loadForwarder?.targets || []);
  }
  return out;
}
function resultTargetLogKey(rawTarget){
  const n = normalizeTarget(rawTarget);
  return n || targetValue(rawTarget) || String(rawTarget || "");
}
function resultSentInfo(logValue){
  if(logValue && typeof logValue === "object" && !Array.isArray(logValue)){
    return { signature:String(logValue.signature || ""), targets:logValue.targets && typeof logValue.targets === "object" ? logValue.targets : {}, updatedAt:logValue.updatedAt || "" };
  }
  // Legacy sent-log value was a plain string and did not know which WhatsApp targets succeeded.
  // Treat it as informational only so newly saved group/private/Forward targets can receive the result.
  return { signature:String(logValue || ""), targets:{}, updatedAt:"", legacy:true };
}
function markResultTargetSent(key, signature, rawTarget){
  const info = resultSentInfo(sentLog[key]);
  info.signature = signature;
  info.targets = info.targets || {};
  info.targets[resultTargetLogKey(rawTarget)] = nowIso();
  info.updatedAt = nowIso();
  info.legacy = false;
  sentLog[key] = info;
}
function isResultTargetAlreadySent(key, signature, rawTarget){
  const info = resultSentInfo(sentLog[key]);
  if(info.signature !== signature) return false;
  return !!(info.targets && info.targets[resultTargetLogKey(rawTarget)]);
}

// ============================================================
// STRICT WHATSAPP ENTRY PARSER — Phase 3
// Accepts only explicit card format:
// MARKET: KALYAN OPEN
// TYPE: ANK | JODI | PENEL
// DIGITS: 1,2,3
// PAR DIGIT: 100
// TOTAL: 300
// ============================================================
function phoneKey(v){
  const raw = String(v || "").trim();
  // New WhatsApp/Baileys group messages can sometimes expose a @lid sender id.
  // @lid digits are not the real phone number, so never use them for VIP linking.
  if(raw.includes("@") && !raw.includes("@s.whatsapp.net")) return "";
  const d = raw.replace(/\D/g, "");
  if(d.length < 10) return "";
  return d.length > 10 ? d.slice(-10) : d;
}
function senderCandidatesFromMessage(m, chatJid){
  const key = m?.key || {};
  const candidates = [
    key.participant,
    key.participantPn,
    key.senderPn,
    key.participantAlt,
    key.participantAltJid,
    key.remoteJidAlt,
    m?.participant,
    m?.participantPn,
    m?.senderPn
  ];
  if(chatJid && !String(chatJid).endsWith("@g.us")) candidates.push(chatJid);
  return [...new Set(candidates.map(x => String(x || "").trim()).filter(Boolean))];
}
function profileTemplateForAutoLink(phone, name){
  return {
    name: name || (phone ? `VIP ${phone}` : "AUTO VIP"),
    phone: phone || "",
    config: { ankSplit:true, panSplit:true, capital:0, dayTarget:0, ank:{cap:0,tgt:0}, jodi:{cap:0,tgt:0}, pannel:{cap:0,tgt:0} },
    dayRecords: {},
    expiryDate: "",
    vipAccessEnabled: true,
    autoCreated: true,
    createdAt: nowIso()
  };
}
function nowIso(){ return new Date().toISOString(); }
function money(v){ const n = Number(v || 0); return "₹" + (Number.isInteger(n) ? String(n) : n.toFixed(2)); }
function normalizeEntryMarketText(v){
  return String(v || "").toUpperCase().replace(/SRIDEVI\s+DAY/g, "SRIDEV DAY").replace(/[^A-Z0-9]+/g, " ").trim().replace(/\s+/g, " ");
}
function compactEntryMarket(v){ return normalizeEntryMarketText(v).replace(/[^A-Z0-9]/g, ""); }
function deletedMarketsList(state){
  const vals = []
    .concat(state?.settings?.setup?.deletedMarkets || [])
    .concat(state?.settings?.markets?.deletedMarkets || [])
    .concat(state?.deletedMarkets || []);
  return [...new Set(vals.map(normalizeEntryMarketText).filter(Boolean))];
}
function isDeletedMarket(state, market){ return deletedMarketsList(state).includes(normalizeEntryMarketText(market)); }
function marketAliasesForDeleteName(market){
  const base = normalizeEntryMarketText(market).replace(/\s+(OPEN|CLOSE)$/i, '').trim();
  return [base, `${base} OPEN`, `${base} CLOSE`].filter(Boolean);
}
function canonicalAnkPenelMarket(v){
  const target = compactEntryMarket(v);
  const found = MARKETS.find(m => compactEntryMarket(m.n) === target);
  return found ? found.n : "";
}
function canonicalJodiMarket(v){
  let raw = normalizeEntryMarketText(v).replace(/\s+(OPEN|CLOSE)$/i, "").trim();
  const target = compactEntryMarket(raw);
  const found = BASE_MARKETS.find(m => compactEntryMarket(m.n) === target);
  return found ? found.n : "";
}
function parseEntryCard(text){
  const raw = String(text || "").replace(/\r/g, "\n");
  if(!/\bMARKET\s*:/i.test(raw) || !/\bDIGITS?\s*:/i.test(raw)) return { ok:false, silent:true, reason:"not_entry_card" };
  const fields = {};
  for(const line of raw.split(/\n+/)){
    const idx = line.indexOf(":");
    if(idx < 0) continue;
    const key = line.slice(0, idx).trim().toUpperCase().replace(/\s+/g, " ");
    const val = line.slice(idx + 1).trim();
    if(["MARKET"].includes(key)) fields.market = val;
    else if(["TYPE", "GAME", "GAME TYPE"].includes(key)) fields.type = val;
    else if(["DIGITS", "DIGIT"].includes(key)) fields.digits = val;
    else if(["PAR DIGIT", "PER DIGIT", "RATE", "PAR", "AMOUNT"].includes(key)) fields.parDigit = val;
    else if(["TOTAL", "TOTAL AMOUNT"].includes(key)) fields.total = val;
  }
  const missing = [];
  for(const k of ["market", "type", "digits", "parDigit", "total"]) if(!fields[k]) missing.push(k);
  if(missing.length) return { ok:false, reason:"missing_fields", message:`Missing field: ${missing.join(", ")}. Strict format: MARKET, TYPE, DIGITS, PAR DIGIT, TOTAL` };
  let gameType = String(fields.type || "").trim().toUpperCase();
  if(gameType === "PANEL" || gameType === "PANNEL") gameType = "PENEL";
  if(!["ANK", "JODI", "PENEL"].includes(gameType)) return { ok:false, reason:"invalid_type", message:"TYPE sirf ANK, JODI, ya PENEL hona chahiye." };
  let market = "";
  if(gameType === "JODI") market = canonicalJodiMarket(fields.market);
  else market = canonicalAnkPenelMarket(fields.market);
  if(!market){
    return { ok:false, reason:"invalid_market", message: gameType === "JODI" ? "JODI ke liye valid base MARKET chahiye. Example: KALYAN" : "ANK/PENEL ke liye valid OPEN/CLOSE MARKET chahiye. Example: KALYAN OPEN" };
  }
  const digits = String(fields.digits || "").split(/[,\s]+/).map(x=>x.trim()).filter(Boolean);
  if(!digits.length) return { ok:false, reason:"digits_missing", message:"DIGITS field empty hai." };
  for(const d of digits){
    if(gameType === "ANK" && !/^\d$/.test(d)) return { ok:false, reason:"invalid_ank_digit", message:`ANK digit invalid: ${d}. Sirf 0-9 allowed.` };
    if(gameType === "JODI" && !/^\d{1,2}$/.test(d)) return { ok:false, reason:"invalid_jodi_digit", message:`JODI digit invalid: ${d}. Sirf 00-99 allowed.` };
    if(gameType === "PENEL" && !/^\d{3}$/.test(d)) return { ok:false, reason:"invalid_penel_digit", message:`PENEL digit invalid: ${d}. Sirf 000-999 allowed.` };
  }
  const normDigits = digits.map(d => gameType === "JODI" ? d.padStart(2,"0") : d);
  const parDigit = Number(String(fields.parDigit || "").replace(/[^0-9.]/g, ""));
  const total = Number(String(fields.total || "").replace(/[^0-9.]/g, ""));
  if(!Number.isFinite(parDigit) || parDigit <= 0) return { ok:false, reason:"invalid_rate", message:"PAR DIGIT valid amount hona chahiye." };
  if(!Number.isFinite(total) || total <= 0) return { ok:false, reason:"invalid_total", message:"TOTAL valid amount hona chahiye." };
  const expected = Math.round(parDigit * normDigits.length * 100) / 100;
  if(Math.abs(expected - total) > 0.001){
    return { ok:false, reason:"total_mismatch", message:`TOTAL mismatch. Expected ${money(expected)} (${normDigits.length} digit × ${money(parDigit)}), received ${money(total)}.` };
  }
  return { ok:true, market, gameType, digits:normDigits, parDigit, total, rawText:raw };
}
function entrySettings(state){
  const s = state?.entrySettings || {};
  return {
    entryParserEnabled: s.entryParserEnabled !== false,
    groupsOnly: s.groupsOnly !== false,
    strictFormat: s.strictFormat !== false,
    autoDebitWallet: s.autoDebitWallet !== false,
    marketTimingEnabled: s.marketTimingEnabled !== false,
    riskLimitEnabled: s.riskLimitEnabled !== false
  };
}
function riskSettings(state){
  const r = state?.riskSettings || {};
  return {
    marketDailyLimit: Number(r.marketDailyLimit || 0),
    digitDailyLimit: Number(r.digitDailyLimit || 0),
    userDailyLimit: Number(r.userDailyLimit || 0),
    warningPercent: Math.max(1, Math.min(100, Number(r.warningPercent || 80))),
    autoLockOnLimit: r.autoLockOnLimit === true
  };
}
function marketCloseTimes(state){
  return {
    ...DEFAULT_MARKET_CLOSE_TIMES,
    ...((state?.riskSettings?.marketCloseTimes && typeof state.riskSettings.marketCloseTimes === "object") ? state.riskSettings.marketCloseTimes : {}),
    ...((state?.entrySettings?.marketCloseTimes && typeof state.entrySettings.marketCloseTimes === "object") ? state.entrySettings.marketCloseTimes : {})
  };
}
function resolveMarketCloseTime(state, market){
  const times = marketCloseTimes(state);
  const raw = normalizeEntryMarketText(market);
  const compact = compactEntryMarket(market);
  const candidates = [market, raw];
  const canon = canonicalAnkPenelMarket(market) || canonicalJodiMarket(market);
  if(canon) candidates.push(canon);
  for(const key of candidates){
    if(times[key]) return times[key];
    const upper = String(key || "").toUpperCase().trim();
    if(times[upper]) return times[upper];
  }
  for(const [key, value] of Object.entries(times)){
    if(compactEntryMarket(key) === compact) return value;
  }
  return "";
}
function isLockedMarket(state, date, market){
  const locks = state?.marketLocks || {};
  const todayLocks = locks[date] || {};
  const rec = todayLocks[market] || locks[market] || null;
  return !!(rec && (rec.locked === true || rec === true));
}
function lockMarket(state, date, market, reason){
  if(!state.marketLocks || typeof state.marketLocks !== "object") state.marketLocks = {};
  if(!state.marketLocks[date] || typeof state.marketLocks[date] !== "object") state.marketLocks[date] = {};
  state.marketLocks[date][market] = { locked:true, reason:reason || "risk_limit", lockedAt:nowIso() };
}
function isEntryMarketClosed(state, market){
  const time = normalizeTime(resolveMarketCloseTime(state, market) || "");
  if(!time) return { closed:false, cutoff:"" };
  const now = nowHHMM();
  const cut = hhmmToMinutes(time), cur = hhmmToMinutes(now);
  if(cut < 0 || cur < 0) return { closed:false, cutoff:time };
  let closed = false;
  if(cut <= 60){
    closed = (cur > cut && cur < 12 * 60);
  } else {
    closed = cur > cut;
  }
  return { closed, cutoff:time, now };
}
function existingAcceptedEntries(state, date){
  return (Array.isArray(state?.entries) ? state.entries : []).filter(e => e && e.status === "accepted" && e.date === date);
}
function entryHasDigit(e, digit){
  const list = Array.isArray(e?.digits) ? e.digits : String(e?.digits || "").split(/[,\.\s]+/).filter(Boolean);
  const target = String(digit);
  return list.map(x => String(x).padStart(target.length, "0")).includes(target);
}
function calculateRiskLoads(state, date, parsed, userId){
  const entries = existingAcceptedEntries(state, date);
  const userTotal = entries.filter(e => e.userId === userId).reduce((s,e)=>s+Number(e.total||0),0);
  const marketTotal = entries.filter(e => e.market === parsed.market).reduce((s,e)=>s+Number(e.total||0),0);
  const digitLoads = {};
  for(const d of parsed.digits){
    digitLoads[d] = entries
      .filter(e => e.market === parsed.market && e.gameType === parsed.gameType && entryHasDigit(e, d))
      .reduce((s,e)=>s+Number(e.parDigit || 0),0);
  }
  return { userTotal, marketTotal, digitLoads };
}
function validateEntryRiskAndTiming(state, parsed, userId){
  const date = todayISO();
  const settings = entrySettings(state);
  const risk = riskSettings(state);
  const warnings = [];
  if(isLockedMarket(state, date, parsed.market)){
    return { ok:false, message:`${parsed.market} locked hai. Admin unlock karein.` };
  }
  if(settings.marketTimingEnabled){
    const t = isEntryMarketClosed(state, parsed.market);
    if(t.closed) return { ok:false, message:`${parsed.market} ka entry time close ho gaya hai. Cut-off ${t.cutoff} IST, current ${t.now} IST.` };
  }
  if(!settings.riskLimitEnabled) return { ok:true, warnings };
  const loads = calculateRiskLoads(state, date, parsed, userId);
  if(risk.userDailyLimit > 0 && loads.userTotal + parsed.total > risk.userDailyLimit){
    return { ok:false, message:`User daily limit cross ho raha hai. Used ${money(loads.userTotal)}, limit ${money(risk.userDailyLimit)}, entry ${money(parsed.total)}.` };
  }
  if(risk.marketDailyLimit > 0 && loads.marketTotal + parsed.total > risk.marketDailyLimit){
    if(risk.autoLockOnLimit) lockMarket(state, date, parsed.market, "market_daily_limit");
    return { ok:false, saveState:risk.autoLockOnLimit, message:`Market daily limit cross ho raha hai. ${parsed.market} used ${money(loads.marketTotal)}, limit ${money(risk.marketDailyLimit)}, entry ${money(parsed.total)}.` };
  }
  if(risk.digitDailyLimit > 0){
    for(const d of parsed.digits){
      const used = Number(loads.digitLoads[d] || 0);
      if(used + parsed.parDigit > risk.digitDailyLimit){
        if(risk.autoLockOnLimit) lockMarket(state, date, parsed.market, `digit_limit_${d}`);
        return { ok:false, saveState:risk.autoLockOnLimit, message:`Digit load limit cross: ${parsed.market} ${parsed.gameType} ${d}. Used ${money(used)}, limit ${money(risk.digitDailyLimit)}, entry ${money(parsed.parDigit)}.` };
      }
    }
  }
  const wp = risk.warningPercent / 100;
  if(risk.userDailyLimit > 0 && loads.userTotal + parsed.total >= risk.userDailyLimit * wp) warnings.push(`User daily load ${money(loads.userTotal + parsed.total)} / ${money(risk.userDailyLimit)}`);
  if(risk.marketDailyLimit > 0 && loads.marketTotal + parsed.total >= risk.marketDailyLimit * wp) warnings.push(`Market load ${money(loads.marketTotal + parsed.total)} / ${money(risk.marketDailyLimit)}`);
  if(risk.digitDailyLimit > 0){
    for(const d of parsed.digits){
      const val = Number(loads.digitLoads[d] || 0) + parsed.parDigit;
      if(val >= risk.digitDailyLimit * wp) warnings.push(`Digit ${d} load ${money(val)} / ${money(risk.digitDailyLimit)}`);
    }
  }
  return { ok:true, warnings };
}
function findProfileBySender(state, senderJid, meta = {}){
  const profiles = state?.profiles || {};
  const candidates = [senderJid, ...(Array.isArray(meta.senderCandidates) ? meta.senderCandidates : [])];
  const keys = [...new Set(candidates.map(phoneKey).filter(Boolean))];
  if(!keys.length) return null;

  // 1) Exact match against every profile, including admin profiles.
  // Earlier admin profiles were skipped, so admin/test numbers were rejected even when linked.
  for(const [pid, prof] of Object.entries(profiles)){
    const pk = phoneKey(prof?.phone || "");
    if(pk && keys.includes(pk)) return { userId:pid, profile:prof, matchedPhone:pk };
  }

  // 2) Fallback: if a wallet already has this phone, bind through the same userId.
  const wallets = state?.wallets || {};
  for(const [uid, wallet] of Object.entries(wallets)){
    const wk = phoneKey(wallet?.phone || "");
    if(wk && keys.includes(wk) && profiles[uid]) return { userId:uid, profile:profiles[uid], matchedPhone:wk };
  }

  // 3) Safe auto-link: when exactly one non-admin VIP profile has no phone, link this sender to it.
  // This fixes the common setup issue where the VIP was created but phone number was left blank.
  const settings = entrySettings(state);
  if(settings.autoLinkUnknownSender !== false){
    const emptyClients = Object.entries(profiles).filter(([pid, prof]) =>
      !String(pid).startsWith("admin") && (!phoneKey(prof?.phone || ""))
    );
    if(emptyClients.length === 1){
      const [pid, prof] = emptyClients[0];
      prof.phone = keys[0];
      if(!prof.name && meta.pushName) prof.name = meta.pushName;
      prof.autoLinkedPhoneAt = nowIso();
      prof.autoLinkedFrom = candidates[0] || senderJid || "";
      return { userId:pid, profile:prof, matchedPhone:keys[0], autoLinked:true };
    }

    // 4) If no exact VIP exists, create a new client profile for this phone.
    // Wallet default credit is 0, so the entry will still need balance/credit before acceptance.
    const uid = `client_${keys[0]}`;
    if(!profiles[uid]){
      profiles[uid] = profileTemplateForAutoLink(keys[0], meta.pushName || `VIP ${keys[0]}`);
      return { userId:uid, profile:profiles[uid], matchedPhone:keys[0], autoCreated:true };
    }
  }
  return null;
}
function ensureWalletInState(state, userId){
  if(!state.wallets || typeof state.wallets !== "object") state.wallets = {};
  const prof = state?.profiles?.[userId] || {};
  const settings = state.walletSettings || {};
  if(!state.wallets[userId] || typeof state.wallets[userId] !== "object"){
    state.wallets[userId] = { userId, name:prof.name || userId, phone:prof.phone || "", balance:0, creditLimit:Number(settings.defaultCreditLimit || 0), ledger:[], createdAt:nowIso(), updatedAt:nowIso() };
  }
  const w = state.wallets[userId];
  if(!Array.isArray(w.ledger)) w.ledger = [];
  w.balance = Number(w.balance || 0);
  w.creditLimit = Number(w.creditLimit || 0);
  w.name = prof.name || w.name || userId;
  w.phone = prof.phone || w.phone || "";
  return w;
}
function entrySignature(entry){
  return [entry.date, entry.userId, entry.market, entry.gameType, entry.digits.join("."), entry.parDigit, entry.total].join("|");
}
function nextEntryId(state){
  const n = (state.entries || []).length + 1;
  const rand = Math.random().toString(36).slice(2,5).toUpperCase();
  return "E" + todayISO().replace(/-/g,"").slice(2) + "-" + String(n).padStart(4,"0") + rand;
}
async function saveAcceptedEntryToFirebase(parsed, meta){
  const state = await fetchFirebaseState();
  const settings = entrySettings(state);
  if(!settings.entryParserEnabled) return { ok:false, reason:"parser_disabled", message:"Entry parser admin app me OFF hai." };
  if(!state.entries || !Array.isArray(state.entries)) state.entries = [];
  const found = findProfileBySender(state, meta.senderJid, meta);
  if(!found){
    const detected = (Array.isArray(meta.senderCandidates) ? meta.senderCandidates : [meta.senderJid]).map(phoneKey).filter(Boolean)[0] || "phone_not_detected";
    return { ok:false, reason:"profile_not_found", message:`Aapka WhatsApp number VIP profile me linked nahi hai. Detected: ${detected}. Admin app me VIP phone same number se set karein.` };
  }
  const profile = found.profile || {};
  const riskCheck = validateEntryRiskAndTiming(state, parsed, found.userId);
  if(!riskCheck.ok){
    if(riskCheck.saveState) await saveFirebaseState(state);
    return { ok:false, reason:"risk_or_time_rejected", message:riskCheck.message || "Entry risk/time validation failed." };
  }
  const entry = {
    id: nextEntryId(state),
    date: todayISO(),
    createdAt: nowIso(),
    source: "whatsapp_entry_parser",
    status: "accepted",
    userId: found.userId,
    userName: profile.name || found.userId,
    userPhone: profile.phone || "",
    senderJid: meta.senderJid,
    chatJid: meta.chatJid,
    market: parsed.market,
    gameType: parsed.gameType,
    digits: parsed.digits,
    parDigit: parsed.parDigit,
    total: parsed.total,
    rawText: parsed.rawText,
    riskWarning: Array.isArray(riskCheck.warnings) ? riskCheck.warnings : []
  };
  const sig = entrySignature(entry);
  const duplicate = state.entries.find(e => e.status === "accepted" && [e.date, e.userId, e.market, e.gameType, (Array.isArray(e.digits)?e.digits.join("."):String(e.digits||"")), e.parDigit, e.total].join("|") === sig);
  if(duplicate) return { ok:false, reason:"duplicate_entry", message:`Duplicate entry already accepted. ID: ${duplicate.id}` };
  const wSettings = state.walletSettings || {};
  const walletEnabled = wSettings.walletEnabled !== false && settings.autoDebitWallet !== false;
  let wallet = null;
  if(walletEnabled){
    wallet = ensureWalletInState(state, found.userId);
    const available = Number(wallet.balance || 0) + Number(wallet.creditLimit || 0);
    if(available + 0.0001 < parsed.total){
      return { ok:false, reason:"insufficient_wallet", message:`Insufficient wallet. Available ${money(available)}, entry total ${money(parsed.total)}.` };
    }
    const before = Number(wallet.balance || 0);
    const after = Math.round((before - parsed.total) * 100) / 100;
    wallet.balance = after;
    wallet.updatedAt = nowIso();
    wallet.ledger.push({ id:entry.id, time:nowIso(), type:"entry_debit", amount:-parsed.total, balanceBefore:before, balanceAfter:after, note:`Entry debit ${entry.market} ${entry.gameType}`, source:"whatsapp_entry_parser", entryId:entry.id });
    entry.walletDebited = true;
    entry.balanceAfter = after;
  } else {
    entry.walletDebited = false;
  }
  state.entries.push(entry);
  if(!Array.isArray(state.auditLog)) state.auditLog = [];
  state.auditLog.push({ id:entry.id, time:nowIso(), action:"entry_accepted", detail:{ userId:entry.userId, market:entry.market, gameType:entry.gameType, total:entry.total, walletDebited:entry.walletDebited } });
  if(state.auditLog.length > 500) state.auditLog.splice(0, state.auditLog.length - 500);
  await saveFirebaseState(state);
  return { ok:true, entry, wallet };
}
function getMessageText(m){
  const msg = m?.message || {};
  return msg.conversation || msg.extendedTextMessage?.text || msg.imageMessage?.caption || msg.videoMessage?.caption || msg.documentMessage?.caption || "";
}


function defaultSpamGuardSettings(){
  return {
    enabled:true,
    groupsOnly:true,
    linkGuardEnabled:true,
    forwardGuardEnabled:true,
    deleteMessage:true,
    kickEnabled:true,
    exemptAdmins:true,
    linkStrikeLimit:3,
    forwardStrikeLimit:3,
    forwardWindowSeconds:60,
    alertMessage:"⚠️ *ALERT*\nBhai Group Me Link Dalna Mana he",
    warningMessage:"⚠️ *WARNING*\nNext Time Group Me Link Daloge To Remove Kiya Jayega Group Se",
    kickMessage:"🚫 *REMOVED*\n@{number} ko group se remove kiya gaya.\nReason: 3 baar link/forward spam.",
    forwardAlertMessage:"⚠️ *ALERT*\nBhai Group Me Forward/Spam Message Dalna Mana he",
    forwardWarningMessage:"⚠️ *WARNING*\nNext Time Multiple Forward Message Daloge To Remove Kiya Jayega Group Se"
  };
}
function spamGuardSettings(state){
  const d = defaultSpamGuardSettings();
  const s = state?.spamGuardSettings || {};
  return {
    ...d,
    ...s,
    // Guard is intentionally 3-stage: Alert → Warning → Kick/Remove.
    // Keep minimum 3 so it never repeats only ALERT because of a bad/empty saved limit.
    linkStrikeLimit:Math.max(Number(s.linkStrikeLimit || d.linkStrikeLimit), 3),
    forwardStrikeLimit:Math.max(Number(s.forwardStrikeLimit || d.forwardStrikeLimit), 3),
    forwardWindowSeconds:Math.max(Number(s.forwardWindowSeconds || d.forwardWindowSeconds), 10)
  };
}
function deepContextInfo(msg){
  return msg?.extendedTextMessage?.contextInfo || msg?.imageMessage?.contextInfo || msg?.videoMessage?.contextInfo || msg?.documentMessage?.contextInfo || msg?.audioMessage?.contextInfo || msg?.stickerMessage?.contextInfo || {};
}
function isForwardedMessage(m){
  const ci = deepContextInfo(m?.message || {});
  return !!(ci?.isForwarded || Number(ci?.forwardingScore || 0) > 0);
}
function containsBlockedLink(text){
  const t = String(text || "");
  if(!t.trim()) return false;
  const patterns = [
    /https?:\/\/\S+/i,
    /www\.\S+/i,
    /chat\.whatsapp\.com\/[A-Za-z0-9_-]+/i,
    /t\.me\/\S+/i,
    /telegram\.me\/\S+/i,
    /(?:instagram|facebook|fb|youtube|youtu\.be|x\.com|twitter|threads|snapchat)\.com\/\S+/i,
    /\b(?:bit\.ly|tinyurl\.com|shorturl\.at|cutt\.ly|rebrand\.ly|linktr\.ee)\/\S+/i,
    /\b[a-z0-9-]+\.(?:com|in|net|org|co|me|io|app|site|online|xyz|club|live|shop|store|info)(?:\/\S*)?\b/i
  ];
  return patterns.some(re => re.test(t));
}
function mentionNumberFromJid(jid){
  const d = String(jid || "").replace(/\D/g, "");
  return d ? d.slice(-12) : "user";
}
function guardNormalizeJid(v){
  return String(v || "").trim().replace(/:\d+(?=@)/, "");
}
function guardIdentityFromCandidates(candidates){
  const list = uniqueJids(candidates || []);
  // Prefer real phone number because @lid can vary across WhatsApp multi-device contexts.
  for(const c of list){
    const pk = phoneKey(c);
    if(pk) return { key:`phone:${pk}`, mention: pk.length === 10 ? `91${pk}@s.whatsapp.net` : `${pk}@s.whatsapp.net` };
  }
  const lid = list.find(x => /@lid$/i.test(x));
  if(lid) return { key:`lid:${guardNormalizeJid(lid)}`, mention: guardNormalizeJid(lid) };
  const jid = list.find(x => x.includes("@"));
  if(jid) return { key:`jid:${guardNormalizeJid(jid)}`, mention: guardNormalizeJid(jid) };
  return { key:"unknown", mention:"" };
}
function spamKey(chatJid, identityKey, kind){
  return `${todayISO()}|${chatJid}|${identityKey}|${kind}`;
}
function guardAliasKeys(chatJid, kind, candidates = [], pushName = ""){
  const keys = [];
  const add = (label, value) => {
    const v = String(value || "").trim().toLowerCase();
    if(v) keys.push(spamKey(chatJid, `${label}:${v}`, kind));
  };
  for(const c of uniqueJids(candidates || [])){
    const norm = guardNormalizeJid(c);
    const ph = phoneKey(norm);
    if(ph) add("phone", ph);
    if(norm && norm.includes("@")) add("jid", norm);
    if(/@lid$/i.test(norm)) add("lid", norm);
  }
  const nm = String(pushName || "").trim().replace(/\s+/g, " ").slice(0,60);
  if(nm) add("name", nm);
  return [...new Set(keys)];
}
function getSpamGuardRecordFromAliases(aliasKeys, fallback = {}){
  let best = null;
  for(const k of (aliasKeys || [])){
    const a = spamGuardLocalState?.strikes?.[k];
    const b = fallback?.[k];
    for(const rec of [a,b]){
      if(!rec || typeof rec !== "object") continue;
      if(!best || Number(rec.count || 0) > Number(best.count || 0)) best = rec;
    }
  }
  return best;
}
function saveSpamGuardLocalState(){
  try{
    spamGuardLocalState.strikes = spamGuardLocalState.strikes && typeof spamGuardLocalState.strikes === "object" ? spamGuardLocalState.strikes : {};
    spamGuardLocalState.events = Array.isArray(spamGuardLocalState.events) ? spamGuardLocalState.events.slice(-500) : [];
    saveJson(SPAM_GUARD_STATE_FILE, spamGuardLocalState);
  }catch(e){ console.log("SpamGuard local save failed:", e.message); }
}
async function deleteIncomingMessage(chatJid, m){
  try{
    if(sock && connected && chatJid && m?.key) await sock.sendMessage(chatJid, { delete: m.key });
    return true;
  }catch(e){ console.log("SpamGuard delete failed:", e.message); return false; }
}
async function isGroupAdmin(chatJid, senderJid){
  try{
    if(!chatJid.endsWith("@g.us") || !senderJid) return false;
    const meta = await sock.groupMetadata(chatJid);
    const target = String(senderJid).replace(/:\d+(?=@)/, "");
    const p = (meta.participants || []).find(x => String(x.id || "").replace(/:\d+(?=@)/, "") === target);
    return !!(p && (p.admin === "admin" || p.admin === "superadmin"));
  }catch(e){ return false; }
}
function uniqueJids(list){
  return [...new Set((list || []).map(x => String(x || "").trim().replace(/:\d+(?=@)/, "")).filter(Boolean))];
}
function guardParticipantCandidates(m, senderJid){
  return uniqueJids([
    senderJid,
    m?.key?.participantPn,
    m?.key?.senderPn,
    m?.participantPn,
    m?.senderPn,
    m?.key?.participant,
    m?.participant
  ]);
}
async function removeGroupParticipant(chatJid, senderJid, candidates = []){
  const tried = [];
  try{
    if(!sock || !connected || !chatJid.endsWith("@g.us")) return { ok:false, error:"not_group_or_offline", tried };

    const rawCandidates = uniqueJids([senderJid, ...candidates]);
    const phoneCandidates = rawCandidates.map(phoneKey).filter(Boolean);
    const directIds = [...rawCandidates];

    // Baileys/WhatsApp sometimes emits @lid in messages but group removal may require the participant id
    // exactly as present in group metadata. Add matching metadata participant ids by phone or raw id.
    try{
      const meta = await sock.groupMetadata(chatJid);
      for(const p of (meta.participants || [])){
        const pid = guardNormalizeJid(p.id || p.jid || "");
        if(!pid) continue;
        const pPhone = phoneKey(pid);
        if(rawCandidates.includes(pid) || (pPhone && phoneCandidates.includes(pPhone))) directIds.push(pid);
      }
    }catch(e){ console.log("SpamGuard metadata lookup failed:", e.message); }

    const ids = uniqueJids(directIds).filter(x => x && x.includes("@") && x !== chatJid);
    for(const id of ids){
      tried.push(id);
      try{
        await sock.groupParticipantsUpdate(chatJid, [id], "remove");
        return { ok:true, target:id, tried };
      }catch(e){
        console.log("SpamGuard remove try failed:", id, e.message);
      }
    }
    return { ok:false, error:"all_candidates_failed", tried };
  }catch(e){
    console.log("SpamGuard remove failed:", e.message);
    return { ok:false, error:e.message, tried };
  }
}
function renderSpamGuardMessage(tpl, senderJid){
  const num = mentionNumberFromJid(senderJid);
  return String(tpl || "").replace(/\{number\}/g, num);
}
async function sendSpamGuardNotice(chatJid, text, mentionJid, quoted){
  if(!sock || !connected || !chatJid || !text) return { ok:false, error:"offline_or_empty" };
  try{
    const opts = quoted ? { quoted } : undefined;
    const payload = { text:String(text) };
    if(mentionJid && String(mentionJid).includes("@")) payload.mentions = [mentionJid];
    const r = await sock.sendMessage(chatJid, payload, opts);
    return { ok:true, id:r?.key?.id || "sent" };
  }catch(e){
    console.log("SpamGuard notice failed:", e.message);
    return { ok:false, error:e.message };
  }
}
function guardSleep(ms){ return new Promise(resolve => setTimeout(resolve, ms)); }
async function handleSpamGuardMessage(m){
  try{
    if(!m || m.key?.fromMe) return false;
    const chatJid = m.key?.remoteJid || "";
    if(!chatJid || chatJid === "status@broadcast") return false;
    const state = await fetchFirebaseState();
    const cfg = spamGuardSettings(state);
    if(!cfg.enabled) return false;
    if(cfg.groupsOnly && !chatJid.endsWith("@g.us")) return false;
    const senderCandidates = senderCandidatesFromMessage(m, chatJid);
    const senderJid = chatJid.endsWith("@g.us") ? (senderCandidates[0] || m.key?.participant || "") : chatJid;
    if(!senderJid) return false;
    if(cfg.exemptAdmins && await isGroupAdmin(chatJid, senderJid)) return false;

    const text = getMessageText(m);
    const hasLink = cfg.linkGuardEnabled && containsBlockedLink(text);
    const isFwd = cfg.forwardGuardEnabled && isForwardedMessage(m);
    if(!hasLink && !isFwd) return false;

    state.spamGuardStrikes = state.spamGuardStrikes && typeof state.spamGuardStrikes === "object" ? state.spamGuardStrikes : {};
    state.spamGuardEvents = Array.isArray(state.spamGuardEvents) ? state.spamGuardEvents : [];
    spamGuardLocalState.strikes = spamGuardLocalState.strikes && typeof spamGuardLocalState.strikes === "object" ? spamGuardLocalState.strikes : {};
    spamGuardLocalState.events = Array.isArray(spamGuardLocalState.events) ? spamGuardLocalState.events : [];

    const kind = hasLink ? "link" : "forward";
    const participantCandidates = guardParticipantCandidates(m, senderJid);
    const allIdentityCandidates = [senderJid, ...senderCandidates, ...participantCandidates];
    const identity = guardIdentityFromCandidates(allIdentityCandidates);
    const aliasKeys = guardAliasKeys(chatJid, kind, allIdentityCandidates, m.pushName || "");
    const primaryKey = aliasKeys[0] || spamKey(chatJid, identity.key, kind);

    // Robust 3-stage source of truth:
    // Baileys may alternate @lid / @s.whatsapp.net / PN ids. We read all aliases, take the highest count,
    // then write the same count back to every alias so Alert -> Warning -> Kick cannot reset to Alert.
    let record = getSpamGuardRecordFromAliases(aliasKeys, state.spamGuardStrikes) || { count:0, firstAt:nowIso(), lastAt:"", kind, chatJid, senderJid, identityKey:identity.key, aliasKeys };
    if(kind === "forward"){
      const nowMs = Date.now();
      const firstMs = record.firstMs || nowMs;
      if((nowMs - firstMs) > cfg.forwardWindowSeconds * 1000) record = { count:0, firstAt:nowIso(), firstMs:nowMs, lastAt:"", kind, chatJid, senderJid, identityKey:identity.key, aliasKeys };
      record.firstMs = record.firstMs || firstMs;
    }
    record = { ...record };
    record.count = Number(record.count || 0) + 1;
    record.lastAt = nowIso();
    record.senderJid = senderJid;
    record.identityKey = identity.key;
    record.aliasKeys = aliasKeys;
    for(const k of (aliasKeys.length ? aliasKeys : [primaryKey])){
      spamGuardLocalState.strikes[k] = record;
      state.spamGuardStrikes[k] = record;
    }
    saveSpamGuardLocalState();

    const limit = kind === "link" ? cfg.linkStrikeLimit : cfg.forwardStrikeLimit;
    let action = "alert";
    let msgText = kind === "link" ? cfg.alertMessage : cfg.forwardAlertMessage;
    if(record.count >= limit){ action = "remove"; msgText = cfg.kickMessage; }
    else if(record.count >= 2){ action = "warning"; msgText = kind === "link" ? cfg.warningMessage : cfg.forwardWarningMessage; }

    const mentionJid = identity.mention || participantCandidates.find(x => x.endsWith("@s.whatsapp.net")) || senderJid;
    const rendered = renderSpamGuardMessage(msgText, mentionJid);

    // Send alert/warning first, then delete the spam message. Some WhatsApp builds drop follow-up sends if the source message is deleted first.
    const noticeResult = rendered ? await sendSpamGuardNotice(chatJid, rendered, mentionJid, m) : { ok:false, error:"empty_message" };
    if(cfg.deleteMessage){
      await guardSleep(250);
      await deleteIncomingMessage(chatJid, m);
    }

    let removeResult = { ok:false, skipped: action !== "remove" || !cfg.kickEnabled };
    if(action === "remove" && cfg.kickEnabled){
      await guardSleep(350);
      removeResult = await removeGroupParticipant(chatJid, senderJid, participantCandidates);
    }

    const event = {
      id:`SG${Date.now()}`, time:nowIso(), date:todayISO(), chatJid, senderJid, identityKey:identity.key, aliasKeys:(aliasKeys || []).slice(0,8), kind, count:record.count, action,
      noticeOk:!!noticeResult.ok, noticeError:noticeResult.error || "",
      removeOk:!!removeResult.ok, removeError:removeResult.error || "", removeTarget:removeResult.target || "",
      candidates:participantCandidates.slice(0,8), triedRemove:(removeResult.tried || []).slice(0,8), textSample:String(text || "").slice(0,120)
    };
    state.spamGuardEvents.push(event);
    spamGuardLocalState.events.push(event);
    if(state.spamGuardEvents.length > 300) state.spamGuardEvents.splice(0, state.spamGuardEvents.length - 300);
    if(spamGuardLocalState.events.length > 500) spamGuardLocalState.events.splice(0, spamGuardLocalState.events.length - 500);
    saveSpamGuardLocalState();
    await saveFirebaseState(state);

    console.log(`🛡️ SpamGuard ${action}: ${kind} ${record.count}/${limit} ${identity.key} aliases=${(aliasKeys || []).length} notice=${noticeResult.ok?"OK":"FAIL"} remove=${removeResult.ok?"OK":(removeResult.skipped?"SKIP":"FAIL")} tried=${(removeResult.tried || []).join(",")}`);
    return true;
  }catch(e){ console.log("SpamGuard error:", e.response ? `HTTP ${e.response.status}` : e.message); return false; }
}
async function replyToMessage(chatJid, text, quoted){
  if(!sock || !connected || !chatJid || !text) return;
  try { await sock.sendMessage(chatJid, { text:String(text) }, quoted ? { quoted } : undefined); }
  catch(e){ console.log("Reply failed:", e.message); }
}
function acceptedEntryText(entry){
  const warn = Array.isArray(entry.riskWarning) && entry.riskWarning.length ? `⚠️ *Warning:* ${entry.riskWarning.slice(0,3).join(" | ")}\n` : "";
  return `✅ *ENTRY ACCEPTED*\n━━━━━━━━━━━━━━━━━━━━\n🆔 *ID:* ${entry.id}\n👤 *User:* ${entry.userName}\n🔥 *Market:* ${entry.market}\n🎮 *Type:* ${entry.gameType}\n🔢 *Digits:* ${entry.digits.join(",")}\n💵 *Par Digit:* ${money(entry.parDigit)}\n💰 *Total:* ${money(entry.total)}\n${entry.walletDebited ? `💳 *Wallet Debited:* ${money(entry.total)}\n` : ""}${warn}━━━━━━━━━━━━━━━━━━━━`;
}
function rejectedEntryText(reason){
  return `❌ *ENTRY REJECTED*\n━━━━━━━━━━━━━━━━━━━━\n📝 *Reason:* ${reason}\n━━━━━━━━━━━━━━━━━━━━\nCorrect format:\nMARKET: KALYAN OPEN\nTYPE: ANK\nDIGITS: 1,2,3\nPAR DIGIT: 100\nTOTAL: 300`;
}
async function handleIncomingEntryMessage(m){
  try{
    if(!m || m.key?.fromMe) return;
    const chatJid = m.key?.remoteJid || "";
    if(!chatJid || chatJid === "status@broadcast") return;
    const text = getMessageText(m);
    if(!/\bMARKET\s*:/i.test(text) || !/\bDIGITS?\s*:/i.test(text)) return;
    const parsed = parseEntryCard(text);
    if(parsed.silent) return;
    const stateLite = await fetchFirebaseState();
    const settings = entrySettings(stateLite);
    if(!settings.entryParserEnabled) return;
    if(settings.groupsOnly && !chatJid.endsWith("@g.us")) return;
    if(!parsed.ok){ await replyToMessage(chatJid, rejectedEntryText(parsed.message || parsed.reason || "Invalid entry."), m); return; }
    if(isDeletedMarket(stateLite, parsed.market)){ await replyToMessage(chatJid, "❌ Market deleted/disabled. Entry rejected.", m); return; }
    const senderCandidates = senderCandidatesFromMessage(m, chatJid);
    const senderJid = chatJid.endsWith("@g.us") ? (senderCandidates[0] || m.key?.participant || "") : chatJid;
    const saved = await saveAcceptedEntryToFirebase(parsed, { chatJid, senderJid, senderCandidates, pushName:m.pushName || m.verifiedBizName || "" });
    if(!saved.ok){ await replyToMessage(chatJid, rejectedEntryText(saved.message || saved.reason || "Entry rejected."), m); return; }
    await replyToMessage(chatJid, acceptedEntryText(saved.entry), m);
    console.log(`🧾 Entry accepted ${saved.entry.id}: ${saved.entry.market} ${saved.entry.gameType} ${saved.entry.total}`);
  } catch(e){
    console.log("Entry parser error:", e.response ? `HTTP ${e.response.status}` : e.message);
  }
}
function cleanResult(v){ return String(v || "").trim().replace(/\s+/g, ""); }
function resultStage(v){
  const t = cleanResult(v);
  if(/^\d{3}-\d$/.test(t)) return "open";
  if(/^\d{3}-\d{2}-\d{3}$/.test(t)) return "close";
  return "";
}
function formatResultMessage(market, result){
  return `🏆 TITAN NOVA RESULT\n\n🔥 MARKET: ${market}\n🎯 RESULT: ${cleanResult(result)}\n\n✅ Updated Successfully`;
}

const RESULT_MARKET_ALIASES = [
  { market:"SRIDEV DAY", aliases:["SRIDEV DAY", "SRIDEVI DAY", "SRIDEVI"] },
  { market:"TIME BAZAR", aliases:["TIME BAZAR"] },
  { market:"MADHUR DAY", aliases:["MADHUR DAY"] },
  { market:"MILAN DAY", aliases:["MILAN DAY"] },
  { market:"RAJDHANI DAY", aliases:["RAJDHANI DAY"] },
  { market:"SUPREME DAY", aliases:["SUPREME DAY"] },
  { market:"KALYAN", aliases:["KALYAN"] },
  { market:"SRIDEVI NIGHT", aliases:["SRIDEVI NIGHT", "SRIDEV NIGHT"] },
  { market:"MADHUR NIGHT", aliases:["MADHUR NIGHT", "MADHURI NIGHT"] },
  { market:"SUPREME NIGHT", aliases:["SUPREME NIGHT"] },
  { market:"MILAN NIGHT", aliases:["MILAN NIGHT"] },
  { market:"KALYAN NIGHT", aliases:["KALYAN NIGHT", "MAIN KALYAN NIGHT"] },
  { market:"RAJDHANI NIGHT", aliases:["RAJDHANI NIGHT"] },
  { market:"MAIN BAZAR", aliases:["MAIN BAZAR", "MAINBAZAR", "MAIN BAZAR NIGHT"] }
];
const RESULT_ALIAS_LOOKUP = new Map();
for(const item of RESULT_MARKET_ALIASES){
  for(const a of item.aliases) RESULT_ALIAS_LOOKUP.set(normalizeMarketText(a), item.market);
}

function normalizeMarketText(v){
  return String(v || "")
    .toUpperCase()
    .replace(/&AMP;/g, "&")
    .replace(/[^A-Z0-9]+/g, " ")
    .trim()
    .replace(/\s+/g, " ");
}
function decodeEntitiesBasic(v){
  return String(v || "")
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&#45;/g, "-")
    .replace(/&ndash;|&mdash;|&#8211;|&#8212;/gi, "-");
}
function htmlToLines(html){
  return decodeEntitiesBasic(String(html || ""))
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<br\s*\/?\s*>/gi, "\n")
    .replace(/<\/div>|<\/p>|<\/h[1-6]>|<\/li>|<\/tr>|<\/section>|<\/article>/gi, "\n")
    .replace(/<[^>]+>/g, " ")
    .split(/\n+/)
    .map(x => x.replace(/\s+/g, " ").trim())
    .filter(Boolean);
}
function cleanScrapedResult(v){
  const raw = String(v || "")
    .replace(/[–—−]/g, "-")
    .replace(/&nbsp;/gi, " ")
    .trim();
  if(!raw || raw.includes("*")) return "";
  // Extract only the result at the beginning of the text.
  // This avoids merging following time text, e.g. "144-9 9:35 PM" must stay "144-9".
  const close = raw.match(/^\s*(\d{3})\s*-\s*(\d{2})\s*-\s*(\d{3})(?!\d|\s*-\s*\d)/);
  if(close) return `${close[1]}-${close[2]}-${close[3]}`;
  const open = raw.match(/^\s*(\d{3})\s*-\s*(\d)(?!\d|\s*-\s*\d)/);
  if(open) return `${open[1]}-${open[2]}`;
  return "";
}
function escapeRegex(s){ return String(s).replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }
const RESULT_ALIAS_ROWS = [];
for(const item of RESULT_MARKET_ALIASES){
  for(const alias of item.aliases){
    RESULT_ALIAS_ROWS.push({ market:item.market, alias:String(alias).toUpperCase().replace(/\s+/g, " ").trim() });
  }
}
RESULT_ALIAS_ROWS.sort((a,b)=>b.alias.length-a.alias.length);
function resultAtStart(v){ return cleanScrapedResult(String(v || "").trim()); }
function liveStatusFromText(v){
  const t = normalizeMarketText(String(v || ""));
  if(!t) return "";
  if(/\b(LOADING|LOADING\.\.\.|WAIT|WAITING|COMING SOON)\b/i.test(t)) return "loading";
  if(/\b(HOLIDAY|CLOSED|NO RESULT)\b/i.test(t)) return "holiday";
  return "";
}
function ensureLiveDateState(date){
  if(!liveResultState || typeof liveResultState !== "object") liveResultState = {};
  if(!liveResultState[date]) liveResultState[date] = {};
  return liveResultState[date];
}
function rememberLiveStatus(item){
  const date = todayISO();
  if(!item || !item.market) return;
  const day = ensureLiveDateState(date);
  const rec = day[item.market] || { market:item.market };
  if(item.status){
    rec.lastStatus = item.status;
    rec.lastStatusAt = new Date().toISOString();
    rec.rawStatusLine = item.rawStatusLine || "";
    if(item.status === "loading"){
      rec.loadingSeen = true;
      rec.loadingSeenAt = rec.lastStatusAt;
    }
    if(item.status === "holiday"){
      rec.holidaySeen = true;
      rec.holidaySeenAt = rec.lastStatusAt;
    }
  }
  if(item.result){
    rec.lastResult = cleanResult(item.result);
    rec.lastResultStage = resultStage(item.result);
    rec.lastResultAt = new Date().toISOString();
  }
  day[item.market] = rec;
  // Keep only today's live state so old Loading/Result transitions never leak into tomorrow.
  for(const k of Object.keys(liveResultState)) if(k !== date) delete liveResultState[k];
  saveJson(LIVE_RESULT_STATE_FILE, liveResultState);
}
function liveStateForMarket(market){
  const day = ensureLiveDateState(todayISO());
  return day[market] || {};
}
function marketFromLineStart(line){
  const raw = decodeEntitiesBasic(line).toUpperCase().replace(/\s+/g, " ").trim();
  if(!raw) return null;
  for(const row of RESULT_ALIAS_ROWS){
    const re = new RegExp("^" + escapeRegex(row.alias).replace(/\\\s\+/g, "\\s+") + "(?:\\s+|$)");
    const m = raw.match(re);
    if(!m) continue;
    const rest = raw.slice(m[0].length).trim();
    const result = resultAtStart(rest);
    if(resultStage(result)) return { market:row.market, result, stage:resultStage(result), status:"result", rest, exact:false };
    const status = liveStatusFromText(rest);
    // Treat as a standalone market line only when it does not continue as another market name.
    // Example: "KALYAN MORNING 150-61-560" must not become "KALYAN".
    if(!rest || status || /^(\*|\-)/i.test(rest)) return { market:row.market, result:"", stage:"", status, rest, exact:true };
  }
  return null;
}
function marketFromLineAnywhere(line){
  const raw = decodeEntitiesBasic(line).toUpperCase().replace(/\s+/g, " ").trim();
  if(!raw) return null;
  for(const row of RESULT_ALIAS_ROWS){
    const aliasPattern = escapeRegex(row.alias).replace(/\s+/g, "\\s+");
    const re = new RegExp("(?:^|\\s)" + aliasPattern + "(?:\\s+|$)(.*)$");
    const m = raw.match(re);
    if(!m) continue;
    const rest = String(m[1] || "").replace(/^[:\-]+\s*/, "").trim();
    const result = resultAtStart(rest);
    if(resultStage(result)) return { market:row.market, result, stage:resultStage(result), status:"result", rest, exact:false };
    const status = liveStatusFromText(rest);
    if(status) return { market:row.market, result:"", stage:"", status, rest, exact:false };
  }
  return null;
}

function findLiveResultSlices(lines){
  const slices = [];
  for(let i=0; i<lines.length; i++){
    const n = normalizeMarketText(lines[i]);
    if(n.includes("LIVE RESULT")){
      let end = Math.min(lines.length, i + 90);
      for(let j=i+1; j<end; j++){
        const x = normalizeMarketText(lines[j]);
        if(x.includes("WORLD ME SABSE FAST") || x.includes("PLAY ONLINE MATKA") || x.includes("INDIA S BIGGEST") || x.includes("BOOKING OPEN")){ end = j; break; }
      }
      slices.push({ start:i+1, end, label:"DPBOSS LIVE RESULT" });
    }
    if(n.includes("WORLD ME SABSE FAST") || n.includes("LIVE MATKA RESULT")){
      let end = Math.min(lines.length, i + 900);
      for(let j=i+1; j<end; j++){
        const x = normalizeMarketText(lines[j]);
        if(x.includes("CONTACT FOR ANY SUPPORT") || x.includes("MEMBER S FORUM") || x.includes("SATTA MATKA JODI CHART") || x.includes("WEEKLY PANEL") || x.includes("OPEN TO CLOSE FREE GAME ZONE") || x.includes("GUESSING") || x.includes("FIX SINGLE")){ end = j; break; }
      }
      slices.push({ start:i+1, end, label:n.includes("WORLD ME SABSE FAST") ? "DPBOSS MAIN RESULT" : "LIVE MATKA RESULT" });
    }
    if(n.includes("LIVE UPDATE")){
      let end = Math.min(lines.length, i + 80);
      for(let j=i+1; j<end; j++){
        const x = normalizeMarketText(lines[j]);
        if(x.includes("LIVE MATKA RESULT") || x.includes("WORLD ME SABSE FAST") || x.includes("PLAY ONLINE MATKA") || x.includes("INDIA S BIGGEST")){ end = j; break; }
      }
      slices.push({ start:i+1, end, label:"LIVE UPDATE" });
    }
  }
  if(!slices.length){
    let end = Math.min(lines.length, 720);
    for(let j=0; j<end; j++){
      const x = normalizeMarketText(lines[j]);
      if(x.includes("CONTACT FOR ANY SUPPORT") || x.includes("MEMBER S FORUM") || x.includes("SATTA MATKA JODI CHART") || x.includes("WEEKLY PANEL") || x.includes("OPEN TO CLOSE FREE GAME ZONE")){ end = j; break; }
    }
    slices.push({ start:0, end, label:"TOP SAFE BLOCK" });
  }
  return slices;
}
function chooseBetterResult(prev, item){
  if(!prev) return item;
  // Prefer the dedicated LIVE MATKA RESULT list over small widgets/fallback blocks.
  const rank = (x) => (x.block === "DPBOSS LIVE RESULT" ? 5 : (x.block === "DPBOSS MAIN RESULT" ? 4 : (x.block === "LIVE MATKA RESULT" ? 3 : (x.block === "LIVE UPDATE" ? 2 : 1))));
  if(rank(item) !== rank(prev)) return rank(item) > rank(prev) ? item : prev;
  // Same stage only: never replace a fresh open result with a full close result here.
  // Fresh lifecycle is enforced later: open 123-4 must exist before close 123-45-678 is accepted.
  return prev;
}
function extractResultsFromHtml(html, sourceUrl){
  const lines = htmlToLines(html);
  // Keep every distinct market+stage+result candidate.
  // DPBOSSE pages can contain old complete results and fresh live results in nearby blocks.
  // If we collapse only by market+stage, a stale close can hide the fresh matching close.
  const found = new Map();
  const statuses = [];
  const slices = findLiveResultSlices(lines);
  for(const slice of slices){
    for(let i=slice.start; i<slice.end; i++){
      let hit = marketFromLineStart(lines[i]);
      if(!hit && slice.label === "DPBOSS LIVE RESULT") hit = marketFromLineAnywhere(lines[i]);
      if(!hit) continue;
      if(hit.result && hit.stage){
        const item = { market:hit.market, result:hit.result, stage:hit.stage, status:"result", sourceUrl, rawMarketLine:lines[i], rawResultLine:lines[i], block:slice.label, confidence:"same_line", lineIndex:i };
        const key = `${item.market}_${item.stage}_${cleanResult(item.result)}`;
        found.set(key, chooseBetterResult(found.get(key), item));
        continue;
      }
      if(hit.status === "loading" || hit.status === "holiday"){
        statuses.push({ market:hit.market, status:hit.status, sourceUrl, rawMarketLine:lines[i], rawStatusLine:lines[i], block:slice.label, confidence:"same_line_status" });
        continue;
      }
      // Separate market line: accept only the immediate next 1-3 clean lines before any next market.
      // Handles the real widget pattern:
      // MARKET NAME / Loading... / Refresh -> later MARKET NAME / 123-4 / Refresh -> later MARKET NAME / 123-45-678 / Refresh
      for(let j=i+1; j<Math.min(slice.end, i+4); j++){
        if(marketFromLineStart(lines[j])) break;
        const status = liveStatusFromText(lines[j]);
        if(status){
          statuses.push({ market:hit.market, status, sourceUrl, rawMarketLine:lines[i], rawStatusLine:lines[j], block:slice.label, confidence:"next_line_status" });
          break;
        }
        const result = resultAtStart(lines[j]);
        const stage = resultStage(result);
        if(stage){
          const item = { market:hit.market, result, stage, status:"result", sourceUrl, rawMarketLine:lines[i], rawResultLine:lines[j], block:slice.label, confidence:"next_line", lineIndex:j };
          const key = `${item.market}_${item.stage}_${cleanResult(item.result)}`;
          found.set(key, chooseBetterResult(found.get(key), item));
          break;
        }
      }
    }
  }
  return { results:[...found.values()], statuses };
}
async function scrapeLiveResultPages(){
  const byMarketStage = new Map();
  const statuses = [];
  const errors = [];
  const headers = {
    "User-Agent":"Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36",
    "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language":"en-IN,en;q=0.9,hi;q=0.8",
    "Cache-Control":"no-cache, no-store, must-revalidate",
    "Pragma":"no-cache",
    "Expires":"0"
  };
  for(const url of RESULT_SCRAPE_URLS){
    try {
      const fetchUrl = url + (url.includes("?") ? "&" : "?") + "_=" + Date.now();
      const res = await axios.get(fetchUrl, { timeout:8000, headers });
      const parsed = extractResultsFromHtml(res.data || "", url);
      for(const st of parsed.statuses || []) statuses.push(st);
      for(const item of parsed.results || []){
        const key = `${item.market}_${item.stage}_${cleanResult(item.result)}`;
        const prev = byMarketStage.get(key);
        byMarketStage.set(key, chooseBetterResult(prev, item));
      }
    } catch(e) {
      errors.push(`${url}: ${e.response ? "HTTP "+e.response.status : e.message}`);
    }
  }
  return { results:[...byMarketStage.values()], statuses, errors };
}
function confirmScrapedResults(scraped){
  const date = todayISO();
  const confirmed = [];
  const seenKeys = new Set();
  for(const item of scraped || []){
    const stage = resultStage(item.result);
    if(!stage) continue;
    const key = `${date}_${item.market}_${stage}`;
    const signature = cleanResult(item.result);
    seenKeys.add(key);
    const old = scrapeConfirm[key] || {};
    if(old.signature === signature){
      old.count = Number(old.count || 0) + 1;
    } else {
      old.signature = signature;
      old.count = 1;
      old.firstSeenAt = new Date().toISOString();
    }
    old.market = item.market;
    old.stage = stage;
    old.result = signature;
    old.lastSeenAt = new Date().toISOString();
    old.sourceUrl = item.sourceUrl || "";
    old.rawMarketLine = item.rawMarketLine || "";
    old.rawResultLine = item.rawResultLine || "";
    old.block = item.block || "";
    scrapeConfirm[key] = old;
    if(old.count >= RESULT_SCRAPE_CONFIRM_COUNT){
      confirmed.push({ ...item, result:signature, stage, confirmCount:old.count });
    }
  }
  // Keep file small: remove old dates.
  for(const key of Object.keys(scrapeConfirm)){
    if(!key.startsWith(date + "_")) delete scrapeConfirm[key];
  }
  saveJson(SCRAPE_CONFIRM_FILE, scrapeConfirm);
  return confirmed;
}

function extractInviteCode(raw){
  const t = String(raw || "").trim();
  const m = t.match(/chat\.whatsapp\.com\/([A-Za-z0-9_-]+)/i);
  if(m) return m[1];
  if(/^[A-Za-z0-9_-]{20,}$/.test(t) && !/^\d+$/.test(t) && !t.includes("@")) return t;
  return "";
}

function normalizeTarget(raw){
  let t = targetValue(raw);
  if(!t) return "";
  t = t.replace(/[<>]/g, "").trim();
  const jidMatch = t.match(/([0-9A-Za-z._:-]+@(?:g\.us|s\.whatsapp\.net))/i);
  if(jidMatch) return jidMatch[1].replace(/:\d+(?=@)/, "");
  if(t.includes("@g.us") || t.includes("@s.whatsapp.net")) return t.replace(/:\d+(?=@)/, "");
  const inviteCode = extractInviteCode(t);
  if(inviteCode) return "invite:" + inviteCode;
  // Supports wa.me/91xxxx, api.whatsapp.com/send?phone=, +91 xxxx, and plain 10 digit numbers.
  let digits = t.replace(/[^0-9]/g, "");
  if(!digits) return "";
  // Avoid accidentally merging a visible serial number with the phone; keep the last Indian number shape.
  if(digits.length > 12 && digits.endsWith("0")) digits = digits.slice(-12);
  if(digits.length > 12) digits = digits.slice(-12);
  if(digits.length === 10) digits = "91" + digits;
  if(digits.length < 10) return "";
  return digits + "@s.whatsapp.net";
}

async function resolveTarget(rawTarget){
  let jid = normalizeTarget(rawTarget);
  if(!jid) return "";
  if(jid.startsWith("invite:")){
    if(!sock || !connected) return "";
    const code = jid.slice(7);
    try {
      const info = await sock.groupGetInviteInfo(code);
      if(info?.id) return String(info.id).includes("@g.us") ? String(info.id) : String(info.id) + "@g.us";
    } catch(e) {
      console.log("Group invite resolve failed:", e.message || e);
      return "";
    }
  }
  return jid;
}

async function isValidTarget(jid){
  if(!jid) return false;
  if(jid.endsWith("@g.us")) return true;
  if(!sock || !connected) return false;
  try {
    const res = await sock.onWhatsApp(jid.replace("@s.whatsapp.net", ""));
    return Array.isArray(res) && res[0] && !!res[0].exists;
  } catch { return true; }
}

async function sendText(rawTarget, text){
  const jid = await resolveTarget(rawTarget);
  if(!jid){
    gatewayHealth.lastSendAt = nowIso();
    gatewayHealth.lastSendOk = false;
    gatewayHealth.lastSendTarget = String(rawTarget || "");
    gatewayHealth.lastSendError = "invalid/unresolved target";
    return {ok:false, rawTarget, target:rawTarget, error:"invalid/unresolved target"};
  }
  if(!sock || !connected){
    gatewayHealth.lastSendAt = nowIso();
    gatewayHealth.lastSendOk = false;
    gatewayHealth.lastSendTarget = jid;
    gatewayHealth.lastSendError = "WhatsApp not connected";
    return {ok:false, rawTarget, target:jid, error:"WhatsApp not connected"};
  }
  const okTarget = await isValidTarget(jid);
  if(!okTarget){
    gatewayHealth.lastSendAt = nowIso();
    gatewayHealth.lastSendOk = false;
    gatewayHealth.lastSendTarget = jid;
    gatewayHealth.lastSendError = "number is not on WhatsApp";
    return {ok:false, rawTarget, target:jid, error:"number is not on WhatsApp"};
  }
  try {
    const r = await sock.sendMessage(jid, { text: String(text || "") });
    gatewayHealth.lastSendAt = nowIso();
    gatewayHealth.lastSendOk = true;
    gatewayHealth.lastSendTarget = jid;
    gatewayHealth.lastSendError = "";
    return {ok:true, rawTarget, target:jid, id:r?.key?.id || "sent"};
  } catch(e) {
    gatewayHealth.lastSendAt = nowIso();
    gatewayHealth.lastSendOk = false;
    gatewayHealth.lastSendTarget = jid;
    gatewayHealth.lastSendError = e.message;
    return {ok:false, rawTarget, target:jid, error:e.message};
  }
}

function _jidKey(v){ return String(v || "").trim().replace(/:\d+(?=@)/, ""); }
function _targetName(x){ return String(x?.name || x?.subject || x?.pushName || x?.verifiedName || x?.id || "").trim(); }
function _mergeTargetList(oldList, newList, type){
  const m = new Map();
  for(const item of Array.isArray(oldList) ? oldList : []){
    const id = _jidKey(item?.id || item?.jid || item);
    if(id) m.set(id, { id, name:_targetName(item) || id, type:item?.type || type });
  }
  for(const item of Array.isArray(newList) ? newList : []){
    const id = _jidKey(item?.id || item?.jid || item);
    if(id) m.set(id, { id, name:_targetName(item) || id, type:item?.type || type });
  }
  return [...m.values()].sort((a,b)=>String(a.name||a.id).localeCompare(String(b.name||b.id)));
}
function _saveTargetsCache(cache){
  targetsCache = {
    contacts: Array.isArray(cache.contacts) ? cache.contacts : [],
    groups: Array.isArray(cache.groups) ? cache.groups : [],
    updatedAt: cache.updatedAt || new Date().toISOString(),
    lastSyncError: cache.lastSyncError || ""
  };
  saveJson(TARGET_CACHE_FILE, targetsCache);
  gatewayHealth.lastTargetSyncAt = targetsCache.updatedAt;
  gatewayHealth.lastTargetSyncGroups = targetsCache.groups.length;
  gatewayHealth.lastTargetSyncContacts = targetsCache.contacts.length;
  gatewayHealth.lastTargetSyncError = targetsCache.lastSyncError || "";
  return targetsCache;
}
function rememberPrivateTarget(jid, name = ""){
  const id = _jidKey(jid);
  if(!id || !id.endsWith("@s.whatsapp.net")) return targetsCache;
  const current = loadJson(TARGET_CACHE_FILE, targetsCache || {contacts:[], groups:[]});
  const contacts = _mergeTargetList(current.contacts || targetsCache.contacts || [], [{id, name:name || id, type:"contact"}], "contact");
  return _saveTargetsCache({
    contacts,
    groups: _mergeTargetList(current.groups || targetsCache.groups || [], [], "group"),
    updatedAt: new Date().toISOString(),
    lastSyncError: current.lastSyncError || ""
  });
}

async function syncTargets(options = {}){
  const previous = loadJson(TARGET_CACHE_FILE, targetsCache || { contacts: [], groups: [], updatedAt: null, lastSyncError: "" });
  const prevGroups = Array.isArray(previous.groups) ? previous.groups : [];
  const prevContacts = Array.isArray(previous.contacts) ? previous.contacts : [];
  if(!sock || !connected){
    return _saveTargetsCache({ contacts: prevContacts, groups: prevGroups, updatedAt: previous.updatedAt || new Date().toISOString(), lastSyncError: "WhatsApp not connected" });
  }

  let fetchedGroups = [];
  let syncError = "";
  try {
    const allGroups = await sock.groupFetchAllParticipating();
    fetchedGroups = Object.values(allGroups || {}).map(g => ({ id:g.id, name:g.subject || g.name || g.id, type:"group" })).filter(x => x.id);
  } catch(e) {
    syncError = "groupFetchAllParticipating: " + (e.message || String(e));
  }

  // Important: do not wipe a good saved group list when Baileys returns an empty/temporary result.
  let groups = prevGroups;
  if(fetchedGroups.length > 0 || prevGroups.length === 0 || options.clearEmpty === true){
    groups = _mergeTargetList(prevGroups, fetchedGroups, "group");
  }

  const contactCandidates = [];
  try {
    if(sock.user?.id) contactCandidates.push({ id:_jidKey(sock.user.id), name:sock.user.name || sock.user.verifiedName || "Linked WhatsApp", type:"contact" });
  } catch(e) {}
  let contacts = _mergeTargetList(prevContacts, contactCandidates, "contact");

  const out = _saveTargetsCache({ contacts, groups, updatedAt:new Date().toISOString(), lastSyncError: syncError });
  const note = syncError ? ` | ${syncError}` : "";
  console.log(`📦 Synced targets: groups ${out.groups.length} (live ${fetchedGroups.length}), private ${out.contacts.length}. Saved: ${TARGET_CACHE_FILE}${note}`);
  return out;
}

function getRecMaps(day){ return [["ank","data",MARKETS],["jodi","jodiData",BASE_MARKETS],["pannel","pannelData",MARKETS]]; }
function collectSchedules(state){
  const date = todayISO();
  const list = [];
  const profiles = state && state.profiles ? state.profiles : {};
  for(const [pid, profile] of Object.entries(profiles)){
    const day = profile?.dayRecords?.[date] || {};
    for(const [type, key, marketArr] of getRecMaps(day)){
      const dict = day[key] || {};
      for(const [idx, rec] of Object.entries(dict)){
        if(!rec || typeof rec !== "object") continue;
        const time = normalizeTime(rec.schTime || rec.scheduleTime || "");
        const targets = arr(rec.schTargets || rec.targets);
        const digits = cleanDigits(rec.d || "");
        const market = marketArr[Number(idx)]?.n || "";
        if(!time || !targets.length || !digits || !market || isDeletedMarket(state, market)) continue;
        list.push({ id:`${pid}_${date}_${type}_${idx}`, profileId:pid, date, type, index:Number(idx), time, market, digits, targets, message:formatMessage(date, market, digits) });
      }
    }
  }
  return list;
}

function collectResults(state){
  const date = todayISO();
  const targets = collectResultTargets(state);
  const records = state?.resultRecords?.[date] || {};
  const list = [];
  if(!targets.length) return list;
  for(const [market, rec] of Object.entries(records)){
    if(!rec || typeof rec !== "object" || isDeletedMarket(state, market)) continue;
    const openResult = cleanResult(rec.openResult || "");
    const closeResult = cleanResult(rec.closeResult || "");
    if(resultStage(openResult) === "open"){
      list.push({ id:`result_${date}_${market}_open`, date, market, stage:"open", result:openResult, targets, message:formatResultMessage(market, openResult) });
    }
    if(resultStage(closeResult) === "close"){
      // Auto-scraped final close is valid only after today's fresh open exists and matches its prefix.
      // This blocks yesterday/old full results that appear on pages before the fresh open result arrives.
      if(rec.source === "auto_scrape"){
        if(resultStage(openResult) !== "open") continue;
        if(!closeResult.startsWith(openResult)) continue;
      }
      list.push({ id:`result_${date}_${market}_close`, date, market, stage:"close", result:closeResult, targets, message:formatResultMessage(market, closeResult) });
    }
  }
  return list;
}


// ============================================================
// PHASE 5 + PHASE 8 — RESULT SETTLEMENT + HIT/MISS DETAIL REPORT
// Entry amount is debited at acceptance time. Settlement only credits winner payout.
// Open result settles OPEN ANK + OPEN PENEL. Close result settles JODI + CLOSE ANK + CLOSE PENEL.
// Phase 8 adds detailed HIT/MISS list for manual/optional WhatsApp send.
// ============================================================
function settlementSettings(state){
  const s = state?.settlementSettings || {};
  const pm = s.payoutMultipliers || {};
  return {
    enabled: s.enabled !== false,
    includeSummaryInResultMessage: s.includeSummaryInResultMessage !== false,
    includeHitMissInResultMessage: s.includeHitMissInResultMessage === true,
    payoutMultipliers: {
      ank: Number(pm.ank ?? 9.5),
      jodi: Number(pm.jodi ?? 9.5),
      penel: Number(pm.penel ?? 150)
    }
  };
}
function roundMoney(n){ return Math.round(Number(n || 0) * 100) / 100; }
function normalizeSettlementMarket(v){ return String(v || '').toUpperCase().replace(/SRIDEVI\s+DAY/g, 'SRIDEV DAY').replace(/[^A-Z0-9]+/g, ' ').trim().replace(/\s+/g, ' '); }
function baseFromAnyMarket(v){ return normalizeSettlementMarket(v).replace(/\s+(OPEN|CLOSE)$/i, '').trim(); }
function resultParts(result){
  const r = cleanResult(result);
  let m = r.match(/^(\d{3})-(\d)$/);
  if(m) return { stage:'open', openPenel:m[1], openAnk:m[2], jodi:'', closeAnk:'', closePenel:'' };
  m = r.match(/^(\d{3})-(\d)(\d)-(\d{3})$/);
  if(m) return { stage:'close', openPenel:m[1], openAnk:m[2], jodi:m[2]+m[3], closeAnk:m[3], closePenel:m[4] };
  return { stage:'' };
}
function entryDigitList(entry){
  if(Array.isArray(entry?.digits)) return entry.digits.map(x => String(x).trim()).filter(Boolean);
  return String(entry?.digits || '').split(/[,.\s]+/).map(x=>x.trim()).filter(Boolean);
}
function entryType(entry){
  const t = String(entry?.gameType || entry?.type || '').trim().toLowerCase();
  if(t === 'panel' || t === 'pannel') return 'penel';
  return t;
}
function isEntryEligibleForSettlement(entry, job){
  if(!entry || entry.status !== 'accepted') return false;
  if(String(entry.date || '') !== String(job.date || todayISO())) return false;
  const base = normalizeSettlementMarket(job.market);
  const em = normalizeSettlementMarket(entry.market);
  const typ = entryType(entry);
  if(job.stage === 'open'){
    if(typ !== 'ank' && typ !== 'penel') return false;
    return em === `${base} OPEN`;
  }
  if(job.stage === 'close'){
    if(typ === 'jodi') return baseFromAnyMarket(em) === base;
    if(typ === 'ank' || typ === 'penel') return em === `${base} CLOSE`;
  }
  return false;
}
function winningDigitForEntryType(job, typ){
  const parts = resultParts(job.result);
  if(job.stage === 'open'){
    if(typ === 'ank') return parts.openAnk || '';
    if(typ === 'penel') return parts.openPenel || '';
  }
  if(job.stage === 'close'){
    if(typ === 'ank') return parts.closeAnk || '';
    if(typ === 'penel') return parts.closePenel || '';
    if(typ === 'jodi') return parts.jodi || '';
  }
  return '';
}
function digitMatchesType(digit, win, typ){
  let d = String(digit || '').trim();
  let w = String(win || '').trim();
  if(typ === 'jodi'){ d = d.padStart(2,'0'); w = w.padStart(2,'0'); }
  if(typ === 'penel'){ d = d.padStart(3,'0'); w = w.padStart(3,'0'); }
  return d === w;
}
function settlementKey(job){ return `${job.market}_${job.stage}`; }
function ensureSettlementStores(state, date){
  if(!state.settlementRecords || typeof state.settlementRecords !== 'object') state.settlementRecords = {};
  if(!state.settlementRecords[date]) state.settlementRecords[date] = {};
  if(!Array.isArray(state.auditLog)) state.auditLog = [];
}
function settlementSummaryText(settlement){
  if(!settlement) return '';
  const pl = Number(settlement.marketProfit || 0);
  const plLabel = pl >= 0 ? `Profit ${money(pl)}` : `Loss ${money(Math.abs(pl))}`;
  const hitLine = (settlement.hitUsers || []).slice(0,5).map(x => `${x.name || x.userId} ${String(x.gameType||'').toUpperCase()} ${x.digit} ${money(x.payout)}`).join(' | ');
  return `\n\n📊 *SETTLEMENT SUMMARY*\n━━━━━━━━━━━━━━━━━━━━\n🧾 *Entries:* ${settlement.eligibleCount || 0} | ✅ *Hit:* ${settlement.hitCount || 0} | ❌ *Miss:* ${settlement.missCount || 0}\n💵 *Load:* ${money(settlement.totalStake || 0)}\n🏆 *Payout:* ${money(settlement.payoutTotal || 0)}\n📈 *Market:* ${plLabel}${hitLine ? `\n👑 *Hit Users:* ${hitLine}` : ''}\n━━━━━━━━━━━━━━━━━━━━`;
}
function userMentionFromId(userId){
  const digits = String(userId || '').replace(/\D/g, '');
  return digits ? '@' + digits : String(userId || 'USER');
}
function hitMissGroupLabel(type){ return String(type || '').toUpperCase(); }
function formatHitMissDetailedText(settlement, options = {}){
  if(!settlement) return '';
  const maxRows = Number(options.maxRows || 80);
  const lines = [];
  const pl = Number(settlement.marketProfit || 0);
  const plText = pl >= 0 ? `Profit ${money(pl)}` : `Loss ${money(Math.abs(pl))}`;
  lines.push('📋 *TITAN NOVA HIT/MISS LIST*');
  lines.push('━━━━━━━━━━━━━━━━━━━━');
  lines.push(`📅 *DATE:* ${settlement.date || todayISO()}`);
  lines.push(`🔥 *MARKET:* ${settlement.market || ''}`);
  lines.push(`🎯 *RESULT:* ${settlement.result || ''} (${String(settlement.stage || '').toUpperCase()})`);
  lines.push(`🧾 *Entries:* ${settlement.eligibleCount || 0} | ✅ *Hit:* ${settlement.hitCount || 0} | ❌ *Miss:* ${settlement.missCount || 0}`);
  lines.push(`💵 *Load:* ${money(settlement.totalStake || 0)} | 🏆 *Payout:* ${money(settlement.payoutTotal || 0)} | 📈 *Market:* ${plText}`);
  const hitByType = { ank:[], penel:[], jodi:[] };
  for(const x of (settlement.hitUsers || [])){
    const typ = entryType(x) || String(x.gameType || '').toLowerCase();
    if(hitByType[typ]) hitByType[typ].push(x);
  }
  const missByType = { ank:[], penel:[], jodi:[] };
  for(const x of (settlement.missUsers || [])){
    const typ = entryType(x) || String(x.gameType || '').toLowerCase();
    if(missByType[typ]) missByType[typ].push(x);
  }
  let rowCount = 0;
  const addBlock = (title, arrRows, isHit) => {
    lines.push('');
    lines.push(title);
    if(!arrRows.length){ lines.push('_None_'); return; }
    for(const x of arrRows){
      if(rowCount >= maxRows){ lines.push('...more'); break; }
      rowCount += 1;
      const user = userMentionFromId(x.userJid || x.phone || x.userId);
      const name = x.name && String(x.name) !== String(x.userId) ? ` (${x.name})` : '';
      if(isHit){
        lines.push(`${rowCount}. ${user}${name} — ${String(x.gameType||'').toUpperCase()} ${x.digit || ''} | Stake ${money(x.stake || 0)} | Payout ${money(x.payout || 0)}`);
      } else {
        const digits = x.digits || x.entryDigits || '';
        lines.push(`${rowCount}. ${user}${name} — ${String(x.gameType||'').toUpperCase()} ${digits ? '['+digits+'] ' : ''}| Stake ${money(x.stake || 0)}`);
      }
    }
  };
  for(const typ of ['ank','penel','jodi']) addBlock(`🏆 *HIT ${hitMissGroupLabel(typ)}*`, hitByType[typ], true);
  for(const typ of ['ank','penel','jodi']) addBlock(`❌ *MISS ${hitMissGroupLabel(typ)}*`, missByType[typ], false);
  lines.push('━━━━━━━━━━━━━━━━━━━━');
  return lines.join('\n');
}
function settleResultInState(state, job){
  const settings = settlementSettings(state);
  const date = job.date || todayISO();
  ensureSettlementStores(state, date);
  if(!settings.enabled) return { changed:false, skipped:true, reason:'settlement_disabled' };
  const key = settlementKey(job);
  const existing = state.settlementRecords[date][key];
  const result = cleanResult(job.result);
  if(existing && existing.result === result && existing.status === 'settled') return { changed:false, alreadySettled:true, settlement:existing };
  if(existing && existing.status === 'settled' && existing.result !== result){
    return { changed:false, skipped:true, reason:`stage_already_settled_with_${existing.result}`, settlement:existing };
  }
  const entries = Array.isArray(state.entries) ? state.entries : [];
  const eligible = entries.filter(e => isEntryEligibleForSettlement(e, job));
  const hitUsers = [];
  const missUsers = [];
  let totalStake = 0, hitStake = 0, missStake = 0, payoutTotal = 0;
  for(const entry of eligible){
    const typ = entryType(entry);
    const win = winningDigitForEntryType(job, typ);
    const digits = entryDigitList(entry);
    const parDigit = Number(entry.parDigit || 0);
    const total = Number(entry.total || (parDigit * digits.length) || 0);
    totalStake += total;
    const isHit = !!win && digits.some(d => digitMatchesType(d, win, typ));
    entry.settlementStages = Array.isArray(entry.settlementStages) ? entry.settlementStages : [];
    if(isHit){
      const payout = roundMoney(parDigit * Number(settings.payoutMultipliers[typ] || 0));
      payoutTotal += payout;
      hitStake += total;
      const wallet = ensureWalletInState(state, entry.userId);
      const before = Number(wallet.balance || 0);
      const after = roundMoney(before + payout);
      wallet.balance = after;
      wallet.updatedAt = nowIso();
      wallet.ledger = Array.isArray(wallet.ledger) ? wallet.ledger : [];
      wallet.ledger.push({
        id:`${key}_${entry.id}`, time:nowIso(), type:'winner_payout', amount:payout, balanceBefore:before, balanceAfter:after,
        note:`Winner payout ${job.market} ${job.stage.toUpperCase()} ${result}`, source:'result_settlement', entryId:entry.id, settlementKey:key, result
      });
      hitUsers.push({ entryId:entry.id, userId:entry.userId, userJid:entry.senderJid || entry.userJid || entry.phone || '', phone:entry.phone || '', name:entry.userName || entry.userId, digit:win, gameType:typ, stake:total, payout, balanceAfter:after });
      entry.settlementStages.push({ key, result, status:'hit', payout, settledAt:nowIso() });
    } else {
      missStake += total;
      missUsers.push({ entryId:entry.id, userId:entry.userId, userJid:entry.senderJid || entry.userJid || entry.phone || '', phone:entry.phone || '', name:entry.userName || entry.userId, gameType:typ, digits:digits.join(','), stake:total });
      entry.settlementStages.push({ key, result, status:'miss', payout:0, settledAt:nowIso() });
    }
  }
  const settlement = {
    id:`S${date.replace(/-/g,'')}_${key.replace(/[^A-Z0-9]/ig,'_')}`,
    date, market:job.market, stage:job.stage, result, status:'settled', settledAt:nowIso(),
    eligibleCount:eligible.length, hitCount:hitUsers.length, missCount:missUsers.length,
    totalStake:roundMoney(totalStake), hitStake:roundMoney(hitStake), missStake:roundMoney(missStake), payoutTotal:roundMoney(payoutTotal),
    marketProfit:roundMoney(totalStake - payoutTotal), hitUsers, missUsers,
    payoutMultipliers:settings.payoutMultipliers
  };
  settlement.hitMissText = formatHitMissDetailedText(settlement, { maxRows: 120 });
  state.settlementRecords[date][key] = settlement;
  state.auditLog.push({ id:settlement.id, time:nowIso(), action:'result_settlement', detail:{ market:job.market, stage:job.stage, result, eligibleCount:settlement.eligibleCount, hitCount:settlement.hitCount, payoutTotal:settlement.payoutTotal, marketProfit:settlement.marketProfit } });
  if(state.auditLog.length > 500) state.auditLog.splice(0, state.auditLog.length - 500);
  return { changed:true, settlement };
}
function findSettlementRecord(state, date, market, stage){
  const recs = state?.settlementRecords?.[date || todayISO()] || {};
  if(market && stage){
    const key = `${market}_${stage}`;
    if(recs[key]) return recs[key];
    const nkey = normalizeSettlementMarket(key);
    for(const [k,v] of Object.entries(recs)) if(normalizeSettlementMarket(k) === nkey) return v;
  }
  const list = Object.values(recs).filter(Boolean).sort((a,b)=>String(b.settledAt||'').localeCompare(String(a.settledAt||'')));
  return list[0] || null;
}

function firebaseDataUrl(){
  return FIREBASE_URL.endsWith(".json") ? FIREBASE_URL : FIREBASE_URL + "/titan_master_data.json";
}
async function fetchFirebaseState(){
  const res = await axios.get(firebaseDataUrl(), { timeout: 15000 });
  return res.data || {};
}
async function saveFirebaseState(state){
  const res = await axios.put(firebaseDataUrl(), state || {}, { timeout: 15000 });
  return res.data;
}
function mergeScrapedResultsIntoState(state, scraped){
  const date = todayISO();
  if(!state || typeof state !== "object") state = {};
  if(!state.resultRecords) state.resultRecords = {};
  if(!state.resultRecords[date]) state.resultRecords[date] = {};
  const updates = [];
  const skipped = [];
  // Fresh result lifecycle is strict and follows the live widget transition:
  // Loading/Holiday = status only, never a result.
  // Loading -> 123-4 = fresh open.
  // 123-4 -> 123-45-678 = fresh close, accepted only when the close starts with today's saved open.
  // Any full 123-45-678 seen before today's open is treated as old/yesterday data and skipped.
  const ordered = [...(scraped || [])].sort((a,b) => {
    const sa = resultStage(a.result), sb = resultStage(b.result);
    if(sa !== sb) return sa === "open" ? -1 : 1;
    // Within the same stage prefer the higher confidence block first, but keep all distinct candidates.
    const rank = (x) => (x.block === "DPBOSS LIVE RESULT" ? 5 : (x.block === "DPBOSS MAIN RESULT" ? 4 : (x.block === "LIVE MATKA RESULT" ? 3 : (x.block === "LIVE UPDATE" ? 2 : 1))));
    return rank(b) - rank(a);
  });
  for(const item of ordered){
    const stage = resultStage(item.result);
    if(!stage) continue;
    const rec = state.resultRecords[date][item.market] || { market:item.market };
    if(stage === "open"){
      const live = liveStateForMarket(item.market);
      // Open format is the first true fresh result. We prefer that Loading was seen before it,
      // but we still accept 123-4 after double confirmation to avoid missing a fresh open if Gateway started late.
      rec.market = item.market;
      rec.source = "auto_scrape";
      rec.sourceUrl = item.sourceUrl || "";
      rec.updatedAt = new Date().toISOString();
      rec.openLifecycle = live.loadingSeen ? "loading_to_open" : "open_confirmed_without_loading_seen";
      if(cleanResult(rec.openResult || "") !== item.result){
        rec.openResult = item.result;
        rec.openUpdatedAt = new Date().toISOString();
        updates.push({ market:item.market, stage, result:item.result, lifecycle:rec.openLifecycle });
      }
      state.resultRecords[date][item.market] = rec;
      rememberLiveStatus(item);
      continue;
    }

    if(stage === "close"){
      const openResult = cleanResult(rec.openResult || "");
      if(resultStage(openResult) !== "open"){
        skipped.push({ market:item.market, stage, result:item.result, reason:"fresh_open_missing" });
        continue;
      }
      if(!item.result.startsWith(openResult)){
        skipped.push({ market:item.market, stage, result:item.result, reason:`close_does_not_match_open_${openResult}` });
        continue;
      }
      rec.market = item.market;
      rec.source = "auto_scrape";
      rec.sourceUrl = item.sourceUrl || "";
      rec.updatedAt = new Date().toISOString();
      if(cleanResult(rec.closeResult || "") !== item.result){
        rec.closeResult = item.result;
        rec.closeUpdatedAt = new Date().toISOString();
        updates.push({ market:item.market, stage, result:item.result });
      }
      state.resultRecords[date][item.market] = rec;
      rememberLiveStatus(item);
    }
  }
  return { state, updates, skipped };
}
function firebaseAutoScrapeEnabled(state){
  return !(state && state.resultSettings && state.resultSettings.autoScrapeEnabled === false);
}
async function autoScrapeResultsOnce(){
  if(!RESULT_SCRAPE_ENABLED) return { status:"disabled_env", updates:[], scraped:[], confirmed:[], message:"RESULT_SCRAPE_ENABLED=0" };
  const state = await fetchFirebaseState();
  if(!firebaseAutoScrapeEnabled(state)) return { status:"disabled", updates:[], scraped:[], confirmed:[], message:"Auto scrape is OFF in admin app settings" };
  const scrape = await scrapeLiveResultPages();
  const deleted = deletedMarketsList(state);
  scrape.results = (scrape.results || []).filter(x => !deleted.includes(normalizeEntryMarketText(x.market)));
  scrape.statuses = (scrape.statuses || []).filter(x => !deleted.includes(normalizeEntryMarketText(x.market)));
  for(const st of scrape.statuses || []) rememberLiveStatus(st);
  if(!scrape.results.length) return { status:"empty", updates:[], scraped:[], statuses:scrape.statuses || [], confirmed:[], errors:scrape.errors };
  const confirmed = confirmScrapedResults(scrape.results);
  if(!confirmed.length){
    return { status:"waiting_confirmation", updates:[], scraped:scrape.results, statuses:scrape.statuses || [], confirmed:[], confirmRequired:RESULT_SCRAPE_CONFIRM_COUNT, errors:scrape.errors };
  }
  const merged = mergeScrapedResultsIntoState(state, confirmed);
  if(merged.updates.length) await saveFirebaseState(merged.state);
  return { status:"success", scraped:scrape.results, statuses:scrape.statuses || [], confirmed, updates:merged.updates, skipped:merged.skipped || [], confirmRequired:RESULT_SCRAPE_CONFIRM_COUNT, errors:scrape.errors };
}
async function resultScrapeTick(){
  if(resultScrapeTickRunning) return;
  resultScrapeTickRunning = true;
  gatewayHealth.lastResultScrapeTickAt = nowIso();
  try {
    const out = await autoScrapeResultsOnce();
    gatewayHealth.lastResultScrapeStatus = out.status || "unknown";
    gatewayHealth.lastResultScrapeUpdates = (out.updates || []).slice(-10);
    gatewayHealth.lastResultScrapeSkipped = (out.skipped || []).slice(-10);
    gatewayHealth.lastResultScrapeError = (out.errors || []).join(" ; ");
    if(out.updates && out.updates.length){
      console.log("🧲 Scraped result update:", out.updates.map(x => `${x.market} ${x.stage} ${x.result}`).join(" | "));
      // Low-latency mode: as soon as Firebase is updated from scrape, trigger WhatsApp result sending immediately.
      // This removes the old extra wait for the separate 15-second result poller.
      if(connected) await resultTick();
    }
    if(out.statuses && out.statuses.length){
      const statusLine = out.statuses.slice(0, 8).map(x => `${x.market}:${x.status}`).join(" | ");
      if(statusLine) console.log("📡 Live statuses:", statusLine);
    }
    if(out.skipped && out.skipped.length){
      console.log("🛡️ Skipped old/unmatched scrape:", out.skipped.map(x => `${x.market} ${x.result} (${x.reason})`).join(" | "));
    }
    if(out.errors && out.errors.length) console.log("Scrape fallback errors:", out.errors.join(" ; "));
  } catch(e) {
    gatewayHealth.lastResultScrapeStatus = "error";
    gatewayHealth.lastResultScrapeError = e.response ? `HTTP ${e.response.status}` : e.message;
    console.log("Result scrape error:", e.response ? `HTTP ${e.response.status}` : e.message);
  } finally {
    resultScrapeTickRunning = false;
  }
}

async function scheduleTick(){
  gatewayHealth.lastScheduleTickAt = nowIso();
  try {
    if(!connected) return;
    const state = await fetchFirebaseState();
    const schedules = collectSchedules(state);
    const hhmm = nowHHMM();
    const date = todayISO();
    for(const job of schedules){
      if(!isDueNow(job.time, hhmm)) continue;
      const key = `${job.id}_${job.time}`;
      if(sentLog[key] === date) continue;
      console.log(`⏰ HIT ${job.time}: ${job.market} -> ${job.targets.length} target(s)`);
      const results = [];
      for(const target of job.targets) results.push(await sendText(target, job.message));
      sentLog[key] = date;
      saveJson(SENT_LOG_FILE, sentLog);
      console.log(`✅ Auto sent ${job.market}:`, results.map(r => r.ok ? "OK" : "FAIL:"+r.error).join(" | "));
    }
  } catch(e) {
    gatewayHealth.lastScheduleError = e.response ? `HTTP ${e.response.status}` : e.message;
    console.log("Schedule poll error:", e.response ? `HTTP ${e.response.status}` : e.message);
    console.log("👉 Firebase direct mode hai. FIREBASE_URL check karo if repeated error.");
  }
}

async function resultTick(){
  if(resultTickRunning) return;
  resultTickRunning = true;
  gatewayHealth.lastResultTickAt = nowIso();
  try {
    if(!connected) return;
    const state = await fetchFirebaseState();
    const jobs = collectResults(state);
    const date = todayISO();
    for(const job of jobs){
      // Target-aware delivery guard: each result is sent once per WhatsApp target.
      // If targets are changed later, new group/private/Forward targets still receive the result.
      const key = job.id;
      const resultSignature = `${date}_${cleanResult(job.result)}`;
      const allTargets = targetList(job.targets);
      if(!allTargets.length){
        console.log(`⚠️ RESULT ${job.stage.toUpperCase()} skipped: no resultTargets/forward targets saved for ${job.market}`);
        continue;
      }
      const pendingTargets = allTargets.filter(t => !isResultTargetAlreadySent(key, resultSignature, t));
      if(!pendingTargets.length) continue;
      const settlementOut = settleResultInState(state, job);
      if(settlementOut.changed) await saveFirebaseState(state);
      let messageText = formatResultMessage(job.market, job.result);
      const sSettings = settlementSettings(state);
      const settlement = settlementOut.settlement;
      if(sSettings.enabled && sSettings.includeSummaryInResultMessage && settlement) messageText += settlementSummaryText(settlement);
      if(sSettings.enabled && sSettings.includeHitMissInResultMessage && settlement) messageText += "\n\n" + formatHitMissDetailedText(settlement, { maxRows: 60 });
      console.log(`🏆 RESULT ${job.stage.toUpperCase()}: ${job.market} ${job.result} -> ${pendingTargets.length}/${allTargets.length} pending target(s)${settlement ? ` | settlement hit:${settlement.hitCount} payout:${settlement.payoutTotal}` : ""}`);
      const results = [];
      for(const target of pendingTargets) results.push(await sendText(target, messageText));
      const okCount = results.filter(r => r.ok).length;
      if(okCount > 0){
        for(const r of results){ if(r.ok) markResultTargetSent(key, resultSignature, r.rawTarget || r.target || ""); }
        saveJson(SENT_LOG_FILE, sentLog);
      }
      gatewayHealth.lastResultSendAt = nowIso();
      gatewayHealth.lastResultSendSummary = `${job.market} ${job.stage} ${okCount}/${results.length}`;
      gatewayHealth.lastResultDelivery = results.slice(-20);
      if(okCount === 0 && results.length){ gatewayHealth.lastResultError = results.map(r => `${r.target||''}:${r.error||'failed'}`).join(' | '); }
      else if(okCount > 0){ gatewayHealth.lastResultError = ''; }
      console.log(`✅ Result sent ${job.market} ${job.stage}:`, results.map(r => r.ok ? "OK" : "FAIL:"+r.error).join(" | "));
    }
  } catch(e) {
    gatewayHealth.lastResultError = e.response ? `HTTP ${e.response.status}` : e.message;
    console.log("Result poll error:", e.response ? `HTTP ${e.response.status}` : e.message);
  } finally {
    resultTickRunning = false;
  }
}

function normalizeLoadGameTypes(types){
  const order = ["ANK", "PENEL", "JODI"];
  if(!types) return order.slice();
  if(!Array.isArray(types)) types = String(types).split(/[\n,]+/).map(x=>x.trim()).filter(Boolean);
  const out = [];
  for(const t of types){
    let typ = String(t || "").trim().toUpperCase();
    if(typ === "PANEL" || typ === "PANNEL") typ = "PENEL";
    if(order.includes(typ) && !out.includes(typ)) out.push(typ);
  }
  return order.filter(x => out.includes(x)).length ? order.filter(x => out.includes(x)) : order.slice();
}

function loadForwarderSettings(state){
  const lf = state?.loadForwarder || {};
  return {
    enabled: lf.enabled === true,
    scheduleTime: normalizeTime(lf.scheduleTime || "18:00") || "18:00",
    selectedMarket: normalizeEntryMarketText(lf.selectedMarket || ""),
    targets: targetList(lf.targets || []),
    gameTypes: normalizeLoadGameTypes(lf.gameTypes || ["ANK", "PENEL", "JODI"]),
    maxRowsPerType: Math.max(5, Math.min(300, Number(lf.maxRowsPerType || 80))),
    includeEmptyTypes: lf.includeEmptyTypes === true,
    lastSentKey: lf.lastSentKey || ""
  };
}
function loadEntryDigits(entry){
  const d = entry?.digits;
  if(Array.isArray(d)) return d.map(x => String(x).trim()).filter(Boolean);
  return String(d || "").replace(/[.\s]+/g, ",").split(",").map(x => x.trim()).filter(Boolean);
}
function buildLoadReport(state, date, market, maxRowsPerType, includeEmptyTypes, gameTypes){
  date = date || todayISO();
  market = normalizeEntryMarketText(market || "");
  const selectedTypes = normalizeLoadGameTypes(gameTypes || ["ANK", "PENEL", "JODI"]);
  const entries = (Array.isArray(state?.entries) ? state.entries : []).filter(e => {
    if(!e || e.status !== "accepted" || e.date !== date) return false;
    if(isDeletedMarket(state, e.market || "")) return false;
    if(market && normalizeEntryMarketText(e.market || "") !== market) return false;
    return true;
  });
  const grouped = new Map();
  let grandTotal = 0;
  let includedCount = 0;
  const typeTotals = {};
  const typeEntryCounts = {};
  for(const t of selectedTypes){ typeTotals[t] = 0; typeEntryCounts[t] = 0; }
  for(const e of entries){
    const mk = normalizeEntryMarketText(e.market || "UNKNOWN") || "UNKNOWN";
    let typ = String(e.gameType || e.type || "ANK").toUpperCase();
    if(typ === "PANEL" || typ === "PANNEL") typ = "PENEL";
    if(!["ANK","JODI","PENEL"].includes(typ)) typ = "ANK";
    if(!selectedTypes.includes(typ)) continue;
    const rate = Number(e.parDigit || e.rate || 0) || 0;
    const total = Number(e.total || 0) || 0;
    grandTotal += total;
    includedCount += 1;
    typeTotals[typ] = Math.round((Number(typeTotals[typ] || 0) + total) * 100) / 100;
    typeEntryCounts[typ] = Number(typeEntryCounts[typ] || 0) + 1;
    for(let digit of loadEntryDigits(e)){
      digit = String(digit).trim();
      if(typ === "JODI") digit = digit.padStart(2,"0");
      const key = `${mk}|${typ}|${digit}`;
      const old = grouped.get(key) || { market:mk, type:typ, digit, amount:0, entryCount:0, users:new Set() };
      old.amount += rate;
      old.entryCount += 1;
      old.users.add(String(e.userId || e.senderJid || e.userName || "user"));
      grouped.set(key, old);
    }
  }
  const markets = [...new Set([...grouped.values()].map(x => x.market).concat(market ? [market] : []))].filter(Boolean).sort();
  const out = { date, market, gameTypes:selectedTypes, entryCount:includedCount, grandTotal:Math.round(grandTotal*100)/100, typeTotals, typeEntryCounts, markets:[] };
  for(const mk of markets){
    const mObj = { market:mk, overallTotal:0, types:[] };
    for(const typ of selectedTypes){
      const items = [...grouped.values()].filter(x => x.market === mk && x.type === typ)
        .map(x => ({ digit:x.digit, amount:Math.round(x.amount*100)/100, entryCount:x.entryCount, userCount:x.users.size }))
        .sort((a,b) => (b.amount - a.amount) || String(a.digit).localeCompare(String(b.digit)))
        .slice(0, maxRowsPerType || 80);
      if(items.length || includeEmptyTypes){
        const typeTotal = Math.round(items.reduce((s,x)=>s+x.amount,0)*100)/100;
        mObj.overallTotal = Math.round((mObj.overallTotal + typeTotal)*100)/100;
        mObj.types.push({ type:typ, overallTotal:typeTotal, items });
      }
    }
    out.markets.push(mObj);
  }
  return out;
}

function formatLoadReportText(report){
  const money = (v) => `₹${Number(v || 0).toLocaleString("en-IN", {maximumFractionDigits:2})}`;
  const lines = [
    "📊 *TITAN NOVA LOAD REPORT*",
    "━━━━━━━━━━━━━━━━━━━━",
    `📅 *DATE:* ${report.date}`,
    `🔥 *MARKET:* ${report.market || "ALL MARKETS"}`,
    `🧾 *ENTRIES:* ${report.entryCount || 0}`,
    `💰 *TOTAL LOAD:* ${money(report.grandTotal || 0)}`,
    `🎮 *GAMES:* ${(report.gameTypes || ["ANK", "PENEL", "JODI"]).join(", ")}`,
    "━━━━━━━━━━━━━━━━━━━━"
  ];
  if(report.typeTotals){
    lines.push("", "*GAME TYPE TOTALS*");
    for(const gt of (report.gameTypes || ["ANK", "PENEL", "JODI"])) lines.push(`${gt}: ${money(report.typeTotals[gt] || 0)} | Entries: ${(report.typeEntryCounts || {})[gt] || 0}`);
  }
  if(!report.markets || !report.markets.length){
    lines.push("Aaj is market me accepted entry load nahi hai.");
    return lines.join("\n");
  }
  for(const mk of report.markets){
    lines.push(`\n🔥 *${mk.market}*`);
    if(!mk.types || !mk.types.length){ lines.push("No load."); continue; }
    for(const typ of mk.types){
      lines.push(`\n*${typ.type} LOAD*`);
      if(!typ.items || !typ.items.length) lines.push("No load.");
      else for(const it of typ.items) lines.push(`${it.digit} = ${money(it.amount)} | Users: ${it.userCount || 0} | Entries: ${it.entryCount || 0}`);
      lines.push(`${typ.type} Overall: ${money(typ.overallTotal || 0)}`);
    }
    lines.push(`📌 Market Overall: ${money(mk.overallTotal || 0)}`);
  }
  return lines.join("\n").trim();
}
async function sendLoadReportToTargets(targets, text){
  const results = [];
  for(const target of targetList(targets)) results.push(await sendText(target, text));
  return results;
}
async function loadForwarderTick(){
  if(loadForwarderTickRunning) return;
  loadForwarderTickRunning = true;
  gatewayHealth.lastLoadForwarderTickAt = nowIso();
  try{
    if(!connected) return;
    const state = await fetchFirebaseState();
    let changed = false;
    // 1) Dashboard send-now outbox
    const outbox = Array.isArray(state.loadForwarderOutbox) ? state.loadForwarderOutbox : [];
    for(const msg of outbox){
      if(!msg || msg.status !== "pending") continue;
      if(isDeletedMarket(state, msg.market || "")){ msg.status = "failed"; msg.lastError = "market deleted/disabled"; changed = true; continue; }
      const attempts = Number(msg.attempts || 0);
      if(attempts >= 5){ msg.status = "failed"; msg.lastError = msg.lastError || "max attempts"; changed = true; continue; }
      if(!msg.text || !arr(msg.targets).length){ msg.status = "failed"; msg.lastError = "missing text/targets"; changed = true; continue; }
      const results = await sendLoadReportToTargets(msg.targets, msg.text);
      msg.attempts = attempts + 1;
      msg.lastTriedAt = nowIso();
      msg.delivery = results;
      const okCount = results.filter(x => x.ok).length;
      if(okCount > 0){ msg.status = "sent"; msg.sentAt = nowIso(); }
      else { msg.lastError = results.map(x => x.error).filter(Boolean).join(" | ") || "send failed"; }
      changed = true;
      console.log(`📊 Load report outbox ${msg.id || ""}: ${okCount}/${results.length} sent`);
    }
    if(outbox.length > 300){ state.loadForwarderOutbox = outbox.slice(-300); changed = true; }

    // 2) Daily scheduled load report
    const lf = loadForwarderSettings(state);
    if(lf.enabled && lf.targets.length && !isDeletedMarket(state, lf.selectedMarket || "")){
      const now = nowHHMM();
      if(isDueNow(lf.scheduleTime, now)){
        const date = todayISO();
        const key = `${date}_${lf.scheduleTime}_${lf.selectedMarket || "ALL"}`;
        state.loadForwarder = state.loadForwarder || {};
        if(state.loadForwarder.lastSentKey !== key){
          const report = buildLoadReport(state, date, lf.selectedMarket, lf.maxRowsPerType, lf.includeEmptyTypes, lf.gameTypes);
          const text = formatLoadReportText(report);
          const results = await sendLoadReportToTargets(lf.targets, text);
          const okCount = results.filter(x => x.ok).length;
          state.loadForwarder.lastSentKey = key;
          state.loadForwarder.lastSentAt = nowIso();
          state.loadForwarder.lastDelivery = results;
          state.loadForwarder.lastReportSummary = { date, market:lf.selectedMarket, entryCount:report.entryCount, total:report.grandTotal, okCount, targetCount:results.length };
          changed = true;
          gatewayHealth.lastLoadForwarderSendAt = nowIso();
          console.log(`📊 Scheduled load report ${lf.selectedMarket || "ALL"}: ${okCount}/${results.length} sent`);
        }
      }
    }
    if(changed) await saveFirebaseState(state);
  }catch(e){
    gatewayHealth.lastLoadForwarderError = e.response ? `HTTP ${e.response.status}` : e.message;
    console.log("Load forwarder error:", e.response ? `HTTP ${e.response.status}` : e.message);
  }finally{
    loadForwarderTickRunning = false;
  }
}

async function paymentOutboxTick(){
  if(paymentOutboxTickRunning) return;
  paymentOutboxTickRunning = true;
  gatewayHealth.lastPaymentOutboxTickAt = nowIso();
  try {
    if(!connected) return;
    const state = await fetchFirebaseState();
    const settings = state?.paymentSettings || {};
    if(settings.notifyUserPrivate === false) return;
    const outbox = Array.isArray(state.paymentOutbox) ? state.paymentOutbox : [];
    let changed = false;
    for(const msg of outbox){
      if(!msg || msg.status !== "pending") continue;
      if(!msg.target || !msg.text){ msg.status = "failed"; msg.lastError = "missing target/text"; changed = true; continue; }
      const attempts = Number(msg.attempts || 0);
      if(attempts >= 5){ msg.status = "failed"; msg.lastError = msg.lastError || "max attempts"; changed = true; continue; }
      const out = await sendText(msg.target, msg.text);
      msg.attempts = attempts + 1;
      msg.lastTriedAt = nowIso();
      if(out.ok){
        msg.status = "sent";
        msg.sentAt = nowIso();
        msg.sentId = out.id || "sent";
      } else {
        msg.lastError = out.error || "send failed";
        if(/invalid|unresolved|not on WhatsApp/i.test(String(out.error || ""))) msg.status = "failed";
      }
      changed = true;
    }
    if(changed){
      // Keep latest queue history compact.
      if(outbox.length > 300) state.paymentOutbox = outbox.slice(-300);
      await saveFirebaseState(state);
      const pending = (state.paymentOutbox || outbox).filter(x => x.status === "pending").length;
      console.log(`💳 Payment outbox processed. pending:${pending}`);
    }
  } catch(e){
    gatewayHealth.lastPaymentOutboxError = e.response ? `HTTP ${e.response.status}` : e.message;
    console.log("Payment outbox error:", e.response ? `HTTP ${e.response.status}` : e.message);
  } finally {
    paymentOutboxTickRunning = false;
  }
}


function clearWhatsAppSessionFiles(){
  try {
    fs.rmSync(AUTH_DIR, { recursive: true, force: true });
    return { ok:true };
  } catch(e) {
    return { ok:false, error:e.message || String(e) };
  }
}

async function stopWhatsAppSocket(reason = "manual_reset"){
  try { if(sock && typeof sock.end === "function") sock.end(new Error(reason)); } catch(e) {}
  try { if(sock && sock.ws && typeof sock.ws.close === "function") sock.ws.close(); } catch(e) {}
  sock = null;
  connected = false;
}

async function restartWhatsAppFresh(reason = "manual_reset"){
  whatsappResetCount += 1;
  lastSessionResetAt = new Date().toISOString();
  gatewayHealth.lastWhatsAppEvent = reason;
  gatewayHealth.lastDisconnectCode = "";
  lastQR = "";
  lastQRAt = "";
  await stopWhatsAppSocket(reason);
  const cleared = clearWhatsAppSessionFiles();
  console.log(`🔐 WhatsApp session reset (${reason}). Auth cleared: ${cleared.ok ? "YES" : "NO"}${cleared.error ? " - " + cleared.error : ""}`);
  setTimeout(() => startWhatsApp().catch(e => console.error("WA restart error", e.message || e)), 1200);
  return cleared;
}

async function startWhatsApp(){
  if(whatsappStartInProgress) return;
  whatsappStartInProgress = true;
  try {
    if(!fs.existsSync(AUTH_DIR)) fs.mkdirSync(AUTH_DIR, { recursive:true });
  } catch(e) {}
  const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
  const { version } = await fetchLatestBaileysVersion();
  sock = makeWASocket({
    version,
    auth: state,
    printQRInTerminal: false,
    browser: Browsers.ubuntu("TitanNova"),
    logger: pino({ level: "silent" })
  });
  whatsappStartInProgress = false;
  sock.ev.on("creds.update", saveCreds);
  sock.ev.on("connection.update", async (u) => {
    const { connection, lastDisconnect, qr } = u;
    if(qr){ lastQR = qr; lastQRAt = new Date().toISOString(); gatewayHealth.lastWhatsAppEvent = "qr"; qrcode.generate(qr, {small:true}); console.log("📲 Scan QR in WhatsApp > Linked devices"); }
    if(connection === "open") { connected = true; lastQR = ""; lastQRAt = ""; gatewayHealth.lastWhatsAppEvent = "open"; console.log("WhatsApp connected"); await syncTargets(); }
    if(connection === "close") {
      connected = false;
      gatewayHealth.lastWhatsAppEvent = "close";
      const statusCode = lastDisconnect?.error?.output?.statusCode;
      gatewayHealth.lastDisconnectCode = String(statusCode || "");
      const loggedOut = statusCode === DisconnectReason.loggedOut;
      console.log("WhatsApp disconnected", statusCode || "");
      if(!loggedOut) setTimeout(() => startWhatsApp().catch(e => console.error("WA reconnect error", e.message || e)), 3000);
      else {
        console.log("Logged out. Auto-clearing auth_info_baileys and generating fresh QR...");
        await restartWhatsAppFresh("logged_out_auto_reset");
      }
    }
  });
  sock.ev.on("groups.update", () => syncTargets().catch(()=>{}));
  sock.ev.on("messages.upsert", async ({ messages }) => {
    for(const m of (messages || [])) {
      try {
        const remote = _jidKey(m?.key?.remoteJid || "");
        const participant = _jidKey(m?.key?.participant || "");
        const displayName = m?.pushName || m?.verifiedBizName || "";
        if(remote.endsWith("@s.whatsapp.net")) rememberPrivateTarget(remote, displayName || remote);
        if(participant.endsWith("@s.whatsapp.net")) rememberPrivateTarget(participant, displayName || participant);
      } catch(e) {}
      const stopped = await handleSpamGuardMessage(m);
      if(!stopped) await handleIncomingEntryMessage(m);
    }
  });
}

const app = express();
app.use(express.json({limit:"2mb"}));

app.get("/wa_login_status", (req,res)=>{
  const qrAgeSeconds = lastQRAt ? Math.floor((Date.now() - new Date(lastQRAt).getTime()) / 1000) : null;
  res.json({
    status:"success",
    connected,
    user:sock?.user || null,
    lastWhatsAppEvent:gatewayHealth.lastWhatsAppEvent || "",
    lastDisconnectCode:gatewayHealth.lastDisconnectCode || "",
    qrAvailable:!!lastQR,
    qr:lastQR,
    qrAt:lastQRAt,
    qrAgeSeconds,
    authDir:AUTH_DIR,
    resetCount:whatsappResetCount,
    lastSessionResetAt,
    note: connected ? "WhatsApp connected" : (lastQR ? "Scan QR from WhatsApp > Linked devices" : "Waiting for QR. Use reset session if QR does not appear.")
  });
});

app.post("/wa_reset_session", async (req,res)=>{
  try {
    const out = await restartWhatsAppFresh("manual_reset_api");
    res.json({status:"success", message:"WhatsApp session reset. Fresh QR will appear shortly.", cleared:out, authDir:AUTH_DIR});
  } catch(e) {
    res.status(500).json({status:"error", message:e.message || String(e)});
  }
});

app.get("/wa_qr_text", (req,res)=>{
  if(!lastQR) return res.status(404).type("text/plain").send("QR not available yet. Refresh or reset session.");
  res.type("text/plain").send(lastQR);
});

app.get("/status", async (req,res)=>{
  let adminEnabled = true;
  let counts = {};
  try {
    const st = await fetchFirebaseState();
    adminEnabled = firebaseAutoScrapeEnabled(st);
    counts = {
      resultTargets: collectResultTargets(st).length,
      paymentPending: Array.isArray(st.paymentOutbox) ? st.paymentOutbox.filter(x => x && x.status === "pending").length : 0,
      loadForwardPending: Array.isArray(st.loadForwarderOutbox) ? st.loadForwarderOutbox.filter(x => x && x.status === "pending").length : 0,
      acceptedEntriesToday: Array.isArray(st.entries) ? st.entries.filter(x => x && x.status === "accepted" && x.date === todayISO() && !isDeletedMarket(st, x.market || "")).length : 0,
      settlementsToday: st.settlementRecords?.[todayISO()] ? Object.keys(st.settlementRecords[todayISO()]).filter(m => !isDeletedMarket(st, m)).length : 0
    };
  } catch(e) {
    counts.firebaseReadError = e.response ? `HTTP ${e.response.status}` : e.message;
  }
  res.json({
    status:"success", connected, user:sock?.user || null, firebase:FIREBASE_URL, timezone:APP_TZ, now:nowHHMM(), date:todayISO(), cache:targetsCache.updatedAt,
    waLogin:{qrAvailable:!!lastQR, qrAt:lastQRAt, authDir:AUTH_DIR, resetCount:whatsappResetCount, lastSessionResetAt},
    resultScrape:{enabled:RESULT_SCRAPE_ENABLED && adminEnabled, envEnabled:RESULT_SCRAPE_ENABLED, adminEnabled, intervalMs:RESULT_SCRAPE_INTERVAL_MS, confirmCount:RESULT_SCRAPE_CONFIRM_COUNT, urls:RESULT_SCRAPE_URLS},
    paymentOutbox:true, loadForwarder:true, spamGuard:true, counts, health:gatewayHealth
  });
});
app.get("/health", async (req,res)=>{
  try {
    const state = await fetchFirebaseState();
    const lf = state.loadForwarder || {};
    const sg = state.spamGuardSettings || {};
    res.json({
      status:"success", connected, user:sock?.user || null, timezone:APP_TZ, now:nowHHMM(), date:todayISO(),
      waLogin:{qrAvailable:!!lastQR, qrAt:lastQRAt, authDir:AUTH_DIR, resetCount:whatsappResetCount, lastSessionResetAt, lastWhatsAppEvent:gatewayHealth.lastWhatsAppEvent || "", lastDisconnectCode:gatewayHealth.lastDisconnectCode || ""},
      targets:{ contacts:(targetsCache.contacts||[]).length, groups:(targetsCache.groups||[]).length, updatedAt:targetsCache.updatedAt, lastSyncError:targetsCache.lastSyncError || "" },
      scrape:{ enabled: RESULT_SCRAPE_ENABLED && firebaseAutoScrapeEnabled(state), envEnabled: RESULT_SCRAPE_ENABLED, adminEnabled: firebaseAutoScrapeEnabled(state), intervalMs:RESULT_SCRAPE_INTERVAL_MS, confirmCount:RESULT_SCRAPE_CONFIRM_COUNT, urls:RESULT_SCRAPE_URLS },
      queue:{ paymentPending:Array.isArray(state.paymentOutbox)?state.paymentOutbox.filter(x=>x&&x.status==="pending").length:0, loadForwardPending:Array.isArray(state.loadForwarderOutbox)?state.loadForwarderOutbox.filter(x=>x&&x.status==="pending"&&!isDeletedMarket(state, x.market || "")).length:0 },
      modules:{ entryParser: state.entrySettings?.entryParserEnabled !== false, settlement: state.settlementSettings?.enabled !== false, loadForwarder: lf.enabled === true, spamGuard: sg.enabled !== false },
      health: gatewayHealth
    });
  } catch(e){
    res.status(500).json({status:"error", connected, message:e.response ? `HTTP ${e.response.status}` : e.message, health:gatewayHealth});
  }
});
app.get("/targets", async (req,res)=>{
  try {
    const force = String(req.query.force || "") === "1";
    if(connected || force) await syncTargets({force});
    else targetsCache = loadJson(TARGET_CACHE_FILE, targetsCache);
    res.json({status:connected?"success":"offline", connected, ...targetsCache});
  } catch(e) {
    const cached = loadJson(TARGET_CACHE_FILE, targetsCache || {contacts:[], groups:[]});
    res.json({status:connected?"partial":"offline", connected, ...cached, lastSyncError:e.message || String(e)});
  }
});
app.get("/chats", async (req,res)=>{
  try { if(connected) await syncTargets({force:true}); } catch(e) {}
  res.json({connected, ...targetsCache});
});
app.get("/send", async (req,res)=>{ const out=await sendText(req.query.to || req.query.target, req.query.text || req.query.msg || ""); res.status(out.ok?200:400).json(out); });
app.post("/send_bulk", async (req,res)=>{ const targets=arr(req.body.targets || req.body.to); const text=req.body.text || req.body.message || ""; const results=[]; for(const t of targets) results.push(await sendText(t,text)); res.json({status:"done", total:results.length, sent:results.filter(x=>x.ok).length, results}); });
app.post("/send_category", async (req,res)=>{ const text=req.body.text || req.body.message || ""; if(connected) await syncTargets(); const category=req.body.category || "all"; let targets=[]; if(category==="groups") targets=targetsCache.groups.map(x=>x.id); else if(category==="contacts") targets=targetsCache.contacts.map(x=>x.id); else targets=[...targetsCache.contacts,...targetsCache.groups].map(x=>x.id); const results=[]; for(const t of targets) results.push(await sendText(t,text)); res.json({status:"done", total:results.length, sent:results.filter(x=>x.ok).length, results}); });
app.get("/bot_schedule", async (req,res)=>{ const state=await fetchFirebaseState(); const schedules=collectSchedules(state); res.json({status:"success", now:nowHHMM(), date:todayISO(), timezone:APP_TZ, connected, schedules}); });
app.get("/load_report", async (req,res)=>{ const state=await fetchFirebaseState(); const lf=loadForwarderSettings(state); const market=req.query.market || lf.selectedMarket; if(isDeletedMarket(state, market)) return res.status(410).json({status:"error", message:"Market deleted/disabled."}); const gameTypes=normalizeLoadGameTypes(req.query.gameTypes || lf.gameTypes); const report=buildLoadReport(state, req.query.date || todayISO(), market, Number(req.query.maxRowsPerType || lf.maxRowsPerType || 80), lf.includeEmptyTypes, gameTypes); res.json({status:"success", report, text:formatLoadReportText(report)}); });
app.post("/load_forwarder_send", async (req,res)=>{ const state=await fetchFirebaseState(); const targets=arr(req.body.targets || req.body.to); if(!targets.length) return res.status(400).json({status:"error", message:"targets required"}); const lf=loadForwarderSettings(state); const market=req.body.market || lf.selectedMarket; if(isDeletedMarket(state, market)) return res.status(410).json({status:"error", message:"Market deleted/disabled."}); const report=buildLoadReport(state, req.body.date || todayISO(), market, Number(req.body.maxRowsPerType || lf.maxRowsPerType || 80), lf.includeEmptyTypes); const text=req.body.text || formatLoadReportText(report); const results=await sendLoadReportToTargets(targets, text); res.json({status:"done", sent:results.filter(x=>x.ok).length, total:results.length, results, report}); });

app.post("/result_retry", async (req,res)=>{
  try{
    const body = req.body || {};
    const state = await fetchFirebaseState();
    const date = body.date || todayISO();
    const marketFilter = String(body.market || "").trim().toUpperCase();
    let cleared = 0;
    for(const key of Object.keys(sentLog || {})){
      if(!key.startsWith(`result_${date}_`)) continue;
      if(marketFilter && !key.toUpperCase().includes(marketFilter.replace(/\s+/g, "_"))) continue;
      delete sentLog[key];
      cleared += 1;
    }
    saveJson(SENT_LOG_FILE, sentLog);
    if(connected) setTimeout(()=>resultTick().catch(()=>{}), 200);
    res.json({status:"success", cleared, message:"Result send locks cleared. Gateway will retry pending declarations."});
  }catch(e){ res.status(500).json({status:"error", message:e.message}); }
});
app.get("/results", async (req,res)=>{ const state=await fetchFirebaseState(); const results=collectResults(state); res.json({status:"success", now:nowHHMM(), date:todayISO(), timezone:APP_TZ, connected, results}); });
app.get("/scrape_results", async (req,res)=>{ try { const out=await autoScrapeResultsOnce(); res.json({ ...out, now:nowHHMM(), date:todayISO(), timezone:APP_TZ }); } catch(e){ res.status(500).json({status:"error", message:e.response ? `HTTP ${e.response.status}` : e.message}); } });



app.get("/spam_guard_status", async (req,res)=>{
  try{
    const state = await fetchFirebaseState();
    const cfg = spamGuardSettings(state);
    const events = Array.isArray(state.spamGuardEvents) ? state.spamGuardEvents.slice(-50).reverse() : [];
    res.json({status:"success", settings:cfg, events});
  }catch(e){ res.status(500).json({status:"error", message:e.message}); }
});

app.post("/send_hitmiss", async (req,res)=>{
  try {
    const body = req.body || {};
    const state = await fetchFirebaseState();
    const date = body.date || todayISO();
    const market = body.market || "";
    const stage = body.stage || "";
    const settlement = findSettlementRecord(state, date, market, stage);
    if(!settlement) return res.status(404).json({status:"error", message:"settlement not found"});
    const text = settlement.hitMissText || formatHitMissDetailedText(settlement, { maxRows: 120 });
    const targets = targetList(body.targets || collectResultTargets(state));
    if(!targets.length) return res.status(400).json({status:"error", message:"no targets saved"});
    const results=[];
    for(const t of targets) results.push(await sendText(t, text));
    const sent = results.filter(x=>x.ok).length;
    return res.status(sent ? 200 : 400).json({status:sent?"success":"failed", sent, total:results.length, results});
  } catch(e){
    return res.status(500).json({status:"error", message:e.message});
  }
});

app.listen(PORT, () => console.log(`🚀 Titan Gateway running: http://127.0.0.1:${PORT}`));
startWhatsApp().catch(e => console.error("WA start error", e));
setInterval(scheduleTick, 15000);
setInterval(resultTick, 5000);
setInterval(resultScrapeTick, RESULT_SCRAPE_INTERVAL_MS);
setInterval(paymentOutboxTick, 10000);
setInterval(loadForwarderTick, 10000);
setTimeout(()=>resultScrapeTick().catch(()=>{}), 2000);
setTimeout(()=>paymentOutboxTick().catch(()=>{}), 5000);
setTimeout(()=>loadForwarderTick().catch(()=>{}), 7000);
setInterval(()=>syncTargets().catch(()=>{}), 10*60*1000);
