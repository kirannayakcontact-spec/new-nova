# 💳 Payment System - Deposit & Withdrawal Flow

**Complete Guide for Admin & Users**

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PAYMENT SYSTEM                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  USER SUBMITS DEPOSIT/WITHDRAWAL                             │
│           ↓                                                   │
│  ┌──────────────────────────────────────────┐                │
│  │ VALIDATION LAYER                         │                │
│  │ - Amount check                           │                │
│  │ - Balance check (for withdrawal)         │                │
│  │ - Duplicate detection                    │                │
│  │ - UTR/UPI format validation              │                │
│  └──────────────────────────────────────────┘                │
│           ↓                                                   │
│  FIREBASE STORE (Pending Queue)                              │
│           ↓                                                   │
│  ┌──────────────────────────────────────────┐                │
│  │ ADMIN DASHBOARD                          │                │
│  │ - Review pending requests                │                │
│  │ - Approve/Reject with reason             │                │
│  │ - Add transaction notes                  │                │
│  └──────────────────────────────────────────┘                │
│           ↓                                                   │
│  UPDATE WALLET (Firebase)                                    │
│           ↓                                                   │
│  SEND CONFIRMATION (WhatsApp)                                │
│           ↓                                                   │
│  AUDIT LOG                                                   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 User Flows

### 1️⃣ DEPOSIT FLOW (Paise Aane ka Process)

```
USER SIDE:
┌────────────────────────────────────────────────────────┐
│ Step 1: Choose Payment Method                          │
│ - UPI: 9876543210@upi                                 │
│ - Bank: Account details (admin provides)              │
│ - Manual: Contact admin                               │
└────────────────────────────────────────────────────────┘
           ↓
┌────────────────────────────────────────────────────────┐
│ Step 2: Send Money                                     │
│ - Amount: ₹500 - ₹50,000                              │
│ - UTR/Reference: 405070123456                         │
│ - Wait for confirmation                               │
└────────────────────────────────────────────────────────┘
           ↓
┌────────────────────────────────────────────────────────┐
│ Step 3: Submit via App                                 │
│ POST /api/submit/payment                              │
│ {                                                      │
│   "userId": "client_9876543210",                      │
│   "amount": 500,                                       │
│   "utr": "405070123456",                              │
│   "method": "upi"                                      │
│ }                                                      │
└────────────────────────────────────────────────────────┘
           ↓
┌────────────────────────────────────────────────────────┐
│ Step 4: Wait for Admin Approval                        │
│ Status: PENDING                                        │
│ (Admin ke paas 24 hours approval time)               │
└────────────────────────────────────────────────────────┘
           ↓
┌────────────────────────────────────────────────────────┐
│ Step 5: Receive Confirmation                           │
│ ✅ Wallet credited                                     │
│ 📱 WhatsApp notification sent                          │
│ 📊 Ledger entry created                               │
└────────────────────────────────────────────────────────┘

ADMIN SIDE:
┌────────────────────────────────────────────────────────┐
│ Admin Dashboard → Payments Tab                         │
│ - See all pending deposits                             │
│ - Verify payment received (check bank)                │
│ - Click "Approve" or "Reject"                         │
│ - Add comment if needed                               │
└────────────────────────────────────────────────────────┘
```

---

### 2️⃣ WITHDRAWAL FLOW (Paise Nikalne ka Process)

