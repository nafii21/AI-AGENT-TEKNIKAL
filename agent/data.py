import os, httpx, pandas as pd

TWELVE_KEY = os.getenv("TWELVE_DATA_API_KEY")
TF_MAP_TWELVE = {"M1": "1min", "M5": "5min", "M15": "15min", "H1": "1h", "H4": "4h", "D1": "1day"}

def fetch_twelvedata(symbol: str, timeframe: str, outputsize: int = 300) -> pd.DataFrame:
    # Contoh: XAU/USD
    tw_symbol = "XAU/USD" if symbol == "XAUUSD" else symbol
    interval = TF_MAP_TWELVE.get(timeframe, "15min")
    
    url = f"https://api.twelvedata.com/time_series?symbol={tw_symbol}&interval={interval}&outputsize={outputsize}&timezone=UTC&apikey={TWELVE_KEY}"
    resp = httpx.get(url, timeout=20).json()
    
    if "values" not in resp:
        raise ValueError(f"TwelveData Error: {resp.get('message', 'No data')}")
    
    df = pd.DataFrame(resp["values"]).rename(columns={"datetime": "timestamps"})
    
    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    df = df.dropna(subset=["open", "high", "low", "close"])
    df["volume"] = pd.to_numeric(df.get("volume", 1), errors="coerce").fillna(1).replace(0, 1)
    
    df["timestamps"] = pd.to_datetime(df["timestamps"])
    return df.sort_values("timestamps").reset_index(drop=True)
