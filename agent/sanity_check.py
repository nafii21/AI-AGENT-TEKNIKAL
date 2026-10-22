import math
def sanity_check(decision: dict) -> tuple[bool, str]:
    action = decision.get("action")
    if action not in ("BUY_LIMIT", "SELL_LIMIT", "WAIT"): return False, "Action invalid"
    if action == "WAIT": return False, "WAIT"
    
    entry, sl, tp1 = decision.get("entry_price"), decision.get("sl"), decision.get("tp1")
    if None in (entry, sl, tp1): return False, "Harga tidak lengkap"

    if action == "BUY_LIMIT" and (sl >= entry or tp1 <= entry): return False, "Logika Buy salah"
    if action == "SELL_LIMIT" and (sl <= entry or tp1 >= entry): return False, "Logika Sell salah"
    return True, "OK"
