import pandas as pd
from smartmoneyconcepts import smc

def analyze_ict_structure(df_main: pd.DataFrame, df_smt: pd.DataFrame, df_dxy: pd.DataFrame) -> dict:
    d = df_main.set_index("timestamps")[["open", "high", "low", "close", "volume"]].copy()
    d.index = pd.to_datetime(d.index)
    d = d.sort_index()
    
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
                if isinstance(v, pd.Timestamp): rr[k] = v.isoformat()
                elif pd.isna(v): rr[k] = None
                else: rr[k] = v
            out.append(rr)
        return out

    # 1. BOS/CHoCH
    bos_data = []
    if bos_choch is not None and not bos_choch.empty:
        valid_bos = bos_choch.dropna(subset=["BOS", "CHOCH"], how="all")
        bos_data = _clean(valid_bos.tail(10).reset_index().to_dict("records"))

    # 2. OB (Ambil 20 terakhir, tandai mana yang udah mitigated)
    ob_data = []
    if ob is not None and not ob.empty:
        # Kita TIDAK membuang yang mitigated, tapi kita ambil 20 terakhir
        recent_ob = ob.tail(20) 
        ob_data = _clean(recent_ob.reset_index().to_dict("records"))

    # 3. FVG (Ambil 20 terakhir, tandai mana yang udah mitigated)
    fvg_data = []
    if fvg is not None and not fvg.empty:
        recent_fvg = fvg.tail(20)
        fvg_data = _clean(recent_fvg.reset_index().to_dict("records"))

    # 4. Liquidity (BSL/SSL)
    liq_data = []
    if liquidity is not None and not liquidity.empty:
        valid_liq = liquidity.dropna(subset=["Liquidity"])
        liq_data = _clean(valid_liq.tail(10).reset_index().to_dict("records"))

    bsl_levels = [x.get("Level") for x in liq_data if x.get("Liquidity") in (1, "BSL")]
    ssl_levels = [x.get("Level") for x in liq_data if x.get("Liquidity") in (-1, "SSL")]

    # 5. Swing Points
    swings_data = []
    if swing_hl is not None and not swing_hl.empty:
        valid_swings = swing_hl.dropna(subset=["HighLow"])
        swings_data = _clean(valid_swings.tail(10).reset_index().to_dict("records"))

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

    actual_swings = len(swing_hl[swing_hl["HighLow"].notna()]) if swing_hl is not None else 0
    current_price = float(d["close"].iloc[-1])

    return {
        "current_price": round(current_price, 2),
        "data_len": len(d),
        "swing_len": actual_swings,
        "recent_swings": swings_data,
        "bos_choch": bos_data,
        "order_blocks_active": ob_data, 
        "fvg_active": fvg_data,
        "liquidity_summary": {
            "BSL_above": bsl_levels[:3],
            "SSL_below": ssl_levels[:3]
        },
        "smt_status": smt_status,
        "usd_bias_dxy": usd_bias
    }
