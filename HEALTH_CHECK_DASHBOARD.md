# 🏥 Health Check Dashboard & Monitoring

**Real-time System Health Monitoring**

---

## 📊 Dashboard Overview

```
┌─────────────────────────────────────────────────────────────┐
│ TITAN NOVA - HEALTH MONITOR                          🟢 OK   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  FIREBASE STATUS              GATEWAY STATUS                │
│  🟢 Connected                 🟢 Online                      │
│  📡 Latency: 245ms           ⏱️  Uptime: 14h 23m            │
│  💾 Data: 2.4 MB             👥 Users: 42                   │
│                                                               │
│  WHATSAPP STATUS              RESULT SCRAPER                │
│  🟢 Connected                 🟢 Active                      │
│  📱 Groups: 8                 ✅ Last run: 2m ago           │
│  👤 Contacts: 156             📈 Updates today: 24          │
│                                                               │
│  ENTRY PARSER                 PAYMENT QUEUE                 │
│  🟢 Active                    🟡 1 Pending                  │
│  ✅ Accepted: 45              ⏳ Last send: 5m ago          │
│  ❌ Rejected: 3               💰 Total: ₹2,500             │
│                                                               │
│  SPAM GUARD                   LOAD FORWARDER                │
│  🟢 Enabled                   🟢 Ready                      │
│  🛡️  Events: 8                📊 Last report: 1h ago        │
│  ✅ Blocks: 12                🎯 Next run: 2h               │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔍 Health Endpoints

### GET `/health` (Gateway)
**Detailed gateway health**

```bash
curl http://127.0.0.1:3000/health
```

**Response:**
```json
{
  "status": "success",
  "connected": true,
  "user": {
    "id": "919876543210@s.whatsapp.net",
    "name": "Titan Nova Bot"
  },
  "firebase": {
    "url": "https://titan-bbbc4-default-rtdb.firebaseio.com/",
    "connected": true,
    "lastCheckedAt": "2024-01-15T10:30:00Z"
  },
  "waLogin": {
    "qrAvailable": false,
    "connected": true,
    "authDir": "/root/new-nova/auth_info_baileys",
    "resetCount": 2,
    "lastSessionResetAt": "2024-01-15T08:00:00Z"
  },
  "targets": {
    "contacts": 156,
    "groups": 8,
    "updatedAt": "2024-01-15T10:15:00Z"
  },
  "scrape": {
    "enabled": true,
    "envEnabled": true,
    "adminEnabled": true,
    "intervalMs": 5000,
    "confirmCount": 2,
    "status": "active"
  },
  "queue": {
    "paymentPending": 1,
    "loadForwardPending": 0,
    "entriesAcceptedToday": 45
  },
  "modules": {
    "entryParser": true,
    "settlement": true,
    "loadForwarder": true,
    "spamGuard": true
  },
  "health": {
    "startedAt": "2024-01-15T08:00:00Z",
    "lastWhatsAppEvent": "open",
    "lastDisconnectCode": "",
    "lastScheduleTickAt": "2024-01-15T10:29:00Z",
    "lastResultTickAt": "2024-01-15T10:29:00Z",
    "lastResultSendAt": "2024-01-15T10:25:00Z",
    "lastResultScrapeTickAt": "2024-01-15T10:29:00Z",
    "lastResultScrapeStatus": "success",
    "lastResultScrapeUpdates": [
      {
        "market": "KALYAN OPEN",
        "stage": "open",
        "result": "144-9"
      }
    ],
    "lastPaymentOutboxTickAt": "2024-01-15T10:29:00Z",
    "lastLoadForwarderTickAt": "2024-01-15T10:29:00Z"
  }
}
```

---

### GET `/status` (Gateway Quick Status)
**Quick status check**

```bash
curl http://127.0.0.1:3000/status
```

**Response:**
```json
{
  "status": "success",
  "connected": true,
  "firebase": "https://titan-bbbc4-default-rtdb.firebaseio.com/titan_master_data.json",
  "timezone": "Asia/Kolkata",
  "now": "10:30",
  "date": "2024-01-15",
  "cache": "2024-01-15T10:15:00Z",
  "counts": {
    "activeMarkets": 18,
    "customMarkets": 2,
    "resultTargets": 12,
    "acceptedEntriesToday": 45,
    "settlementsToday": 8
  },
  "health": {
    "uptime": "14h 30m",
    "lastError": null
  }
}
```

---

### GET `/logger/health` (Logging System)
**Check logging system health**

```bash
curl http://127.0.0.1:3000/logger/health
```

**Response:**
```json
{
  "app": "gateway",
  "timestamp": "2024-01-15T10:30:00Z",
  "logFiles": {
    "main": true,
    "errors": true,
    "audit": true
  },
  "logSizes": {
    "main": 2457600,
    "errors": 512000,
    "audit": 1024000
  }
}
```

---

### GET `/api/health-monitor` (Flask App)
**Flask app health details**

```bash
curl http://127.0.0.1:5000/api/health-monitor
```

**Response:**
```json
{
  "status": "success",
  "app": "flask_app",
  "timestamp": "2024-01-15T10:30:00Z",
  "firebase": {
    "status": "connected",
    "latency_ms": 245,
    "lastCheckedAt": "2024-01-15T10:30:00Z"
  },
  "database": {
    "entries": 1250,
    "wallets": 42,
    "settlements": 156,
    "auditLogs": 5420
  },
  "systemHealth": {
    "memoryUsage": "45%",
    "cpuUsage": "12%",
    "diskUsage": "68%"
  },
  "recentErrors": [],
  "warningCount": 0
}
```

---

## 📈 Monitoring Metrics

### Key Metrics to Track

```
Performance:
├─ API Response Time < 500ms
├─ Firebase Latency < 1000ms
├─ WhatsApp Message Delivery > 95%
├─ Entry Processing < 2s
└─ Result Settlement < 5s

