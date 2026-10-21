import pandas as pd
from smartmoneyconcepts import smc

def analyze_ict_structure(df_main: pd.DataFrame, df_smt: pd.DataFrame, df_dxy: pd.DataFrame) -> dict:
    d = df_main.set_index("timestamps")[["open", "high", "low", "close", "volume"]].copy()
    
    swing_hl = smc.swing_highs_lows(d, swing_length=10)
    bos_choch = smc.bos_choch(d, swing_hl)
    ob = smc.ob(d, swing_hl)
    fvg = smc.fvg(d)
    liquidity = smc.liquidity(d, swing_hl)

    def _clean(rows):
        out = []
        for r in rows:
            rr = {}
            for k, v in r.items():
                if isinstance(v, pd.Timestamp): 
                    rr[k] = v.isoformat()
                elif pd.isna(v): 
                    rr[k] = None
                else: 
                    rr[k] = v
            out.append(rr)
        return out

    def _active(feat, col="MitigatedIndex", n=3):
        if feat is None or feat.empty: return []
        if col not in feat.columns: return []
        active = feat[feat[col].isna()]
        return _clean(active.tail(n).reset_index().to_dict("records"))

    # SMT Divergence
    smt_high_main = d["high"].iloc[-20:].max()
    smt_high_comp = df_smt["high"].iloc[-20:].max()
    smt_low_main = d["low"].iloc[-20:].min()
    smt_low_comp = df_smt["low"].iloc[-20:].min()
    
    smt_status = "neutral"
    if smt_high_main > d["high"].iloc[-40:-20].max() and smt_high_comp < df_smt["high"].iloc[-40:-20].max():
        smt_status = "bearish_divergence"
    elif smt_low_main < d["low"].iloc[-40:-20].min() and smt_low_comp > df_smt["low"].iloc[-40:-20].min():
        smt_status = "bullish_divergence"

    # DXY Bias
    dxy_change = df_dxy["close"].pct_change(5).iloc[-1]
    usd_bias = "usd_menguat" if dxy_change > 0.001 else "usd_melemah" if dxy_change < -0.001 else "netral"

    # Ekstrak Likuiditas (BSL / SSL)
    liq_data = _clean(liquidity.tail(5).reset_index().to_dict("records") if liquidity is not None and not liquidity.empty else [])
    
    bsl_levels = []
    ssl_levels = []
    for x in liq_data:
        liq_val = x.get("Liquidity")
        if liq_val == 1 or liq_val == "BSL":
            bsl_levels.append(x.get("Level"))
        elif liq_val == -1 or liq_val == "SSL":
            ssl_levels.append(x.get("Level"))

    return {
        "bos_choch": _clean(bos_choch.tail(3).reset_index().to_dict("records") if bos_choch is not None and not bos_choch.empty else []),
        "order_blocks_active": _active(ob),
        "fvg_active": _active(fvg),
        "liquidity_raw": liq_data,
        "liquidity_summary": {
            "BSL_above": bsl_levels[:2],
            "SSL_below": ssl_levels[:2]
        },
        "smt_status": smt_status,
        "usd_bias_dxy": usd_bias,
        "dxy_5bar_change": round(float(dxy_change), 5) if pd.notna(dxy_change) else 0
    }
