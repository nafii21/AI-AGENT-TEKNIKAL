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
Tugasmu menganalisis market dengan strategi APAPUN (SMC, ICT, Wyckoff, Price Action, Elliott, Supply-Demand, Fibo, OB, FVG) dan memberikan setup eksekusi presisi.

ATURAN EKSEKUSI (SANGAT KETAT - BACA DENGAN TELITI):
1. ENTRY SNIPER: Berikan harga entry presisi (Limit Order). Jangan pernah menyarankan Market Order.
2. SL (STOP LOSS) BERDASARKAN LOGIKA STRUKTUR: 
   - Letakkan SL di balik struktur yang menginvalidasi setup (Misal: di atas Swing High terakhir, di bawah Swing Low terakhir, atau di balik zona Order Block).
   - DILARANG KERAS menaruh SL terlalu mepet hanya untuk memperbesar nilai RR. Jarak SL harus logis dan cukup untuk menahan "noise" (pergerakan acak) sesuai time frame.
3. TP (TAKE PROFIT): Targetkan level probabilitas tinggi berikutnya (likuiditas, S/R, dll). TP harus logis, bukan angka asal-asalan.
4. RR (RISK:REWARD): WAJIB MINIMAL 1:2. 
   - Jika setup tidak memenuhi RR 1:2, kembalikan action = "WAIT".
   - Jika RR kamu di atas 1:5, pastikan itu karena TP-nya sangat jauh (di likuiditas besar), BUKAN karena SL-nya terlalu mepet. Jika SL terlalu mepet, lebarkan SL sesuai struktur!
5. REASON: Jelaskan secara logis strategi dan alasan kenapa SL diletakkan di level tersebut (Sebutkan struktur swing/OB-nya).

OUTPUT HARUS JSON VALID (tanpa markdown, tanpa teks tambahan):
{
  "action": "BUY_LIMIT|SELL_LIMIT|WAIT",
  "entry_price": float,
  "sl": float,
  "tp": float,
  "rr": float,
  "reason": "Alasan spesifik (sebutkan strategi, level Entry, dan alasan peletakan SL)"
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
