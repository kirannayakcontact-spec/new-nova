"""
Comprehensive Error Logging Utility for Titan Nova
Provides structured logging, error tracking, and audit trail
"""

import json
import os
from datetime import datetime
from pathlib import Path
from enum import Enum
import traceback
import sys

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class TitanLogger:
    """Central logging system for flask_app.py"""
    
    LOG_DIR = Path(os.environ.get("LOG_DIR", "./logs"))
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_RETENTION_DAYS = 30
    
    def __init__(self, name="titan-nova"):
        self.name = name
        self.log_dir = self.LOG_DIR
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / f"{name}.log"
        self.error_log_file = self.log_dir / f"{name}-errors.log"
        self.audit_log_file = self.log_dir / f"{name}-audit.log"
    
    def _get_timestamp(self):
        """Get ISO format timestamp"""
        return datetime.utcnow().isoformat() + "Z"
    
    def _format_log_entry(self, level, message, context=None, error=None):
        """Format structured log entry"""
        entry = {
            "timestamp": self._get_timestamp(),
            "level": level.value,
            "message": message,
            "app": self.name
        }
        
        if context:
            entry["context"] = context
        
        if error:
            entry["error"] = {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc()
            }
        
        return json.dumps(entry)
    
    def _check_log_rotation(self, log_file):
        """Rotate log if size exceeds limit"""
        if log_file.exists() and log_file.stat().st_size > self.MAX_LOG_SIZE:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup = log_file.parent / f"{log_file.stem}_{timestamp}.log"
            log_file.rename(backup)
            print(f"📋 Log rotated: {backup}")
    
    def _write_log(self, log_file, entry):
        """Write log entry to file"""
        try:
            self._check_log_rotation(log_file)
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(entry + "\n")
        except Exception as e:
            print(f"❌ Log write failed: {e}", file=sys.stderr)
    
    def debug(self, message, context=None):
        """Debug level logging"""
        entry = self._format_log_entry(LogLevel.DEBUG, message, context)
        self._write_log(self.log_file, entry)
        if os.environ.get("DEBUG") == "1":
            print(f"🔍 {message}", flush=True)
    
    def info(self, message, context=None):
        """Info level logging"""
        entry = self._format_log_entry(LogLevel.INFO, message, context)
        self._write_log(self.log_file, entry)
        print(f"ℹ️ {message}", flush=True)
    
    def warning(self, message, context=None):
        """Warning level logging"""
        entry = self._format_log_entry(LogLevel.WARNING, message, context)
        self._write_log(self.log_file, entry)
        print(f"⚠️ {message}", flush=True)
    
    def error(self, message, error=None, context=None):
        """Error level logging - always writes to errors.log"""
        entry = self._format_log_entry(LogLevel.ERROR, message, context, error)
        self._write_log(self.log_file, entry)
        self._write_log(self.error_log_file, entry)
        print(f"❌ {message}", flush=True)
        if error:
            print(f"   Exception: {type(error).__name__}: {error}", flush=True)
    
    def critical(self, message, error=None, context=None):
        """Critical level logging - alerts"""
        entry = self._format_log_entry(LogLevel.CRITICAL, message, context, error)
        self._write_log(self.log_file, entry)
        self._write_log(self.error_log_file, entry)
        print(f"🚨 CRITICAL: {message}", flush=True)
    
    def audit(self, action, user_id=None, detail=None, status="success"):
        """Audit trail logging for compliance"""
        entry = {
            "timestamp": self._get_timestamp(),
            "action": action,
            "user_id": user_id,
            "status": status,
            "detail": detail,
            "app": self.name
        }
        try:
            self._check_log_rotation(self.audit_log_file)
            with open(self.audit_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            self.error("Audit log write failed", e)
    
    def log_api_call(self, endpoint, method, status_code, duration_ms, user_id=None, error=None):
        """Log API calls with performance metrics"""
        context = {
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "user_id": user_id
        }
        
        if status_code >= 500:
            self.error(f"API {method} {endpoint} failed with {status_code}", error, context)
        elif status_code >= 400:
            self.warning(f"API {method} {endpoint} returned {status_code}", context)
        else:
            if duration_ms > 1000:
                self.warning(f"API {method} {endpoint} slow: {duration_ms}ms", context)
            else:
                self.debug(f"API {method} {endpoint} {status_code}", context)
    
    def log_firebase_operation(self, operation, duration_ms, success, error=None):
        """Log Firebase operations"""
        context = {
            "operation": operation,
            "duration_ms": duration_ms,
            "success": success
        }
        
        if not success:
            self.error(f"Firebase {operation} failed", error, context)
        elif duration_ms > 5000:
            self.warning(f"Firebase {operation} slow: {duration_ms}ms", context)
        else:
            self.debug(f"Firebase {operation} OK in {duration_ms}ms", context)
    
    def get_recent_errors(self, limit=10):
        """Retrieve recent errors from log"""
        try:
            with open(self.error_log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                return [json.loads(line) for line in lines[-limit:]]
        except Exception as e:
            self.error("Failed to read error log", e)
            return []
    
    def get_audit_trail(self, limit=50, action=None, user_id=None):
        """Retrieve audit trail"""
        try:
            with open(self.audit_log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                entries = [json.loads(line) for line in lines[-limit:]]
                
                if action:
                    entries = [e for e in entries if e.get("action") == action]
                if user_id:
                    entries = [e for e in entries if e.get("user_id") == user_id]
                
                return entries
        except Exception as e:
            self.error("Failed to read audit log", e)
            return []


# Global logger instance
logger = TitanLogger("flask_app")


# Usage examples (add to flask_app.py):
"""
from logging_utility import logger

# In API endpoints:
@app.route('/api/setup/load')
def api_setup_load():
    start_time = time.time()
    try:
        # Your code here
        duration = (time.time() - start_time) * 1000
        logger.log_api_call('/api/setup/load', 'GET', 200, duration)
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.log_api_call('/api/setup/load', 'GET', 500, duration, error=e)
        return jsonify({'error': str(e)}), 500

# For Firebase operations:
start = time.time()
try:
    result = load_from_firebase()
    duration = (time.time() - start) * 1000
    logger.log_firebase_operation('load_state', duration, True)
except Exception as e:
    duration = (time.time() - start) * 1000
    logger.log_firebase_operation('load_state', duration, False, e)

# For audit trails:
logger.audit('entry_accepted', user_id=uid, detail={'entry_id': entry.id}, status='success')

# For errors:
try:
    process_payment()
except ValueError as e:
    logger.error('Payment processing failed', e, {'user_id': uid, 'amount': amount})
"""
