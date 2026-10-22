import json, os
import pandas as pd
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY", "")
)

MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"

SYSTEM_PROMPT = """
Kamu adalah "Sniper Analyst" profesional kelas institusional.
Tugasmu menganalisis market dengan strategi APAPUN (SMC, ICT, Wyckoff, Price Action, Supply-Demand, Fibo, Order Block, FVG) dan memberikan setup eksekusi presisi.

ATURAN EKSEKUSI (SANGAT KETAT):
1. ENTRY SNIPER: Berikan harga entry presisi (Limit Order).
2. SL (STOP LOSS) & BUFFER: 
   - Letakkan SL di balik struktur (Swing High/Low, OB).
   - DILARANG KERAS menaruh SL terlalu mepet hanya untuk memperbesar RR.
   - WAJIB TAMBAHKAN BUFFER (jarak aman) minimal 15-20 poin (untuk XAUUSD) atau 10-15 pips (untuk Forex) dari titik struktur terluar. Ini untuk menghindari jebakan "noise" dan spread broker.
3. TP (TAKE PROFIT): Targetkan level probabilitas tinggi berikutnya (likuiditas, S/R).
4. RR (RISK:REWARD): WAJIB MINIMAL 1:2. Jika tidak memenuhi, kembalikan action = "WAIT".
5. REASON (WAJIB BAHASA INDONESIA): Jelaskan secara logis, profesional, dan jelas dalam BAHASA INDONESIA. Jelaskan strategi apa yang dipakai, kenapa Entry di situ, dan sebutkan struktur mana yang dijadikan acuan peletakan SL.

OUTPUT HARUS JSON VALID (tanpa markdown, tanpa teks tambahan):
{
  "action": "BUY_LIMIT|SELL_LIMIT|WAIT",
  "entry_price": float,
  "sl": float,
  "tp": float,
  "rr": float,
  "reason": "Alasan dalam Bahasa Indonesia (Sebutkan struktur dan buffer SL)"
}
"""

def analyze(df: pd.DataFrame) -> dict:
    data_json = df.tail(50).to_dict(orient="records")
    
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(data_json, ensure_ascii=False, default=str)},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        result = json.loads(resp.choices[0].message.content)
        
        # --- SATPAM MATEMATIKA (Anti-Halusinasi AI) ---
        if result.get("action") not in ("BUY_LIMIT", "SELL_LIMIT", "WAIT"):
            return {"action": "WAIT", "reason": "Sistem: Format action dari AI tidak valid."}

        if result.get("action") in ("BUY_LIMIT", "SELL_LIMIT"):
            entry = result.get("entry_price", 0)
            sl = result.get("sl", 0)
            tp = result.get("tp", 0)
            
            if entry and sl and tp:
                risk = abs(entry - sl)
                reward = abs(tp - entry)
                
                # Cek jarak SL minimal (misal buat XAUUSD jangan sampe di bawah 5 poin)
                # Biar bener-bener aman dari noise, kita set minimal 5 poin.
                if risk < 5.0 and risk > 0:
                     return {
                        "action": "WAIT", 
                        "reason": f"Sistem menolak setup: Jarak SL terlalu mepet ({risk:.2f} poin). Rawan terkena noise."
                    }
                
                if risk == 0:
                    return {"action": "WAIT", "reason": "Sistem: SL dan Entry tidak boleh sama."}
                    
                actual_rr = reward / risk
                
                if actual_rr < 1.8: 
                    return {
                        "action": "WAIT", 
                        "reason": f"Sistem membatalkan: RR aktual hanya 1:{actual_rr:.2f} (Minimal 1:2)."
                    }
                
                result["rr"] = round(actual_rr, 2)
            else:
                return {"action": "WAIT", "reason": "Sistem: Data Entry, SL, atau TP tidak lengkap."}

        return result
    except Exception as e:
        return {"action": "WAIT", "reason": f"LLM Error: {str(e)}"}
