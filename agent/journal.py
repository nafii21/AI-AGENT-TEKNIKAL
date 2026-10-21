import sqlite3, os

DB_FILE = "journal.db"

def init_db():
    # Jika file journal.db kosong/belum ada, SQLite akan otomatis bikin tabel
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS journal
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  symbol TEXT, action TEXT, entry REAL, sl REAL, tp REAL, result TEXT, notes TEXT)''')
    conn.commit()
    return conn

def add_journal(symbol, action, entry, sl, tp, result, notes):
    conn = init_db()
    c = conn.cursor()
    c.execute("INSERT INTO journal (symbol, action, entry, sl, tp, result, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (symbol, action, entry, sl, tp, result, notes))
    conn.commit()
    conn.close()

def get_journals(limit=5):
    conn = init_db()
    c = conn.cursor()
    c.execute("SELECT timestamp, symbol, action, entry, sl, tp, result, notes FROM journal ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows
