import math

def sanity_check(decision: dict) -> tuple[bool, str]:
    action = decision.get("action")
    if action not in ("BUY_LIMIT", "SELL_LIMIT", "WAIT"): 
        return False, f"action tidak valid: {action}"
    
    if action == "WAIT": 
        return False, "WAIT — tidak ada setup"

    vals = [decision.get(k) for k in ("entry_zone_min", "entry_zone_max", "sl", "tp1")]
    for k, v in zip(("entry_zone_min", "entry_zone_max", "sl", "tp1"), vals):
        if not isinstance(v, (int, float)) or not math.isfinite(v):
            return False, f"{k} bukan angka valid: {v}"

    entry_min, entry_max, sl, tp1 = vals
    
    if action == "BUY_LIMIT":
        if sl >= entry_min: return False, f"BUY_LIMIT: SL harus < entry_min"
        if tp1 <= entry_max: return False, f"BUY_LIMIT: TP1 harus > entry_max"
    if action == "SELL_LIMIT":
        if sl <= entry_max: return False, f"SELL_LIMIT: SL harus > entry_max"
        if tp1 >= entry_min: return False, f"SELL_LIMIT: TP1 harus < entry_min"

    return True, "OK"
