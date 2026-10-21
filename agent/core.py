from agent.data import fetch_twelvedata, fetch_yfinance
from agent.ict_layer import analyze_ict_structure
from agent.llm_layer import decide
from agent.sanity_check import sanity_check
from agent.setup_tracker import validate_and_update

def analyze_market(symbol: str) -> dict:
    try:
        if symbol == "NASDAQ":
            df_h1 = fetch_yfinance("NASDAQ", "H1")
            df_m15 = fetch_yfinance("NASDAQ", "M15")
            df_m1 = fetch_yfinance("NASDAQ", "M1")
        else:
            df_h1 = fetch_twelvedata(symbol, "H1")
            df_m15 = fetch_twelvedata(symbol, "M15")
            df_m1 = fetch_twelvedata(symbol, "M1")
            
        df_dxy = fetch_yfinance("DXY", "M15")

        if symbol == "XAUUSD":
            df_smt = fetch_yfinance("XAG", "M15")
        elif symbol == "NASDAQ":
            df_smt = fetch_yfinance("SPX", "M15")
        elif symbol == "GBPUSD":
            df_smt = fetch_yfinance("EUR", "M15") 
        elif symbol == "USDJPY":
            df_smt = fetch_yfinance("CHF", "M15") 
        else:
            df_smt = df_m15.copy()

        current_price = float(df_m15["close"].iloc[-1])

        ict_h1 = analyze_ict_structure(df_h1, df_smt, df_dxy)
        ict_m15 = analyze_ict_structure(df_m15, df_smt, df_dxy)
        ict_m1 = analyze_ict_structure(df_m1, df_smt, df_dxy)
        
        decision = decide(symbol, ict_h1, ict_m15, ict_m1)
        
        decision["df_ohlcv"] = df_m15.tail(60).to_dict(orient="records")
        decision["current_price"] = current_price
        
        # --- SUNTIK DATA LIKUIDITAS BUAT CHART WAIT ---
        decision["liquidity"] = ict_m15.get("liquidity_summary", {})
        decision["recent_swings"] = ict_m15.get("recent_swings", [])
        # ----------------------------------------------
        
        tracker_msg = validate_and_update(symbol, "M15", decision, current_price)
        
        ok, reason = sanity_check(decision)
        if not ok and decision.get("action") != "WAIT":
            decision["action"] = "WAIT"
            decision["reason"] = f"Sanity check gagal: {reason}"

        decision["symbol"] = symbol
        decision["tracker_msg"] = tracker_msg
        return decision
    except Exception as e:
        return {"error": str(e)}
