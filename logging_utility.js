/**
 * Comprehensive Logging Utility for Gateway.js
 * Provides structured logging, error tracking, and audit trail for Node.js
 */

const fs = require('fs');
const path = require('path');
const { EventEmitter } = require('events');

class LogLevel {
  static DEBUG = 'DEBUG';
  static INFO = 'INFO';
  static WARNING = 'WARNING';
  static ERROR = 'ERROR';
  static CRITICAL = 'CRITICAL';
}

class TitanLogger extends EventEmitter {
  constructor(name = 'gateway') {
    super();
    this.name = name;
    this.logDir = path.join(process.cwd(), process.env.LOG_DIR || './logs');
    this.maxLogSize = 10 * 1024 * 1024; // 10MB
    this.logFile = path.join(this.logDir, `${name}.log`);
    this.errorLogFile = path.join(this.logDir, `${name}-errors.log`);
    this.auditLogFile = path.join(this.logDir, `${name}-audit.log`);
    
    this._ensureLogDir();
  }

  _ensureLogDir() {
    if (!fs.existsSync(this.logDir)) {
      fs.mkdirSync(this.logDir, { recursive: true });
    }
  }

  _getTimestamp() {
    return new Date().toISOString();
  }

  _formatLogEntry(level, message, context = null, error = null) {
    const entry = {
      timestamp: this._getTimestamp(),
      level,
      message,
      app: this.name,
      pid: process.pid
    };

    if (context) {
      entry.context = context;
    }

    if (error) {
      entry.error = {
        type: error.constructor.name,
        message: error.message,
        stack: error.stack
      };
    }

    return JSON.stringify(entry);
  }

  _checkLogRotation(logFile) {
    try {
      if (fs.existsSync(logFile)) {
        const stats = fs.statSync(logFile);
        if (stats.size > this.maxLogSize) {
          const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
          const backup = `${logFile}.${timestamp}`;
          fs.renameSync(logFile, backup);
          console.log(`📋 Log rotated: ${backup}`);
        }
      }
    } catch (e) {
      console.error('Log rotation failed:', e.message);
    }
  }

  _writeLog(logFile, entry) {
    try {
      this._checkLogRotation(logFile);
      fs.appendFileSync(logFile, entry + '\n', 'utf8');
    } catch (e) {
      console.error(`❌ Log write failed to ${logFile}:`, e.message);
    }
  }

  debug(message, context = null) {
    const entry = this._formatLogEntry(LogLevel.DEBUG, message, context);
    this._writeLog(this.logFile, entry);
    if (process.env.DEBUG === '1') {
      console.log(`🔍 [DEBUG] ${message}`, context || '');
    }
  }

  info(message, context = null) {
    const entry = this._formatLogEntry(LogLevel.INFO, message, context);
    this._writeLog(this.logFile, entry);
    console.log(`ℹ️  [INFO] ${message}`, context || '');
  }

  warning(message, context = null) {
    const entry = this._formatLogEntry(LogLevel.WARNING, message, context);
    this._writeLog(this.logFile, entry);
    console.log(`⚠️  [WARN] ${message}`, context || '');
  }

  error(message, errorObj = null, context = null) {
    const entry = this._formatLogEntry(LogLevel.ERROR, message, context, errorObj);
    this._writeLog(this.logFile, entry);
    this._writeLog(this.errorLogFile, entry);
    console.error(`❌ [ERROR] ${message}`);
    if (errorObj) {
      console.error(`   ${errorObj.constructor.name}: ${errorObj.message}`);
    }
    this.emit('error', { message, error: errorObj, context });
  }

  critical(message, errorObj = null, context = null) {
    const entry = this._formatLogEntry(LogLevel.CRITICAL, message, context, errorObj);
    this._writeLog(this.logFile, entry);
    this._writeLog(this.errorLogFile, entry);
    console.error(`🚨 [CRITICAL] ${message}`);
    this.emit('critical', { message, error: errorObj, context });
  }

  audit(action, userId = null, detail = null, status = 'success') {
    const entry = {
      timestamp: this._getTimestamp(),
      action,
      user_id: userId,
      status,
      detail,
      app: this.name,
      pid: process.pid
    };

    try {
      this._checkLogRotation(this.auditLogFile);
      fs.appendFileSync(this.auditLogFile, JSON.stringify(entry) + '\n', 'utf8');
    } catch (e) {
      this.error('Audit log write failed', e);
    }
  }

  logWhatsAppEvent(eventType, detail = null) {
    const context = {
      event: eventType,
      ...detail
    };
    this.info(`WhatsApp: ${eventType}`, context);
    this.audit(`whatsapp_${eventType}`, null, detail);
  }

  logApiCall(endpoint, method, statusCode, durationMs, userId = null, error = null) {
    const context = {
      endpoint,
      method,
      status_code: statusCode,
      duration_ms: durationMs,
      user_id: userId
    };

    if (statusCode >= 500) {
      this.error(`API ${method} ${endpoint} failed with ${statusCode}`, error, context);
    } else if (statusCode >= 400) {
      this.warning(`API ${method} ${endpoint} returned ${statusCode}`, context);
    } else {
      if (durationMs > 1000) {
        this.warning(`API ${method} ${endpoint} slow: ${durationMs}ms`, context);
      } else {
        this.debug(`API ${method} ${endpoint} ${statusCode}`, context);
      }
    }
  }

