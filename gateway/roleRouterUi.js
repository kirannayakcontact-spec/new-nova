"use strict";

// Admin UI/API for WhatsApp role targets.
// Saved controls use a dedicated Firebase namespace outside titan_master_data so
// Flask Manual Overwrite root PUTs cannot remove or roll back router settings.

const fs = require("fs");
const path = require("path");
const axios = require("axios");
const roleRouter = require("./roleRouter.js");

const FIREBASE_URL = (process.env.FIREBASE_URL || "https://titan-bbbc4-default-rtdb.firebaseio.com/titan_master_data.json").replace(/\/$/, "");
const TARGET_CACHE_FILE = path.join(process.cwd(), "whatsapp_targets_cache.json");
const ROLES = ["entry", "bookie", "schedule", "result", "forward"];
const ROLE_TO_CONFIG_KEY = {
  entry: "entryTargets",
  bookie: "bookieTargets",
  schedule: "scheduleTargets",
  result: "resultTargets",
  forward: "forwardTargets"
};

function firebaseDataUrl() {
  return FIREBASE_URL.endsWith(".json") ? FIREBASE_URL : FIREBASE_URL + "/titan_master_data.json";
}
function firebaseDatabaseRoot() {
  let url = FIREBASE_URL.split(/[?#]/)[0].replace(/\/+$/, "");
  if (url.endsWith(".json")) url = url.slice(0, -5);
  if (url.endsWith("/titan_master_data")) url = url.slice(0, -"/titan_master_data".length);
  return url.replace(/\/+$/, "");
}
function roleConfigUrl() {
  return firebaseDatabaseRoot() + "/titan_role_router/targets.json";
}
function legacyRoleConfigUrl() {
  return firebaseDataUrl().replace(/\.json(?:[?#].*)?$/, "/marketRoleTargets/KALYAN.json");
}
function loadJson(file, fallback) {
  try { return JSON.parse(fs.readFileSync(file, "utf8")); } catch { return fallback; }
}
function normalizeJid(value) {
  return roleRouter.normalizeJid ? roleRouter.normalizeJid(value) : String(value || "").trim();
}
function uniqueTargets(value) {
  const out = [];
  const add = (item) => {
    if (Array.isArray(item)) return item.forEach(add);
    const jid = normalizeJid(item && typeof item === "object" ? (item.id || item.jid || item.target) : item);
    if (jid && !out.includes(jid)) out.push(jid);
  };
  add(value);
  return out;
}
function envFallback(role) {
  return Array.isArray(roleRouter.ROLE_TARGETS && roleRouter.ROLE_TARGETS[role]) ? roleRouter.ROLE_TARGETS[role].slice() : [];
}
const ENV_FALLBACK = Object.fromEntries(ROLES.map(role => [role, envFallback(role)]));
function targetsFromConfig(config) {
  if (config && config.enabled === false) return Object.fromEntries(ROLES.map(role => [role, []]));
  return Object.fromEntries(ROLES.map(role => {
    const key = ROLE_TO_CONFIG_KEY[role];
    const saved = uniqueTargets(config && (config[key] || config[role]));
    return [role, saved.length ? saved : ENV_FALLBACK[role].slice()];
  }));
}
function applyLiveTargets(config) {
  const targets = targetsFromConfig(config || {});
  for (const role of ROLES) {
    const arr = roleRouter.ROLE_TARGETS && roleRouter.ROLE_TARGETS[role];
    if (Array.isArray(arr)) arr.splice(0, arr.length, ...targets[role]);
  }
  return targets;
}
function countsFor(targets) {
  return Object.fromEntries(ROLES.map(role => [role, (targets[role] || []).length]));
}
function configForResponse(config) {
  return {
    enabled: config.enabled !== false,
    entryTargets: uniqueTargets(config.entryTargets || config.entry),
    bookieTargets: uniqueTargets(config.bookieTargets || config.bookie),
    scheduleTargets: uniqueTargets(config.scheduleTargets || config.schedule),
    resultTargets: uniqueTargets(config.resultTargets || config.result),
    forwardTargets: uniqueTargets(config.forwardTargets || config.forward),
    updatedAt: config.updatedAt || "",
    source: config.source || ""
  };
}
function effectiveConfigForResponse(config) {
  const targets = targetsFromConfig(config || {});
  return {
    enabled: config.enabled !== false,
    entryTargets: targets.entry,
    bookieTargets: targets.bookie,
    scheduleTargets: targets.schedule,
    resultTargets: targets.result,
    forwardTargets: targets.forward
  };
}
function sanitizeConfig(body) {
  return {
    enabled: body.enabled !== false,
    entryTargets: uniqueTargets(body.entryTargets),
    bookieTargets: uniqueTargets(body.bookieTargets),
    scheduleTargets: uniqueTargets(body.scheduleTargets),
    resultTargets: uniqueTargets(body.resultTargets),
    forwardTargets: uniqueTargets(body.forwardTargets),
    updatedAt: new Date().toISOString(),
    source: "gateway_role_router_ui"
  };
}
function hasSavedTargets(config) {
  if (!config || typeof config !== "object") return false;
  return config.enabled === false || ROLES.some(role => uniqueTargets(config[ROLE_TO_CONFIG_KEY[role]] || config[role]).length > 0);
}
async function readRoleConfig() {
  const res = await axios.get(roleConfigUrl(), { timeout: 8000 });
  let config = res.data && typeof res.data === "object" ? res.data : {};
  if (hasSavedTargets(config)) return config;

  // One-time compatibility read for PR #19's old in-root location.
  try {
    const legacy = await axios.get(legacyRoleConfigUrl(), { timeout: 6000 });
    if (hasSavedTargets(legacy.data)) {
      config = { ...legacy.data, migratedAt: new Date().toISOString(), source: "legacy_marketRoleTargets_migration" };
      await axios.put(roleConfigUrl(), config, { timeout: 8000 });
    }
  } catch (error) {}
  return config;
}
async function saveRoleConfig(config) {
  const res = await axios.put(roleConfigUrl(), config || {}, { timeout: 10000 });
  applyLiveTargets(config || {});
  return res.data;
}
async function refreshLiveTargets() {
  try {
    const config = await readRoleConfig();
    const targets = applyLiveTargets(config);
    console.log("[roleRouterUi] UI role targets loaded:", countsFor(targets));
    return { config, targets };
  } catch (error) {
    console.warn("[roleRouterUi] Role target load failed; using .env fallback:", error.message || error);
    const targets = applyLiveTargets({});
    return { config: {}, targets };
  }
}
function roleRouterPage() {
  return `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Titan Role Routing</title><style>
  :root{--bg:#17212B;--card:#232E3C;--light:#2B3A4D;--line:#374F65;--primary:#2AABEE;--green:#00C26F;--rose:#FF5D5D;--amber:#FAC748;--muted:#7A9CB8}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:white;font-family:Inter,Arial,sans-serif;padding:14px 12px 90px}.top{position:sticky;top:0;background:var(--bg);padding:4px 0 10px;z-index:1}.card{background:var(--card);border:1px solid rgba(255,255,255,.08);border-radius:16px;padding:14px;margin:0 0 12px}.muted{color:var(--muted);font-size:11px;line-height:1.45}.lbl{font-size:10px;color:var(--muted);text-transform:uppercase;font-weight:900;margin:0 0 6px}textarea,input{width:100%;background:var(--light);color:#fff;border:1.5px solid var(--line);border-radius:12px;padding:12px;font-weight:800;font-size:13px;outline:none}textarea{min-height:58px;text-align:left}button{border:0;border-radius:13px;padding:13px 14px;font-weight:900;text-transform:uppercase;color:#fff;background:var(--primary);width:100%;min-height:44px}.row{display:flex;gap:8px;align-items:center;justify-content:space-between}.pill{display:inline-block;background:rgba(42,171,238,.15);color:var(--primary);border:1px solid rgba(42,171,238,.25);padding:5px 8px;border-radius:999px;font-size:10px;font-weight:900;margin:3px 3px 0 0}.danger{background:var(--rose)}.ok{background:var(--green)}.secondary{background:var(--line)}.pick{width:auto;min-height:34px;padding:7px 9px;font-size:9px;margin:5px 4px 0 0;background:rgba(42,171,238,.18);color:var(--primary);border:1px solid rgba(42,171,238,.3)}</style></head><body>
  <div class="top"><h2 style="margin:0;font-size:18px;font-weight:1000">TITAN NOVA ROLE ROUTER</h2><div class="muted">Global WhatsApp role-group control for every market</div></div>
  <div class="card"><div class="row"><div><b>Status</b><div id="status" class="muted">Loading...</div></div><span id="enabled-pill" class="pill">...</span></div></div>
  <div class="card"><label style="font-weight:900"><input id="enabled" type="checkbox" style="width:auto;margin-right:8px"> Enable Role Router</label><p class="muted">OFF karne par role targets empty honge aur Gateway ka normal target behaviour chalega.</p></div>
  ${[
    ["entryTargets","Entry Target 🎮","KALYAN_ADMIN_GROUP: sabhi valid VIP market entries yahin se accept hongi"],
    ["bookieTargets","Bookie Target 🛡️","KALYAN_ADMIN_GROUP: withdrawal, payment aur admin alerts"],
    ["scheduleTargets","Schedule Target 📅","KALYAN_INTEL_GROUP: sabhi markets ka Daily Intel only"],
    ["resultTargets","Result Target 🏆","KALYAN_RESULT_GROUP: sabhi markets ke Open/Close results only"],
    ["forwardTargets","Forward Target 📊","BOOKIE_LOAD_REPORT_GROUP: evening Load Report only"]
  ].map(([id,title,help]) => `<div class="card"><p class="lbl">${title}</p><textarea id="${id}" placeholder="120363xxxxxxxx@g.us"></textarea><p class="muted">${help}. Multiple JIDs comma/new-line se add kar sakte hain.</p></div>`).join("")}
  <div class="card"><button onclick="save()">Save & Apply Role Targets</button><button class="danger" style="margin-top:8px" onclick="resetEnv()">Clear UI Targets / Use .env</button><button class="secondary" style="margin-top:8px" onclick="load()">Refresh</button></div>
  <div class="card"><p class="lbl">WhatsApp Groups Detected</p><div id="groups" class="muted">Gateway group cache loading...</div></div>
<script>
const fields=['entryTargets','bookieTargets','scheduleTargets','resultTargets','forwardTargets'];
function esc(v){return String(v||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function val(id){return document.getElementById(id).value.split(/[\\n,]+/).map(x=>x.trim()).filter(Boolean)}
function setVal(id,v){document.getElementById(id).value=(v||[]).join('\\n')}
function pick(id,field){const values=val(field);if(!values.includes(id))values.push(id);setVal(field,values)}
async function load(){const r=await fetch('/api/role_router');const d=await r.json();if(d.status!=='success'){document.getElementById('status').textContent=d.message||'Load failed';return}const c=d.effectiveConfig||d.config||{};document.getElementById('enabled').checked=c.enabled!==false;fields.forEach(k=>setVal(k,c[k]||[]));document.getElementById('status').textContent='Live counts: '+JSON.stringify(d.runtimeCounts||{})+(d.config&&d.config.updatedAt?' • Saved '+d.config.updatedAt:' • .env/default source');document.getElementById('enabled-pill').textContent=(c.enabled!==false?'ON':'OFF');document.getElementById('enabled-pill').className='pill '+(c.enabled!==false?'ok':'danger');document.getElementById('groups').innerHTML=(d.groups||[]).map(g=>'<div style="padding:9px 0;border-bottom:1px solid rgba(255,255,255,.06)"><b>'+esc(g.name||g.id)+'</b><div class="muted">'+esc(g.id)+'</div>'+fields.map(f=>'<button class="pick" onclick="pick(\''+String(g.id).replace(/'/g,"\\'")+'\',\''+f+'\')">'+f.replace('Targets','')+'</button>').join('')+'</div>').join('')||'No cached groups yet. WhatsApp connect karke Refresh karein.'}
async function save(){const body={enabled:document.getElementById('enabled').checked,entryTargets:val('entryTargets'),bookieTargets:val('bookieTargets'),scheduleTargets:val('scheduleTargets'),resultTargets:val('resultTargets'),forwardTargets:val('forwardTargets')};const r=await fetch('/api/role_router',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const d=await r.json();if(d.status!=='success') return alert(d.message||'Save failed');alert('✅ Role targets saved aur live apply ho gaye');load()}
async function resetEnv(){if(!confirm('Saved UI targets clear karke .env fallback use karna hai?'))return;const r=await fetch('/api/role_router',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({clear:true})});const d=await r.json();if(d.status!=='success') return alert(d.message||'Clear failed');alert('✅ Cleared. .env fallback active.');load()}
load();
</script></body></html>`;
}
function patchExpress() {
  let express;
  try { express = require("express"); } catch (error) { console.error("[roleRouterUi] express preload failed:", error.message || error); return; }
  if (express.__titanRoleRouterUiPatched) return;
  const originalExpress = express;
  const wrapped = function roleRouterUiExpress(...args) {
    const app = originalExpress(...args);
    if (app && typeof app.get === "function" && typeof app.post === "function" && !app.__titanRoleRouterUiInstalled) {
      app.get("/role_router", (req, res) => res.type("html").send(roleRouterPage()));
      app.get("/api/role_router", async (req, res) => {
        try {
          const config = await readRoleConfig();
          const targets = applyLiveTargets(config);
          const groups = loadJson(TARGET_CACHE_FILE, { groups: [] }).groups || [];
          res.json({ status: "success", config: configForResponse(config), effectiveConfig: effectiveConfigForResponse(config), envFallback: ENV_FALLBACK, runtimeCounts: countsFor(targets), groups });
        } catch (error) { res.status(500).json({ status: "error", message: error.message || String(error), config: {}, groups: [] }); }
      });
      // Route-local parser is required because these routes are installed before
      // Gateway.js calls app.use(express.json()). Without it req.body is empty.
      app.post("/api/role_router", originalExpress.json({ limit: "256kb" }), async (req, res) => {
        try {
          const body = req.body || {};
          const config = body.clear ? { enabled: true, updatedAt: new Date().toISOString(), source: "gateway_role_router_ui_clear" } : sanitizeConfig(body);
          await saveRoleConfig(config);
          res.json({ status: "success", config: configForResponse(config), effectiveConfig: effectiveConfigForResponse(config), runtimeCounts: countsFor(targetsFromConfig(config)) });
        } catch (error) { res.status(500).json({ status: "error", message: error.message || String(error) }); }
      });
      Object.defineProperty(app, "__titanRoleRouterUiInstalled", { value: true, enumerable: false });
    }
    return app;
  };
  Object.setPrototypeOf(wrapped, originalExpress);
  Object.assign(wrapped, originalExpress);
  require.cache[require.resolve("express")].exports = wrapped;
  Object.defineProperty(wrapped, "__titanRoleRouterUiPatched", { value: true, enumerable: false });
}

patchExpress();
refreshLiveTargets();

module.exports = { applyLiveTargets, refreshLiveTargets, targetsFromConfig, sanitizeConfig, roleConfigUrl };
