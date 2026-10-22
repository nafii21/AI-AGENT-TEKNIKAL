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
    data = load_journal()
    updated = False
    for entry in data:
        if entry.get('result') == 'PENDING':
            symbol = entry.get('symbol')
            try:
                df = fetch_data(symbol, "M5")
                current_price = float(df["close"].iloc[-1])
                
                action = entry.get('action')
                tp = float(entry.get('tp', 0))
                sl = float(entry.get('sl', 0))
                
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
            except Exception:
                pass 
                
    if updated:
        save_journal(data)

def get_monthly_stats():
    """Fungsi buat ngitung TP, SL, dan Winrate bulan ini"""
    data = load_journal()
    now = datetime.utcnow()
    current_month = now.strftime("%Y-%m") # Format: 2026-10
    
    tp_count = 0
    sl_count = 0
    total_closed = 0
    
    for entry in data:
        ts = entry.get("timestamp", "")
        if ts.startswith(current_month):
            res = entry.get("result", "")
            if "TP HIT" in res:
                tp_count += 1
                total_closed += 1
            elif "SL HIT" in res:
                sl_count += 1
                total_closed += 1
                
    winrate = (tp_count / total_closed * 100) if total_closed > 0 else 0
    
    return {
        "month": now.strftime("%B %Y"),
        "tp": tp_count,
        "sl": sl_count,
        "total": total_closed,
        "winrate": round(winrate, 1)
    }

def get_journals(limit=5):
    update_statuses() 
    data = load_journal()
    return data[:limit]
