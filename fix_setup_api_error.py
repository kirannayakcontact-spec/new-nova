#!/usr/bin/env python3
from pathlib import Path
import sys

P = Path('flask_app.py')
FIXES = [
    (
        "'firebaseUrlStatus':'READY' if FIREBASE_URL else 'SETUP'",
        "'firebaseUrlStatus':'READY' if FIREBASE_DB_URL else 'SETUP'",
        'Fix undefined FIREBASE_URL in /api/setup/load and /api/setup/status'
    ),
    (
        '"firebaseUrlStatus":"READY" if FIREBASE_URL else "SETUP"',
        '"firebaseUrlStatus":"READY" if FIREBASE_DB_URL else "SETUP"',
        'Fix undefined FIREBASE_URL double-quote variant'
    ),
]

def main():
    if not P.exists():
        print('ERROR: flask_app.py not found. Run this inside ~/titan-app.', file=sys.stderr)
        return 1
    s = P.read_text(encoding='utf-8')
    original = s
    applied = []
    for old, new, label in FIXES:
        if old in s:
            s = s.replace(old, new)
            applied.append(label)
    if s != original:
        bak = P.with_name('flask_app.py.bak_api_fix')
        if not bak.exists():
            bak.write_text(original, encoding='utf-8')
        P.write_text(s, encoding='utf-8')
        print('OK: Setup API error fixed.')
        for item in applied:
            print('-', item)
        print('Backup:', bak)
    else:
        print('OK: No API replacement needed. File already fixed or pattern not present.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
