# ==========================================================
# TWO FILE EDITION
# Python deps: pip install flask requests
# Run UI/API: python flask_app.py
# Node Gateway is controlled over localhost endpoints from this file.
# ==========================================================

# ==========================================================
# FIREBASE ONLY STORAGE EDITION
# Local JSON storage removed
# ==========================================================

from flask import Flask, render_template_string, request, jsonify
import json
import os
import uuid
import datetime
import io
import csv
import zipfile
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None
import requests

app = Flask(__name__)

# ==========================================================
# ANDRES BARLIN SYSTEM MANIFEST - NATIVE PUSH SYSTEM (V10.9)
# ==========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_TZ = os.environ.get("APP_TZ", "Asia/Kolkata")

# 👇 FIREBASE REALTIME DATABASE URL 👇
FIREBASE_DB_URL = "https://titan-bbbc4-default-rtdb.firebaseio.com/"

def get_firebase_url():
    url = FIREBASE_DB_URL.strip().rstrip('/')
    if not url.endswith('.json'):
        url += '/titan_master_data.json'
    return url

def load_from_firebase():
    try:
        res = requests.get(get_firebase_url(), timeout=10)
        if res.status_code == 200 and res.json():
            return res.json()
    except Exception as e:
        print("Firebase Load Error:", e)
    return None

def save_to_firebase(data):
    try:
        requests.put(get_firebase_url(), json=data, timeout=10)
    except Exception as e:
        print("Firebase Save Error:", e)

MARKETS = [
    {"n": "SRIDEV DAY OPEN", "hr": 11, "min": 35}, {"n": "SRIDEV DAY CLOSE", "hr": 12, "min": 35},
    {"n": "TIME BAZAR OPEN", "hr": 13, "min": 0}, {"n": "MADHUR DAY OPEN", "hr": 13, "min": 15},
    {"n": "TIME BAZAR CLOSE", "hr": 14, "min": 0}, {"n": "MADHUR DAY CLOSE", "hr": 14, "min": 15},
    {"n": "MILAN DAY OPEN", "hr": 15, "min": 0}, {"n": "RAJDHANI DAY OPEN", "hr": 15, "min": 5},
    {"n": "SUPREME DAY OPEN", "hr": 15, "min": 35}, {"n": "KALYAN OPEN", "hr": 15, "min": 50},
    {"n": "MILAN DAY CLOSE", "hr": 17, "min": 0}, {"n": "RAJDHANI DAY CLOSE", "hr": 17, "min": 5},
    {"n": "SUPREME DAY CLOSE", "hr": 17, "min": 35}, {"n": "KALYAN CLOSE", "hr": 17, "min": 50},
    {"n": "SRIDEVI NIGHT OPEN", "hr": 19, "min": 0}, {"n": "SRIDEVI NIGHT CLOSE", "hr": 20, "min": 0},
    {"n": "MADHUR NIGHT OPEN", "hr": 20, "min": 30}, {"n": "SUPREME NIGHT OPEN", "hr": 20, "min": 45},
    {"n": "MILAN NIGHT OPEN", "hr": 21, "min": 0}, {"n": "KALYAN NIGHT OPEN", "hr": 21, "min": 25},
    {"n": "RAJDHANI NIGHT OPEN", "hr": 21, "min": 35}, {"n": "MAIN BAZAR OPEN", "hr": 21, "min": 40},
    {"n": "MADHUR NIGHT CLOSE", "hr": 22, "min": 30}, {"n": "SUPREME NIGHT CLOSE", "hr": 22, "min": 45},
    {"n": "MILAN NIGHT CLOSE", "hr": 23, "min": 0}, {"n": "KALYAN NIGHT CLOSE", "hr": 23, "min": 35},
    {"n": "RAJDHANI NIGHT CLOSE", "hr": 23, "min": 45}, {"n": "MAIN BAZAR CLOSE", "hr": 0, "min": 5}
]

BASE_MARKETS = [
    {"n": "SRIDEV DAY"}, {"n": "TIME BAZAR"}, {"n": "MADHUR DAY"}, {"n": "MILAN DAY"},
    {"n": "RAJDHANI DAY"}, {"n": "SUPREME DAY"}, {"n": "KALYAN"}, {"n": "SRIDEVI NIGHT"},
    {"n": "MADHUR NIGHT"}, {"n": "SUPREME NIGHT"}, {"n": "MILAN NIGHT"}, {"n": "KALYAN NIGHT"},
    {"n": "RAJDHANI NIGHT"}, {"n": "MAIN BAZAR"}
]

CHART_LINKS = [
    {"n": "SRIDEV DAY", "l": "https://sattamatkadpboss.co/record/sridevi-satta-penal-chart.php"},
    {"n": "TIME BAZAR", "l": "https://sattamatkadpboss.co/time-bazar-panel-chart.php"},
    {"n": "MADHUR DAY", "l": "https://sattamatkadpboss.co/madhur-day-panel-chart.php"},
    {"n": "MILAN DAY", "l": "https://sattamatkadpboss.co/record/milan-day-penal-chart.php"},
    {"n": "RAJDHANI DAY", "l": "https://sattamatkadpboss.co/record/rajdhani-day-penal-chart.php"},
    {"n": "SUPREME DAY", "l": "https://sattamatkadpboss.co/supreme-day-panel-chart.php"},
    {"n": "KALYAN", "l": "https://sattamatkadpboss.co/record/kalyan-penal-chart.php"},
    {"n": "SRIDEVI NIGHT", "l": "https://sattamatkadpboss.mobi/record/sridevi-night-satta-penal-chart.php"},
    {"n": "MADHUR NIGHT", "l": "https://sattamatkadpboss.co/madhur-night-panel-chart.php"},
    {"n": "SUPREME NIGHT", "l": "https://sattamatkadpboss.co/supreme-night-panel-chart.php"},
    {"n": "MILAN NIGHT", "l": "https://sattamatkadpboss.co/record/milan-night-penal-chart.php"},
    {"n": "KALYAN NIGHT", "l": "https://sattamatkadpboss.co/record/kalyan-night-penal-chart.php"},
    {"n": "RAJDHANI NIGHT", "l": "https://sattamatkadpboss.co/record/rajdhani-night-penal-chart.php"},
    {"n": "MAIN BAZAR", "l": "https://sattamatkadpboss.mobi/main-bazar-panel-chart.php"}
]

def get_default_config():
    return {"ankSplit": True, "panSplit": True, "capital": 0, "dayTarget": 0, "ank": {"cap": 0, "tgt": 0}, "jodi": {"cap": 0, "tgt": 0}, "pannel": {"cap": 0, "tgt": 0}}

def _now_iso_local():
    if ZoneInfo:
        try:
            return datetime.datetime.now(ZoneInfo(APP_TZ)).isoformat(timespec="seconds")
        except Exception:
            pass
    return datetime.datetime.now().isoformat(timespec="seconds")

def _default_wallet_settings():
    return {
        "defaultCreditLimit": 0,
        "requirePositiveBalance": False,
        "currency": "₹",
        "walletEnabled": True
    }

def _default_risk_settings():
    return {
        "marketDailyLimit": 0,
        "digitDailyLimit": 0,
        "userDailyLimit": 0,
        "warningPercent": 80,
        "autoLockOnLimit": False
    }

def _default_settlement_settings():
    return {
        "enabled": True,
        "includeSummaryInResultMessage": True,
        "includeHitMissInResultMessage": False,
        "payoutMultipliers": {"ank": 9.5, "jodi": 9.5, "penel": 150}
    }

def _default_payment_settings():
    return {
        "paymentAutomationEnabled": True,
        "requireUtr": True,
        "duplicateUtrBlock": True,
        "approveCreditsWallet": True,
        "extendMembershipOnApprove": True,
        "minAmount": 1,
        "maxAmount": 200000,
        "notifyUserPrivate": True
    }

def _default_load_forwarder_settings():
    return {
        "enabled": False,
        "scheduleTime": "18:00",
        "selectedMarket": "",
        "targets": [],
        "gameTypes": ["ANK", "PENEL", "JODI"],
        "maxRowsPerType": 80,
        "includeEmptyTypes": False,
        "lastSentKey": "",
        "lastSentAt": "",
        "lastDelivery": []
    }

def _default_spam_guard_settings():
    return {
        "enabled": True,
        "groupsOnly": True,
        "linkGuardEnabled": True,
        "forwardGuardEnabled": True,
        "deleteMessage": True,
        "kickEnabled": True,
        "exemptAdmins": True,
        "linkStrikeLimit": 3,
        "forwardStrikeLimit": 3,
        "forwardWindowSeconds": 60,
        "alertMessage": "⚠️ *ALERT*\nBhai Group Me Link Dalna Mana he",
        "warningMessage": "⚠️ *WARNING*\nNext Time Group Me Link Daloge To Remove Kiya Jayega Group Se",
        "kickMessage": "🚫 *REMOVED*\n@{number} ko group se remove kiya gaya.\nReason: 3 baar link/forward spam.",
        "forwardAlertMessage": "⚠️ *ALERT*\nBhai Group Me Forward/Spam Message Dalna Mana he",
        "forwardWarningMessage": "⚠️ *WARNING*\nNext Time Multiple Forward Message Daloge To Remove Kiya Jayega Group Se"
    }

def _normalize_forward_targets(targets):
    if isinstance(targets, str):
        targets = [x.strip() for x in targets.replace('\n', ',').split(',') if x.strip()]
    if not isinstance(targets, list):
        return []
    out = []
    for t in targets:
        txt = str(t or '').strip()
        if txt and txt not in out:
            out.append(txt)
    return out

def _normalize_game_types(types):
    order = ['ANK', 'PENEL', 'JODI']
    if isinstance(types, str):
        types = [x.strip() for x in types.replace('\n', ',').split(',') if x.strip()]
    if not isinstance(types, list):
        types = order[:]
    out = []
    for t in types:
        typ = str(t or '').strip().upper()
        if typ in ('PANEL', 'PANNEL'):
            typ = 'PENEL'
        if typ in order and typ not in out:
            out.append(typ)
    return [t for t in order if t in out] or order[:]

def _entry_digits_list(entry):
    d = entry.get('digits', []) if isinstance(entry, dict) else []
    if isinstance(d, list):
        return [str(x).strip() for x in d if str(x).strip()]
    return [x.strip() for x in str(d or '').replace('.', ',').replace(' ', ',').split(',') if x.strip()]

def _build_load_report(state_obj, date=None, market=None, max_rows=80, include_empty=False, game_types=None):
    date = date or _safe_today()
    market = ' '.join(str(market or '').strip().upper().split())
    selected_types = _normalize_game_types(game_types)
    entries = state_obj.get('entries', []) if isinstance(state_obj.get('entries', []), list) else []
    rows = [e for e in entries if isinstance(e, dict) and e.get('status') == 'accepted' and e.get('date') == date]
    if market:
        rows = [e for e in rows if ' '.join(str(e.get('market') or '').upper().split()) == market]
    grouped = {}
    user_sets = {}
    entry_counts = {}
    type_totals = {t: 0.0 for t in selected_types}
    type_entry_counts = {t: 0 for t in selected_types}
    grand_total = 0.0
    included_rows = 0
    for e in rows:
        m = ' '.join(str(e.get('market') or 'UNKNOWN').upper().split())
        typ = str(e.get('gameType') or e.get('type') or 'ANK').upper()
        if typ in ('PANEL', 'PANNEL'):
            typ = 'PENEL'
        if typ not in ['ANK', 'JODI', 'PENEL']:
            typ = 'ANK'
        if typ not in selected_types:
            continue
        rate = _wallet_float(e.get('parDigit', e.get('rate', 0)))
        total = _wallet_float(e.get('total', 0))
        grand_total += total
        type_totals[typ] = round(type_totals.get(typ, 0) + total, 2)
        type_entry_counts[typ] = type_entry_counts.get(typ, 0) + 1
        included_rows += 1
        for d in _entry_digits_list(e):
            digit = str(d).strip()
            if typ == 'JODI':
                digit = digit.zfill(2)
            key = (m, typ, digit)
            grouped[key] = round(grouped.get(key, 0) + rate, 2)
            entry_counts[key] = entry_counts.get(key, 0) + 1
            user_sets.setdefault(key, set()).add(str(e.get('userId') or e.get('senderJid') or e.get('userName') or 'user'))
    markets_found = sorted(set([k[0] for k in grouped.keys()] + ([market] if market else [])))
    report = {
        'date': date,
        'market': market,
        'gameTypes': selected_types,
        'entryCount': included_rows,
        'grandTotal': round(grand_total, 2),
        'typeTotals': {t: round(type_totals.get(t, 0), 2) for t in selected_types},
        'typeEntryCounts': {t: int(type_entry_counts.get(t, 0)) for t in selected_types},
        'markets': []
    }
    for m in markets_found:
        market_obj = {'market': m, 'overallTotal': 0, 'types': []}
        for typ in selected_types:
            items = []
            for (mk, gt, digit), amount in grouped.items():
                if mk == m and gt == typ:
                    items.append({
                        'digit': digit,
                        'amount': round(amount, 2),
                        'entryCount': entry_counts.get((mk, gt, digit), 0),
                        'userCount': len(user_sets.get((mk, gt, digit), set()))
                    })
            items.sort(key=lambda x: (-x['amount'], x['digit']))
            if items or include_empty:
                type_total = round(sum(x['amount'] for x in items), 2)
                market_obj['overallTotal'] = round(market_obj['overallTotal'] + type_total, 2)
                market_obj['types'].append({'type': typ, 'overallTotal': type_total, 'items': items[:max(1, int(max_rows or 80))]})
        report['markets'].append(market_obj)
    return report

def _format_load_report_text(report):
    def money(v):
        try:
            n = float(v or 0)
        except Exception:
            n = 0
        return f"₹{n:g}"
    date = report.get('date') or ''
    market = report.get('market') or 'ALL MARKETS'
    lines = [
        '📊 *TITAN NOVA LOAD REPORT*',
        '━━━━━━━━━━━━━━━━━━━━',
        f'📅 *DATE:* {date}',
        f'🔥 *MARKET:* {market}',
        f'🧾 *ENTRIES:* {report.get("entryCount", 0)}',
        f'💰 *TOTAL LOAD:* {money(report.get("grandTotal", 0))}',
        f'🎮 *GAMES:* {", ".join(report.get("gameTypes") or ["ANK", "PENEL", "JODI"])}',
        '━━━━━━━━━━━━━━━━━━━━'
    ]
    type_totals = report.get('typeTotals') or {}
    type_counts = report.get('typeEntryCounts') or {}
    if type_totals:
        lines.append('')
        lines.append('*GAME TYPE TOTALS*')
        for gt in (report.get('gameTypes') or ['ANK', 'PENEL', 'JODI']):
            lines.append(f'{gt}: {money(type_totals.get(gt, 0))} | Entries: {type_counts.get(gt, 0)}')
    if not report.get('markets'):
        lines.append('Aaj is market me accepted entry load nahi hai.')
        return '\n'.join(lines)
    for mk in report.get('markets', []):
        lines.append(f'\n🔥 *{mk.get("market", "MARKET")}*')
        if not mk.get('types'):
            lines.append('No load.')
            continue
        for typ in mk.get('types', []):
            lines.append(f'\n*{typ.get("type")} LOAD*')
            items = typ.get('items') or []
            if not items:
                lines.append('No load.')
            else:
                for it in items:
                    lines.append(f'{it.get("digit")} = {money(it.get("amount"))} | Users: {it.get("userCount",0)} | Entries: {it.get("entryCount",0)}')
            lines.append(f'{typ.get("type")} Overall: {money(typ.get("overallTotal",0))}')
        lines.append(f'📌 Market Overall: {money(mk.get("overallTotal",0))}')
    return '\n'.join(lines).strip()

def _payment_float(v):
    try:
        return round(float(v or 0), 2)
    except Exception:
        return 0.0

def _normalize_utr(v):
    return ''.join(ch for ch in str(v or '').upper().strip() if ch.isalnum())

def _phone_target_from_profile(profile):
    raw = str((profile or {}).get('phone') or '').strip()
    digits = ''.join(ch for ch in raw if ch.isdigit())
    if not digits:
        return ''
    if len(digits) == 10:
        digits = '91' + digits
    return digits

def _queue_payment_message(state_obj, user_id, text, meta=None):
    settings = state_obj.get('paymentSettings', _default_payment_settings()) if isinstance(state_obj, dict) else _default_payment_settings()
    if not settings.get('notifyUserPrivate', True):
        return None
    profile = (state_obj.get('profiles', {}) or {}).get(user_id, {}) if isinstance(state_obj, dict) else {}
    target = _phone_target_from_profile(profile)
    if not target or not text:
        return None
    msg = {
        'id': str(uuid.uuid4())[:8].upper(),
        'time': _now_iso_local(),
        'target': target,
        'text': str(text),
        'status': 'pending',
        'attempts': 0,
        'meta': meta or {}
    }
    state_obj.setdefault('paymentOutbox', []).append(msg)
    # Keep queue compact. Sent/failed history is useful but should not grow forever.
    if len(state_obj.get('paymentOutbox', [])) > 300:
        state_obj['paymentOutbox'] = state_obj['paymentOutbox'][-300:]
    return msg

def _payment_risk_flag(state_obj, user_id, amount, utr):
    settings = state_obj.get('paymentSettings', _default_payment_settings())
    utr_norm = _normalize_utr(utr)
    if amount < _payment_float(settings.get('minAmount', 1)):
        return 'low_amount'
    if amount > _payment_float(settings.get('maxAmount', 200000)):
        return 'high_amount'
    if settings.get('requireUtr', True) and not utr_norm:
        return 'utr_missing'
    for pmt in state_obj.get('payments', []):
        if _normalize_utr(pmt.get('utr')) and _normalize_utr(pmt.get('utr')) == utr_norm and str(pmt.get('status', '')).lower() != 'rejected':
            return 'duplicate'
    pending_same_user = [pmt for pmt in state_obj.get('payments', []) if pmt.get('userId') == user_id and pmt.get('status') == 'pending']
    if len(pending_same_user) >= 3:
        return 'spam'
    return 'safe'

def _credit_wallet_from_payment(state_obj, payment, note=None):
    user_id = payment.get('userId')
    amount = _payment_float(payment.get('amount', 0))
    if not user_id or amount <= 0:
        return None
    wallet = _ensure_wallet_for_user(state_obj, user_id)
    if wallet is None:
        return None
    before = _wallet_float(wallet.get('balance', 0))
    after = round(before + amount, 2)
    wallet['balance'] = after
    wallet['updatedAt'] = _now_iso_local()
    ledger_entry = {
        'id': str(uuid.uuid4())[:8].upper(),
        'time': _now_iso_local(),
        'type': 'payment_credit',
        'amount': amount,
        'balanceBefore': before,
        'balanceAfter': after,
        'note': note or f"Payment approved #{payment.get('id')}",
        'source': 'payment_automation',
        'paymentId': payment.get('id'),
        'utr': payment.get('utr', '')
    }
    wallet.setdefault('ledger', []).append(ledger_entry)
    payment['walletCredited'] = True
    payment['walletCreditAmount'] = amount
    payment['walletBalanceAfter'] = after
    payment['walletLedgerId'] = ledger_entry['id']
    return wallet

def _default_market_close_times():
    out = {m["n"]: f"{int(m['hr']):02d}:{int(m['min']):02d}" for m in MARKETS}
    for b in BASE_MARKETS:
        name = b["n"]
        close = next((m for m in MARKETS if m["n"] == name + " CLOSE"), None)
        open_m = next((m for m in MARKETS if m["n"] == name + " OPEN"), None)
        if close:
            out[name] = f"{int(close['hr']):02d}:{int(close['min']):02d}"
        elif open_m:
            out[name] = f"{int(open_m['hr']):02d}:{int(open_m['min']):02d}"
    if "SRIDEV DAY" in out and "SRIDEVI DAY" not in out:
        out["SRIDEVI DAY"] = out["SRIDEV DAY"]
    return out

def _compact_market_time_key(value):
    return ''.join(ch for ch in str(value or '').upper().replace('SRIDEVI DAY', 'SRIDEV DAY') if ch.isalnum())

def _canonical_market_time_key(value):
    raw = str(value or '').strip().upper().replace('*', '')
    compact = _compact_market_time_key(raw)
    for item in list(MARKETS) + list(BASE_MARKETS):
        name = str(item.get('n') or '').strip().upper()
        if _compact_market_time_key(name) == compact:
            return name
    return ' '.join(raw.split())

def _normalize_hhmm(value):
    txt = str(value or '').strip()
    parts = txt.split(':')
    if len(parts) != 2:
        return ''
    try:
        h, m = int(parts[0]), int(parts[1])
    except Exception:
        return ''
    if 0 <= h <= 23 and 0 <= m <= 59:
        return f"{h:02d}:{m:02d}"
    return ''

def _default_entry_settings():
    return {
        "entryParserEnabled": True,
        "groupsOnly": True,
        "strictFormat": True,
        "autoDebitWallet": True,
        "marketTimingEnabled": True,
        "riskLimitEnabled": True,
        "duplicatePolicy": "sender_market_type_digits_date",
        "marketCloseTimes": _default_market_close_times()
    }

def _client_profile_ids(state_obj):
    profiles = state_obj.get("profiles", {}) if isinstance(state_obj, dict) else {}
    return [pid for pid in profiles.keys() if not str(pid).startswith("admin")]

def _ensure_foundation_state(state_obj):
    if not isinstance(state_obj, dict):
        return state_obj
    state_obj.setdefault("entries", [])
    state_obj.setdefault("wallets", {})
    state_obj.setdefault("auditLog", [])
    state_obj.setdefault("marketLocks", {})
    state_obj.setdefault("riskSettings", _default_risk_settings())
    state_obj.setdefault("walletSettings", _default_wallet_settings())
    state_obj.setdefault("entrySettings", _default_entry_settings())
    state_obj.setdefault("settlementRecords", {})
    state_obj.setdefault("settlementSettings", _default_settlement_settings())
    state_obj.setdefault("paymentSettings", _default_payment_settings())
    state_obj.setdefault("paymentOutbox", [])
    state_obj.setdefault("loadForwarder", _default_load_forwarder_settings())
    state_obj.setdefault("loadForwarderOutbox", [])
    state_obj.setdefault("spamGuardSettings", _default_spam_guard_settings())
    state_obj.setdefault("spamGuardStrikes", {})
    state_obj.setdefault("spamGuardEvents", [])
    # Preserve existing custom values while adding any missing keys.
    for k, v in _default_risk_settings().items():
        state_obj["riskSettings"].setdefault(k, v)
    for k, v in _default_wallet_settings().items():
        state_obj["walletSettings"].setdefault(k, v)
    for k, v in _default_settlement_settings().items():
        state_obj["settlementSettings"].setdefault(k, v)
    for k, v in _default_payment_settings().items():
        state_obj["paymentSettings"].setdefault(k, v)
    for k, v in _default_load_forwarder_settings().items():
        state_obj["loadForwarder"].setdefault(k, v)
    for k, v in _default_spam_guard_settings().items():
        state_obj["spamGuardSettings"].setdefault(k, v)
    if not isinstance(state_obj["settlementSettings"].get("payoutMultipliers"), dict):
        state_obj["settlementSettings"]["payoutMultipliers"] = _default_settlement_settings()["payoutMultipliers"]
    else:
        for k, v in _default_settlement_settings()["payoutMultipliers"].items():
            state_obj["settlementSettings"]["payoutMultipliers"].setdefault(k, v)
    for k, v in _default_entry_settings().items():
        state_obj["entrySettings"].setdefault(k, v)
    if not isinstance(state_obj["entrySettings"].get("marketCloseTimes"), dict):
        state_obj["entrySettings"]["marketCloseTimes"] = _default_market_close_times()
    else:
        for mk, mt in _default_market_close_times().items():
            state_obj["entrySettings"]["marketCloseTimes"].setdefault(mk, mt)
    return state_obj

def _ensure_wallet_for_user(state_obj, user_id):
    _ensure_foundation_state(state_obj)
    profiles = state_obj.get("profiles", {})
    if user_id not in profiles:
        return None
    settings = state_obj.get("walletSettings", _default_wallet_settings())
    wallets = state_obj.setdefault("wallets", {})
    prof = profiles.get(user_id, {}) or {}
    if user_id not in wallets or not isinstance(wallets.get(user_id), dict):
        wallets[user_id] = {
            "userId": user_id,
            "name": prof.get("name", user_id),
            "phone": prof.get("phone", ""),
            "balance": 0,
            "creditLimit": float(settings.get("defaultCreditLimit", 0) or 0),
            "ledger": [],
            "createdAt": _now_iso_local(),
            "updatedAt": _now_iso_local()
        }
    else:
        wallets[user_id].setdefault("userId", user_id)
        wallets[user_id]["name"] = prof.get("name", wallets[user_id].get("name", user_id))
        wallets[user_id]["phone"] = prof.get("phone", wallets[user_id].get("phone", ""))
        wallets[user_id].setdefault("balance", 0)
        wallets[user_id].setdefault("creditLimit", float(settings.get("defaultCreditLimit", 0) or 0))
        wallets[user_id].setdefault("ledger", [])
        wallets[user_id].setdefault("createdAt", _now_iso_local())
        wallets[user_id]["updatedAt"] = wallets[user_id].get("updatedAt", _now_iso_local())
    return wallets[user_id]

def _ensure_wallets_for_profiles(state_obj):
    _ensure_foundation_state(state_obj)
    for uid in _client_profile_ids(state_obj):
        _ensure_wallet_for_user(state_obj, uid)
    return state_obj.get("wallets", {})

def _wallet_float(v):
    try:
        return round(float(v or 0), 2)
    except Exception:
        return 0.0

def _add_audit(state_obj, action, detail=None):
    _ensure_foundation_state(state_obj)
    log = state_obj.setdefault("auditLog", [])
    log.append({
        "id": str(uuid.uuid4())[:8].upper(),
        "time": _now_iso_local(),
        "action": action,
        "detail": detail or {}
    })
    if len(log) > 500:
        del log[:-500]
    return log[-1]

def migrate_and_get_state():
    data = load_from_firebase()
    if data and "profiles" in data:
        _ensure_foundation_state(data)
        # Auto-migrate old single master into multi-admin system
        if "master" in data["profiles"] and "admin1" not in data["profiles"]:
            old_master = data["profiles"].pop("master")
            data["profiles"]["admin1"] = old_master
            data["profiles"]["admin2"] = json.loads(json.dumps(old_master))
            data["profiles"]["admin2"]["name"] = "MASTER ADMIN 2"
            data["profiles"]["admin3"] = json.loads(json.dumps(old_master))
            data["profiles"]["admin3"]["name"] = "MASTER ADMIN 3"

        if "client_dummy" not in data["profiles"]:
            data["profiles"]["client_dummy"] = {"name": "DUMMY TEST VIP", "phone": "", "config": get_default_config(), "dayRecords": {}}
        if "broadcasts" not in data:
            data["broadcasts"] = []
        if "payments" not in data:
            data["payments"] = []
        if "paymentMethods" not in data:
            data["paymentMethods"] = {"upi": "", "phone": "", "qr": ""}
        if "resultRecords" not in data:
            data["resultRecords"] = {}
        if "resultTargets" not in data:
            data["resultTargets"] = []
        if "resultSettings" not in data:
            data["resultSettings"] = {"autoScrapeEnabled": True, "useForwardTargetsForResults": True}
        if "autoScrapeEnabled" not in data.get("resultSettings", {}):
            data["resultSettings"]["autoScrapeEnabled"] = True
        if "settlementRecords" not in data:
            data["settlementRecords"] = {}
        if "settlementSettings" not in data:
            data["settlementSettings"] = _default_settlement_settings()
        _ensure_wallets_for_profiles(data)
        for pid, profile in data["profiles"].items():
            if "expiryDate" not in profile:
                profile["expiryDate"] = ""
            if "vipAccessEnabled" not in profile:
                profile["vipAccessEnabled"] = True
            if "config" not in profile:
                profile["config"] = get_default_config()
            else:
                if "capital" not in profile["config"]:
                    profile["config"]["capital"] = 0
                if "dayTarget" not in profile["config"]:
                    profile["config"]["dayTarget"] = 0
        return data

    default_state = {
        "activeId": "admin1",
        "broadcasts": [],
        "payments": [],
        "paymentMethods": {"upi": "", "phone": "", "qr": ""},
        "resultRecords": {},
        "resultTargets": [],
        "resultSettings": {"autoScrapeEnabled": True, "useForwardTargetsForResults": True},
        "entries": [],
        "wallets": {},
        "auditLog": [],
        "marketLocks": {},
        "riskSettings": _default_risk_settings(),
        "walletSettings": _default_wallet_settings(),
        "entrySettings": _default_entry_settings(),
        "loadForwarder": _default_load_forwarder_settings(),
        "loadForwarderOutbox": [],
        "spamGuardSettings": _default_spam_guard_settings(),
        "spamGuardStrikes": {},
        "spamGuardEvents": [],
        "profiles": {
            "admin1": { "name": "MASTER ADMIN 1", "phone": "", "config": get_default_config(), "dayRecords": {}, "expiryDate": "" },
            "admin2": { "name": "MASTER ADMIN 2", "phone": "", "config": get_default_config(), "dayRecords": {}, "expiryDate": "" },
            "admin3": { "name": "MASTER ADMIN 3", "phone": "", "config": get_default_config(), "dayRecords": {}, "expiryDate": "" },
            "client_dummy": { "name": "DUMMY TEST VIP", "phone": "", "config": get_default_config(), "dayRecords": {}, "expiryDate": "" }
        }
    }
    _ensure_wallets_for_profiles(default_state)
    save_to_firebase(default_state)
    return default_state

@app.route('/sw.js')
def sw():
    js = """
    self.addEventListener('install', (e)=>{self.skipWaiting();});
    self.addEventListener('activate', (e)=>{self.clients.claim();});
    self.addEventListener('fetch', (e)=>{ e.respondWith(fetch(e.request).catch(()=>new Response('Offline'))); });
    self.addEventListener('notificationclick', function(event) {
        event.notification.close();
        event.waitUntil(clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function(clientList) {
            if (clientList.length > 0) {
                let client = clientList[0];
                for (let i = 0; i < clientList.length; i++) { if (clientList[i].focused) { client = clientList[i]; } }
                return client.focus();
            }
            return clients.openWindow('/');
        }));
    });
    """
    return app.response_class(js, mimetype='application/javascript')

@app.route('/icon.svg')
def app_icon_svg():
    svg = """<svg xmlns='http://www.w3.org/2000/svg' width='512' height='512' viewBox='0 0 512 512'>
  <rect width='512' height='512' rx='100' fill='#2AABEE'/>
  <text x='256' y='360' font-size='300' text-anchor='middle' font-family='Arial Black,sans-serif' font-weight='900' fill='white'>T</text>
</svg>"""
    return app.response_class(svg, mimetype='image/svg+xml', headers={'Cache-Control': 'public, max-age=86400'})

@app.route('/manifest.json')
def manifest():
    vip_id = request.args.get('vip')
    start_url = f"/?vip={vip_id}" if vip_id else "/"
    app_name = "TITAN VIP" if vip_id else "TITAN MASTER"
    base = request.host_url.rstrip('/')
    return jsonify({
        "name": app_name,
        "short_name": "Titan",
        "description": "Titan Nova - Professional Matka Ledger",
        "start_url": start_url,
        "scope": "/",
        "display": "standalone",
        "background_color": "#17212B",
        "theme_color": "#2AABEE",
        "orientation": "portrait",
        "icons": [
            {"src": f"{base}/icon.svg", "sizes": "192x192", "type": "image/svg+xml", "purpose": "any"},
            {"src": f"{base}/icon.svg", "sizes": "512x512", "type": "image/svg+xml", "purpose": "any"},
            {"src": "https://cdn-icons-png.flaticon.com/512/5738/5738033.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": "https://cdn-icons-png.flaticon.com/512/5738/5738033.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}
        ]
    })

@app.route('/api/state')
def get_state_api():
    return jsonify(migrate_and_get_state())

@app.route('/')
def index():
    state = migrate_and_get_state()
    vip_id = request.args.get('vip')

    manifest_url = f"/manifest.json?vip={vip_id}" if vip_id else "/manifest.json"

    if vip_id:
        if vip_id in state.get("profiles", {}):
            user_payments = [p for p in state.get("payments", []) if p.get("userId") == vip_id]
            isolated_state = { "activeId": vip_id, "broadcasts": state.get("broadcasts", []), "profiles": { vip_id: state["profiles"][vip_id] }, "paymentMethods": state.get("paymentMethods", {"upi":"","phone":"","qr":""}), "payments": user_payments, "resultRecords": state.get("resultRecords", {}), "resultTargets": [], "resultSettings": state.get("resultSettings", {"autoScrapeEnabled": True, "useForwardTargetsForResults": True}), "wallets": {vip_id: state.get("wallets", {}).get(vip_id, {})}, "walletSettings": state.get("walletSettings", _default_wallet_settings()), "entrySettings": state.get("entrySettings", _default_entry_settings()), "entries": [e for e in state.get("entries", []) if e.get("userId") == vip_id], "settlementRecords": state.get("settlementRecords", {}), "settlementSettings": state.get("settlementSettings", _default_settlement_settings()), "paymentSettings": state.get("paymentSettings", _default_payment_settings()), "loadForwarder": state.get("loadForwarder", _default_load_forwarder_settings()), "loadForwarderOutbox": [], "spamGuardSettings": state.get("spamGuardSettings", _default_spam_guard_settings()), "spamGuardEvents": [] }
            return render_template_string(HTML_TEMPLATE, state=isolated_state, markets=MARKETS, baseMarkets=BASE_MARKETS, chartLinks=CHART_LINKS, is_master=False, manifest_url=manifest_url)
        else:
            blocked_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
                <title>Access Denied</title>
            </head>
            <body style="background:#17212B; color:#fff; font-family:sans-serif; text-align:center; padding:50px 20px;">
                <div style="background:#232E3C; border:1px solid #FF5D5D; padding:30px; border-radius:16px; margin-top:20vh; box-shadow: 0 4px 20px rgba(239, 68, 68, 0.2);">
                    <h2 style="color:#FF5D5D; margin-top:0; font-weight:900;">MEMBERSHIP EXPIRED</h2>
                    <p style="color:#7A9CB8; font-size:14px; margin-bottom:0; line-height:1.5;">Aapka access admin dwara hata diya gaya hai. Kripya naye app link ke liye Admin se sampark karein.</p>
                </div>
            </body>
            </html>
            """
            return blocked_html
    else:
        state["activeId"] = "admin1"
        return render_template_string(HTML_TEMPLATE, state=state, markets=MARKETS, baseMarkets=BASE_MARKETS, chartLinks=CHART_LINKS, is_master=True, manifest_url=manifest_url)

@app.route('/save', methods=['POST'])
def save():
    incoming = request.json
    if not incoming: return jsonify({"status": "error"})

    active_id = incoming.get("activeId")
    is_master_saving = (
    active_id in ["admin1", "admin2", "admin3"]
    or "admin1" in incoming.get("profiles", {})
    or "admin2" in incoming.get("profiles", {})
    or "admin3" in incoming.get("profiles", {})
)

    if is_master_saving:
        save_to_firebase(incoming)
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "rejected", "msg": "Client app is restricted to Read-Only mode."})

@app.route('/api/submit_payment', methods=['POST'])
def submit_payment():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "Invalid request"}), 400

    state = migrate_and_get_state()
    _ensure_foundation_state(state)
    if 'payments' not in state:
        state['payments'] = []

    settings = state.setdefault('paymentSettings', _default_payment_settings())
    if not settings.get('paymentAutomationEnabled', True):
        return jsonify({'status': 'error', 'message': 'Payment automation OFF hai.'}), 403

    utr = str(data.get('utr', '')).strip()
    amount = _payment_float(data.get('amount', 0))
    user_id = data.get('userId')
    if not user_id or user_id not in state.get('profiles', {}):
        return jsonify({'status': 'error', 'message': 'Valid user missing'}), 400
    if amount <= 0:
        return jsonify({'status': 'error', 'message': 'Amount 0 se zyada hona chahiye'}), 400

    autoFlag = _payment_risk_flag(state, user_id, amount, utr)
    decision = 'pending'
    if autoFlag == 'duplicate' and settings.get('duplicateUtrBlock', True):
        decision = 'blocked'

    payment = {
        'id': str(uuid.uuid4())[:8].upper(),
        'userId': user_id,
        'userName': data.get('userName') or state.get('profiles', {}).get(user_id, {}).get('name', user_id),
        'amount': amount,
        'utr': utr,
        'utrNormalized': _normalize_utr(utr),
        'planLabel': data.get('planLabel', ''),
        'image': data.get('image', ''),
        'status': 'pending' if decision != 'blocked' else 'rejected',
        'autoFlag': autoFlag,
        'riskLevel': 'LOW' if autoFlag == 'safe' else ('HIGH' if autoFlag in ['duplicate', 'high_amount', 'utr_missing'] else 'MEDIUM'),
        'decision': decision,
        'walletCredited': False,
        'time': datetime.datetime.now().strftime('%d-%m-%Y %I:%M %p'),
        'createdAt': _now_iso_local()
    }
    if decision == 'blocked':
        payment['rejectReason'] = 'Duplicate UTR blocked automatically.'
        payment['rejectedAt'] = _now_iso_local()

    state['payments'].append(payment)
    _add_audit(state, 'payment_submitted', {'paymentId': payment['id'], 'userId': user_id, 'amount': amount, 'flag': autoFlag, 'status': payment['status']})
    _queue_payment_message(
        state,
        user_id,
        f"💳 *PAYMENT SUBMITTED*\n━━━━━━━━━━━━━━━━━━━━\n🆔 *ID:* #{payment['id']}\n💵 *Amount:* ₹{amount:g}\n🔢 *UTR:* {utr or '-'}\n⚡ *Status:* {payment['status'].upper()}\n📝 Admin verification ke baad wallet update hoga.",
        {'type': 'payment_submitted', 'paymentId': payment['id']}
    )
    save_to_firebase(state)
    return jsonify({'status': 'success', 'flag': autoFlag, 'paymentStatus': payment['status'], 'paymentId': payment['id']})

@app.route('/api/approve_payment', methods=['POST'])
def approve_payment():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "Invalid request"}), 400
    state = migrate_and_get_state()
    _ensure_foundation_state(state)
    settings = state.setdefault('paymentSettings', _default_payment_settings())
    pid = data.get('paymentId')
    days = int(_payment_float(data.get('days', 30)))
    credit_wallet = bool(data.get('creditWallet', settings.get('approveCreditsWallet', True)))
    extend_membership = bool(data.get('extendMembership', settings.get('extendMembershipOnApprove', True)))
    payment = None
    for p in state.get('payments', []):
        if p.get('id') == pid:
            payment = p
            break
    if not payment:
        return jsonify({'status': 'error', 'message': 'Payment not found'}), 404
    if payment.get('status') == 'approved':
        return jsonify({'status': 'success', 'message': 'Already approved', 'payment': payment, 'wallets': state.get('wallets', {})})
    if payment.get('status') == 'rejected' and payment.get('decision') == 'blocked':
        return jsonify({'status': 'error', 'message': 'Blocked duplicate payment approve nahi ho sakta.'}), 400

    user_id = payment.get('userId')
    wallet = None
    if credit_wallet and not payment.get('walletCredited'):
        wallet = _credit_wallet_from_payment(state, payment, f"Payment approved #{pid}")
    if extend_membership and user_id and user_id in state.get('profiles', {}):
        profile = state['profiles'][user_id]
        current_expiry = profile.get('expiryDate', '')
        now = datetime.datetime.now()
        if current_expiry:
            try:
                base = datetime.datetime.fromisoformat(current_expiry)
                if base < now:
                    base = now
            except Exception:
                base = now
        else:
            base = now
        if days > 0:
            profile['expiryDate'] = (base + datetime.timedelta(days=days)).date().isoformat()
            payment['membershipDays'] = days
            payment['membershipExtended'] = True

    payment['status'] = 'approved'
    payment['approvedAt'] = _now_iso_local()
    payment['approvedBy'] = 'admin'
    _add_audit(state, 'payment_approved', {'paymentId': pid, 'userId': user_id, 'amount': payment.get('amount'), 'walletCredited': bool(wallet), 'days': days if extend_membership else 0})
    bal_line = f"\n💰 *Wallet Balance:* ₹{_wallet_float(wallet.get('balance')):g}" if wallet else ""
    _queue_payment_message(
        state,
        user_id,
        f"✅ *PAYMENT APPROVED*\n━━━━━━━━━━━━━━━━━━━━\n🆔 *ID:* #{pid}\n💵 *Amount:* ₹{_payment_float(payment.get('amount')):g}\n🔢 *UTR:* {payment.get('utr') or '-'}{bal_line}\n📝 Wallet/payment update complete.",
        {'type': 'payment_approved', 'paymentId': pid}
    )
    save_to_firebase(state)
    return jsonify({'status': 'success', 'payment': payment, 'wallet': wallet, 'wallets': state.get('wallets', {})})

@app.route('/api/reject_payment', methods=['POST'])
def reject_payment():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "Invalid request"}), 400
    state = migrate_and_get_state()
    _ensure_foundation_state(state)
    pid = data.get('paymentId')
    reason = str(data.get('reason') or 'Payment rejected by admin').strip()
    payment = None
    for p in state.get('payments', []):
        if p.get('id') == pid:
            payment = p
            break
    if not payment:
        return jsonify({'status': 'error', 'message': 'Payment not found'}), 404
    if payment.get('status') == 'approved':
        return jsonify({'status': 'error', 'message': 'Approved payment reject nahi ho sakta.'}), 400
    payment['status'] = 'rejected'
    payment['rejectReason'] = reason
    payment['rejectedAt'] = _now_iso_local()
    _add_audit(state, 'payment_rejected', {'paymentId': pid, 'userId': payment.get('userId'), 'reason': reason})
    _queue_payment_message(
        state,
        payment.get('userId'),
        f"❌ *PAYMENT REJECTED*\n━━━━━━━━━━━━━━━━━━━━\n🆔 *ID:* #{pid}\n💵 *Amount:* ₹{_payment_float(payment.get('amount')):g}\n📝 *Reason:* {reason}",
        {'type': 'payment_rejected', 'paymentId': pid}
    )
    save_to_firebase(state)
    return jsonify({'status': 'success', 'payment': payment})

@app.route('/api/payment_settings', methods=['POST'])
def api_payment_settings():
    data = request.json or {}
    state = migrate_and_get_state()
    settings = state.setdefault('paymentSettings', _default_payment_settings())
    for key in ['paymentAutomationEnabled', 'requireUtr', 'duplicateUtrBlock', 'approveCreditsWallet', 'extendMembershipOnApprove', 'notifyUserPrivate']:
        if key in data:
            settings[key] = bool(data.get(key))
    if 'minAmount' in data:
        settings['minAmount'] = max(0, _payment_float(data.get('minAmount')))
    if 'maxAmount' in data:
        settings['maxAmount'] = max(settings.get('minAmount', 0), _payment_float(data.get('maxAmount')))
    _add_audit(state, 'payment_settings', settings)
    save_to_firebase(state)
    return jsonify({'status': 'success', 'paymentSettings': settings})

@app.route('/api/payments')
def api_payments():
    state = migrate_and_get_state()
    payments = state.get('payments', []) if isinstance(state.get('payments', []), list) else []
    return jsonify({
        'status': 'success',
        'payments': payments,
        'paymentSettings': state.get('paymentSettings', _default_payment_settings()),
        'wallets': state.get('wallets', {}),
        'paymentOutbox': state.get('paymentOutbox', [])[-50:]
    })



def get_combined_digits_recent_to_old(jodis):
    seen = set()
    result = []

    recent_to_old = list(reversed(jodis))

    for j in recent_to_old:
        clean = j.replace("-", "").strip()

        if len(clean) == 2 and clean.isdigit():
            for d in [clean[0], clean[1]]:
                if d not in seen:
                    seen.add(d)
                    result.append(d)

                if len(result) >= 10:
                    return ",".join(result)

    return ",".join(result)

@app.route('/api/scrape_market', methods=['POST'])
def scrape_market():
    import urllib.request, urllib.error, gzip, re, ssl

    data = request.json
    if not data: return jsonify({'status': 'error', 'message': 'Invalid request'})

    market_name = data.get('market', '').strip().upper()
    url = None
    for link in CHART_LINKS:
        if link['n'].upper() == market_name:
            url = link['l']
            break

    if not url: return jsonify({'status': 'error', 'message': f'Market not found: {market_name}'})

    def unique_seq(lst):
        seen, result = set(), []
        for x in lst:
            if x not in seen:
                seen.add(x)
                result.append(x)
            if len(result) == 10: break
        return ",".join(result)

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-IN,en;q=0.9,hi;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://www.google.com/',
        }
        req_obj = urllib.request.Request(url, headers=headers)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        response = urllib.request.urlopen(req_obj, timeout=20, context=ctx)
        raw = response.read()

        enc = response.info().get('Content-Encoding', '')
        if enc == 'gzip': raw = gzip.decompress(raw)
        html = raw.decode('utf-8', errors='ignore')

        clean = re.sub(r'<[^>]+>', ' ', html)
        tokens = clean.split()
        jodis = [t.replace("-", "") for t in tokens if len(t.replace("-", "")) == 2 and t.replace("-", "").isdigit()]

        if not jodis: return jsonify({'status': 'error', 'message': 'Page pe koi jodi data nahi mila'})

        recent_to_old = list(reversed(jodis))
        seq_open  = unique_seq([j[0] for j in recent_to_old])
        seq_close = unique_seq([j[1] for j in recent_to_old])

        seen_j, recent_jodis = set(), []
        for j in recent_to_old:
            if j not in seen_j:
                seen_j.add(j)
                recent_jodis.append(j)
            if len(recent_jodis) == 10: break
        seq_jodi = ",".join(recent_jodis)

        combined_seq = get_combined_digits_recent_to_old(jodis)

        return jsonify({
            'status': 'success',
            'market': market_name,
            'open': seq_open,
            'close': seq_close,
            'combined': combined_seq,
            'jodi': seq_jodi,
            'total': len(jodis)
        })
    except Exception as e: return jsonify({'status': 'error', 'message': f'Error: {str(e)}'})

@app.route('/api/save_payment_methods', methods=['POST'])
def save_payment_methods():
    data = request.json
    if not data: return jsonify({"status": "error"})
    state = migrate_and_get_state()
    state['paymentMethods'] = data
    save_to_firebase(state)
    return jsonify({'status': 'success'})

@app.route('/api/set_expiry', methods=['POST'])
def set_expiry():
    data = request.json
    if not data: return jsonify({"status": "error"})
    state = migrate_and_get_state()
    user_id = data.get('userId')
    expiry = data.get('expiryDate')
    if user_id and user_id in state.get('profiles', {}):
        state['profiles'][user_id]['expiryDate'] = expiry
    save_to_firebase(state)
    return jsonify({'status': 'success'})


def _now_label():
    if ZoneInfo:
        try:
            return datetime.datetime.now(ZoneInfo(APP_TZ)).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            pass
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def _clean_result_value(v):
    return str(v or '').strip().upper().replace(' ', '')

def _detect_result_stage(v):
    import re
    val = _clean_result_value(v)
    if re.fullmatch(r'\d{3}-\d', val):
        return 'open', val
    if re.fullmatch(r'\d{3}-\d{2}-\d{3}', val):
        return 'close', val
    return '', val

def _valid_base_market_name(market):
    market = str(market or '').strip().upper()
    for m in BASE_MARKETS:
        if m['n'].upper() == market:
            return m['n']
    return ''

@app.route('/api/wallets')
def api_wallets():
    state = migrate_and_get_state()
    _ensure_wallets_for_profiles(state)
    profiles = state.get('profiles', {})
    clients = []
    for uid in _client_profile_ids(state):
        prof = profiles.get(uid, {}) or {}
        wallet = state.get('wallets', {}).get(uid, {}) or {}
        bal = _wallet_float(wallet.get('balance', 0))
        credit = _wallet_float(wallet.get('creditLimit', 0))
        clients.append({
            'userId': uid,
            'name': prof.get('name', uid),
            'phone': prof.get('phone', ''),
            'expiryDate': prof.get('expiryDate', ''),
            'vipAccessEnabled': prof.get('vipAccessEnabled', True),
            'balance': bal,
            'creditLimit': credit,
            'available': round(bal + credit, 2),
            'ledgerCount': len(wallet.get('ledger', []) if isinstance(wallet.get('ledger', []), list) else [])
        })
    return jsonify({
        'status': 'success',
        'wallets': state.get('wallets', {}),
        'walletSettings': state.get('walletSettings', _default_wallet_settings()),
        'clients': clients
    })

@app.route('/api/wallet_transaction', methods=['POST'])
def api_wallet_transaction():
    data = request.json or {}
    user_id = data.get('userId')
    action = str(data.get('action') or 'add').strip().lower()
    note = str(data.get('note') or '').strip()
    amount = _wallet_float(data.get('amount', 0))
    if not user_id:
        return jsonify({'status': 'error', 'message': 'userId missing'}), 400
    if action not in ['add', 'subtract']:
        return jsonify({'status': 'error', 'message': 'action add/subtract hona chahiye'}), 400
    if amount <= 0:
        return jsonify({'status': 'error', 'message': 'Amount 0 se zyada hona chahiye'}), 400
    state = migrate_and_get_state()
    wallet = _ensure_wallet_for_user(state, user_id)
    if wallet is None:
        return jsonify({'status': 'error', 'message': 'User/profile not found'}), 404
    signed = amount if action == 'add' else -amount
    before = _wallet_float(wallet.get('balance', 0))
    after = round(before + signed, 2)
    wallet['balance'] = after
    wallet['updatedAt'] = _now_iso_local()
    entry = {
        'id': str(uuid.uuid4())[:8].upper(),
        'time': _now_iso_local(),
        'type': action,
        'amount': signed,
        'balanceBefore': before,
        'balanceAfter': after,
        'note': note or ('Manual add' if action == 'add' else 'Manual subtract'),
        'source': 'admin_wallet_tab'
    }
    wallet.setdefault('ledger', []).append(entry)
    _add_audit(state, 'wallet_transaction', {'userId': user_id, 'amount': signed, 'balanceAfter': after, 'note': entry['note']})
    save_to_firebase(state)
    return jsonify({'status': 'success', 'wallet': wallet, 'wallets': state.get('wallets', {})})

@app.route('/api/wallet_credit_limit', methods=['POST'])
def api_wallet_credit_limit():
    data = request.json or {}
    user_id = data.get('userId')
    credit = _wallet_float(data.get('creditLimit', 0))
    if not user_id:
        return jsonify({'status': 'error', 'message': 'userId missing'}), 400
    if credit < 0:
        return jsonify({'status': 'error', 'message': 'Credit limit negative nahi ho sakta'}), 400
    state = migrate_and_get_state()
    wallet = _ensure_wallet_for_user(state, user_id)
    if wallet is None:
        return jsonify({'status': 'error', 'message': 'User/profile not found'}), 404
    before = _wallet_float(wallet.get('creditLimit', 0))
    wallet['creditLimit'] = credit
    wallet['updatedAt'] = _now_iso_local()
    wallet.setdefault('ledger', []).append({
        'id': str(uuid.uuid4())[:8].upper(),
        'time': _now_iso_local(),
        'type': 'credit_limit',
        'amount': 0,
        'balanceBefore': _wallet_float(wallet.get('balance', 0)),
        'balanceAfter': _wallet_float(wallet.get('balance', 0)),
        'note': f'Credit limit {before} → {credit}',
        'source': 'admin_wallet_tab'
    })
    _add_audit(state, 'wallet_credit_limit', {'userId': user_id, 'oldCreditLimit': before, 'creditLimit': credit})
    save_to_firebase(state)
    return jsonify({'status': 'success', 'wallet': wallet, 'wallets': state.get('wallets', {})})

@app.route('/api/wallet_zero_settle', methods=['POST'])
def api_wallet_zero_settle():
    data = request.json or {}
    user_id = data.get('userId')
    note = str(data.get('note') or 'Zero settle').strip()
    if not user_id:
        return jsonify({'status': 'error', 'message': 'userId missing'}), 400
    state = migrate_and_get_state()
    wallet = _ensure_wallet_for_user(state, user_id)
    if wallet is None:
        return jsonify({'status': 'error', 'message': 'User/profile not found'}), 404
    before = _wallet_float(wallet.get('balance', 0))
    wallet['balance'] = 0
    wallet['updatedAt'] = _now_iso_local()
    wallet.setdefault('ledger', []).append({
        'id': str(uuid.uuid4())[:8].upper(),
        'time': _now_iso_local(),
        'type': 'zero_settle',
        'amount': -before,
        'balanceBefore': before,
        'balanceAfter': 0,
        'note': note,
        'source': 'admin_wallet_tab'
    })
    _add_audit(state, 'wallet_zero_settle', {'userId': user_id, 'oldBalance': before})
    save_to_firebase(state)
    return jsonify({'status': 'success', 'wallet': wallet, 'wallets': state.get('wallets', {})})

@app.route('/api/wallet_settings', methods=['POST'])
def api_wallet_settings():
    data = request.json or {}
    state = migrate_and_get_state()
    settings = state.setdefault('walletSettings', _default_wallet_settings())
    if 'defaultCreditLimit' in data:
        settings['defaultCreditLimit'] = _wallet_float(data.get('defaultCreditLimit', 0))
    if 'requirePositiveBalance' in data:
        settings['requirePositiveBalance'] = bool(data.get('requirePositiveBalance'))
    if 'walletEnabled' in data:
        settings['walletEnabled'] = bool(data.get('walletEnabled'))
    _add_audit(state, 'wallet_settings', settings)
    save_to_firebase(state)
    return jsonify({'status': 'success', 'walletSettings': settings})

@app.route('/api/entries')
def api_entries():
    state = migrate_and_get_state()
    date = request.args.get('date') or _safe_today()
    all_entries = state.get('entries', []) if isinstance(state.get('entries', []), list) else []
    entries = [e for e in all_entries if not date or e.get('date') == date]
    # newest first, limit to keep mobile UI light
    entries = sorted(entries, key=lambda x: str(x.get('createdAt') or x.get('time') or ''), reverse=True)[:300]
    total_amount = round(sum(_wallet_float(e.get('total', 0)) for e in entries if e.get('status') == 'accepted'), 2)
    by_market = {}
    for e in entries:
        if e.get('status') != 'accepted':
            continue
        m = str(e.get('market') or 'UNKNOWN')
        by_market.setdefault(m, {'market': m, 'entries': 0, 'total': 0})
        by_market[m]['entries'] += 1
        by_market[m]['total'] = round(by_market[m]['total'] + _wallet_float(e.get('total', 0)), 2)
    return jsonify({
        'status': 'success',
        'date': date,
        'entries': entries,
        'totalEntries': len(entries),
        'totalAmount': total_amount,
        'byMarket': sorted(by_market.values(), key=lambda x: (-x['total'], x['market'])),
        'entrySettings': state.get('entrySettings', _default_entry_settings()),
        'riskSettings': state.get('riskSettings', _default_risk_settings()),
        'marketLocks': state.get('marketLocks', {})
    })

@app.route('/api/entry_settings', methods=['POST'])
def api_entry_settings():
    data = request.json or {}
    state = migrate_and_get_state()
    settings = state.setdefault('entrySettings', _default_entry_settings())
    for key in ['entryParserEnabled', 'groupsOnly', 'strictFormat', 'autoDebitWallet', 'marketTimingEnabled', 'riskLimitEnabled']:
        if key in data:
            settings[key] = bool(data.get(key))
    if 'duplicatePolicy' in data:
        settings['duplicatePolicy'] = str(data.get('duplicatePolicy') or 'sender_market_type_digits_date')
    if isinstance(data.get('marketCloseTimes'), dict):
        cur = settings.setdefault('marketCloseTimes', _default_market_close_times())
        for mk, val in data.get('marketCloseTimes', {}).items():
            norm_time = _normalize_hhmm(val)
            if not norm_time:
                continue
            raw_key = ' '.join(str(mk or '').strip().upper().split())
            canon_key = _canonical_market_time_key(raw_key)
            if raw_key:
                cur[raw_key] = norm_time
            if canon_key:
                cur[canon_key] = norm_time
        settings['marketCloseTimesUpdatedAt'] = datetime.datetime.now().isoformat()
    _add_audit(state, 'entry_settings', settings)
    save_to_firebase(state)
    return jsonify({'status': 'success', 'entrySettings': settings})

@app.route('/api/save_entry_safety', methods=['POST'])
def api_save_entry_safety():
    data = request.json or {}
    state = migrate_and_get_state()
    entry = state.setdefault('entrySettings', _default_entry_settings())
    risk = state.setdefault('riskSettings', _default_risk_settings())

    for key in ['entryParserEnabled', 'groupsOnly', 'strictFormat', 'autoDebitWallet', 'marketTimingEnabled', 'riskLimitEnabled']:
        if key in data:
            entry[key] = bool(data.get(key))

    if isinstance(data.get('marketCloseTimes'), dict):
        cur = entry.setdefault('marketCloseTimes', _default_market_close_times())
        saved_times = {}
        for mk, val in data.get('marketCloseTimes', {}).items():
            norm_time = _normalize_hhmm(val)
            if not norm_time:
                continue
            raw_key = ' '.join(str(mk or '').strip().upper().split())
            canon_key = _canonical_market_time_key(raw_key)
            if raw_key:
                cur[raw_key] = norm_time
                saved_times[raw_key] = norm_time
            if canon_key:
                cur[canon_key] = norm_time
                saved_times[canon_key] = norm_time
        entry['marketCloseTimesUpdatedAt'] = datetime.datetime.now().isoformat()
        entry['lastSavedMarketTimes'] = saved_times

    for key in ['marketDailyLimit', 'digitDailyLimit', 'userDailyLimit']:
        if key in data:
            try:
                risk[key] = max(0, float(data.get(key) or 0))
            except Exception:
                pass
    if 'warningPercent' in data:
        try:
            risk['warningPercent'] = max(1, min(100, int(data.get('warningPercent') or 80)))
        except Exception:
            pass
    if 'autoLockOnLimit' in data:
        risk['autoLockOnLimit'] = bool(data.get('autoLockOnLimit'))

    _add_audit(state, 'entry_safety_settings', {'entrySettings': entry, 'riskSettings': risk})
    save_to_firebase(state)
    return jsonify({'status': 'success', 'entrySettings': entry, 'riskSettings': risk})

@app.route('/api/risk_settings', methods=['POST'])
def api_risk_settings():
    data = request.json or {}
    state = migrate_and_get_state()
    settings = state.setdefault('riskSettings', _default_risk_settings())
    for key in ['marketDailyLimit', 'digitDailyLimit', 'userDailyLimit']:
        if key in data:
            settings[key] = max(0, _wallet_float(data.get(key, 0)))
    if 'warningPercent' in data:
        wp = int(_wallet_float(data.get('warningPercent', 80)))
        settings['warningPercent'] = max(1, min(100, wp))
    if 'autoLockOnLimit' in data:
        settings['autoLockOnLimit'] = bool(data.get('autoLockOnLimit'))
    _add_audit(state, 'risk_settings', settings)
    save_to_firebase(state)
    return jsonify({'status': 'success', 'riskSettings': settings})

@app.route('/api/market_unlock', methods=['POST'])
def api_market_unlock():
    data = request.json or {}
    state = migrate_and_get_state()
    date = data.get('date') or _safe_today()
    market = str(data.get('market') or '').strip().upper()
    locks = state.setdefault('marketLocks', {})
    if isinstance(locks.get(date), dict) and market in locks.get(date, {}):
        locks[date].pop(market, None)
    if market in locks:
        locks.pop(market, None)
    _add_audit(state, 'market_unlock', {'date': date, 'market': market})
    save_to_firebase(state)
    return jsonify({'status': 'success', 'marketLocks': locks})

@app.route('/api/results')
def api_results():
    state = migrate_and_get_state()
    date = request.args.get('date') or _safe_today()
    return jsonify({
        'status': 'success',
        'date': date,
        'resultRecords': state.get('resultRecords', {}),
        'records': state.get('resultRecords', {}).get(date, {}),
        'resultTargets': state.get('resultTargets', []),
        'resultSettings': state.get('resultSettings', {'autoScrapeEnabled': True}),
        'settlementRecords': state.get('settlementRecords', {}),
        'settlementSettings': state.get('settlementSettings', _default_settlement_settings())
    })

@app.route('/api/settlements')
def api_settlements():
    state = migrate_and_get_state()
    date = request.args.get('date') or _safe_today()
    return jsonify({
        'status': 'success',
        'date': date,
        'settlementRecords': state.get('settlementRecords', {}),
        'records': state.get('settlementRecords', {}).get(date, {}),
        'settlementSettings': state.get('settlementSettings', _default_settlement_settings())
    })

@app.route('/api/save_settlement_settings', methods=['POST'])
def api_save_settlement_settings():
    data = request.json or {}
    state = migrate_and_get_state()
    settings = state.setdefault('settlementSettings', _default_settlement_settings())
    if 'enabled' in data:
        settings['enabled'] = bool(data.get('enabled'))
    if 'includeSummaryInResultMessage' in data:
        settings['includeSummaryInResultMessage'] = bool(data.get('includeSummaryInResultMessage'))
    if 'includeHitMissInResultMessage' in data:
        settings['includeHitMissInResultMessage'] = bool(data.get('includeHitMissInResultMessage'))
    if isinstance(data.get('payoutMultipliers'), dict):
        pm = settings.setdefault('payoutMultipliers', _default_settlement_settings()['payoutMultipliers'])
        for k in ['ank', 'jodi', 'penel']:
            if k in data['payoutMultipliers']:
                try:
                    val = float(data['payoutMultipliers'][k])
                    if val >= 0: pm[k] = val
                except Exception:
                    pass
    _add_audit(state, 'settlement_settings', settings)
    save_to_firebase(state)
    return jsonify({'status': 'success', 'settlementSettings': settings})


@app.route('/api/send_hitmiss_report', methods=['POST'])
def api_send_hitmiss_report():
    data = request.json or {}
    try:
        res = requests.post('http://127.0.0.1:3000/send_hitmiss', json=data, timeout=30)
        try:
            payload = res.json()
        except Exception:
            payload = {'status': 'error', 'message': res.text}
        return jsonify(payload), res.status_code
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Gateway offline or unavailable: {str(e)}'}), 503

@app.route('/api/save_result', methods=['POST'])
def api_save_result():
    data = request.json or {}
    market = _valid_base_market_name(data.get('market'))
    stage, result_value = _detect_result_stage(data.get('result'))
    date = data.get('date') or _safe_today()

    if not market:
        return jsonify({'status': 'error', 'message': 'Valid market select karein.'}), 400
    if not stage:
        return jsonify({'status': 'error', 'message': 'Result format 123-4 ya 123-45-678 hona chahiye.'}), 400

    state = migrate_and_get_state()
    state.setdefault('resultRecords', {}).setdefault(date, {})
    rec = state['resultRecords'][date].setdefault(market, {'market': market})
    rec['market'] = market
    rec['updatedAt'] = _now_label()
    rec['source'] = data.get('source') or 'manual'

    if stage == 'open':
        rec['openResult'] = result_value
        rec['openUpdatedAt'] = _now_label()
    else:
        open_stage, open_value = _detect_result_stage(rec.get('openResult'))
        if open_stage != 'open':
            return jsonify({'status': 'error', 'message': 'Pehle fresh open result 123-4 save/declare karein. Old close direct accept nahi hoga.'}), 400
        if not result_value.startswith(open_value):
            return jsonify({'status': 'error', 'message': f'Close result open se match nahi hai. Open {open_value} hai, close {result_value} nahi chalega.'}), 400
        rec['closeResult'] = result_value
        rec['closeUpdatedAt'] = _now_label()

    save_to_firebase(state)
    return jsonify({
        'status': 'success',
        'stage': stage,
        'market': market,
        'result': result_value,
        'record': rec,
        'resultRecords': state.get('resultRecords', {})
    })


@app.route('/api/clear_invalid_auto_results', methods=['POST'])
def api_clear_invalid_auto_results():
    data = request.json or {}
    date = data.get('date') or _safe_today()
    state = migrate_and_get_state()
    day = state.setdefault('resultRecords', {}).setdefault(date, {})
    cleared = []
    for market, rec in list(day.items()):
        if not isinstance(rec, dict):
            continue
        close_stage, close_value = _detect_result_stage(rec.get('closeResult'))
        if close_stage != 'close':
            continue
        open_stage, open_value = _detect_result_stage(rec.get('openResult'))
        # Fresh close is valid only after today's open and must start with that open prefix.
        # Anything else is treated as old/yesterday scraped data and removed from the visible/send queue.
        if open_stage != 'open' or not close_value.startswith(open_value):
            old_close = rec.pop('closeResult', '')
            rec.pop('closeUpdatedAt', None)
            rec['ignoredCloseResult'] = old_close
            rec['ignoredCloseAt'] = _now_label()
            rec['ignoredCloseReason'] = 'fresh_open_missing' if open_stage != 'open' else 'close_does_not_match_open'
            cleared.append({'market': market, 'oldClose': old_close, 'openResult': open_value if open_stage == 'open' else ''})
    save_to_firebase(state)
    return jsonify({'status': 'success', 'date': date, 'cleared': cleared, 'resultRecords': state.get('resultRecords', {})})

@app.route('/api/save_result_targets', methods=['POST'])
def api_save_result_targets():
    data = request.json or {}
    targets = data.get('targets') or []
    if isinstance(targets, str):
        targets = [x.strip() for x in targets.replace('\n', ',').split(',') if x.strip()]
    clean_targets = []
    for t in targets:
        if isinstance(t, dict):
            t = t.get('id') or t.get('jid') or t.get('target') or t.get('phone') or t.get('number') or t.get('value') or ''
        t = str(t or '').strip()
        import re
        m = re.search(r'([0-9A-Za-z._:-]+@(?:g\.us|s\.whatsapp\.net))', t, re.I)
        if m:
            t = m.group(1)
        if t and t not in clean_targets:
            clean_targets.append(t)
    state = migrate_and_get_state()
    state['resultTargets'] = clean_targets
    save_to_firebase(state)
    return jsonify({'status': 'success', 'resultTargets': clean_targets})

@app.route('/api/save_result_settings', methods=['POST'])
def api_save_result_settings():
    data = request.json or {}
    state = migrate_and_get_state()
    settings = state.setdefault('resultSettings', {'autoScrapeEnabled': True})
    if 'autoScrapeEnabled' in data:
        settings['autoScrapeEnabled'] = bool(data.get('autoScrapeEnabled'))
    if 'useForwardTargetsForResults' in data:
        settings['useForwardTargetsForResults'] = bool(data.get('useForwardTargetsForResults'))
    save_to_firebase(state)
    return jsonify({'status': 'success', 'resultSettings': settings})




@app.route('/api/gateway_result_retry', methods=['POST'])
def api_gateway_result_retry():
    data = request.json or {}
    try:
        res = requests.post('http://127.0.0.1:3000/result_retry', json=data, timeout=8)
        return jsonify(res.json()), res.status_code
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/spam_guard')
def api_spam_guard():
    state = migrate_and_get_state()
    settings = state.get('spamGuardSettings', _default_spam_guard_settings())
    events = state.get('spamGuardEvents', []) if isinstance(state.get('spamGuardEvents', []), list) else []
    strikes = state.get('spamGuardStrikes', {}) if isinstance(state.get('spamGuardStrikes', {}), dict) else {}
    return jsonify({
        'status': 'success',
        'settings': settings,
        'events': list(reversed(events[-80:])),
        'strikeCount': len(strikes)
    })

@app.route('/api/save_spam_guard', methods=['POST'])
def api_save_spam_guard():
    data = request.json or {}
    state = migrate_and_get_state()
    settings = state.setdefault('spamGuardSettings', _default_spam_guard_settings())
    bool_keys = ['enabled', 'groupsOnly', 'linkGuardEnabled', 'forwardGuardEnabled', 'deleteMessage', 'kickEnabled', 'exemptAdmins']
    for k in bool_keys:
        if k in data:
            settings[k] = bool(data.get(k))
    int_keys = {'linkStrikeLimit': 3, 'forwardStrikeLimit': 3, 'forwardWindowSeconds': 60}
    for k, default in int_keys.items():
        if k in data:
            try:
                settings[k] = max(1 if 'Limit' in k else 10, int(data.get(k) or default))
            except Exception:
                settings[k] = default
    text_keys = ['alertMessage', 'warningMessage', 'kickMessage', 'forwardAlertMessage', 'forwardWarningMessage']
    for k in text_keys:
        if k in data:
            settings[k] = str(data.get(k) or _default_spam_guard_settings().get(k, '')).strip()
    _add_audit(state, 'spam_guard_settings', {'settings': settings})
    save_to_firebase(state)
    return jsonify({'status': 'success', 'settings': settings})

@app.route('/api/clear_spam_guard', methods=['POST'])
def api_clear_spam_guard():
    state = migrate_and_get_state()
    state['spamGuardStrikes'] = {}
    state['spamGuardEvents'] = []
    _add_audit(state, 'spam_guard_clear', {})
    save_to_firebase(state)
    return jsonify({'status': 'success'})

@app.route('/api/load_forwarder')
def api_load_forwarder():
    state = migrate_and_get_state()
    settings = state.get('loadForwarder', _default_load_forwarder_settings())
    date = request.args.get('date') or _safe_today()
    market = request.args.get('market') or settings.get('selectedMarket') or ''
    max_rows = int(settings.get('maxRowsPerType') or 80)
    report = _build_load_report(state, date=date, market=market, max_rows=max_rows, include_empty=bool(settings.get('includeEmptyTypes')), game_types=settings.get('gameTypes'))
    return jsonify({
        'status': 'success',
        'date': date,
        'settings': settings,
        'report': report,
        'text': _format_load_report_text(report),
        'targets': settings.get('targets', [])
    })

@app.route('/api/save_load_forwarder', methods=['POST'])
def api_save_load_forwarder():
    data = request.json or {}
    state = migrate_and_get_state()
    settings = state.setdefault('loadForwarder', _default_load_forwarder_settings())
    if 'enabled' in data:
        settings['enabled'] = bool(data.get('enabled'))
    if 'scheduleTime' in data:
        norm = _normalize_hhmm(data.get('scheduleTime'))
        if norm:
            settings['scheduleTime'] = norm
    if 'selectedMarket' in data:
        settings['selectedMarket'] = ' '.join(str(data.get('selectedMarket') or '').strip().upper().split())
    if 'targets' in data:
        settings['targets'] = _normalize_forward_targets(data.get('targets'))
    if 'gameTypes' in data:
        settings['gameTypes'] = _normalize_game_types(data.get('gameTypes'))
    if 'maxRowsPerType' in data:
        try:
            settings['maxRowsPerType'] = max(5, min(300, int(data.get('maxRowsPerType') or 80)))
        except Exception:
            settings['maxRowsPerType'] = 80
    if 'includeEmptyTypes' in data:
        settings['includeEmptyTypes'] = bool(data.get('includeEmptyTypes'))
    settings['updatedAt'] = _now_iso_local()
    _add_audit(state, 'load_forwarder_settings', settings)
    save_to_firebase(state)
    return jsonify({'status': 'success', 'settings': settings})

@app.route('/api/load_report_preview')
def api_load_report_preview():
    state = migrate_and_get_state()
    settings = state.get('loadForwarder', _default_load_forwarder_settings())
    date = request.args.get('date') or _safe_today()
    market = request.args.get('market') or settings.get('selectedMarket') or ''
    max_rows = int(request.args.get('maxRowsPerType') or settings.get('maxRowsPerType') or 80)
    game_types = request.args.get('gameTypes') or ','.join(settings.get('gameTypes') or ['ANK', 'PENEL', 'JODI'])
    report = _build_load_report(state, date=date, market=market, max_rows=max_rows, include_empty=bool(settings.get('includeEmptyTypes')), game_types=game_types)
    return jsonify({'status': 'success', 'date': date, 'report': report, 'text': _format_load_report_text(report)})

@app.route('/api/load_forwarder_send', methods=['POST'])
def api_load_forwarder_send():
    data = request.json or {}
    state = migrate_and_get_state()
    settings = state.setdefault('loadForwarder', _default_load_forwarder_settings())
    date = data.get('date') or _safe_today()
    market = data.get('market') if 'market' in data else settings.get('selectedMarket', '')
    targets = _normalize_forward_targets(data.get('targets') if 'targets' in data else settings.get('targets', []))
    if not targets:
        return jsonify({'status': 'error', 'message': 'Forward target select/save karein.'}), 400
    max_rows = int(data.get('maxRowsPerType') or settings.get('maxRowsPerType') or 80)
    game_types = data.get('gameTypes') if 'gameTypes' in data else settings.get('gameTypes')
    report = _build_load_report(state, date=date, market=market, max_rows=max_rows, include_empty=bool(settings.get('includeEmptyTypes')), game_types=game_types)
    text = _format_load_report_text(report)
    msg = {
        'id': str(uuid.uuid4())[:8].upper(),
        'date': date,
        'market': ' '.join(str(market or '').strip().upper().split()),
        'targets': targets,
        'text': text,
        'status': 'pending',
        'attempts': 0,
        'createdAt': _now_iso_local(),
        'source': data.get('source') or 'dashboard_send_now'
    }
    state.setdefault('loadForwarderOutbox', []).append(msg)
    if len(state['loadForwarderOutbox']) > 300:
        state['loadForwarderOutbox'] = state['loadForwarderOutbox'][-300:]
    settings['lastQueuedAt'] = _now_iso_local()
    _add_audit(state, 'load_report_queued', {'id': msg['id'], 'date': date, 'market': msg['market'], 'targets': targets})
    save_to_firebase(state)
    return jsonify({'status': 'success', 'message': 'Load report queue ho gaya. Gateway online hote hi send karega.', 'queued': msg, 'text': text})


# ==========================================================
# TITAN NOVA BACKUP / EXPORT / AUDIT API
# ==========================================================
def _json_dumps_safe(obj):
    try:
        return json.dumps(obj, ensure_ascii=False, sort_keys=True)
    except Exception:
        return str(obj)

def _csv_bytes(headers, rows):
    buff = io.StringIO()
    writer = csv.DictWriter(buff, fieldnames=headers, extrasaction='ignore')
    writer.writeheader()
    for row in rows:
        writer.writerow({h: row.get(h, '') for h in headers})
    return buff.getvalue().encode('utf-8-sig')

def _csv_response(filename, headers, rows):
    data = _csv_bytes(headers, rows)
    return app.response_class(
        data,
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )

def _backup_summary(state_obj):
    today = _safe_today()
    entries = state_obj.get('entries', []) if isinstance(state_obj.get('entries', []), list) else []
    payments = state_obj.get('payments', []) if isinstance(state_obj.get('payments', []), list) else []
    wallets = state_obj.get('wallets', {}) if isinstance(state_obj.get('wallets', {}), dict) else {}
    settlements = state_obj.get('settlementRecords', {}) if isinstance(state_obj.get('settlementRecords', {}), dict) else {}
    today_settlements = settlements.get(today, {}) if isinstance(settlements.get(today, {}), dict) else {}
    audit = state_obj.get('auditLog', []) if isinstance(state_obj.get('auditLog', []), list) else []
    accepted_today = [e for e in entries if e.get('date') == today and e.get('status') == 'accepted']
    return {
        'date': today,
        'profiles': len(state_obj.get('profiles', {}) or {}),
        'wallets': len(wallets),
        'entries': len(entries),
        'acceptedToday': len(accepted_today),
        'todayLoad': round(sum(_wallet_float(e.get('total', 0)) for e in accepted_today), 2),
        'payments': len(payments),
        'pendingPayments': len([p for p in payments if p.get('status') == 'pending']),
        'settlementDays': len(settlements),
        'todaySettlements': len(today_settlements),
        'auditEvents': len(audit),
        'lastBackupAt': (state_obj.get('backupSettings') or {}).get('lastBackupAt', '')
    }

def _entries_export_rows(state_obj):
    rows = []
    for e in state_obj.get('entries', []) if isinstance(state_obj.get('entries', []), list) else []:
        if not isinstance(e, dict):
            continue
        rows.append({
            'id': e.get('id', ''),
            'date': e.get('date', ''),
            'time': e.get('time') or e.get('createdAt', ''),
            'status': e.get('status', ''),
            'userId': e.get('userId', ''),
            'userName': e.get('userName', ''),
            'phone': e.get('phone') or e.get('senderPhone', ''),
            'market': e.get('market', ''),
            'gameType': e.get('gameType') or e.get('type', ''),
            'digits': ','.join([str(x) for x in e.get('digits', [])]) if isinstance(e.get('digits'), list) else str(e.get('digits', '')),
            'parDigit': e.get('parDigit') or e.get('rate', ''),
            'total': e.get('total', ''),
            'source': e.get('source', ''),
            'rawText': e.get('rawText', '')
        })
    return rows

def _wallet_export_rows(state_obj):
    rows = []
    wallets = state_obj.get('wallets', {}) if isinstance(state_obj.get('wallets', {}), dict) else {}
    for uid, w in wallets.items():
        if not isinstance(w, dict):
            continue
        ledger = w.get('ledger', []) if isinstance(w.get('ledger', []), list) else []
        rows.append({
            'userId': uid,
            'name': w.get('name', ''),
            'phone': w.get('phone', ''),
            'balance': w.get('balance', 0),
            'creditLimit': w.get('creditLimit', 0),
            'available': round(_wallet_float(w.get('balance', 0)) + _wallet_float(w.get('creditLimit', 0)), 2),
            'ledgerCount': len(ledger),
            'createdAt': w.get('createdAt', ''),
            'updatedAt': w.get('updatedAt', '')
        })
    return rows

def _wallet_ledger_export_rows(state_obj):
    rows = []
    wallets = state_obj.get('wallets', {}) if isinstance(state_obj.get('wallets', {}), dict) else {}
    for uid, w in wallets.items():
        if not isinstance(w, dict):
            continue
        for item in w.get('ledger', []) if isinstance(w.get('ledger', []), list) else []:
            if not isinstance(item, dict):
                continue
            rows.append({
                'userId': uid,
                'name': w.get('name', ''),
                'phone': w.get('phone', ''),
                'time': item.get('time') or item.get('timestamp') or item.get('createdAt', ''),
                'type': item.get('type', ''),
                'amount': item.get('amount', ''),
                'balanceAfter': item.get('balanceAfter', ''),
                'note': item.get('note') or item.get('reason', ''),
                'ref': item.get('ref', '')
            })
    return rows

def _payments_export_rows(state_obj):
    rows = []
    for pmt in state_obj.get('payments', []) if isinstance(state_obj.get('payments', []), list) else []:
        if not isinstance(pmt, dict):
            continue
        rows.append({
            'id': pmt.get('id', ''),
            'userId': pmt.get('userId', ''),
            'userName': pmt.get('userName', ''),
            'amount': pmt.get('amount', ''),
            'utr': pmt.get('utr', ''),
            'status': pmt.get('status', ''),
            'autoFlag': pmt.get('autoFlag', ''),
            'planLabel': pmt.get('planLabel', ''),
            'time': pmt.get('time', ''),
            'approvedAt': pmt.get('approvedAt', ''),
            'rejectedAt': pmt.get('rejectedAt', ''),
            'rejectReason': pmt.get('rejectReason', ''),
            'walletCredited': pmt.get('walletCredited', '')
        })
    return rows

def _settlement_export_rows(state_obj):
    rows = []
    records = state_obj.get('settlementRecords', {}) if isinstance(state_obj.get('settlementRecords', {}), dict) else {}
    for date, markets_map in records.items():
        if not isinstance(markets_map, dict):
            continue
        for market, stages in markets_map.items():
            if not isinstance(stages, dict):
                continue
            for stage, rec in stages.items():
                if not isinstance(rec, dict):
                    continue
                rows.append({
                    'date': date,
                    'market': market,
                    'stage': stage,
                    'result': rec.get('result', ''),
                    'entries': rec.get('entries', rec.get('entryCount', '')),
                    'hit': rec.get('hit', rec.get('hitCount', '')),
                    'miss': rec.get('miss', rec.get('missCount', '')),
                    'load': rec.get('load', rec.get('totalLoad', '')),
                    'payout': rec.get('payout', rec.get('totalPayout', '')),
                    'profitLoss': rec.get('profitLoss', rec.get('marketProfit', '')),
                    'settledAt': rec.get('settledAt') or rec.get('createdAt', '')
                })
    return rows

def _audit_export_rows(state_obj):
    rows = []
    for a in state_obj.get('auditLog', []) if isinstance(state_obj.get('auditLog', []), list) else []:
        if not isinstance(a, dict):
            continue
        rows.append({
            'id': a.get('id', ''),
            'time': a.get('time', ''),
            'action': a.get('action', ''),
            'detail': _json_dumps_safe(a.get('detail', {}))
        })
    return rows

def _csv_export_spec(kind, state_obj):
    kind = str(kind or '').strip().lower()
    if kind == 'entries':
        rows = _entries_export_rows(state_obj)
        return 'entries', ['id','date','time','status','userId','userName','phone','market','gameType','digits','parDigit','total','source','rawText'], rows
    if kind == 'wallets':
        rows = _wallet_export_rows(state_obj)
        return 'wallets', ['userId','name','phone','balance','creditLimit','available','ledgerCount','createdAt','updatedAt'], rows
    if kind in ('wallet_ledger','ledger'):
        rows = _wallet_ledger_export_rows(state_obj)
        return 'wallet_ledger', ['userId','name','phone','time','type','amount','balanceAfter','note','ref'], rows
    if kind == 'payments':
        rows = _payments_export_rows(state_obj)
        return 'payments', ['id','userId','userName','amount','utr','status','autoFlag','planLabel','time','approvedAt','rejectedAt','rejectReason','walletCredited'], rows
    if kind == 'settlements':
        rows = _settlement_export_rows(state_obj)
        return 'settlements', ['date','market','stage','result','entries','hit','miss','load','payout','profitLoss','settledAt'], rows
    if kind == 'audit':
        rows = _audit_export_rows(state_obj)
        return 'audit', ['id','time','action','detail'], rows
    return None, None, None



def _health_recent_result_updates(state_obj, today):
    """Return recent saved open/close results from Firebase state for Health tab.
    This survives Gateway restarts, unlike runtime gatewayHealth counters.
    """
    out = []
    records = (state_obj.get('resultRecords', {}) or {}).get(today, {}) if isinstance(state_obj, dict) else {}
    if not isinstance(records, dict):
        return out
    for market, rec in records.items():
        if not isinstance(rec, dict):
            continue
        for stage_key, result_key, time_key in [
            ('open', 'openResult', 'openUpdatedAt'),
            ('close', 'closeResult', 'closeUpdatedAt')
        ]:
            result = str(rec.get(result_key, '') or '').strip()
            if not result:
                continue
            out.append({
                'market': market,
                'stage': stage_key,
                'result': result,
                'time': rec.get(time_key) or rec.get('updatedAt') or rec.get('lastResultAt') or '',
                'source': rec.get('source') or rec.get('sourceUrl') or 'firebase'
            })
    def _sort_key(x):
        return str(x.get('time') or '')
    return sorted(out, key=_sort_key, reverse=True)[:12]

def _health_label_guard_reason(reason):
    reason = str(reason or '').strip()
    labels = {
        'fresh_open_missing': 'Old/final ignored — fresh open missing',
        'close_open_mismatch': 'Close ignored — open/result mismatch',
        'invalid_format': 'Invalid result format skipped',
        'stale_candidate': 'Stale duplicate skipped'
    }
    return labels.get(reason, reason or 'skipped')

@app.route('/api/health_monitor')
def api_health_monitor():
    state = migrate_and_get_state()
    today = _safe_today()

    def _count_pending(items):
        if not isinstance(items, list):
            return 0
        return len([x for x in items if isinstance(x, dict) and str(x.get('status', '')).lower() == 'pending'])

    gateway = {'status': 'offline', 'connected': False, 'message': 'Gateway not reachable'}
    gateway_results = {'status': 'offline', 'results': []}
    gateway_targets = {'status': 'offline', 'contacts': [], 'groups': []}
    wa_login = {'status': 'offline', 'connected': False, 'qrAvailable': False}
    try:
        r = requests.get('http://127.0.0.1:3000/health', timeout=4)
        try:
            gateway = r.json()
        except Exception:
            gateway = {'status': 'error', 'connected': False, 'message': r.text[:200]}
    except Exception as e:
        gateway = {'status': 'offline', 'connected': False, 'message': str(e)}
    try:
        r = requests.get('http://127.0.0.1:3000/results', timeout=4)
        gateway_results = r.json()
    except Exception as e:
        gateway_results = {'status': 'offline', 'results': [], 'message': str(e)}
    try:
        r = requests.get('http://127.0.0.1:3000/targets?force=1', timeout=6)
        gateway_targets = r.json()
    except Exception as e:
        gateway_targets = {'status': 'offline', 'contacts': [], 'groups': [], 'message': str(e)}

    try:
        r = requests.get('http://127.0.0.1:3000/wa_login_status', timeout=4)
        wa_login = r.json()
    except Exception as e:
        wa_login = {'status': 'offline', 'connected': False, 'qrAvailable': False, 'message': str(e)}

    entries = state.get('entries', []) if isinstance(state.get('entries', []), list) else []
    today_entries = [e for e in entries if isinstance(e, dict) and e.get('date') == today and e.get('status') == 'accepted']
    today_load = sum(_wallet_float(e.get('total', 0)) for e in today_entries)
    settlements_today = state.get('settlementRecords', {}).get(today, {}) if isinstance(state.get('settlementRecords', {}), dict) else {}
    result_records_today = state.get('resultRecords', {}).get(today, {}) if isinstance(state.get('resultRecords', {}), dict) else {}
    audit = state.get('auditLog', []) if isinstance(state.get('auditLog', []), list) else []
    payments = state.get('payments', []) if isinstance(state.get('payments', []), list) else []
    payment_outbox = state.get('paymentOutbox', []) if isinstance(state.get('paymentOutbox', []), list) else []
    load_outbox = state.get('loadForwarderOutbox', []) if isinstance(state.get('loadForwarderOutbox', []), list) else []
    lf = state.get('loadForwarder', _default_load_forwarder_settings()) or {}
    rs = state.get('resultSettings', {'autoScrapeEnabled': True}) or {}

    risk = state.get('riskSettings', _default_risk_settings()) or {}
    wallets = state.get('wallets', {}) if isinstance(state.get('wallets', {}), dict) else {}
    low_wallets = []
    for uid, wallet in wallets.items():
        if not isinstance(wallet, dict):
            continue
        available = _wallet_float(wallet.get('balance', 0)) + _wallet_float(wallet.get('creditLimit', 0))
        if available <= 0:
            low_wallets.append({
                'userId': uid,
                'name': wallet.get('name') or uid,
                'available': round(available, 2),
                'balance': round(_wallet_float(wallet.get('balance', 0)), 2),
                'creditLimit': round(_wallet_float(wallet.get('creditLimit', 0)), 2)
            })
    low_wallets = sorted(low_wallets, key=lambda x: x.get('available', 0))[:8]
    risk_summary = {
        'marketDailyLimit': risk.get('marketDailyLimit', 0),
        'digitDailyLimit': risk.get('digitDailyLimit', 0),
        'userDailyLimit': risk.get('userDailyLimit', 0),
        'warningPercent': risk.get('warningPercent', 80),
        'autoLockOnLimit': risk.get('autoLockOnLimit', False),
        'lowWallets': low_wallets
    }
    action_plan = []
    if not (gateway.get('connected') is True):
        action_plan.append({'level': 'danger', 'title': 'WhatsApp reconnect required', 'detail': 'Gateway/WhatsApp online nahi hai, QR scan ya session reset karo.', 'target': 'health'})
    if len(state.get('resultTargets', []) or []) == 0 and not (lf.get('targets') or []):
        action_plan.append({'level': 'warning', 'title': 'Result targets missing', 'detail': 'Result/Forward target save karo warna result send skip hoga.', 'target': 'results'})
    if _count_pending(load_outbox):
        action_plan.append({'level': 'warning', 'title': 'Load report pending', 'detail': f"{_count_pending(load_outbox)} load forward message pending hai.", 'target': 'forward'})
    if len([p for p in payments if isinstance(p, dict) and p.get('status') == 'pending']):
        action_plan.append({'level': 'info', 'title': 'Payments pending', 'detail': 'Pending payments verify karke wallet credit flow complete karo.', 'target': 'payments'})
    if low_wallets:
        action_plan.append({'level': 'warning', 'title': 'Wallet balance attention', 'detail': f"{len(low_wallets)} wallet zero/negative available balance par hai.", 'target': 'wallets'})
    if not action_plan:
        action_plan.append({'level': 'success', 'title': 'Professional flow healthy', 'detail': 'Entry, result, wallet aur delivery flow ready hai.', 'target': 'health'})

    flow_status = [
        {'key': 'entry', 'title': 'Entry', 'ok': bool((state.get('entrySettings') or {}).get('entryParserEnabled', True)), 'detail': f"Today {len(today_entries)} accepted / ₹{round(today_load, 2)} load"},
        {'key': 'wallet', 'title': 'Wallet', 'ok': bool((state.get('walletSettings') or {}).get('walletEnabled', True)), 'detail': f"{len(wallets)} wallets, {len(low_wallets)} low balance"},
        {'key': 'risk', 'title': 'Risk', 'ok': bool((state.get('entrySettings') or {}).get('riskLimitEnabled', True)), 'detail': f"Warn at {risk_summary['warningPercent']}%, auto-lock {'ON' if risk_summary['autoLockOnLimit'] else 'OFF'}"},
        {'key': 'result', 'title': 'Result', 'ok': bool(rs.get('autoScrapeEnabled', True)), 'detail': f"{len(result_records_today or {})} markets saved today"},
        {'key': 'settlement', 'title': 'Settlement', 'ok': bool((state.get('settlementSettings') or {}).get('enabled', True)), 'detail': f"{len(settlements_today or {})} settlements today"},
        {'key': 'delivery', 'title': 'Delivery', 'ok': bool(gateway.get('connected') is True), 'detail': f"Targets {len(state.get('resultTargets', []) or [])} + Forward {len(lf.get('targets') or [])}"},
        {'key': 'guard', 'title': 'Guard', 'ok': bool((state.get('spamGuardSettings') or {}).get('enabled', True)), 'detail': f"{len(state.get('spamGuardEvents', []) or []) if isinstance(state.get('spamGuardEvents', []), list) else 0} guard events"},
        {'key': 'backup', 'title': 'Backup', 'ok': bool((state.get('backupSettings') or {}).get('lastBackupAt', '')), 'detail': (state.get('backupSettings') or {}).get('lastBackupAt', 'Backup recommended')}
    ]

    two_system_control = flow_status

    summary = {
        'firebase': {'status': 'success', 'url': get_firebase_url(), 'lastCheckedAt': _now_iso_local()},
        'gateway': gateway,
        'gatewayResults': gateway_results,
        'gatewayTargets': gateway_targets,
        'waLogin': wa_login,
        'modules': {
            'autoScrape': rs.get('autoScrapeEnabled', True),
            'entryParser': (state.get('entrySettings') or {}).get('entryParserEnabled', True),
            'marketTiming': (state.get('entrySettings') or {}).get('marketTimingEnabled', True),
            'riskLimits': (state.get('entrySettings') or {}).get('riskLimitEnabled', True),
            'settlement': (state.get('settlementSettings') or {}).get('enabled', True),
            'paymentAutomation': (state.get('paymentSettings') or {}).get('paymentAutomationEnabled', True),
            'loadForwarder': lf.get('enabled', False),
            'spamGuard': (state.get('spamGuardSettings') or {}).get('enabled', True)
        },
        'counts': {
            'profiles': len(state.get('profiles', {}) or {}),
            'wallets': len(state.get('wallets', {}) or {}),
            'acceptedEntriesToday': len(today_entries),
            'todayLoad': round(today_load, 2),
            'paymentsPending': len([p for p in payments if isinstance(p, dict) and p.get('status') == 'pending']),
            'paymentOutboxPending': _count_pending(payment_outbox),
            'loadForwardOutboxPending': _count_pending(load_outbox),
            'settlementsToday': len(settlements_today or {}),
            'resultMarketsToday': len(result_records_today or {}),
            'resultTargets': len(state.get('resultTargets', []) or []),
            'auditEvents': len(audit),
            'guardEvents': len(state.get('spamGuardEvents', []) or []) if isinstance(state.get('spamGuardEvents', []), list) else 0
        },
        'professional': {
            'flowStatus': flow_status,
            'actionPlan': action_plan,
            'riskSummary': risk_summary,
            'systems': two_system_control
        },
        'last': {
            'backupAt': (state.get('backupSettings') or {}).get('lastBackupAt', ''),
            'audit': audit[-1] if audit else None,
            'loadForwarder': {'scheduleTime': lf.get('scheduleTime', ''), 'lastSentAt': lf.get('lastSentAt', ''), 'lastSentKey': lf.get('lastSentKey', '')},
            'recentResultMarkets': list((result_records_today or {}).keys())[-8:],
            'recentFirebaseResults': _health_recent_result_updates(state, today),
            'guardReasonLabels': {
                'fresh_open_missing': _health_label_guard_reason('fresh_open_missing'),
                'close_open_mismatch': _health_label_guard_reason('close_open_mismatch'),
                'invalid_format': _health_label_guard_reason('invalid_format'),
                'stale_candidate': _health_label_guard_reason('stale_candidate')
            }
        }
    }
    return jsonify({'status': 'success', 'health': summary})

@app.route('/api/backup_audit')
def api_backup_audit():
    state = migrate_and_get_state()
    audit = state.get('auditLog', []) if isinstance(state.get('auditLog', []), list) else []
    return jsonify({
        'status': 'success',
        'summary': _backup_summary(state),
        'auditLog': list(reversed(audit[-200:])),
        'exports': ['entries', 'wallets', 'wallet_ledger', 'payments', 'settlements', 'audit']
    })

@app.route('/api/export_csv')
def api_export_csv():
    kind = request.args.get('kind') or 'entries'
    state = migrate_and_get_state()
    name, headers, rows = _csv_export_spec(kind, state)
    if not name:
        return jsonify({'status': 'error', 'message': 'Invalid export kind'}), 400
    date = _safe_today()
    return _csv_response(f'titan_{name}_{date}.csv', headers, rows)

@app.route('/api/download_backup')
def api_download_backup():
    state = migrate_and_get_state()
    _ensure_foundation_state(state)
    date = _safe_today()
    state.setdefault('backupSettings', {})['lastBackupAt'] = _now_iso_local()
    _add_audit(state, 'manual_backup_download', {'date': date})
    save_to_firebase(state)
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('state.json', json.dumps(state, ensure_ascii=False, indent=2))
        for kind in ['entries', 'wallets', 'wallet_ledger', 'payments', 'settlements', 'audit']:
            name, headers, rows = _csv_export_spec(kind, state)
            zf.writestr(f'{name}.csv', _csv_bytes(headers, rows))
        zf.writestr('README.txt', 'Titan Nova backup export. Restore carefully: state.json contains the full Firebase app state. CSV files are for audit/review.\n')
    mem.seek(0)
    return app.response_class(
        mem.read(),
        mimetype='application/zip',
        headers={'Content-Disposition': f'attachment; filename="titan_backup_{date}.zip"'}
    )

@app.route('/api/clear_audit_log', methods=['POST'])
def api_clear_audit_log():
    state = migrate_and_get_state()
    state['auditLog'] = []
    _add_audit(state, 'audit_log_cleared', {'time': _now_iso_local()})
    save_to_firebase(state)
    return jsonify({'status': 'success', 'auditLog': state.get('auditLog', []), 'summary': _backup_summary(state)})

# ==========================================================
# TITAN NOVA BAILEYS GATEWAY / AUTO-SCHEDULE API
# These routes keep the app stable even if the Node bot reads Firebase directly.
# ==========================================================
def _safe_today():
    if ZoneInfo:
        try:
            return datetime.datetime.now(ZoneInfo(APP_TZ)).date().isoformat()
        except Exception:
            pass
    return datetime.datetime.now().date().isoformat()

def _digits_display(v):
    if not v:
        return ""
    parts = [x.strip() for x in str(v).replace("|", ",").replace(" ", ",").split(",") if x.strip()]
    return ",".join(parts)

def _normalize_schedule_time(v):
    txt = str(v or "").strip()
    parts = txt.split(":")
    if len(parts) < 2:
        return ""
    try:
        h, m = int(parts[0]), int(parts[1])
    except Exception:
        return ""
    if h < 0 or h > 23 or m < 0 or m > 59:
        return ""
    return f"{h:02d}:{m:02d}"

def _market_name_for_schedule(t, idx):
    try:
        idx = int(idx)
    except Exception:
        return ""
    if t == "jodi":
        return BASE_MARKETS[idx]["n"] if 0 <= idx < len(BASE_MARKETS) else ""
    return MARKETS[idx]["n"] if 0 <= idx < len(MARKETS) else ""

def _collect_bot_schedule(state_obj=None):
    state_obj = state_obj or migrate_and_get_state()
    today = _safe_today()
    result = []
    profiles = state_obj.get("profiles", {}) if isinstance(state_obj, dict) else {}
    for profile_id, profile in profiles.items():
        day_records = profile.get("dayRecords", {}) if isinstance(profile, dict) else {}
        today_rec = day_records.get(today, {}) or {}
        maps = [("ank", "data"), ("jodi", "jodiData"), ("pannel", "pannelData")]
        for typ, key in maps:
            data_map = today_rec.get(key, {}) or {}
            for idx, rec in data_map.items():
                if not isinstance(rec, dict):
                    continue
                sch_time = _normalize_schedule_time(rec.get("schTime") or rec.get("scheduleTime") or "")
                targets = rec.get("schTargets") or rec.get("targets") or []
                if isinstance(targets, str):
                    targets = [x.strip() for x in targets.replace("\n", ",").split(",") if x.strip()]
                digits = _digits_display(rec.get("d", ""))
                if not sch_time or not targets or not digits:
                    continue
                market_name = _market_name_for_schedule(typ, idx)
                if not market_name:
                    continue
                result.append({
                    "id": f"{profile_id}_{today}_{typ}_{idx}",
                    "profileId": profile_id,
                    "date": today,
                    "type": typ,
                    "index": int(idx),
                    "time": sch_time,
                    "market": market_name,
                    "digits": digits,
                    "targets": targets,
                    "message": f"🚀 *TITAN NOVA INTEL* [{today}]\n━━━━━━━━━━━━━━━━━━━━\n🔥 *MARKET:* {market_name}\n🔢 *DIGITS:* [{digits}]\n━━━━━━━━━━━━━━━━━━━━"
                })
    return result

@app.route('/api/bot_schedule')
def api_bot_schedule():
    try:
        return jsonify({"status": "success", "date": _safe_today(), "timezone": APP_TZ, "schedules": _collect_bot_schedule()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e), "schedules": []}), 500

@app.route('/bot_schedule')
def bot_schedule_alias():
    return api_bot_schedule()

@app.route('/api/schedule_targets', methods=['POST'])
def api_schedule_targets():
    data = request.json or {}
    profile_id = data.get('profileId') or 'admin1'
    typ = data.get('type')
    idx = str(data.get('index'))
    sch_time = _normalize_schedule_time(data.get('time') or '')
    targets = data.get('targets') or []
    if isinstance(targets, str):
        targets = [x.strip() for x in targets.replace('\n', ',').split(',') if x.strip()]
    dict_name = 'data' if typ == 'ank' else ('jodiData' if typ == 'jodi' else 'pannelData')
    state_obj = migrate_and_get_state()
    if profile_id not in state_obj.get('profiles', {}):
        return jsonify({'status': 'error', 'message': 'profile not found'}), 404
    prof = state_obj['profiles'][profile_id]
    today = _safe_today()
    prof.setdefault('dayRecords', {}).setdefault(today, {})
    prof['dayRecords'][today].setdefault(dict_name, {})
    prof['dayRecords'][today][dict_name].setdefault(idx, {'s':'WAIT','d':'','r':''})
    rec = prof['dayRecords'][today][dict_name][idx]
    incoming_rec = data.get('record') or {}
    if isinstance(incoming_rec, dict):
        # Keep digits/rate/status/trick together with schedule so Gateway never skips due to missing digits.
        for k, v in incoming_rec.items():
            if k not in ('__proto__', 'constructor', 'prototype'):
                rec[k] = v
    rec['schTime'] = sch_time
    rec['schTargets'] = targets
    save_to_firebase(state_obj)
    return jsonify({'status': 'success'})

@app.route('/api/wa_targets')
def api_wa_targets():
    # Proxy to local Baileys Gateway if running. App still works if gateway is off.
    try:
        res = requests.get('http://127.0.0.1:3000/targets?force=1', timeout=6)
        return jsonify(res.json())
    except Exception as e:
        return jsonify({'status': 'offline', 'contacts': [], 'groups': [], 'message': str(e)})


@app.route('/api/wa_login_status')
def api_wa_login_status():
    try:
        res = requests.get('http://127.0.0.1:3000/wa_login_status', timeout=5)
        return jsonify(res.json()), res.status_code
    except Exception as e:
        return jsonify({'status': 'offline', 'connected': False, 'qrAvailable': False, 'message': str(e)}), 503

@app.route('/api/wa_reset_session', methods=['POST'])
def api_wa_reset_session():
    try:
        res = requests.post('http://127.0.0.1:3000/wa_reset_session', timeout=10)
        return jsonify(res.json()), res.status_code
    except Exception as e:
        return jsonify({'status': 'offline', 'message': str(e)}), 503

@app.route('/api/wa_qr_image')
def api_wa_qr_image():
    try:
        import urllib.parse
        res = requests.get('http://127.0.0.1:3000/wa_login_status', timeout=5)
        data = res.json()
        qr = str(data.get('qr') or '')
        if not qr:
            return app.response_class('QR not available yet. Refresh or reset WhatsApp session.', mimetype='text/plain'), 404
        url = 'https://api.qrserver.com/v1/create-qr-code/?size=280x280&data=' + urllib.parse.quote(qr)
        return app.redirect(url)
    except Exception as e:
        return app.response_class('QR error: ' + str(e), mimetype='text/plain'), 503

@app.route('/api/gateway_status')
def api_gateway_status():
    try:
        res = requests.get('http://127.0.0.1:3000/status', timeout=5)
        return jsonify(res.json())
    except Exception as e:
        return jsonify({'status': 'offline', 'connected': False, 'message': str(e), 'timezone': APP_TZ})

@app.route('/api/gateway_scrape_results')
def api_gateway_scrape_results():
    # Manual trigger for Gateway auto-result scraper. Gateway still scrapes automatically on interval.
    try:
        res = requests.get('http://127.0.0.1:3000/scrape_results', timeout=30)
        return jsonify(res.json()), res.status_code
    except Exception as e:
        return jsonify({'status': 'offline', 'message': str(e), 'updates': [], 'scraped': []}), 503

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <meta name="theme-color" content="#2AABEE">

    <link rel="manifest" href="{{ manifest_url }}">
    <link rel="apple-touch-icon" href="/icon.svg">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="Titan Nova">
    <meta name="mobile-web-app-capable" content="yes">

    <title>TITAN NOVA</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.tailwindcss.com"></script>

    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

        :root {
            --app-bg:       #17212B;
            --surface:      #232E3C;
            --surface-light:#2B3A4D;
            --surface-mid:  #374F65;
            --primary:      #2AABEE;
            --primary-glow: rgba(42,171,238,0.20);
            --primary-dark: #1A8FC4;
            --green:        #00C26F;
            --green-dark:   #00A05E;
            --green-glow:   rgba(0,194,111,0.18);
            --cyan:         #2AABEE;
            --cyan-glow:    rgba(42,171,238,0.18);
            --rose:         #FF5D5D;
            --rose-glow:    rgba(255,93,93,0.18);
            --purple:       #7B8FFF;
            --purple-glow:  rgba(123,143,255,0.18);
            --amber:        #FAC748;
            --text-main:    #FFFFFF;
            --text-muted:   #7A9CB8;
            --border:       rgba(255,255,255,0.07);
            --radius-lg:    16px;
            --radius-md:    12px;
            --radius-sm:    8px;
            --header-h:     56px;
        }

        * { box-sizing: border-box; }
        body {
            background: var(--app-bg);
            color: var(--text-main);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            -webkit-tap-highlight-color: transparent;
            -webkit-user-select: none; user-select: none;
            overscroll-behavior-y: contain;
            padding-bottom: 88px;
        }
        input, textarea { -webkit-user-select: auto; user-select: auto; }
        .no-scrollbar::-webkit-scrollbar { display: none; }

        /* ── CARDS ── */
        .native-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            margin-bottom: 8px;
            overflow: hidden;
            transition: transform 0.1s ease;
        }

        /* ── INPUTS ── */
        .native-input {
            background: var(--surface-light);
            border: 1.5px solid var(--surface-mid);
            color: var(--text-main);
            border-radius: var(--radius-md);
            text-align: center;
            font-weight: 700;
            padding: 13px 12px;
            outline: none;
            width: 100%;
            font-size: 16px;
            transition: 0.2s;
            font-family: inherit;
        }
        .native-input:focus { border-color: var(--primary); box-shadow: 0 0 0 3px var(--primary-glow); }
        .native-input::placeholder { color: var(--text-muted); font-weight: 500; }

        /* ── STATS HUD ── */
        .wallet-hud {
            display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px;
            padding: 12px 14px;
            background: var(--surface);
            border-bottom: 1px solid var(--border);
        }
        .stat-box {
            background: var(--surface-light);
            border-radius: var(--radius-sm);
            padding: 10px 12px;
            border: 1px solid var(--border);
        }

        /* ── APP BAR ── */
        .app-bar {
            position: sticky; top: 0; z-index: 50;
            background: #1C2733;
            border-bottom: 1px solid rgba(42,171,238,0.15);
            height: var(--header-h);
            padding: 0 12px;
            display: flex; align-items: center; justify-content: space-between;
        }

        /* ── BOTTOM NAV — scrollable native tab rail ── */
        .bottom-nav {
            position: fixed; bottom: 0; left: 0; width: 100%;
            background: #1C2733;
            border-top: 1px solid rgba(255,255,255,0.06);
            display: flex; justify-content: flex-start; align-items: stretch;
            gap: 4px;
            padding: 6px 8px env(safe-area-inset-bottom, 8px);
            z-index: 100; height: 76px;
            overflow-x: auto; overflow-y: hidden;
            scrollbar-width: none;
            -webkit-overflow-scrolling: touch;
            scroll-snap-type: x proximity;
        }
        .bottom-nav::-webkit-scrollbar { display: none; }
        .nav-item {
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            color: var(--text-muted); font-size: 8.5px; font-weight: 700;
            text-transform: uppercase; padding: 4px 8px; border-radius: 10px;
            transition: 0.2s; min-width: 62px; flex: 0 0 62px; letter-spacing: 0.02em;
            position: relative; scroll-snap-align: center;
            white-space: nowrap;
        }
        .nav-item i { font-size: 18px; margin-bottom: 3px; transition: 0.2s; }
        @media (max-width: 380px) {
            .nav-item { min-width: 58px; flex-basis: 58px; font-size: 8px; padding-left: 6px; padding-right: 6px; }
            .nav-item i { font-size: 17px; }
        }
        .nav-item.active { color: var(--primary); }
        .nav-item.active i { filter: drop-shadow(0 0 6px rgba(42,171,238,0.5)); }
        .nav-item.active::after {
            content: '';
            position: absolute;
            top: 0; left: 50%; transform: translateX(-50%);
            width: 32px; height: 3px;
            background: var(--primary);
            border-radius: 0 0 4px 4px;
        }

        /* ── PILL TABS ── */
        .pill-tabs {
            display: flex; background: var(--surface); padding: 4px 14px; gap: 6px;
            border-bottom: 1px solid var(--border);
            overflow-x: auto; scrollbar-width: none;
        }
        .pill-tab {
            flex: 1; text-align: center; padding: 8px 0; font-size: 11px;
            font-weight: 700; text-transform: uppercase; color: var(--text-muted);
            border-radius: 8px; transition: 0.2s; white-space: nowrap;
            border-bottom: 2px solid transparent;
        }
        .pill-tab.active { color: var(--primary); border-bottom-color: var(--primary); background: rgba(42,171,238,0.08); }
        .pill-btn {
            background: var(--surface-light); border: 1px solid var(--surface-mid);
            color: var(--text-muted); border-radius: 20px; padding: 7px 18px;
            font-size: 11px; font-weight: 700; text-transform: uppercase; transition: 0.2s;
            font-family: inherit;
        }
        .pill-btn.active { background: var(--primary); color: #fff; border-color: var(--primary); box-shadow: 0 4px 12px var(--primary-glow); }

        /* ── PAY PLAN CARDS ── */
        .plan-card-wrap { border-radius: var(--radius-lg); padding: 1.5px; }
        .plan-card-inner { background: var(--surface); border-radius: calc(var(--radius-lg) - 1.5px); padding: 16px; }
        .plan-card-wrap.selected { background: linear-gradient(135deg, var(--primary), var(--green)); }
        .plan-card-wrap:not(.selected) { background: var(--surface-light); }

        /* ── BOTTOM SHEET ── */
        .bottom-sheet {
            position: fixed; inset: 0; z-index: 9001;
            background: rgba(0,0,0,0.6); backdrop-filter: blur(4px);
            display: flex; flex-direction: column; justify-content: flex-end;
            opacity: 0; pointer-events: none; transition: opacity 0.25s ease;
        }
        .bottom-sheet.open { opacity: 1; pointer-events: auto; }
        .sheet-content {
            background: #1C2733;
            border-top-left-radius: 20px; border-top-right-radius: 20px;
            padding: 20px; padding-bottom: calc(20px + env(safe-area-inset-bottom, 0px));
            transform: translateY(100%); transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1);
            border-top: 1px solid rgba(42,171,238,0.2); max-height: 85vh; overflow-y: auto;
        }
        .bottom-sheet.open .sheet-content { transform: translateY(0); }
        .sheet-handle { width: 36px; height: 4px; background: rgba(255,255,255,0.15); border-radius: 10px; margin: 0 auto 18px auto; }

        /* ── TOGGLE SWITCH ── */
        .switch { position: relative; display: inline-block; width: 36px; height: 20px; }
        .switch input { opacity: 0; width: 0; height: 0; }
        .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: var(--surface-mid); transition: .3s; border-radius: 20px; }
        .slider:before { position: absolute; content: ""; height: 16px; width: 16px; left: 2px; bottom: 2px; background-color: #fff; transition: .3s; border-radius: 50%; opacity: 0.5; }
        input:checked + .slider { background-color: var(--primary); }
        input:checked + .slider:before { opacity: 1; transform: translateX(16px); }

        /* ── SIDEBAR ── */
        #sidebar {
            position: fixed; top: 0; left: -300px; height: 100%; width: 280px;
            background: #1C2733; z-index: 1000;
            transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border-right: 1px solid rgba(42,171,238,0.15); overflow-y: auto;
        }
        #sidebar.open { left: 0; box-shadow: 10px 0 40px rgba(0,0,0,0.7); }
        .sidebar-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; padding: 12px; }
        .side-link-btn {
            display: block; background: var(--surface-light); color: var(--text-muted);
            border: 1px solid var(--border); font-size: 9px; font-weight: 700;
            padding: 10px; border-radius: 10px; text-transform: uppercase; text-align: center;
            font-family: inherit;
        }

        /* ── TOAST — Telegram Style ── */
        .tg-toast {
            background: #2B3A4D;
            border: 1px solid rgba(42,171,238,0.25);
            border-radius: 14px;
            padding: 12px 14px;
            display: flex; align-items: center; gap: 10px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.5);
            transform: translateY(-120%) scale(0.96);
            opacity: 0;
            transition: all 0.35s cubic-bezier(0.175, 0.885, 0.32, 1.1);
            pointer-events: auto; cursor: pointer;
            min-width: 0;
        }
        .tg-toast.show { transform: translateY(0) scale(1); opacity: 1; }
        .tg-toast-icon {
            width: 36px; height: 36px; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 16px; flex-shrink: 0;
        }
        .tg-toast-icon.info  { background: rgba(42,171,238,0.2);  color: #2AABEE; }
        .tg-toast-icon.success { background: rgba(0,194,111,0.2); color: #00C26F; }
        .tg-toast-icon.danger  { background: rgba(255,93,93,0.2);  color: #FF5D5D; }
        .tg-toast-body h4 { font-size: 13px; font-weight: 700; color: #fff; margin: 0 0 2px; line-height: 1.3; }
        .tg-toast-body p  { font-size: 11px; color: var(--text-muted); margin: 0; line-height: 1.4; }

        /* ── INSTALL MODAL ── */
        .install-modal {
            position: fixed; inset: 0; z-index: 9500;
            background: rgba(0,0,0,0.75); backdrop-filter: blur(6px);
            display: flex; align-items: flex-end;
            opacity: 0; pointer-events: none; transition: opacity 0.3s;
        }
        .install-modal.open { opacity: 1; pointer-events: auto; }
        .install-modal-content {
            background: #1C2733; width: 100%;
            border-top-left-radius: 20px; border-top-right-radius: 20px;
            padding: 24px; padding-bottom: calc(24px + env(safe-area-inset-bottom, 0px));
            border-top: 2px solid var(--primary);
            transform: translateY(100%); transition: transform 0.35s cubic-bezier(0.175, 0.885, 0.32, 1);
        }
        .install-modal.open .install-modal-content { transform: translateY(0); }

        /* ── SECTION HEADER ── */
        .sec-header {
            font-size: 11px; font-weight: 700; color: var(--text-muted);
            text-transform: uppercase; letter-spacing: 0.06em;
            padding: 14px 14px 8px; display: flex; justify-content: space-between; align-items: center;
        }

        /* ── SCROLLBAR FIX ── */
        .pill-tabs::-webkit-scrollbar { display: none; }

        /* ── STAT LABEL ── */
        .stat-lbl { font-size: 9px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); margin-bottom: 4px; }
        .stat-val  { font-size: 15px; font-weight: 800; }
    </style>
</head>
<body>
    <!-- Toast Container -->
    <div id="push-container" class="fixed top-3 left-1/2 -translate-x-1/2 w-[92%] max-w-sm z-[9999] pointer-events-none flex flex-col gap-2"></div>

    <!-- PWA Install Banner — shows when Android prompt is available -->
    <div id="pwa-install-banner" class="fixed top-[calc(var(--header-h)+8px)] left-1/2 -translate-x-1/2 z-[100] hidden w-[92%] max-w-sm pointer-events-auto">
        <div class="flex items-center gap-3 bg-[#1A3348] border border-[var(--primary)] rounded-2xl px-4 py-3 shadow-lg shadow-[rgba(42,171,238,0.2)]">
            <div class="w-10 h-10 rounded-xl bg-[var(--primary)] flex items-center justify-center shrink-0">
                <i class="fas fa-mobile-alt text-white text-lg"></i>
            </div>
            <div class="flex-1 min-w-0">
                <p class="text-white font-bold text-[13px] leading-tight">App Install Karein</p>
                <p class="text-[var(--text-muted)] text-[10px]">Faster, offline-ready experience</p>
            </div>
            <button onclick="installPWA()" class="bg-[var(--primary)] text-white px-4 py-2 rounded-xl font-bold text-[11px] uppercase shrink-0 active:scale-95 transition-transform">
                Install
            </button>
            <button onclick="document.getElementById('pwa-install-banner').classList.add('hidden')" class="text-[var(--text-muted)] w-6 h-6 flex items-center justify-center shrink-0 text-xs">
                <i class="fas fa-times"></i>
            </button>
        </div>
    </div>

    <!-- Manual Install Guide Modal -->
    <div id="install-modal" class="install-modal" onclick="if(event.target===this)closeInstallModal()">
        <div class="install-modal-content">
            <div class="flex items-center gap-3 mb-5">
                <div class="w-12 h-12 rounded-2xl bg-[var(--primary)] flex items-center justify-center text-white text-xl">
                    <i class="fas fa-download"></i>
                </div>
                <div>
                    <h3 class="text-white font-black text-base">App Install Karein</h3>
                    <p class="text-[var(--text-muted)] text-[11px]">Android pe Home Screen add karein</p>
                </div>
            </div>

            <div id="auto-install-section" class="hidden mb-4">
                <button onclick="installPWA()" class="w-full bg-[var(--primary)] text-white py-4 rounded-2xl font-black text-[13px] uppercase tracking-wide active:scale-95 transition-transform shadow-lg shadow-[rgba(42,171,238,0.3)]">
                    <i class="fas fa-download mr-2"></i> Abhi Install Karein
                </button>
                <p class="text-[var(--text-muted)] text-[10px] text-center mt-2">Ya neeche manual steps follow karein</p>
            </div>

            <div class="space-y-3">
                <div class="flex items-start gap-3 bg-[var(--surface-light)] p-3 rounded-xl border border-[var(--border)]">
                    <div class="w-7 h-7 rounded-full bg-[var(--primary)] text-white text-[11px] font-black flex items-center justify-center shrink-0 mt-0.5">1</div>
                    <div>
                        <p class="text-white font-bold text-[12px]">Chrome Browser Mein Kholo</p>
                        <p class="text-[var(--text-muted)] text-[10px] mt-0.5">Google Chrome mein yeh page open karo</p>
                    </div>
                </div>
                <div class="flex items-start gap-3 bg-[var(--surface-light)] p-3 rounded-xl border border-[var(--border)]">
                    <div class="w-7 h-7 rounded-full bg-[var(--primary)] text-white text-[11px] font-black flex items-center justify-center shrink-0 mt-0.5">2</div>
                    <div>
                        <p class="text-white font-bold text-[12px]">3 Dots Menu Tap Karein</p>
                        <p class="text-[var(--text-muted)] text-[10px] mt-0.5">Browser ke top-right mein ⋮ icon</p>
                    </div>
                </div>
                <div class="flex items-start gap-3 bg-[var(--surface-light)] p-3 rounded-xl border border-[var(--border)]">
                    <div class="w-7 h-7 rounded-full bg-[var(--primary)] text-white text-[11px] font-black flex items-center justify-center shrink-0 mt-0.5">3</div>
                    <div>
                        <p class="text-white font-bold text-[12px]">"Add to Home Screen" Choose Karein</p>
                        <p class="text-[var(--text-muted)] text-[10px] mt-0.5">Menu mein se yeh option select karo</p>
                    </div>
                </div>
                <div class="flex items-start gap-3 bg-[var(--surface-light)] p-3 rounded-xl border border-[var(--border)]">
                    <div class="w-7 h-7 rounded-full bg-[var(--green)] text-white text-[11px] font-black flex items-center justify-center shrink-0 mt-0.5"><i class="fas fa-check text-[9px]"></i></div>
                    <div>
                        <p class="text-white font-bold text-[12px]">"Add" pe Tap Karein</p>
                        <p class="text-[var(--text-muted)] text-[10px] mt-0.5">App Home Screen par install ho jayega!</p>
                    </div>
                </div>
            </div>

            <button onclick="closeInstallModal()" class="mt-5 w-full py-4 rounded-2xl font-bold text-[13px] text-[var(--text-muted)] border border-[var(--border)] active:scale-95 transition-transform">
                Samajh Gaya, Close Karein
            </button>
        </div>
    </div>

    <div id="sidebar-overlay" onclick="toggleSidebar()" class="fixed inset-0 bg-black/70 z-[999] hidden backdrop-blur-sm"></div>
    <div id="sidebar">
        <div class="p-5 border-b border-[rgba(42,171,238,0.15)]">
            <div class="flex items-center gap-3 mb-4">
                <div class="w-10 h-10 rounded-xl bg-[var(--primary)] flex items-center justify-center text-white font-black text-lg">T</div>
                <div>
                    <h2 class="text-white font-black text-base">TITAN NOVA</h2>
                    <p class="text-[var(--text-muted)] text-[10px]">Charts & Live Database</p>
                </div>
            </div>
            <button id="sidebar-install-btn" onclick="showInstallModal()" class="w-full bg-[rgba(42,171,238,0.15)] text-[var(--primary)] py-3 rounded-xl font-bold text-[11px] uppercase tracking-wide border border-[rgba(42,171,238,0.3)] flex items-center justify-center gap-2 active:scale-95 transition-transform">
                <i class="fas fa-download"></i> Install App
            </button>
        </div>
        <div id="sidebar-links-container" class="sidebar-grid"></div>
    </div>

    <div id="top-bar-container" class="app-bar"></div>
    <main id="screen-content"></main>
    <div id="bottom-nav-container" class="bottom-nav"></div>

    <div id="shareModal" class="bottom-sheet" onclick="if(event.target===this) closeShareModal()">
        <div class="sheet-content">
            <div class="sheet-handle"></div>
            <h4 class="text-white font-black uppercase text-[12px] mb-5 tracking-widest text-center">Dispatch Destination</h4>
            <div id="modal-client-list" class="max-h-64 overflow-y-auto flex flex-col no-scrollbar mb-5"></div>
            <button onclick="closeShareModal()" class="text-[var(--rose)] font-bold text-[12px] uppercase block mx-auto py-3.5 w-full bg-[rgba(255,93,93,0.1)] rounded-xl border border-[rgba(255,93,93,0.2)] active:scale-95 transition-all">Cancel</button>
        </div>
    </div>

    <script>
        // ==========================================
        // IMGBB FREE IMAGE UPLOAD SETUP
        // ==========================================
        const IMGBB_API_KEY = "9f04735b90825ed61aa6f5d97dee417a";
        // ==========================================

        // ── PWA / SERVICE WORKER ──
        if ('serviceWorker' in navigator) { navigator.serviceWorker.register('/sw.js').catch(()=>{}); }
        let deferredPrompt;

        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            const floatBanner = document.getElementById('pwa-install-banner');
            const autoSection = document.getElementById('auto-install-section');
            if(floatBanner) floatBanner.classList.remove('hidden');
            if(autoSection) autoSection.classList.remove('hidden');
        });

        function installPWA() {
            if (deferredPrompt) {
                deferredPrompt.prompt();
                deferredPrompt.userChoice.then((choiceResult) => {
                    if (choiceResult.outcome === 'accepted') {
                        showRealNotification('✅ Install Successful!', 'App aapke home screen par add ho gaya hai!', 'success');
                        document.getElementById('pwa-install-banner').classList.add('hidden');
                    }
                    deferredPrompt = null;
                });
            } else {
                showInstallModal();
            }
        }

        function showInstallModal() {
            document.getElementById('install-modal').classList.add('open');
        }
        function closeInstallModal() {
            document.getElementById('install-modal').classList.remove('open');
        }

        const IS_MASTER = {{ 'true' if is_master else 'false' }};
        let appState = {{ state | tojson }};
        const chartLinks = {{ chartLinks | tojson }};

        const LOCAL_KEY = IS_MASTER ? 'TITAN_NOVA_None' : 'TITAN_NOVA_VIP_' + appState.activeId;

        // SERVER FIRST SYNC (PythonAnywhere/Firebase source of truth)
        fetch('/api/state')
            .then(r => r.json())
            .then(serverState => {
                appState = serverState; appState.activeId = 'admin1';
                localStorage.setItem(LOCAL_KEY, JSON.stringify(serverState));
                state = appState.profiles[appState.activeId] || appState.profiles['admin1'];
                render(true);
            })
            .catch(() => {
                let cached = localStorage.getItem(LOCAL_KEY);
                if(cached) {
                    try {
                        const parsed = JSON.parse(cached);
                        if(parsed.activeId === appState.activeId) appState = parsed;
                    } catch(e) {}
                }
            });

        let state = appState.profiles[appState.activeId];
        if(!state){
            appState.activeId = "admin1";
            state = appState.profiles["admin1"];
        }
        const markets = {{ markets | tojson }};
        const baseMarkets = {{ baseMarkets | tojson }};

        let mainNav = 'ledger';
        let activeTab = 'ank';
        let weeklyTabType = 'ank';

        function titanLocalDateISO(){
            const d = new Date();
            const y = d.getFullYear();
            const m = String(d.getMonth()+1).padStart(2,'0');
            const day = String(d.getDate()).padStart(2,'0');
            return `${y}-${m}-${day}`;
        }
        let currentDate = titanLocalDateISO();
        let currentMsg = ""; let selectedPhone = "";
        let globalStats = { ank: { spent: 0, win: 0, pl: 0, port: 0, maxLoss: 0 }, jodi: { spent: 0, win: 0, pl: 0, port: 0, maxLoss: 0 }, pannel: { spent: 0, win: 0, pl: 0, port: 0, maxLoss: 0 } };

        let autoSyncTimer;
        function autoSave() { clearTimeout(autoSyncTimer); autoSyncTimer = setTimeout(() => { saveMaster(true); }, 500); }

        // ── HARDCODED UPI IDs (per payment app) ──
        const HARDCODED_UPIS = {
            phonepe: '7077550644@ybl',
            gpay:    'kirannaik93244-4@okhdfcbank',
            paytm:   '7077550644@ptsbi'
        };
        const HARDCODED_NAME = 'TITAN NOVA';

        window.shareModalOpen = false;
        function pushNativeState() { history.pushState({nova: true}, '', window.location.href); }

        window.addEventListener("popstate", function(e) {
            if (window.shareModalOpen) { closeShareModal(true); }
            else if (IS_MASTER && appState.activeId !== 'admin1') { appState.activeId = 'admin1'; state = appState.profiles['admin1']; setMainNav('clients'); }
            else if (mainNav !== 'ledger') { setMainNav('ledger'); }
        });

        function backToMasterUI() {
            if (!IS_MASTER) return;
            if (window.history.state && window.history.state.nova) { history.back(); }
            else { appState.activeId = 'admin1'; state = appState.profiles['admin1']; setMainNav('clients'); }
        }

        function closeShareModal(fromHistory = false) {
            document.getElementById('shareModal').classList.remove('open');
            window.shareModalOpen = false;
            if(!fromHistory) { if(window.history.state && window.history.state.nova) history.back(); }
        }

        function requestNotificationPermission() {
            if (!("Notification" in window)) {
                showRealNotification('⚠️ Not Supported', 'Aapka phone notifications support nahi karta.', 'danger');
                return;
            }
            if (Notification.permission !== "granted" && Notification.permission !== "denied") {
                Notification.requestPermission().then(permission => {
                    if (permission === "granted") {
                        showRealNotification('✅ Notifications ON!', 'Ab aapko phone par direct alerts milenge!', 'success');
                        renderAppBar();
                    } else {
                        showRealNotification('❌ Permission Denied', 'Notifications allow nahi kiye gaye.', 'danger');
                    }
                });
            } else if (Notification.permission === "granted") {
                showRealNotification('🔔 Already Active', 'Native Notifications pehle se on hain.', 'success');
            } else {
                showRealNotification('⚠️ Blocked', 'Browser settings mein notifications allow karein.', 'danger');
            }
        }

        function showRealNotification(title, body, type='info') {
            const container = document.getElementById('push-container');
            const toast = document.createElement('div');
            toast.className = 'tg-toast';

            const icons = {
                info:    { icon: 'fa-bullhorn',            cls: 'info'    },
                success: { icon: 'fa-check',               cls: 'success' },
                danger:  { icon: 'fa-exclamation-triangle', cls: 'danger'  }
            };
            const ic = icons[type] || icons.info;

            toast.innerHTML = `
                <div class="tg-toast-icon ${ic.cls}"><i class="fas ${ic.icon}"></i></div>
                <div class="tg-toast-body flex-1 min-w-0">
                    <h4>${title}</h4>
                    <p>${body}</p>
                </div>
                <button onclick="this.parentElement.classList.remove('show');setTimeout(()=>this.parentElement.remove(),350)" class="text-[var(--text-muted)] text-xs w-5 h-5 flex items-center justify-center shrink-0 opacity-60">
                    <i class="fas fa-times"></i>
                </button>`;

            toast.onclick = (e) => {
                if(e.target.closest('button')) return;
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 350);
            };

            container.appendChild(toast);
            setTimeout(() => toast.classList.add('show'), 10);
            setTimeout(() => { if(toast.parentElement) { toast.classList.remove('show'); setTimeout(() => toast.remove(), 350); } }, 6000);

            if ("Notification" in window && Notification.permission === "granted") {
                navigator.serviceWorker.ready.then((registration) => {
                    registration.showNotification(title, {
                        body: body,
                        icon: '/icon.svg',
                        badge: '/icon.svg',
                        vibrate: [150, 80, 150]
                    });
                }).catch(()=>{});
            }
        }

        function checkTargetsAndLimits() {
            if (IS_MASTER) return;
            ['ank', 'jodi', 'pannel'].forEach(type => {
                let stats = globalStats[type];
                let cfg = state.config[type];
                let tgt = parseFloat(cfg.tgt) || 0;
                let cap = parseFloat(cfg.cap) || 0;

                let keyPrefix = `TITAN_ALERT_${appState.activeId}_${currentDate}_${type}`;

                if (tgt > 0 && stats.pl >= tgt) {
                    if (!localStorage.getItem(keyPrefix+'_tgt')) {
                        showRealNotification('🎯 Target Hit!', `Aapka ${type.toUpperCase()} ka target (₹${tgt}) pura ho gaya hai!`, 'success');
                        localStorage.setItem(keyPrefix+'_tgt', '1');
                    }
                }

                if (cap > 0 && stats.pl <= -cap) {
                    if (!localStorage.getItem(keyPrefix+'_cap')) {
                        showRealNotification('⚠️ Capital Risk!', `Dhyan de! Aapka ${type.toUpperCase()} ka loss limit (-₹${cap}) cross ho gaya hai.`, 'danger');
                        localStorage.setItem(keyPrefix+'_cap', '1');
                    }
                }
            });
        }

        // ==========================================
        // AUTO-SYNC FIX: STOP RENDER LOOP ON MEMBERSHIP TAB
        // ==========================================
        if (!IS_MASTER) {
            setInterval(async () => {
                try {
                    let res = await fetch('/api/state');
                    let newState = await res.json();

                    let lastBcast = parseInt(localStorage.getItem('TITAN_BCAST_LAST') || '0');
                    let maxId = lastBcast;
                    if(newState.broadcasts) {
                        newState.broadcasts.forEach(b => {
                            if(b.id > lastBcast) {
                                showRealNotification(b.title, b.msg, 'info');
                                if(b.id > maxId) maxId = b.id;
                            }
                        });
                    }
                    if(maxId > lastBcast) localStorage.setItem('TITAN_BCAST_LAST', maxId.toString());

                    if(newState.profiles && newState.profiles[appState.activeId]) {
                        function sortedStringify(obj) {
                            if (obj !== null && typeof obj === 'object') {
                                if (Array.isArray(obj)) return '[' + obj.map(sortedStringify).join(',') + ']';
                                return '{' + Object.keys(obj).sort().map(k => '"' + k + '":' + sortedStringify(obj[k])).join(',') + '}';
                            }
                            return JSON.stringify(obj);
                        }

                        let localRec = appState.profiles[appState.activeId].dayRecords[currentDate] || {};
                        let fetchedRec = newState.profiles[appState.activeId].dayRecords[currentDate] || {};
                        let currentLocalStateStr = sortedStringify(localRec);
                        let fetchedStateStr = sortedStringify(fetchedRec);

                        let currentAccess = appState.profiles[appState.activeId].vipAccessEnabled;
                        let fetchedAccess = newState.profiles[appState.activeId].vipAccessEnabled;

                        if (currentLocalStateStr !== fetchedStateStr || currentAccess !== fetchedAccess) {
                            appState = newState;
                            state = appState.profiles[appState.activeId];

                            // ── Save VIP state to localStorage (mobile offline support) ──
                            try { localStorage.setItem(LOCAL_KEY, JSON.stringify(appState)); } catch(e) {}

                            let activeTag = document.activeElement ? document.activeElement.tagName : '';
                            let isTyping = (activeTag === 'INPUT' || activeTag === 'TEXTAREA');
                            let isSafeTab = (mainNav === 'ledger' || mainNav === 'audit');

                            if (isSafeTab && !isTyping) {
                                render(true);
                            }
                        } else {
                            // Always update payments + broadcasts in localStorage even if ledger didn't change
                            appState.payments = (newState.payments || []).filter(p => p.userId === appState.activeId);
                            appState.broadcasts = newState.broadcasts || [];
                            try { localStorage.setItem(LOCAL_KEY, JSON.stringify(appState)); } catch(e) {}
                        }
                    }
                } catch(e) {}
            }, 5000);
        }

        function showToast(msg, color='blue') {
            const typeMap = { blue:'info', green:'success', cyan:'info', rose:'danger', red:'danger', emerald:'success' };
            showRealNotification('Titan Nova', msg, typeMap[color] || 'info');
        }


        // ==========================================
        // WALLET FOUNDATION UI HELPERS
        // ==========================================
        function ensureWalletStruct(){
            if(!appState.wallets) appState.wallets = {};
            if(!appState.walletSettings) appState.walletSettings = {defaultCreditLimit:0, requirePositiveBalance:false, walletEnabled:true, currency:'₹'};
        }
        function walletCurrency(){ ensureWalletStruct(); return appState.walletSettings.currency || '₹'; }
        function fmtMoney(v){
            const n = Number(v || 0);
            const clean = Number.isInteger(n) ? String(n) : n.toFixed(2);
            return walletCurrency() + clean;
        }
        function htmlEscape(v){
            return String(v == null ? '' : v)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#39;');
        }
        function attrEscape(v){ return htmlEscape(v); }
        function walletForUser(userId){
            ensureWalletStruct();
            const prof = (appState.profiles || {})[userId] || {};
            if(!appState.wallets[userId]) appState.wallets[userId] = {userId, name:prof.name || userId, phone:prof.phone || '', balance:0, creditLimit:Number(appState.walletSettings.defaultCreditLimit || 0), ledger:[]};
            if(!Array.isArray(appState.wallets[userId].ledger)) appState.wallets[userId].ledger = [];
            return appState.wallets[userId];
        }
        function walletClientIds(){
            return Object.keys(appState.profiles || {}).filter(id => !id.startsWith('admin'));
        }
        async function refreshWalletsState(){
            try{
                const res = await fetch('/api/wallets');
                const data = await res.json();
                if(data.status === 'success'){
                    appState.wallets = data.wallets || {};
                    appState.walletSettings = data.walletSettings || appState.walletSettings || {};
                }
            } catch(e) {}
        }
        async function walletAddSubtract(userId, action){
            if(!IS_MASTER) return;
            const label = action === 'subtract' ? 'Minus amount' : 'Add amount';
            const amountRaw = prompt(label + ' enter karo:');
            if(amountRaw === null) return;
            const amount = Number(String(amountRaw).replace(/[^0-9.]/g,''));
            if(!amount || amount <= 0){ showRealNotification('⚠️ Invalid Amount', 'Amount 0 se zyada hona chahiye.', 'danger'); return; }
            const note = prompt('Note optional:', action === 'subtract' ? 'Manual debit' : 'Manual credit') || '';
            try{
                const res = await fetch('/api/wallet_transaction', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({userId, action, amount, note})});
                const data = await res.json();
                if(data.status !== 'success') throw new Error(data.message || 'Wallet update failed');
                appState.wallets = data.wallets || appState.wallets;
                showRealNotification('✅ Wallet Updated', `${userId} ${action === 'subtract' ? 'debited' : 'credited'} ${fmtMoney(amount)}`, 'success');
                render(true);
            } catch(e){ showRealNotification('❌ Wallet Error', String(e.message || e), 'danger'); }
        }
        async function walletSetCredit(userId){
            if(!IS_MASTER) return;
            const w = walletForUser(userId);
            const raw = prompt('Credit limit set karo:', String(w.creditLimit || 0));
            if(raw === null) return;
            const creditLimit = Number(String(raw).replace(/[^0-9.]/g,''));
            if(creditLimit < 0 || Number.isNaN(creditLimit)){ showRealNotification('⚠️ Invalid Credit', 'Credit limit valid number hona chahiye.', 'danger'); return; }
            try{
                const res = await fetch('/api/wallet_credit_limit', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({userId, creditLimit})});
                const data = await res.json();
                if(data.status !== 'success') throw new Error(data.message || 'Credit update failed');
                appState.wallets = data.wallets || appState.wallets;
                showRealNotification('✅ Credit Limit Updated', `${userId}: ${fmtMoney(creditLimit)}`, 'success');
                render(true);
            } catch(e){ showRealNotification('❌ Credit Error', String(e.message || e), 'danger'); }
        }
        async function walletZeroSettle(userId){
            if(!IS_MASTER) return;
            const w = walletForUser(userId);
            if(!confirm(`Zero settle ${w.name || userId}? Current balance ${fmtMoney(w.balance || 0)} reset ho jayega.`)) return;
            try{
                const res = await fetch('/api/wallet_zero_settle', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({userId, note:'Zero settle from Wallet tab'})});
                const data = await res.json();
                if(data.status !== 'success') throw new Error(data.message || 'Zero settle failed');
                appState.wallets = data.wallets || appState.wallets;
                showRealNotification('✅ Zero Settled', `${userId} balance zero ho gaya.`, 'success');
                render(true);
            } catch(e){ showRealNotification('❌ Settle Error', String(e.message || e), 'danger'); }
        }
        async function saveWalletDefaultCredit(){
            if(!IS_MASTER) return;
            const raw = document.getElementById('wallet-default-credit')?.value || '0';
            const defaultCreditLimit = Number(String(raw).replace(/[^0-9.]/g,'')) || 0;
            try{
                const res = await fetch('/api/wallet_settings', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({defaultCreditLimit})});
                const data = await res.json();
                if(data.status !== 'success') throw new Error(data.message || 'Settings save failed');
                appState.walletSettings = data.walletSettings || appState.walletSettings;
                showRealNotification('✅ Wallet Settings Saved', 'New clients ke liye default credit update ho gaya.', 'success');
                render(true);
            } catch(e){ showRealNotification('❌ Settings Error', String(e.message || e), 'danger'); }
        }
        function walletLedgerPreview(userId){
            const w = walletForUser(userId);
            const rows = (w.ledger || []).slice(-8).reverse();
            if(!rows.length) return '<p class="text-[10px] text-[var(--text-muted)] mt-3">No wallet ledger yet.</p>';
            return `<div class="mt-3 border-t border-[var(--border)] pt-2 space-y-1">${rows.map(x => {
                const amt = Number(x.amount || 0);
                const cls = amt >= 0 ? 'text-[var(--green)]' : 'text-[var(--rose)]';
                return `<div class="flex items-start justify-between gap-2 text-[9px]"><div class="min-w-0"><p class="text-white font-bold truncate">${x.note || x.type || 'Wallet'}</p><p class="text-[var(--text-muted)] truncate">${String(x.time || '').replace('T',' ')}</p></div><div class="text-right shrink-0"><p class="${cls} font-black">${amt >= 0 ? '+' : ''}${fmtMoney(amt)}</p><p class="text-[var(--text-muted)]">Bal ${fmtMoney(x.balanceAfter || 0)}</p></div></div>`;
            }).join('')}</div>`;
        }

        // ==========================================
        // WHATSAPP ENTRY PARSER UI HELPERS
        // ==========================================
        function ensureEntryStruct(){
            if(!Array.isArray(appState.entries)) appState.entries = [];
            if(!appState.entrySettings) appState.entrySettings = {entryParserEnabled:true, groupsOnly:true, strictFormat:true, autoDebitWallet:true, marketTimingEnabled:true, riskLimitEnabled:true, marketCloseTimes:{}};
            if(!appState.riskSettings) appState.riskSettings = {marketDailyLimit:0, digitDailyLimit:0, userDailyLimit:0, warningPercent:80, autoLockOnLimit:false};
            if(!appState.marketLocks) appState.marketLocks = {};
        }
        async function refreshEntriesState(){
            try{
                const res = await fetch('/api/entries');
                const data = await res.json();
                if(data.status === 'success'){
                    appState.entries = data.entries || [];
                    appState.entrySettings = data.entrySettings || appState.entrySettings || {};
                    appState.riskSettings = data.riskSettings || appState.riskSettings || {};
                    appState.marketLocks = data.marketLocks || appState.marketLocks || {};
                    return data;
                }
            }catch(e){}
            return null;
        }
        async function saveEntryParserToggle(enabled){
            if(!IS_MASTER) return;
            try{
                const res = await fetch('/api/entry_settings', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({entryParserEnabled:!!enabled})});
                const data = await res.json();
                if(data.status !== 'success') throw new Error(data.message || 'Entry settings save failed');
                appState.entrySettings = data.entrySettings || appState.entrySettings;
                showRealNotification(enabled ? '✅ Entry Parser ON' : '⏸️ Entry Parser OFF', enabled ? 'WhatsApp strict entries accept hongi.' : 'WhatsApp entry auto-accept stopped.', enabled ? 'success' : 'info');
                render(true);
            }catch(e){ showRealNotification('❌ Entry Settings Error', String(e.message || e), 'danger'); }
        }
        async function saveEntrySafetySettings(){
            if(!IS_MASTER) return;
            try{
                const marketCloseTimes = {};
                document.querySelectorAll('.entry-time-input[data-market]').forEach(inp => {
                    const market = String(inp.getAttribute('data-market') || '').trim().toUpperCase().replace(/\\s+/g, ' ');
                    const value = String(inp.value || '').trim();
                    if(market && /^\\d{2}:\\d{2}$/.test(value)) marketCloseTimes[market] = value;
                });
                const payload = {
                    marketTimingEnabled: !!document.getElementById('entryTimingToggle')?.checked,
                    riskLimitEnabled: !!document.getElementById('entryRiskToggle')?.checked,
                    marketCloseTimes,
                    marketDailyLimit: Number(document.getElementById('riskMarketLimit')?.value || 0),
                    digitDailyLimit: Number(document.getElementById('riskDigitLimit')?.value || 0),
                    userDailyLimit: Number(document.getElementById('riskUserLimit')?.value || 0),
                    warningPercent: Number(document.getElementById('riskWarnPercent')?.value || 80),
                    autoLockOnLimit: !!document.getElementById('riskAutoLock')?.checked
                };
                const res = await fetch('/api/save_entry_safety', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
                const data = await res.json();
                if(data.status !== 'success') throw new Error(data.message || 'Entry safety save failed');
                appState.entrySettings = data.entrySettings || appState.entrySettings;
                appState.riskSettings = data.riskSettings || appState.riskSettings;
                await refreshEntriesState();
                const changedCount = Object.keys(marketCloseTimes).length;
                showRealNotification('✅ Entry Safety Saved', `Manual market times saved: ${changedCount}. Gateway next message me new cut-off use karega.`, 'success');
                render(true);
            }catch(e){ showRealNotification('❌ Risk Save Error', String(e.message || e), 'danger'); }
        }
        async function unlockMarketFromEntries(market){
            if(!market) return;
            try{
                const res = await fetch('/api/market_unlock', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({market})});
                const data = await res.json();
                if(data.status !== 'success') throw new Error(data.message || 'Unlock failed');
                appState.marketLocks = data.marketLocks || {};
                showRealNotification('🔓 Market Unlocked', market + ' unlocked.', 'success');
                render(true);
            }catch(e){ showRealNotification('❌ Unlock Error', String(e.message || e), 'danger'); }
        }
        function formatEntryDigits(e){
            const d = Array.isArray(e.digits) ? e.digits : String(e.digits || '').split(',');
            return d.map(x => String(x).trim()).filter(Boolean).join(', ');
        }
        function renderEntriesTab(){
            ensureEntryStruct();
            const entries = (appState.entries || []).slice().sort((a,b)=>String(b.createdAt||'').localeCompare(String(a.createdAt||''))).slice(0,120);
            const accepted = entries.filter(e => e.status === 'accepted');
            const total = accepted.reduce((s,e)=>s+Number(e.total||0),0);
            const parserOn = appState.entrySettings.entryParserEnabled !== false;
            const byMarket = {};
            accepted.forEach(e=>{ const m=e.market||'UNKNOWN'; byMarket[m]=(byMarket[m]||0)+Number(e.total||0); });
            const marketRows = Object.entries(byMarket).sort((a,b)=>b[1]-a[1]).slice(0,8);
            let html = `<div class="p-3">
                <div class="native-card p-4 mb-3">
                    <div class="flex items-center justify-between gap-3 mb-3">
                        <div><h2 class="text-white font-black text-sm uppercase tracking-wide">WhatsApp Entry Parser</h2><p class="text-[var(--text-muted)] text-[10px]">Strict format entries accept + wallet auto debit</p></div>
                        <label class="switch shrink-0"><input type="checkbox" ${parserOn?'checked':''} onchange="saveEntryParserToggle(this.checked)"><span class="slider"></span></label>
                    </div>
                    <div class="grid grid-cols-3 gap-2">
                        <div class="stat-box"><p class="stat-lbl">Today Entries</p><p class="stat-val text-white">${accepted.length}</p></div>
                        <div class="stat-box"><p class="stat-lbl">Today Load</p><p class="stat-val text-[var(--green)]">${fmtMoney(total)}</p></div>
                        <div class="stat-box"><p class="stat-lbl">Parser</p><p class="stat-val ${parserOn?'text-[var(--green)]':'text-[var(--rose)]'}">${parserOn?'ON':'OFF'}</p></div>
                    </div>
                    <button onclick="refreshEntriesState().then(()=>render(true))" class="mt-3 w-full bg-[var(--surface-light)] text-white py-3 rounded-xl font-black text-[10px] uppercase border border-[var(--border)] active:scale-95"><i class="fas fa-sync mr-1"></i> Refresh Entries</button>
                </div>
                ${(()=>{ const rs = appState.riskSettings || {}; const es = appState.entrySettings || {}; return `<div class="native-card p-4 mb-3">
                    <div class="flex items-center justify-between gap-3 mb-3"><div><p class="text-white font-black text-[12px] uppercase">Market Time + Risk Controls</p><p class="text-[var(--text-muted)] text-[9px]">0 limit = disabled. Timing ON rahega to cut-off ke baad entry reject hogi.</p></div></div>
                    <div class="grid grid-cols-2 gap-2 mb-3">
                        <label class="flex items-center justify-between bg-[var(--surface-light)] rounded-xl p-3 border border-[var(--border)]"><span class="text-white font-bold text-[10px]">Market Timing</span><span class="switch"><input id="entryTimingToggle" type="checkbox" ${es.marketTimingEnabled!==false?'checked':''}><span class="slider"></span></span></label>
                        <label class="flex items-center justify-between bg-[var(--surface-light)] rounded-xl p-3 border border-[var(--border)]"><span class="text-white font-bold text-[10px]">Risk Limits</span><span class="switch"><input id="entryRiskToggle" type="checkbox" ${es.riskLimitEnabled!==false?'checked':''}><span class="slider"></span></span></label>
                    </div>
                    <div class="grid grid-cols-2 gap-2">
                        <div><p class="stat-lbl">Market Daily Limit</p><input id="riskMarketLimit" class="native-input text-[12px]" type="number" value="${Number(rs.marketDailyLimit||0)}"></div>
                        <div><p class="stat-lbl">Digit Load Limit</p><input id="riskDigitLimit" class="native-input text-[12px]" type="number" value="${Number(rs.digitDailyLimit||0)}"></div>
                        <div><p class="stat-lbl">User Daily Limit</p><input id="riskUserLimit" class="native-input text-[12px]" type="number" value="${Number(rs.userDailyLimit||0)}"></div>
                        <div><p class="stat-lbl">Warning %</p><input id="riskWarnPercent" class="native-input text-[12px]" type="number" value="${Number(rs.warningPercent||80)}"></div>
                    </div>
                    <label class="mt-3 flex items-center justify-between bg-[var(--surface-light)] rounded-xl p-3 border border-[var(--border)]"><span class="text-white font-bold text-[10px]">Auto Lock Market On Limit</span><span class="switch"><input id="riskAutoLock" type="checkbox" ${rs.autoLockOnLimit?'checked':''}><span class="slider"></span></span></label>
                    ${(()=>{
                        const times = (es.marketCloseTimes && typeof es.marketCloseTimes === 'object') ? es.marketCloseTimes : {};
                        const list = [];
                        (markets || []).forEach(m => { if(m && m.n && !list.includes(m.n)) list.push(m.n); });
                        (baseMarkets || []).forEach(m => { if(m && m.n && !list.includes(m.n)) list.push(m.n); });
                        return `<details class="mt-3 bg-[var(--surface-light)] rounded-xl border border-[var(--border)] overflow-hidden">
                            <summary class="px-3 py-3 text-white font-black text-[10px] uppercase cursor-pointer">
                                <i class="fas fa-clock mr-1 text-[var(--primary)]"></i> Manual Market Entry Time Setup
                            </summary>
                            <div class="px-3 pb-3">
                                <p class="text-[var(--text-muted)] text-[9px] mb-3 leading-relaxed">Jis market ka entry time extend/test karna ho, uska cut-off yahan set karo. Example: abhi 23:36 hai aur KALYAN OPEN test karna hai to KALYAN OPEN ko 23:59 set karo. Timing OFF karne se sab market time-check skip hoga.</p>
                                <div class="grid grid-cols-1 gap-2 max-h-72 overflow-y-auto no-scrollbar">
                                    ${list.map(m => `<div class="flex items-center justify-between gap-2 bg-[#17212B] rounded-xl p-2 border border-[var(--border)]">
                                        <span class="text-white font-bold text-[10px] leading-tight">${htmlEscape(m)}</span>
                                        <input data-market="${attrEscape(m)}" class="entry-time-input native-input max-w-[110px] text-[12px] py-2" type="time" value="${attrEscape(times[m] || '')}">
                                    </div>`).join('')}
                                </div>
                            </div>
                        </details>`;
                    })()}
                    <button onclick="saveEntrySafetySettings()" class="mt-3 w-full bg-[var(--primary)] text-white py-3 rounded-xl font-black text-[10px] uppercase active:scale-95">Save Risk Controls</button>
                </div>`; })()}
                ${(()=>{ const locks = appState.marketLocks || {}; const today = new Date().toISOString().slice(0,10); const rows = Object.entries(locks[today] || {}).filter(([m,v])=>v && (v.locked===true || v===true)); if(!rows.length) return ''; return `<div class="native-card p-3 mb-3"><p class="text-white font-black text-[11px] uppercase mb-2">Locked Markets Today</p>${rows.map(([m,v])=>`<div class="flex items-center justify-between gap-2 py-2 border-b border-[var(--border)] last:border-0"><div><p class="text-white font-bold text-[10px]">${m}</p><p class="text-[var(--text-muted)] text-[9px]">${(v&&v.reason)||'locked'}</p></div><button onclick="unlockMarketFromEntries('${String(m).replace(/'/g,"\'")}')" class="text-[var(--green)] font-black text-[10px] px-3 py-2 rounded-lg bg-[rgba(0,194,111,0.12)]">Unlock</button></div>`).join('')}</div>`; })()}
                <div class="native-card p-3 mb-3">
                    <p class="text-white font-black text-[11px] uppercase mb-2">Strict WhatsApp Format</p>
                    <pre class="text-[10px] text-[var(--text-muted)] whitespace-pre-wrap bg-[#17212B] rounded-xl p-3 border border-[var(--border)]">MARKET: KALYAN OPEN
TYPE: ANK
DIGITS: 1,2,3
PAR DIGIT: 100
TOTAL: 300</pre>
                    <p class="text-[9px] text-[var(--text-muted)] mt-2">ANK/PENEL me OPEN/CLOSE market required hai. JODI me base market allowed hai, jaise KALYAN.</p>
                </div>`;
            if(marketRows.length){
                html += `<div class="native-card p-3 mb-3"><p class="text-white font-black text-[11px] uppercase mb-2">Market Load</p>${marketRows.map(([m,v])=>`<div class="flex justify-between text-[10px] py-1 border-b border-[var(--border)] last:border-0"><span class="text-[var(--text-muted)] font-bold">${m}</span><span class="text-white font-black">${fmtMoney(v)}</span></div>`).join('')}</div>`;
            }
            if(!entries.length){
                html += `<div class="native-card p-5 text-center text-[var(--text-muted)] text-xs">Abhi accepted WhatsApp entries nahi hain.</div>`;
            } else {
                html += `<div class="space-y-2">${entries.map(e=>{
                    const ok = e.status === 'accepted';
                    return `<div class="native-card p-3">
                        <div class="flex justify-between gap-2 mb-2"><div class="min-w-0"><p class="text-white font-black text-[12px] truncate">${e.market || '-'}</p><p class="text-[var(--text-muted)] text-[9px] truncate">${e.userName || e.userId || e.senderJid || '-'}</p></div><div class="text-right shrink-0"><p class="${ok?'text-[var(--green)]':'text-[var(--rose)]'} font-black text-[11px]">${String(e.status||'').toUpperCase()}</p><p class="text-[var(--text-muted)] text-[9px]">#${e.id || ''}</p></div></div>
                        <div class="grid grid-cols-3 gap-2 text-center">
                            <div class="bg-[var(--surface-light)] rounded-lg p-2"><p class="stat-lbl">Type</p><p class="text-white font-black text-[11px]">${e.gameType || '-'}</p></div>
                            <div class="bg-[var(--surface-light)] rounded-lg p-2"><p class="stat-lbl">Rate</p><p class="text-white font-black text-[11px]">${fmtMoney(e.parDigit || 0)}</p></div>
                            <div class="bg-[var(--surface-light)] rounded-lg p-2"><p class="stat-lbl">Total</p><p class="text-[var(--green)] font-black text-[11px]">${fmtMoney(e.total || 0)}</p></div>
                        </div>
                        <p class="text-[10px] text-[var(--text-muted)] mt-2"><b>Digits:</b> ${formatEntryDigits(e)}</p>
                        <p class="text-[9px] text-[var(--text-muted)] mt-1">${String(e.createdAt || e.time || '').replace('T',' ')}</p>
                    </div>`;
                }).join('')}</div>`;
            }
            html += `</div>`;
            setTimeout(()=>refreshEntriesState().then(()=>{}), 100);
            return html;
        }

        // ==========================================
        // SPAM / LINK GUARD UI HELPERS
        // ==========================================
        function ensureSpamGuardStruct(){
            if(!appState.spamGuardSettings) appState.spamGuardSettings = {enabled:true, groupsOnly:true, linkGuardEnabled:true, forwardGuardEnabled:true, deleteMessage:true, kickEnabled:true, exemptAdmins:true, linkStrikeLimit:3, forwardStrikeLimit:3, forwardWindowSeconds:60, alertMessage:'⚠️ ALERT - Bhai Group Me Link Dalna Mana he', warningMessage:'⚠️ WARNING - Next Time Group Me Link Daloge To Remove Kiya Jayega Group Se', kickMessage:'🚫 REMOVED - @{number} ko group se remove kiya gaya. Reason: 3 baar link/forward spam.', forwardAlertMessage:'⚠️ ALERT - Bhai Group Me Forward/Spam Message Dalna Mana he', forwardWarningMessage:'⚠️ WARNING - Next Time Multiple Forward Message Daloge To Remove Kiya Jayega Group Se'};
            if(!Array.isArray(appState.spamGuardEvents)) appState.spamGuardEvents = [];
        }
        async function refreshSpamGuardState(){
            ensureSpamGuardStruct();
            try{
                const res = await fetch('/api/spam_guard');
                const data = await res.json();
                if(data.status !== 'success') throw new Error(data.message || 'Spam guard load failed');
                appState.spamGuardSettings = data.settings || appState.spamGuardSettings;
                appState.spamGuardEvents = data.events || [];
                appState.spamGuardStrikeCount = data.strikeCount || 0;
                render(true);
            }catch(e){ showRealNotification('❌ Guard Error', String(e.message || e), 'danger'); }
        }
        async function saveSpamGuardSettings(){
            ensureSpamGuardStruct();
            const payload = {
                enabled: document.getElementById('guard-enabled')?.checked,
                groupsOnly: document.getElementById('guard-groups-only')?.checked,
                linkGuardEnabled: document.getElementById('guard-link')?.checked,
                forwardGuardEnabled: document.getElementById('guard-forward')?.checked,
                deleteMessage: document.getElementById('guard-delete')?.checked,
                kickEnabled: document.getElementById('guard-kick')?.checked,
                exemptAdmins: document.getElementById('guard-exempt')?.checked,
                linkStrikeLimit: Number(document.getElementById('guard-link-limit')?.value || 3),
                forwardStrikeLimit: Number(document.getElementById('guard-forward-limit')?.value || 3),
                forwardWindowSeconds: Number(document.getElementById('guard-forward-window')?.value || 60),
                alertMessage: document.getElementById('guard-alert-msg')?.value || '',
                warningMessage: document.getElementById('guard-warning-msg')?.value || '',
                kickMessage: document.getElementById('guard-kick-msg')?.value || '',
                forwardAlertMessage: document.getElementById('guard-forward-alert-msg')?.value || '',
                forwardWarningMessage: document.getElementById('guard-forward-warning-msg')?.value || ''
            };
            try{
                const res = await fetch('/api/save_spam_guard', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
                const data = await res.json();
                if(data.status !== 'success') throw new Error(data.message || 'Save failed');
                appState.spamGuardSettings = data.settings || appState.spamGuardSettings;
                showRealNotification('✅ Guard Saved', 'Spam/link guard settings save ho gaye.', 'success');
                render(true);
            }catch(e){ showRealNotification('❌ Save Error', String(e.message || e), 'danger'); }
        }
        async function clearSpamGuardState(){
            if(!confirm('Spam guard strikes/events clear karne hain?')) return;
            try{
                const res = await fetch('/api/clear_spam_guard', {method:'POST'});
                const data = await res.json();
                if(data.status !== 'success') throw new Error(data.message || 'Clear failed');
                appState.spamGuardEvents = [];
                appState.spamGuardStrikeCount = 0;
                showRealNotification('✅ Guard Cleared', 'Strikes aur events clear ho gaye.', 'success');
                render(true);
            }catch(e){ showRealNotification('❌ Clear Error', String(e.message || e), 'danger'); }
        }
        function renderGuardTab(){
            ensureSpamGuardStruct();
            const g = appState.spamGuardSettings || {};
            const events = appState.spamGuardEvents || [];
            const evHtml = events.length ? events.slice(0,40).map(ev => `<div class="native-card p-3 mb-2"><div class="flex justify-between gap-2"><div><p class="text-white font-black text-[11px]">${ev.action || '-'} • ${ev.kind || '-'}</p><p class="text-[var(--text-muted)] text-[9px] break-all">${ev.senderJid || ''}</p><p class="text-[var(--text-muted)] text-[9px] break-all">${ev.chatJid || ''}</p></div><div class="text-right shrink-0"><p class="text-[var(--primary)] text-[10px] font-black">${ev.count || 0}</p><p class="text-[var(--text-muted)] text-[9px]">${String(ev.time || '').replace('T',' ').slice(0,16)}</p></div></div>${ev.textSample ? `<p class="mt-2 text-[var(--text-muted)] text-[9px] break-words">${ev.textSample}</p>` : ''}</div>`).join('') : `<div class="native-card p-4 text-center text-[var(--text-muted)] text-[11px]">No spam/link events yet.</div>`;
            return `<div class="p-3 pb-24">
                <div class="sec-header">Spam / Link Guard <button onclick="refreshSpamGuardState()" class="text-[var(--primary)]"><i class="fas fa-sync"></i></button></div>
                <div class="native-card p-4 mb-3">
                    <div class="grid grid-cols-2 gap-2 mb-3">
                        ${toggleRow('guard-enabled','Guard ON', g.enabled !== false)}
                        ${toggleRow('guard-groups-only','Groups Only', g.groupsOnly !== false)}
                        ${toggleRow('guard-link','Link Guard', g.linkGuardEnabled !== false)}
                        ${toggleRow('guard-forward','Forward Guard', g.forwardGuardEnabled !== false)}
                        ${toggleRow('guard-delete','Delete Msg', g.deleteMessage !== false)}
                        ${toggleRow('guard-kick','Kick ON', g.kickEnabled !== false)}
                        ${toggleRow('guard-exempt','Admin Exempt', g.exemptAdmins !== false)}
                    </div>
                    <div class="grid grid-cols-3 gap-2 mb-3">
                        <label><p class="stat-lbl">Link Limit</p><input id="guard-link-limit" type="number" min="1" value="${g.linkStrikeLimit || 3}" class="native-input text-xs"></label>
                        <label><p class="stat-lbl">Forward Limit</p><input id="guard-forward-limit" type="number" min="1" value="${g.forwardStrikeLimit || 3}" class="native-input text-xs"></label>
                        <label><p class="stat-lbl">Window Sec</p><input id="guard-forward-window" type="number" min="10" value="${g.forwardWindowSeconds || 60}" class="native-input text-xs"></label>
                    </div>
                    <div class="space-y-2">
                        <label><p class="stat-lbl">Link Alert Message</p><textarea id="guard-alert-msg" class="native-input text-left text-xs min-h-[55px]">${g.alertMessage || ''}</textarea></label>
                        <label><p class="stat-lbl">Link Warning Message</p><textarea id="guard-warning-msg" class="native-input text-left text-xs min-h-[55px]">${g.warningMessage || ''}</textarea></label>
                        <label><p class="stat-lbl">Kick Message</p><textarea id="guard-kick-msg" class="native-input text-left text-xs min-h-[55px]">${g.kickMessage || ''}</textarea></label>
                        <label><p class="stat-lbl">Forward Alert Message</p><textarea id="guard-forward-alert-msg" class="native-input text-left text-xs min-h-[55px]">${g.forwardAlertMessage || ''}</textarea></label>
                        <label><p class="stat-lbl">Forward Warning Message</p><textarea id="guard-forward-warning-msg" class="native-input text-left text-xs min-h-[55px]">${g.forwardWarningMessage || ''}</textarea></label>
                    </div>
                    <button onclick="saveSpamGuardSettings()" class="mt-3 w-full bg-[var(--primary)] text-white py-3 rounded-xl font-black text-[11px] uppercase active:scale-95"><i class="fas fa-save mr-1"></i> Save Guard Settings</button>
                    <button onclick="clearSpamGuardState()" class="mt-2 w-full bg-[rgba(255,93,93,0.12)] text-[var(--rose)] py-3 rounded-xl font-black text-[11px] uppercase active:scale-95"><i class="fas fa-trash mr-1"></i> Clear Strikes / Events</button>
                    <p class="mt-3 text-[var(--text-muted)] text-[10px] leading-relaxed">Remove/delete ke liye bot ko WhatsApp group admin banana zaroori hai. Admin Exempt ON rahega to group admins par action nahi hoga.</p>
                </div>
                <div class="sec-header">Recent Guard Events <span>${appState.spamGuardStrikeCount || 0} strikes</span></div>
                ${evHtml}
            </div>`;
        }

        // ==========================================

        // HEALTH MONITOR UI HELPERS
        function ensureHealthMonitorStruct(){
            if(!appState.healthMonitor) appState.healthMonitor = null;
        }
        async function refreshHealthMonitor(){
            ensureHealthMonitorStruct();
            try{
                const res = await fetch('/api/health_monitor?ts=' + Date.now());
                const data = await res.json();
                if(data.status !== 'success') throw new Error(data.message || 'Health load failed');
                appState.healthMonitor = data.health || {};
                if(mainNav === 'health') render(false);
            }catch(e){
                appState.healthMonitor = {gateway:{status:'offline', connected:false, message:String(e.message || e)}, counts:{}, modules:{}, firebase:{status:'error'}};
                if(mainNav === 'health') render(false);
                showRealNotification('❌ Health Error', String(e.message || e), 'danger');
            }
        }
        async function resetWhatsAppSession(){
            if(!confirm('WhatsApp session reset karna hai? Iske baad fresh QR scan karna padega.')) return;
            try{
                const res = await fetch('/api/wa_reset_session', {method:'POST'});
                const data = await res.json();
                if(data.status !== 'success') throw new Error(data.message || 'Reset failed');
                showRealNotification('✅ WhatsApp Reset', 'Fresh QR generate ho raha hai. 3-5 sec wait karein.', 'success');
                setTimeout(refreshHealthMonitor, 2500);
                setTimeout(refreshHealthMonitor, 6500);
            }catch(e){ showRealNotification('❌ Reset Error', String(e.message || e), 'danger'); }
        }
        async function refreshWaLoginCard(){
            try{
                const res = await fetch('/api/wa_login_status?ts=' + Date.now());
                const data = await res.json();
                if(!appState.healthMonitor) appState.healthMonitor = {};
                if(!appState.healthMonitor.gateway) appState.healthMonitor.gateway = {};
                appState.healthMonitor.waLogin = data;
                appState.healthMonitor.gateway.waLogin = data;
                render(false);
            }catch(e){ showRealNotification('❌ Login Status', String(e.message || e), 'danger'); }
        }
        function healthStatusPill(ok, labelOk, labelBad, neutral){
            if(neutral){
                return `<span class="px-2 py-1 rounded-lg text-[9px] font-black uppercase bg-[rgba(122,156,184,0.14)] text-[var(--text-muted)] border border-[rgba(122,156,184,0.18)]">${neutral}</span>`;
            }
            return `<span class="px-2 py-1 rounded-lg text-[9px] font-black uppercase ${ok ? 'bg-[rgba(0,194,111,0.16)] text-[var(--green)] border border-[rgba(0,194,111,0.22)]' : 'bg-[rgba(255,93,93,0.14)] text-[var(--rose)] border border-[rgba(255,93,93,0.22)]'}">${ok ? labelOk : labelBad}</span>`;
        }
        function healthTime(v){
            if(!v) return 'Never';
            try{
                const d = new Date(v);
                if(!isNaN(d.getTime())){
                    return d.toLocaleString('en-GB', {
                        timeZone: 'Asia/Kolkata', year:'numeric', month:'2-digit', day:'2-digit',
                        hour:'2-digit', minute:'2-digit', second:'2-digit', hour12:false
                    }).replace(',', '');
                }
                return String(v).replace('T',' ').replace('Z','').slice(0,19);
            }catch(e){ return String(v); }
        }
        function healthGuardReason(reason){
            const labels = (appState.healthMonitor && appState.healthMonitor.last && appState.healthMonitor.last.guardReasonLabels) || {};
            return labels[reason] || ({
                fresh_open_missing: 'Old/final ignored — fresh open missing',
                close_open_mismatch: 'Close ignored — open/result mismatch',
                invalid_format: 'Invalid result format skipped',
                stale_candidate: 'Stale duplicate skipped'
            }[reason]) || reason || 'skipped';
        }
        function healthMoney(v){
            const n = Number(v || 0);
            return '₹' + (Number.isInteger(n) ? String(n) : n.toFixed(2));
        }
        function proLevelPill(level){
            const map = {
                success: 'bg-[rgba(0,194,111,0.16)] text-[var(--green)] border-[rgba(0,194,111,0.22)]',
                info: 'bg-[rgba(42,171,238,0.14)] text-[var(--primary)] border-[rgba(42,171,238,0.22)]',
                warning: 'bg-[rgba(250,199,72,0.14)] text-[var(--amber)] border-[rgba(250,199,72,0.22)]',
                danger: 'bg-[rgba(255,93,93,0.14)] text-[var(--rose)] border-[rgba(255,93,93,0.22)]'
            };
            const label = {success:'READY', info:'INFO', warning:'CHECK', danger:'FIX'}[level] || 'INFO';
            return `<span class="px-2 py-1 rounded-lg text-[9px] font-black uppercase border ${map[level] || map.info}">${label}</span>`;
        }
        function setMainNavFromHealth(target){
            if(!target) return;
            setMainNav(target);
        }
        function renderHealthMonitorTab(){
            const h = appState.healthMonitor || {};
            const gw = h.gateway || {};
            const gh = gw.health || h.health || {};
            const counts = h.counts || {};
            const mods = h.modules || {};
            const targets = h.gatewayTargets || {};
            const groups = (targets.groups || []).length || (((gw.targets || {}).groups) || 0);
            const contacts = (targets.contacts || []).length || (((gw.targets || {}).contacts) || 0);
            const resultScrape = gw.scrape || gw.resultScrape || {};
            const runtimeUpdates = gh.lastResultScrapeUpdates || [];
            const firebaseUpdates = (h.last && h.last.recentFirebaseResults) || [];
            const recentUpdates = runtimeUpdates.length ? runtimeUpdates : firebaseUpdates;
            const recentSkipped = (gh.lastResultScrapeSkipped || []).slice(-6);
            const professional = h.professional || {};
            const flowStatus = professional.flowStatus || [];
            const actionPlan = professional.actionPlan || [];
            const riskSummary = professional.riskSummary || {};
            const gatewayOnline = gw.status === 'success' || gw.status === 'online';
            const waConnected = !!(gw.connected || gw.connected === true);
            const waLogin = h.waLogin || gw.waLogin || {};
            const cards = [
                {title:'Firebase', ok:h.firebase && h.firebase.status === 'success', line1:healthTime(h.firebase?.lastCheckedAt || ''), line2:h.firebase?.url || ''},
                {title:'Gateway', ok:gatewayOnline, line1:gh.startedAt ? 'Started: ' + healthTime(gh.startedAt) : (gw.message || ''), line2:'Port 3000'},
                {title:'WhatsApp', ok:waConnected, line1:gw.user ? (gw.user.name || gw.user.id || 'Connected') : (gh.lastWhatsAppEvent || ''), line2:gh.lastDisconnectCode ? 'Disconnect: ' + gh.lastDisconnectCode : ''},
                {title:'Auto Scrape', ok:!!mods.autoScrape && resultScrape.enabled !== false, line1:'Interval: ' + ((resultScrape.intervalMs || 0) / 1000 || '-') + 's', line2:(resultScrape.urls || []).join(', ')},
                {title:'Entry Parser', ok:!!mods.entryParser, line1:'Timing: ' + (mods.marketTiming ? 'ON' : 'OFF'), line2:'Risk: ' + (mods.riskLimits ? 'ON' : 'OFF')},
                {title:'Settlement', ok:!!mods.settlement, line1:'Today: ' + (counts.settlementsToday || 0), line2:'Result targets: ' + (counts.resultTargets || 0)},
                {title:'Payment', ok:!!mods.paymentAutomation, line1:'Pending: ' + (counts.paymentsPending || 0), line2:'Outbox: ' + (counts.paymentOutboxPending || 0)},
                {title:'Forwarder', ok:!!mods.loadForwarder, neutral:mods.loadForwarder ? '' : 'DISABLED', line1:'Queue: ' + (counts.loadForwardOutboxPending || 0), line2:'Last: ' + healthTime(h.last?.loadForwarder?.lastSentAt)},
                {title:'Guard', ok:!!mods.spamGuard, line1:'Events: ' + (counts.guardEvents || 0), line2:''}
            ];
            return `
                <div class="sec-header">System Health <button onclick="refreshHealthMonitor()" class="text-[var(--primary)]"><i class="fas fa-sync"></i></button></div>
                <div class="p-3 pb-28">
                    <div class="native-card p-4 mb-3 bg-[#1A3348] border border-[rgba(42,171,238,0.25)]">
                        <div class="flex items-center justify-between gap-3">
                            <div>
                                <p class="text-white font-black text-[14px] uppercase">Titan Nova Health Monitor</p>
                                <p class="text-[var(--text-muted)] text-[10px] mt-1">Last check: ${healthTime(h.firebase?.lastCheckedAt || new Date().toISOString())}</p>
                            </div>
                            <div class="text-right">${healthStatusPill(gatewayOnline && waConnected, 'ONLINE', 'CHECK')}</div>
                        </div>
                        <div class="grid grid-cols-3 gap-2 mt-4 text-center">
                            <div class="stat-box"><p class="stat-lbl">Today Entries</p><p class="stat-val">${counts.acceptedEntriesToday || 0}</p></div>
                            <div class="stat-box"><p class="stat-lbl">Today Load</p><p class="stat-val">${healthMoney(counts.todayLoad || 0)}</p></div>
                            <div class="stat-box"><p class="stat-lbl">Targets</p><p class="stat-val">${counts.resultTargets || 0}</p></div>
                        </div>
                    </div>
                    <div class="native-card p-4 mb-3 border border-[rgba(0,194,111,0.16)] bg-[linear-gradient(135deg,rgba(0,194,111,0.08),rgba(42,171,238,0.05))]">
                        <div class="flex items-start justify-between gap-3 mb-3">
                            <div>
                                <p class="text-white font-black text-[13px] uppercase"><i class="fas fa-diagram-project text-[var(--green)] mr-1"></i> Professional Flow Board</p>
                                <p class="text-[var(--text-muted)] text-[10px] mt-1">Entry → Wallet/Risk → Load → Result → Settlement → Delivery → Backup</p>
                            </div>
                            ${healthStatusPill((actionPlan[0] || {}).level === 'success', 'READY', 'ACTION')}
                        </div>
                        <div class="grid grid-cols-2 gap-2 mb-3">
                            ${flowStatus.map(item => `<button onclick="setMainNavFromHealth('${item.key === 'entry' ? 'entries' : item.key === 'delivery' ? 'results' : item.key === 'risk' ? 'entries' : item.key}')" class="text-left bg-[var(--surface-light)] border border-[var(--border)] rounded-xl p-3 active:scale-95">
                                <div class="flex items-center justify-between gap-2"><p class="text-white font-black text-[10px] uppercase">${item.title}</p>${healthStatusPill(item.ok, 'OK', 'OFF')}</div>
                                <p class="text-[var(--text-muted)] text-[9px] mt-1 leading-snug">${htmlEscape(item.detail || '-')}</p>
                            </button>`).join('')}
                        </div>
                        <div class="space-y-2">
                            ${(actionPlan || []).map(a => `<button onclick="setMainNavFromHealth('${a.target || 'health'}')" class="w-full flex items-start justify-between gap-3 text-left bg-[#17212B] border border-[var(--border)] rounded-xl p-3 active:scale-95">
                                <div><p class="text-white font-black text-[10px] uppercase">${htmlEscape(a.title || 'Action')}</p><p class="text-[var(--text-muted)] text-[9px] mt-1 leading-snug">${htmlEscape(a.detail || '')}</p></div>${proLevelPill(a.level || 'info')}
                            </button>`).join('')}
                        </div>
                        ${(riskSummary.lowWallets || []).length ? `<details class="mt-3 bg-[#17212B] rounded-xl border border-[var(--border)] overflow-hidden"><summary class="px-3 py-3 text-white font-black text-[10px] uppercase cursor-pointer">Low Wallet Watchlist (${riskSummary.lowWallets.length})</summary><div class="px-3 pb-3 space-y-1">${riskSummary.lowWallets.map(w => `<div class="flex justify-between gap-2 text-[10px] py-1 border-b border-[var(--border)] last:border-0"><span class="text-[var(--text-muted)] truncate">${htmlEscape(w.name || w.userId)}</span><b class="text-[var(--rose)] shrink-0">${healthMoney(w.available || 0)}</b></div>`).join('')}</div></details>` : ''}
                    </div>
                    <div class="native-card p-4 mb-3 border border-[rgba(42,171,238,0.18)]">
                        <div class="flex items-center justify-between gap-3 mb-3">
                            <div>
                                <p class="text-white font-black text-[12px] uppercase"><i class="fab fa-whatsapp text-[var(--green)] mr-1"></i> WhatsApp Login Helper</p>
                                <p class="text-[var(--text-muted)] text-[10px] mt-1">Logout ho jaye to yahin se QR scan karke reconnect karo.</p>
                            </div>
                            ${healthStatusPill(waConnected, 'CONNECTED', (waLogin.qrAvailable ? 'QR READY' : 'OFFLINE'))}
                        </div>
                        ${waConnected ? `<div class="bg-[rgba(0,194,111,0.08)] border border-[rgba(0,194,111,0.16)] rounded-xl p-3 text-[10px] text-[var(--green)]">WhatsApp connected: ${gw.user ? (gw.user.name || gw.user.id || 'Connected') : 'Connected'}</div>` : `
                            <div class="grid grid-cols-1 gap-3">
                                ${waLogin.qrAvailable ? `<div class="bg-white rounded-2xl p-3 mx-auto w-[220px] h-[220px] flex items-center justify-center"><img src="/api/wa_qr_image?ts=${Date.now()}" class="w-[200px] h-[200px]" alt="WhatsApp QR"></div><p class="text-[var(--text-muted)] text-[10px] text-center">WhatsApp → Linked devices → Link a device → QR scan karo.</p>` : `<div class="bg-[rgba(250,199,72,0.08)] border border-[rgba(250,199,72,0.16)] rounded-xl p-3 text-[10px] text-[var(--amber)]">QR abhi available nahi hai. Refresh karo ya Reset Session dabao.</div>`}
                            </div>`}
                        <div class="grid grid-cols-2 gap-2 mt-3">
                            <button onclick="refreshWaLoginCard()" class="bg-[var(--surface-light)] text-white py-3 rounded-xl font-black text-[10px] uppercase active:scale-95"><i class="fas fa-sync mr-1"></i> Refresh QR</button>
                            <button onclick="resetWhatsAppSession()" class="bg-[rgba(255,93,93,0.14)] text-[var(--rose)] border border-[rgba(255,93,93,0.22)] py-3 rounded-xl font-black text-[10px] uppercase active:scale-95"><i class="fas fa-right-from-bracket mr-1"></i> Reset Session</button>
                        </div>
                        <p class="text-[9px] text-[var(--text-muted)] mt-3 break-all">Auth folder: ${waLogin.authDir || (gw.waLogin && gw.waLogin.authDir) || 'auth_info_baileys'}</p>
                    </div>
                    <div class="grid grid-cols-1 gap-2 mb-3">
                        ${cards.map(c => `<div class="native-card p-3"><div class="flex items-center justify-between gap-3"><div class="min-w-0"><p class="text-white font-black text-[12px] uppercase">${c.title}</p><p class="text-[var(--text-muted)] text-[10px] truncate mt-1">${c.line1 || '-'}</p><p class="text-[var(--text-muted)] text-[9px] truncate mt-0.5">${c.line2 || ''}</p></div>${healthStatusPill(c.ok, 'OK', 'OFF', c.neutral || '')}</div></div>`).join('')}
                    </div>
                    <div class="native-card p-4 mb-3">
                        <p class="text-white font-black text-[12px] uppercase mb-3">Gateway Details</p>
                        <div class="grid grid-cols-2 gap-2 text-center">
                            <div class="stat-box"><p class="stat-lbl">Groups</p><p class="stat-val">${groups || 0}</p></div>
                            <div class="stat-box"><p class="stat-lbl">Contacts</p><p class="stat-val">${contacts || 0}</p></div>
                            <div class="stat-box"><p class="stat-lbl">Gateway Now</p><p class="stat-val text-[11px]">${gw.now || '-'}</p></div>
                            <div class="stat-box"><p class="stat-lbl">Timezone</p><p class="stat-val text-[10px]">${gw.timezone || '-'}</p></div>
                        </div>
                    </div>
                    <div class="native-card p-4 mb-3">
                        <p class="text-white font-black text-[12px] uppercase mb-3">Realtime Result Scrape</p>
                        <div class="space-y-2 text-[10px]">
                            <div class="flex justify-between gap-2"><span class="text-[var(--text-muted)]">Last scrape</span><span class="text-white font-bold text-right">${healthTime(gh.lastResultScrapeTickAt)}</span></div>
                            <div class="flex justify-between gap-2"><span class="text-[var(--text-muted)]">Status</span><span class="text-white font-bold text-right">${gh.lastResultScrapeStatus || '-'}</span></div>
                            <div class="flex justify-between gap-2"><span class="text-[var(--text-muted)]">Last result send</span><span class="text-white font-bold text-right">${gh.lastResultSendAt ? healthTime(gh.lastResultSendAt) : 'No send since restart'} ${gh.lastResultSendSummary ? '— ' + gh.lastResultSendSummary : ''}</span></div>
                            <div class="flex justify-between gap-2"><span class="text-[var(--text-muted)]">Last send</span><span class="text-white font-bold text-right">${gh.lastSendAt ? healthTime(gh.lastSendAt) : 'No send since restart'} ${gh.lastSendOk === true ? '✅' : (gh.lastSendOk === false ? '❌' : '')}</span></div>
                            ${gh.lastResultScrapeError ? `<div class="bg-[rgba(255,93,93,0.1)] border border-[rgba(255,93,93,0.2)] rounded-xl p-2 text-[var(--rose)]">${gh.lastResultScrapeError}</div>` : ''}
                        </div>
                        <div class="mt-3">
                            <p class="stat-lbl">Recent Updates / Saved Results</p>
                            ${recentUpdates.length ? recentUpdates.map(x => `<div class="bg-[var(--surface-light)] rounded-xl p-2 mb-1 text-[10px] text-white flex justify-between gap-2"><span class="truncate">${x.market || '-'}</span><b class="shrink-0">${(x.stage || '').toUpperCase()} ${x.result || ''}</b></div>`).join('') : `<p class="text-[10px] text-[var(--text-muted)]">No saved result update recorded today.</p>`}
                            ${!runtimeUpdates.length && firebaseUpdates.length ? `<p class="text-[9px] text-[var(--text-muted)] mt-1">Showing Firebase saved results because Gateway runtime counters reset after restart.</p>` : ''}
                        </div>
                        ${recentSkipped.length ? `<div class="mt-3"><p class="stat-lbl">Guarded / Ignored Old Results</p><p class="text-[9px] text-[var(--text-muted)] mb-2">Ye warning nahi hai. System old/final result ko skip kar raha hai jab fresh open match nahi mila.</p>${recentSkipped.map(x => `<div class="bg-[rgba(250,199,72,0.06)] border border-[rgba(250,199,72,0.12)] rounded-xl p-2 mb-1 text-[10px] text-[var(--amber)]">${x.market || '-'} ${x.result || ''} — ${healthGuardReason(x.reason)}</div>`).join('')}</div>` : ''}
                    </div>
                    <div class="native-card p-4">
                        <p class="text-white font-black text-[12px] uppercase mb-3">Data Summary</p>
                        <div class="grid grid-cols-2 gap-2 text-center">
                            <div class="stat-box"><p class="stat-lbl">Profiles</p><p class="stat-val">${counts.profiles || 0}</p></div>
                            <div class="stat-box"><p class="stat-lbl">Wallets</p><p class="stat-val">${counts.wallets || 0}</p></div>
                            <div class="stat-box"><p class="stat-lbl">Result Markets</p><p class="stat-val">${counts.resultMarketsToday || 0}</p></div>
                            <div class="stat-box"><p class="stat-lbl">Audit</p><p class="stat-val">${counts.auditEvents || 0}</p></div>
                        </div>
                        <p class="text-[9px] text-[var(--text-muted)] mt-3 leading-relaxed">Troubleshooting: Gateway/WhatsApp OFF ho to result/entry/send issue Gateway side hai. Firebase OK but queues pending ho to Gateway online rakhna hoga.</p>
                    </div>
                </div>`;
        }

        // BACKUP / EXPORT / AUDIT UI HELPERS
        // ==========================================
        function ensureBackupAuditStruct(){
            if(!appState.backupSummary) appState.backupSummary = {};
            if(!Array.isArray(appState.auditLog)) appState.auditLog = [];
        }
        async function refreshBackupAuditState(){
            ensureBackupAuditStruct();
            try{
                const res = await fetch('/api/backup_audit');
                const data = await res.json();
                if(data.status !== 'success') throw new Error(data.message || 'Backup load failed');
                appState.backupSummary = data.summary || {};
                appState.auditLog = data.auditLog || [];
                render(true);
            }catch(e){ showRealNotification('❌ Backup Error', String(e.message || e), 'danger'); }
        }
        function downloadBackupZip(){
            window.open('/api/download_backup', '_blank');
            showRealNotification('✅ Backup Started', 'ZIP download start ho raha hai.', 'success');
            setTimeout(refreshBackupAuditState, 1200);
        }
        function exportCsv(kind){
            window.open('/api/export_csv?kind=' + encodeURIComponent(kind), '_blank');
        }
        async function clearAuditLog(){
            if(!confirm('Audit log clear karna hai? Backup ZIP pehle download karna recommended hai.')) return;
            try{
                const res = await fetch('/api/clear_audit_log', {method:'POST'});
                const data = await res.json();
                if(data.status !== 'success') throw new Error(data.message || 'Clear failed');
                appState.auditLog = data.auditLog || [];
                appState.backupSummary = data.summary || appState.backupSummary || {};
                showRealNotification('✅ Audit Cleared', 'Audit log clear ho gaya.', 'success');
                render(true);
            }catch(e){ showRealNotification('❌ Clear Error', String(e.message || e), 'danger'); }
        }
        function renderBackupAuditTab(){
            ensureBackupAuditStruct();
            const s = appState.backupSummary || {};
            const audit = appState.auditLog || [];
            const exportButtons = [
                ['entries','Entries CSV','fa-receipt'],
                ['wallets','Wallets CSV','fa-wallet'],
                ['wallet_ledger','Ledger CSV','fa-list'],
                ['payments','Payments CSV','fa-rupee-sign'],
                ['settlements','Settlements CSV','fa-trophy'],
                ['audit','Audit CSV','fa-clipboard-list']
            ];
            const auditHtml = audit.length ? audit.slice(0,80).map(a => `<div class="native-card p-3 mb-2"><div class="flex justify-between gap-2"><div class="min-w-0"><p class="text-white font-black text-[11px] truncate">${a.action || '-'}</p><p class="text-[var(--text-muted)] text-[9px] break-all">${a.id || ''}</p></div><p class="text-[var(--primary)] text-[9px] shrink-0">${String(a.time || '').replace('T',' ').slice(0,19)}</p></div><pre class="mt-2 text-[9px] text-[var(--text-muted)] whitespace-pre-wrap break-words bg-[#17212B] rounded-lg p-2 border border-[var(--border)] max-h-24 overflow-y-auto no-scrollbar">${String(JSON.stringify(a.detail || {}, null, 2)).replace(/</g,'&lt;')}</pre></div>`).join('') : `<div class="native-card p-5 text-center text-[var(--text-muted)] text-xs">No audit events.</div>`;
            return `<div class="p-3 pb-24">
                <div class="sec-header">Backup / Export / Audit <button onclick="refreshBackupAuditState()" class="text-[var(--primary)]"><i class="fas fa-sync"></i></button></div>
                <div class="wallet-hud rounded-2xl mb-3">
                    <div class="stat-box"><div class="stat-lbl">Entries</div><div class="stat-val">${s.entries || 0}</div></div>
                    <div class="stat-box"><div class="stat-lbl">Today Load</div><div class="stat-val">₹${Number(s.todayLoad || 0).toFixed(0)}</div></div>
                    <div class="stat-box"><div class="stat-lbl">Wallets</div><div class="stat-val">${s.wallets || 0}</div></div>
                    <div class="stat-box"><div class="stat-lbl">Audit Events</div><div class="stat-val">${s.auditEvents || 0}</div></div>
                </div>
                <div class="native-card p-4 mb-3">
                    <div class="flex items-start gap-3 mb-4">
                        <div class="w-11 h-11 rounded-2xl bg-[rgba(42,171,238,0.15)] text-[var(--primary)] flex items-center justify-center text-lg"><i class="fas fa-file-zipper"></i></div>
                        <div class="flex-1"><p class="text-white font-black text-[13px] uppercase">Full Backup ZIP</p><p class="text-[var(--text-muted)] text-[10px] leading-relaxed">state.json + entries/wallets/payments/settlements/audit CSV files. Last: ${s.lastBackupAt ? String(s.lastBackupAt).replace('T',' ').slice(0,19) : 'Never'}</p></div>
                    </div>
                    <button onclick="downloadBackupZip()" class="w-full bg-[var(--primary)] text-white py-3 rounded-xl font-black text-[11px] uppercase active:scale-95"><i class="fas fa-download mr-1"></i> Download Full Backup ZIP</button>
                </div>
                <div class="native-card p-4 mb-3">
                    <p class="text-white font-black text-[12px] uppercase mb-3">CSV Exports</p>
                    <div class="grid grid-cols-2 gap-2">${exportButtons.map(([kind,label,icon])=>`<button onclick="exportCsv('${kind}')" class="bg-[var(--surface-light)] border border-[var(--border)] text-white py-3 rounded-xl font-black text-[10px] uppercase active:scale-95"><i class="fas ${icon} mr-1 text-[var(--primary)]"></i>${label}</button>`).join('')}</div>
                </div>
                <div class="native-card p-4 mb-3">
                    <p class="text-white font-black text-[12px] uppercase mb-2">Data Summary</p>
                    <div class="grid grid-cols-2 gap-2 text-[10px]">
                        <div class="bg-[var(--surface-light)] rounded-xl p-3"><p class="stat-lbl">Profiles</p><p class="text-white font-black">${s.profiles || 0}</p></div>
                        <div class="bg-[var(--surface-light)] rounded-xl p-3"><p class="stat-lbl">Pending Payments</p><p class="text-white font-black">${s.pendingPayments || 0}</p></div>
                        <div class="bg-[var(--surface-light)] rounded-xl p-3"><p class="stat-lbl">Settlements Today</p><p class="text-white font-black">${s.todaySettlements || 0}</p></div>
                        <div class="bg-[var(--surface-light)] rounded-xl p-3"><p class="stat-lbl">Accepted Today</p><p class="text-white font-black">${s.acceptedToday || 0}</p></div>
                    </div>
                </div>
                <div class="sec-header">Recent Audit <button onclick="clearAuditLog()" class="text-[var(--rose)] text-[10px] font-black uppercase">Clear</button></div>
                ${auditHtml}
            </div>`;
        }

        function toggleRow(id,label,checked){
            return `<label class="flex items-center justify-between gap-2 bg-[var(--surface-light)] border border-[var(--border)] rounded-xl px-3 py-2"><span class="text-white text-[10px] font-bold">${label}</span><span class="switch"><input id="${id}" type="checkbox" ${checked?'checked':''}><span class="slider"></span></span></label>`;
        }

        // ==========================================
        // LOAD REPORT FORWARDER UI HELPERS
        // ==========================================
        function ensureLoadForwarderStruct(){
            if(!appState.loadForwarder) appState.loadForwarder = {enabled:false, scheduleTime:'18:00', selectedMarket:'', targets:[], gameTypes:['ANK','PENEL','JODI'], maxRowsPerType:80, includeEmptyTypes:false};
            if(!Array.isArray(appState.loadForwarder.targets)) appState.loadForwarder.targets = [];
            if(!Array.isArray(appState.loadForwarder.gameTypes) || !appState.loadForwarder.gameTypes.length) appState.loadForwarder.gameTypes = ['ANK','PENEL','JODI'];
            if(!Array.isArray(appState.forwardTargetOptions)) appState.forwardTargetOptions = [];
            if(typeof appState.loadForwarder.enabled === 'undefined') appState.loadForwarder.enabled = false;
            if(!appState.loadForwarder.scheduleTime) appState.loadForwarder.scheduleTime = '18:00';
            if(!appState.loadForwarder.maxRowsPerType) appState.loadForwarder.maxRowsPerType = 80;
        }
        function forwardMarketsList(){
            const fromEntries = Array.from(new Set((appState.entries || []).map(e => String(e.market || '').trim().toUpperCase()).filter(Boolean)));
            const fromStatic = (markets || []).map(m => m.n).concat((baseMarkets || []).map(m => m.n));
            return Array.from(new Set(fromStatic.concat(fromEntries).map(x => String(x || '').trim().toUpperCase()).filter(Boolean))).sort();
        }
        async function refreshLoadForwarderState(){
            ensureLoadForwarderStruct();
            try{
                const market = encodeURIComponent(appState.loadForwarder.selectedMarket || '');
                const res = await fetch(`/api/load_forwarder?market=${market}`);
                const data = await res.json();
                if(data.status !== 'success') throw new Error(data.message || 'Load forwarder load failed');
                appState.loadForwarder = data.settings || appState.loadForwarder;
                appState.loadReportPreview = data.text || '';
                render(true);
            }catch(e){ showRealNotification('❌ Forward Error', String(e.message || e), 'danger'); }
        }
        async function syncForwardTargets(){
            ensureLoadForwarderStruct();
            try{
                const res = await fetch('/api/wa_targets');
                const data = await res.json();
                const opts = [];
                (data.groups || []).forEach(g => opts.push({id:g.id, name:g.name || g.subject || g.id, type:'Group'}));
                (data.contacts || []).forEach(c => opts.push({id:c.id, name:c.name || c.id, type:'Private'}));
                (appState.loadForwarder.targets || []).forEach(t => { if(!opts.find(o => o.id === t)) opts.push({id:t, name:t, type:'Saved'}); });
                appState.forwardTargetOptions = opts;
                showRealNotification('✅ Targets Synced', `${opts.length} WhatsApp target loaded.`, 'success');
                render(true);
            }catch(e){ showRealNotification('❌ Sync Error', String(e.message || e), 'danger'); }
        }
        function toggleForwardTarget(target, checked){
            ensureLoadForwarderStruct();
            const set = new Set(appState.loadForwarder.targets || []);
            if(checked) set.add(target); else set.delete(target);
            appState.loadForwarder.targets = Array.from(set);
        }
        function addManualForwardTarget(){
            ensureLoadForwarderStruct();
            const raw = document.getElementById('manual-forward-target')?.value || '';
            const parts = raw.split(String.fromCharCode(10)).join(',').split(',').map(x => x.trim()).filter(Boolean);
            if(!parts.length) return showRealNotification('⚠️ Empty', 'Number/group JID paste karo.', 'danger');
            const set = new Set(appState.loadForwarder.targets || []);
            parts.forEach(x => set.add(x));
            appState.loadForwarder.targets = Array.from(set);
            appState.forwardTargetOptions = appState.forwardTargetOptions || [];
            parts.forEach(x => { if(!appState.forwardTargetOptions.find(o => o.id === x)) appState.forwardTargetOptions.push({id:x, name:x, type:'Manual'}); });
            const inp = document.getElementById('manual-forward-target'); if(inp) inp.value = '';
            render(true);
        }
        function selectedLoadGameTypes(){
            const vals = [];
            ['ANK','PENEL','JODI'].forEach(gt => { if(document.getElementById('load-game-'+gt)?.checked) vals.push(gt); });
            return vals.length ? vals : ['ANK','PENEL','JODI'];
        }
        async function saveLoadForwarderSettings(){
            ensureLoadForwarderStruct();
            const payload = {
                enabled: document.getElementById('load-enabled')?.checked,
                scheduleTime: document.getElementById('load-schedule-time')?.value || '18:00',
                selectedMarket: document.getElementById('load-market')?.value || '',
                maxRowsPerType: Number(document.getElementById('load-max-rows')?.value || 80),
                includeEmptyTypes: document.getElementById('load-empty-types')?.checked,
                gameTypes: selectedLoadGameTypes(),
                targets: appState.loadForwarder.targets || []
            };
            try{
                const res = await fetch('/api/save_load_forwarder', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
                const data = await res.json();
                if(data.status !== 'success') throw new Error(data.message || 'Save failed');
                appState.loadForwarder = data.settings || appState.loadForwarder;
                showRealNotification('✅ Forward Saved', 'Load report schedule/settings save ho gaya.', 'success');
                render(true);
            }catch(e){ showRealNotification('❌ Save Error', String(e.message || e), 'danger'); }
        }
        async function previewLoadReport(){
            ensureLoadForwarderStruct();
            const market = encodeURIComponent(document.getElementById('load-market')?.value || appState.loadForwarder.selectedMarket || '');
            const rows = encodeURIComponent(document.getElementById('load-max-rows')?.value || appState.loadForwarder.maxRowsPerType || 80);
            const gameTypes = encodeURIComponent(selectedLoadGameTypes().join(','));
            try{
                const res = await fetch(`/api/load_report_preview?market=${market}&maxRowsPerType=${rows}&gameTypes=${gameTypes}`);
                const data = await res.json();
                if(data.status !== 'success') throw new Error(data.message || 'Preview failed');
                appState.loadReportPreview = data.text || '';
                showRealNotification('📊 Preview Ready', 'Load report preview update ho gaya.', 'success');
                render(true);
            }catch(e){ showRealNotification('❌ Preview Error', String(e.message || e), 'danger'); }
        }
        async function sendLoadReportNow(){
            ensureLoadForwarderStruct();
            const market = document.getElementById('load-market')?.value || appState.loadForwarder.selectedMarket || '';
            const targets = appState.loadForwarder.targets || [];
            if(!targets.length) return showRealNotification('⚠️ No Target', 'Pehle WhatsApp target select/save karo.', 'danger');
            if(!confirm('Load report abhi selected targets par bhejna hai?')) return;
            try{
                const res = await fetch('/api/load_forwarder_send', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({market, targets, gameTypes:selectedLoadGameTypes(), maxRowsPerType:Number(document.getElementById('load-max-rows')?.value || 80), source:'dashboard_send_now'})});
                const data = await res.json();
                if(data.status !== 'success') throw new Error(data.message || 'Send queue failed');
                appState.loadReportPreview = data.text || appState.loadReportPreview;
                showRealNotification('✅ Queued', 'Gateway online hote hi load report send karega.', 'success');
            }catch(e){ showRealNotification('❌ Send Error', String(e.message || e), 'danger'); }
        }
        function renderForwarderTab(){
            ensureLoadForwarderStruct();
            const lf = appState.loadForwarder;
            const selected = new Set(lf.targets || []);
            const targetOptions = appState.forwardTargetOptions || (lf.targets || []).map(t => ({id:t, name:t, type:'Saved'}));
            const mlist = forwardMarketsList();
            const preview = appState.loadReportPreview || '';
            const selectedGames = new Set(lf.gameTypes || ['ANK','PENEL','JODI']);
            return `<div class="pb-24">
                <p class="sec-header">Load Report Forwarder</p>
                <div class="native-card p-3 mb-3">
                    <div class="flex items-center justify-between gap-3 mb-3">
                        <div><p class="text-white font-black text-[13px] uppercase">Auto Load Forward</p><p class="text-[var(--text-muted)] text-[10px]">Daily selected market load report WhatsApp par send hoga.</p></div>
                        <label class="switch"><input id="load-enabled" type="checkbox" ${lf.enabled !== false && lf.enabled ? 'checked' : ''}><span class="slider"></span></label>
                    </div>
                    <div class="grid grid-cols-2 gap-2">
                        <div><p class="stat-lbl">IST Time</p><input id="load-schedule-time" type="time" class="native-input text-[12px]" value="${lf.scheduleTime || '18:00'}"></div>
                        <div><p class="stat-lbl">Rows / Type</p><input id="load-max-rows" type="number" class="native-input text-[12px]" value="${lf.maxRowsPerType || 80}"></div>
                    </div>
                    <div class="mt-3"><p class="stat-lbl">Market</p><select id="load-market" class="native-input text-[12px] text-left"><option value="">ALL MARKETS</option>${mlist.map(m=>`<option value="${m}" ${String(lf.selectedMarket||'').toUpperCase()===m?'selected':''}>${m}</option>`).join('')}</select></div>
                    <div class="mt-3 bg-[var(--surface-light)] p-3 rounded-xl border border-[var(--border)]">
                        <p class="stat-lbl mb-2">Game Type Blocks</p>
                        <div class="grid grid-cols-3 gap-2">${['ANK','PENEL','JODI'].map(gt=>`<label class="flex items-center justify-center gap-2 bg-[#17212B] rounded-lg p-2 text-[10px] font-black text-white border border-[var(--border)]"><input id="load-game-${gt}" type="checkbox" ${selectedGames.has(gt)?'checked':''}> ${gt}</label>`).join('')}</div>
                    </div>
                    <label class="mt-3 flex items-center justify-between gap-2 text-[10px] text-[var(--text-muted)] font-bold bg-[var(--surface-light)] p-3 rounded-xl border border-[var(--border)]"><span>Include empty ANK/PENEL/JODI blocks</span><input id="load-empty-types" type="checkbox" ${lf.includeEmptyTypes?'checked':''}></label>
                    <button onclick="saveLoadForwarderSettings()" class="mt-3 w-full bg-[var(--green)] text-white py-3 rounded-xl font-black text-[10px] uppercase active:scale-95"><i class="fas fa-save mr-1"></i> Save Forward Settings</button>
                </div>
                <div class="native-card p-3 mb-3">
                    <div class="flex items-center justify-between gap-2 mb-2"><p class="text-white font-black text-[11px] uppercase">WhatsApp Targets</p><button onclick="syncForwardTargets()" class="bg-[var(--primary)] text-white px-3 py-2 rounded-lg font-black text-[9px] uppercase"><i class="fas fa-sync mr-1"></i> Sync</button></div>
                    <div class="flex gap-2 mb-3"><input id="manual-forward-target" class="native-input text-[11px]" placeholder="Manual number/group JID"><button onclick="addManualForwardTarget()" class="bg-[var(--surface-light)] border border-[var(--border)] text-white px-3 rounded-xl font-black text-[10px]">Add</button></div>
                    ${targetOptions.length ? `<div class="max-h-60 overflow-y-auto no-scrollbar space-y-2">${targetOptions.map(o=>`<label class="flex items-center gap-3 bg-[var(--surface-light)] border border-[var(--border)] rounded-xl p-3"><input type="checkbox" ${selected.has(o.id)?'checked':''} onchange="toggleForwardTarget('${String(o.id).replace(/'/g,"\\'")}', this.checked)"><div class="min-w-0"><p class="text-white font-bold text-[11px] truncate">${o.name || o.id}</p><p class="text-[var(--text-muted)] text-[9px] truncate">${o.type || 'Target'} · ${o.id}</p></div></label>`).join('')}</div>` : `<p class="text-[10px] text-[var(--text-muted)]">Sync WhatsApp Targets dabao, ya manual target add karo.</p>`}
                    <p class="text-[9px] text-[var(--text-muted)] mt-3">Selected: ${(lf.targets || []).length}</p>
                </div>
                <div class="grid grid-cols-2 gap-2 px-3 mb-3">
                    <button onclick="previewLoadReport()" class="bg-[var(--surface-light)] text-white py-3 rounded-xl font-black text-[10px] uppercase border border-[var(--border)] active:scale-95"><i class="fas fa-eye mr-1"></i> Preview</button>
                    <button onclick="sendLoadReportNow()" class="bg-[var(--primary)] text-white py-3 rounded-xl font-black text-[10px] uppercase active:scale-95"><i class="fas fa-paper-plane mr-1"></i> Send Now</button>
                </div>
                <div class="native-card p-3 mx-3 mb-3"><p class="text-white font-black text-[11px] uppercase mb-2">Preview</p><pre class="text-[10px] text-[var(--text-muted)] whitespace-pre-wrap bg-[#17212B] rounded-xl p-3 border border-[var(--border)] max-h-80 overflow-y-auto no-scrollbar">${preview ? preview.replace(/</g,'&lt;') : 'Preview button dabao.'}</pre></div>
                <button onclick="refreshLoadForwarderState()" class="mx-3 w-[calc(100%-24px)] bg-[var(--surface-light)] text-white py-3 rounded-xl font-black text-[10px] uppercase border border-[var(--border)] active:scale-95"><i class="fas fa-refresh mr-1"></i> Refresh Forwarder</button>
            </div>`;
        }

        // ==========================================
        // AUTO RESULT SENDER UI HELPERS
        // ==========================================
        function ensureResultStruct(){
            if(!appState.resultRecords) appState.resultRecords = {};
            if(!appState.resultRecords[currentDate]) appState.resultRecords[currentDate] = {};
            if(!Array.isArray(appState.resultTargets)) appState.resultTargets = [];
            if(!appState.resultSettings) appState.resultSettings = {autoScrapeEnabled:true,useForwardTargetsForResults:true};
            if(typeof appState.resultSettings.autoScrapeEnabled === 'undefined') appState.resultSettings.autoScrapeEnabled = true;
            if(typeof appState.resultSettings.useForwardTargetsForResults === 'undefined') appState.resultSettings.useForwardTargetsForResults = true;
            if(!appState.settlementRecords) appState.settlementRecords = {};
            if(!appState.settlementRecords[currentDate]) appState.settlementRecords[currentDate] = {};
            if(!appState.settlementSettings) appState.settlementSettings = {enabled:true, includeSummaryInResultMessage:true, includeHitMissInResultMessage:false, payoutMultipliers:{ank:9.5,jodi:9.5,penel:150}};
            if(!appState.settlementSettings.payoutMultipliers) appState.settlementSettings.payoutMultipliers = {ank:9.5,jodi:9.5,penel:150};
        }
        function resultStageLabel(value){
            const v = String(value || '').trim().replace(/\\s+/g, '');
            if(/^\\d{3}-\\d$/.test(v)) return 'open';
            if(/^\\d{3}-\\d{2}-\\d{3}$/.test(v)) return 'close';
            return '';
        }
        function getResultRec(marketName){
            ensureResultStruct();
            return appState.resultRecords[currentDate][marketName] || {};
        }
        function resultDisplayView(rec){
            rec = rec || {};
            const open = String(rec.openResult || '').trim().replace(/\\s+/g, '');
            const close = String(rec.closeResult || '').trim().replace(/\\s+/g, '');
            const openOk = resultStageLabel(open) === 'open';
            const closeOk = resultStageLabel(close) === 'close';
            const freshCloseOk = closeOk && openOk && close.startsWith(open);
            return {
                open: openOk ? open : '',
                close: freshCloseOk ? close : '',
                rawClose: closeOk ? close : '',
                ignoredClose: closeOk && !freshCloseOk
            };
        }
        function titanResultTargetsText(){
            ensureResultStruct();
            return appState.resultTargets.join('\\n');
        }
        async function refreshResultsState(){
            try {
                const res = await fetch('/api/results?date=' + encodeURIComponent(currentDate));
                const data = await res.json();
                if(data.status === 'success'){
                    appState.resultRecords = data.resultRecords || {};
                    appState.resultTargets = data.resultTargets || [];
                    appState.resultSettings = data.resultSettings || {autoScrapeEnabled:true,useForwardTargetsForResults:true};
                    appState.settlementRecords = data.settlementRecords || {};
                    appState.settlementSettings = data.settlementSettings || {enabled:true, includeSummaryInResultMessage:true, includeHitMissInResultMessage:false, payoutMultipliers:{ank:9.5,jodi:9.5,penel:150}};
                }
            } catch(e) {}
        }
        async function saveResultTargets(){
            if(!IS_MASTER) return;
            const raw = document.getElementById('result-targets-input')?.value || '';
            const targets = titanCleanTargets(raw);
            try {
                const res = await fetch('/api/save_result_targets', {
                    method:'POST', headers:{'Content-Type':'application/json'},
                    body: JSON.stringify({targets})
                });
                const data = await res.json();
                if(data.status !== 'success') throw new Error(data.message || 'Target save failed');
                appState.resultTargets = data.resultTargets || [];
                showRealNotification('✅ Result Targets Saved', appState.resultTargets.length + ' WhatsApp target ready.', 'success');
            } catch(e) { showRealNotification('❌ Error', String(e.message || e), 'danger'); }
        }
        async function syncResultTargets(){
            if(!IS_MASTER) return;
            try {
                const res = await fetch('/api/wa_targets');
                const data = await res.json();
                const all = [...(data.contacts || []), ...(data.groups || [])];
                if(!all.length){ showRealNotification('⚠️ Gateway Offline', 'Pehle Termux me node Gateway.js run karo, phir sync karo.', 'danger'); return; }
                const labels = all.slice(0, 80).map((x,n)=>`${n+1}. ${x.name || x.id}  [${x.type || ''}]`).join('\\n');
                const ans = prompt('Result send target select karo. Multiple ke liye comma use karo.\\n\\n' + labels);
                if(!ans) return;
                const selected = ans.split(',').map(x=>parseInt(x.trim(),10)-1).filter(n=>n>=0 && n<all.length).map(n=>all[n].id);
                if(!selected.length) return;
                ensureResultStruct();
                selected.forEach(t => { if(!appState.resultTargets.includes(t)) appState.resultTargets.push(t); });
                const box = document.getElementById('result-targets-input');
                if(box) box.value = titanResultTargetsText();
                await saveResultTargets();
            } catch(e){ showRealNotification('❌ Sync Error', String(e.message || e), 'danger'); }
        }
        async function saveResultScrapeSetting(enabled){
            if(!IS_MASTER) return;
            ensureResultStruct();
            try {
                const res = await fetch('/api/save_result_settings', {
                    method:'POST', headers:{'Content-Type':'application/json'},
                    body: JSON.stringify({autoScrapeEnabled: !!enabled, useForwardTargetsForResults: appState.resultSettings?.useForwardTargetsForResults !== false})
                });
                const data = await res.json();
                if(data.status !== 'success') throw new Error(data.message || 'Setting save failed');
                appState.resultSettings = data.resultSettings || {autoScrapeEnabled: !!enabled, useForwardTargetsForResults: appState.resultSettings?.useForwardTargetsForResults !== false};
                showRealNotification(enabled ? '🟢 Auto Scrape ON' : '🔴 Auto Scrape OFF', enabled ? 'Gateway ab live result scrape karega.' : 'Gateway auto scrape skip karega. Manual Declare abhi bhi active hai.', enabled ? 'success' : 'danger');
                render(true);
            } catch(e) {
                showRealNotification('❌ Setting Error', String(e.message || e), 'danger');
                render(true);
            }
        }

        async function saveResultDeliverySettings(){
            if(!IS_MASTER) return;
            ensureResultStruct();
            const useForward = document.getElementById('result-use-forward-targets')?.checked;
            try {
                const res = await fetch('/api/save_result_settings', {
                    method:'POST', headers:{'Content-Type':'application/json'},
                    body: JSON.stringify({autoScrapeEnabled: appState.resultSettings.autoScrapeEnabled !== false, useForwardTargetsForResults: !!useForward})
                });
                const data = await res.json();
                if(data.status !== 'success') throw new Error(data.message || 'Delivery save failed');
                appState.resultSettings = data.resultSettings || appState.resultSettings;
                showRealNotification('✅ Delivery Saved', useForward ? 'Result targets + Forward targets dono use honge.' : 'Sirf Result targets use honge.', 'success');
                render(true);
            } catch(e) { showRealNotification('❌ Error', String(e.message || e), 'danger'); }
        }
        async function retryResultDeclarations(){
            if(!IS_MASTER) return;
            if(!confirm('Aaj ke result send locks clear karke pending declarations retry karna hai?')) return;
            try {
                const res = await fetch('/api/gateway_result_retry', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({date: currentDate})});
                const data = await res.json();
                if(data.status !== 'success') throw new Error(data.message || 'Retry failed');
                showRealNotification('🔁 Result Retry', (data.cleared || 0) + ' send lock clear. Gateway retry karega.', 'success');
            } catch(e) { showRealNotification('❌ Retry Error', String(e.message || e), 'danger'); }
        }
        async function runResultScrapeNow(){
            if(!IS_MASTER) return;
            ensureResultStruct();
            if(appState.resultSettings && appState.resultSettings.autoScrapeEnabled === false){
                showRealNotification('🔴 Auto Scrape OFF', 'Pehle switch ON karo, phir Scrape Now/Test run karo.', 'danger');
                return;
            }
            try {
                showRealNotification('🧲 Scraping Started', 'Gateway live result page check kar raha hai...', 'info');
                const res = await fetch('/api/gateway_scrape_results');
                const data = await res.json();
                if(data.status === 'offline') throw new Error(data.message || 'Gateway offline');
                if(data.status === 'error') throw new Error(data.message || 'Scrape failed');
                await refreshResultsState();
                const upd = data.updates || [];
                const scraped = data.scraped || [];
                showRealNotification('✅ Scrape Complete', `${upd.length} new update, ${scraped.length} result found.`, 'success');
                render(true);
            } catch(e){
                showRealNotification('❌ Scrape Error', String(e.message || e), 'danger');
            }
        }
        async function clearInvalidAutoResults(){
            if(!IS_MASTER) return;
            try {
                const res = await fetch('/api/clear_invalid_auto_results', {
                    method:'POST', headers:{'Content-Type':'application/json'},
                    body: JSON.stringify({date: currentDate})
                });
                const data = await res.json();
                if(data.status !== 'success') throw new Error(data.message || 'Cleanup failed');
                appState.resultRecords = data.resultRecords || appState.resultRecords;
                const n = (data.cleared || []).length;
                showRealNotification('🛡️ Old Results Cleared', n + ' invalid close result removed/ignored.', n ? 'success' : 'info');
                render(true);
            } catch(e){
                showRealNotification('❌ Cleanup Error', String(e.message || e), 'danger');
            }
        }

        function settlementCurrency(){ return (appState.walletSettings && appState.walletSettings.currency) || '₹'; }
        function fmtSettlementMoney(v){
            const n = Number(v || 0);
            return settlementCurrency() + (Number.isInteger(n) ? String(n) : n.toFixed(2));
        }
        function todaySettlements(){
            ensureResultStruct();
            return Object.values(appState.settlementRecords[currentDate] || {}).filter(Boolean);
        }
        function settlementCardHtml(){
            ensureResultStruct();
            const list = todaySettlements().sort((a,b)=>String(b.settledAt||'').localeCompare(String(a.settledAt||'')));
            const enabled = !(appState.settlementSettings && appState.settlementSettings.enabled === false);
            const summaryOn = !(appState.settlementSettings && appState.settlementSettings.includeSummaryInResultMessage === false);
            const hitMissAutoOn = !!(appState.settlementSettings && appState.settlementSettings.includeHitMissInResultMessage === true);
            const totalPayout = list.reduce((s,x)=>s+Number(x.payoutTotal||0),0);
            const totalStake = list.reduce((s,x)=>s+Number(x.totalStake||0),0);
            const totalProfit = list.reduce((s,x)=>s+Number(x.marketProfit||0),0);
            return `<p class="sec-header">Settlement Engine</p>
                <div class="native-card p-4 mb-3" style="border-color:rgba(0,194,111,0.18);background:rgba(0,194,111,0.035)">
                    <div class="flex items-center justify-between gap-3 mb-3">
                        <div>
                            <h3 class="text-white font-black text-[13px] uppercase">Result Settlement</h3>
                            <p class="text-[9px] text-[var(--text-muted)] leading-relaxed">Result declare hote hi accepted entries settle hongi; winner wallet me payout credit hoga.</p>
                        </div>
                        <div class="text-[8px] font-black uppercase px-2 py-1 rounded-lg border ${enabled ? 'text-[var(--green)] border-[rgba(0,194,111,0.25)] bg-[rgba(0,194,111,0.08)]' : 'text-[var(--rose)] border-[rgba(255,93,93,0.25)] bg-[rgba(255,93,93,0.08)]'}">${enabled ? 'ON' : 'OFF'}</div>
                    </div>
                    <div class="grid grid-cols-3 gap-2 mb-3">
                        <div class="stat-box"><p class="stat-lbl">Settled</p><p class="stat-val text-white">${list.length}</p></div>
                        <div class="stat-box"><p class="stat-lbl">Payout</p><p class="stat-val text-[var(--green)]">${fmtSettlementMoney(totalPayout)}</p></div>
                        <div class="stat-box"><p class="stat-lbl">P/L</p><p class="stat-val ${totalProfit>=0?'text-[var(--green)]':'text-[var(--rose)]'}">${fmtSettlementMoney(totalProfit)}</p></div>
                    </div>
                    <div class="grid grid-cols-3 gap-2 mb-3">
                        <label class="flex items-center justify-between gap-2 bg-[var(--surface-light)] border border-[var(--border)] rounded-xl p-3 text-[10px] font-bold text-white">Settlement ON <input type="checkbox" onchange="saveSettlementSettings({enabled:this.checked})" ${enabled?'checked':''}></label>
                        <label class="flex items-center justify-between gap-2 bg-[var(--surface-light)] border border-[var(--border)] rounded-xl p-3 text-[10px] font-bold text-white">Msg Summary <input type="checkbox" onchange="saveSettlementSettings({includeSummaryInResultMessage:this.checked})" ${summaryOn?'checked':''}></label>
                        <label class="flex items-center justify-between gap-2 bg-[var(--surface-light)] border border-[var(--border)] rounded-xl p-3 text-[10px] font-bold text-white">Auto Hit/Miss <input type="checkbox" onchange="saveSettlementSettings({includeHitMissInResultMessage:this.checked})" ${hitMissAutoOn?'checked':''}></label>
                    </div>
                    <p class="text-[9px] text-[var(--text-muted)] leading-relaxed mb-3">Auto Hit/Miss OFF recommended hai. Detailed list lambi hoti hai; settlement card se manual Send Hit/Miss use karo.</p>
                    ${list.length ? `<div class="space-y-2 max-h-56 overflow-y-auto no-scrollbar">${list.slice(0,10).map(x=>`<div class="bg-[var(--surface-light)] border border-[var(--border)] rounded-xl p-3"><div class="flex items-center justify-between gap-2"><p class="text-white font-black text-[10px] uppercase">${x.market} ${String(x.stage||'').toUpperCase()}</p><p class="text-[var(--amber)] font-black text-[10px]">${x.result}</p></div><div class="grid grid-cols-4 gap-2 mt-2 text-center"><div><p class="stat-lbl">Entries</p><p class="text-white font-black text-[10px]">${x.eligibleCount||0}</p></div><div><p class="stat-lbl">Hit</p><p class="text-[var(--green)] font-black text-[10px]">${x.hitCount||0}</p></div><div><p class="stat-lbl">Miss</p><p class="text-[var(--rose)] font-black text-[10px]">${x.missCount||0}</p></div><div><p class="stat-lbl">Payout</p><p class="text-[var(--green)] font-black text-[10px]">${fmtSettlementMoney(x.payoutTotal||0)}</p></div></div><button onclick="sendHitMissReport(decodeURIComponent('${encodeURIComponent(String(x.market||''))}'), decodeURIComponent('${encodeURIComponent(String(x.stage||''))}'))" class="mt-3 w-full bg-[rgba(42,171,238,0.15)] text-[var(--primary)] border border-[rgba(42,171,238,0.25)] py-2 rounded-xl font-black text-[9px] uppercase active:scale-95"><i class="fas fa-list-check mr-1"></i> Send Hit/Miss</button></div>`).join('')}</div>` : `<p class="text-[10px] text-[var(--text-muted)]">Aaj abhi koi settlement nahi hua.</p>`}
                </div>`;
        }

        async function sendHitMissReport(market, stage){
            if(!IS_MASTER) return;
            try {
                const res = await fetch('/api/send_hitmiss_report', {
                    method:'POST', headers:{'Content-Type':'application/json'},
                    body: JSON.stringify({date: currentDate, market, stage})
                });
                const data = await res.json();
                if(data.status !== 'success') throw new Error(data.message || 'Hit/Miss send failed');
                showRealNotification('✅ Hit/Miss Sent', (data.sent || 0) + ' target par report send hua.', 'success');
            } catch(e){ showRealNotification('❌ Hit/Miss Error', String(e.message || e), 'danger'); }
        }

        async function saveSettlementSettings(patch){
            if(!IS_MASTER) return;
            try {
                const res = await fetch('/api/save_settlement_settings', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(patch || {})});
                const data = await res.json();
                if(data.status !== 'success') throw new Error(data.message || 'Settlement setting failed');
                appState.settlementSettings = data.settlementSettings || appState.settlementSettings;
                showRealNotification('✅ Settlement Settings', 'Saved successfully.', 'success');
                render(true);
            } catch(e){ showRealNotification('❌ Settlement Error', String(e.message || e), 'danger'); }
        }

        async function saveMarketResult(idx){
            if(!IS_MASTER) return;
            const market = baseMarkets[idx]?.n || '';
            const input = document.getElementById('result-input-' + idx);
            const val = (input?.value || '').trim().replace(/\\s+/g, '');
            const stage = resultStageLabel(val);
            if(!stage){ showRealNotification('⚠️ Format Error', 'Open: 123-4 | Close: 123-45-678', 'danger'); return; }
            if(stage === 'close'){
                const rec = getResultRec(market);
                const view = resultDisplayView(rec);
                if(!view.open){ showRealNotification('⚠️ Fresh Open Missing', 'Close declare se pehle fresh open 123-4 save hona chahiye.', 'danger'); return; }
                if(!val.startsWith(view.open)){ showRealNotification('⚠️ Old/Unmatched Close', 'Close result open ' + view.open + ' se start hona chahiye.', 'danger'); return; }
            }
            if(!appState.resultTargets || !appState.resultTargets.length){
                showRealNotification('⚠️ Result Targets Missing', 'Pehle Result WhatsApp targets save karo.', 'danger');
                return;
            }
            try {
                const res = await fetch('/api/save_result', {
                    method:'POST', headers:{'Content-Type':'application/json'},
                    body: JSON.stringify({date: currentDate, market, result: val, source:'manual'})
                });
                const data = await res.json();
                if(data.status !== 'success') throw new Error(data.message || 'Result save failed');
                appState.resultRecords = data.resultRecords || appState.resultRecords;
                showRealNotification(stage === 'open' ? '🏆 Open Result Saved' : '🏆 Close Result Saved', market + ' result Gateway se auto declare hoga.', 'success');
                render(true);
            } catch(e){ showRealNotification('❌ Error', String(e.message || e), 'danger'); }
        }





        // ==========================================
        // BAILEYS AUTO-SCHEDULE UI HELPERS
        // ==========================================
        function titanScheduleDict(type){ return type === 'ank' ? 'data' : (type === 'jodi' ? 'jodiData' : 'pannelData'); }
        function titanTargetsText(rec){
            let arr = (rec && Array.isArray(rec.schTargets)) ? rec.schTargets : [];
            return arr.length ? arr.join(', ') : 'No target';
        }
        function titanCleanTargets(raw){
            if(!raw) return [];
            return String(raw).split(/[\\r\\n,]+/).map(x => x.trim()).filter(Boolean);
        }
        async function saveScheduleNow(type, idx){
            if(!IS_MASTER) return;
            try {
                ensureDataStruct();
                const dn = titanScheduleDict(type);
                const rec = state.dayRecords[currentDate][dn][idx] || {};
                await fetch('/api/schedule_targets', {
                    method: 'POST',
                    headers: {'Content-Type':'application/json'},
                    body: JSON.stringify({
                        profileId: appState.activeId,
                        type: type,
                        index: idx,
                        time: rec.schTime || '',
                        targets: Array.isArray(rec.schTargets) ? rec.schTargets : [],
                        record: rec
                    })
                });
            } catch(e) { console.log('schedule save failed', e); }
        }
        async function setScheduleTime(type, idx, value){
            if(!IS_MASTER) return;
            ensureDataStruct();
            const dn = titanScheduleDict(type);
            if(!state.dayRecords[currentDate][dn][idx]) state.dayRecords[currentDate][dn][idx] = {s:'WAIT', d:'', r:''};
            state.dayRecords[currentDate][dn][idx].schTime = value || '';
            await saveScheduleNow(type, idx);
            autoSave();
            showRealNotification('⏰ Schedule Time', value ? ('Time set: '+value) : 'Time cleared', 'info');
        }
        async function pickCardContact(type, idx){
            if(!IS_MASTER) return;
            ensureDataStruct();
            const dn = titanScheduleDict(type);
            if(!state.dayRecords[currentDate][dn][idx]) state.dayRecords[currentDate][dn][idx] = {s:'WAIT', d:'', r:''};
            let rec = state.dayRecords[currentDate][dn][idx];
            if(!Array.isArray(rec.schTargets)) rec.schTargets = [];

            try {
                if(navigator.contacts && navigator.contacts.select){
                    const picked = await navigator.contacts.select(['name','tel'], {multiple:true});
                    picked.forEach(c => (c.tel || []).forEach(t => { if(t && !rec.schTargets.includes(t)) rec.schTargets.push(t); }));
                    await saveScheduleNow(type, idx); autoSave(); render(true);
                    showRealNotification('✅ Contact Picked', rec.schTargets.length+' target saved in this card.', 'success');
                    return;
                }
            } catch(e) {}

            let v = prompt('Phone number / WhatsApp JID / Group JID add karo. Multiple ke liye comma use karo:', rec.schTargets.join(', '));
            if(v !== null){ rec.schTargets = titanCleanTargets(v); await saveScheduleNow(type, idx); autoSave(); render(true); }
        }
        async function syncWhatsAppTargetsToCard(type, idx){
            if(!IS_MASTER) return;
            try{
                const res = await fetch('/api/wa_targets');
                const data = await res.json();
                const all = [...(data.contacts || []), ...(data.groups || [])];
                if(!all.length){ showRealNotification('⚠️ Gateway Offline', 'Pehle Termux me node Gateway.js run karo, phir sync karo.', 'danger'); return; }
                const labels = all.slice(0, 80).map((x,n)=>`${n+1}. ${x.name || x.id}  [${x.type || ''}]`).join('\\n');
                const ans = prompt('Select target number(s) comma se.\\n\\n'+labels);
                if(!ans) return;
                const selected = ans.split(',').map(x=>parseInt(x.trim(),10)-1).filter(n=>n>=0 && n<all.length).map(n=>all[n].id);
                if(!selected.length) return;
                ensureDataStruct();
                const dn = titanScheduleDict(type);
                if(!state.dayRecords[currentDate][dn][idx]) state.dayRecords[currentDate][dn][idx] = {s:'WAIT', d:'', r:''};
                let rec = state.dayRecords[currentDate][dn][idx];
                if(!Array.isArray(rec.schTargets)) rec.schTargets = [];
                selected.forEach(t => { if(!rec.schTargets.includes(t)) rec.schTargets.push(t); });
                await saveScheduleNow(type, idx); autoSave(); render(true);
                showRealNotification('✅ WhatsApp Synced', selected.length+' target added in card.', 'success');
            }catch(e){ showRealNotification('❌ Sync Error', String(e.message || e), 'danger'); }
        }
        function clearCardTargets(type, idx){
            if(!IS_MASTER) return;
            ensureDataStruct();
            const dn = titanScheduleDict(type);
            if(state.dayRecords[currentDate][dn][idx]){
                state.dayRecords[currentDate][dn][idx].schTargets = [];
                saveScheduleNow(type, idx); autoSave(); render(true);
            }
        }

        // ==========================================
        // AUTO-TRICK LOGIC WITH ADMIN SYNC
        // ==========================================
        function applyTrick(type, i, trickNum) {
            const inputEl = document.getElementById(`in-d-${type}-${i}`);
            if (!inputEl) return;
            let val = inputEl.value;
            let digits = val.match(/\\d/g);
            if (!digits || digits.length < 10) {
                showRealNotification('⚠️ Error', 'Trick ke liye pehle 10 digits enter karein!', 'danger');
                return;
            }
            ensureDataStruct();
            const dictName = type === 'ank' ? 'data' : (type === 'jodi' ? 'jodiData' : 'pannelData');
            if(!state.dayRecords[currentDate][dictName][i]) state.dayRecords[currentDate][dictName][i] = { s: 'WAIT', d: '', r: '' };

            // Backup for current profile
            if(!state.dayRecords[currentDate][dictName][i].od || digits.length >= 10) {
                state.dayRecords[currentDate][dictName][i].od = val;
            }

            let res = [];
            if (trickNum === 1) { res = [digits[1], digits[3], digits[5], digits[7], digits[9]]; }
            else if (trickNum === 2) { res = [digits[0], digits[2], digits[4], digits[6], digits[8]]; }
            else if (trickNum === 3) { res = [digits[1], digits[2], digits[3], digits[6], digits[7], digits[8]]; }
            const formatted = res.join(', ');

            state.dayRecords[currentDate][dictName][i].d = formatted;
            state.dayRecords[currentDate][dictName][i].trick = 'T' + trickNum;

            // --- GLOBAL SYNC LOGIC ---
            if(appState.activeId === 'admin1') {
                Object.keys(appState.profiles).forEach(pid => {
                    if(pid === 'admin1') return;
                    let pState = appState.profiles[pid];
                    ensureDataStructForProfile(pState);
                    if(!pState.dayRecords[currentDate][dictName][i]) pState.dayRecords[currentDate][dictName][i] = { s: 'WAIT', d: '', r: '' };

                    if(!pState.dayRecords[currentDate][dictName][i].od || digits.length >= 10) {
                        pState.dayRecords[currentDate][dictName][i].od = val;
                    }
                    pState.dayRecords[currentDate][dictName][i].d = formatted;
                    pState.dayRecords[currentDate][dictName][i].trick = 'T' + trickNum;
                });
            }

            inputEl.value = formatted;
            autoSave(); render(true);
        }

        function undoTrick(type, i) {
            ensureDataStruct();
            const dictName = type === 'ank' ? 'data' : (type === 'jodi' ? 'jodiData' : 'pannelData');
            let rec = state.dayRecords[currentDate][dictName][i];
            if(rec && rec.od) {
                const originalDigits = rec.od;
                rec.d = originalDigits;
                delete rec.trick;

                // --- GLOBAL SYNC LOGIC ---
                if(appState.activeId === 'admin1') {
                    Object.keys(appState.profiles).forEach(pid => {
                        if(pid === 'admin1') return;
                        let pState = appState.profiles[pid];
                        ensureDataStructForProfile(pState);
                        let r = pState.dayRecords[currentDate][dictName][i];
                        if(r && r.od) {
                            r.d = r.od;
                            delete r.trick;
                        }
                    });
                }

                autoSave(); render(true);
                showRealNotification('🔙 Undo', 'Original digits wapas aa gaye!', 'info');
            }
        }

        function getTrickHistoryHTML(type, idx) {
            if (type === 'jodi') return '';
            const dictName = type === 'ank' ? 'data' : 'pannelData';
            let html = '<div class="flex gap-1 mt-3 pt-3 border-t border-[rgba(255,255,255,0.05)] items-center overflow-x-auto no-scrollbar shrink-0"><span class="text-[8px] font-bold text-[var(--text-muted)] uppercase mr-1 shrink-0"><i class="fas fa-history"></i> 7-DAY:</span>';
            let dObj = new Date(currentDate);
            let dayOfWeek = dObj.getDay();
            let diff = dObj.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1);
            let monday = new Date(dObj);
            monday.setDate(diff);

            let badges = [];
            for(let j = 0; j < 7; j++) {
                let pastDate = new Date(monday);
                pastDate.setDate(monday.getDate() + j);
                let dateStr = pastDate.getFullYear() + '-' + String(pastDate.getMonth() + 1).padStart(2, '0') + '-' + String(pastDate.getDate()).padStart(2, '0');
                let trick = '-';
                let tColor = 'bg-[var(--surface-light)] text-[var(--text-muted)] border-[var(--border)]';
                if (state.dayRecords[dateStr] && state.dayRecords[dateStr][dictName] && state.dayRecords[dateStr][dictName][idx]) {
                    let rec = state.dayRecords[dateStr][dictName][idx];
                    if (rec.trick) {
                        trick = rec.trick;
                        if (trick === 'T1') tColor = 'bg-[rgba(123,143,255,0.1)] text-[var(--purple)] border-[rgba(123,143,255,0.2)]';
                        else if (trick === 'T2') tColor = 'bg-[rgba(250,199,72,0.1)] text-[var(--amber)] border-[rgba(250,199,72,0.2)]';
                        else if (trick === 'T3') tColor = 'bg-[rgba(0,194,111,0.1)] text-[var(--green)] border-[rgba(0,194,111,0.2)]';
                    }
                }
                let dayName = pastDate.toLocaleDateString('en-US', {weekday: 'short'}).toUpperCase();
                badges.push(`<div class="flex flex-col items-center shrink-0"><span class="text-[6px] text-[var(--text-muted)] font-bold mb-0.5">${dayName}</span><span class="text-[8px] px-1.5 py-0.5 rounded font-black border ${tColor}">${trick}</span></div>`);
            }
            html += badges.join('<div class="w-px h-3 bg-[var(--surface-mid)] mx-0.5 shrink-0"></div>');
            html += '</div>';
            return html;
        }
        // ==========================================

        function ensureDataStructForProfile(pState) {
            if(!pState) return;
            if(!pState.config) pState.config = {};
            if(!pState.config.ank) pState.config.ank = {cap: 0, tgt: 0};
            if(!pState.config.jodi) pState.config.jodi = {cap: 0, tgt: 0};
            if(!pState.config.pannel) pState.config.pannel = {cap: 0, tgt: 0};
            if(typeof pState.config.ankSplit === 'undefined') pState.config.ankSplit = true;
            if(typeof pState.config.panSplit === 'undefined') pState.config.panSplit = true;
            if(typeof pState.config.capital === 'undefined') pState.config.capital = 0;
            if(typeof pState.config.dayTarget === 'undefined') pState.config.dayTarget = 0;
            if(typeof pState.vipAccessEnabled === 'undefined') pState.vipAccessEnabled = true;
            if(!pState.dayRecords) pState.dayRecords = {};
            if(!pState.dayRecords[currentDate]) pState.dayRecords[currentDate] = {};
            if(!pState.dayRecords[currentDate].data) pState.dayRecords[currentDate].data = {};
            if(!pState.dayRecords[currentDate].jodiData) pState.dayRecords[currentDate].jodiData = {};
            if(!pState.dayRecords[currentDate].pannelData) pState.dayRecords[currentDate].pannelData = {};
            if(!pState.dayRecords[currentDate].visAnk) pState.dayRecords[currentDate].visAnk = {};
            if(!pState.dayRecords[currentDate].visJodi) pState.dayRecords[currentDate].visJodi = {};
            if(!pState.dayRecords[currentDate].visPan) pState.dayRecords[currentDate].visPan = {};
        }

        function ensureDataStruct() { ensureDataStructForProfile(state); }

        function renderAppBar() {
            const container = document.getElementById('top-bar-container');
            if(!container) return;

            const showSplitToggle = (IS_MASTER && mainNav === 'ledger' && (activeTab === 'ank' || activeTab === 'pannel'));
            const splitToggleChecked = (activeTab === 'ank') ? state.config.ankSplit : state.config.panSplit;

            let leftIcon = '';
            if (IS_MASTER && appState.activeId === 'admin1') {
                leftIcon = `<button onclick="toggleSidebar()" class="w-9 h-9 rounded-xl flex items-center justify-center text-[var(--text-muted)] hover:text-white active:scale-95 transition-all"><i class="fas fa-bars text-lg"></i></button>`;
            } else if (IS_MASTER && appState.activeId !== 'admin1') {
                leftIcon = `<button onclick="backToMasterUI()" class="w-9 h-9 rounded-xl flex items-center justify-center text-[var(--primary)] active:scale-95 transition-all"><i class="fas fa-arrow-left text-lg"></i></button>`;
            } else {
                leftIcon = `<button onclick="toggleSidebar()" class="w-9 h-9 rounded-xl flex items-center justify-center text-[var(--text-muted)] hover:text-white active:scale-95 transition-all"><i class="fas fa-bars text-lg"></i></button>`;
            }

            let titleSection = (appState.activeId === 'admin1')
                ? `<div class="flex flex-col items-center"><h1 class="text-[15px] font-black tracking-tight text-white leading-tight">TITAN NOVA</h1><span class="text-[9px] text-[var(--primary)] font-bold uppercase tracking-wider">Admin Panel</span></div>`
                : `<div class="flex flex-col items-center"><h1 class="text-[15px] font-black tracking-tight text-white leading-tight">${state.name}</h1><span class="text-[9px] text-[var(--primary)] font-bold uppercase tracking-wider">VIP App${!IS_MASTER ? ' • LIVE' : ''}</span></div>`;

            let rightSection = `<div class="flex items-center gap-2">`;

            if (!IS_MASTER) {
                let bellColor = ('Notification' in window && Notification.permission === 'granted') ? 'text-[var(--green)]' : 'text-[var(--text-muted)]';
                rightSection += `
                    <button onclick="requestNotificationPermission()" class="w-9 h-9 rounded-xl flex items-center justify-center ${bellColor} active:scale-95 transition-all">
                        <i class="fas fa-bell text-lg"></i>
                    </button>`;
            }

            if (IS_MASTER) {
                rightSection += `
                    <button onclick="showInstallModal()" class="w-9 h-9 rounded-xl flex items-center justify-center text-[var(--text-muted)] active:scale-95 transition-all">
                        <i class="fas fa-download text-lg"></i>
                    </button>`;
            }

            if (showSplitToggle) {
                rightSection += `
                    <div class="flex items-center gap-1.5 h-9 px-2 bg-[var(--surface-light)] border border-[var(--border)] rounded-xl">
                        <label class="switch transform scale-75 m-0">
                            <input type="checkbox" onchange="toggleHybridMode(this.checked)" ${splitToggleChecked ? 'checked' : ''}>
                            <span class="slider"></span>
                        </label>
                        <span class="text-[8px] font-bold uppercase ${splitToggleChecked ? 'text-[var(--primary)]' : 'text-[var(--text-muted)]'}">Split</span>
                    </div>`;
            }
            rightSection += `
                <div class="relative w-9 h-9 bg-[var(--surface-light)] rounded-xl flex items-center justify-center border border-[var(--border)] text-[var(--text-muted)] overflow-hidden active:scale-95 transition-all">
                    <i class="fas fa-calendar-alt text-sm"></i>
                    <input type="date" value="${currentDate}" onchange="changeDate(this.value)" class="absolute inset-0 opacity-0 w-full h-full cursor-pointer">
                </div>
            </div>`;

            container.innerHTML = `${leftIcon} ${titleSection} ${rightSection}`;
        }

        // ── VIP capability helpers ──────────────────────────────
        function isVipPlanActive() {
            if(IS_MASTER) return true;
            const p = appState.profiles[appState.activeId] || {};
            const exp = p.expiryDate || '';
            if(!exp) return false;
            const expObj = new Date(exp); const today = new Date();
            today.setHours(0,0,0,0); expObj.setHours(0,0,0,0);
            return expObj >= today;
        }
        function vipCanEdit() {
            if(IS_MASTER) return true;
            const p = appState.profiles[appState.activeId] || {};
            return (p.vipAccessEnabled !== false);
        }
        function vipCanViewOnly() {
            if(IS_MASTER) return false;
            const p = appState.profiles[appState.activeId] || {};
            return (p.vipAccessEnabled === false);
        }
        // ────────────────────────────────────────────────────────

        function renderBottomNav() {
            let navHtml = '';
            const navItems = [
                { id: 'ledger', icon: 'fa-gamepad', label: 'Ledger' },
                { id: 'audit', icon: 'fa-chart-pie', label: 'Audit' }
            ];

            if(IS_MASTER) {
                navItems.push({ id: 'settings', icon: 'fa-cog', label: 'Setup' });
                if(appState.activeId === 'admin1') {
                    navItems.splice(1, 0, { id: 'clients', icon: 'fa-users', label: 'VIPs' });
                    navItems.splice(2, 0, { id: 'wallets', icon: 'fa-wallet', label: 'Wallet' });
                    navItems.splice(3, 0, { id: 'entries', icon: 'fa-receipt', label: 'Entries' });
                    navItems.splice(4, 0, { id: 'payments', icon: 'fa-rupee-sign', label: 'Pay' });
                    navItems.splice(5, 0, { id: 'results', icon: 'fa-trophy', label: 'Results' });
                    navItems.splice(6, 0, { id: 'forward', icon: 'fa-share-nodes', label: 'Forward' });
                    navItems.splice(7, 0, { id: 'guard', icon: 'fa-shield-halved', label: 'Guard' });
                    navItems.splice(8, 0, { id: 'backup', icon: 'fa-file-export', label: 'Backup' });
                    navItems.splice(9, 0, { id: 'health', icon: 'fa-heart-pulse', label: 'Health' });
                    navItems.splice(10, 0, { id: 'smart', icon: 'fa-bolt', label: 'AI Scan' });
                }
            } else {
                // VIP always sees Settings tab, but inputs will be disabled if Read-Only
                navItems.push({ id: 'settings', icon: 'fa-sliders-h', label: 'Settings' });
                navItems.push({ id: 'membership', icon: 'fa-crown', label: 'Member' });
            }

            navItems.forEach(item => {
                navHtml += `<div onclick="setMainNav('${item.id}')" class="nav-item ${mainNav === item.id ? 'active' : ''}"><i class="fas ${item.icon}"></i><span>${item.label}</span></div>`;
            });
            const navEl = document.getElementById('bottom-nav-container');
            navEl.innerHTML = navHtml;
            const activeItem = navEl.querySelector('.nav-item.active');
            if(activeItem) {
                setTimeout(() => {
                    try { activeItem.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' }); } catch(e) {}
                }, 0);
            }
        }

        function renderSubTabs() {
            if (mainNav !== 'ledger' && mainNav !== 'audit') return '';
            const t = (mainNav === 'ledger') ? activeTab : weeklyTabType;
            return `
                <div class="pill-tabs">
                    <button onclick="setSubTab('ank')" class="pill-tab ${t === 'ank' ? 'active' : ''}">Ank <span class="text-[9px] opacity-60 ml-1">x9.5</span></button>
                    <button onclick="setSubTab('jodi')" class="pill-tab ${t === 'jodi' ? 'active' : ''}">Jodi <span class="text-[9px] opacity-60 ml-1">x95</span></button>
                    <button onclick="setSubTab('pannel')" class="pill-tab ${t === 'pannel' ? 'active' : ''}">Pannel <span class="text-[9px] opacity-60 ml-1">x150</span></button>
                </div>
            `;
        }

        function renderWalletHUD() {
            let activeStats; let pLabel = "Portfolio";
            let t = (mainNav === 'ledger') ? activeTab : weeklyTabType;
            if(t === 'ank') { activeStats = globalStats.ank; pLabel = "Ank Port."; }
            else if(t === 'jodi') { activeStats = globalStats.jodi; pLabel = "Jodi Port."; }
            else if(t === 'pannel') { activeStats = globalStats.pannel; pLabel = "Pan Port."; }

            const capital   = parseFloat(state.config.capital)   || 0;
            const dayTarget = parseFloat(state.config.dayTarget)  || 0;
            const totalPL   = globalStats.ank.pl + globalStats.jodi.pl + globalStats.pannel.pl;
            const dayPct    = dayTarget > 0 ? Math.min(100, Math.max(0, Math.round((totalPL / dayTarget) * 100))) : 0;

            const capitalRow = ((capital > 0 || dayTarget > 0)) ? `
                <div class="stat-box col-span-2 px-4 py-2.5" style="border-color:rgba(0,194,111,0.2);background:rgba(0,194,111,0.04)">
                    <div class="flex justify-between items-center mb-1.5">
                        <span class="stat-lbl" style="color:var(--green)">Capital: ₹${capital.toLocaleString()}</span>
                        <span class="stat-lbl ${totalPL >= 0 ? 'text-[var(--green)]' : 'text-[var(--rose)]'}">${totalPL >= 0 ? '+' : ''}₹${totalPL.toLocaleString()} / ₹${dayTarget.toLocaleString()} <span class="font-black">${dayPct}%</span></span>
                    </div>
                    <div class="h-1.5 bg-[var(--surface-light)] rounded-full overflow-hidden">
                        <div class="h-full rounded-full transition-all" style="width:${dayPct}%;background:${totalPL >= 0 ? 'var(--green)' : 'var(--rose)'}"></div>
                    </div>
                </div>` : '';

            return `
                <div class="wallet-hud">
                    <div class="stat-box">
                        <p class="stat-lbl">Total Spent</p>
                        <p id="stat-spent" class="stat-val text-[var(--text-muted)]">₹${activeStats.spent.toLocaleString()}</p>
                    </div>
                    <div class="stat-box" style="border-color:rgba(0,194,111,0.2); background:rgba(0,194,111,0.05)">
                        <p class="stat-lbl" style="color:var(--green)">Net P/L</p>
                        <p id="stat-pl" class="stat-val ${activeStats.pl >= 0 ? 'text-[#00C26F]' : 'text-[#FF5D5D]'}">${activeStats.pl >= 0 ? '+' : ''}₹${activeStats.pl.toLocaleString()}</p>
                    </div>
                    <div class="stat-box col-span-2 flex justify-between items-center" style="border-color:rgba(42,171,238,0.2); background:rgba(42,171,238,0.05)">
                        <div>
                            <p id="stat-port-label" class="stat-lbl" style="color:var(--primary)">${pLabel}</p>
                            <p id="stat-wallet" class="stat-val text-white">₹${activeStats.port.toLocaleString()}</p>
                        </div>
                        <div class="text-right">
                            <p class="stat-lbl" style="color:var(--rose)">Max Risk</p>
                            <p id="stat-maxloss" class="stat-val text-[#FF5D5D]">-₹${activeStats.maxLoss.toLocaleString()}</p>
                        </div>
                    </div>
                    ${capitalRow}
                </div>
            `;
        }

        function toggleHybridMode(isChecked) { ensureDataStruct(); if(activeTab === 'ank') state.config.ankSplit = isChecked; else if(activeTab === 'pannel') state.config.panSplit = isChecked; autoSave(); render(true); }
        function toggleMarketVis(visType, bmName, isChecked) { ensureDataStruct(); state.dayRecords[currentDate][visType][bmName] = isChecked; autoSave(); render(true); }
        function toggleAllMarkets(visType, isChecked) { ensureDataStruct(); const arr = visType === 'visJodi' ? baseMarkets : markets; arr.forEach(m => { state.dayRecords[currentDate][visType][m.n] = isChecked; }); autoSave(); render(true); }
        function setMainNav(nav) { mainNav = nav; render(false); }
        function setSubTab(tab) { if(mainNav === 'ledger') activeTab = tab; else if(mainNav === 'audit') weeklyTabType = tab; render(false); }
        function changeDate(d) { currentDate = d; render(false); }
        function toggleSidebar() { document.getElementById('sidebar').classList.toggle('open'); document.getElementById('sidebar-overlay').classList.toggle('hidden'); }

        async function saveMaster(silent = false) {
            if(!IS_MASTER) return;
            try {
                // Save to localStorage first (instant mobile persistence)
                try { localStorage.setItem(LOCAL_KEY, JSON.stringify(appState)); } catch(e) {}
                // Then sync to PythonAnywhere + Firebase
                await fetch('/save', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(appState) });
                if(!silent) {
                    const syncBtn = document.getElementById('ledger-sync-btn');
                    if(syncBtn) {
                        const oText = syncBtn.innerHTML;
                        syncBtn.innerHTML = '<i class="fas fa-check mr-2"></i> Synced';
                        syncBtn.style.background = "var(--green)"; syncBtn.style.color = "#fff";
                        setTimeout(() => { syncBtn.innerHTML = oText; syncBtn.style.background = ""; syncBtn.style.color = ""; }, 2000);
                    }
                }
            } catch (e) {}
        }

        function getHistoricalMultiplier(type, idx, currentDateStr) {
            if(!IS_MASTER) return 1.0;
            const mRecs = appState.profiles['admin1'].dayRecords;
            const dates = Object.keys(mRecs).sort();
            const currPos = dates.indexOf(currentDateStr);
            const dictName = type === 'ank' ? 'data' : (type === 'jodi' ? 'jodiData' : 'pannelData');
            let dailyBoost = 0;
            if (currPos > 0) {
                let consecutiveFails = 0;
                for (let j = currPos - 1; j >= 0; j--) {
                    const rec = mRecs[dates[j]]?.[dictName]?.[idx];
                    if (!rec) continue;
                    if (rec.s === 'FAIL') consecutiveFails++;
                    else if (rec.s === 'PASS') break;
                }
                dailyBoost = consecutiveFails * 0.20;
            }
            let weeklyBoost = 0;
            const currObj = new Date(currentDateStr);
            currObj.setDate(currObj.getDate() - 7);
            const yyyy = currObj.getFullYear();
            const mm = String(currObj.getMonth() + 1).padStart(2, '0');
            const dd = String(currObj.getDate()).padStart(2, '0');
            const lastWeekRec = mRecs[`${yyyy}-${mm}-${dd}`]?.[dictName]?.[idx];
            if (lastWeekRec && lastWeekRec.s === 'FAIL') weeklyBoost = 0.10;
            return 1.0 + dailyBoost + weeklyBoost;
        }

        function getBaseNameForMarket(fullMarketName) { if (!fullMarketName) return null; const sorted = [...baseMarkets].sort((a, b) => b.n.length - a.n.length); for(let bm of sorted) { if(fullMarketName.includes(bm.n)) return bm.n; } return null; }

        function runLiveSync(changedType = null, changedIdx = -1, fieldChanged = null) {
            ensureDataStruct();
            globalStats = { ank: { spent: 0, win: 0, pl: 0, port: 0, maxLoss: 0 }, jodi: { spent: 0, win: 0, pl: 0, port: 0, maxLoss: 0 }, pannel: { spent: 0, win: 0, pl: 0, port: 0, maxLoss: 0 } };
            let debt = { ankOpen: 0, ankClose: 0, ankUnified: 0, jodi: 0, panOpen: 0, panClose: 0, panUnified: 0 };
            let unreal = { ankOpen: 0, ankClose: 0, ankUnified: 0, jodi: 0, panOpen: 0, panClose: 0, panUnified: 0 };
            const record = state.dayRecords[currentDate];

            const processGroup = (type, dataDict, arr, marginMultiplier, trackPrefix) => {
                const targetProf = parseFloat(state.config[type].tgt) || 0;
                const visDict = type === 'ank' ? state.dayRecords[currentDate].visAnk : (type === 'jodi' ? state.dayRecords[currentDate].visJodi : state.dayRecords[currentDate].visPan);
                const isSplitOn = (type === 'ank') ? state.config.ankSplit : (type === 'pannel' ? state.config.panSplit : false);
                let runningChronologicalPL = 0; let maxDip = 0;

                arr.forEach((m, i) => {
                    if (visDict && visDict[m.n] === false) return;
                    let trackKey = trackPrefix;
                    if (trackPrefix !== 'jodi') trackKey += (isSplitOn ? (m.n.includes("OPEN") ? "Open" : "Close") : "Unified");
                    const d = dataDict[i] || { s: 'WAIT', d: '', r: '' };
                    const count = (d.d ? String(d.d) : '').split(/[, ]+/).filter(x => x.trim()).length;
                    const invest = count * (parseFloat(d.r) || 0);

                    if (d.s === 'FAIL') { runningChronologicalPL -= invest; if (runningChronologicalPL < maxDip) maxDip = runningChronologicalPL; debt[trackKey] += invest; unreal[trackKey] += 1; globalStats[type].spent += invest; }
                    else if (d.s === 'PASS') { runningChronologicalPL -= invest; if (runningChronologicalPL < maxDip) maxDip = runningChronologicalPL; const winAmount = (parseFloat(d.r) || 0) * marginMultiplier; runningChronologicalPL += winAmount; globalStats[type].spent += invest; globalStats[type].win += winAmount; debt[trackKey] = 0; unreal[trackKey] = 0; }
                    else if (d.s === 'SKIP') { unreal[trackKey] += 1; }
                    else if (d.s === 'WAIT') {
                        if (IS_MASTER && fieldChanged !== 'r' || changedType !== type || changedIdx !== i) {
                            const rIn = document.getElementById(`in-r-${type}-${i}`);
                            if(rIn && count > 0) {
                                const margin = marginMultiplier - count;
                                if(margin > 0) {
                                    const nextRate = (debt[trackKey] + ((unreal[trackKey] + 1) * targetProf)) / margin;
                                    const finalRate = Math.ceil((nextRate * getHistoricalMultiplier(type, i, currentDate)) / 10) * 10;
                                    state.dayRecords[currentDate][type === 'ank' ? 'data' : (type === 'jodi' ? 'jodiData' : 'pannelData')][i].r = Math.max(10, finalRate).toString();
                                    if(rIn) rIn.value = state.dayRecords[currentDate][type === 'ank' ? 'data' : (type === 'jodi' ? 'jodiData' : 'pannelData')][i].r;
                                }
                            }
                        }
                    }
                });
                globalStats[type].pl = globalStats[type].win - globalStats[type].spent;
                const masterCap = IS_MASTER ? (parseFloat(appState.profiles['admin1'].config[type].cap) || 0) : 0;
                globalStats[type].port = (parseFloat(state.config[type].cap) || masterCap) + globalStats[type].pl;
                globalStats[type].maxLoss = Math.abs(maxDip);
            };

            processGroup('ank', record.data, markets, 9.5, 'ank');
            processGroup('jodi', record.jodiData, baseMarkets, 95.0, 'jodi');
            processGroup('pannel', record.pannelData, markets, 150.0, 'pan');

            checkTargetsAndLimits();
        }

        function createLedgerList(type, arr, dictName) {
            ensureDataStruct();
            const list = document.createElement('div'); list.className = 'px-3 pb-4 pt-1';
            const visDict = type === 'ank' ? state.dayRecords[currentDate].visAnk : (type === 'jodi' ? state.dayRecords[currentDate].visJodi : state.dayRecords[currentDate].visPan);

            arr.forEach((m, i) => {
                if (visDict && visDict[m.n] === false) return;
                const isOpen = m.n.includes("OPEN");
                const isJodi = type === 'jodi';
                const trackColor = isJodi ? 'text-[#B85CFF]' : (isOpen ? 'text-[var(--primary)]' : 'text-[var(--amber)]');
                const boostPercent = Math.round((getHistoricalMultiplier(type, i, currentDate) - 1) * 100);
                const memoryBadge = boostPercent > 0 ? `<span class="text-[8px] bg-[var(--rose)] text-white px-1.5 py-0.5 rounded font-bold uppercase ml-2">+${boostPercent}%</span>` : '';
                const d = state.dayRecords[currentDate][dictName][i] || { s: 'WAIT', d: '', r: '' };
                const trickBadge = d.trick ? `<span class="text-[8px] bg-[var(--purple)] text-white px-1.5 py-0.5 rounded font-black uppercase ml-2">${d.trick}</span>` : '';

                const card = document.createElement('div');

                if (!IS_MASTER) {
                    let sBg = ''; let sLbl = 'text-[var(--text-muted)]'; let sIcon = 'fa-clock'; let sTxt = 'WAITING';
                    if(d.s === 'PASS') { sBg = 'border-l-4 border-l-[var(--green)]'; sLbl = 'text-[var(--green)]'; sIcon = 'fa-check-circle'; sTxt = 'PASS'; }
                    else if(d.s === 'FAIL') { sBg = 'border-l-4 border-l-[var(--rose)]'; sLbl = 'text-[var(--rose)]'; sIcon = 'fa-times-circle'; sTxt = 'FAIL'; }
                    else if(d.s === 'SKIP') { sBg = 'border-l-4 border-l-[var(--text-muted)]'; sLbl = 'text-[var(--text-muted)]'; sIcon = 'fa-minus-circle'; sTxt = 'SKIP'; }

                    const canEdit = vipCanEdit();

                    if(canEdit) {
                        // ── Full interactive card for VIP with access enabled ──
                        const isCardLocked = (d.s !== 'WAIT');
                        if(isCardLocked) {
                            card.className = `native-card ${sBg}`;
                            card.innerHTML = `
                                <div class="flex justify-between items-center px-4 py-2.5 border-b border-[var(--border)]">
                                    <span class="text-[12px] font-bold uppercase text-white">${m.n}</span> ${trickBadge}
                                    <span class="text-[10px] font-bold ${sLbl} flex items-center gap-1"><i class="fas ${sIcon}"></i> ${sTxt}</span>
                                </div>
                                <div class="p-4 grid grid-cols-2 gap-3 mb-2">
                                    <div class="bg-[var(--surface-light)] p-3 rounded-xl border border-[var(--border)]">
                                        <p class="stat-lbl mb-1">Target Digits</p>
                                        <p class="text-[15px] font-black text-white">${d.d || '---'}</p>
                                    </div>
                                    <div class="bg-[var(--surface-light)] p-3 rounded-xl border border-[var(--border)]">
                                        <p class="stat-lbl mb-1">Amount / Pt</p>
                                        <p class="text-[15px] font-black text-white">₹${d.r || 0}</p>
                                    </div>
                                </div>
                                <button onclick="copyIntel('${type}', ${i}, this)" class="w-full bg-[rgba(42,171,238,0.1)] text-[var(--primary)] py-2.5 rounded-xl font-bold text-[11px] uppercase active:scale-95 transition-all flex justify-center items-center gap-2 border border-[rgba(42,171,238,0.2)] mx-4 mb-3" style="width:calc(100% - 2rem)">
                                    <i class="fas fa-copy"></i> Copy Card Data
                                </button>
                            `;
                        } else {
                            card.className = `native-card`;
                            card.innerHTML = `
                                <div class="flex justify-between items-center px-4 py-2.5 border-b border-[var(--border)]">
                                    <span class="text-[12px] font-bold uppercase ${trackColor}">${m.n}</span> ${trickBadge}
                                    <span class="text-[10px] font-bold ${sLbl} flex items-center gap-1"><i class="fas ${sIcon}"></i> ${sTxt}</span>
                                </div>
                                <div class="p-4">
                                    <div class="grid grid-cols-2 gap-3 mb-3">
                                        <div class="relative flex flex-col">
    <label class="absolute -top-2 left-3 z-10 bg-[var(--surface)] px-1 text-[8px] font-bold text-[var(--text-muted)] uppercase">Digits</label>
    <input id="in-d-${type}-${i}" oninput="updateMarket('${type}', ${i}, 'd', this.value)" value="${d.d || ''}" placeholder="${type === 'jodi' ? 'Jodi' : 'Values'}" class="native-input text-[var(--amber)]">
    ${type !== 'jodi' ? `
    <div class="flex gap-1 mt-2 justify-center">
        <button onclick="applyTrick('${type}', ${i}, 1)" class="flex-1 text-[9px] bg-[rgba(123,143,255,0.1)] border border-[rgba(123,143,255,0.2)] text-[var(--purple)] py-1.5 rounded font-black active:scale-90 transition-transform shadow-sm">T1</button>
        <button onclick="applyTrick('${type}', ${i}, 2)" class="flex-1 text-[9px] bg-[rgba(250,199,72,0.1)] border border-[rgba(250,199,72,0.2)] text-[var(--amber)] py-1.5 rounded font-black active:scale-90 transition-transform shadow-sm">T2</button>
        <button onclick="applyTrick('${type}', ${i}, 3)" class="flex-1 text-[9px] bg-[rgba(0,194,111,0.1)] border border-[rgba(0,194,111,0.2)] text-[var(--green)] py-1.5 rounded font-black active:scale-90 transition-transform shadow-sm">T3</button>
        ${d.trick ? `<button onclick="undoTrick('${type}', ${i})" class="flex-none px-2.5 text-[10px] bg-[rgba(255,93,93,0.1)] border border-[rgba(255,93,93,0.2)] text-[var(--rose)] py-1.5 rounded font-black active:scale-90 transition-transform shadow-sm"><i class="fas fa-undo"></i></button>` : ''}
    </div>
    ${getTrickHistoryHTML(type, i)}
    ` : ''}
                                        </div>
                                        <div class="relative">
                                            <label class="absolute -top-2 left-3 bg-[var(--surface)] px-1 text-[8px] font-bold text-[var(--text-muted)] uppercase">Invest ₹</label>
                                            <input id="in-r-${type}-${i}" type="number" oninput="updateMarket('${type}', ${i}, 'r', this.value)" value="${d.r || ''}" placeholder="Amount" class="native-input text-white">
                                        </div>
                                    </div>
                                    <div class="flex gap-2 mb-3">
                                        <button onclick="act('${type}', ${i}, 'PASS')" class="flex-1 bg-[var(--green)] text-white py-3 rounded-xl font-black text-[11px] uppercase active:scale-95 transition-transform shadow-[0_4px_0_rgba(0,160,94,1)] active:translate-y-1 active:shadow-none">PASS</button>
                                        <button onclick="act('${type}', ${i}, 'FAIL')" class="flex-1 bg-[var(--rose)] text-white py-3 rounded-xl font-black text-[11px] uppercase active:scale-95 transition-transform shadow-[0_4px_0_rgba(200,40,40,1)] active:translate-y-1 active:shadow-none">FAIL</button>
                                        <button onclick="act('${type}', ${i}, 'SKIP')" class="w-14 bg-[var(--surface-light)] text-[var(--text-muted)] py-3 rounded-xl font-bold text-[11px] uppercase active:scale-95 transition-transform border border-[var(--border)]"><i class="fas fa-forward"></i></button>
                                    </div>
                                    <button onclick="copyIntel('${type}', ${i}, this)" class="w-full bg-[rgba(42,171,238,0.1)] text-[var(--primary)] py-2.5 rounded-xl font-bold text-[11px] uppercase active:scale-95 transition-all flex justify-center items-center gap-2 border border-[rgba(42,171,238,0.2)]">
                                        <i class="fas fa-copy"></i> Copy Card Data
                                    </button>
                                </div>
                            `;
                        }
                    } else {
                        // ── View-only card for VIP with access disabled (read-only) ──
                        card.className = `native-card ${sBg}`;
                        card.innerHTML = `
                            <div class="flex justify-between items-center px-4 py-2.5 border-b border-[var(--border)]">
                                <span class="text-[12px] font-bold uppercase ${d.s === 'WAIT' ? trackColor : 'text-white'}">${m.n}</span> ${trickBadge}
                                <span class="text-[10px] font-bold ${sLbl} flex items-center gap-1"><i class="fas ${sIcon}"></i> ${sTxt}</span>
                            </div>
                            <div class="p-4">
                                <div class="grid grid-cols-2 gap-3 mb-3">
                                    <div class="bg-[var(--surface-light)] p-3 rounded-xl border border-[var(--border)]">
                                        <p class="stat-lbl mb-1">Target Digits</p>
                                        <p class="text-[15px] font-black text-white">${d.d || '---'}</p>
                                    </div>
                                    <div class="bg-[var(--surface-light)] p-3 rounded-xl border border-[var(--border)]">
                                        <p class="stat-lbl mb-1">Amount / Pt</p>
                                        <p class="text-[15px] font-black text-white">₹${d.r || 0}</p>
                                    </div>
                                </div>
                                <button onclick="copyIntel('${type}', ${i}, this)" class="w-full bg-[rgba(42,171,238,0.1)] text-[var(--primary)] py-2.5 rounded-xl font-bold text-[11px] uppercase active:scale-95 transition-all flex justify-center items-center gap-2 border border-[rgba(42,171,238,0.2)]">
                                    <i class="fas fa-copy"></i> Copy Card Data
                                </button>
                            </div>
                        `;
                    }
                } else {
                    const isLocked = (d.s !== 'WAIT');
                    if (isLocked) {
                        let sBg = ''; let sLbl = ''; let sIcon = '';
                        if(d.s === 'PASS') { sBg = 'border-l-4 border-l-[var(--green)]'; sLbl = 'text-[var(--green)]'; sIcon = 'fa-check-circle'; }
                        else if(d.s === 'FAIL') { sBg = 'border-l-4 border-l-[var(--rose)]'; sLbl = 'text-[var(--rose)]'; sIcon = 'fa-times-circle'; }
                        else if(d.s === 'SKIP') { sBg = 'border-l-4 border-l-[var(--text-muted)]'; sLbl = 'text-[var(--text-muted)]'; sIcon = 'fa-minus-circle'; }

                        card.className = `native-card ${sBg}`;
                        card.innerHTML = `
                            <div class="flex justify-between items-center px-4 py-2.5 border-b border-[var(--border)]">
                                <span class="text-[12px] font-bold uppercase text-white">${m.n}</span> ${trickBadge}
                                <span class="text-[10px] font-bold ${sLbl} flex items-center gap-1"><i class="fas ${sIcon}"></i> ${d.s}</span>
                            </div>
                            <div class="p-4 grid grid-cols-2 gap-3">
                                <div class="bg-[var(--surface-light)] p-3 rounded-xl border border-[var(--border)]">
                                    <p class="stat-lbl mb-1">Target Digits</p>
                                    <p class="text-[15px] font-black text-white">${d.d || '-'}</p>
                                </div>
                                <div class="bg-[var(--surface-light)] p-3 rounded-xl border border-[var(--border)]">
                                    <p class="stat-lbl mb-1">Amount / Pt</p>
                                    <p class="text-[15px] font-black text-white">₹${d.r || 0}</p>
                                </div>
                            </div>
                            <button onclick="cardUndo('${type}', ${i})" class="w-full bg-[var(--surface-light)] text-[var(--text-muted)] py-3 font-bold text-[10px] uppercase flex items-center justify-center gap-2 active:opacity-70 transition-opacity border-t border-[var(--border)]">
                                <i class="fas fa-undo"></i> Unlock Round
                            </button>
                        `;
                    } else {
                        card.className = `native-card`;
                        card.innerHTML = `
                            <div class="flex justify-between items-center px-4 py-2.5 border-b border-[var(--border)]">
                                <div class="flex items-center">
                                    <span class="text-[12px] font-bold uppercase ${trackColor}">${m.n}</span> ${trickBadge}
                                    ${memoryBadge}
                                </div>
                                <div class="flex items-center gap-2">
                                    ${IS_MASTER ? `<button id="scrape-btn-${type}-${i}" onclick="scrapeMarket('${type}',${i},'${m.n}')" class="flex items-center gap-1 text-[var(--primary)] bg-[rgba(42,171,238,0.1)] border border-[rgba(42,171,238,0.2)] px-2.5 py-1 rounded-lg active:scale-95 transition-all text-[9px] font-bold uppercase"><i class="fas fa-satellite-dish"></i> Scrape</button>
<button onclick="fetchCombinedScrape(this)"  class="ml-2 bg-[#00C26F] text-white px-3 py-1 rounded-lg text-[10px] font-bold uppercase">Combo</button>` : ''}
                                    <button onclick="resetCard('${type}', ${i})" class="text-[var(--text-muted)] hover:text-[var(--rose)] active:scale-95 transition-all ml-1"><i class="fas fa-eraser"></i></button>
                                </div>
                            </div>
                            <div class="p-4">
                                <div class="grid grid-cols-2 gap-3 mb-3">
                                    <div class="relative flex flex-col">
    <label class="absolute -top-2 left-3 z-10 bg-[var(--surface)] px-1 text-[8px] font-bold text-[var(--text-muted)] uppercase">Digits</label>
    <input id="in-d-${type}-${i}" oninput="updateMarket('${type}', ${i}, 'd', this.value)" value="${d.d || ''}" placeholder="${type === 'jodi' ? 'Jodi' : 'Values'}" class="native-input text-[var(--amber)]">
    ${type !== 'jodi' ? `
    <div class="flex gap-1 mt-2 justify-center">
        <button onclick="applyTrick('${type}', ${i}, 1)" class="flex-1 text-[9px] bg-[rgba(123,143,255,0.1)] border border-[rgba(123,143,255,0.2)] text-[var(--purple)] py-1.5 rounded font-black active:scale-90 transition-transform shadow-sm">T1</button>
        <button onclick="applyTrick('${type}', ${i}, 2)" class="flex-1 text-[9px] bg-[rgba(250,199,72,0.1)] border border-[rgba(250,199,72,0.2)] text-[var(--amber)] py-1.5 rounded font-black active:scale-90 transition-transform shadow-sm">T2</button>
        <button onclick="applyTrick('${type}', ${i}, 3)" class="flex-1 text-[9px] bg-[rgba(0,194,111,0.1)] border border-[rgba(0,194,111,0.2)] text-[var(--green)] py-1.5 rounded font-black active:scale-90 transition-transform shadow-sm">T3</button>
        ${d.trick ? `<button onclick="undoTrick('${type}', ${i})" class="flex-none px-2.5 text-[10px] bg-[rgba(255,93,93,0.1)] border border-[rgba(255,93,93,0.2)] text-[var(--rose)] py-1.5 rounded font-black active:scale-90 transition-transform shadow-sm"><i class="fas fa-undo"></i></button>` : ''}
    </div>
    ${getTrickHistoryHTML(type, i)}
    ` : ''}
                                    </div>
                                    <div class="relative">
                                        <label class="absolute -top-2 left-3 bg-[var(--surface)] px-1 text-[8px] font-bold text-[var(--text-muted)] uppercase">Invest ₹</label>
                                        <input id="in-r-${type}-${i}" type="number" oninput="updateMarket('${type}', ${i}, 'r', this.value)" value="${d.r || ''}" placeholder="Amount" class="native-input text-white">
                                    </div>
                                </div>

                                <div class="flex gap-2 mb-3">
                                    <button onclick="act('${type}', ${i}, 'PASS')" class="flex-1 bg-[var(--green)] text-white py-3 rounded-xl font-black text-[11px] uppercase active:scale-95 transition-transform shadow-[0_4px_0_rgba(0,160,94,1)] active:translate-y-1 active:shadow-none">PASS</button>
                                    <button onclick="act('${type}', ${i}, 'FAIL')" class="flex-1 bg-[var(--rose)] text-white py-3 rounded-xl font-black text-[11px] uppercase active:scale-95 transition-transform shadow-[0_4px_0_rgba(200,40,40,1)] active:translate-y-1 active:shadow-none">FAIL</button>
                                    <button onclick="act('${type}', ${i}, 'SKIP')" class="w-14 bg-[var(--surface-light)] text-[var(--text-muted)] py-3 rounded-xl font-bold text-[11px] uppercase active:scale-95 transition-transform border border-[var(--border)]"><i class="fas fa-forward"></i></button>
                                </div>


                                <div class="mb-3 border border-[rgba(0,194,111,0.18)] bg-[rgba(0,194,111,0.06)] rounded-xl p-3">
                                    <div class="flex items-center justify-between gap-2 mb-2">
                                        <div class="text-[9px] font-black uppercase tracking-widest text-[var(--green)]"><i class="fas fa-robot mr-1"></i> Auto Schedule</div>
                                        <div class="text-[8px] text-[var(--text-muted)] truncate max-w-[55%]">${titanTargetsText(d)}</div>
                                    </div>
                                    <div class="grid grid-cols-2 gap-2 mb-2">
                                        <input type="time" value="${d.schTime || ''}" onchange="setScheduleTime('${type}', ${i}, this.value)" class="native-input text-[13px] py-2.5 text-[var(--green)]">
                                        <button onclick="pickCardContact('${type}', ${i})" class="bg-[rgba(42,171,238,0.12)] border border-[rgba(42,171,238,0.25)] text-[var(--primary)] py-2.5 rounded-xl font-black text-[9px] uppercase active:scale-95 transition-all"><i class="fas fa-address-book mr-1"></i> Pick Contact</button>
                                    </div>
                                    <div class="grid grid-cols-2 gap-2">
                                        <button onclick="syncWhatsAppTargetsToCard('${type}', ${i})" class="bg-[rgba(0,194,111,0.12)] border border-[rgba(0,194,111,0.25)] text-[var(--green)] py-2.5 rounded-xl font-black text-[9px] uppercase active:scale-95 transition-all"><i class="fab fa-whatsapp mr-1"></i> WA Sync</button>
                                        <button onclick="clearCardTargets('${type}', ${i})" class="bg-[rgba(255,93,93,0.08)] border border-[rgba(255,93,93,0.18)] text-[var(--rose)] py-2.5 rounded-xl font-black text-[9px] uppercase active:scale-95 transition-all"><i class="fas fa-trash mr-1"></i> Clear</button>
                                    </div>
                                </div>

                                <div class="grid grid-cols-3 gap-2 border-t border-[var(--border)] pt-3">
                                    <button onclick="copyIntel('${type}', ${i}, this)" class="text-[var(--primary)] bg-[rgba(42,171,238,0.1)] py-2.5 rounded-lg font-bold text-[9px] uppercase active:scale-95 transition-all flex justify-center items-center gap-1 border border-[rgba(42,171,238,0.15)]"><i class="fas fa-copy"></i> Copy</button>
                                    <button onclick="prepShare('${type}', ${i}, 'GUIDE')" class="text-[var(--amber)] bg-[rgba(250,199,72,0.1)] py-2.5 rounded-lg font-bold text-[9px] uppercase active:scale-95 transition-all flex justify-center items-center gap-1 border border-[rgba(250,199,72,0.15)]"><i class="fas fa-lightbulb"></i> Intel</button>
                                    <button onclick="prepShare('${type}', ${i}, 'STATUS')" class="text-[var(--green)] bg-[rgba(0,194,111,0.1)] py-2.5 rounded-lg font-bold text-[9px] uppercase active:scale-95 transition-all flex justify-center items-center gap-1 border border-[rgba(0,194,111,0.15)]"><i class="fas fa-paper-plane"></i> Result</button>
                                </div>
                            </div>`;
                    }
                }
                list.appendChild(card);
            });

            const actionRow = document.createElement('div');
            actionRow.className = 'flex gap-3 mt-2';
            if(IS_MASTER) {
                actionRow.innerHTML = `
                    <button onclick="prepDailyReportShare('${type}')" class="flex-1 bg-[var(--primary)] text-white py-4 rounded-2xl font-black text-[11px] uppercase tracking-wide active:scale-95 transition-all shadow-lg shadow-[rgba(42,171,238,0.2)]"><i class="fas fa-share-alt mr-1"></i> Day Report</button>
                    <button id="ledger-sync-btn" onclick="saveMaster(false)" class="flex-1 bg-[var(--surface-light)] border border-[var(--border)] text-white py-4 rounded-2xl font-black text-[11px] uppercase tracking-wide active:scale-95 transition-all"><i class="fas fa-cloud-upload-alt mr-1"></i> Sync</button>
                `;
            } else {
                actionRow.innerHTML = `
                    <div class="w-full flex items-center justify-center gap-2 bg-[rgba(0,194,111,0.08)] text-[var(--green)] border border-[rgba(0,194,111,0.2)] py-4 rounded-2xl font-bold text-[11px] uppercase tracking-wide">
                        <i class="fas fa-satellite-dish animate-pulse"></i> LIVE SYNC ACTIVE
                    </div>
                `;
            }
            list.appendChild(actionRow);
            return list;
        }

        function act(type, i, s) {
            if(!IS_MASTER) return;
            ensureDataStruct();
            const dictName = type === 'ank' ? 'data' : (type === 'jodi' ? 'jodiData' : 'pannelData');
            if(!state.dayRecords[currentDate][dictName][i]) state.dayRecords[currentDate][dictName][i] = { s: 'WAIT', d: '', r: '' };
            state.dayRecords[currentDate][dictName][i].s = s;

            if(appState.activeId === 'admin1') {
                Object.keys(appState.profiles).forEach(pid => {
                    if(pid === 'admin1') return;
                    let pState = appState.profiles[pid];
                    ensureDataStructForProfile(pState);
                    if(!pState.dayRecords[currentDate][dictName][i]) pState.dayRecords[currentDate][dictName][i] = { s: 'WAIT', d: '', r: '' };
                    pState.dayRecords[currentDate][dictName][i].s = s;
                });
            }

            autoSave(); render(true);
        }

        function updateMarket(type, idx, field, value) {
            if(!IS_MASTER) return;
            ensureDataStruct();
            const dictName = type === 'ank' ? 'data' : (type === 'jodi' ? 'jodiData' : 'pannelData');
            if(!state.dayRecords[currentDate][dictName][idx]) state.dayRecords[currentDate][dictName][idx] = { s: 'WAIT', d: '', r: '' };
            state.dayRecords[currentDate][dictName][idx][field] = value;

            if(appState.activeId === 'admin1') {
                Object.keys(appState.profiles).forEach(pid => {
                    if(pid === 'admin1') return;
                    let pState = appState.profiles[pid];
                    ensureDataStructForProfile(pState);
                    if(!pState.dayRecords[currentDate][dictName][idx]) pState.dayRecords[currentDate][dictName][idx] = { s: 'WAIT', d: '', r: '' };
                    pState.dayRecords[currentDate][dictName][idx][field] = value;
                });
            }

            runLiveSync(type, idx, field);
            autoSave();
        }

        function resetCard(type, i) {
            if(!IS_MASTER) return;
            const d = type === 'ank' ? 'data' : (type === 'jodi' ? 'jodiData' : 'pannelData');
            if(state.dayRecords[currentDate]?.[d]?.[i]) {
                state.dayRecords[currentDate][d][i] = { s: 'WAIT', d: '', r: '' };
                if(appState.activeId === 'admin1') {
                    Object.keys(appState.profiles).forEach(pid => {
                        if(pid === 'admin1') return;
                        let pState = appState.profiles[pid];
                        ensureDataStructForProfile(pState);
                        if(pState.dayRecords[currentDate]?.[d]?.[i]) pState.dayRecords[currentDate][d][i] = { s: 'WAIT', d: '', r: '' };
                    });
                }
                autoSave(); render(true);
            }
        }

        function cardUndo(type, i) {
            if(!IS_MASTER) return;
            const d = type === 'ank' ? 'data' : (type === 'jodi' ? 'jodiData' : 'pannelData');
            if(state.dayRecords[currentDate]?.[d]?.[i]) {
                state.dayRecords[currentDate][d][i].s = 'WAIT';
                if(appState.activeId === 'admin1') {
                    Object.keys(appState.profiles).forEach(pid => {
                        if(pid === 'admin1') return;
                        let pState = appState.profiles[pid];
                        ensureDataStructForProfile(pState);
                        if(pState.dayRecords[currentDate]?.[d]?.[i]) pState.dayRecords[currentDate][d][i].s = 'WAIT';
                    });
                }
                autoSave(); render(true);
            }
        }

        function getWeekStats(currDateStr) { let parts = currDateStr.split('-'); let d = new Date(parts[0], parts[1]-1, parts[2]); let day = d.getDay(); let diff = d.getDate() - day + (day === 0 ? -6 : 1); let monday = new Date(d); monday.setDate(diff); let stats = { ank: {}, jodi: {}, pannel: {} }; baseMarkets.forEach(bm => { stats.ank[bm.n] = { rounds: 0, pass: 0, fail: 0, invest: 0, win: 0 }; stats.jodi[bm.n] = { rounds: 0, pass: 0, fail: 0, invest: 0, win: 0 }; stats.pannel[bm.n] = { rounds: 0, pass: 0, fail: 0, invest: 0, win: 0 }; }); let totals = { ank: { invest: 0, win: 0, runningPL: 0, maxLoss: 0 }, jodi: { invest: 0, win: 0, runningPL: 0, maxLoss: 0 }, pannel: { invest: 0, win: 0, runningPL: 0, maxLoss: 0 } }; for(let i=0; i<7; i++) { let loopDate = new Date(monday); loopDate.setDate(monday.getDate() + i); let yyyy = loopDate.getFullYear(); let mm = String(loopDate.getMonth() + 1).padStart(2, '0'); let dd = String(loopDate.getDate()).padStart(2, '0'); let dateStr = `${yyyy}-${mm}-${dd}`; let record = state.dayRecords[dateStr]; if(!record) continue; const processItem = (type, dataDict, arr, marginMultiplier) => { if(!dataDict) return; arr.forEach((m, idx) => { let bmName = getBaseNameForMarket(m.n); if(!bmName || !stats[type][bmName]) return; const dObj = dataDict[idx]; if(!dObj || dObj.s === 'WAIT' || dObj.s === 'SKIP') return; const r = parseFloat(dObj.r) || 0; let count = (dObj.d ? String(dObj.d) : '').split(/[, ]+/).filter(x => x.trim()).length; let invest = count * r; if(dObj.s === 'FAIL') { totals[type].runningPL -= invest; if(totals[type].runningPL < totals[type].maxLoss) totals[type].maxLoss = totals[type].runningPL; } else if(dObj.s === 'PASS') { totals[type].runningPL -= invest; if(totals[type].runningPL < totals[type].maxLoss) totals[type].maxLoss = totals[type].runningPL; totals[type].runningPL += (r * marginMultiplier); } stats[type][bmName].rounds++; stats[type][bmName].invest += invest; totals[type].invest += invest; if(dObj.s === 'PASS') { stats[type][bmName].pass++; stats[type][bmName].win += (r * marginMultiplier); totals[type].win += (r * marginMultiplier); } else if(dObj.s === 'FAIL') { stats[type][bmName].fail++; } }); }; processItem('ank', record.data, markets, 9.5); processItem('jodi', record.jodiData, baseMarkets, 95.0); processItem('pannel', record.pannelData, markets, 150.0); } return { monday, stats, totals }; }

        function renderWeeklyReport() {
            ensureDataStruct();
            let { monday, stats, totals } = getWeekStats(currentDate); let sunday = new Date(monday); sunday.setDate(sunday.getDate() + 6); let dateStr = `${monday.toLocaleDateString('en-GB', {day:'2-digit', month:'short'})} - ${sunday.toLocaleDateString('en-GB', {day:'2-digit', month:'short'})}`;
            let typeStats = stats[weeklyTabType]; let tInvest = totals[weeklyTabType].invest; let tWin = totals[weeklyTabType].win; let net = tWin - tInvest;

            let html = `
                ${renderSubTabs()}
                <div class="px-3 pb-4 pt-2">
                    <div class="native-card p-4 mb-3 text-center" style="border-color:rgba(123,143,255,0.25); background:rgba(123,143,255,0.06)">
                        <h3 class="text-[11px] font-bold text-[var(--purple)] uppercase tracking-widest mb-1">Weekly Audit Report</h3>
                        <p class="text-[9px] text-[var(--text-muted)] uppercase tracking-widest font-bold mb-4">${dateStr}</p>
                        <div class="grid grid-cols-2 gap-3">
                            <div class="bg-[var(--surface-light)] border border-[var(--border)] p-3 rounded-xl">
                                <p class="stat-lbl mb-1">Total Invest</p>
                                <p class="text-[14px] font-black text-[var(--text-muted)]">₹${tInvest.toLocaleString()}</p>
                            </div>
                            <div class="bg-[var(--surface-light)] border ${net >= 0 ? 'border-[rgba(0,194,111,0.3)]' : 'border-[rgba(255,93,93,0.3)]'} p-3 rounded-xl">
                                <p class="stat-lbl mb-1">Weekly P/L</p>
                                <p class="text-[14px] font-black ${net >= 0 ? 'text-[var(--green)]' : 'text-[var(--rose)]'}">${net >= 0 ? '+' : ''}₹${net.toLocaleString()}</p>
                            </div>
                        </div>
                    </div>
            `;

            for (let bmName in typeStats) {
                let s = typeStats[bmName];
                if(s.rounds > 0) {
                    let pl = s.win - s.invest;
                    html += `
                        <div class="native-card p-4 flex justify-between items-center border-l-4 ${pl >= 0 ? 'border-l-[var(--green)]' : 'border-l-[var(--rose)]'} mb-2">
                            <div>
                                <h4 class="text-[12px] font-bold uppercase text-white mb-1">${bmName}</h4>
                                <p class="text-[9px] text-[var(--text-muted)] font-medium">Invest: ₹${s.invest.toLocaleString()}</p>
                            </div>
                            <div class="text-right">
                                <p class="text-[12px] font-black ${pl >= 0 ? 'text-[var(--green)]' : 'text-[var(--rose)]'} mb-1">${pl >= 0 ? '+' : ''}₹${pl.toLocaleString()}</p>
                                <p class="text-[9px] text-[var(--text-muted)] font-medium"><span class="text-[var(--green)]">W:${s.pass}</span> <span class="text-[var(--rose)] ml-1">L:${s.fail}</span></p>
                            </div>
                        </div>`;
                }
            }

            if(IS_MASTER) {
                html += `<button onclick="shareWeeklyReport()" class="w-full bg-[var(--purple)] text-white py-4 rounded-2xl font-black text-[11px] uppercase tracking-wide mt-3 active:scale-95 shadow-lg shadow-[rgba(123,143,255,0.2)]"><i class="fas fa-paper-plane mr-1"></i> Send Weekly Report</button>`;
            }
            html += `</div>`;
            return html;
        }

        function renderSmartAI() {
            if(!IS_MASTER) return '';
            return `
            <div class="px-3 py-4">
                <div class="native-card p-5" style="border-color:rgba(42,171,238,0.25); background:rgba(42,171,238,0.04)">
                    <div class="flex items-center gap-3 mb-4">
                        <div class="w-10 h-10 rounded-xl bg-[rgba(42,171,238,0.15)] flex items-center justify-center text-[var(--primary)] text-lg"><i class="fas fa-brain"></i></div>
                        <div>
                            <h3 class="text-[14px] font-black text-white">Global AI Scanner</h3>
                            <p class="text-[9px] text-[var(--text-muted)] uppercase tracking-widest mt-0.5">Extract & Paste into all VIPs</p>
                        </div>
                    </div>

                    <textarea id="smart-text-input" rows="7" class="w-full bg-[var(--surface-light)] border border-[var(--border)] text-[var(--amber)] font-bold p-4 rounded-xl outline-none text-[13px] placeholder-[var(--text-muted)] transition-colors focus:border-[var(--primary)]" placeholder="Paste your raw text format here..."></textarea>

                    <div class="grid grid-cols-3 gap-3 mt-4">
                        <button onclick="processSmartPaste('ank')" class="bg-[rgba(42,171,238,0.1)] text-[var(--primary)] py-3 rounded-xl font-bold uppercase text-[10px] active:scale-95 border border-[rgba(42,171,238,0.2)]">Ank</button>
                        <button onclick="processSmartPaste('jodi')" class="bg-[rgba(184,92,255,0.1)] text-[#B85CFF] py-3 rounded-xl font-bold uppercase text-[10px] active:scale-95 border border-[rgba(184,92,255,0.2)]">Jodi</button>
                        <button onclick="processSmartPaste('pannel')" class="bg-[rgba(250,199,72,0.1)] text-[var(--amber)] py-3 rounded-xl font-bold uppercase text-[10px] active:scale-95 border border-[rgba(250,199,72,0.2)]">Pan</button>
                    </div>
                </div>
            </div>`;
        }

        function renderVipSettings() {
            if(IS_MASTER) return '';
            ensureDataStruct();
            const canEdit = vipCanEdit();
            const disAttr = !canEdit ? 'disabled' : '';
            const disClass = !canEdit ? 'opacity-50' : '';

            const capital   = parseFloat(state.config.capital)   || 0;
            const dayTarget = parseFloat(state.config.dayTarget)  || 0;
            const totalPL   = globalStats.ank.pl + globalStats.jodi.pl + globalStats.pannel.pl;
            const dayPct    = dayTarget > 0 ? Math.min(100, Math.max(0, Math.round((totalPL / dayTarget) * 100))) : 0;

            const protoRow = (type, label, colorClass) => `
                <div class="flex justify-between items-center bg-[var(--surface-light)] px-4 py-3 rounded-xl border border-[var(--border)]">
                    <div>
                        <p class="text-[9px] font-bold text-[var(--text-muted)] uppercase">${label}</p>
                        <p class="text-[10px] font-bold ${colorClass} mt-0.5">Target / Card</p>
                    </div>
                    <input type="number" inputmode="numeric" ${disAttr}
                        oninput="state.config.${type}.tgt=parseFloat(this.value)||0; runLiveSync(); autoSave();"
                        value="${state.config[type] ? (state.config[type].tgt || 0) : 0}"
                        class="w-24 bg-[var(--surface)] border border-[var(--border)] text-white rounded-xl px-3 py-2 text-[13px] font-black text-right outline-none focus:border-[var(--primary)] ${disClass}"
                        placeholder="₹">
                </div>`;

            return `
                <div class="px-3 py-4">
                    <p class="sec-header">Meri Financial Settings</p>

                    ${!canEdit ? `<div class="bg-[rgba(255,93,93,0.1)] border border-[rgba(255,93,93,0.2)] rounded-xl p-3 mb-4 text-center">
                        <p class="text-[var(--rose)] text-[10px] font-black uppercase"><i class="fas fa-lock"></i> Read-Only Mode</p>
                        <p class="text-[var(--text-muted)] text-[9px] mt-1">Sirf admin details edit kar sakte hain.</p>
                    </div>` : ''}

                    <div class="native-card p-4 mb-3" style="border-color:rgba(0,194,111,0.25);background:rgba(0,194,111,0.04)">
                        <h3 class="text-[11px] font-bold text-[var(--green)] uppercase tracking-widest mb-3 flex items-center gap-2"><i class="fas fa-wallet"></i> Capital & Din Ka Target</h3>
                        <div class="grid grid-cols-2 gap-3 mb-3">
                            <div>
                                <label class="block text-[9px] text-[var(--text-muted)] uppercase font-bold mb-2 ml-1">Apna Capital ₹</label>
                                <input type="number" inputmode="numeric" ${disAttr}
                                    oninput="state.config.capital=parseFloat(this.value)||0; autoSave();"
                                    value="${capital}"
                                    class="native-input text-sm py-3 text-[var(--green)] ${disClass}" placeholder="Aapka capital">
                            </div>
                            <div>
                                <label class="block text-[9px] text-[var(--text-muted)] uppercase font-bold mb-2 ml-1">Din Ka Target ₹</label>
                                <input type="number" inputmode="numeric" ${disAttr}
                                    oninput="state.config.dayTarget=parseFloat(this.value)||0; render(true); autoSave();"
                                    value="${dayTarget}"
                                    class="native-input text-sm py-3 text-[var(--primary)] ${disClass}" placeholder="Daily profit goal">
                            </div>
                        </div>
                        ${dayTarget > 0 ? `
                        <div>
                            <div class="flex justify-between mb-1.5">
                                <span class="text-[9px] font-bold text-[var(--text-muted)] uppercase">Aaj Ka Progress</span>
                                <span class="text-[9px] font-bold ${totalPL >= 0 ? 'text-[var(--green)]' : 'text-[var(--rose)]'}">${totalPL >= 0 ? '+' : ''}₹${totalPL.toLocaleString()} / ₹${dayTarget.toLocaleString()}</span>
                            </div>
                            <div class="h-2 bg-[var(--surface-light)] rounded-full overflow-hidden">
                                <div class="h-full rounded-full transition-all" style="width:${Math.max(0, dayPct)}%;background:${totalPL >= 0 ? 'var(--green)' : 'var(--rose)'}"></div>
                            </div>
                            <p class="text-[9px] text-right mt-1 font-bold ${totalPL >= 0 ? 'text-[var(--green)]' : 'text-[var(--rose)]'}">${dayPct}% complete</p>
                        </div>` : ''}
                    </div>

                    <p class="sec-header">Har Card Ka Profit Target</p>
                    <div class="native-card p-4 mb-6 space-y-2">
                        ${protoRow('ank',    'ANK (x9.5)',   'text-[var(--primary)]')}
                        ${protoRow('jodi',   'JODI (x95)',   'text-[#B85CFF]')}
                        ${protoRow('pannel', 'PANNEL (x150)','text-[var(--amber)]')}
                    </div>

                    ${canEdit ? `<button onclick="autoSave(); showToast('Settings saved!', 'green')"
                        class="w-full bg-[var(--green)] text-white py-4 rounded-2xl font-black text-[12px] uppercase tracking-wide mb-8 active:scale-95 shadow-lg shadow-[rgba(0,194,111,0.2)]">
                        <i class="fas fa-save mr-2"></i> Save My Settings
                    </button>` : ''}
                </div>`;
        }

        function renderSettings() {
            if(!IS_MASTER) return '';
            ensureDataStruct();

            // ── ANK/PAN: one row per base market, OPEN + CLOSE toggle ──
            let mktsHtmlOpenClose = (title, colorClass, trackDict) => {
                let isAllChecked = baseMarkets.every(bm => {
                    const ok = bm.n + ' OPEN'; const ck = bm.n + ' CLOSE';
                    return state.dayRecords[currentDate][trackDict][ok] !== false &&
                           state.dayRecords[currentDate][trackDict][ck] !== false;
                });
                return `
                <div class="native-card p-4 mb-3">
                    <div class="flex justify-between items-center mb-3">
                        <h3 class="text-[11px] font-bold ${colorClass} uppercase tracking-widest flex items-center gap-2"><i class="fas fa-eye"></i> ${title}</h3>
                        <div class="flex items-center gap-2 bg-[var(--surface-light)] px-2 py-1.5 rounded-lg border border-[var(--border)]">
                            <span class="text-[9px] font-bold text-[var(--text-muted)] uppercase">ALL</span>
                            <label class="switch transform scale-[0.6] origin-right m-0">
                                <input type="checkbox" onchange="toggleAllMarketsOpenClose('${trackDict}', this.checked)" ${isAllChecked ? 'checked' : ''}>
                                <span class="slider"></span>
                            </label>
                        </div>
                    </div>
                    <div class="flex justify-end gap-5 mb-1.5 pr-1">
                        <span class="text-[8px] font-black text-[var(--primary)] uppercase tracking-wider">OPEN</span>
                        <span class="text-[8px] font-black text-[var(--amber)] uppercase tracking-wider">CLOSE</span>
                    </div>
                    <div class="space-y-1.5">
                        ${baseMarkets.map(bm => {
                            const ok = bm.n + ' OPEN'; const ck = bm.n + ' CLOSE';
                            const openOn  = state.dayRecords[currentDate][trackDict][ok]  !== false;
                            const closeOn = state.dayRecords[currentDate][trackDict][ck] !== false;
                            return `
                            <div class="flex items-center gap-2 bg-[var(--surface-light)] px-3 py-2 rounded-xl border border-[var(--border)]">
                                <span class="flex-1 text-[9px] font-bold text-[var(--text-muted)] uppercase truncate">${bm.n}</span>
                                <label class="switch transform scale-[0.55] origin-right m-0">
                                    <input type="checkbox" onchange="toggleMarketVis('${trackDict}', '${ok}', this.checked)" ${openOn ? 'checked' : ''}>
                                    <span class="slider"></span>
                                </label>
                                <label class="switch transform scale-[0.55] origin-right m-0">
                                    <input type="checkbox" onchange="toggleMarketVis('${trackDict}', '${ck}', this.checked)" ${closeOn ? 'checked' : ''}>
                                    <span class="slider"></span>
                                </label>
                            </div>`;
                        }).join('')}
                    </div>
                </div>`;
            };

            // ── JODI: single toggle per base market ──
            let mktsHtmlJodi = () => {
                let isAllChecked = baseMarkets.every(m => state.dayRecords[currentDate].visJodi[m.n] !== false);
                return `
                <div class="native-card p-4 mb-3">
                    <div class="flex justify-between items-center mb-3">
                        <h3 class="text-[11px] font-bold text-[#B85CFF] uppercase tracking-widest flex items-center gap-2"><i class="fas fa-eye"></i> Jodi Markets</h3>
                        <div class="flex items-center gap-2 bg-[var(--surface-light)] px-2 py-1.5 rounded-lg border border-[var(--border)]">
                            <span class="text-[9px] font-bold text-[var(--text-muted)] uppercase">ALL</span>
                            <label class="switch transform scale-[0.6] origin-right m-0">
                                <input type="checkbox" onchange="toggleAllMarkets('visJodi', this.checked)" ${isAllChecked ? 'checked' : ''}>
                                <span class="slider"></span>
                            </label>
                        </div>
                    </div>
                    <div class="grid grid-cols-2 gap-2">
                        ${baseMarkets.map(m => `
                            <div class="flex justify-between items-center bg-[var(--surface-light)] p-3 rounded-xl border border-[var(--border)]">
                                <span class="text-[9px] font-bold text-[var(--text-muted)] uppercase truncate pr-2">${m.n}</span>
                                <label class="switch transform scale-[0.6] origin-right m-0">
                                    <input type="checkbox" onchange="toggleMarketVis('visJodi', '${m.n}', this.checked)" ${state.dayRecords[currentDate].visJodi[m.n] !== false ? 'checked' : ''}>
                                    <span class="slider"></span>
                                </label>
                            </div>`).join('')}
                    </div>
                </div>`;
            };

            let protoHTML = (type, title, colorClass) => `
                <div class="native-card p-4 mb-3">
                    <h3 class="text-[11px] font-bold ${colorClass} uppercase tracking-widest mb-4">${title}</h3>
                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="block text-[9px] text-[var(--text-muted)] uppercase font-bold mb-2 ml-1">Capital Cap</label>
                            <input type="number" oninput="state.config.${type}.cap=parseFloat(this.value)||0; runLiveSync(); autoSave();" value="${state.config[type].cap}" class="native-input text-sm py-3" placeholder="0 = Master">
                        </div>
                        <div>
                            <label class="block text-[9px] text-[var(--text-muted)] uppercase font-bold mb-2 ml-1">Target / Card</label>
                            <input type="number" oninput="state.config.${type}.tgt=parseFloat(this.value)||0; runLiveSync(); autoSave();" value="${state.config[type].tgt}" class="native-input text-sm py-3" placeholder="Per card profit">
                        </div>
                    </div>
                </div>`;

            const totalDayPL = globalStats.ank.pl + globalStats.jodi.pl + globalStats.pannel.pl;
            const dayTgt = parseFloat(state.config.dayTarget) || 0;
            const dayPct = dayTgt > 0 ? Math.min(100, Math.round((totalDayPL / dayTgt) * 100)) : 0;
            const capital = parseFloat(state.config.capital) || 0;

            return `
                <div class="px-3 py-4">
                    <p class="sec-header">Capital & Day Targets</p>
                    <div class="native-card p-4 mb-3" style="border-color:rgba(0,194,111,0.25);background:rgba(0,194,111,0.04)">
                        <div class="grid grid-cols-2 gap-3 mb-3">
                            <div>
                                <label class="block text-[9px] text-[var(--text-muted)] uppercase font-bold mb-2 ml-1">Apna Capital ₹</label>
                                <input type="number" inputmode="numeric" oninput="state.config.capital=parseFloat(this.value)||0; autoSave();" value="${capital}" class="native-input text-sm py-3 text-[var(--green)]" placeholder="Aapka capital">
                            </div>
                            <div>
                                <label class="block text-[9px] text-[var(--text-muted)] uppercase font-bold mb-2 ml-1">Din Ka Target ₹</label>
                                <input type="number" inputmode="numeric" oninput="state.config.dayTarget=parseFloat(this.value)||0; autoSave();" value="${dayTgt}" class="native-input text-sm py-3 text-[var(--primary)]" placeholder="Daily profit goal">
                            </div>
                        </div>
                        ${dayTgt > 0 ? `
                        <div class="mt-1">
                            <div class="flex justify-between mb-1">
                                <span class="text-[9px] font-bold text-[var(--text-muted)] uppercase">Today's Progress</span>
                                <span class="text-[9px] font-bold ${totalDayPL >= 0 ? 'text-[var(--green)]' : 'text-[var(--rose)]'}">${totalDayPL >= 0 ? '+' : ''}₹${totalDayPL.toLocaleString()} / ₹${dayTgt.toLocaleString()}</span>
                            </div>
                            <div class="h-2 bg-[var(--surface-light)] rounded-full overflow-hidden">
                                <div class="h-full rounded-full transition-all" style="width:${Math.max(0, dayPct)}%;background:${totalDayPL >= 0 ? 'var(--green)' : 'var(--rose)'}"></div>
                            </div>
                            <p class="text-[9px] text-[var(--text-muted)] text-right mt-1 font-bold">${dayPct}% complete</p>
                        </div>` : ''}
                    </div>

                    ${mktsHtmlOpenClose('Ank Markets', 'text-[var(--primary)]', 'visAnk')}
                    ${mktsHtmlJodi()}
                    ${mktsHtmlOpenClose('Pan Markets', 'text-[var(--amber)]', 'visPan')}
                    ${protoHTML('ank', 'ANK PROTOCOL', 'text-[var(--primary)]')}
                    ${protoHTML('jodi', 'JODI PROTOCOL', 'text-[#B85CFF]')}
                    ${protoHTML('pannel', 'PAN PROTOCOL', 'text-[var(--amber)]')}
                    <button onclick="saveMaster(false)" class="w-full bg-[var(--green)] text-white py-4 rounded-2xl font-black text-[12px] uppercase tracking-wide mt-2 mb-8 active:scale-95 shadow-lg shadow-[rgba(0,194,111,0.2)]">Save Configuration</button>
                </div>
            `;
        }

        function shareVipApp(pid, name) {
            const safePid = pid.replace('_', '%5F');
            const link = window.location.origin + '/?vip=' + safePid;

            const msg = `🚀 *TITAN NOVA VIP APP* 🚀\\nHello ${name}, yeh aapka personal App portal hai. Is naye link ko open karke *Install App* pe click karein:\\n\\n🔗 ${link}`;

            let textArea = document.createElement("textarea"); textArea.value = msg.replace(/\\\\n/g, '\\n'); textArea.style.position = "fixed"; textArea.style.left = "-999999px"; document.body.appendChild(textArea); textArea.focus(); textArea.select();
            try { document.execCommand('copy'); alert("✅ VIP App Link Copied! Send this link to the client via WhatsApp."); } catch (err) { alert("Link manually copy karein:\\n" + link); } textArea.remove();
        }

        function renderClients() {
            if(!IS_MASTER) return '';
            let html = `
                <div class="px-3 py-4">
                    <div class="native-card p-4 mb-3" style="border-color:rgba(42,171,238,0.25); background:rgba(42,171,238,0.04)">
                        <div class="flex items-center gap-3 mb-4">
                            <div class="w-10 h-10 rounded-xl bg-[rgba(42,171,238,0.15)] text-[var(--primary)] flex items-center justify-center shrink-0"><i class="fas fa-bullhorn"></i></div>
                            <div>
                                <h3 class="text-[14px] font-black text-white">Live Push Broadcast</h3>
                                <p class="text-[9px] text-[var(--text-muted)] uppercase tracking-widest mt-0.5">Send Alert to all VIPs</p>
                            </div>
                        </div>
                        <input id="bcast-title" class="native-input text-[13px] py-3 mb-2" placeholder="Title (e.g. 🔥 Dhamaka Offer)">
                        <textarea id="bcast-msg" rows="2" class="native-input text-[13px] py-3 mb-3" placeholder="Type your message here..."></textarea>
                        <button onclick="sendBroadcast()" class="w-full bg-[var(--primary)] text-white py-3.5 rounded-xl font-black text-[11px] uppercase active:scale-95 shadow-lg shadow-[rgba(42,171,238,0.2)]"><i class="fas fa-paper-plane mr-1"></i> Send Push Notification</button>
                    </div>

                    <div class="native-card p-4 mb-3" style="border-color:rgba(250,199,72,0.2); background:rgba(250,199,72,0.04)">
                        <div class="flex justify-between items-center mb-4">
                            <div>
                                <h3 class="text-[14px] font-black text-white">VIP Connections</h3>
                                <p class="text-[9px] text-[var(--text-muted)] uppercase tracking-widest mt-0.5">Manage Client Links</p>
                            </div>
                            <button onclick="importContacts()" class="w-10 h-10 bg-[rgba(250,199,72,0.15)] text-[var(--amber)] rounded-xl flex items-center justify-center active:scale-95 border border-[rgba(250,199,72,0.2)]"><i class="fas fa-address-book"></i></button>
                        </div>
                        <div class="space-y-3">
                            <input id="c-name" class="native-input py-3 text-sm" placeholder="Client Display Name">
                            <input id="c-phone" type="text" inputmode="numeric" class="native-input py-3 text-sm" placeholder="WhatsApp Number">
                            <button onclick="addVIP()" class="w-full bg-[var(--amber)] text-black py-3.5 rounded-xl font-black text-[11px] uppercase active:scale-95">Add VIP Member</button>
                        </div>
                    </div>

                    <p class="sec-header">Active Profiles</p>
                    <div class="space-y-2">
            `;

            Object.keys(appState.profiles).forEach(pid => {
                if(pid === 'admin1') return;
                const c = appState.profiles[pid];
                const isDummy = (pid === 'client_dummy');
                const expDate = c.expiryDate || '';
                let expLabel = 'No Expiry Set'; let expColor = 'text-[var(--text-muted)]';
                if (expDate) {
                    const expObj = new Date(expDate); const today = new Date(); today.setHours(0,0,0,0); expObj.setHours(0,0,0,0);
                    const dLeft = Math.ceil((expObj - today) / (1000*60*60*24));
                    expLabel = dLeft > 0 ? `${dLeft}d left - ${expObj.toLocaleDateString('en-IN',{day:'2-digit',month:'short',year:'numeric'})}` : `Expired - ${expObj.toLocaleDateString('en-IN',{day:'2-digit',month:'short',year:'numeric'})}`;
                    expColor = dLeft > 0 ? 'text-[var(--green)]' : 'text-[var(--rose)]';
                }
                html += `
                    <div class="native-card m-0 border-l-4 ${isDummy ? 'border-l-[var(--purple)]' : 'border-l-[var(--primary)]'}">
                        <div onclick="openClient('${pid}')" class="p-4 flex justify-between items-center cursor-pointer active:opacity-70 transition-opacity">
                            <div class="flex items-center gap-3">
                                <div class="w-10 h-10 rounded-full bg-[var(--surface-light)] border border-[var(--border)] flex items-center justify-center ${isDummy ? 'text-[var(--purple)]' : 'text-[var(--primary)]'}"><i class="fas ${isDummy ? 'fa-vial' : 'fa-user'}"></i></div>
                                <div>
                                    <p class="${isDummy ? 'text-[var(--purple)]' : 'text-white'} font-black text-[14px] uppercase">${c.name}</p>
                                    <p class="text-[10px] ${expColor} font-medium mt-0.5"><i class="fas fa-crown text-[8px] mr-1"></i>${expLabel}</p>
                                </div>
                            </div>
                            <div class="flex gap-2">
                                <button onclick="event.stopPropagation(); shareVipApp('${pid}', '${c.name}')" class="w-9 h-9 text-[var(--primary)] bg-[rgba(42,171,238,0.1)] rounded-xl flex items-center justify-center active:scale-95 border border-[rgba(42,171,238,0.15)]"><i class="fas fa-link text-xs"></i></button>
                                ${!isDummy ? `<button onclick="event.stopPropagation(); deleteProfile('${pid}')" class="w-9 h-9 text-[var(--rose)] bg-[rgba(255,93,93,0.1)] rounded-xl flex items-center justify-center active:scale-95 border border-[rgba(255,93,93,0.15)]"><i class="fas fa-trash-alt text-xs"></i></button>` : ''}
                            </div>
                        </div>
                        <div class="px-4 pb-3 flex items-center gap-2 border-t border-[var(--border)]">
                            <i class="fas fa-calendar-check text-[var(--amber)] text-xs shrink-0"></i>
                            <input type="date" id="exp-${pid}" value="${expDate}" class="flex-1 min-w-0 bg-[var(--surface-light)] border border-[var(--border)] text-white rounded-lg px-2 py-1.5 text-[11px] font-bold outline-none focus:border-[var(--primary)]">
                            <button onclick="saveExpiryDate('${pid}')" class="bg-[rgba(250,199,72,0.15)] text-[var(--amber)] border border-[rgba(250,199,72,0.2)] px-3 py-1.5 rounded-lg font-bold text-[10px] uppercase active:scale-95 shrink-0">Set</button>
                        </div>
                        <div class="px-4 pb-3 flex items-center justify-between border-t border-[var(--border)]">
                            <div>
                                <p class="text-[9px] font-bold text-[var(--text-muted)] uppercase">App Access</p>
                                <p class="text-[10px] font-bold ${c.vipAccessEnabled !== false ? 'text-[var(--green)]' : 'text-[var(--rose)]'}">${c.vipAccessEnabled !== false ? 'Enabled — VIP can use app' : 'Disabled — Read-Only Mode'}</p>
                            </div>
                            <label class="switch m-0">
                                <input type="checkbox" onchange="toggleVipAccess('${pid}', this.checked)" ${c.vipAccessEnabled !== false ? 'checked' : ''}>
                                <span class="slider"></span>
                            </label>
                        </div>
                    </div>`;
            });

            html += '</div></div>';
            return html;
        }

        function renderWalletsTab() {
            if(!IS_MASTER) return '';
            ensureWalletStruct();
            const ids = walletClientIds();
            const totalBalance = ids.reduce((s,id)=>s + Number(walletForUser(id).balance || 0), 0);
            const totalCredit = ids.reduce((s,id)=>s + Number(walletForUser(id).creditLimit || 0), 0);
            let html = `<div class="px-3 py-4">
                <p class="sec-header">Wallet Foundation</p>
                <div class="native-card p-4 mb-3" style="border-color:rgba(0,194,111,0.22);background:rgba(0,194,111,0.04)">
                    <div class="flex items-center gap-3 mb-3">
                        <div class="w-10 h-10 rounded-xl bg-[rgba(0,194,111,0.15)] text-[var(--green)] flex items-center justify-center border border-[rgba(0,194,111,0.2)]"><i class="fas fa-wallet"></i></div>
                        <div class="flex-1 min-w-0">
                            <h3 class="text-white font-black text-[14px]">Wallet & Credit Base</h3>
                            <p class="text-[9px] text-[var(--text-muted)] uppercase tracking-widest mt-0.5">Phase 1/2 foundation for future entry parser and settlement</p>
                        </div>
                    </div>
                    <div class="grid grid-cols-3 gap-2 mb-3">
                        <div class="stat-box"><p class="stat-lbl">Clients</p><p class="stat-val text-[var(--primary)]">${ids.length}</p></div>
                        <div class="stat-box"><p class="stat-lbl">Balance</p><p class="stat-val text-[var(--green)]">${fmtMoney(totalBalance)}</p></div>
                        <div class="stat-box"><p class="stat-lbl">Credit</p><p class="stat-val text-[var(--amber)]">${fmtMoney(totalCredit)}</p></div>
                    </div>
                    <div class="grid grid-cols-[1fr_auto] gap-2 items-end">
                        <div>
                            <label class="block text-[9px] text-[var(--text-muted)] uppercase font-bold mb-2 ml-1">Default Credit For New Clients</label>
                            <input id="wallet-default-credit" type="number" value="${Number(appState.walletSettings.defaultCreditLimit || 0)}" class="native-input text-sm py-3" placeholder="0">
                        </div>
                        <button onclick="saveWalletDefaultCredit()" class="bg-[var(--green)] text-white px-4 py-3 rounded-xl font-black text-[10px] uppercase active:scale-95"><i class="fas fa-save mr-1"></i>Save</button>
                    </div>
                    <p class="text-[9px] text-[var(--text-muted)] leading-relaxed mt-2">Abhi wallet manual mode me hai. Next phase me WhatsApp entry accept hote hi debit aur result hit par payout credit isi wallet se hoga.</p>
                </div>
                <p class="sec-header">Client Wallets</p>`;
            if(!ids.length){
                html += `<div class="native-card p-4 text-center text-[var(--text-muted)] text-xs">No VIP/client profiles found.</div>`;
            }
            html += ids.map(uid => {
                const p = (appState.profiles || {})[uid] || {};
                const w = walletForUser(uid);
                const bal = Number(w.balance || 0);
                const credit = Number(w.creditLimit || 0);
                const available = bal + credit;
                const status = p.vipAccessEnabled === false ? 'Blocked' : 'Active';
                const balCls = bal >= 0 ? 'text-[var(--green)]' : 'text-[var(--rose)]';
                return `<div class="native-card p-4 mb-2">
                    <div class="flex items-start justify-between gap-3">
                        <div class="min-w-0">
                            <h3 class="text-white font-black text-[13px] uppercase truncate">${p.name || uid}</h3>
                            <p class="text-[9px] text-[var(--text-muted)] font-bold mt-1 truncate">${p.phone || 'No phone'} · ${uid}</p>
                        </div>
                        <span class="text-[8px] font-black uppercase px-2 py-1 rounded-lg border ${status === 'Active' ? 'text-[var(--green)] border-[rgba(0,194,111,0.25)] bg-[rgba(0,194,111,0.08)]' : 'text-[var(--rose)] border-[rgba(255,93,93,0.25)] bg-[rgba(255,93,93,0.08)]'}">${status}</span>
                    </div>
                    <div class="grid grid-cols-3 gap-2 mt-3">
                        <div class="stat-box"><p class="stat-lbl">Balance</p><p class="stat-val ${balCls}">${fmtMoney(bal)}</p></div>
                        <div class="stat-box"><p class="stat-lbl">Credit</p><p class="stat-val text-[var(--amber)]">${fmtMoney(credit)}</p></div>
                        <div class="stat-box"><p class="stat-lbl">Available</p><p class="stat-val text-[var(--primary)]">${fmtMoney(available)}</p></div>
                    </div>
                    <div class="grid grid-cols-4 gap-2 mt-3">
                        <button onclick="walletAddSubtract('${uid}','add')" class="bg-[rgba(0,194,111,0.14)] text-[var(--green)] border border-[rgba(0,194,111,0.25)] py-2.5 rounded-xl font-black text-[9px] uppercase active:scale-95">+ Add</button>
                        <button onclick="walletAddSubtract('${uid}','subtract')" class="bg-[rgba(255,93,93,0.10)] text-[var(--rose)] border border-[rgba(255,93,93,0.22)] py-2.5 rounded-xl font-black text-[9px] uppercase active:scale-95">- Minus</button>
                        <button onclick="walletSetCredit('${uid}')" class="bg-[rgba(250,199,72,0.12)] text-[var(--amber)] border border-[rgba(250,199,72,0.25)] py-2.5 rounded-xl font-black text-[9px] uppercase active:scale-95">Credit</button>
                        <button onclick="walletZeroSettle('${uid}')" class="bg-[var(--surface-light)] text-[var(--text-muted)] border border-[var(--border)] py-2.5 rounded-xl font-black text-[9px] uppercase active:scale-95">Zero</button>
                    </div>
                    ${walletLedgerPreview(uid)}
                </div>`;
            }).join('');
            html += `<div class="native-card p-3 mb-8 text-[10px] text-[var(--text-muted)] leading-relaxed"><b class="text-white">Next:</b> Entry parser active hai: accepted WhatsApp entries wallet se debit hongi. Next phase me result settlement winners ko payout credit karega.</div></div>`;
            return html;
        }

        function renderResultsTab() {
            if(!IS_MASTER) return '';
            ensureResultStruct();
            const targetCount = appState.resultTargets.length;
            const records = appState.resultRecords[currentDate] || {};
            const autoScrapeOn = !(appState.resultSettings && appState.resultSettings.autoScrapeEnabled === false);
            let html = `<div class="px-3 py-4">
                <p class="sec-header">Auto Result Sender</p>
                <div class="native-card p-4 mb-3" style="border-color:rgba(250,199,72,0.22);background:rgba(250,199,72,0.04)">
                    <div class="flex items-center gap-3 mb-3">
                        <div class="w-10 h-10 rounded-xl bg-[rgba(250,199,72,0.15)] text-[var(--amber)] flex items-center justify-center border border-[rgba(250,199,72,0.2)]"><i class="fas fa-trophy"></i></div>
                        <div class="flex-1 min-w-0">
                            <h3 class="text-white font-black text-[14px]">Open / Close Result Declaration</h3>
                            <p class="text-[9px] text-[var(--text-muted)] uppercase tracking-widest mt-0.5">Open: 123-4 · Close: 123-45-678</p>
                        </div>
                    </div>
                    <div class="grid grid-cols-2 gap-3 mb-3">
                        <div>
                            <label class="block text-[9px] text-[var(--text-muted)] uppercase font-bold mb-2 ml-1">Result Date</label>
                            <input type="date" value="${currentDate}" onchange="changeDate(this.value); setMainNav('results');" class="native-input text-sm py-3">
                        </div>
                        <div>
                            <label class="block text-[9px] text-[var(--text-muted)] uppercase font-bold mb-2 ml-1">Targets</label>
                            <div class="native-input text-sm py-3 text-[var(--green)]">${targetCount} Saved</div>
                        </div>
                    </div>
                    <label class="block text-[9px] text-[var(--text-muted)] uppercase font-bold mb-2 ml-1">Result WhatsApp Targets</label>
                    <textarea id="result-targets-input" class="native-input text-left text-xs font-semibold h-24 mb-3" placeholder="Phone / Group JID / Invite link — one per line">${titanResultTargetsText()}</textarea>
                    <div class="grid grid-cols-2 gap-2">
                        <button onclick="syncResultTargets()" class="bg-[rgba(42,171,238,0.15)] text-[var(--primary)] border border-[rgba(42,171,238,0.25)] py-3 rounded-xl font-black text-[10px] uppercase active:scale-95"><i class="fab fa-whatsapp mr-1"></i> Sync Targets</button>
                        <button onclick="saveResultTargets()" class="bg-[var(--green)] text-white py-3 rounded-xl font-black text-[10px] uppercase active:scale-95"><i class="fas fa-save mr-1"></i> Save Targets</button>
                    </div>
                    <div class="mt-3 flex items-center justify-between gap-3 bg-[var(--surface-light)] border border-[var(--border)] rounded-xl p-3">
                        <div class="min-w-0">
                            <p class="text-white font-black text-[11px] uppercase">Auto Scrape</p>
                            <p class="text-[9px] text-[var(--text-muted)] leading-relaxed">${autoScrapeOn ? 'ON: Gateway live page se result detect karega.' : 'OFF: Gateway scrape skip karega. Manual Declare active hai.'}</p>
                        </div>
                        <label class="switch m-0 shrink-0">
                            <input type="checkbox" onchange="saveResultScrapeSetting(this.checked)" ${autoScrapeOn ? 'checked' : ''}>
                            <span class="slider"></span>
                        </label>
                    </div>
                    <div class="mt-2 flex items-center justify-between gap-3 bg-[var(--surface-light)] border border-[var(--border)] rounded-xl p-3">
                        <div class="min-w-0">
                            <p class="text-white font-black text-[11px] uppercase">Use Forward Targets</p>
                            <p class="text-[9px] text-[var(--text-muted)] leading-relaxed">ON: Result declarations Result targets + Forward tab targets dono par jayenge.</p>
                        </div>
                        <label class="switch m-0 shrink-0"><input id="result-use-forward-targets" type="checkbox" onchange="saveResultDeliverySettings()" ${appState.resultSettings.useForwardTargetsForResults === false ? '' : 'checked'}><span class="slider"></span></label>
                    </div>
                    <div class="grid grid-cols-3 gap-2 mt-2">
                        <button onclick="runResultScrapeNow()" class="w-full ${autoScrapeOn ? 'bg-[rgba(250,199,72,0.14)] text-[var(--amber)] border-[rgba(250,199,72,0.28)]' : 'bg-[rgba(255,93,93,0.10)] text-[var(--rose)] border-[rgba(255,93,93,0.22)]'} border py-3 rounded-xl font-black text-[10px] uppercase active:scale-95"><i class="fas fa-magnet mr-1"></i> Scrape Test</button>
                        <button onclick="retryResultDeclarations()" class="w-full bg-[rgba(42,171,238,0.12)] text-[var(--primary)] border border-[rgba(42,171,238,0.25)] py-3 rounded-xl font-black text-[10px] uppercase active:scale-95"><i class="fas fa-rotate mr-1"></i> Retry Send</button>
                        <button onclick="clearInvalidAutoResults()" class="w-full bg-[rgba(255,93,93,0.10)] text-[var(--rose)] border border-[rgba(255,93,93,0.22)] py-3 rounded-xl font-black text-[10px] uppercase active:scale-95"><i class="fas fa-shield-alt mr-1"></i> Clear Old</button>
                    </div>
                    <p class="text-[9px] text-[var(--text-muted)] leading-relaxed mt-2">Fresh rule: pehle 123-4 open save hoga; 123-45-678 close tabhi valid hoga jab woh usi open se start ho. Old/yesterday close auto ignore hoga.</p>
                </div>
                ${settlementCardHtml()}
                <p class="sec-header">Market Results</p>`;

            html += baseMarkets.map((m, i) => {
                const rec = records[m.n] || {};
                const view = resultDisplayView(rec);
                const currentVal = view.close || view.open || '';
                const openText = view.open ? view.open : 'Pending';
                const closeText = view.close ? view.close : (view.ignoredClose ? 'Ignored old' : 'Pending');
                const badgeText = view.close ? 'Final' : (view.open ? 'Open Done' : (view.ignoredClose ? 'Old Skipped' : 'Waiting'));
                const badgeClass = view.close ? 'text-[var(--green)] border-[rgba(0,194,111,0.25)] bg-[rgba(0,194,111,0.08)]' : (view.open ? 'text-[var(--primary)] border-[rgba(42,171,238,0.25)] bg-[rgba(42,171,238,0.08)]' : (view.ignoredClose ? 'text-[var(--rose)] border-[rgba(255,93,93,0.25)] bg-[rgba(255,93,93,0.08)]' : 'text-[var(--text-muted)] border-[var(--border)] bg-[var(--surface-light)]'));
                const ignoredNote = view.ignoredClose ? `<p class="text-[8px] text-[var(--rose)] font-bold mt-1">Old close ${view.rawClose} ignored: fresh open missing/mismatch.</p>` : '';
                return `<div class="native-card p-4 mb-2">
                    <div class="flex items-start justify-between gap-3 mb-3">
                        <div class="min-w-0">
                            <h3 class="text-white font-black text-[13px] uppercase truncate">${m.n}</h3>
                            <p class="text-[9px] text-[var(--text-muted)] font-bold mt-1">Open: <span class="text-[var(--primary)]">${openText}</span> · Close: <span class="text-[var(--amber)]">${closeText}</span></p>
                            ${ignoredNote}
                        </div>
                        <div class="text-[8px] font-black uppercase px-2 py-1 rounded-lg border ${badgeClass}">${badgeText}</div>
                    </div>
                    <div class="flex gap-2">
                        <input id="result-input-${i}" class="native-input text-sm py-3 flex-1" placeholder="123-4 / 123-45-678" value="${currentVal}">
                        <button onclick="saveMarketResult(${i})" class="bg-[var(--primary)] text-white px-4 rounded-xl font-black text-[10px] uppercase active:scale-95 shrink-0"><i class="fas fa-paper-plane mr-1"></i>Declare</button>
                    </div>
                </div>`;
            }).join('');

            html += `<div class="native-card p-3 mb-8 text-[10px] text-[var(--text-muted)] leading-relaxed">
                <b class="text-white">Note:</b> Gateway live page scrape karke Firebase me result save karega, phir WhatsApp declare karega. Same date + same market ke liye Open ek baar aur Close ek baar hi send hoga.
            </div></div>`;
            return html;
        }

        function paymentAutomationSettingsHtml(){
            const ps = appState.paymentSettings || {};
            const boolRow = (id, label, help, val) => `
                <div class="flex items-center justify-between gap-3 bg-[var(--surface-light)] border border-[var(--border)] rounded-xl p-3 mb-2">
                    <div class="min-w-0">
                        <p class="text-white font-black text-[11px] uppercase">${label}</p>
                        <p class="text-[9px] text-[var(--text-muted)] leading-relaxed">${help}</p>
                    </div>
                    <label class="switch m-0 shrink-0"><input id="${id}" type="checkbox" ${val ? 'checked' : ''}><span class="slider"></span></label>
                </div>`;
            return `
                <div class="flex items-center gap-3 mb-4">
                    <div class="w-10 h-10 rounded-xl bg-[rgba(42,171,238,0.15)] text-[var(--primary)] flex items-center justify-center border border-[rgba(42,171,238,0.2)]"><i class="fas fa-shield-halved"></i></div>
                    <div>
                        <h3 class="text-white font-black text-[14px]">Payment Verification</h3>
                        <p class="text-[9px] text-[var(--text-muted)] uppercase tracking-widest mt-0.5">Approve = wallet credit + optional membership</p>
                    </div>
                </div>
                ${boolRow('pay-auto-enabled', 'Automation Enabled', 'OFF karne par users payment submit nahi kar paayenge.', ps.paymentAutomationEnabled !== false)}
                ${boolRow('pay-require-utr', 'Require UTR', 'UTR blank ho to payment high-risk/blocked mark hoga.', ps.requireUtr !== false)}
                ${boolRow('pay-dup-block', 'Duplicate UTR Block', 'Same UTR pending/approved ho to auto reject/block.', ps.duplicateUtrBlock !== false)}
                ${boolRow('pay-credit-wallet', 'Approve Credits Wallet', 'Approve hote hi user wallet me amount add hoga.', ps.approveCreditsWallet !== false)}
                ${boolRow('pay-extend-membership', 'Approve Extends Membership', 'Approve prompt ke days se VIP expiry extend hogi.', ps.extendMembershipOnApprove !== false)}
                ${boolRow('pay-private-notify', 'Private WhatsApp Notify', 'Gateway online ho to user ko private status message jayega.', ps.notifyUserPrivate !== false)}
                <div class="grid grid-cols-2 gap-2 mt-3">
                    <div><label class="block text-[9px] text-[var(--text-muted)] uppercase font-bold mb-1 ml-1">Min Amount</label><input id="pay-min-amount" class="native-input py-3 text-sm" type="number" value="${ps.minAmount ?? 1}"></div>
                    <div><label class="block text-[9px] text-[var(--text-muted)] uppercase font-bold mb-1 ml-1">Max Amount</label><input id="pay-max-amount" class="native-input py-3 text-sm" type="number" value="${ps.maxAmount ?? 200000}"></div>
                </div>
                <button onclick="savePaymentSettings()" class="mt-3 w-full bg-[var(--primary)] text-white py-3.5 rounded-xl font-black text-[11px] uppercase active:scale-95"><i class="fas fa-save mr-1"></i> Save Payment Automation</button>`;
        }

        async function savePaymentSettings(){
            const payload = {
                paymentAutomationEnabled: document.getElementById('pay-auto-enabled')?.checked,
                requireUtr: document.getElementById('pay-require-utr')?.checked,
                duplicateUtrBlock: document.getElementById('pay-dup-block')?.checked,
                approveCreditsWallet: document.getElementById('pay-credit-wallet')?.checked,
                extendMembershipOnApprove: document.getElementById('pay-extend-membership')?.checked,
                notifyUserPrivate: document.getElementById('pay-private-notify')?.checked,
                minAmount: parseFloat(document.getElementById('pay-min-amount')?.value || 0),
                maxAmount: parseFloat(document.getElementById('pay-max-amount')?.value || 0)
            };
            try{
                const res = await fetch('/api/payment_settings', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
                const data = await res.json();
                if(data.status !== 'success') throw new Error(data.message || 'Save failed');
                appState.paymentSettings = data.paymentSettings;
                showRealNotification('✅ Payment Settings Saved', 'Automation settings update ho gaye.', 'success');
            }catch(e){ showRealNotification('❌ Payment Error', String(e.message || e), 'danger'); }
        }

        function renderAdminPaymentsTab() {
            if(!IS_MASTER) return '';
            let html = '<div class="px-3 py-4">';
            const pm = appState.paymentMethods || {};
            const allPayments = appState.payments || [];
            const pendingPayments = allPayments.filter(p => p.status === 'pending');

            html += `
            <div class="mt-4">
                <p class="sec-header">Payment Methods Setup</p>
                <div class="native-card p-4" style="border-color:rgba(0,194,111,0.2); background:rgba(0,194,111,0.04)">
                    <div class="flex items-center gap-3 mb-4">
                        <div class="w-10 h-10 rounded-xl bg-[rgba(0,194,111,0.15)] text-[var(--green)] flex items-center justify-center border border-[rgba(0,194,111,0.2)]"><i class="fas fa-qrcode"></i></div>
                        <div>
                            <h3 class="text-white font-black text-[14px]">Payment Details</h3>
                            <p class="text-[9px] text-[var(--text-muted)] uppercase tracking-widest mt-0.5">VIP users ko dikhayenge</p>
                        </div>
                    </div>
                    <input id="pm-upi" class="native-input py-3 mb-3 text-sm" placeholder="UPI ID (e.g. name@upi)" value="${pm.upi || ''}">
                    <input id="pm-phone" class="native-input py-3 mb-3 text-sm" placeholder="Phone / WhatsApp Number" value="${pm.phone || ''}">
                    <div class="mb-3">
                        <label class="text-[9px] text-[var(--text-muted)] font-bold uppercase block mb-2">QR Code Image</label>
                        <label class="block w-full bg-[var(--surface-light)] border border-dashed border-[var(--surface-mid)] rounded-xl p-3 text-center cursor-pointer" for="pm-qr-input">
                            <i class="fas fa-qrcode text-xl text-[var(--text-muted)] mb-1 block"></i>
                            <p class="text-[var(--text-muted)] text-[10px] font-bold" id="pm-qr-label">${pm.qr ? 'QR Uploaded ✓' : 'Tap to upload QR'}</p>
                        </label>
                        <input type="file" id="pm-qr-input" accept="image/*" class="hidden" onchange="handleQRSelect(this)">
                        <input type="hidden" id="pm-qr-b64" value="${pm.qr || ''}">
                        ${pm.qr ? `<img id="pm-qr-preview" src="${pm.qr}" class="mx-auto mt-2 max-h-32 rounded-xl border border-[var(--border)]">` : `<img id="pm-qr-preview" class="hidden mx-auto mt-2 max-h-32 rounded-xl border border-[var(--border)]">`}
                    </div>
                    <button onclick="savePaymentMethods()" class="w-full bg-[var(--green)] text-white py-3.5 rounded-xl font-black text-[11px] uppercase active:scale-95"><i class="fas fa-save mr-1"></i> Save Payment Methods</button>
                </div>
            </div>

            <div class="mt-4">
                <p class="sec-header">Payment Automation</p>
                <div class="native-card p-4" style="border-color:rgba(42,171,238,0.2); background:rgba(42,171,238,0.04)">
                    ${paymentAutomationSettingsHtml()}
                </div>
            </div>

            <div id="admin-payment-dashboard" class="mt-4 mb-8">
                <div class="native-card p-4 mb-3">
                    <div class="flex justify-between items-center mb-4">
                        <div>
                            <h3 class="text-[14px] font-black text-white">Payments</h3>
                            <p class="text-[9px] text-[var(--text-muted)] uppercase tracking-widest mt-0.5">${pendingPayments.length} pending</p>
                        </div>
                        <button onclick="approveSafePayments()" class="bg-[rgba(0,194,111,0.15)] text-[var(--green)] border border-[rgba(0,194,111,0.2)] px-3 py-2 rounded-xl font-bold text-[10px] uppercase active:scale-95">
                            <i class="fas fa-check-double mr-1"></i> Approve Safe
                        </button>
                    </div>
                    <div class="flex gap-2 flex-wrap">
                        <button id="filter-all" onclick="setPaymentFilter('all')" class="pill-btn active">All</button>
                        <button id="filter-pending" onclick="setPaymentFilter('pending')" class="pill-btn">Pending</button>
                        <button id="filter-approved" onclick="setPaymentFilter('approved')" class="pill-btn">Approved</button>
                        <button id="filter-rejected" onclick="setPaymentFilter('rejected')" class="pill-btn">Rejected</button>
                    </div>
                </div>
                <div id="admin-payment-list"></div>
            </div>
            </div>`;
            return html;
        }

        function renderMembership() {
            if(IS_MASTER) return '';
            const profile = appState.profiles[appState.activeId];
            const pm = appState.paymentMethods || {};
            const expiryDate = profile.expiryDate || '';
            let isActive = false; let daysLeft = 0; let expiryLabel = 'Not Set';
            if (expiryDate) {
                const expObj = new Date(expiryDate);
                const today = new Date(); today.setHours(0,0,0,0); expObj.setHours(0,0,0,0);
                daysLeft = Math.ceil((expObj - today) / (1000*60*60*24));
                isActive = daysLeft > 0;
                expiryLabel = expObj.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
            }

            const makeUpiLink = (plan) => {
                const amt = plan === 'day' ? 500 : plan === 'week' ? 1500 : 4000;
                const note = encodeURIComponent('TITAN NOVA ' + plan.toUpperCase());
                const upi  = encodeURIComponent(pm.upi || 'admin@upi');
                const name = encodeURIComponent(pm.name || 'TITAN NOVA');
                return `upi://pay?pa=${upi}&pn=${name}&am=${amt}&cu=INR&tn=${note}`;
            };

            return `
            <div class="pb-6">
              <div class="mx-3 mt-3 mb-3 rounded-2xl overflow-hidden shadow-xl"
                   style="background:${isActive ? 'linear-gradient(135deg,#00A05E 0%,#1A8FC4 100%)' : 'linear-gradient(135deg,#8B1A1A 0%,#5B21B6 100%)'}">
                <div class="p-5">
                  <div class="flex items-center justify-between mb-4">
                    <div class="flex items-center gap-3">
                      <div class="w-11 h-11 rounded-2xl bg-white/15 flex items-center justify-center backdrop-blur-sm">
                        <i class="fas ${isActive ? 'fa-crown' : 'fa-lock'} text-white text-lg"></i>
                      </div>
                      <div>
                        <p class="text-white/60 text-[10px] font-bold uppercase tracking-widest">Membership</p>
                        <p class="text-white font-black text-base tracking-tight leading-tight">${profile.name}</p>
                      </div>
                    </div>
                    <span class="bg-white/20 text-white text-[10px] font-black px-3 py-1 rounded-full backdrop-blur-sm uppercase tracking-wider">
                      ${isActive ? '✓ ACTIVE' : '✗ EXPIRED'}
                    </span>
                  </div>
                  <div class="grid grid-cols-2 gap-3">
                    <div class="bg-white/10 rounded-xl p-3 backdrop-blur-sm border border-white/10">
                      <p class="text-white/60 text-[9px] font-black uppercase mb-1">Expiry Date</p>
                      <p class="text-white font-black text-sm">${expiryLabel}</p>
                    </div>
                    <div class="bg-white/10 rounded-xl p-3 backdrop-blur-sm border border-white/10">
                      <p class="text-white/60 text-[9px] font-black uppercase mb-1">Days Left</p>
                      <p class="text-white font-black text-sm">${expiryDate ? (isActive ? daysLeft + ' Days' : 'Expired') : '---'}</p>
                    </div>
                  </div>
                </div>
              </div>

              <div class="px-3 mb-3">
                <p class="sec-header">Plan Chunein</p>
                <div class="grid grid-cols-3 gap-2.5" id="plan-grid">
                  ${[
                    {id:'day',   label:'1 Din',  price:'₹500',  icon:'fa-sun',      grad:'linear-gradient(135deg,#FAC748,#EF4444)'},
                    {id:'week',  label:'Weekly',  price:'₹1500', icon:'fa-calendar-week', grad:'linear-gradient(135deg,#2AABEE,#3B82F6)'},
                    {id:'month', label:'Monthly', price:'₹4000', icon:'fa-gem',      grad:'linear-gradient(135deg,#7B8FFF,#EC4899)'},
                  ].map(p => `
                  <div class="rounded-2xl p-[1.5px] cursor-pointer plan-wrap" data-plan="${p.id}"
                       onclick="selectPlan('${p.id}')"
                       style="background:var(--surface-light)">
                    <div class="plan-inner bg-[var(--surface)] rounded-[15px] p-3 flex flex-col items-center gap-2">
                      <div class="w-10 h-10 rounded-xl flex items-center justify-center" style="background:${p.grad}">
                        <i class="fas ${p.icon} text-white text-sm"></i>
                      </div>
                      <p class="text-white font-black text-[11px] text-center leading-tight">${p.label}</p>
                      <p class="font-black text-[13px]" style="background:${p.grad};-webkit-background-clip:text;-webkit-text-fill-color:transparent">${p.price}</p>
                    </div>
                  </div>`).join('')}
                </div>
              </div>

              <div class="px-3 mb-3">
                <p class="sec-header">Plan Chunein, Phir Pay Karein</p>
                <div class="grid grid-cols-3 gap-2.5">
                  ${[
                    {id:'phonepe', label:'PhonePe', upi:'7077550644@ybl',               icon:'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/PhonePe_Logo.svg/2560px-PhonePe_Logo.svg.png',  color:'#6F3FFF'},
                    {id:'gpay',    label:'GPay',    upi:'kirannaik93244-4@okhdfcbank',   icon:'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f2/Google_Pay_Logo.svg/2560px-Google_Pay_Logo.svg.png', color:'#4285F4'},
                    {id:'paytm',   label:'Paytm',   upi:'7077550644@ptsbi',              icon:'https://upload.wikimedia.org/wikipedia/commons/4/42/Paytm_logo.png',                                         color:'#00BAF2'},
                  ].map(app => `
                  <button onclick="openUPIApp('${app.id}')"
                    class="flex flex-col items-center gap-2 py-4 px-2 rounded-2xl border border-[var(--border)] bg-[var(--surface-light)] active:scale-95 transition-transform"
                    style="border-color:${app.color}30">
                    <div class="w-10 h-10 rounded-xl flex items-center justify-center" style="background:${app.color}20">
                      <img src="${app.icon}" class="h-6 object-contain" onerror="this.style.display='none'" />
                    </div>
                    <span class="text-[11px] font-black text-white">${app.label}</span>
                    <span class="text-[8px] font-bold text-[var(--text-muted)] truncate w-full text-center px-1">${app.upi}</span>
                  </button>`).join('')}
                </div>
                <p class="text-[9px] text-[var(--text-muted)] text-center mt-2 font-bold">Upar se apna app choose karein — amount auto-fill hoga, sirf PIN dalein</p>

                <div class="mt-3 space-y-2">
                  ${[
                    {label:'PhonePe UPI', upi:'7077550644@ybl', color:'#6F3FFF'},
                    {label:'GPay UPI',    upi:'kirannaik93244-4@okhdfcbank', color:'#4285F4'},
                    {label:'Paytm UPI',  upi:'7077550644@ptsbi', color:'#00BAF2'},
                  ].map(u => `
                  <div class="flex items-center gap-3 bg-[var(--surface-light)] border border-[var(--border)] rounded-2xl p-3">
                    <div class="flex-1 min-w-0">
                      <p class="text-[9px] font-bold uppercase mb-0.5" style="color:${u.color}">${u.label}</p>
                      <p class="text-white font-black text-sm truncate">${u.upi}</p>
                    </div>
                    <button onclick="navigator.clipboard.writeText('${u.upi}').then(()=>showRealNotification('UPI Copied!','${u.upi} copy ho gaya','success'))"
                      class="shrink-0 text-white px-3 py-2 rounded-xl font-bold text-[10px] uppercase active:scale-95"
                      style="background:${u.color}">Copy</button>
                  </div>`).join('')}
                </div>

                ${pm.phone ? `
                <div class="mt-2 flex items-center gap-3 bg-[var(--surface-light)] border border-[var(--border)] rounded-2xl p-3">
                  <div class="flex-1">
                    <p class="text-[9px] text-[var(--text-muted)] font-bold uppercase mb-0.5">Phone Number</p>
                    <p class="text-white font-black text-sm">${pm.phone}</p>
                  </div>
                  <button onclick="navigator.clipboard.writeText('${pm.phone}').then(()=>showRealNotification('Number Copied!','Clipboard pe copy ho gaya.','success'))"
                    class="bg-[var(--green)] text-white px-4 py-2 rounded-xl font-bold text-[11px] uppercase active:scale-95">
                    Copy
                  </button>
                </div>` : ''}

                ${pm.qr ? `
                <div class="mt-3 bg-white rounded-2xl p-3 flex items-center justify-center">
                  <img src="${pm.qr}" class="w-48 h-48 object-contain" />
                </div>` : ''}
              </div>

              <div class="px-3 mb-3">
                <p class="sec-header">Payment Proof Submit</p>
                <div class="native-card p-4">
                  <div class="relative mb-3">
                    <div class="absolute left-3 top-1/2 -translate-y-1/2 w-7 h-7 bg-[var(--primary-glow)] rounded-lg flex items-center justify-center">
                      <i class="fas fa-rupee-sign text-[var(--primary)] text-xs"></i>
                    </div>
                    <input id="pay-amount" type="number" inputmode="numeric" placeholder="Amount ₹"
                      class="w-full bg-[var(--surface-light)] border border-[var(--border)] text-white font-bold rounded-2xl pl-11 pr-4 py-3.5 outline-none text-sm focus:border-[var(--primary)] transition-colors">
                  </div>
                  <div class="relative mb-3">
                    <div class="absolute left-3 top-1/2 -translate-y-1/2 w-7 h-7 bg-[rgba(42,171,238,0.12)] rounded-lg flex items-center justify-center">
                      <i class="fas fa-hashtag text-[var(--primary)] text-xs"></i>
                    </div>
                    <input id="pay-utr" type="text" placeholder="UTR / Transaction ID"
                      class="w-full bg-[var(--surface-light)] border border-[var(--border)] text-white font-bold rounded-2xl pl-11 pr-4 py-3.5 outline-none text-sm focus:border-[var(--primary)] transition-colors">
                  </div>
                  <label for="pay-image"
                    class="flex items-center gap-3 bg-[var(--surface-light)] border border-dashed border-[var(--surface-mid)] rounded-2xl p-3.5 mb-4 cursor-pointer active:scale-98 transition-transform">
                    <div class="w-9 h-9 bg-[rgba(123,143,255,0.12)] rounded-xl flex items-center justify-center shrink-0">
                      <i class="fas fa-camera text-[var(--purple)] text-base"></i>
                    </div>
                    <p class="text-[var(--text-muted)] text-sm font-bold" id="pay-file-label">Screenshot Upload Karein</p>
                    <i class="fas fa-chevron-right text-[var(--text-muted)] ml-auto text-xs"></i>
                  </label>
                  <input type="file" id="pay-image" accept="image/*" class="hidden"
                    onchange="document.getElementById('pay-file-label').textContent = this.files[0]?.name || 'Screenshot Upload Karein'">
                  <button id="pay-submit-btn" onclick="submitPayment()"
                    class="w-full py-4 rounded-2xl font-black text-[13px] uppercase tracking-wide text-white active:scale-95 transition-transform"
                    style="background:linear-gradient(135deg,var(--green),var(--green-dark));box-shadow:0 6px 20px rgba(0,194,111,0.3)">
                    <i class="fas fa-upload mr-2"></i> Payment Submit Karein
                  </button>
                </div>
              </div>

              <div class="px-3 mb-3">
                <p class="sec-header">Payment History</p>
                <div id="payment-list">
                  <div class="flex items-center justify-center py-8">
                    <i class="fas fa-spinner fa-spin text-[var(--text-muted)] text-xl"></i>
                  </div>
                </div>
              </div>

            </div>`;
        }

        function copyText(text, btn) {
            if(navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.writeText(text).then(() => {
                    const o = btn.innerHTML; btn.innerHTML = '<i class="fas fa-check mr-1"></i>Copied';
                    setTimeout(() => btn.innerHTML = o, 2000);
                });
            } else {
                let t = document.createElement('textarea'); t.value = text; t.style.position = 'fixed'; t.style.left = '-999999px'; document.body.appendChild(t); t.focus(); t.select();
                try { document.execCommand('copy'); const o = btn.innerHTML; btn.innerHTML = '<i class="fas fa-check mr-1"></i>Copied'; setTimeout(() => btn.innerHTML = o, 2000); } catch(e) {}
                t.remove();
            }
        }

        let _selectedPlan = 'week';
        function selectPlan(plan) {
            _selectedPlan = plan;
            document.querySelectorAll('.plan-wrap').forEach(el => {
                const isSelected = el.dataset.plan === plan;
                const grads = {
                    day:'linear-gradient(135deg,#FAC748,#EF4444)',
                    week:'linear-gradient(135deg,#2AABEE,#3B82F6)',
                    month:'linear-gradient(135deg,#7B8FFF,#EC4899)'
                };
                if (isSelected) {
                    el.style.background = grads[plan];
                    el.querySelector('.plan-inner').style.background = 'rgba(0,0,0,0.5)';
                } else {
                    el.style.background = 'var(--surface-light)';
                    el.querySelector('.plan-inner').style.background = 'var(--surface)';
                }
            });
            const amts = {day:500, week:1500, month:4000};
            const amtEl = document.getElementById('pay-amount');
            if (amtEl) amtEl.value = amts[plan];
        }

        function openUPIApp(appId) {
            const amts = {day:500, week:1500, month:4000};
            const amt = amts[_selectedPlan] || 1500;

            // Use hardcoded per-app UPI ID
            const upi  = HARDCODED_UPIS[appId] || HARDCODED_UPIS.phonepe;
            const name = HARDCODED_NAME;
            const note = 'TITAN NOVA ' + _selectedPlan.toUpperCase();

            const pa = encodeURIComponent(upi);
            const pn = encodeURIComponent(name);
            const tn = encodeURIComponent(note);

            // Pre-fill amount field
            const amtEl = document.getElementById('pay-amount');
            if (amtEl) amtEl.value = amt;

            const deepLinks = {
                gpay:    `tez://upi/pay?pa=${pa}&pn=${pn}&am=${amt}&cu=INR&tn=${tn}`,
                phonepe: `phonepe://pay?pa=${pa}&pn=${pn}&am=${amt}&cu=INR&tn=${tn}`,
                paytm:   `paytmmp://pay?pa=${pa}&pn=${pn}&am=${amt}&cu=INR&tn=${tn}`,
            };
            const genericUpi = `upi://pay?pa=${pa}&pn=${pn}&am=${amt}&cu=INR&tn=${tn}`;
            const link = deepLinks[appId] || genericUpi;

            let a = document.createElement('a');
            a.href = link;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);

            // Fallback to generic UPI after 1.5s if app didn't open
            setTimeout(() => {
                let b = document.createElement('a');
                b.href = genericUpi;
                document.body.appendChild(b);
                b.click();
                document.body.removeChild(b);
            }, 1500);
        }

        async function submitPayment() {
            const amount = document.getElementById('pay-amount').value;
            const utr    = document.getElementById('pay-utr').value;
            const fileInput = document.getElementById('pay-image');
            const submitBtn = document.getElementById('pay-submit-btn');

            if (!amount || !utr) { showRealNotification('⚠️ Error', 'Amount aur UTR zaroor daalein', 'danger'); return; }

            const originalBtnText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Uploading...';
            submitBtn.disabled = true;

            try {
                let imageUrl = '';
                if (fileInput && fileInput.files[0]) {
                    if (!IMGBB_API_KEY || IMGBB_API_KEY.includes("YAHAN")) {
                        showRealNotification('⚠️ Error', 'API Key missing!', 'danger');
                        submitBtn.innerHTML = originalBtnText; submitBtn.disabled = false;
                        return;
                    }

                    const formData = new FormData();
                    formData.append('image', fileInput.files[0]);

                    const res = await fetch('https://api.imgbb.com/1/upload?key=' + IMGBB_API_KEY, {
                        method: 'POST',
                        body: formData
                    });
                    const data = await res.json();

                    if (data.success) {
                        imageUrl = data.data.url;
                    } else {
                        throw new Error("ImgBB Upload API Error!");
                    }
                }

                await sendPayment(amount, utr, imageUrl);
            } catch(error) {
                showRealNotification('❌ Upload Failed', error.message, 'danger');
            } finally {
                submitBtn.innerHTML = originalBtnText;
                submitBtn.disabled = false;
            }
        }

        async function sendPayment(amount, utr, image) {
            const profile = appState.profiles[appState.activeId];
            const planLabels = {day:'1 Din - ₹500', week:'Weekly - ₹1500', month:'Monthly - ₹4000'};
            try {
                const res = await fetch('/api/submit_payment', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        userId: appState.activeId,
                        userName: profile.name,
                        amount: amount,
                        utr: utr,
                        image: image,
                        planLabel: planLabels[_selectedPlan] || _selectedPlan
                    })
                });
                const data = await res.json();
                const flagMessages = {
                    duplicate:  '⚠️ Duplicate UTR detected',
                    spam:       '⚠️ Multiple requests flagged',
                    low_amount: '⚠️ Amount too low',
                    high_amount:'⚠️ Amount too high',
                    utr_missing:'⚠️ UTR missing',
                    safe:       '✅ Payment submitted successfully'
                };
                const flagTypes = { duplicate: 'danger', spam: 'danger', low_amount: 'danger', high_amount:'danger', utr_missing:'danger', safe: 'success' };
                showRealNotification(flagMessages[data.flag] || '✅ Submitted', 'Admin jald verify karenge.', flagTypes[data.flag] || 'success');
                document.getElementById('pay-amount').value = '';
                document.getElementById('pay-utr').value = '';
                document.getElementById('pay-file-label').textContent = 'Screenshot Upload Karein';
                try {
                    const stateRes = await fetch('/api/state');
                    const newState = await stateRes.json();
                    appState.payments = (newState.payments || []).filter(p => p.userId === appState.activeId);
                } catch(e) {}
                loadPayments();
            } catch(e) { showRealNotification('❌ Network Error', 'Dobara try karein.', 'danger'); }
        }

        function loadPayments() {
            const container = document.getElementById('payment-list');
            if (!container) return;
            container.innerHTML = '';
            const payments = appState.payments || [];
            if (payments.length === 0) {
                container.innerHTML = '<p class="text-[var(--text-muted)] text-xs text-center py-4">Koi payment history nahi hai</p>';
                return;
            }
            payments.slice().reverse().forEach(p => {
                let color = 'text-[var(--amber)]';
                if (p.status === 'approved') color = 'text-[var(--green)]';
                if (p.status === 'rejected') color = 'text-[var(--rose)]';
                container.innerHTML += `
                <div class="native-card p-3 mb-2">
                    <div class="flex justify-between">
                        <span class="font-black text-white">₹${p.amount}</span>
                        <span class="${color} text-xs font-black uppercase">${p.status}</span>
                    </div>
                    <div class="text-xs text-[var(--text-muted)] mt-1">UTR: ${p.utr || '-'}</div>
                    <div class="text-[10px] text-[var(--text-muted)]">${p.time}</div>
                </div>`;
            });
        }

        let paymentFilter = 'all';

        function setPaymentFilter(type) {
            paymentFilter = type;
            document.querySelectorAll('.pill-btn').forEach(el => el.classList.remove('active'));
            const btn = document.getElementById('filter-' + type);
            if (btn) btn.classList.add('active');
            renderAdminPayments();
        }

        function renderAdminPayments() {
            const container = document.getElementById('admin-payment-list');
            if (!container) return;
            container.innerHTML = '';

            let payments = (appState.payments || []).slice();
            if (paymentFilter !== 'all') payments = payments.filter(p => p.status === paymentFilter);
            payments.reverse();

            if (payments.length === 0) {
                container.innerHTML = '<div class="text-center text-[var(--text-muted)] text-xs py-6 native-card"><i class="fas fa-inbox text-2xl mb-2 block opacity-30"></i>Koi payment nahi mili</div>';
                return;
            }

            payments.forEach(p => {
                let flagColor = 'text-[var(--text-muted)]';
                const flagText = p.autoFlag || 'safe';
                if (flagText === 'safe')      flagColor = 'text-[var(--green)]';
                if (flagText === 'duplicate') flagColor = 'text-[var(--rose)]';
                if (flagText === 'spam')      flagColor = 'text-[var(--amber)]';
                if (flagText === 'low_amount') flagColor = 'text-orange-400';

                let statusColor = 'text-[var(--amber)]';
                if (p.status === 'approved') statusColor = 'text-[var(--green)]';
                if (p.status === 'rejected') statusColor = 'text-[var(--rose)]';

                container.innerHTML += `
                <div class="native-card p-4 mb-2">
                    <div class="flex justify-between items-start mb-3">
                        <div>
                            <h3 class="font-black text-white uppercase text-[13px]">${p.userName}</h3>
                            <p class="text-xs text-[var(--text-muted)] mt-0.5">${p.time}</p>
                        </div>
                        <span class="${statusColor} text-xs font-black uppercase">${p.status}</span>
                    </div>
                    <div class="grid grid-cols-2 gap-2 mb-3">
                        <div class="bg-[var(--surface-light)] p-2.5 rounded-xl border border-[var(--border)]">
                            <p class="stat-lbl mb-0.5">Amount</p>
                            <p class="font-black text-white text-[13px]">₹${p.amount}</p>
                        </div>
                        <div class="bg-[var(--surface-light)] p-2.5 rounded-xl border border-[var(--border)]">
                            <p class="stat-lbl mb-0.5">UTR</p>
                            <p class="font-black text-white text-[11px] break-all">${p.utr || '-'}</p>
                        </div>
                    </div>
                    <div class="mb-3 flex flex-wrap gap-2 items-center">
                        <span class="${flagColor} text-[10px] font-black uppercase">⚡ ${flagText.toUpperCase()}</span>
                        ${p.riskLevel ? `<span class="text-[10px] font-black uppercase text-[var(--purple)]">🛡️ ${p.riskLevel}</span>` : ''}
                        ${p.walletCredited ? `<span class="text-[10px] font-black uppercase text-[var(--green)]">💳 WALLET +₹${p.walletCreditAmount || p.amount}</span>` : ''}
                    </div>
                    ${p.rejectReason ? `<div class="mb-3 bg-[rgba(255,93,93,0.08)] border border-[rgba(255,93,93,0.18)] rounded-xl p-2 text-[10px] text-[var(--rose)] font-bold">Reason: ${p.rejectReason}</div>` : ''}
                    ${p.image ? `<img src="${p.image}" class="w-full rounded-xl mb-3 border border-[var(--border)] max-h-48 object-contain"/>` : ''}
                    ${p.status === 'pending' ? `
                    <div class="flex gap-2">
                        <button onclick="approvePayment('${p.id}')" class="flex-1 bg-[var(--green)] text-white py-2.5 rounded-xl font-black text-xs active:scale-95">Approve</button>
                        <button onclick="rejectPayment('${p.id}')" class="flex-1 bg-[var(--rose)] text-white py-2.5 rounded-xl font-black text-xs active:scale-95">Reject</button>
                    </div>` : ''}
                </div>`;
            });
        }

        async function approvePayment(id) {
            const ps = appState.paymentSettings || {};
            const defaultDays = ps.extendMembershipOnApprove === false ? '0' : '30';
            const days = prompt('Kitne din membership extend karna hai? Wallet only ke liye 0 daalo.', defaultDays);
            if (days === null) return;
            const creditWallet = confirm('Is payment amount ko user wallet me credit karna hai? OK = Yes, Cancel = No');
            try {
                const res = await fetch('/api/approve_payment', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({paymentId: id, days: parseInt(days || '0'), creditWallet, extendMembership: ps.extendMembershipOnApprove !== false})
                });
                const data = await res.json();
                if(data.status !== 'success') throw new Error(data.message || 'Approve failed');
                if(data.wallets) appState.wallets = data.wallets;
                showRealNotification('✅ Approved!', creditWallet ? 'Wallet credit + payment approve complete.' : 'Payment approve complete.', 'success');
                await refreshPayments();
            } catch(e) { showRealNotification('❌ Approve Failed', String(e.message || e), 'danger'); }
        }

        async function rejectPayment(id) {
            const reason = prompt('Reject reason?', 'UTR/payment proof verify nahi hua');
            if (reason === null) return;
            try {
                const res = await fetch('/api/reject_payment', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({paymentId: id, reason})
                });
                const data = await res.json();
                if(data.status !== 'success') throw new Error(data.message || 'Reject failed');
                showRealNotification('❌ Rejected', 'Payment reject kar di gayi.', 'danger');
                await refreshPayments();
            } catch(e) { showRealNotification('❌ Reject Failed', String(e.message || e), 'danger'); }
        }

        async function approveSafePayments() {
            const payments = appState.payments || [];
            let count = 0;
            for (const p of payments) {
                if (p.status === 'pending' && p.autoFlag === 'safe') {
                    const res = await fetch('/api/approve_payment', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({paymentId: p.id, days: 0, creditWallet: true, extendMembership: false})
                    });
                    const data = await res.json();
                    if(data.status === 'success') count++;
                }
            }
            if (count > 0) showRealNotification('✅ Approved!', `${count} safe payment(s) wallet me credit kar di gayi.`, 'success');
            else showRealNotification('ℹ️ None Found', 'Koi safe pending payment nahi mili.', 'info');
            await refreshPayments();
        }

        async function refreshPayments() {
            try {
                const res = await fetch('/api/state');
                const newState = await res.json();
                appState = newState;
                state = appState.profiles[appState.activeId];
                renderAdminPayments();
            } catch(e) {}
        }

        async function savePaymentMethods() {
            const upi = document.getElementById('pm-upi').value.trim();
            const phone = document.getElementById('pm-phone').value.trim();
            const qr = document.getElementById('pm-qr-b64').value.trim();
            try {
                await fetch('/api/save_payment_methods', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({upi, phone, qr}) });
                showRealNotification('✅ Saved!', 'Payment methods update ho gaye.', 'success');
                await refreshMasterState();
            } catch(e) { showRealNotification('❌ Error', 'Save nahi ho saka.', 'danger'); }
        }

        async function scrapeMarket(type, i, marketName) {
            let field = 'open';
            let baseName = marketName;
            if (marketName.endsWith(' OPEN')) {
                field = 'open';
                baseName = marketName.replace(/ OPEN$/, '').trim();
            } else if (marketName.endsWith(' CLOSE')) {
                field = 'close';
                baseName = marketName.replace(/ CLOSE$/, '').trim();
            } else if (type === 'jodi') {
                field = 'jodi';
                baseName = marketName.trim();
            }

            const btn = document.getElementById(`scrape-btn-${type}-${i}`);
            const origHTML = btn ? btn.innerHTML : '';
            if (btn) { btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>'; btn.disabled = true; }

            try {
                const res = await fetch('/api/scrape_market', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({market: baseName})
                });
                const data = await res.json();

                if (data.status === 'success') {
                    const digits = field === 'open' ? data.open : (field === 'close' ? data.close : data.jodi);
                    const inp = document.getElementById(`in-d-${type}-${i}`);
                    if (inp) {
                        inp.value = digits;
                        updateMarket(type, i, 'd', digits);
                    }
                    if (btn) {
                        btn.innerHTML = '<i class="fas fa-check"></i> Done';
                        setTimeout(() => { if (btn) btn.innerHTML = origHTML; }, 3000);
                    }
                } else {
                    showRealNotification('⚠️ Scraping Error', data.message || 'Unknown error', 'danger');
                    if (btn) btn.innerHTML = origHTML;
                }
            } catch(e) {
                showRealNotification('❌ Network Error', 'Server se connect nahi ho pa raha.', 'danger');
                if (btn) btn.innerHTML = origHTML;
            } finally {
                if (btn) btn.disabled = false;
            }
        }

        async function saveExpiryDate(userId) {
            const expEl = document.getElementById('exp-' + userId);
            if (!expEl) return;
            const expiry = expEl.value;
            if (!expiry) return showRealNotification('⚠️ Error', 'Date select karein!', 'danger');
            try {
                await fetch('/api/set_expiry', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({userId, expiryDate: expiry}) });
                showRealNotification('✅ Expiry Set!', 'Membership expiry date update ho gayi.', 'success');
                await refreshMasterState();
                render(true);
            } catch(e) { showRealNotification('❌ Error', 'Save nahi ho saka.', 'danger'); }
        }

        async function refreshMasterState() {
            try {
                const res = await fetch('/api/state');
                const newState = await res.json();
                appState = newState;
                state = appState.profiles[appState.activeId];
            } catch(e) {}
        }

        async function handleQRSelect(input) {
            if (!input.files || !input.files[0]) return;

            if (!IMGBB_API_KEY || IMGBB_API_KEY.includes("YAHAN")) {
                showRealNotification('⚠️ Error', 'API Key missing!', 'danger');
                return;
            }

            const file = input.files[0];
            const label = document.getElementById('pm-qr-label');
            const originalText = label.textContent;
            label.textContent = "Uploading QR... ⏳";

            try {
                const formData = new FormData();
                formData.append('image', file);

                const res = await fetch('https://api.imgbb.com/1/upload?key=' + IMGBB_API_KEY, {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();

                if (data.success) {
                    const downloadURL = data.data.url;
                    document.getElementById('pm-qr-b64').value = downloadURL;
                    label.textContent = "QR Uploaded ✓";
                    document.getElementById('pm-qr-preview').src = downloadURL;
                    document.getElementById('pm-qr-preview').classList.remove('hidden');
                } else {
                    throw new Error("ImgBB Upload API Error!");
                }
            } catch(error) {
                showRealNotification('❌ QR Upload Failed', error.message, 'danger');
                label.textContent = originalText;
            }
        }

        function toggleVipAccess(pid, enabled) {
            if(!appState.profiles[pid]) return;
            appState.profiles[pid].vipAccessEnabled = enabled;
            autoSave();
            showRealNotification(enabled ? '✅ Access Enabled' : '🔒 Access Disabled',
                `${appState.profiles[pid].name} ka app access ${enabled ? 'enable' : 'disable'} kar diya gaya.`,
                enabled ? 'success' : 'danger');
        }

        function toggleAllMarketsOpenClose(trackDict, isChecked) {
            ensureDataStruct();
            baseMarkets.forEach(bm => {
                state.dayRecords[currentDate][trackDict][bm.n + ' OPEN']  = isChecked;
                state.dayRecords[currentDate][trackDict][bm.n + ' CLOSE'] = isChecked;
            });
            autoSave();
            render(true);
        }

        function sendBroadcast() {
            let t = document.getElementById('bcast-title').value.trim();
            let m = document.getElementById('bcast-msg').value.trim();
            if(!t || !m) return showRealNotification('⚠️ Error', 'Title aur Message dono likhna zaroori hai!', 'danger');

            if(!appState.broadcasts) appState.broadcasts = [];
            appState.broadcasts.push({id: Date.now(), title: t, msg: m});

            saveMaster(true);
            document.getElementById('bcast-title').value = '';
            document.getElementById('bcast-msg').value = '';

            showRealNotification('✅ Broadcast Sent!', 'Aapka message sabhi online VIPs ko bhej diya gaya hai.', 'success');
        }

        function render(keepScroll = true) {
            const currentScroll = window.scrollY || document.documentElement.scrollTop;

            ensureDataStruct();
            runLiveSync();

            renderAppBar();
            renderBottomNav();

            const sidebarContainer = document.getElementById('sidebar-links-container');
            if (sidebarContainer && sidebarContainer.innerHTML.trim() === '') {
                sidebarContainer.innerHTML = chartLinks.map(link =>
                    `<a href="${link.l}" target="_blank" class="side-link-btn active:scale-95 transition-transform">${link.n}</a>`
                ).join('');
            }

            const container = document.getElementById('screen-content');
            container.innerHTML = '';

            // User screen unlocked based on request

            if(mainNav === 'ledger') {
                container.innerHTML = renderSubTabs() + renderWalletHUD();
                container.appendChild(createLedgerList(activeTab, (activeTab==='jodi'?baseMarkets:markets), (activeTab==='ank'?'data':(activeTab==='jodi'?'jodiData':'pannelData'))));
            }
            else if(mainNav === 'audit') { container.innerHTML = renderWeeklyReport(); }
            else if(mainNav === 'smart' && IS_MASTER) { container.innerHTML = renderSmartAI(); }
            else if(mainNav === 'clients' && IS_MASTER) { container.innerHTML = renderClients(); }
            else if(mainNav === 'wallets' && IS_MASTER) { container.innerHTML = renderWalletsTab(); }
            else if(mainNav === 'entries' && IS_MASTER) { container.innerHTML = renderEntriesTab(); }
            else if(mainNav === 'payments' && IS_MASTER) { container.innerHTML = renderAdminPaymentsTab(); setTimeout(renderAdminPayments, 100); }
            else if(mainNav === 'results' && IS_MASTER) { container.innerHTML = renderResultsTab(); }
            else if(mainNav === 'forward' && IS_MASTER) { container.innerHTML = renderForwarderTab(); }
            else if(mainNav === 'guard' && IS_MASTER) { container.innerHTML = renderGuardTab(); }
            else if(mainNav === 'backup' && IS_MASTER) { container.innerHTML = renderBackupAuditTab(); }
            else if(mainNav === 'health' && IS_MASTER) { container.innerHTML = renderHealthMonitorTab(); if(!appState.healthMonitor) refreshHealthMonitor(); }
            else if(mainNav === 'settings' && IS_MASTER) { container.innerHTML = renderSettings(); }
            else if(mainNav === 'settings' && !IS_MASTER) { container.innerHTML = renderVipSettings(); }
            else if(mainNav === 'membership' && !IS_MASTER) { container.innerHTML = renderMembership(); setTimeout(() => { selectPlan(_selectedPlan); loadPayments(); }, 100); }

            if(keepScroll) {
                setTimeout(() => window.scrollTo(0, currentScroll), 10);
            } else {
                setTimeout(() => window.scrollTo(0, 0), 10);
            }
        }

        function processSmartPaste(targetType) {
            if(!IS_MASTER) return;
            ensureDataStruct();
            const textRaw = document.getElementById('smart-text-input').value;
            if(!textRaw.trim()) return showRealNotification('⚠️ Error', 'Paste input message!', 'danger');
            const lines = textRaw.toUpperCase().replace(/[^\\w\\s,:;|\\-⬆️⬇️₹]/g, ' ').split('\\n');
            let currentBaseMarket = ''; let currentPhase = 'OPEN'; let updatesCount = 0;
            const sortedMarkets = [...baseMarkets].sort((a, b) => b.n.length - a.n.length);
            const targetDict = targetType === 'ank' ? 'data' : (targetType === 'jodi' ? 'jodiData' : 'pannelData');
            const targetArr = targetType === 'jodi' ? baseMarkets : markets;

            lines.forEach(line => {
                let foundMarket = '';
                for(let bm of sortedMarkets) { if(line.includes(bm.n)) { foundMarket = bm.n; break; } }
                if(!foundMarket) {
                    if(line.includes('SRIDEVI') || line.includes('SRIDEV')) foundMarket = 'SRIDEV DAY';
                    else if(line.includes('MADHUR')) foundMarket = 'MADHUR DAY';
                    else if(line.includes('MILAN')) foundMarket = 'MILAN DAY';
                    else if(line.includes('RAJDHANI')) foundMarket = 'RAJDHANI DAY';
                    else if(line.includes('SUPREME')) foundMarket = 'SUPREME DAY';
                    else if(line.includes('KALYAN')) foundMarket = 'KALYAN';
                    else if(line.includes('TIME')) foundMarket = 'TIME BAZAR';
                    else if(line.includes('MAIN BAZAR')) foundMarket = 'MAIN BAZAR';
                }
                if (foundMarket) { currentBaseMarket = foundMarket; currentPhase = 'OPEN'; }
                if (currentBaseMarket) {
                    if (line.includes('NIGHT') || line.includes('NIT') || line.includes('NITE')) {
                        if (currentBaseMarket.includes('SRIDEV')) currentBaseMarket = 'SRIDEVI NIGHT'; else if (currentBaseMarket === 'KALYAN') currentBaseMarket = 'KALYAN NIGHT'; else if (currentBaseMarket.includes('MADHUR')) currentBaseMarket = 'MADHUR NIGHT'; else if (currentBaseMarket.includes('MILAN')) currentBaseMarket = 'MILAN NIGHT'; else if (currentBaseMarket.includes('RAJDHANI')) currentBaseMarket = 'RAJDHANI NIGHT'; else if (currentBaseMarket.includes('SUPREME')) currentBaseMarket = 'SUPREME NIGHT';
                    } else if (line.includes('DAY') || line.includes('MORNING')) {
                        if (currentBaseMarket.includes('SRIDEVI NIGHT')) currentBaseMarket = 'SRIDEV DAY'; else if (currentBaseMarket === 'KALYAN NIGHT') currentBaseMarket = 'KALYAN'; else if (currentBaseMarket.includes('MADHUR NIGHT')) currentBaseMarket = 'MADHUR DAY'; else if (currentBaseMarket.includes('MILAN NIGHT')) currentBaseMarket = 'MILAN DAY'; else if (currentBaseMarket.includes('RAJDHANI NIGHT')) currentBaseMarket = 'RAJDHANI DAY'; else if (currentBaseMarket.includes('SUPREME NIGHT')) currentBaseMarket = 'SUPREME DAY';
                    }
                }
                if (line.includes('CLOSE') || line.includes('⬇️') || line.includes('CL')) { currentPhase = 'CLOSE'; } else if (line.includes('OPEN') || line.includes('⬆️') || line.includes('OP')) { currentPhase = 'OPEN'; }
                if(!currentBaseMarket) return;
                let cleanLine = line.replace(/\\d{1,2}:\\d{2}/g, '').replace(/(RATE|INVEST|RS|₹|PRICE|AMT|AMOUNT|INV|INVESTMENT)[\\s:=]*\\d+/g, '');
                let digitMatches = cleanLine.match(/\\d+/g);
                if(!digitMatches) return;
                let validDigits = [];
                if(targetType === 'ank') validDigits = digitMatches.filter(n => n.length === 1); else if (targetType === 'jodi') validDigits = digitMatches.filter(n => n.length === 2); else if (targetType === 'pannel') validDigits = digitMatches.filter(n => n.length === 3);
                if(validDigits.length === 0) return;
                let extractedDigits = validDigits.join(', ');

                if (targetType === 'jodi') {
                    const idx = targetArr.findIndex(m => m.n === currentBaseMarket);
                    if (idx !== -1) {
                        Object.keys(appState.profiles).forEach(pid => {
                            let pState = appState.profiles[pid]; ensureDataStructForProfile(pState);
                            if(!pState.dayRecords[currentDate][targetDict][idx]) pState.dayRecords[currentDate][targetDict][idx] = { s: 'WAIT', d: '', r: '' };
                            let existing = pState.dayRecords[currentDate][targetDict][idx].d || "";
                            if(existing && !existing.includes(extractedDigits)) { pState.dayRecords[currentDate][targetDict][idx].d = existing + ", " + extractedDigits; } else if (!existing) { pState.dayRecords[currentDate][targetDict][idx].d = extractedDigits; }
                        }); updatesCount++;
                    }
                } else {
                    const targetName = currentBaseMarket + " " + currentPhase; const idx = targetArr.findIndex(m => m.n === targetName);
                    if(idx !== -1) {
                        Object.keys(appState.profiles).forEach(pid => {
                            let pState = appState.profiles[pid]; ensureDataStructForProfile(pState);
                            if(!pState.dayRecords[currentDate][targetDict][idx]) pState.dayRecords[currentDate][targetDict][idx] = { s: 'WAIT', d: '', r: '' };
                            let existing = pState.dayRecords[currentDate][targetDict][idx].d || "";
                            if(existing && !existing.includes(extractedDigits)) { pState.dayRecords[currentDate][targetDict][idx].d = existing + ", " + extractedDigits; } else if (!existing) { pState.dayRecords[currentDate][targetDict][idx].d = extractedDigits; }
                        }); updatesCount++;
                    }
                }
            });

            if(updatesCount > 0) { runLiveSync(); saveMaster(); document.getElementById('smart-text-input').value = ''; activeTab = targetType; setMainNav('ledger'); }
            else { showRealNotification('⚠️ No Data Found', 'No valid digits found in target format.', 'danger'); }
        }

        async function importContacts() { if (!('contacts' in navigator)) return showRealNotification('⚠️ Not Supported', 'Direct import support nahi karta.', 'danger'); try { const contacts = await navigator.contacts.select(['name', 'tel'], { multiple: false }); if (contacts.length) { const n = contacts[0].name[0]; let p = contacts[0].tel[0].replace(/\\D/g, ''); if (p.length >= 10) { const pid = 'client_' + Date.now(); appState.profiles[pid] = buildNewProfile(n, p.slice(-10)); autoSave(); render(true); } else showRealNotification('⚠️ Error', 'Phone support nahi mila!', 'danger'); } } catch (e) {} }
        function addVIP() { const n = document.getElementById('c-name').value.trim(); const p = document.getElementById('c-phone').value.replace(/\\D/g, ''); if(n) { const pid = 'client_' + Date.now(); appState.profiles[pid] = buildNewProfile(n, p.slice(-10)); autoSave(); render(true); } else showRealNotification('⚠️ Error', 'Valid Name chahiye.', 'danger'); }
        function deleteProfile(pid) { if(pid === 'client_dummy') return showRealNotification('⚠️ Error', 'Cannot delete Default Dummy Profile.', 'danger'); if(confirm("Bhai, kya sachme is VIP ka pura ledger delete karna hai?")) { delete appState.profiles[pid]; autoSave(); render(true); } }

        function openClient(pid) {
            if(!IS_MASTER) return;
            pushNativeState(); appState.activeId = pid; state = appState.profiles[pid]; activeTab = 'ank'; ensureDataStruct(); setMainNav('ledger');
        }

        function buildNewProfile(name, phone) {
            let masterConfig = appState.profiles['admin1'].config;
            let newProfile = { name: name, phone: phone, config: JSON.parse(JSON.stringify(masterConfig)), dayRecords: {}, expiryDate: '' };
            let masterToday = appState.profiles['admin1'].dayRecords[currentDate];
            if(masterToday) {
                newProfile.dayRecords[currentDate] = JSON.parse(JSON.stringify(masterToday));
            }
            return newProfile;
        }

        function prepDailyReportShare(type) {
            ensureDataStruct(); let arr = type === 'ank' ? markets : (type === 'jodi' ? baseMarkets : markets); let dictName = type === 'ank' ? 'data' : (type === 'jodi' ? 'jodiData' : 'pannelData'); let marginMultiplier = type === 'ank' ? 9.5 : (type === 'jodi' ? 95.0 : 150.0); let typeLabel = type.toUpperCase(); let record = state.dayRecords[currentDate]; if(!record || !record[dictName]) return showRealNotification('⚠️ No Data', 'No data available for today!', 'danger'); let msg = `🏆 *TITAN NOVA - DAILY REPORT [${typeLabel}]* 🏆\\n${appState.activeId !== 'admin1' ? '👤 *VIP:* ' + state.name + '\\n' : ''}📅 *DATE:* ${new Date(currentDate).toLocaleDateString('en-GB')}\\n━━━━━━━━━━━━━━━━━━━━\\n`; let tInvest = 0; let tWin = 0; let tPass = 0; let tFail = 0; let tRounds = 0; let details = ""; const visDict = type === 'ank' ? state.dayRecords[currentDate].visAnk : (type === 'jodi' ? state.dayRecords[currentDate].visJodi : state.dayRecords[currentDate].visPan); arr.forEach((m, idx) => { if (visDict && visDict[m.n] === false) return; let d = record[dictName][idx]; if(d && (d.s === 'PASS' || d.s === 'FAIL')) { const rawDigits = d.d ? String(d.d) : ''; const r = parseFloat(d.r) || 0; const invest = rawDigits.split(/[, ]+/).filter(x => x.trim()).length * r; let win = d.s === 'PASS' ? (r * marginMultiplier) : 0; let pl = win - invest; tInvest += invest; tWin += win; tRounds++; if(d.s === 'PASS') tPass++; else if(d.s === 'FAIL') tFail++; let plSign = pl >= 0 ? '+' : '-'; details += `🏛️ *${m.n}* [${d.s === 'PASS' ? '✅ PASS' : '❌ FAIL'}]\\n🔢 Digits: ${rawDigits}\\n💸 Inv: ₹${invest.toLocaleString()} | 💹 ${plSign}₹${Math.abs(pl).toLocaleString()}\\n\\n`; } }); if (tRounds === 0) return showRealNotification('⚠️ No Data', 'Koi completed round nahi hai aaj!', 'danger'); let net = tWin - tInvest; let finalLabel = net >= 0 ? 'PROFIT' : 'LOSS'; let finalSign = net >= 0 ? '+' : '-'; let maxRiskValue = globalStats[type].maxLoss || 0;
            msg += details + `━━━━━━━━━━━━━━━━━━━━\\n*DAILY SUMMARY [${typeLabel}]*\\n🔄 Rounds: ${tRounds} | ✅ Pass: ${tPass} | ❌ Fail: ${tFail}\\n🛡️ *Balance Risk:* Is Profit ko bachane ke liye ₹${maxRiskValue.toLocaleString()} backup zaroori tha.\\n🚀 *FINAL ${finalLabel}:* ${finalSign}₹${Math.abs(net).toLocaleString()}\\n━━━━━━━━━━━━━━━━━━━━\\n🚀 _Andres Barlin Logic V10.9_`;
            currentMsg = msg; renderShareModal();
        }

        function shareWeeklyReport() {
            let { monday, stats, totals } = getWeekStats(currentDate); let sunday = new Date(monday); sunday.setDate(sunday.getDate() + 6); let dateRange = `${monday.toLocaleDateString('en-GB', {day:'2-digit', month:'short'})} - ${sunday.toLocaleDateString('en-GB', {day:'2-digit', month:'short'})}`; let typeLabel = weeklyTabType.toUpperCase(); let typeStats = stats[weeklyTabType]; let msg = `🏆 *TITAN NOVA - WEEKLY REPORT [${typeLabel}]* 🏆\\n${appState.activeId !== 'admin1' ? '👤 *VIP:* ' + state.name + '\\n' : ''}📅 *WEEK:* ${dateRange}\\n━━━━━━━━━━━━━━━━━━━━\\n`; for (let bmName in typeStats) { let s = typeStats[bmName]; if(s.rounds > 0) { let pl = s.win - s.invest; msg += `🏛️ *${bmName}*\\n🔄 Rounds: ${s.rounds} | ✅ Pass: ${s.pass} | ❌ Fail: ${s.fail}\\n💸 Invest: ₹${s.invest.toLocaleString()}\\n💹 Net P/L: ${pl >= 0 ? '+' : ''}₹${pl.toLocaleString()}\\n━━━━━━━━━━━━━━━━━━━━\\n`; } } let tInvest = totals[weeklyTabType].invest; let tWin = totals[weeklyTabType].win; let net = tWin - tInvest; let tMaxLoss = totals[weeklyTabType].maxLoss || 0; let finalLabel = net >= 0 ? 'PROFIT' : 'LOSS'; let finalSign = net >= 0 ? '+' : '-';
            msg += `*${weeklyTabType.toUpperCase()} WEEKLY SUMMARY*\\n💰 Total Invest: ₹${tInvest.toLocaleString()}\\n💎 Total Win: ₹${tWin.toLocaleString()}\\n🛡️ *Ledger Risk:* Is hafte ₹${Math.abs(tMaxLoss).toLocaleString()} karcha backup chahiye tha.\\n🚀 *FINAL ${finalLabel}:* ${finalSign}₹${Math.abs(net).toLocaleString()}\\n━━━━━━━━━━━━━━━━━━━━\\n🚀 _Andres Barlin Logic V10.9_`;
            currentMsg = msg; renderShareModal();
        }

        function copyIntel(type, idx, btnElem) {
            const arr = type === 'ank' ? markets : (type === 'jodi' ? baseMarkets : markets); const m = arr[idx]; const dictName = type === 'ank' ? 'data' : (type === 'jodi' ? 'jodiData' : 'pannelData'); const d = state.dayRecords[currentDate]?.[dictName]?.[idx] || { d: '', r: '', s: 'WAIT' }; const rawDigits = d.d ? String(d.d) : ''; const r = parseFloat(d.r) || 0; const invest = rawDigits.split(/[, ]+/).filter(x => x.trim()).length * r; const s = globalStats[type]; const marginMultiplier = type === 'ank' ? 9.5 : (type === 'jodi' ? 95.0 : 150.0); const winAmount = r * marginMultiplier; const projectedPass = s.port + winAmount - invest; const projectedFail = s.port - invest;
            const copyText = `🚀 *TITAN NOVA INTEL* [${new Date(currentDate).toLocaleDateString('en-GB')}]\\n━━━━━━━━━━━━━━━━━━━━\\n🔥 *MARKET:* ${m.n}\\n🔢 *DIGITS:* [${d.d}]\\n💰 *PAR DIGIT:* ₹${r}\\n💸 *TOTAL:* ₹${invest.toLocaleString()}\\n━━━━━━━━━━━━━━━━━━━━\\n✅ *PASS HONE SE:* ${(projectedPass >= 0 ? '+' : '-')}₹${Math.abs(projectedPass).toLocaleString()}\\n❌ *FAIL HONE SE:* ${(projectedFail >= 0 ? '+' : '-')}₹${Math.abs(projectedFail).toLocaleString()}\\n━━━━━━━━━━━━━━━━━━━━`;
            const textToCopy = copyText.replace(/\\\\n/g, '\\n').replace(/\\n/g, '\\n');
            if(navigator.clipboard && window.isSecureContext) { navigator.clipboard.writeText(textToCopy).then(() => { const oHTML = btnElem.innerHTML; btnElem.innerHTML = '<i class="fas fa-check"></i> Copied'; setTimeout(() => { btnElem.innerHTML = oHTML; }, 2000); }); }
            else { let textArea = document.createElement("textarea"); textArea.value = textToCopy; textArea.style.position = "fixed"; textArea.style.left = "-999999px"; document.body.appendChild(textArea); textArea.focus(); textArea.select(); try { document.execCommand('copy'); const oHTML = btnElem.innerHTML; btnElem.innerHTML = '<i class="fas fa-check"></i> Copied'; setTimeout(() => { btnElem.innerHTML = oHTML; }, 2000); } catch (err) {} textArea.remove(); }
        }

        function prepShare(type, idx, msgType) {
            const arr = type === 'ank' ? markets : (type === 'jodi' ? baseMarkets : markets); const m = arr[idx]; const dictName = type === 'ank' ? 'data' : (type === 'jodi' ? 'jodiData' : 'pannelData'); const d = state.dayRecords[currentDate]?.[dictName]?.[idx] || { d: '', r: '', s: 'WAIT' }; const rawDigits = d.d ? String(d.d) : ''; const r = parseFloat(d.r) || 0; const invest = rawDigits.split(/[, ]+/).filter(x => x.trim()).length * r; const s = globalStats[type]; const typeLabel = type.toUpperCase(); const marginMultiplier = type === 'ank' ? 9.5 : (type === 'jodi' ? 95.0 : 150.0); const projectedPass = s.port + (r * marginMultiplier) - invest; const projectedFail = s.port - invest;
            if(msgType === 'GUIDE') { currentMsg = `🚀 *TITAN NOVA INTEL* [${new Date(currentDate).toLocaleDateString('en-GB')}]\\n━━━━━━━━━━━━━━━━━━━━\\n🔥 *MARKET:* ${m.n}\\n🔢 *DIGITS:* [${d.d}]\\n💰 *PAR DIGIT:* ₹${r}\\n💸 *TOTAL:* ₹${invest.toLocaleString()}\\n━━━━━━━━━━━━━━━━━━━━\\n✅ *PASS HONE SE:* ${(projectedPass >= 0 ? '+' : '-')}₹${Math.abs(projectedPass).toLocaleString()}\\n❌ *FAIL HONE SE:* ${(projectedFail >= 0 ? '+' : '-')}₹${Math.abs(projectedFail).toLocaleString()}\\n━━━━━━━━━━━━━━━━━━━━`; }
            else { currentMsg = `🚀 *RESULT UPDATE [${typeLabel}]*\\n👤 *VIP:* ${state.name}\\n━━━━━━━━━━━━━━━━━━━━\\n🔥 *MARKET:* ${m.n}\\n📝 *RESULT:* ${d.s === 'PASS' ? '✅ PASS' : (d.s === 'SKIP' ? '⚪ SKIP' : '❌ FAIL')}\\n🔢 *DIGITS:* [${d.d}]\\n━━━━━━━━━━━━━━━━━━━━\\n💹 *NET P/L:* ${(s.pl >= 0 ? '+' : '-')}₹${Math.abs(s.pl).toLocaleString()}\\n💎 *PORTFOLIO:* ₹${s.port.toLocaleString()}\\n━━━━━━━━━━━━━━━━━━━━\\n🚀 _Andres Barlin Logic V10.9_`; }
            renderShareModal();
        }

        function renderShareModal() {
            let html = '';
            Object.keys(appState.profiles).forEach(pid => {
                if(pid === 'admin1' || pid === 'client_dummy') return;
                let c = appState.profiles[pid];
                if(c.phone) {
                    html += `
                    <div class="p-4 rounded-xl bg-[var(--surface-light)] border border-[var(--border)] mb-2 flex justify-between items-center active:opacity-70 transition-opacity">
                        <div class="text-left leading-tight">
                            <p class="text-white text-[13px] font-black uppercase">${c.name}</p>
                            <p class="text-[var(--text-muted)] text-[9px] mt-0.5">+${c.phone}</p>
                        </div>
                        <div class="flex gap-2">
                            <button onclick="selectedPhone='${c.phone}'; triggerShare('WA')" class="w-10 h-10 bg-[#128C7E] text-white rounded-xl flex items-center justify-center active:scale-95"><i class="fab fa-whatsapp"></i></button>
                            <button onclick="selectedPhone='${c.phone}'; triggerShare('WAB')" class="w-10 h-10 bg-[rgba(42,171,238,0.2)] text-[var(--primary)] rounded-xl flex items-center justify-center active:scale-95 border border-[rgba(42,171,238,0.2)]"><i class="fas fa-briefcase text-sm"></i></button>
                        </div>
                    </div>`;
                }
            });

            let broadcastBtn = `
                <div class="flex gap-3 mb-2 mt-4">
                    <button onclick="selectedPhone=''; triggerShare('WA')" class="flex-1 py-3 rounded-xl border border-[var(--border)] text-[var(--text-muted)] bg-[var(--surface-light)] text-[10px] font-bold uppercase flex justify-center items-center gap-2 active:scale-95"><i class="fab fa-whatsapp text-[#25D366]"></i> WA Group</button>
                    <button onclick="selectedPhone=''; triggerShare('WAB')" class="flex-1 py-3 rounded-xl border border-[var(--border)] text-[var(--text-muted)] bg-[var(--surface-light)] text-[10px] font-bold uppercase flex justify-center items-center gap-2 active:scale-95"><i class="fas fa-users"></i> Biz Group</button>
                </div>`;

            document.getElementById('modal-client-list').innerHTML = (html || '') + broadcastBtn;
            pushNativeState();
            document.getElementById('shareModal').classList.add('open');
            window.shareModalOpen = true;
        }

        function triggerShare(appType) {
            const text = encodeURIComponent(currentMsg);
            let p = selectedPhone ? (selectedPhone.length === 10 ? '91'+selectedPhone : selectedPhone) : "";
            let url = '';
            if (appType === 'WA') { url = p ? `whatsapp://send?phone=${p}&text=${text}` : `whatsapp://send?text=${text}`; }
            else if (appType === 'WAB') { url = p ? `intent://send?phone=${p}&text=${text}#Intent;package=com.whatsapp.w4b;scheme=whatsapp;end;` : `intent://send?text=${text}#Intent;package=com.whatsapp.w4b;scheme=whatsapp;end;`; }
            window.location.href = url;
            setTimeout(() => { if(appType === 'WA' && !url.startsWith('intent')) { window.location.href = p ? `https://wa.me/${p}?text=${text}` : `https://api.whatsapp.com/send?text=${text}`; } }, 600);
            closeShareModal(false);
        }

        render();
        history.replaceState({base: true}, '', window.location.href);
    

function applyCombinedScrape(marketIndex, combinedDigits) {
    try {
        const inputEl = document.getElementById(`in-d-ank-${marketIndex}`);
        if(inputEl){
            inputEl.value = combinedDigits;
            inputEl.dispatchEvent(new Event('input', { bubbles: true }));
        }
    } catch(e){
        console.log(e);
    }
}





async function fetchCombinedScrape(btn){
    try{
        let card = btn.closest('.native-card');

        let market = '';

        if(card){
            const allText = card.innerText || '';
            const found = allText.match(/SRIDEV DAY|TIME BAZAR|MADHUR DAY|MILAN DAY|RAJDHANI DAY|SUPREME DAY|KALYAN NIGHT|KALYAN|SRIDEVI NIGHT|MADHUR NIGHT|SUPREME NIGHT|MILAN NIGHT|RAJDHANI NIGHT|MAIN BAZAR/i);

            if(found){
                market = found[0];
            }
        }

        if(!market){
            alert('Market detect failed');
            return;
        }

        const res = await fetch('/api/scrape_market', {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body: JSON.stringify({market: market})
        });

        const data = await res.json();

        if(data.status === 'success'){
            const combined = data.combined || '';

            const input = card ? card.querySelector('input') : null;

            if(input){
                input.value = combined;
                input.dispatchEvent(new Event('input', { bubbles:true }));
            }

            alert('Combined Applied: ' + combined);
        } else {
            alert(data.message || 'Scrape Failed');
        }

    }catch(e){
        console.log(e);
        alert('Error');
    }
}



</script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=False)
