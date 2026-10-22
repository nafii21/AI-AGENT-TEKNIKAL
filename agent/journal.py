import json, os
from datetime import datetime
from agent.data import fetch_data

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
    data.insert(0, new_entry) 
    save_journal(data)

def update_statuses():
    """Fungsi buat ngecek harga terbaru dan nge-update TP/SL"""
    data = load_journal()
    updated = False
    for entry in data:
        if entry['result'] == 'PENDING':
            symbol = entry['symbol']
            try:
                # Ambil harga terbaru pakai TF M5
                df = fetch_data(symbol, "M5")
                current_price = float(df["close"].iloc[-1])
                
                action = entry['action']
                tp = float(entry['tp'])
                sl = float(entry['sl'])
                
                if action == "BUY_LIMIT":
                    if current_price >= tp:
                        entry['result'] = '✅ TP HIT'
                        updated = True
                    elif current_price <= sl:
                        entry['result'] = '❌ SL HIT'
                        updated = True
                elif action == "SELL_LIMIT":
                    if current_price <= tp:
                        entry['result'] = '✅ TP HIT'
                        updated = True
                    elif current_price >= sl:
                        entry['result'] = '❌ SL HIT'
                        updated = True
            except Exception as e:
                pass # Skip kalau data gagal diambil
                
    if updated:
        save_journal(data)

def get_journals(limit=5):
    # Update status dulu sebelum ditampilin
    update_statuses() 
    data = load_journal()
    return data[:limit]