Reliability:
├─ Gateway Uptime > 99.5%
├─ Firebase Connection Success > 99%
├─ WhatsApp Connection Stability > 98%
├─ Scheduled Tasks Completion > 95%
└─ Payment Processing Success > 99%

Business:
├─ Entries Accepted per Hour
├─ Settlements per Day
├─ Payment Queue Length
├─ Active Users
└─ Result Update Frequency
```

---

## 🚨 Alert Conditions

### Critical Alerts (Immediate Action)

```
🚨 FIREBASE OFFLINE
   → Check network connectivity
   → Verify FIREBASE_URL in env
   → Check Firebase dashboard
   → Action: Restart Gateway

🚨 WHATSAPP DISCONNECTED
   → Check internet connection
   → Verify account not logged in elsewhere
   → Check QR code generation
   → Action: Reset WhatsApp session

🚨 PAYMENT QUEUE OVERFLOW (> 50 items)
   → Payment processing slow
   → Admin not approving/rejecting
   → Check payment processor
   → Action: Manual review needed

🚨 ERROR LOG SIZE > 100MB
   → Disk space issue
   → High error rate
   → Check application logs
   → Action: Archive old logs
```

### Warning Alerts (Monitor)

```
⚠️ API Response Time > 1000ms
   → Performance degraded
   → Check Firebase latency
   → Monitor CPU usage

⚠️ WhatsApp QR Not Generated (> 5 mins)
   → Session issue
   → Network problem
   → Action: Check logs

⚠️ Scraper Failures (> 3 consecutive)
   → Website structure changed
   → Network blocks
   → Action: Check scraper URLs

⚠️ Spam Guard Events > 10/hour
   → High spam activity
   → Possible attack
   → Action: Review events
```

---

## 📊 Monitoring Dashboard (Admin UI)

```html
<!-- Add to flask_app.py HTML_TEMPLATE -->

<div class="health-monitor">
  <!-- Status Indicators -->
  <div class="status-grid">
    <div class="status-card firebase">
      <h3>🔥 Firebase</h3>
      <p class="status">🟢 Connected</p>
      <p class="metric">Latency: 245ms</p>
      <p class="metric">Last: 2m ago</p>
    </div>
    
    <div class="status-card gateway">
      <h3>⚙️ Gateway</h3>
      <p class="status">🟢 Online</p>
      <p class="metric">Uptime: 14h 23m</p>
      <p class="metric">Users: 42</p>
    </div>
    
    <div class="status-card whatsapp">
      <h3>💬 WhatsApp</h3>
      <p class="status">🟢 Connected</p>
      <p class="metric">Groups: 8</p>
      <p class="metric">Contacts: 156</p>
    </div>
    
    <div class="status-card parser">
      <h3>✍️ Entry Parser</h3>
      <p class="status">🟢 Active</p>
      <p class="metric">Accepted: 45</p>
      <p class="metric">Rejected: 3</p>
    </div>
  </div>

  <!-- Error Log -->
  <div class="error-log">
    <h3>📋 Recent Errors</h3>
    <table>
      <thead>
        <tr>
          <th>Time</th>
          <th>Level</th>
          <th>Message</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody id="error-list">
        <!-- Populated dynamically -->
      </tbody>
    </table>
  </div>

  <!-- Auto Refresh -->
  <div class="controls">
    <button onclick="refreshHealthMonitor()">🔄 Refresh</button>
    <button onclick="downloadHealthReport()">📥 Download Report</button>
    <label>Auto-refresh: 
      <input type="checkbox" id="auto-refresh" checked>
    </label>
  </div>
