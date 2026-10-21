import json, os
from openai import OpenAI

client_groq = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.environ.get("GROQ_API_KEY", ""))
GROQ_MODEL = "openai/gpt-oss-120b"

SYSTEM_PROMPT = """
Kamu adalah "Sniper Analyst" profesional dengan keahlian ICT (Inner Circle Trader).
Tugasmu memberikan setup LIMIT ORDER yang presisi.

FRAMEWORK ANALISIS:
1. Cek "bos_choch" (struktur).
2. Cek "liquidity_summary" (BSL/SSL).
3. Cek "order_blocks_active" dan "fvg_active". 
   PENTING: Cek kolom "MitigatedIndex". Jika isinya null/kosong, berarti POI tersebut BELUM dilewati harga (masih aktif). Jika ada angkanya, berarti POI sudah dilewati (mitigated/tidak valid).
   Pilih POI yang BELUM dimitigasi dan paling dekat dengan "current_price".

ATURAN ENTRY:
- JIKA SELL_LIMIT: Ambil nilai `Top` dari Bearish OB/FVG (OB=-1/FVG=-1) yang belum mitigated.
- JIKA BUY_LIMIT: Ambil nilai `Bottom` dari Bullish OB/FVG (OB=1/FVG=1) yang belum mitigated.
- RR WAJIB minimal 1:2.
- Jika TIDAK ADA sama sekali POI yang belum mitigated di list, WAJIB action = "WAIT".

OUTPUT HARUS JSON VALID (tanpa markdown):
{
  "action": "BUY_LIMIT|SELL_LIMIT|WAIT",
  "setup": "deskripsi singkat",
  "market_condition": "Penjelasan kondisi market",
  "entry": float,
  "sl": float,
  "tp1": float,
  "tp2": float,
  "rr": float,
  "confidence": float (0-1),
  "reason": "alasan lengkap dalam Bahasa Indonesia"
}
"""

def decide(symbol: str, kronos: dict, stats: dict, ict_data: dict, session: dict) -> dict:
    user_payload = {
        "symbol": symbol,
        "kronos_bias": kronos.get("bias"),
        "stats": stats,
        "ict_structure": ict_data,
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
        return {"action": "WAIT", "reason": f"LLM Error: {str(e)}", "confidence": 0, "market_condition": "Gagal menghubungi AI"}
