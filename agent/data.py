import os, httpx, yfinance as yf
import pandas as pd

TWELVE_KEY = os.getenv("TWELVE_DATA_API_KEY")

TWELVE_SYMBOLS = {
    "XAUUSD": "XAU/USD",
    "NASDAQ": "QQQ",
    "GBPUSD": "GBP/USD",
    "USDJPY": "USD/JPY"
}

YF_SYMBOLS = {
    "DXY": "DX-Y.NYB", 
    "XAG": "SI=F",     
    "SPX": "ES=F",
    "EUR": "EURUSD=X", 
    "CHF": "CHF=X"     
}

TF_MAP_TWELVE = {
    "M5": "5min",
    "M15": "15min", 
    "H1": "1h", 
    "H4": "4h", 
    "D1": "1day"
}

def fetch_twelvedata(symbol_key: str, timeframe: str, outputsize: int = 500) -> pd.DataFrame:
    symbol = TWELVE_SYMBOLS.get(symbol_key, symbol_key)
    interval = TF_MAP_TWELVE.get(timeframe, "1h")
    
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize={outputsize}&timezone=UTC&apikey={TWELVE_KEY}"
    resp = httpx.get(url, timeout=20).json()
    
    if "values" not in resp:
        raise ValueError(f"TwelveData Error untuk {symbol}: {resp.get('message', 'No data')}")
    
    df = pd.DataFrame(resp["values"])
    df = df.rename(columns={"datetime": "timestamps"})
    
    for col in ["open", "high", "low", "close"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
    df = df.dropna(subset=["open", "high", "low", "close"])
    
    if "volume" not in df.columns:
        df["volume"] = 1
    else:
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(1)
        df.loc[df["volume"] == 0, "volume"] = 1
        
    df["timestamps"] = pd.to_datetime(df["timestamps"])
    df = df.sort_values("timestamps").reset_index(drop=True)
    
    if df.empty:
        raise ValueError(f"Data kosong setelah dibersihkan untuk {symbol}")
        
    df["amount"] = df["close"] * df["volume"]
    return df

def fetch_yfinance(symbol_key: str, timeframe: str) -> pd.DataFrame:
    ticker = YF_SYMBOLS.get(symbol_key, symbol_key)
    
    if timeframe == "M5":
        interval, period = "5m", "5d"
    elif timeframe == "M15":
        interval, period = "15m", "5d"
    elif timeframe in ["H1", "H4"]:
        interval, period = "1h", "3mo"
    else:
        interval, period = "1d", "1y"

    df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
    if df.empty:
        raise ValueError(f"yfinance Error: Data kosong untuk {ticker}")
    
    if hasattr(df.columns, 'levels'):
        df.columns = df.columns.get_level_values(0)
        
    df = df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
    df = df.reset_index().rename(columns={"Datetime": "timestamps", "Date": "timestamps"})
    
    for col in ["open", "high", "low", "close"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            
    df = df.dropna(subset=["open", "high", "low", "close"])
    
    if "volume" not in df.columns:
        df["volume"] = 1
    else:
        df["volume"] = df["volume"].fillna(1)
        df.loc[df["volume"] == 0, "volume"] = 1
        
    df["amount"] = df["close"] * df["volume"]

    if timeframe == "H4":
        df = df.set_index("timestamps")
        df = df.resample('4h').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum', 'amount': 'sum'}).dropna().reset_index()

    return df
