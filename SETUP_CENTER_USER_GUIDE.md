# 📖 Setup Control Center - Complete User Guide

**Setup Tab में सब कुछ समझें - Hindi + English**

---

## 🎯 Setup Center क्या है?

Setup Control Center एक **Admin Dashboard** है जहां आप:
- ✅ बाजारों को add/remove/customize कर सकते हो
- ✅ Entry parser settings configure कर सकते हो
- ✅ Result scraper settings manage कर सकते हो
- ✅ Spam guard rules set कर सकते हो
- ✅ Load forwarder schedule कर सकते हो
- ✅ Complete backup ले सकते हो

---

## 📱 Setup Tab में Kya Hai?

```
┌─────────────────────────────────────────┐
│ SETUP CONTROL CENTER                    │
├─────────────────────────────────────────┤
│                                          │
│ [MARKET] [VISIBLE] [MONEY] [RULES]      │ ← 4 Main Tabs
│                                          │
│ ┌──────────────────────────────────────┐ │
│ │ MARKET TAB                            │ │
│ ├──────────────────────────────────────┤ │
│ │ • Add/Save/Delete Markets             │ │
│ │ • Set market timings                  │ │
│ │ • Custom markets management           │ │
│ └──────────────────────────────────────┘ │
│                                          │
│ ┌──────────────────────────────────────┐ │
│ │ VISIBLE TAB                           │ │
│ ├──────────────────────────────────────┤ │
│ │ • Select which markets to show        │ │
│ │ • ANK / JODI / PENEL filtering        │ │
│ └──────────────────────────────────────┘ │
│                                          │
│ ┌──────────────────────────────────────┐ │
│ │ MONEY TAB                             │ │
│ ├──────────────────────────────────────┤ │
│ │ • Set settlement payouts              │ │
│ │ • Credit limit settings               │ │
│ │ • Wallet configuration                │ │
│ └──────────────────────────────────────┘ │
│                                          │
│ ┌──────────────────────────────────────┐ │
│ │ RULES TAB                             │ │
│ ├──────────────────────────────────────┤ │
│ │ • Entry parsing rules                 │ │
│ │ • Risk limits                         │ │
│ │ • Auto scrape settings                │ │
│ └──────────────────────────────────────┘ │
│                                          │
└─────────────────────────────────────────┘
```

---

## 1️⃣ MARKET TAB - बाजार प्रबंधन

### Add New Market

```
📌 STEP 1: "ADD / SAVE MARKET" button दबाओ

┌─────────────────────────────────────────┐
│ MARKET NAME:                             │
│ [____________________]                  │
│ उदाहरण: KALYAN, DELHI DAY, SRIDEVI    │
│                                          │
│ OPEN TIME:                               │
│ [___:___] (24 hour format, e.g., 15:50) │
│                                          │
│ CLOSE TIME:                              │
│ [___:___]                                │
│                                          │
│ [☐] Include in scraping                 │
│ [☐] Show in results                     │
│                                          │
│ RESULT URL (optional):                   │
│ [_______________________]                │
│                                          │
│ [SAVE MARKET]  [CANCEL]                 │
└─────────────────────────────────────────┘

📌 STEP 2: "SAVE MARKET" दबाओ

✅ SUCCESS: Market KALYAN added!
```

### Delete Market

```
❌ STEP 1: Market को list से select करो

┌─────────────────────────────────────────┐
│ EXISTING MARKETS:                       │
│ • KALYAN [Edit] [Delete]               │
│ • SRIDEVI DAY [Edit] [Delete]          │
│ • MILAN [Edit] [Delete]                │
└─────────────────────────────────────────┘

❌ STEP 2: "Delete" button दबाओ

⚠️  CONFIRM: सभी entries delete हो जाएंगी?
[YES, DELETE] [CANCEL]

✅ DONE: Market KALYAN deleted!
```

---

## 2️⃣ VISIBLE TAB - दृश्यता सेटिंग्स

### Market Display Settings

```
👁️  कौन से markets को दिखाना है?

GAME TYPE FILTER:
┌─────────────────────────────────────────┐
│ [✓] ANK         (Single digit)          │
│ [✓] JODI        (Two digits)            │
│ [✓] PENEL       (Three digits)          │
└─────────────────────────────────────────┘

MARKET VISIBILITY:
┌─────────────────────────────────────────┐
│ DAY MARKETS:                             │
│ [✓] SRIDEV DAY         [Edit]           │
│ [✓] TIME BAZAR         [Edit]           │
│ [✓] MADHUR DAY         [Edit]           │
│ [☐] CUSTOM MARKET 1    [Edit]           │
│                                          │
│ NIGHT MARKETS:                           │
│ [✓] SRIDEVI NIGHT      [Edit]           │
│ [✓] KALYAN NIGHT       [Edit]           │
│ [☐] MAIN BAZAR         [Edit]           │
└─────────────────────────────────────────┘

[SAVE VISIBILITY] [RESET TO DEFAULT]
```

