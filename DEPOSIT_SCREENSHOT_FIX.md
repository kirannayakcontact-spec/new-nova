# Deposit Screenshot Flow Fix

## Problem
Current `Gateway.js` receives WhatsApp messages but only runs spam guard and entry parser. Payment screenshot images/captions are not routed into a deposit payment handler, so screenshots can be ignored.

## What this patch script adds
Run:

```bash
node scripts/upgrade-deposit-screenshot-flow.js
node --check Gateway.js
```

The script patches `Gateway.js` to:

- import Baileys `downloadContentFromMessage` for screenshot download
- detect WhatsApp image/caption payment proof messages
- optionally OCR screenshots when `OCR_SPACE_API_KEY` is set
- parse amount, UTR/RRN, transaction ID, paid-to UPI/name
- create a pending `payments[]` record in Firebase
- avoid duplicate submissions by message key, UTR, or transaction ID
- reply to the user with pending/admin-review status

## How to test in Termux

```bash
cd ~/titan-app
node scripts/upgrade-deposit-screenshot-flow.js
node --check Gateway.js
node Gateway.js
```

Then send one WhatsApp image screenshot with caption like:

```text
paid 500 UTR 123456789012
```

Expected result:

- Bot replies: `Payment screenshot received... Pending admin approval`
- Firebase `payments` gets a new record with `source: whatsapp_screenshot`
- Admin panel payments list should show the pending payment

## Optional OCR
Without OCR key, caption text still works. For automatic screenshot text extraction, set:

```bash
export OCR_SPACE_API_KEY="your_key_here"
```

Keep admin approval ON. This flow only records payment proof as pending; it does not auto-credit wallet without admin approval.