```
USER SIDE:
┌────────────────────────────────────────────────────────┐
│ Step 1: Check Wallet Balance                           │
│ Available: ₹5,000 + ₹10,000 (credit) = ₹15,000       │
│ Minimum withdrawal: ₹100                               │
└────────────────────────────────────────────────────────┘
           ↓
┌────────────────────────────────────────────────────────┐
│ Step 2: Submit Withdrawal Request                      │
│ POST /api/submit/withdrawal                            │
│ {                                                      │
│   "userId": "client_9876543210",                      │
│   "amount": 2000,                                      │
│   "upiId": "user@upi",                                │
│   "method": "upi"                                      │
│ }                                                      │
└────────────────────────────────────────────────────────┘
           ↓
┌────────────────────────────────────────────────────────┐
│ Step 3: Validation                                     │
│ ✅ Balance sufficient?                                │
│ ✅ No pending withdrawals?                            │
│ ✅ Cooldown period (1 hour)?                          │
│ ✅ Kyc complete?                                      │
└────────────────────────────────────────────────────────┘
           ↓
┌────────────────────────────────────────────────────────┐
│ Step 4: Wait for Admin Processing                      │
│ Status: PENDING_REVIEW                                 │
│ (Process within 4 hours during business hours)        │
└────────────────────────────────────────────────────────┘
           ↓
┌────────────────────────────────────────────────────────┐
│ Step 5: Money Transferred                              │
│ ✅ Paise UPI/Bank account me                          │
│ 📱 WhatsApp confirmation                               │
│ ⏰ Usually 30 mins - 2 hours                          │
└────────────────────────────────────────────────────────┘

ADMIN SIDE:
┌────────────────────────────────────────────────────────┐
│ Admin Dashboard → Withdrawals Tab                      │
│ - Pending requests list                                │
│ - Verify UPI/Bank details                             │
│ - Process via payment gateway                         │
│ - Mark "Approved" when transferred                    │
│ - Send receipt to user                                │
└────────────────────────────────────────────────────────┘
```

---

## 📱 API Endpoints

### Deposit APIs

#### POST `/api/submit/payment`
**User submits deposit request**

```python
# Request
{
  "userId": "client_9876543210",
  "amount": 500,
  "utr": "405070123456",
  "method": "upi",  # upi, bank, manual
  "referenceNo": "405070123456"
}

# Response (Success)
{
  "status": "success",
  "paymentId": "PAY-2024-001",
  "message": "Payment submitted. Awaiting admin approval.",
  "createdAt": "2024-01-15T10:00:00Z"
}

# Response (Error)
{
  "status": "error",
  "message": "Minimum deposit amount is ₹100",
  "code": "AMOUNT_ERROR"
}
```

---

#### GET `/api/payments?status=pending`
**Admin fetch pending deposits**

```python
# Response
{
  "payments": [
    {
      "id": "PAY-2024-001",
      "userId": "client_9876543210",
      "userName": "Rajesh Kumar",
      "amount": 500,
      "utr": "405070123456",
      "method": "upi",
      "status": "pending",
      "createdAt": "2024-01-15T10:00:00Z",
      "submittedBy": "WhatsApp: 919876543210"
    },
    {
      "id": "PAY-2024-002",
      "userId": "client_8765432109",
      "userName": "Priya Singh",
      "amount": 1000,
      "status": "pending",
      "createdAt": "2024-01-15T10:30:00Z"
    }
  ],
  "totalPending": 1500,
  "count": 2
}
```

---

#### POST `/api/approve/payment`
**Admin approves deposit**

```python
# Request
{
  "paymentId": "PAY-2024-001",
  "approvedBy": "admin_user",
  "remark": "Verified in bank account"
}

# Response
{
  "status": "success",
  "message": "Payment approved",
  "wallet": {
    "userId": "client_9876543210",
    "balanceBefore": 5000,
    "balanceAfter": 5500,
    "creditedAmount": 500
  },
  "notification": {
    "sent": true,
    "method": "whatsapp",
    "message": "✅ ₹500 credited to your wallet"
  }
}
```

---

#### POST `/api/reject/payment`
**Admin rejects deposit**

```python
# Request
{
  "paymentId": "PAY-2024-001",
  "reason": "UTR not found in bank",
  "returnUtr": "405070123456"
}

# Response
{
  "status": "success",
  "message": "Payment rejected",
  "notification": {
    "sent": true,
    "method": "whatsapp",
    "message": "❌ Payment rejected: UTR not found. Please resubmit with correct details."
  }
}
```

---

### Withdrawal APIs

#### POST `/api/submit/withdrawal`
**User requests withdrawal**

```python
# Request
{
  "userId": "client_9876543210",
  "amount": 2000,
  "upiId": "user@upi",
  "method": "upi"  # upi, bank
}

# Response (Success)
{
  "status": "success",
  "withdrawalId": "WID-2024-001",
  "message": "Withdrawal request submitted",
  "estimatedTime": "4 hours",
  "wallet": {
    "balanceBefore": 5000,
    "balanceAfter": 3000,
    "creditLimit": 10000,
    "available": 13000
  }
}

# Response (Error - Insufficient Balance)
{
  "status": "error",
  "message": "Insufficient balance",
  "available": 3000,
  "requested": 5000,
  "code": "INSUFFICIENT_BALANCE"
}

# Response (Error - Cooldown)
{
  "status": "error",
  "message": "Please wait before next withdrawal",
  "nextWithdrawalAt": "2024-01-15T11:00:00Z",
  "code": "COOLDOWN_ACTIVE"
}
```

