import json, os
from openai import OpenAI

client_groq = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.environ.get("GROQ_API_KEY", ""))
GROQ_MODEL = "openai/gpt-oss-120b"

SYSTEM_PROMPT = """
Kamu adalah "Sniper Analyst" profesional dengan keahlian ICT (Inner Circle Trader) dan Liquidity.
Tugasmu menganalisa market dan memberikan setup LIMIT ORDER (Buy Limit / Sell Limit) yang presisi.

FRAMEWORK ANALISIS:
1. Market Structure (ICT): Cek data "bos_choch". Jika BOS=1 (Bullish), BOS=-1 (Bearish). Jika "bos_choch" kosong, cek "recent_swings" untuk melihat struktur terakhir.
2. Liquidity (BSL/SSL): Cek "liquidity_summary". Jika kosong, cek "recent_swings" (HighLow=1 adalah BSL, HighLow=-1 adalah SSL).
3. POI (Point of Interest): Cek "order_blocks_active" (OB=1 adalah Bullish OB, OB=-1 adalah Bearish OB) dan "fvg_active" (FVG=1 Bullish FVG, FVG=-1 Bearish FVG).
4. SMT Divergence: (BONUS). Jika ada divergence, tambah confidence. Jika tidak ada, tetap cari setup.
5. USD Bias (DXY): "usd_menguat" (bearish aset), "usd_melemah" (bullish aset).

ATURAN ENTRY (SANGAT PENTING):
- Gunakan LIMIT ORDER (Buy Limit/Sell Limit) di area OB atau FVG.
- SL di balik swing yang menginvalidasi setup.
- TP1 di likuiditas terdekat.
- RR (Risk:Reward) WAJIB minimal 1:2.
- Setup VALID jika minimal memenuhi 2 syarat: Ada Struktur (BOS/CHoCH dari recent_swings) DAN Ada POI (OB/FVG). Sweep likuiditas adalah nilai tambah yang kuat.
- Jika tidak ada struktur, tidak ada POI, atau RR kurang dari 1:2, WAJIB action = "WAIT".

OUTPUT HARUS JSON VALID (tanpa markdown):
{
  "action": "BUY_LIMIT|SELL_LIMIT|WAIT",
  "setup": "deskripsi singkat setup ICT",
  "market_condition": "Penjelasan kondisi market saat ini. Jika WAIT, jelaskan kenapa.",
  "entry": float,
  "sl": float,
  "tp1": float,
  "tp2": float (isi 0 jika tidak ada),
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