</div>

<style>
  .health-monitor {
    padding: 20px;
  }
  
  .status-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
    margin-bottom: 30px;
  }
  
  .status-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    padding: 15px;
    text-align: center;
  }
  
  .status-card.firebase { border-color: rgba(255, 100, 0, 0.3); }
  .status-card.gateway { border-color: rgba(0, 150, 200, 0.3); }
  .status-card.whatsapp { border-color: rgba(0, 200, 100, 0.3); }
  .status-card.parser { border-color: rgba(200, 150, 0, 0.3); }
  
  .status { font-size: 18px; font-weight: bold; margin: 10px 0; }
  .metric { font-size: 12px; color: #aaa; margin: 5px 0; }
</style>

<script>
  async function refreshHealthMonitor() {
    try {
      const res = await fetch('/api/health-monitor');
      const data = await res.json();
      updateDashboard(data);
    } catch (e) {
      console.error('Health check failed:', e);
    }
  }
  
  // Auto-refresh every 10 seconds
  if (document.getElementById('auto-refresh')?.checked) {
    setInterval(refreshHealthMonitor, 10000);
  }
</script>
```

---

## 🔧 Health Check Script

```bash
#!/bin/bash
# health-check.sh - Monitor system health

echo "🏥 Titan Nova Health Check"
echo "================================"

# Check Flask App
echo -n "Flask App: "
if curl -s http://127.0.0.1:5000/api/health-monitor > /dev/null; then
  echo "✅ OK"
else
  echo "❌ DOWN"
fi

# Check Gateway
echo -n "Gateway: "
if curl -s http://127.0.0.1:3000/health > /dev/null; then
  echo "✅ OK"
else
  echo "❌ DOWN"
fi

# Check Firebase
echo -n "Firebase: "
if curl -s https://titan-bbbc4-default-rtdb.firebaseio.com/.json > /dev/null 2>&1; then
  echo "✅ OK"
else
  echo "❌ DOWN"
fi

# Check Logs
echo ""
echo "📊 Log Status:"
echo "  Main: $(wc -l < logs/gateway.log 2>/dev/null || echo 'N/A') lines"
echo "  Errors: $(wc -l < logs/gateway-errors.log 2>/dev/null || echo 'N/A') lines"
echo "  Audit: $(wc -l < logs/gateway-audit.log 2>/dev/null || echo 'N/A') lines"

echo ""
echo "✅ Health check complete"
```

**Run:**
```bash
chmod +x health-check.sh
./health-check.sh
```

---

## 📱 WhatsApp Health Alerts

Bot automatically sends health alerts to admin group:

```
🏥 *DAILY HEALTH REPORT*
━━━━━━━━━━━━━━━━━━━━
📅 Date: 2024-01-15
🕐 Time: 11:00 PM

✅ *SYSTEM STATUS: HEALTHY*

📊 *Today's Stats:*
  Entries: 245
  Settlements: 18
  Payments: ₹45,000
  Errors: 0

🟢 *All Systems Online*
  Firebase: Connected (avg 245ms)
  WhatsApp: Connected (8 groups)
  Scraper: Running (24 updates)

⏰ *Next Report: 2024-01-16 11:00 PM*
```

---

## 🛠️ Troubleshooting Guide

| Issue | Check | Fix |
|-------|-------|-----|
| Gateway offline | Port 3000 listening? | `lsof -i :3000` |
| Firebase errors | Network? URL? | `curl https://...` |
| WhatsApp disc. | Auth files? Network? | Reset session via UI |
| High CPU | Memory leaks? Scraper? | Check logs, restart |
| Slow API | Firebase latency? | Move to closer region |

---

## 📞 Emergency Contacts

```
🚨 Critical Issues:
  Admin: +91-XXXXXX-XXXX
  Tech Lead: +91-YYYYYY-YYYY

⚠️ Support Hours:
  9 AM - 11 PM IST
  Daily except Sundays
```
