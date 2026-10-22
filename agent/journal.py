import json, os
from datetime import datetime
from agent.data import fetch_data
import pandas as pd

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

def has_active_setup(symbol: str) -> bool:
    data = load_journal()
    for entry in data:
        if entry.get("symbol") == symbol and entry.get("result") == "PENDING":
            return True
    return False

def update_statuses():
    data = load_journal()
    updated = False
    
    # Kelompokkan biar hemat API call
    pending_entries = {}
    for i, entry in enumerate(data):
        if entry.get('result') == 'PENDING':
            sym = entry.get('symbol')
            if sym not in pending_entries: pending_entries[sym] = []
            pending_entries[sym].append((i, entry))
            
    for sym, entries in pending_entries.items():
        try:
            df = fetch_data(sym, "M5") 
            df['timestamps'] = pd.to_datetime(df['timestamps']).dt.tz_localize(None)
            
            for idx, entry in entries:
                entry_time = pd.to_datetime(entry.get('timestamp'))
                
                # Ambil candle SETELAH setup dibuat
                df_after = df[df['timestamps'] >= entry_time]
                if df_after.empty: continue 
                
                action = entry.get('action')
                entry_price = float(entry.get('entry', 0))
                tp = float(entry.get('tp', 0))
                sl = float(entry.get('sl', 0))
                
                hit_status = None
                is_triggered = False 
                
                for _, row in df_after.iterrows():
                    high, low = float(row['high']), float(row['low'])
                    
                    # 1. CEK KETINGGALAN KERETA (TP kena duluan sebelum Entry)
                    if not is_triggered:
                        if action == "BUY_LIMIT":
                            if low <= entry_price: 
                                is_triggered = True
                            elif high >= tp: 
                                hit_status = '⚠️ MISSED (TP Before Entry)'
                                break
                        elif action == "SELL_LIMIT":
                            if high >= entry_price: 
                                is_triggered = True
                            elif low <= tp:
                                hit_status = '⚠️ MISSED (TP Before Entry)'
                                break
                    
                    # 2. CEK TP / SL (Kalau Entry sudah tersentuh)
                    if is_triggered:
                        if action == "BUY_LIMIT":
                            if high >= tp: hit_status = '✅ TP HIT'; break
                            elif low <= sl: hit_status = '❌ SL HIT'; break
                        elif action == "SELL_LIMIT":
                            if low <= tp: hit_status = '✅ TP HIT'; break
                            elif high >= sl: hit_status = '❌ SL HIT'; break
                            
                if hit_status:
                    data[idx]['result'] = hit_status
                    updated = True
                    
        except Exception as e:
            print(f"Error update status {sym}: {e}")
                
    if updated:
        save_journal(data)

def get_monthly_stats():
    data = load_journal()
    now = datetime.utcnow()
    current_month = now.strftime("%Y-%m") 
    
    tp_count, sl_count, total_closed = 0, 0, 0
    
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
