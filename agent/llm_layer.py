import json, os
from openai import OpenAI

client_groq = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.environ.get("GROQ_API_KEY", ""))
GROQ_MODEL = "openai/gpt-oss-120b"

SYSTEM_PROMPT = """
Kamu adalah "Sniper MSNR Analyst".
Tugasmu memberikan harga ENTRY LIMIT PRESISI (Sniper) di area Support/Resistance. Tanpa menunggu pola candle.

FRAMEWORK:
1. Lihat "bias_trend". Jika BULLISH, cari BUY_LIMIT di area "nearest_support". Jika BEARISH, cari SELL_LIMIT di area "nearest_resistance".
2. SNIPER ENTRY: Tentukan harga di ujung terluar S/R (Proximal) agar mendapat harga terbaik.
3. SL: Letakkan sedikit di balik S/R tersebut (Distal).
4. TP: Letakkan di S/R berikutnya atau hitung dengan RR minimal 1:2.
5. RR WAJIB 1:2. Jika tidak memenuhi, action = "WAIT".

OUTPUT HARUS JSON VALID:
{
  "action": "BUY_LIMIT|SELL_LIMIT|WAIT",
  "entry_price": float,
  "sl": float,
  "tp1": float,
  "tp2": float,
  "rr": float,
  "confidence": float (0-10),
  "reason": "Penjelasan singkat Bahasa Indonesia (sebutkan level S/R yang dipakai)"
}
"""

def decide(symbol: str, bias_tf: str, setup_tf: str, pa_data: dict) -> dict:
    try:
        resp = client_groq.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps({"symbol": symbol, "data": pa_data}, ensure_ascii=False, default=str)},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        return {"action": "WAIT", "reason": f"LLM Error: {str(e)}", "confidence": 0}
