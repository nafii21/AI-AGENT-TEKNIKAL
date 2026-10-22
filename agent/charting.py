import pandas as pd
import mplfinance as mpf
import os

def generate_chart(df: pd.DataFrame, decision: dict, symbol: str, timeframe: str) -> str:
    try:
        df_chart = df.tail(60).copy().set_index('timestamps')
        df_chart.index = pd.to_datetime(df_chart.index)
        df_chart = df_chart.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})

        mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', edge='inherit', wick='inherit', volume='in')
        s  = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc)

        lines = []
        y_min = df_chart["Low"].min()
        y_max = df_chart["High"].max()

        if decision.get("action") in ("BUY_LIMIT", "SELL_LIMIT"):
            entry = decision.get("entry_price")
            sl = decision.get("sl")
            tp1 = decision.get("tp1")
            tp2 = decision.get("tp2")
            
            # Gambar garis Entry, SL, TP1
            if entry: 
                lines.append(mpf.make_addplot(pd.Series(entry, index=df_chart.index), color='yellow', linestyle='dashed', width=1.5))
                y_min, y_max = min(y_min, entry), max(y_max, entry)
            if sl: 
                lines.append(mpf.make_addplot(pd.Series(sl, index=df_chart.index), color='red', linestyle='solid', width=1.5))
                y_min, y_max = min(y_min, sl), max(y_max, sl)
            if tp1: 
                lines.append(mpf.make_addplot(pd.Series(tp1, index=df_chart.index), color='green', linestyle='solid', width=1.5))
                y_min, y_max = min(y_min, tp1), max(y_max, tp1)
            
            # TP2 cuma digambar kalau jaraknya gak terlalu ekstrem (biar chart gak gepeng)
            if tp2 and abs(tp2 - entry) < (df_chart["High"].max() - df_chart["Low"].min()) * 2:
                lines.append(mpf.make_addplot(pd.Series(tp2, index=df_chart.index), color='#00e676', linestyle='dotted', width=1.5))
                y_min, y_max = min(y_min, tp2), max(y_max, tp2)

        # Kasih padding dikit di atas & bawah biar candle gak nempel garis
        padding = (y_max - y_min) * 0.1
        y_min -= padding
        y_max += padding

        filename = f"chart_{symbol}.png"
        mpf.plot(df_chart, type='candle', style=s, volume=True, addplot=lines if lines else None,
                 ylim=(y_min, y_max), # <-- Ini kunci biar chartnya gak gepeng
                 panel_ratios=(5, 1), figratio=(16, 9), figscale=1.2,
                 savefig=dict(fname=filename, bbox_inches='tight', dpi=150))
        return filename
    except Exception as e:
        print(f"Chart Error: {e}")
        return None
