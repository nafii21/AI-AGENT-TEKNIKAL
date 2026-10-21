import json, os

SETUP_FILE = "active_setups.json"

def load_setups() -> dict:
    if not os.path.exists(SETUP_FILE): return {}
    with open(SETUP_FILE, "r") as f: return json.load(f)

def save_setups(data: dict):
    with open(SETUP_FILE, "w") as f: json.dump(data, f, indent=2)

def validate_and_update(symbol: str, tf: str, new_decision: dict, current_price: float) -> str:
    """
    Cek setup lama, jika invalid hapus.
    Return pesan status (misal: "Setup lama invalid karena harga kena SL").
    """
    setups = load_setups()
    key = f"{symbol}_{tf}"
    status_msg = ""

    if key in setups:
        old = setups[key]
        action = old["action"]
        sl = old["sl"]
        tp = old["tp1"]

        # Cek jika harga sudah menyentuh SL
        if (action == "BUY_LIMIT" and current_price <= sl) or (action == "SELL_LIMIT" and current_price >= sl):
            del setups[key]
            status_msg = f"❌ Setup {action} {symbol} [{tf}] sebelumnya INVALID (Harga menyentuh SL). Mencari setup baru..."
        # Cek jika harga sudah menyentuh TP
        elif (action == "BUY_LIMIT" and current_price >= tp) or (action == "SELL_LIMIT" and current_price <= tp):
            del setups[key]
            status_msg = f"✅ Setup {action} {symbol} [{tf}] sebelumnya sudah mencapai TP. Mencari setup baru..."
        else:
            status_msg = f"⏳ Setup {action} {symbol} [{tf}] sebelumnya masih valid (Harga belum menyentuh SL/TP)."

    # Simpan setup baru jika action bukan WAIT
    if new_decision.get("action") in ("BUY_LIMIT", "SELL_LIMIT"):
        setups[key] = new_decision
        save_setups(setups)
    
    return status_msg
