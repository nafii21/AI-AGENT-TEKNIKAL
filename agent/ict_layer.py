import pandas as pd
from smartmoneyconcepts import smc
import numpy as np

def analyze_ict_structure(df_main: pd.DataFrame, df_smt: pd.DataFrame, df_dxy: pd.DataFrame) -> dict:
    if df_main.empty: return {}
    
    d = df_main.set_index("timestamps")[["open", "high", "low", "close", "volume"]].copy()
    d.index = pd.to_datetime(d.index)
    d = d.sort_index()
    
    swing_hl = smc.swing_highs_lows(d, swing_length=5)
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
                elif isinstance(v, (np.integer, np.floating)):
                    rr[k] = float(v)
                elif isinstance(v, (int, float, str, bool)) or v is None: 
                    rr[k] = v
                else:
                    rr[k] = str(v)
            out.append(rr)
        return out

    bos_data = []
    if bos_choch is not None and not bos_choch.empty:
        valid_bos = bos_choch.dropna(subset=["BOS", "CHOCH"], how="all")
        valid_bos_list = valid_bos.tail(5).reset_index().to_dict("records")
        for b in valid_bos_list:
            # Ubah Timestamp ke index kalau perlu
            idx_val = b.get("timestamps") or b.get("index")
            idx = pd.to_datetime(idx_val) if idx_val else None
            
            if idx and idx in d.index:
                candle = d.loc[idx]
                body_size = abs(candle["close"] - candle["open"])
                atr = (d["high"] - d["low"]).rolling(14).mean().loc[idx]
                b["is_displacement"] = bool(pd.notna(atr) and body_size > (1.2 * atr))
            else:
                b["is_displacement"] = False
        bos_data = _clean(valid_bos_list)

    ob_active, ob_mitigated = [], []
    if ob is not None and not ob.empty:
        if "MitigatedIndex" in ob.columns:
            ob_active = _clean(ob[ob["MitigatedIndex"].isna()].tail(10).reset_index().to_dict("records"))
            ob_mitigated = _clean(ob[ob["MitigatedIndex"].notna()].tail(10).reset_index().to_dict("records"))

    fvg_active, fvg_mitigated = [], []
    if fvg is not None and not fvg.empty:
        if "MitigatedIndex" in fvg.columns:
            fvg_active = _clean(fvg[fvg["MitigatedIndex"].isna()].tail(10).reset_index().to_dict("records"))
            fvg_mitigated = _clean(fvg[fvg["MitigatedIndex"].notna()].tail(10).reset_index().to_dict("records"))

    liq_data = []
    if liquidity is not None and not liquidity.empty:
        valid_liq = liquidity.dropna(subset=["Liquidity"])
        liq_data = _clean(valid_liq.tail(10).reset_index().to_dict("records"))

    bsl_levels = [x.get("Level") for x in liq_data if x.get("Liquidity") in (1, "BSL")]
    ssl_levels = [x.get("Level") for x in liq_data if x.get("Liquidity") in (-1, "SSL")]

    swings_data = []
    if swing_hl is not None and not swing_hl.empty:
        valid_swings = swing_hl.dropna(subset=["HighLow"])
        swings_data = _clean(valid_swings.tail(10).reset_index().to_dict("records"))

    smt_high_main = d["high"].iloc[-20:].max()
    smt_high_comp = df_smt["high"].iloc[-20:].max()
    smt_low_main = d["low"].iloc[-20:].min()
    smt_low_comp = df_smt["low"].iloc[-20:].min()
    
    smt_status = "neutral"
    if smt_high_main > d["high"].iloc[-40:-20].max() and smt_high_comp < df_smt["high"].iloc[-40:-20].max():
        smt_status = "bearish_divergence"
    elif smt_low_main < d["low"].iloc[-40:-20].min() and smt_low_comp > df_smt["low"].iloc[-40:-20].min():
        smt_status = "bullish_divergence"

    dxy_change = df_dxy["close"].pct_change(5).iloc[-1]
    usd_bias = "usd_menguat" if dxy_change > 0.001 else "usd_melemah" if dxy_change < -0.001 else "netral"

    current_price = float(d["close"].iloc[-1])

    return {
        "current_price": round(current_price, 2),
        "recent_swings": swings_data,
        "bos_choch": bos_data,
        "order_blocks_active": ob_active,
        "order_blocks_mitigated": ob_mitigated,
        "fvg_active": fvg_active,
        "fvg_mitigated": fvg_mitigated,
        "liquidity_summary": {
            "BSL_above": bsl_levels[:3],
            "SSL_below": ssl_levels[:3]
        },
        "smt_status": smt_status,
        "usd_bias_dxy": usd_bias
    }
