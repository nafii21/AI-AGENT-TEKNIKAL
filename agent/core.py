from agent.data import fetch_twelvedata, fetch_yfinance
from agent.kronos_layer import kronos_forecast
from agent.stats_layer import compute_stats
from agent.ict_layer import analyze_ict_structure
from agent.session_layer import compute_asian_session
from agent.llm_layer import decide
from agent.sanity_check import sanity_check
from agent.setup_tracker import validate_and_update

def analyze_market(symbol: str, timeframe: str) -> dict:
    try:
        # 1. Fetch Data (H1, M15, M1)
        if symbol == "NASDAQ":
            df_h1 = fetch_yfinance("NASDAQ", "H1")
            df_m15 = fetch_yfinance("NASDAQ", "M15")
            df_m1 = fetch_yfinance("NASDAQ", "M1")
        else:
            df_h1 = fetch_twelvedata(symbol, "H1")
            df_m15 = fetch_twelvedata(symbol, "M15")
            df_m1 = fetch_twelvedata(symbol, "M1")
            
        df_dxy = fetch_yfinance("DXY", timeframe)

        if symbol == "XAUUSD":
            df_smt = fetch_yfinance("XAG", timeframe)
        elif symbol == "NASDAQ":
            df_smt = fetch_yfinance("SPX", timeframe)
        elif symbol == "GBPUSD":
            df_smt = fetch_yfinance("EUR", timeframe) 
        elif symbol == "USDJPY":
            df_smt = fetch_yfinance("CHF", timeframe) 
        else:
            df_smt = df_m15.copy()

        current_price = float(df_m15["close"].iloc[-1])

        # 2. Analisa ICT
        ict_h1 = analyze_ict_structure(df_h1, df_smt, df_dxy)
        ict_m15 = analyze_ict_structure(df_m15, df_smt, df_dxy)
        ict_m1 = analyze_ict_structure(df_m1, df_smt, df_dxy)
        
        # 3. AI Decision (Kirim 3 TF)
        decision = decide(symbol, ict_h1, ict_m15, ict_m1)
        
        decision["df_ohlcv"] = df_m15.tail(60).to_dict(orient="records")
        decision["current_price"] = current_price
        
        # 4. Tracker
        tracker_msg = validate_and_update(symbol, timeframe, decision, current_price)
        
        ok, reason = sanity_check(decision)
        if not ok and decision.get("action") != "WAIT":
            decision["action"] = "WAIT"
            decision["reason"] = f"Sanity check gagal: {reason}"

        decision["timeframe"] = timeframe
        decision["symbol"] = symbol
        decision["tracker_msg"] = tracker_msg
        return decision
    except Exception as e:
        return {"error": str(e)}
