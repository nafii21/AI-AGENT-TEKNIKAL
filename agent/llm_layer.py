import json, os
from openai import OpenAI

client_groq = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.environ.get("GROQ_API_KEY", ""))
GROQ_MODEL = "openai/gpt-oss-120b"

SYSTEM_PROMPT = """
Kamu adalah "Sniper Analyst" profesional dengan keahlian ICT (Inner Circle Trader) dan Liquidity.
Tugasmu menganalisa market dan memberikan setup LIMIT ORDER (Buy Limit / Sell Limit) yang presisi.

FRAMEWORK ANALISIS:
1. Market Structure (ICT): BOS dan CHoCH. Tentukan bias arah (WAJIB).
2. Liquidity (BSL/SSL): Cek "liquidity_summary". Apakah Buy-Side Liquidity (BSL) di atas atau Sell-Side Liquidity (SSL) di bawah sudah di-sweep? (WAJIB).
3. POI (Point of Interest): Gunakan Order Block (OB) atau FVG yang belum mitigated sebagai area entry (WAJIB).
4. SMT Divergence: Bandingkan Main Asset dengan SMT Asset. (BONUS KONFLUEN). Jika ada divergence, ini menambah validitas setup. NAMUN, TIDAK ADANYA SMT BUKAN ALASAN UNTUK MENOLAK SETUP JIKA STRUKTUR ICT & LIQUIDITY SUDAH BAGUS.
5. USD Bias (DXY): Gunakan field "usd_bias_dxy". Jika "usd_menguat", tekan aset (bearish). Jika "usd_melemah", dukung aset (bullish). (KONFLUEN TAMBAHAN).

ATURAN ENTRY (SANGAT PENTING):
- Gunakan LIMIT ORDER (Buy Limit/Sell Limit) di area OB atau FVG.
- SL di balik swing yang menginvalidasi setup.
- TP1 di likuiditas terdekat (cek field liquidity_summary).
- RR (Risk:Reward) WAJIB minimal 1:2.
- Setup dianggap VALID dan boleh diberikan jika minimal memenuhi 3 syarat utama: Struktur (BOS/CHoCH) + Sweep Liquidity + POI (OB/FVG). SMT hanya nilai tambah (bonus confidence).
- Jika tidak ada Sweep likuiditas, struktur berantakan, atau RR kurang dari 1:2, WAJIB action = "WAIT".

OUTPUT HARUS JSON VALID (tanpa markdown):
{
  "action": "BUY_LIMIT|SELL_LIMIT|WAIT",
  "setup": "deskripsi singkat setup ICT (misal: Sweep SSL + OB H1)",
  "market_condition": "Penjelasan detail kondisi market SAAT INI. Jika WAIT, jelaskan kenapa. Jika ENTRY, jelaskan konfirmasinya.",
  "entry": float,
  "sl": float,
  "tp1": float,
  "tp2": float (isi 0 jika tidak ada),
  "rr": float,
  "confidence": float (0-1),
  "reason": "alasan lengkap dalam Bahasa Indonesia mengenai struktur, likuiditas, SMT, dan DXY"
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
