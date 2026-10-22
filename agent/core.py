import pandas as pd
from agent.data import fetch_twelvedata
from price_action_lib import PriceActionAnalyzer
from agent.llm_layer import decide

analyzer = PriceActionAnalyzer()

def analyze_market(symbol: str, bias_tf: str, setup_tf: str) -> dict:
    try:
        df_bias = fetch_twelvedata(symbol, bias_tf)
        df_setup = fetch_twelvedata(symbol, setup_tf)

        df_bias_pa = df_bias.set_index('timestamps').copy()
        df_setup_pa = df_setup.set_index('timestamps').copy()
        
        # Analisa Struktur Bias
        bias_analysis = analyzer.fetch_all(df_bias_pa)
        bias_trend = bias_analysis['structure_trend'].iloc[-1] if 'structure_trend' in bias_analysis else "NEUTRAL"

        # Analisa Setup
        setup_analysis = analyzer.fetch_all(df_setup_pa)
        
        # Ekstrak level Support/Resistance (sesuaikan key dengan output price-action-lib)
        # Kita sediakan fallback kalau key-nya beda
        nearest_support = float(setup_analysis.get('nearest_support', df_setup['low'].min()).iloc[-1]) if hasattr(setup_analysis.get('nearest_support'), 'iloc') else float(df_setup['low'].min())
        nearest_resistance = float(setup_analysis.get('nearest_resistance', df_setup['high'].max()).iloc[-1]) if hasattr(setup_analysis.get('nearest_resistance'), 'iloc') else float(df_setup['high'].max())

        pa_data = {
            "bias_trend": bias_trend,
            "current_price": float(df_setup["close"].iloc[-1]),
            "nearest_support": nearest_support,
            "nearest_resistance": nearest_resistance
        }
        
        decision = decide(symbol, bias_tf, setup_tf, pa_data)
        
        decision["df_ohlcv"] = df_setup.tail(60).to_dict(orient="records")
        decision["bias_tf"] = bias_tf
        decision["setup_tf"] = setup_tf
        decision["current_price"] = pa_data["current_price"]
        return decision
    except Exception as e:
        return {"error": str(e)}
