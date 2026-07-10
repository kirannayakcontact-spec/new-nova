"use strict";

/**
 * Deposit screenshot flow patch for the 2-file Titan Nova runtime.
 *
 * Run from repo root:
 *   node scripts/upgrade-deposit-screenshot-flow.js
 *
 * Then run:
 *   node --check Gateway.js
 *   node Gateway.js
 */

const fs = require("fs");
const path = require("path");

const gatewayPath = path.join(process.cwd(), "Gateway.js");
if (!fs.existsSync(gatewayPath)) {
  console.error("Gateway.js not found. Run this script from the repo root.");
  process.exit(1);
}

let src = fs.readFileSync(gatewayPath, "utf8");
const original = src;

function replaceOnce(label, needle, replacement) {
  if (!src.includes(needle)) {
    console.error(`Patch failed: marker not found for ${label}`);
    process.exit(1);
  }
  src = src.replace(needle, replacement);
}

if (!src.includes("DEPOSIT_SCREENSHOT_FLOW_VERSION")) {
  replaceOnce(
    "Baileys image download import",
    `  DisconnectReason,\n  fetchLatestBaileysVersion,\n  Browsers\n} = require("@whiskeysockets/baileys");`,
    `  DisconnectReason,\n  fetchLatestBaileysVersion,\n  Browsers,\n  downloadContentFromMessage\n} = require("@whiskeysockets/baileys");`
  );

  const helperMarker = `function getMessageText(m){\n  const msg = m?.message || {};\n  return msg.conversation || msg.extendedTextMessage?.text || msg.imageMessage?.caption || msg.videoMessage?.caption || msg.documentMessage?.caption || "";\n}\n`;

  const helperBlock = `function getMessageText(m){\n  const msg = m?.message || {};\n  return msg.conversation || msg.extendedTextMessage?.text || msg.imageMessage?.caption || msg.videoMessage?.caption || msg.documentMessage?.caption || "";\n}\n\n// ============================================================\n// DEPOSIT PAYMENT SCREENSHOT FLOW — v2026-07-08\n// Handles WhatsApp payment screenshots safely as pending admin-review payments.\n// Optional OCR: set OCR_SPACE_API_KEY to parse screenshot text automatically.\n// ============================================================\nconst DEPOSIT_SCREENSHOT_FLOW_VERSION = "2026-07-08-deposit-screenshot-flow-v1";\n\nfunction depositNormalizeText(v){ return String(v || "").replace(/\\s+/g, " ").trim(); }\nfunction depositLooksLikePaymentProof(text, hasImage){\n  const t = depositNormalizeText(text);\n  if(!t && !hasImage) return false;\n  if(/^(?:hi|hello|hey|ok|okay|thanks?|thank you|test)$/i.test(t)) return false;\n  if(/\\b(?:payment|paid|deposit|deposited|recharge|add\\s*money|wallet|utr|rrn|txn|transaction|trans(?:action)?\\s*id|ref(?:erence)?|upi|screenshot|proof|success|successful|completed)\\b/i.test(t)) return true;\n  return !!hasImage && /(?:₹|rs\\.?|inr|amount|amt)\\s*[:#-]?\\s*[0-9]+(?:\\.[0-9]+)?/i.test(t);\n}\nfunction parseDepositPaymentProof(text, hasImage){\n  const raw = String(text || "").replace(/\\r/g, "\\n").trim();\n  const oneLine = depositNormalizeText(raw);\n  const amountMatch = oneLine.match(/(?:₹|rs\\.?|inr|amount|amt)\\s*[:#-]?\\s*([0-9]+(?:\\.[0-9]+)?)/i) || oneLine.match(/\\b(?:paid|payment|deposit|recharge|add\\s*money)\\s+([0-9]+(?:\\.[0-9]+)?)/i) || oneLine.match(/\\b([0-9]+(?:\\.[0-9]+)?)\\s*(?:rs|inr)\\b/i);\n  const utrMatch = oneLine.match(/\\b(?:utr|rrn)\\s*[:#-]?\\s*([A-Z0-9][A-Z0-9-]{5,35})\\b/i);\n  const txnMatch = oneLine.match(/\\b(?:txn|transaction(?:\\s*id)?|trans(?:action)?\\s*id|ref(?:erence)?)\\s*[:#-]?\\s*([A-Z0-9][A-Z0-9-]{5,35})\\b/i);\n  const upiMatch = oneLine.match(/\\b([a-z0-9._-]{2,}@[a-z][a-z0-9._-]{1,})\\b/i);\n  const paidToNameMatch = oneLine.match(/(?:paid\\s*to|receiver|beneficiary|credited\\s*to|to)\\s*[:#-]?\\s*([A-Za-z][A-Za-z0-9 .]{2,60})(?=\\s+(?:upi|utr|txn|transaction|₹|rs\\.?|inr|amount)\\b|$)/i);\n  const amount = amountMatch ? Math.round(Number(amountMatch[1] || 0) * 100) / 100 : 0;\n  const utr = utrMatch ? String(utrMatch[1]).replace(/[^A-Za-z0-9-]/g, "").toUpperCase() : "";\n  const transactionId = txnMatch ? String(txnMatch[1]).replace(/[^A-Za-z0-9-]/g, "").toUpperCase() : "";\n  const status = /\\b(?:success|successful|completed|paid)\\b/i.test(oneLine) ? "successful" : (/\\b(?:failed|failure|declined)\\b/i.test(oneLine) ? "failed" : "unknown");\n  const looksLikeProof = depositLooksLikePaymentProof(oneLine, hasImage) || !!utr || !!transactionId;\n  if(!looksLikeProof) return { ok:false, silent:true };\n  return { ok:true, amount:Number.isFinite(amount) ? amount : 0, utr, transactionId, paidToUpi:upiMatch ? upiMatch[1] : "", paidToName:paidToNameMatch ? paidToNameMatch[1].trim() : "", status, rawOcrText:raw };\n}\nasync function downloadPaymentScreenshotImageData(m){\n  try{\n    const image = m?.message?.imageMessage;\n    if(!image) return { data:"", buffer:null, note:"" };\n    const stream = await downloadContentFromMessage(image, "image");\n    const chunks = []; let total = 0;\n    for await (const chunk of stream){\n      const b = Buffer.from(chunk); total += b.length;\n      if(total > 1500000) return { data:"", buffer:null, note:"Screenshot received; image preview too large" };\n      chunks.push(b);\n    }\n    const buffer = Buffer.concat(chunks);\n    if(!buffer.length) return { data:"", buffer:null, note:"Screenshot received; preview unavailable" };\n    const mime = image.mimetype || "image/jpeg";\n    return { data:`data:${mime};base64,${buffer.toString("base64")}`, buffer, note:"" };\n  }catch(e){ console.log("Payment screenshot download failed:", e.message); return { data:"", buffer:null, note:"Screenshot received; preview unavailable" }; }\n}\nasync function ocrPaymentScreenshot(buffer){\n  const fallback = { text:"", confidence:0, provider:"none" };\n  if(!buffer?.length || !process.env.OCR_SPACE_API_KEY) return fallback;\n  try{\n    const body = new URLSearchParams({ apikey:process.env.OCR_SPACE_API_KEY, base64Image:`data:image/jpeg;base64,${buffer.toString("base64")}`, language:"eng", scale:"true", OCREngine:"2" }).toString();\n    const res = await axios.post("https://api.ocr.space/parse/image", body, { timeout:20000, headers:{"Content-Type":"application/x-www-form-urlencoded"} });\n    const parsed = (res.data?.ParsedResults || [])[0] || {};\n    return { text:String(parsed.ParsedText || ""), confidence: parsed.TextOverlay?.HasOverlay ? 0.8 : 0.6, provider:"ocr.space" };\n  }catch(e){ console.log("Payment OCR failed:", e.message); return fallback; }\n}\nfunction nextDepositPaymentId(state){\n  const n = Array.isArray(state?.payments) ? state.payments.length + 1 : 1;\n  return "P" + todayISO().replace(/-/g, "").slice(2) + "-" + String(n).padStart(4, "0");\n}\nfunction depositMessageKey(m, parsed){\n  return [m?.key?.remoteJid || "", m?.key?.participant || "", m?.key?.id || "", parsed?.utr || "", parsed?.transactionId || "", parsed?.amount || ""].join("|");\n}\nfunction duplicateDepositPayment(state, key, parsed){\n  for(const p of (Array.isArray(state?.payments) ? state.payments : [])){\n    if(key && p.messageKey === key) return p;\n    if(parsed?.utr && String(p.utr || "").toUpperCase() === String(parsed.utr).toUpperCase()) return p;\n    if(parsed?.transactionId && String(p.transactionId || "").toUpperCase() === String(parsed.transactionId).toUpperCase()) return p;\n  }\n  return null;\n}\nasync function saveDepositScreenshotPayment(parsed, meta, imageData, note){\n  const state = await fetchFirebaseState();\n  if(!Array.isArray(state.payments)) state.payments = [];\n  const found = findProfileBySender(state, meta.senderJid, meta);\n  if(!found) return { ok:false, reason:"profile_not_found", message:"Aapka profile linked nahi hai. Admin VIP phone number approve/link kare." };\n  const dup = duplicateDepositPayment(state, meta.messageKey, parsed);\n  if(dup) return { ok:false, reason:"duplicate", message:`⚠️ Ye payment proof already submitted hai. Payment ID: #${dup.id}` };\n  const amount = Number(parsed.amount || 0);\n  const paymentStatus = amount > 0 ? "pending_admin_approval" : "needs_amount";\n  const profile = found.profile || {};\n  const payment = { id:nextDepositPaymentId(state), date:todayISO(), createdAt:nowIso(), source:"whatsapp_screenshot", status:"pending", paymentStatus, userId:found.userId, userName:profile.name || found.userId, phone:profile.phone || found.matchedPhone || "", senderJid:meta.senderJid || "", chatJid:meta.chatJid || "", messageKey:meta.messageKey || "", amount:amount || 0, utr:parsed.utr || "", transactionId:parsed.transactionId || "", paidToName:parsed.paidToName || "", paidToUpi:parsed.paidToUpi || "", screenshotImageData:imageData || "", image:imageData || "", rawOcrText:parsed.rawOcrText || "", note:note || "", walletCredited:false, requestNotified:true, approvalNotified:false, rejectionNotified:false };\n  state.payments.push(payment);\n  if(!Array.isArray(state.auditLog)) state.auditLog = [];\n  state.auditLog.push({ id:payment.id, time:nowIso(), action:"whatsapp_deposit_screenshot_received", detail:{ userId:payment.userId, amount:payment.amount, utr:payment.utr, transactionId:payment.transactionId, paymentStatus } });\n  if(state.auditLog.length > 500) state.auditLog.splice(0, state.auditLog.length - 500);\n  await saveFirebaseState(state);\n  return { ok:true, payment };\n}\nasync function handleIncomingDepositScreenshotMessage(m){\n  try{\n    if(!m || m.key?.fromMe) return false;\n    const chatJid = m.key?.remoteJid || "";\n    if(!chatJid || chatJid === "status@broadcast") return false;\n    const hasImage = !!m?.message?.imageMessage;\n    const caption = getMessageText(m);\n    if(!hasImage && !depositLooksLikePaymentProof(caption, false)) return false;\n    const img = hasImage ? await downloadPaymentScreenshotImageData(m) : { data:"", buffer:null, note:"" };\n    const ocr = hasImage ? await ocrPaymentScreenshot(img.buffer) : { text:"", confidence:0, provider:"none" };\n    const combined = [caption, ocr.text].filter(Boolean).join("\\n");\n    if(!depositLooksLikePaymentProof(combined, hasImage)) return false;\n    const parsed = parseDepositPaymentProof(combined, hasImage);\n    if(parsed.silent) return false;\n    const senderCandidates = senderCandidatesFromMessage(m, chatJid);\n    const senderJid = chatJid.endsWith("@g.us") ? (senderCandidates[0] || m.key?.participant || "") : chatJid;\n    const messageKey = depositMessageKey(m, parsed);\n    const saved = await saveDepositScreenshotPayment(parsed, { chatJid, senderJid, senderCandidates, pushName:m.pushName || m.verifiedBizName || "", messageKey }, img.data, img.note || (ocr.provider !== "none" ? `OCR: ${ocr.provider}` : ""));\n    if(!saved.ok){ await replyToMessage(chatJid, saved.message || "Payment screenshot save nahi hua. Admin check kare.", m); return true; }\n    const p = saved.payment;\n    if(p.paymentStatus === "needs_amount") await replyToMessage(chatJid, "📷 Payment screenshot received, lekin amount clear nahi mila. Amount text me bhejo. Example: paid 500 UTR 123456", m);\n    else await replyToMessage(chatJid, `✅ Payment screenshot received.\\nAmount: ${money(p.amount)}\\nUTR: ${p.utr || "-"}\\nStatus: Pending admin approval.`, m);\n    console.log(`💳 Deposit screenshot ${p.id}: ${p.userId} ${p.amount} ${p.paymentStatus}`);\n    return true;\n  }catch(e){ console.log("Deposit screenshot flow error:", e.response ? `HTTP ${e.response.status}` : e.message); return false; }\n}\n`;

  replaceOnce("deposit helper insertion", helperMarker, helperBlock);

  replaceOnce(
    "message upsert deposit handler",
    `      const stopped = await handleSpamGuardMessage(m);\n      if(!stopped) await handleIncomingEntryMessage(m);`,
    `      const stopped = await handleSpamGuardMessage(m);\n      if(!stopped) {\n        const depositHandled = await handleIncomingDepositScreenshotMessage(m);\n        if(!depositHandled) await handleIncomingEntryMessage(m);\n      }`
  );
}

if (src === original) {
  console.log("Deposit screenshot flow patch already applied. No changes needed.");
  process.exit(0);
}

fs.writeFileSync(gatewayPath, src, "utf8");
console.log("Deposit screenshot flow patch applied to Gateway.js");
console.log("Next: node --check Gateway.js");