---

## 3️⃣ MONEY TAB - पैसे की सेटिंग्स

### Settlement Payouts (जीतने पर कितना देना है)

```
💰 बिट की गई राशि का कितना गुना देना है?

PAYOUT MULTIPLIERS:
┌─────────────────────────────────────────┐
│ ANK:     [_____] ✓ (default: 9.5x)     │
│          ₹100 लगाओ → ₹950 जीतो         │
│                                          │
│ JODI:    [_____] ✓ (default: 9.5x)     │
│          ₹100 लगाओ → ₹950 जीतो         │
│                                          │
│ PENEL:   [_____] ✓ (default: 150x)     │
│          ₹100 लगाओ → ₹15,000 जीतो      │
│                                          │
│ [SAVE PAYOUTS]                          │
└─────────────────────────────────────────┘
```

### Wallet Settings

```
💳 User के wallet settings

DEFAULT CREDIT LIMIT:
┌─────────────────────────────────────────┐
│ New users को कितना credit दे सकते हो? │
│ [₹ _________]                           │
│ (default: ₹10,000)                      │
│                                          │
│ [SAVE SETTINGS]                         │
└─────────────────────────────────────────┘

WALLET FEATURES:
┌─────────────────────────────────────────┐
│ [✓] Auto-debit from wallet               │
│     (Entry लगाते समय automatically काट) │
│                                          │
│ [✓] Settlement auto-credit               │
│     (जीतने पर अपने आप पैसे जमा)        │
│                                          │
│ [✓] Notify user on changes               │
│     (हर transaction पर WhatsApp message) │
└─────────────────────────────────────────┘
```

---

## 4️⃣ RULES TAB - नियम सेटिंग्स

### Entry Parser Rules

```
✍️  Entry कैसे लिए जाएंगे - rules set करो

ENTRY FORMAT:
┌─────────────────────────────────────────┐
│ Users को ये format में भेजना होगा:   │
│                                          │
│ MARKET: KALYAN OPEN                     │
│ TYPE: ANK                               │
│ DIGITS: 5,7,9                           │
│ PAR DIGIT: 100                          │
│ TOTAL: 300                              │
│                                          │
│ [☑] Strict format enforcement           │
│ [☑] Reject if format wrong              │
└─────────────────────────────────────────┘

ENTRY TIMING:
┌─────────────────────────────────────────┐
│ [✓] Entries लगाने का समय सीमा          │
│     Market के close time से पहले       │
│                                          │
│ [✓] Auto-close entries after market time│
│                                          │
│ Day boundary:                            │
│ [__:__] (e.g., 06:00 - रात 6 बजे)    │
└─────────────────────────────────────────┘
```

### Risk Management

```
⚠️  Risk limits - कितना entry ले सकते हो

USER DAILY LIMIT:
┌─────────────────────────────────────────┐
│ Per user daily limit:                   │
│ ₹[________]  (e.g., ₹50,000)           │
│ (एक user एक दिन में कितना खेल सकता है)│
│                                          │
│ Warning at: __% of limit                │
│ Auto-block at: 100%                     │
└─────────────────────────────────────────┘

MARKET DAILY LIMIT:
┌─────────────────────────────────────────┐
│ Per market daily limit:                 │
│ ₹[________]  (e.g., ₹1,00,000)         │
│ (एक बाजार में कुल कितना खेल सकते हैं) │
│                                          │
│ [✓] Auto-lock market if limit reached  │
└─────────────────────────────────────────┘

DIGIT LOAD LIMIT:
┌─────────────────────────────────────────┐
│ Per digit load:                         │
│ ₹[________]  (e.g., ₹10,000)           │
│ (एक अंक पर कुल कितना बीट हो सकता है)  │
└─────────────────────────────────────────┘
```

### Result Scraping

```
🤖 Result automatically fetch करना

AUTO SCRAPE SETTINGS:
┌─────────────────────────────────────────┐
│ [✓] Enable auto-scraping                │
│                                          │
│ Check interval:                         │
│ [__] seconds (default: 5s)              │
│                                          │
│ Confirm count:                          │
│ [__] times (must see same result x times)│
│                                          │
│ Scrape URLs:                            │
│ [_________________________________]     │
│ [_________________________________]     │
│                                          │
│ [SAVE SCRAPER SETTINGS]                 │
└─────────────────────────────────────────┘

🔔 RESULTS WILL AUTO-SEND TO:
├─ WhatsApp targets saved in Forward tab
├─ Result targets from Settings
└─ Settlement report to admin group
```

