import json, os
from openai import OpenAI

client_groq = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.environ.get("GROQ_API_KEY", ""))
GROQ_MODEL = "openai/gpt-oss-120b"

SYSTEM_PROMPT = """
Kamu adalah "Sniper Analyst" profesional (Institutional Grade) dengan keahlian ICT/SMC.
Kamu akan diberikan data 2 Timeframe: H1 (Trend) dan M15 (Setup).

FRAMEWORK ANALISIS (WAJIB):
1. Konteks H1: Tentukan Trend (Bullish/Bearish). Cari BSL/SSL di H1.
2. Konteks M15: Cari BOS/CHoCH, FVG, dan Order Block yang belum mitigated.
3. POI Zone: Tentukan area entry (Range harga) berdasarkan Top dan Bottom dari FVG/OB M15.
4. Trigger: Cari alasan konfirmasi entry (misal: butuh rejection wick di zona POI).

ATURAN ENTRY:
- JIKA SELL: Entry di zona FVG/OB Bearish. SL di atas zona. TP di SSL terdekat.
- JIKA BUY: Entry di zona FVG/OB Bullish. SL di bawah zona. TP di BSL terdekat.
- RR WAJIB minimal 1:2. Jika tidak memenuhi, action = "WAIT".

OUTPUT HARUS JSON VALID (tanpa markdown):
{
  "action": "BUY_LIMIT|SELL_LIMIT|WAIT",
  "grade": "A|B|C",
  "confidence": float (0-10),
  "bias": "BULLISH|BEARISH|NEUTRAL",
  "entry_zone_min": float,
  "entry_zone_max": float,
  "sl": float,
  "tp1": float,
  "tp2": float,
  "rr_tp1": float,
  "rr_tp2": float,
  "reason_h1": "Penjelasan trend H1...",
  "reason_m15": "Penjelasan struktur dan FVG di M15...",
  "trigger_m1": "Penjelasan trigger/konfirmasi yang dibutuhkan...",
  "invalidation": "Setup batal jika harga close di atas/bawah level X...",
  "validity_mins": int (misal 45),
  "reason": "Kesimpulan akhir Bahasa Indonesia"
}
"""

def decide(symbol: str, kronos: dict, stats: dict, ict_h1: dict, ict_m15: dict, session: dict) -> dict:
    user_payload = {
        "symbol": symbol,
        "kronos_bias": kronos.get("bias"),
        "stats": stats,
        "ict_H1": ict_h1,
        "ict_M15": ict_m15,
        "session": session
    }
    
    try:
        resp = client_groq.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        return {"action": "WAIT", "reason": f"LLM Error: {str(e)}", "confidence": 0}
