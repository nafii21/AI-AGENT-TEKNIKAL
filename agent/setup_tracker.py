import json, os
SETUP_FILE = "active_setups.json"

def load_setups() -> dict:
    if not os.path.exists(SETUP_FILE): return {}
    with open(SETUP_FILE, "r") as f: return json.load(f)

def save_setups(data: dict):
    with open(SETUP_FILE, "w") as f: json.dump(data, f, indent=2)

def validate_and_update(symbol: str, tf: str, new_decision: dict, current_price: float) -> str:
    setups = load_setups()
    key = f"{symbol}_{tf}"
    status_msg = ""

    if key in setups:
        old = setups[key]
        action = old["action"]
        sl = old["sl"]
        tp = old["tp1"]

        if (action == "BUY_LIMIT" and current_price <= sl) or (action == "SELL_LIMIT" and current_price >= sl):
            del setups[key]
            status_msg = f"❌ Setup {action} {symbol} [{tf}] sebelumnya INVALID (Kena SL). Mencari setup baru..."
        elif (action == "BUY_LIMIT" and current_price >= tp) or (action == "SELL_LIMIT" and current_price <= tp):
            del setups[key]
            status_msg = f"✅ Setup {action} {symbol} [{tf}] sebelumnya sudah mencapai TP. Mencari setup baru..."
        else:
            status_msg = f"⏳ Setup {action} {symbol} [{tf}] sebelumnya masih valid (Belum kena SL/TP)."

    if new_decision.get("action") in ("BUY_LIMIT", "SELL_LIMIT"):
        setups[key] = new_decision
        save_setups(setups)
    
    return status_msg