---

#### GET `/api/withdrawals?status=pending`
**Admin fetch pending withdrawals**

```python
# Response
{
  "withdrawals": [
    {
      "id": "WID-2024-001",
      "userId": "client_9876543210",
      "userName": "Rajesh Kumar",
      "amount": 2000,
      "upiId": "user@upi",
      "status": "pending_review",
      "createdAt": "2024-01-15T10:00:00Z",
      "requestedAt": "2024-01-15T10:00:00Z",
      "kyc": {
        "verified": true,
        "verifiedAt": "2024-01-10T15:30:00Z"
      }
    }
  ],
  "totalPending": 2000,
  "count": 1
}
```

---

#### POST `/api/approve/withdrawal`
**Admin approves withdrawal**

```python
# Request
{
  "withdrawalId": "WID-2024-001",
  "approvedBy": "admin_user",
  "transactionId": "TXN-2024-001"
}

# Response
{
  "status": "success",
  "message": "Withdrawal approved and processed",
  "withdrawal": {
    "id": "WID-2024-001",
    "status": "approved",
    "approvedAt": "2024-01-15T10:15:00Z"
  },
  "notification": {
    "sent": true,
    "message": "✅ ₹2000 transferred to your UPI. Will arrive in 30 mins."
  }
}
```

---

#### POST `/api/reject/withdrawal`
**Admin rejects withdrawal**

```python
# Request
{
  "withdrawalId": "WID-2024-001",
  "reason": "Invalid UPI ID",
  "returnAmount": true
}

# Response
{
  "status": "success",
  "message": "Withdrawal rejected",
  "wallet": {
    "balanceBefore": 3000,
    "balanceAfter": 5000,
    "refundedAmount": 2000
  },
  "notification": {
    "sent": true,
    "message": "❌ Withdrawal rejected: Invalid UPI. Amount refunded to wallet."
  }
}
```

---

## 💾 Database Schema

```json
{
  "wallets": {
    "client_9876543210": {
      "userId": "client_9876543210",
      "name": "Rajesh Kumar",
      "phone": "9876543210",
      "balance": 5000,
      "creditLimit": 10000,
      "kyc": {
        "verified": true,
        "verifiedAt": "2024-01-10T15:30:00Z"
      },
      "ledger": [
        {
          "id": "PAY-2024-001",
          "type": "deposit",
          "amount": 500,
          "method": "upi",
          "utr": "405070123456",
          "status": "approved",
          "createdAt": "2024-01-15T10:00:00Z",
          "approvedAt": "2024-01-15T10:15:00Z",
          "approvedBy": "admin",
          "balanceBefore": 4500,
          "balanceAfter": 5000,
          "remark": "Verified in bank"
        },
        {
          "id": "WID-2024-001",
          "type": "withdrawal",
          "amount": 2000,
          "method": "upi",
          "upiId": "user@upi",
          "status": "pending_process",
          "createdAt": "2024-01-15T10:30:00Z",
          "approvedAt": "2024-01-15T10:40:00Z",
          "approvedBy": "admin",
          "balanceBefore": 5000,
          "balanceAfter": 3000,
          "transactionId": "TXN-2024-001",
          "processedAt": "2024-01-15T11:00:00Z"
        }
      ],
      "createdAt": "2024-01-01T00:00:00Z",
      "updatedAt": "2024-01-15T11:00:00Z"
    }
  },
  
  "paymentSettings": {
    "depositsEnabled": true,
    "withdrawalsEnabled": true,
    "minDeposit": 100,
    "maxDeposit": 50000,
    "minWithdrawal": 100,
    "maxWithdrawal": 30000,
    "withdrawalCooldownMinutes": 60,
    "autoApproveDeposit": false,
    "defaultCreditLimit": 10000,
    "notifyUserPrivate": true,
    "notifyAdminGroup": "123456@g.us"
  }
}
```

---

## ⚠️ Validation Rules

