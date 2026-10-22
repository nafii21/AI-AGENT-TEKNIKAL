import yfinance as yf
import pandas as pd

SYMBOLS = {
    "XAUUSD": "GC=F",
    "NASDAQ": "NQ=F",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "JPY=X",
    "BTCUSD": "BTC-USD"
}

TF_MAP = {
    "M5": {"interval": "5m", "period": "5d"},
    "M15": {"interval": "15m", "period": "1mo"},
    "H1": {"interval": "1h", "period": "3mo"},
    "H4": {"interval": "1h", "period": "6mo"}, # Ambil H1 dulu buat di-resample
    "D1": {"interval": "1d", "period": "1y"}
}

def fetch_data(symbol: str, timeframe: str) -> pd.DataFrame:
    ticker = SYMBOLS.get(symbol.upper(), symbol)
    tf = TF_MAP.get(timeframe.upper(), TF_MAP["M15"])
    
    df = yf.download(ticker, period=tf["period"], interval=tf["interval"], progress=False)
    if df.empty:
        raise ValueError(f"Data kosong untuk {symbol}")
        
    if hasattr(df.columns, 'levels'):
        df.columns = df.columns.get_level_values(0)
        
    df = df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
    df = df.reset_index().rename(columns={"Datetime": "timestamps", "Date": "timestamps"})
    
    # KHUSUS H4: Kita gabungin data H1 jadi H4
    if timeframe.upper() == "H4":
        df = df.set_index('timestamps')
        df = df.resample('4h').agg({
            'open': 'first', 'high': 'max', 'low': 'min', 
            'close': 'last', 'volume': 'sum'
        }).dropna().reset_index()
    
    df['volume'] = df['volume'].fillna(1)
    return df
