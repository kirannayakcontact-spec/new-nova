# ==========================================================
# TITAN NOVA SETUP CONTROL CENTER ADD-ON
# Existing flask_app.py is preserved. Run this file instead:
# python setup_control_center.py
# ==========================================================

import copy
import datetime
import json
import re
import traceback

import requests
from flask import jsonify, make_response, render_template_string, request

import flask_app as legacy

app = legacy.app
APP_VERSION = "setup-control-center-v1"

def _now():
    try:
        return legacy._now_iso_local()
    except Exception:
        return datetime.datetime.now().isoformat(timespec="seconds")

def _clean_key(name):
    return re.sub(r"[^A-Za-z0-9]+", "_", str(name or "").strip().upper()).strip("_") or "MARKET"

def _hhmm(value, fallback="00:00"):
    txt = str(value or "").strip()
    m = re.match(r"^(\d{1,2}):(\d{1,2})$", txt)
    if not m:
        return fallback
    h, mn = int(m.group(1)), int(m.group(2))
    if 0 <= h <= 23 and 0 <= mn <= 59:
        return f"{h:02d}:{mn:02d}"
    return fallback

def _deep_merge(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        out = copy.deepcopy(a)
        for k, v in b.items():
            out[k] = _deep_merge(out[k], v) if k in out else copy.deepcopy(v)
        return out
    return copy.deepcopy(a if b is None else b)

def _load_root():
    data = legacy.load_from_firebase()
    if isinstance(data, dict):
        return data
    try:
        data = legacy.migrate_and_get_state()
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {"profiles": {}, "settings": {}}

def _save_root(root):
    legacy.save_to_firebase(root)

def _default_markets():
    grouped = {}
    links = {}
    for item in getattr(legacy, "CHART_LINKS", []):
        links[str(item.get("n") or "").upper()] = item.get("l") or ""
    for base in getattr(legacy, "BASE_MARKETS", []):
        name = str(base.get("n") or "").strip().upper()
        if not name:
            continue
        grouped[_clean_key(name)] = {
            "name": name,
            "active": True,
            "open_time": "00:00",
            "close_time": "00:00",
            "open_url": links.get(name, ""),
            "close_url": links.get(name, ""),
        }
    for item in getattr(legacy, "MARKETS", []):
        raw = str(item.get("n") or "").strip().upper()
        phase = "close_time" if raw.endswith(" CLOSE") else "open_time"
        base = raw.replace(" OPEN", "").replace(" CLOSE", "").strip()
        key = _clean_key(base)
        grouped.setdefault(key, {"name": base, "active": True, "open_time": "00:00", "close_time": "00:00", "open_url": links.get(base, ""), "close_url": links.get(base, "")})
        grouped[key][phase] = f"{int(item.get('hr', 0)):02d}:{int(item.get('min', 0)):02d}"
    return grouped

def _default_setup(root=None):
    root = root if isinstance(root, dict) else {}
    result_settings = root.get("resultSettings", {}) if isinstance(root.get("resultSettings"), dict) else {}
    forwarder = root.get("loadForwarder", {}) if isinstance(root.get("loadForwarder"), dict) else {}
    settlement = root.get("settlementSettings", {}) if isinstance(root.get("settlementSettings"), dict) else {}
    payout = settlement.get("payoutMultipliers", {}) if isinstance(settlement.get("payoutMultipliers"), dict) else {}
    wallet = root.get("walletSettings", {}) if isinstance(root.get("walletSettings"), dict) else {}
    return {
        "system": {"app_name": "Titan Nova", "admin_token": root.get("adminToken", ""), "daily_reset_time": root.get("dailyResetTime", "06:00"), "debug_mode": False, "read_only_mode": False},
        "firebase": {"url": getattr(legacy, "FIREBASE_DB_URL", ""), "last_sync": root.get("settingsLastSync", ""), "online": False, "last_error": ""},
        "whatsapp": {"gateway_url": root.get("gatewayUrl", "http://127.0.0.1:3000"), "auto_group_sync": True, "last_message_time": ""},
        "scraping": {"auto_scrape": bool(result_settings.get("autoScrapeEnabled", True)), "auto_result_sender": bool(result_settings.get("autoResultSender", False)), "scrape_interval": int(result_settings.get("scrapeInterval", 30) or 30), "ignore_old_result": bool(result_settings.get("ignoreOldResult", True)), "two_stage_mode": bool(result_settings.get("twoStageMode", True)), "result_target_group": (root.get("resultTargets") or [""])[0] if isinstance(root.get("resultTargets"), list) and root.get("resultTargets") else ""},
        "ledger": {"auto_rate_suggest": bool(root.get("autoRateSuggest", True)), "wallet_update_enabled": bool(wallet.get("walletEnabled", True)), "daily_fresh_start": root.get("dailyFreshStart", "06:00"), "ank_payout": int(float(payout.get("ank", 9.5)) * 100), "jodi_payout": int(float(payout.get("jodi", 95)) * 100), "patti_payout": int(float(payout.get("penel", 150)) * 100), "copy_previous_day": bool(root.get("copyPreviousDay", False))},
        "forward": {"enabled": bool(forwarder.get("enabled", False)), "daily_repeat": bool(forwarder.get("dailyRepeat", True)), "default_group": ",".join(forwarder.get("targets", [])) if isinstance(forwarder.get("targets"), list) else "", "default_template": (forwarder.get("gameTypes") or ["ANK"])[0] if isinstance(forwarder.get("gameTypes"), list) and forwarder.get("gameTypes") else "ANK", "selected_market_only": True},
        "backup": {"auto_backup": bool(root.get("autoBackup", False)), "backup_time": root.get("backupTime", "23:59"), "last_backup": root.get("lastBackup", "")},
        "markets": _default_markets(),
    }

def _get_setup(root=None):
    root = root if isinstance(root, dict) else _load_root()
    saved = (((root.get("settings") or {}).get("setup")) or {}) if isinstance(root.get("settings"), dict) else {}
    setup = _deep_merge(_default_setup(root), saved)
    setup["firebase"]["url"] = getattr(legacy, "FIREBASE_DB_URL", "")
    return setup

def _apply_setup_to_root(root, setup):
    root.setdefault("settings", {})["setup"] = setup
    root["settingsLastSync"] = _now()
    root["adminToken"] = setup.get("system", {}).get("admin_token", "")
    root["dailyResetTime"] = setup.get("system", {}).get("daily_reset_time", "06:00")
    root["dailyFreshStart"] = setup.get("ledger", {}).get("daily_fresh_start", "06:00")
    root["autoRateSuggest"] = bool(setup.get("ledger", {}).get("auto_rate_suggest", True))
    root["copyPreviousDay"] = bool(setup.get("ledger", {}).get("copy_previous_day", False))
    root["gatewayUrl"] = setup.get("whatsapp", {}).get("gateway_url", "http://127.0.0.1:3000")
    root.setdefault("resultSettings", {})
    root["resultSettings"]["autoScrapeEnabled"] = bool(setup.get("scraping", {}).get("auto_scrape", False))
    root["resultSettings"]["autoResultSender"] = bool(setup.get("scraping", {}).get("auto_result_sender", False))
    root["resultSettings"]["ignoreOldResult"] = bool(setup.get("scraping", {}).get("ignore_old_result", True))
    root["resultSettings"]["twoStageMode"] = bool(setup.get("scraping", {}).get("two_stage_mode", True))
    root["resultSettings"]["scrapeInterval"] = int(setup.get("scraping", {}).get("scrape_interval", 30) or 30)
    tgt = setup.get("scraping", {}).get("result_target_group", "")
    if tgt:
        root["resultTargets"] = [tgt]
    root.setdefault("loadForwarder", {})
    root["loadForwarder"]["enabled"] = bool(setup.get("forward", {}).get("enabled", False))
    root["loadForwarder"]["dailyRepeat"] = bool(setup.get("forward", {}).get("daily_repeat", True))
    root["loadForwarder"]["targets"] = [x.strip() for x in str(setup.get("forward", {}).get("default_group", "")).replace("\n", ",").split(",") if x.strip()]
    root["loadForwarder"]["gameTypes"] = [setup.get("forward", {}).get("default_template", "ANK")]
    root.setdefault("walletSettings", {})
    root["walletSettings"]["walletEnabled"] = bool(setup.get("ledger", {}).get("wallet_update_enabled", True))
    root.setdefault("settlementSettings", {}).setdefault("payoutMultipliers", {})
    root["settlementSettings"]["payoutMultipliers"]["ank"] = float(setup.get("ledger", {}).get("ank_payout", 950) or 950) / 100
    root["settlementSettings"]["payoutMultipliers"]["jodi"] = float(setup.get("ledger", {}).get("jodi_payout", 9500) or 9500) / 100
    root["settlementSettings"]["payoutMultipliers"]["penel"] = float(setup.get("ledger", {}).get("patti_payout", 15000) or 15000) / 100
    root["autoBackup"] = bool(setup.get("backup", {}).get("auto_backup", False))
    root["backupTime"] = setup.get("backup", {}).get("backup_time", "23:59")
    return root

def _apply_setup_to_legacy(setup):
    markets_cfg = setup.get("markets", {}) if isinstance(setup.get("markets"), dict) else {}
    base_markets, markets, links = [], [], []
    for key, m in markets_cfg.items():
        if not isinstance(m, dict) or not m.get("active", True):
            continue
        name = str(m.get("name") or key.replace("_", " ")).strip().upper()
        base_markets.append({"n": name})
        links.append({"n": name, "l": m.get("open_url") or m.get("close_url") or ""})
        for phase, time_key in [("OPEN", "open_time"), ("CLOSE", "close_time")]:
            hhmm = _hhmm(m.get(time_key))
            h, mn = [int(x) for x in hhmm.split(":")]
            markets.append({"n": f"{name} {phase}", "hr": h, "min": mn})
    if base_markets and markets:
        legacy.BASE_MARKETS = base_markets
        legacy.MARKETS = markets
        legacy.CHART_LINKS = links

def _json(payload, status=200):
    res = jsonify(payload)
    res.status_code = status
    res.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return res

@app.after_request
def setup_no_cache(resp):
    if request.path.startswith("/api/setup"):
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return resp

@app.route("/setup-control")
def setup_control_page():
    return render_template_string(SETUP_HTML, version=APP_VERSION)

@app.route("/api/setup/load")
def api_setup_load():
    root = _load_root()
    setup = _get_setup(root)
    try:
        _apply_setup_to_legacy(setup)
    except Exception:
        pass
    return _json({"ok": True, "setup": setup, "version": APP_VERSION})

@app.route("/api/setup/save", methods=["POST"])
def api_setup_save():
    body = request.get_json(silent=True) or {}
    root = _load_root()
    setup = _get_setup(root)
    section = body.get("section")
    data = body.get("data", body)
    if section:
        setup[section] = _deep_merge(setup.get(section, {}), data if isinstance(data, dict) else {})
    else:
        setup = _deep_merge(setup, data if isinstance(data, dict) else {})
    setup["firebase"]["last_sync"] = _now()
    root = _apply_setup_to_root(root, setup)
    _apply_setup_to_legacy(setup)
    _save_root(root)
    return _json({"ok": True, "setup": setup, "message": "saved"})

@app.route("/api/setup/test-firebase", methods=["POST"])
def api_setup_test_firebase():
    try:
        root = _load_root()
        return _json({"ok": True, "online": True, "has_data": bool(root), "checked_at": _now()})
    except Exception as e:
        return _json({"ok": False, "online": False, "error": str(e)}, 500)

@app.route("/api/setup/status")
def api_setup_status():
    setup = _get_setup(_load_root())
    gateway_url = setup.get("whatsapp", {}).get("gateway_url", "http://127.0.0.1:3000").rstrip("/")
    gateway = {"online": False, "url": gateway_url, "error": ""}
    try:
        r = requests.get(gateway_url + "/health", timeout=3)
        gateway["online"] = r.ok
        gateway["data"] = r.json() if r.text else {}
    except Exception as e:
        gateway["error"] = str(e)
    return _json({"ok": True, "gateway": gateway, "checked_at": _now()})

@app.route("/api/setup/market/add", methods=["POST"])
def api_market_add():
    body = request.get_json(silent=True) or {}
    name = str(body.get("name") or body.get("market_name") or "").strip().upper()
    if not name:
        return _json({"ok": False, "error": "Market name required"}, 400)
    key = _clean_key(body.get("key") or name)
    root = _load_root()
    setup = _get_setup(root)
    setup.setdefault("markets", {})
    if key in setup["markets"]:
        return _json({"ok": False, "error": "Market already exists"}, 409)
    setup["markets"][key] = {"name": name, "active": bool(body.get("active", True)), "open_time": _hhmm(body.get("open_time")), "close_time": _hhmm(body.get("close_time")), "open_url": body.get("open_url") or body.get("url") or "", "close_url": body.get("close_url") or body.get("open_url") or body.get("url") or ""}
    root = _apply_setup_to_root(root, setup)
    _apply_setup_to_legacy(setup)
    _save_root(root)
    return _json({"ok": True, "key": key, "setup": setup})

@app.route("/api/setup/market/save", methods=["POST"])
def api_market_save():
    body = request.get_json(silent=True) or {}
    key = _clean_key(body.get("key") or body.get("name"))
    if not key:
        return _json({"ok": False, "error": "Market key required"}, 400)
    root = _load_root()
    setup = _get_setup(root)
    old = setup.setdefault("markets", {}).get(key, {})
    market = _deep_merge({"name": key.replace("_", " "), "active": True, "open_time": "00:00", "close_time": "00:00", "open_url": "", "close_url": ""}, old)
    for field in ["name", "active", "open_time", "close_time", "open_url", "close_url"]:
        if field in body:
            market[field] = body[field]
    market["name"] = str(market["name"]).upper()
    market["open_time"] = _hhmm(market.get("open_time"))
    market["close_time"] = _hhmm(market.get("close_time"))
    market["active"] = bool(market.get("active", True))
    setup["markets"][key] = market
    root = _apply_setup_to_root(root, setup)
    _apply_setup_to_legacy(setup)
    _save_root(root)
    return _json({"ok": True, "key": key, "setup": setup})

@app.route("/api/setup/market/delete", methods=["POST"])
def api_market_delete():
    body = request.get_json(silent=True) or {}
    if str(body.get("confirm", "")).upper() != "DELETE":
        return _json({"ok": False, "error": "Type DELETE to confirm"}, 400)
    key = _clean_key(body.get("key") or body.get("name"))
    root = _load_root()
    setup = _get_setup(root)
    setup.setdefault("markets", {}).pop(key, None)
    root = _apply_setup_to_root(root, setup)
    _apply_setup_to_legacy(setup)
    _save_root(root)
    return _json({"ok": True, "key": key, "setup": setup})

@app.route("/api/setup/backup/download", methods=["GET", "POST"])
def api_backup_download():
    root = _load_root()
    payload = {"app": "Titan Nova", "created_at": _now(), "data": root}
    res = make_response(json.dumps(payload, ensure_ascii=False, indent=2))
    res.headers["Content-Type"] = "application/json; charset=utf-8"
    res.headers["Content-Disposition"] = "attachment; filename=titan-nova-backup.json"
    return res

@app.route("/api/setup/backup/restore", methods=["POST"])
def api_backup_restore():
    body = request.get_json(silent=True) or {}
    if str(body.get("confirm", "")).upper() != "RESTORE":
        return _json({"ok": False, "error": "Type RESTORE to confirm"}, 400)
    data = body.get("data", {})
    if isinstance(data, dict) and isinstance(data.get("data"), dict):
        data = data["data"]
    if not isinstance(data, dict):
        return _json({"ok": False, "error": "Backup data must be object"}, 400)
    _save_root(data)
    return _json({"ok": True, "restored_at": _now()})

SETUP_HTML = r"""
<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Titan Nova Setup Control</title><style>body{margin:0;background:#071024;color:#eef5ff;font-family:system-ui,Arial,sans-serif}header{position:sticky;top:0;background:#0d1730;border-bottom:1px solid #26385f;padding:14px;z-index:2}main{max-width:1180px;margin:auto;padding:14px 12px 60px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.card{background:#101d3a;border:1px solid #26385f;border-radius:18px;padding:14px;box-shadow:0 14px 34px #0006}.full{grid-column:1/-1}h1,h2{margin:0 0 10px}.form{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}label{font-size:12px;color:#9fb1d1;display:block;margin:0 0 5px}input,select,textarea{width:100%;box-sizing:border-box;background:#071024;color:#eef5ff;border:1px solid #34466e;border-radius:12px;padding:10px;min-height:42px}button{border:0;border-radius:999px;padding:10px 14px;background:#79a2ff;color:#061024;font-weight:800;margin:8px 6px 0 0}.danger{background:#ff5d6c;color:white}.ghost{background:transparent;border:1px solid #34466e;color:#eef5ff}.pill{display:inline-block;padding:7px 10px;border:1px solid #34466e;border-radius:999px;margin-right:6px}.ok{color:#2ee58d}.bad{color:#ff5d6c}.market{background:#071024;border:1px solid #26385f;border-radius:14px;padding:10px;margin:10px 0}pre{white-space:pre-wrap;max-height:260px;overflow:auto;background:#071024;border:1px solid #26385f;border-radius:12px;padding:10px}@media(max-width:800px){.grid,.form{grid-template-columns:1fr}button{width:100%}}</style></head><body><header><h1 id="appTitle">Titan Nova Setup Control</h1><span class="pill" id="fb">Firebase</span><span class="pill" id="gw">Gateway</span><a class="pill" style="color:#eef5ff;text-decoration:none" href="/">Back to App</a></header><main><div class="grid"><section class="card"><h2>System</h2><div class="form"><div><label>App Name</label><input id="system.app_name"></div><div><label>Admin Token</label><input id="system.admin_token" type="password"></div><div><label>Daily Reset</label><input id="system.daily_reset_time" type="time"></div><div><label>Debug</label><select id="system.debug_mode"><option value="false">Off</option><option value="true">On</option></select></div><div><label>Read Only</label><select id="system.read_only_mode"><option value="false">Off</option><option value="true">On</option></select></div></div><button onclick="save('system')">Save System</button></section><section class="card"><h2>Firebase / Gateway</h2><div class="form"><div><label>Firebase URL</label><input id="firebase.url" readonly></div><div><label>Last Sync</label><input id="firebase.last_sync" readonly></div><div><label>Gateway URL</label><input id="whatsapp.gateway_url"></div><div><label>Auto Group Sync</label><select id="whatsapp.auto_group_sync"><option value="true">On</option><option value="false">Off</option></select></div></div><button onclick="save('whatsapp')">Save Gateway</button><button class="ghost" onclick="testFirebase()">Test Firebase</button><button class="ghost" onclick="status()">Check Status</button><pre id="statusBox"></pre></section><section class="card"><h2>Scraping / Result</h2><div class="form"><div><label>Auto Scrape</label><select id="scraping.auto_scrape"><option value="false">Off</option><option value="true">On</option></select></div><div><label>Auto Result Sender</label><select id="scraping.auto_result_sender"><option value="false">Off</option><option value="true">On</option></select></div><div><label>Ignore Old Result</label><select id="scraping.ignore_old_result"><option value="true">On</option><option value="false">Off</option></select></div><div><label>Two Stage Mode</label><select id="scraping.two_stage_mode"><option value="true">On</option><option value="false">Off</option></select></div><div><label>Interval Seconds</label><input id="scraping.scrape_interval" type="number"></div><div><label>Result Target Group</label><input id="scraping.result_target_group"></div></div><button onclick="save('scraping')">Save Scraping</button></section><section class="card"><h2>Ledger / Forward</h2><div class="form"><div><label>Auto Rate Suggest</label><select id="ledger.auto_rate_suggest"><option value="true">On</option><option value="false">Off</option></select></div><div><label>Wallet Update</label><select id="ledger.wallet_update_enabled"><option value="true">On</option><option value="false">Off</option></select></div><div><label>Fresh Start</label><input id="ledger.daily_fresh_start" type="time"></div><div><label>Ank Payout</label><input id="ledger.ank_payout" type="number"></div><div><label>Jodi Payout</label><input id="ledger.jodi_payout" type="number"></div><div><label>Patti Payout</label><input id="ledger.patti_payout" type="number"></div><div><label>Forward Enabled</label><select id="forward.enabled"><option value="false">Off</option><option value="true">On</option></select></div><div><label>Daily Repeat</label><select id="forward.daily_repeat"><option value="true">On</option><option value="false">Off</option></select></div><div><label>Default Group</label><input id="forward.default_group"></div><div><label>Template</label><select id="forward.default_template"><option>ANK</option><option>JODI</option><option>PENEL</option></select></div></div><button onclick="save('ledger')">Save Ledger</button><button onclick="save('forward')">Save Forward</button></section><section class="card full"><h2>Market Control</h2><div class="form"><div><label>New Market</label><input id="newName"></div><div><label>Open Time</label><input id="newOpen" type="time" value="00:00"></div><div><label>Close Time</label><input id="newClose" type="time" value="00:00"></div><div><label>URL</label><input id="newUrl"></div></div><button onclick="addMarket()">Add Market</button><div id="markets"></div></section><section class="card full"><h2>Backup</h2><button onclick="location.href='/api/setup/backup/download'">Download Backup</button><button class="danger" onclick="restore()">Restore Backup</button><textarea id="restoreBox" rows="4" placeholder="Paste backup JSON for restore"></textarea><pre id="raw"></pre></section></div></main><script>let setup={};const fields={system:['app_name','admin_token','daily_reset_time','debug_mode','read_only_mode'],firebase:['url','last_sync'],whatsapp:['gateway_url','auto_group_sync'],scraping:['auto_scrape','auto_result_sender','scrape_interval','ignore_old_result','two_stage_mode','result_target_group'],ledger:['auto_rate_suggest','wallet_update_enabled','daily_fresh_start','ank_payout','jodi_payout','patti_payout'],forward:['enabled','daily_repeat','default_group','default_template']};function val(el){if(el.tagName==='SELECT'&&(el.value==='true'||el.value==='false'))return el.value==='true';if(el.type==='number')return Number(el.value||0);return el.value}function setVal(id,v){let el=document.getElementById(id);if(!el)return;el.value=String(v??'')}async function api(u,o={}){let r=await fetch(u,{headers:{'Content-Type':'application/json'},cache:'no-store',...o});let d=await r.json().catch(()=>({ok:false,error:'bad json'}));if(!r.ok||d.ok===false)throw Error(d.error||'failed');return d}function fill(){document.getElementById('appTitle').textContent=(setup.system?.app_name||'Titan Nova')+' Setup Control';for(let s in fields){for(let k of fields[s])setVal(s+'.'+k,setup[s]?.[k])}renderMarkets();document.getElementById('raw').textContent=JSON.stringify(setup,null,2)}function read(s){let o={};for(let k of fields[s]||[]){let el=document.getElementById(s+'.'+k);if(el)o[k]=val(el)}return o}async function load(){let d=await api('/api/setup/load');setup=d.setup;fill()}async function save(s){let d=await api('/api/setup/save',{method:'POST',body:JSON.stringify({section:s,data:read(s)})});setup=d.setup;fill();alert(s+' saved')}async function testFirebase(){try{let d=await api('/api/setup/test-firebase',{method:'POST',body:'{}'});document.getElementById('fb').innerHTML='<b class=ok>Firebase Online</b>';document.getElementById('statusBox').textContent=JSON.stringify(d,null,2)}catch(e){document.getElementById('fb').innerHTML='<b class=bad>Firebase Error</b>';alert(e.message)}}async function status(){let d=await api('/api/setup/status');document.getElementById('gw').innerHTML=d.gateway.online?'<b class=ok>Gateway Online</b>':'<b class=bad>Gateway Offline</b>';document.getElementById('statusBox').textContent=JSON.stringify(d,null,2)}function renderMarkets(){let box=document.getElementById('markets');box.innerHTML='';Object.entries(setup.markets||{}).forEach(([key,m])=>{let div=document.createElement('div');div.className='market';div.innerHTML=`<b>${m.name||key}</b> <small>${key}</small><div class=form><div><label>Name</label><input data-k=${key} data-f=name value="${m.name||''}"></div><div><label>Active</label><select data-k=${key} data-f=active><option value=true ${m.active?'selected':''}>On</option><option value=false ${!m.active?'selected':''}>Off</option></select></div><div><label>Open</label><input type=time data-k=${key} data-f=open_time value="${m.open_time||'00:00'}"></div><div><label>Close</label><input type=time data-k=${key} data-f=close_time value="${m.close_time||'00:00'}"></div><div><label>Open URL</label><input data-k=${key} data-f=open_url value="${m.open_url||''}"></div><div><label>Close URL</label><input data-k=${key} data-f=close_url value="${m.close_url||''}"></div></div><button onclick="saveMarket('${key}')">Save Market</button><button class=danger onclick="delMarket('${key}')">Delete</button>`;box.appendChild(div)})}async function addMarket(){let name=document.getElementById('newName').value;if(!name)return alert('Market name required');let url=document.getElementById('newUrl').value;let d=await api('/api/setup/market/add',{method:'POST',body:JSON.stringify({name,open_time:newOpen.value,close_time:newClose.value,open_url:url,close_url:url})});setup=d.setup;fill()}async function saveMarket(key){let p={key};document.querySelectorAll(`[data-k="${key}"]`).forEach(el=>p[el.dataset.f]=val(el));let d=await api('/api/setup/market/save',{method:'POST',body:JSON.stringify(p)});setup=d.setup;fill();alert('Market saved')}async function delMarket(key){if(prompt('Type DELETE')!=='DELETE')return;let d=await api('/api/setup/market/delete',{method:'POST',body:JSON.stringify({key,confirm:'DELETE'})});setup=d.setup;fill()}async function restore(){let raw=restoreBox.value.trim();if(!raw)return alert('Paste JSON');if(prompt('Type RESTORE')!=='RESTORE')return;await api('/api/setup/backup/restore',{method:'POST',body:JSON.stringify({confirm:'RESTORE',data:JSON.parse(raw)})});alert('Restored');load()}load().then(status).catch(e=>alert(e.message));</script></body></html>
"""

try:
    root = _load_root()
    _apply_setup_to_legacy(_get_setup(root))
except Exception:
    traceback.print_exc()

if __name__ == "__main__":
    app.run(debug=False)
