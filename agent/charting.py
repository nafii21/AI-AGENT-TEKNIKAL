import pandas as pd
import mplfinance as mpf
import os

def generate_chart(df: pd.DataFrame, decision: dict, symbol: str, timeframe: str) -> str:
    try:
        # 1. Siapkan Data (Ambil 60 candle terakhir biar ga terlalu kecil)
        df_chart = df.tail(60).copy()
        df_chart = df_chart.set_index('timestamps')
        
        # Pastiin format indexnya bener
        df_chart.index = pd.to_datetime(df_chart.index)
        
        # Rename kolom biar sesuai standar mplfinance
        df_chart = df_chart.rename(columns={
            "open": "Open", "high": "High", "low": "Low", 
            "close": "Close", "volume": "Volume"
        })

        # 2. Set-up Style Dark Mode
        mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', edge='inherit', wick='inherit', volume='in')
        s  = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc)

        # 3. Garis Entry, SL, TP
        lines = []
        if decision.get("action") in ("BUY_LIMIT", "SELL_LIMIT"):
            entry = decision.get("entry")
            sl = decision.get("sl")
            tp1 = decision.get("tp1")
            tp2 = decision.get("tp2")

            if entry: lines.append(mpf.make_addplot(pd.Series(entry, index=df_chart.index), color='yellow', linestyle='dashed', width=1.5))
            if sl: lines.append(mpf.make_addplot(pd.Series(sl, index=df_chart.index), color='red', linestyle='solid', width=1.5))
            if tp1: lines.append(mpf.make_addplot(pd.Series(tp1, index=df_chart.index), color='green', linestyle='solid', width=1.5))
            if tp2: lines.append(mpf.make_addplot(pd.Series(tp2, index=df_chart.index), color='green', linestyle='dotted', width=1.5))

        # 4. Render Chart ke File
        filename = f"chart_{symbol}_{timeframe}.png"
        title = f"\n{symbol} [{timeframe}] - {decision.get('action', 'WAIT')}"
        
        mpf.plot(
            df_chart, 
            type='candle', 
            style=s, 
            title=title,
            volume=True, 
            addplot=lines if lines else None,
            savefig=dict(fname=filename, bbox_inches='tight', dpi=120)
        )
        
        return filename
    except Exception as e:
        print(f"Gagal bikin chart: {e}")
        return None