---

## 🔒 Advanced Settings

### Spam Guard Configuration

```
🛡️  Group में spam हटाने के लिए

LINK GUARD:
┌─────────────────────────────────────────┐
│ [✓] Enable link blocking                │
│ Strike limit: [_] (kick at 3rd strike) │
│ Message: "⚠️ Links not allowed"        │
└─────────────────────────────────────────┘

FORWARD GUARD:
┌─────────────────────────────────────────┐
│ [✓] Enable forward blocking             │
│ Strike limit: [_]                       │
│ Window: [__] seconds                    │
└─────────────────────────────────────────┘
```

---

## 💾 Backup & Restore

### Backup लेना

```
📥 पूरा setup backup करो

BACKUP OPTIONS:
┌─────────────────────────────────────────┐
│ [DOWNLOAD BACKUP]                       │
│ ✓ All markets                           │
│ ✓ Settings                              │
│ ✓ Rules                                 │
│ ✓ Payouts                               │
│ ✓ Wallet config                         │
│                                          │
│ File: setup_backup_2024-01-15.zip      │
│ Size: 2.4 MB                            │
│ Time: ~30 seconds                       │
└─────────────────────────────────────────┘
```

### Restore करना

```
📤 Backup से restore करो

⚠️  WARNING: यह सब कुछ replace कर देगा!

┌─────────────────────────────────────────┐
│ [CHOOSE FILE]  [setup_backup_...]      │
│                                          │
│ [RESTORE FROM BACKUP]                   │
│                                          │
│ Restoring...
│ ✓ Markets restored
│ ✓ Settings restored
│ ✓ Rules restored
│                                          │
│ ✅ RESTORE COMPLETE                     │
└─────────────────────────────────────────┘
```

---

## 🚨 Common Issues & Solutions

### Issue 1: "Firebase Connection Failed"
```
❌ Problem: Firebase URL not working

✅ Solution:
1. Setup tab खोलो
2. "TEST FIREBASE CONNECTION" दबाओ
3. अगर error आए तो:
   - Check internet connection
   - Verify FIREBASE_DB_URL in env
   - Contact admin
```

### Issue 2: "Market Not Appearing"
```
❌ Problem: Market add कर दिया पर दिख नहीं रहा

✅ Solution:
1. VISIBLE tab में check करो कि market enabled है
2. Game type filter check करो
3. "Save Visibility" दबाओ
4. Page refresh करो
```

### Issue 3: "Entries Not Being Accepted"
```
❌ Problem: User entries reject हो रही हैं

✅ Solution:
1. RULES tab में format check करो
2. Market timing check करो
3. Entry format message भेजो user को
4. Logs में error देखो
```

---

## 📊 Tips & Best Practices

### ✅ DO:
- नियमित रूप से backup लो
- Settings को test करो छोटे market से
- Change log maintain करो
- Auto-scrape को हमेशा on रखो
- Risk limits properly set करो

### ❌ DON'T:
- Production में experiment मत करो
- Risk limits को बहुत high मत set करो
- Payouts को randomly change मत करो
- Firebase URL को share मत करो
- Backup files को delete मत करो

---

## 📞 Support

```
❓ समस्या आ रही है?

1. Check करो: Documentation page
2. Message करो: Admin WhatsApp group
3. Call करो: Support team
4. Email करो: support@titannova.com

🕐 Support Hours: 9 AM - 11 PM IST
📅 Days: All days except Sunday
```

---

## 🎓 Video Tutorials

*निम्नलिखित video tutorials YouTube channel पर उपलब्ध हैं:*

```
1. Setup Center का Introduction (5 min)
2. Market कैसे add करें (3 min)
3. Risk limits कैसे set करें (4 min)
4. Auto-scraper कैसे configure करें (5 min)
5. Backup & Restore (3 min)
6. Troubleshooting guide (6 min)
```

**Link:** https://www.youtube.com/channel/titannova

---

## 📋 Quick Reference Card

```
KEYBOARD SHORTCUTS:
S → Setup tab खोलो
M → Market tab
V → Visible tab
C → Config tab
Ctrl+S → Save settings
Ctrl+B → Backup लो
```

---

**Last Updated:** 2024-01-15  
**Version:** 2.0  
**Language:** Hindi + English
