import pandas as pd
import mplfinance as mpf
import os

def generate_chart(df: pd.DataFrame, decision: dict, symbol: str, tf: str) -> str:
    try:
        df_chart = df.tail(60).copy().set_index('timestamps')
        df_chart.index = pd.to_datetime(df_chart.index)
        df_chart = df_chart.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})

        mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', edge='inherit', wick='inherit', volume='in')
        s  = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc)

        lines = []
        if decision.get("action") in ("BUY_LIMIT", "SELL_LIMIT"):
            entry = decision.get("entry_price")
            sl = decision.get("sl")
            tp = decision.get("tp")
            
            if entry: lines.append(mpf.make_addplot(pd.Series(entry, index=df_chart.index), color='yellow', linestyle='dashed', width=1.5))
            if sl: lines.append(mpf.make_addplot(pd.Series(sl, index=df_chart.index), color='red', linestyle='solid', width=1.5))
            if tp: lines.append(mpf.make_addplot(pd.Series(tp, index=df_chart.index), color='green', linestyle='solid', width=1.5))

        filename = f"chart_{symbol}.png"
        mpf.plot(df_chart, type='candle', style=s, volume=True, addplot=lines if lines else None,
                 panel_ratios=(5, 1), figratio=(16, 9), figscale=1.2,
                 savefig=dict(fname=filename, bbox_inches='tight', dpi=150))
        return filename
    except Exception as e:
        print(f"Chart Error: {e}")
        return None
