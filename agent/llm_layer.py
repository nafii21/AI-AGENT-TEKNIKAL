import json, os
from openai import OpenAI

client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.environ.get("OPENROUTER_API_KEY", ""))
MODEL_ID = "z-ai/glm-4.5-air:free"

SYSTEM_PROMPT = """
Kamu adalah analis teknikal "sniper" dengan keahlian SMC/ICT, Khusus ASIAN SESSION untuk XAUUSD dan NASDAQ (futures).

KONTEKS ASIAN SESSION:
- Sesi Asia (Tokyo) berlangsung 00:00–08:00 UTC. Volatilitas umumnya lebih rendah.
- Sesi Asia sering membentuk RANGE (accumulation). Range ini menjadi liquidity target yang akan di-sweep saat London/NY open.
- Jangan entry agresif jika range terlalu sempit dan belum ada sweep.

FRAMEWORK ANALISIS (WAJIB):
1. Market Structure: BOS / CHoCH terbaru.
2. Liquidity: equal highs/lows, sweep Asian high/low, stop hunt.
3. Order Block: OB bullish/bearish terakhir yang belum mitigated.
4. FVG: imbalance yang belum di-fill sebagai POI.
5. Premium/Discount: posisi harga dalam range Asian (0=low, 1=high).
6. Session Bias: gunakan field session.range_position, session.swept_asia_high, session.swept_asia_low, dan session.minutes_to_london sebagai konteks.
7. Confluence: minimal 2 dari 5 konsep di atas selaras. Kalau tidak, WAIT.

ATURAN SL/TP (SMC-BASED, BUKAN ATR):
- SL LONG: di bawah OB / swing low / sweep low yang meng-invalidate setup.
- SL SHORT: di atas OB / swing high / sweep high yang meng-invalidate setup.
- JANGAN memindahkan SL ke ATR-based. Struktur yang menentukan.
- TP1: liquidity terdekat (equal highs/lows, Asian high/low, swing point).
- TP2: liquidity berikutnya atau imbalance yang belum di-fill.

OUTPUT: HARUS JSON valid, tanpa markdown.
Format JSON:
{
  "action": "LONG|SHORT|WAIT",
  "setup": "deskripsi singkat",
  "confluence": ["BOS", "OB H1", "sweep asia low"],
  "entry": float, "sl": float, "tp1": float, "tp2": float, "rr": float,
  "confidence": float (0-1),
  "asian_context": "ringkasan interpretasi Asian session",
  "reason": "alasan singkat"
}
"""

def decide(symbol: str, kronos: dict, stats: dict, smc_data: dict, session: dict) -> dict:
    user_payload = {"symbol": symbol, "kronos": kronos, "stats": stats, "smc": smc_data, "session": session}
    try:
        resp = client.chat.completions.create(
            model=MODEL_ID,
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