  logFirebaseOperation(operation, durationMs, success, error = null) {
    const context = {
      operation,
      duration_ms: durationMs,
      success
    };

    if (!success) {
      this.error(`Firebase ${operation} failed`, error, context);
    } else if (durationMs > 5000) {
      this.warning(`Firebase ${operation} slow: ${durationMs}ms`, context);
    } else {
      this.debug(`Firebase ${operation} OK in ${durationMs}ms`, context);
    }
  }

  logMessageProcessing(messageId, chatJid, type, success, detail = null) {
    const context = {
      message_id: messageId,
      chat_jid: chatJid,
      type,
      ...detail
    };

    if (!success) {
      this.error(`Message processing failed: ${type}`, null, context);
    } else {
      this.debug(`Message processed: ${type}`, context);
    }
    this.audit(`message_${type}`, null, detail, success ? 'success' : 'failed');
  }

  logEntryAccepted(entryId, userId, market, gameType, total) {
    const detail = { entry_id: entryId, user_id: userId, market, game_type: gameType, total };
    this.info(`✅ Entry accepted: ${entryId}`, detail);
    this.audit('entry_accepted', userId, detail);
  }

  logResultSettlement(date, market, stage, result, hitCount, missCount, marketProfit) {
    const detail = {
      date,
      market,
      stage,
      result,
      hit_count: hitCount,
      miss_count: missCount,
      market_profit: marketProfit
    };
    this.info(`🏆 Settlement: ${market} ${stage} ${result}`, detail);
    this.audit('result_settlement', null, detail);
  }

  logSpamGuardAction(chatJid, senderJid, kind, action, count) {
    const detail = {
      chat_jid: chatJid,
      sender_jid: senderJid,
      kind,
      action,
      count
    };
    this.info(`🛡️ SpamGuard ${action}: ${kind} (${count})`, detail);
    this.audit(`spamguard_${action}`, senderJid, detail);
  }

  getRecentErrors(limit = 10) {
    try {
      const data = fs.readFileSync(this.errorLogFile, 'utf8');
      const lines = data.split('\n').filter(Boolean);
      return lines.slice(-limit).map(line => {
        try {
          return JSON.parse(line);
        } catch {
          return { raw: line };
        }
      });
    } catch (e) {
      this.error('Failed to read error log', e);
      return [];
    }
  }

  getAuditTrail(limit = 50, action = null, userId = null) {
    try {
      const data = fs.readFileSync(this.auditLogFile, 'utf8');
      let entries = data.split('\n').filter(Boolean).map(line => {
        try {
          return JSON.parse(line);
        } catch {
          return null;
        }
      }).filter(Boolean);

      if (action) {
        entries = entries.filter(e => e.action === action);
      }
      if (userId) {
        entries = entries.filter(e => e.user_id === userId);
      }

      return entries.slice(-limit);
    } catch (e) {
      this.error('Failed to read audit log', e);
      return [];
    }
  }

  getHealthStatus() {
    return {
      app: this.name,
      timestamp: this._getTimestamp(),
      logFiles: {
        main: fs.existsSync(this.logFile),
        errors: fs.existsSync(this.errorLogFile),
        audit: fs.existsSync(this.auditLogFile)
      },
      logSizes: {
        main: fs.existsSync(this.logFile) ? fs.statSync(this.logFile).size : 0,
        errors: fs.existsSync(this.errorLogFile) ? fs.statSync(this.errorLogFile).size : 0,
        audit: fs.existsSync(this.auditLogFile) ? fs.statSync(this.auditLogFile).size : 0
      }
    };
  }
}

// Global logger instance
const logger = new TitanLogger('gateway');

module.exports = { logger, LogLevel, TitanLogger };

// Usage examples (add to Gateway.js):
/*
const { logger } = require('./logging_utility');

// In WhatsApp connection handler:
sock.ev.on('connection.update', (update) => {
  const { connection, qr } = update;
  if (qr) {
    logger.logWhatsAppEvent('qr_generated', { qr_length: qr.length });
  }
  if (connection === 'open') {
    logger.logWhatsAppEvent('connected');
  }
});

// In entry processing:
const startTime = Date.now();
try {
  const saved = await saveAcceptedEntryToFirebase(parsed, meta);
  if (saved.ok) {
    const duration = Date.now() - startTime;
    logger.logEntryAccepted(saved.entry.id, saved.entry.userId, 
      saved.entry.market, saved.entry.gameType, saved.entry.total);
  }
} catch (e) {
  logger.error('Entry save failed', e, { market: parsed.market });
}

// In API handlers:
app.get('/api/status', async (req, res) => {
  const startTime = Date.now();
  try {
    const state = await fetchFirebaseState();
    const duration = Date.now() - startTime;
    logger.logApiCall('/api/status', 'GET', 200, duration);
    res.json({ status: 'success' });
  } catch (e) {
    const duration = Date.now() - startTime;
    logger.logApiCall('/api/status', 'GET', 500, duration, null, e);
    res.status(500).json({ error: e.message });
  }
});

// In Firebase operations:
const fbStartTime = Date.now();
try {
  const state = await fetchFirebaseState();
  const duration = Date.now() - fbStartTime;
  logger.logFirebaseOperation('fetch_state', duration, true);
} catch (e) {
  const duration = Date.now() - fbStartTime;
  logger.logFirebaseOperation('fetch_state', duration, false, e);
}

// For spam guard:
logger.logSpamGuardAction(chatJid, senderJid, 'link', 'warning', record.count);

// Get health status:
app.get('/logger/health', (req, res) => {
  res.json(logger.getHealthStatus());
});
*/
