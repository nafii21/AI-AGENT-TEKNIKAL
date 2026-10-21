import json, os
from datetime import datetime, timedelta

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
    now = datetime.now()

    if key in setups:
        old = setups[key]
        action = old.get("action")
        
        # Cek Expiry
        expiry_str = old.get("expiry_time")
        if expiry_str:
            expiry = datetime.fromisoformat(expiry_str)
            if now > expiry:
                del setups[key]
                save_setups(setups)
                return f"⚠️ Setup {action} sebelumnya EXPIRED (Waktu habis). Mencari setup baru..."

        # Cek Zona Entry
        zone_min = old.get("entry_zone_min", 0)
        zone_max = old.get("entry_zone_max", 0)
        sl = old.get("sl", 0)
        tp1 = old.get("tp1", 0)

        if zone_min <= current_price <= zone_max:
            status_msg = f"⏳ Setup {action} {symbol} [{tf}] SEDANG AKTIF di Zona! Harga saat ini {current_price}."
        elif (action == "BUY_LIMIT" and current_price <= sl) or (action == "SELL_LIMIT" and current_price >= sl):
            del setups[key]
            save_setups(setups)
            return f"❌ Setup {action} sebelumnya INVALID (Kena SL)."
        elif (action == "BUY_LIMIT" and current_price >= tp1) or (action == "SELL_LIMIT" and current_price <= tp1):
            del setups[key]
            save_setups(setups)
            return f"✅ Setup {action} sebelumnya TP HIT!"
        else:
            status_msg = f"⏳ Setup {action} {symbol} [{tf}] PENDING (Menunggu harga masuk zona)."

    # Simpan setup baru
    if new_decision.get("action") in ("BUY_LIMIT", "SELL_LIMIT"):
        expiry_time = now + timedelta(minutes=new_decision.get("validity_mins", 45))
        new_decision["expiry_time"] = expiry_time.isoformat()
        new_decision["created_at"] = now.isoformat()
        setups[key] = new_decision
        save_setups(setups)
    
    return status_msg
