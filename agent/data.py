import os, httpx, pandas as pd

TWELVE_KEY = os.getenv("TWELVE_DATA_API_KEY")
TF_MAP = {"M15": "15min", "H1": "1h", "H4": "4h", "D1": "1day"}
SYMBOLS = {
    "XAUUSD": "XAU/USD",
    "NASDAQ": "NDX",       # Nasdaq 100
    "XAGUSD": "XAG/USD",   # Silver untuk SMT
    "DXY": "DXY"           # Dollar Index
}

def fetch_twelvedata(symbol_key: str, timeframe: str, outputsize: int = 500) -> pd.DataFrame:
    symbol = SYMBOLS.get(symbol_key)
    interval = TF_MAP.get(timeframe, "1h")
    
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize={outputsize}&timezone=UTC&apikey={TWELVE_KEY}"
    resp = httpx.get(url, timeout=20).json()
    
    if "values" not in resp:
        raise ValueError(f"TwelveData Error: {resp.get('message', 'No data')}")
    
    df = pd.DataFrame(resp["values"])
    df = df.rename(columns={"datetime": "timestamps", "open": "open", "high": "high", "low": "low", "close": "close", "volume": "volume"})
    
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    df["timestamps"] = pd.to_datetime(df["timestamps"])
    df = df.sort_values("timestamps").reset_index(drop=True)
    df["amount"] = df["close"] * df["volume"]
    return df
