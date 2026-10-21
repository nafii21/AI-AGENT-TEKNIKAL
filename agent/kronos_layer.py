import pandas as pd
import torch
import sys

# Tambahin path repo Kronos yang udah di-clone
sys.path.append("/tmp/Kronos")
from model import Kronos, KronosTokenizer, KronosPredictor

# Load model sekali aja (biar nggak lemot)
device = "cuda" if torch.cuda.is_available() else "cpu"
tokenizer = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-base")
model = Kronos.from_pretrained("NeoQuasar/Kronos-small").to(device)
predictor = KronosPredictor(model, tokenizer, device=device)

def kronos_forecast(df: pd.DataFrame, horizon: int = 12) -> dict:
    try:
        hist = df.tail(400).copy()
        x_ts = pd.to_datetime(hist["timestamps"])
        last_ts = x_ts.iloc[-1]

        freq = pd.infer_freq(x_ts) or "1h"
        y_ts = pd.date_range(last_ts, periods=horizon + 1, freq=freq)[1:]

        # Pake predictor resmi
        pred = predictor.predict(
            df=hist[["open", "high", "low", "close", "volume", "amount"]],
            x_timestamp=x_ts,
            y_timestamp=y_ts,
            pred_len=horizon,
        )

        close_pred = pred["close"]
        last_close = float(hist["close"].iloc[-1])
        rets = close_pred.pct_change().dropna()

        mean_ret = float(rets.mean())
        vol = float(rets.std()) if len(rets) > 1 else 0.0

        bias = "bullish" if mean_ret > 0.0005 else "bearish" if mean_ret < -0.0005 else "neutral"

        return {
            "bias": bias,
            "expected_return": round(mean_ret, 6),
            "volatility": round(vol, 6),
            "key_levels": {
                "support": round(float(close_pred.min()), 2),
                "resistance": round(float(close_pred.max()), 2),
                "last_close": last_close,
            },
        }
    except Exception as e:
        return {"bias": "unknown", "error": str(e)}
