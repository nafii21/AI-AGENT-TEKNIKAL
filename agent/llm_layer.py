import json, os
from openai import OpenAI

client_groq = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.environ.get("GROQ_API_KEY", ""))
GROQ_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """
Kamu adalah "Sniper Analyst" profesional dengan keahlian ICT (Inner Circle Trader) dan SMT Divergence.
Tugasmu menganalisa market dan memberikan setup LIMIT ORDER (Buy Limit / Sell Limit) yang presisi.

FRAMEWORK ANALISIS:
1. Market Structure (ICT): BOS (Break of Structure) dan CHoCH (Change of Character). Tentukan bias arah (Bullish/Bearish).
2. Liquidity: Cari sweep liquidity (stop hunt) di swing high/low.
3. POI (Point of Interest): Gunakan Order Block (OB) atau Fair Value Gap (FVG) yang belum mitigated sebagai area entry limit.
4. SMT Divergence: Bandingkan XAUUSD dengan XAGUSD. Jika ada divergence, itu sinyal kuat reversal.
5. DXY (Dollar Index): Jika DXY menguat (bullish_usd), tekan XAUUSD (bearish). Jika DXY melemah, dukung XAUUSD (bullish).

ATURAN ENTRY:
- Gunakan LIMIT ORDER (Buy Limit jika bias Bullish, Sell Limit jika bias Bearish).
- Entry diletakkan di OB atau FVG yang valid.
- SL diletakkan di balik swing high/low yang menginvalidasi setup.
- TP1 diletakkan di liquidity terdekat.
- RR (Risk:Reward) WAJIB minimal 1:2. Jika setup memungkinkan RR lebih besar (misal 1:3 atau 1:4), silakan gunakan.
- Jika tidak ada setup yang memenuhi kriteria, berikan action = "WAIT".

OUTPUT HARUS JSON VALID (tanpa markdown):
{
  "action": "BUY_LIMIT|SELL_LIMIT|WAIT",
  "setup": "deskripsi singkat setup ICT",
  "entry": float,
  "sl": float,
  "tp1": float,
  "tp2": float (opsional, isi 0 jika tidak ada),
  "rr": float,
  "confidence": float (0-1),
  "reason": "alasan lengkap dalam Bahasa Indonesia yang mencakup struktur ICT, SMT, dan DXY"
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
        return {"action": "WAIT", "reason": f"LLM Error: {str(e)}", "confidence": 0}
