import finasys as fs
import pandas as pd

def compute_stats(df: pd.DataFrame) -> dict:
    try:
        fdf = df.copy()
        fdf = fs.features.add_all(fdf)
        last = fdf.iloc[-1]
        ret_1 = fdf["close"].pct_change()
        roll = ret_1.rolling(20).agg(["mean", "std", "skew"]).iloc[-1]

        return {
            "rsi_14": round(float(last.get("rsi_14", 50)), 2),
            "macd": round(float(last.get("macd", 0)), 4),
            "macd_signal": round(float(last.get("macd_signal", 0)), 4),
            "atr_14": round(float(last.get("atr_14", 0)), 2),
            "bb_upper": round(float(last.get("bb_upper", last["close"])), 2),
            "bb_lower": round(float(last.get("bb_lower", last["close"])), 2),
            "rolling_mean_20": round(float(roll["mean"]), 6),
            "rolling_std_20": round(float(roll["std"]), 6),
            "rolling_skew_20": round(float(roll["skew"]), 4),
            "last_close": round(float(last["close"]), 2),
        }
    except Exception as e:
        return {"error": str(e), "rsi_14": 50, "atr_14": 10}
