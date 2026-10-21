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
        if symbol == "NASDAQ":
            df_main = fetch_yfinance("NASDAQ", timeframe)
        else:
            df_main = fetch_twelvedata(symbol, timeframe)
            
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
            df_smt = df_main.copy()

        current_price = float(df_main["close"].iloc[-1])

        session = compute_asian_session(df_main)
        kronos = kronos_forecast(df_main, horizon=12)
        stats  = compute_stats(df_main)
        ict_data = analyze_ict_structure(df_main, df_smt, df_dxy)
        
        decision = decide(symbol, kronos, stats, ict_data, session)
        
        # --- Bawa Data OHLCV untuk digambar ---
        decision["df_ohlcv"] = df_main.tail(60).to_dict(orient="records")
        
        decision["data_len"] = ict_data.get("data_len", 0)
        decision["swing_len"] = ict_data.get("swing_len", 0)
        
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
