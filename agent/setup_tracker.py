import json, os
from datetime import datetime, timedelta
SETUP_FILE = "active_setups.json"

def load_setups():
    if not os.path.exists(SETUP_FILE): return {}
    try:
        with open(SETUP_FILE, "r") as f: return json.load(f)
    except: return {}

def save_setups(data):
    with open(SETUP_FILE, "w") as f: json.dump(data, f, indent=2)

def validate_and_update(symbol, tf, new_decision, current_price):
    setups = load_setups()
    key = f"{symbol}_{tf}"
    status = ""
    now = datetime.utcnow()

    if key in setups:
        old = setups[key]
        action, sl, tp1 = old.get("action"), old.get("sl", 0), old.get("tp1", 0)
        
        # Cek Expired
        if old.get("expiry_time"):
            if now > datetime.fromisoformat(old["expiry_time"]):
                del setups[key]; save_setups(setups)
                return f"⚠️ Setup sebelumnya EXPIRED."
        
        # Cek Hit SL/TP
        if (action == "BUY_LIMIT" and current_price <= sl) or (action == "SELL_LIMIT" and current_price >= sl):
            del setups[key]; save_setups(setups); return f"❌ Setup sebelumnya Kena SL."
        if (action == "BUY_LIMIT" and current_price >= tp1) or (action == "SELL_LIMIT" and current_price <= tp1):
            del setups[key]; save_setups(setups); return f"✅ Setup sebelumnya TP Hit!"
        
        status = f"⏳ Setup {action} PENDING."

    if new_decision.get("action") in ("BUY_LIMIT", "SELL_LIMIT"):
        validity = new_decision.get("validity_mins", 60)
        new_decision["expiry_time"] = (now + timedelta(minutes=validity)).isoformat()
        setups[key] = new_decision
        save_setups(setups)
    return status
