import pandas as pd
from smartmoneyconcepts import smc

def compute_smc(df: pd.DataFrame) -> dict:
    try:
        d = df.set_index("timestamps")[["open", "high", "low", "close", "volume"]].copy()
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
                    elif v != v: rr[k] = None
                    else: rr[k] = v
                out.append(rr)
            return out

        def _active(feat, col="MitigatedIndex", n=3):
            if feat is None or feat.empty: return []
            active = feat[feat[col].isna()]
            return _clean(active.tail(n).reset_index().to_dict("records"))

        return {
            "bos_choch": _clean(bos_choch.tail(3).reset_index().to_dict("records") if bos_choch is not None and not bos_choch.empty else []),
            "order_blocks_active": _active(ob),
            "fvg_active": _active(fvg),
            "liquidity": _clean(liquidity.tail(3).reset_index().to_dict("records") if liquidity is not None and not liquidity.empty else []),
        }
    except Exception as e:
        return {"error": str(e)}
