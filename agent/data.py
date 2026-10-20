import yfinance as yf

TICKER_MAP = {"XAUUSD": "GC=F", "NASDAQ": "NQ=F"}
TF_MAP = {
    "M15": {"interval": "15m", "period": "5d"},
    "H1":  {"interval": "1h",  "period": "1mo"},
    "H4":  {"interval": "1h",  "period": "3mo"},
    "D1":  {"interval": "1d",  "period": "1y"}
}

def fetch_ohlcv_by_tf(symbol: str, timeframe: str) -> dict:
    ticker = TICKER_MAP.get(symbol.upper(), symbol)
    tf = TF_MAP.get(timeframe.upper(), TF_MAP["H1"])
    
    df = yf.download(ticker, period=tf["period"], interval=tf["interval"], progress=False, auto_adjust=True)
    if df.empty:
        raise ValueError(f"Data kosong untuk {ticker}")
        
    if hasattr(df.columns, 'levels'):
        df.columns = df.columns.get_level_values(0)
        
    df = df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
    df["amount"] = df["close"] * df["volume"]
    df = df.reset_index().rename(columns={"Datetime": "timestamps", "Date": "timestamps"})
    return {"df": df, "ticker": ticker}
