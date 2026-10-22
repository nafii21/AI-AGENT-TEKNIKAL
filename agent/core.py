import pandas as pd
from agent.data import fetch_twelvedata
from price_action_lib import PriceActionAnalyzer
from agent.llm_layer import decide

analyzer = PriceActionAnalyzer()

def analyze_market(symbol: str, bias_tf: str, setup_tf: str) -> dict:
    try:
        df_bias = fetch_twelvedata(symbol, bias_tf)
        df_setup = fetch_twelvedata(symbol, setup_tf)

        # Siapkan Data untuk Price Action Lib
        df_bias_pa = df_bias.set_index('timestamps').copy()
        df_setup_pa = df_setup.set_index('timestamps').copy()
        
        # 1. Dapatkan Bias dari TF Besar
        bias_analysis = analyzer.fetch_all(df_bias_pa)
        # Ambil tren terakhir
        bias_trend = bias_analysis['structure_trend'].iloc[-1] if 'structure_trend' in bias_analysis else "NEUTRAL"

        # 2. Cari Level Kunci (S/R) di TF Setup
        setup_analysis = analyzer.fetch_all(df_setup_pa)
        
        # Ambil beberapa data penting (sesuaikan dengan output library price-action-lib)
        # Kita buat dictionary sederhana buat dikirim ke AI
        pa_data = {
            "bias_trend": bias_trend,
            "current_price": float(df_setup["close"].iloc[-1]),
            "support_resistance": {
                # Asumsi library mengembalikan data S/R terdekat
                "nearest_support": float(setup_analysis.get('nearest_support', df_setup["low"].min())),
                "nearest_resistance": float(setup_analysis.get('nearest_resistance', df_setup["high"].max()))
            }
        }
        
        # 3. AI Decision (Sniper Entry)
        decision = decide(symbol, bias_tf, setup_tf, pa_data)
        
        decision["df_ohlcv"] = df_setup.tail(60).to_dict(orient="records")
        decision["bias_tf"] = bias_tf
        decision["setup_tf"] = setup_tf
        return decision

    except Exception as e:
        return {"error": str(e)}
