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
        # 1. Tentukan Timeframe MTF
        tf_h1 = "H1"
        tf_m15 = timeframe # Sesuai pilihan user (M15)
        
        # 2. Fetch Data MTF
        if symbol == "NASDAQ":
            df_h1 = fetch_yfinance("NASDAQ", tf_h1)
            df_m15 = fetch_yfinance("NASDAQ", tf_m15)
        else:
            df_h1 = fetch_twelvedata(symbol, tf_h1)
            df_m15 = fetch_twelvedata(symbol, tf_m15)
            
        df_dxy = fetch_yfinance("DXY", tf_m15)

        if symbol == "XAUUSD":
            df_smt = fetch_yfinance("XAG", tf_m15)
        elif symbol == "NASDAQ":
            df_smt = fetch_yfinance("SPX", tf_m15)
        elif symbol == "GBPUSD":
            df_smt = fetch_yfinance("EUR", tf_m15) 
        elif symbol == "USDJPY":
            df_smt = fetch_yfinance("CHF", tf_m15) 
        else:
            df_smt = df_m15.copy()

        current_price = float(df_m15["close"].iloc[-1])

        # 3. Analisa ICT di M15 & H1
        session = compute_asian_session(df_m15)
        kronos = kronos_forecast(df_m15, horizon=12)
        stats  = compute_stats(df_m15)
        
        ict_h1 = analyze_ict_structure(df_h1, df_smt, df_dxy)
        ict_m15 = analyze_ict_structure(df_m15, df_smt, df_dxy)
        
        # 4. AI Decision (Kirim data H1 & M15)
        decision = decide(symbol, kronos, stats, ict_h1, ict_m15, session)
        
        decision["df_ohlcv"] = df_m15.tail(60).to_dict(orient="records")
        decision["current_price"] = current_price
        
        # 5. Tracker
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
