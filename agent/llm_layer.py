import json, os
import pandas as pd
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY", "")
)

MODEL = "meta-llama/llama-3.3-70b-instruct:free"

SYSTEM_PROMPT = """
Kamu adalah "Sniper Analyst" profesional kelas institusional.
Tugasmu menganalisis market dengan strategi APAPUN (SMC, ICT, Wyckoff, Price Action, Elliott, Supply-Demand, Fibo, Order Block, FVG, dll) — pilihan strategi bebas, TAPI output wajib memenuhi standar eksekusi presisi.

ATURAN EKSEKUSI (SANGAT KETAT):
1. ENTRY SNIPER: Berikan harga entry presisi (Limit Order). Jangan pernah menyarankan Market Order. Entry harus di level yang secara logika bisa memantulkan harga.
2. SL (STOP LOSS): Wajib ada. Letakkan di balik struktur yang menginvalidasi setup.
3. TP (TAKE PROFIT): Wajib ada. Targetkan level probabilitas tinggi berikutnya (liquidity, S/R, dll).
4. RR (RISK:REWARD): WAJIB MINIMAL 1:2. Jika setup yang kamu temukan memiliki RR di bawah 1:2, kamu WAJIB mengembalikan action = "WAIT". Jangan memaksakan entry jika target terlalu dekat.
5. REASON: Jelaskan secara logis dan singkat (Bahasa Indonesia) strategi apa yang kamu gunakan di data ini dan kenapa entry tersebut valid.

OUTPUT HARUS JSON VALID (tanpa markdown, tanpa teks tambahan):
{
  "action": "BUY_LIMIT|SELL_LIMIT|WAIT",
  "entry_price": float,
  "sl": float,
  "tp": float,
  "rr": float,
  "reason": "Alasan spesifik yang mencakup strategi, level S/R/SMC/PA, dan alasan sniper entry"
}
"""

def analyze(df: pd.DataFrame) -> dict:
    # Kirim 50 candle terakhir ke AI untuk dianalisa
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
                
                if risk == 0:
                    return {"action": "WAIT", "reason": "Sistem: SL dan Entry tidak boleh sama."}
                    
                actual_rr = reward / risk
                
                # Kalau AI ngeyel ngasih RR di bawah 1.8, kita bantai jadi WAIT
                if actual_rr < 1.8: 
                    return {
                        "action": "WAIT", 
                        "reason": f"Sistem membatalkan setup karena RR aktual hanya 1:{actual_rr:.2f} (Minimal 1:2). AI terlalu memaksa entry."
                    }
                
                result["rr"] = round(actual_rr, 2)
            else:
                return {"action": "WAIT", "reason": "Sistem: Data Entry, SL, atau TP tidak lengkap."}

        return result
    except Exception as e:
        return {"action": "WAIT", "reason": f"LLM Error: {str(e)}"}
