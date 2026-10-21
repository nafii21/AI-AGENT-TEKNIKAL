import os, httpx, pandas as pd

TWELVE_KEY = os.getenv("TWELVE_DATA_API_KEY")
TF_MAP = {"M15": "15min", "H1": "1h", "H4": "4h", "D1": "1day"}

# Kita pakai proxy ETF & Forex biar lolos free tier Twelve Data
SYMBOLS = {
    "XAUUSD": "XAU/USD",
    "NASDAQ": "QQQ",       # Proxy Nasdaq 100
    "XAGUSD": "XAG/USD",   # Silver untuk SMT
    "US500": "SPY",        # Proxy S&P 500 untuk SMT NASDAQ
    "DXY": "EUR/USD"       # Proxy DXY (Inverse)
}

def fetch_twelvedata(symbol_key: str, timeframe: str, outputsize: int = 500) -> pd.DataFrame:
    symbol = SYMBOLS.get(symbol_key, symbol_key)
    interval = TF_MAP.get(timeframe, "1h")
    
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize={outputsize}&timezone=UTC&apikey={TWELVE_KEY}"
    resp = httpx.get(url, timeout=20).json()
    
    if "values" not in resp:
        raise ValueError(f"TwelveData Error untuk {symbol}: {resp.get('message', 'No data')}")
    
    df = pd.DataFrame(resp["values"])
    df = df.rename(columns={"datetime": "timestamps"})
    
    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
    df["timestamps"] = pd.to_datetime(df["timestamps"])
    df = df.sort_values("timestamps").reset_index(drop=True)
    
    if "volume" not in df.columns:
        df["volume"] = 0
    df["amount"] = df["close"] * df["volume"]
    return df
