import pandas as pd
from datetime import time

ASIA_START = time(0, 0)
ASIA_END   = time(8, 0)

def _to_utc(ts_series: pd.Series) -> pd.Series:
    s = pd.to_datetime(ts_series)
    return s.dt.tz_localize("UTC") if s.dt.tz is None else s.dt.tz_convert("UTC")

def compute_asian_session(df: pd.DataFrame) -> dict:
    try:
        d = df.copy()
        d["ts_utc"] = _to_utc(d["timestamps"])
        now_utc = d["ts_utc"].iloc[-1]

        today_mask = d["ts_utc"].dt.date == now_utc.date()
        today_df = d[today_mask].copy()

        if today_df.empty: return {"error": "Tidak ada data hari ini"}

        asia_mask = (today_df["ts_utc"].dt.time >= ASIA_START) & (today_df["ts_utc"].dt.time < ASIA_END)
        asia_df = today_df[asia_mask]

        if asia_df.empty: return {"error": "Belum masuk Asian session"}

        asia_high = float(asia_df["high"].max())
        asia_low  = float(asia_df["low"].min())
        asia_range = asia_high - asia_low
        last_close = float(d["close"].iloc[-1])

        range_pos = (last_close - asia_low) / asia_range if asia_range > 0 else 0.5
        post = today_df[today_df["ts_utc"] > asia_df["ts_utc"].iloc[-1]]
        swept_high = bool((post["high"] > asia_high).any()) if not post.empty else False
        swept_low  = bool((post["low"]  < asia_low ).any()) if not post.empty else False

        tr = (d["high"] - d["low"]).tail(14)
        atr_proxy = float(tr.mean()) if len(tr) > 0 else 0.0
        range_vs_atr = round(asia_range / atr_proxy, 2) if atr_proxy > 0 else None

        now_t = now_utc.time()
        london_dt = now_utc.replace(hour=7, minute=0, second=0, microsecond=0)
        minutes_to_london = int((london_dt - now_utc).total_seconds() // 60) if now_utc < london_dt else 0

        if range_vs_atr is None: karakter = "unknown"
        elif range_vs_atr < 0.5: karakter = "sangat sempit (compression)"
        elif range_vs_atr < 1.0: karakter = "normal ranging"
        else: karakter = "lebar (sudah trending)"

        return {
            "asia_high": round(asia_high, 2),
            "asia_low": round(asia_low, 2),
            "asia_range": round(asia_range, 2),
            "last_close": round(last_close, 2),
            "range_position": round(range_pos, 3),
            "swept_asia_high": swept_high,
            "swept_asia_low": swept_low,
            "range_vs_atr": range_vs_atr,
            "karakter_sesi": karakter,
            "minutes_to_london": minutes_to_london,
            "now_utc": now_utc.isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}
