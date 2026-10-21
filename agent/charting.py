import pandas as pd
import mplfinance as mpf
import os

def generate_chart(df: pd.DataFrame, decision: dict, symbol: str, timeframe: str) -> str:
    try:
        df_chart = df.tail(60).copy()
        df_chart = df_chart.set_index('timestamps')
        df_chart.index = pd.to_datetime(df_chart.index)
        
        df_chart = df_chart.rename(columns={
            "open": "Open", "high": "High", "low": "Low", 
            "close": "Close", "volume": "Volume"
        })

        mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', edge='inherit', wick='inherit', volume='in')
        s  = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc)

        lines = []
        action = decision.get("action")

        if action in ("BUY_LIMIT", "SELL_LIMIT"):
            # Setup Entry, SL, TP
            zone_min = decision.get("entry_zone_min")
            zone_max = decision.get("entry_zone_max")
            sl = decision.get("sl")
            tp1 = decision.get("tp1")
            tp2 = decision.get("tp2")

            if zone_min and zone_max:
                lines.append(mpf.make_addplot(pd.Series(zone_min, index=df_chart.index), color='yellow', linestyle='dashed', width=1.5))
                lines.append(mpf.make_addplot(pd.Series(zone_max, index=df_chart.index), color='yellow', linestyle='dashed', width=1.5))
            if sl: lines.append(mpf.make_addplot(pd.Series(sl, index=df_chart.index), color='red', linestyle='solid', width=1.5))
            if tp1: lines.append(mpf.make_addplot(pd.Series(tp1, index=df_chart.index), color='green', linestyle='solid', width=1.5))
            if tp2: lines.append(mpf.make_addplot(pd.Series(tp2, index=df_chart.index), color='green', linestyle='dotted', width=1.5))
            
            title = f"\n{symbol} [{timeframe}] - {action}"
        else:
            # Kalau WAIT, Gambar BSL (Biru) dan SSL (Oranye)
            liq = decision.get("liquidity", {})
            bsl_levels = liq.get("BSL_above", [])
            ssl_levels = liq.get("SSL_below", [])

            for bsl in bsl_levels[:2]: # Ambil 2 terdekat
                if bsl:
                    lines.append(mpf.make_addplot(pd.Series(bsl, index=df_chart.index), color='cyan', linestyle='dotted', width=1))
            for ssl in ssl_levels[:2]:
                if ssl:
                    lines.append(mpf.make_addplot(pd.Series(ssl, index=df_chart.index), color='orange', linestyle='dotted', width=1))
            
            title = f"\n{symbol} [{timeframe}] - WAIT / NO TRADE"

        filename = f"chart_{symbol}.png"
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
