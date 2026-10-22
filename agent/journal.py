import json, os
from datetime import datetime

# Ganti dari .db ke .json biar anti-gagal di GitHub Actions
JOURNAL_FILE = "journal.json"

def load_journal():
    if not os.path.exists(JOURNAL_FILE): return []
    try:
        with open(JOURNAL_FILE, "r") as f:
            return json.load(f)
    except: return []

def save_journal(data):
    with open(JOURNAL_FILE, "w") as f:
        json.dump(data, f, indent=2)

def add_journal(symbol, action, entry, sl, tp, result, notes):
    data = load_journal()
    new_entry = {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "symbol": symbol,
        "action": action,
        "entry": entry,
        "sl": sl,
        "tp": tp,
        "result": result,
        "notes": notes
    }
    data.insert(0, new_entry) # Masukin ke paling atas
    save_journal(data)

def get_journals(limit=5):
    data = load_journal()
    return data[:limit] # Ambil 5 terakhir
