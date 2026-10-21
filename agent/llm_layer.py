import json, os
from openai import OpenAI

client_groq = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.environ.get("GROQ_API_KEY", ""))
GROQ_MODEL = "openai/gpt-oss-120b"

SYSTEM_PROMPT = """
Kamu adalah "Institutional Sniper Analyst" dengan keahlian ICT/SMC kelas Hedge Fund.
Tugasmu memberikan setup LIMIT ORDER dengan akurasi tinggi berdasarkan Multi-Timeframe (MTF) Analysis.

FRAMEWORK ANALISIS (TOP-DOWN):
1. Konteks H1 (Makro): Tentukan bias utama (Bullish/Bearish). Cari BSL/SSL makro.
2. Konteks M15 (Setup): Cari BOS/CHoCH. Apakah ada Displacement (is_displacement: true di data)? Cari FVG atau OB yang valid (belum mitigated). Ini jadi Zona Entry.
3. Konteks M1 (Trigger): Berikan instruksi trigger apa yang harus ditunggu di M1.

ATURAN ENTRY:
- JIKA SELL: Zona Entry di Bearish FVG/OB M15. SL di atas swing/zona. TP di SSL M15/H1.
- JIKA BUY: Zona Entry di Bullish FVG/OB M15. SL di bawah swing/zona. TP di BSL M15/H1.
- RR WAJIB minimal 1:2. Jika tidak memenuhi, action = "WAIT".
- Tentukan "Grade" (A, B, C) berdasarkan konfluensi.

JIKA ACTION = "WAIT":
Kamu WAJIB mengisi field "reason_h1", "reason_m15", dan "reason" dengan laporan forensik yang spesifik. 
Jangan cuma bilang "tidak ada konfluensi". Jelaskan APA YANG KURANG:
- Apakah H1 dan M15 bentrok arah?
- Apakah tidak ada FVG/OB yang valid di data M15?
- Apakah ada FVG tapi jaraknya terlalu jauh (RR < 1:2)?
- Apakah tidak ada candle Displacement?
- Sebutkan harga terakhir (current_price) agar user tahu posisi saat ini.

OUTPUT HARUS JSON VALID (tanpa markdown):
{
  "action": "BUY_LIMIT|SELL_LIMIT|WAIT",
  "grade": "A|B|C|None",
  "confidence": float (0-10),
  "bias": "BULLISH|BEARISH|NEUTRAL",
  "entry_zone_min": float,
  "entry_zone_max": float,
  "sl": float,
  "tp1": float,
  "tp2": float,
  "rr_tp1": float,
  "rr_tp2": float,
  "reason_h1": "Penjelasan trend H1 dan likuiditas makro...",
  "reason_m15": "Penjelasan struktur, displacement, dan FVG/OB M15...",
  "trigger_m1": "Instruksi trigger di M1...",
  "invalidation": "Setup batal jika harga close di atas/bawah level X...",
  "validity_mins": int (45),
  "reason": "Kesimpulan akhir Bahasa Indonesia (Jika WAIT, jelaskan spesifik kenapa tidak entry)"
}
"""

def decide(symbol: str, ict_h1: dict, ict_m15: dict, ict_m1: dict) -> dict:
    user_payload = {
        "symbol": symbol,
        "H1_Context": ict_h1,
        "M15_Setup": ict_m15,
        "M1_Trigger": ict_m1
    }
    
    try:
        resp = client_groq.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        return {"action": "WAIT", "reason": f"LLM Error: {str(e)}", "confidence": 0}
