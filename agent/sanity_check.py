import math

def sanity_check(decision: dict) -> tuple[bool, str]:
    action = decision.get("action")
    if action not in ("BUY_LIMIT", "SELL_LIMIT", "WAIT"): 
        return False, f"action tidak valid: {action}"
    
    if action == "WAIT": 
        return False, "WAIT — tidak ada setup"

    vals = [decision.get(k) for k in ("entry", "sl", "tp1")]
    for k, v in zip(("entry", "sl", "tp1"), vals):
        if not isinstance(v, (int, float)) or not math.isfinite(v):
            return False, f"{k} bukan angka valid: {v}"

    entry, sl, tp1 = vals
    
    if action == "BUY_LIMIT":
        if sl >= entry: return False, f"BUY_LIMIT: SL harus < entry"
        if tp1 <= entry: return False, f"BUY_LIMIT: TP1 harus > entry"
    if action == "SELL_LIMIT":
        if sl <= entry: return False, f"SELL_LIMIT: SL harus > entry"
        if tp1 >= entry: return False, f"SELL_LIMIT: TP1 harus < entry"

    return True, "OK"
