import sqlite3, os
BASE = os.path.dirname(os.path.dirname(__file__))
path = os.path.join(BASE, 'db.sqlite3')
print('creating:', path)
# ensure directory exists
os.makedirs(os.path.dirname(path), exist_ok=True)
try:
    conn = sqlite3.connect(path)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.close()
    print('ok')
except Exception as e:
    print('error:', e)