### Deposit Validation
```
✅ Amount between ₹100 - ₹50,000
✅ UTR format: Valid reference number (8-20 chars)
✅ Not duplicate of recent UTR (24 hour check)
✅ User KYC verified OR new user allowed
✅ Payment method enabled
✅ No pending payment for same user (optional)
```

### Withdrawal Validation
```
✅ Amount between ₹100 - ₹30,000
✅ Balance sufficient (actual + credit)
✅ Cooldown period met (1 hour between requests)
✅ UPI/Bank details valid
✅ User KYC verified
✅ Account not restricted
✅ No pending withdrawals (optional)
```

---

## 🔐 Risk Management

| Risk | Mitigation |
|------|------------|
| Duplicate deposits | Check UTR + phone in last 24h |
| Fraud withdrawals | KYC verification required |
| Fake UTR | Admin manual verification |
| Balance tampering | Audit log + Firebase validation |
| Chargeback | Keep transaction records 180 days |

---

## 📊 Admin Dashboard Features

```
DEPOSITS TAB:
┌─────────────────────────────────┐
│ Today: ₹ 15,500                 │
│ Pending: 3 requests             │
│ Approved: 8                      │
│ Rejected: 1                      │
└─────────────────────────────────┘

Table:
│ User      │ Amount  │ Method │ UTR  │ Status   │ Action     │
├───────────┼─────────┼────────┼──────┼──────────┼────────────┤
│ Rajesh    │ ₹500    │ UPI    │ xxx  │ Pending  │ ✅ Reject ❌│
│ Priya     │ ₹1000   │ Bank   │ yyy  │ Pending  │ ✅ Reject ❌│

WITHDRAWALS TAB:
Table:
│ User      │ Amount  │ UPI ID      │ Status    │ Action     │
├───────────┼─────────┼─────────────┼───────────┼────────────┤
│ Rajesh    │ ₹2000   │ raj@upi     │ Pending   │ ✅ Reject ❌│
│ Priya     │ ₹1500   │ priya@bank  │ Processing│ View TXN   │
```

---

## 📢 Notifications

### Deposit Approved
```
✅ *PAYMENT APPROVED*
━━━━━━━━━━━━━━━━━━━
Amount: ₹500
Wallet Balance: ₹5,000
Available: ₹15,000
Credited at: 2024-01-15 10:15 AM
━━━━━━━━━━━━━━━━━━━

Ready to play! 🎮
```

### Withdrawal Approved
```
✅ *WITHDRAWAL APPROVED*
━━━━━━━━━━━━━━━━━━━
Amount: ₹2,000
UPI: user@upi
TXN ID: TXN-2024-001
Status: Processing
Estimated: 30 mins
━━━━━━━━━━━━━━━━━━━

Check your UPI app 📱
```

### Payment Rejected
```
❌ *PAYMENT REJECTED*
━━━━━━━━━━━━━━━━━━━
Reason: UTR not found
Amount: ₹500
Next Steps: Resubmit with correct UTR
━━━━━━━━━━━━━━━━━━━

Contact admin if issue persists 📞
```

---

## 🐛 Error Codes

| Code | Message | Fix |
|------|---------|-----|
| AMOUNT_ERROR | Invalid amount | Use ₹100 - ₹50,000 |
| INSUFFICIENT_BALANCE | Not enough balance | Deposit more or reduce amount |
| UTR_DUPLICATE | UTR already used | Use different UTR |
| KYC_REQUIRED | KYC not verified | Complete KYC first |
| COOLDOWN_ACTIVE | Too soon to withdraw | Wait 1 hour |
| INVALID_UPI | UPI format error | Check UPI ID format |
| DB_ERROR | Firebase error | Try again in 5 mins |

---

## 📈 Audit Trail

Every transaction logged:
```
action: "payment_approved"
user_id: "client_9876543210"
detail: {
  "payment_id": "PAY-2024-001",
  "amount": 500,
  "status": "approved",
  "approved_by": "admin"
}
timestamp: "2024-01-15T10:15:00Z"
```

Access via: `logs/flask_app-audit.log`

---

## 🚀 Upcoming Features

- [ ] Automatic payment confirmation (Bank API integration)
- [ ] Recurring deposits/subscriptions
- [ ] Payment plans (EMI-like)
- [ ] Cashback rewards
- [ ] Referral bonus payouts
