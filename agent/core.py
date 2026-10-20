from agent.data import fetch_ohlcv_by_tf
from agent.kronos_layer import kronos_forecast
from agent.stats_layer import compute_stats
from agent.smc_layer import compute_smc
from agent.session_layer import compute_asian_session
from agent.llm_layer import decide
from agent.sanity_check import sanity_check

def analyze_market(symbol: str, timeframe: str) -> dict:
    try:
        data = fetch_ohlcv_by_tf(symbol, timeframe)
        df = data["df"]
        
        session = compute_asian_session(df)
        if "error" in session:
            return {"error": f"Session Error: {session['error']}"}
            
        kronos = kronos_forecast(df, horizon=12)
        stats  = compute_stats(df)
        smc_data = compute_smc(df)
        
        decision = decide(symbol, kronos, stats, smc_data, session)
        
        ok, reason = sanity_check(decision)
        if not ok and decision.get("action") != "WAIT":
            decision["action"] = "WAIT"
            decision["reason"] = f"Sanity check gagal: {reason}"

        decision["timeframe"] = timeframe
        decision["symbol"] = symbol
        return decision
    except Exception as e:
        return {"error": str(e)}
