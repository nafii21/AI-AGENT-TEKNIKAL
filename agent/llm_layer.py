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
2. SL (STOP LOSS) BERDASARKAN VOLATILITAS & STRUKTUR:
   - Letakkan SL di balik struktur (Swing High/Low, OB).
   - DILARANG KERAS menaruh SL terlalu mepet hanya untuk memperbesar RR.
   - WAJIB hitung jarak aman (buffer) berdasarkan VOLATILITAS harga. 
   - Patokan Buffer: Lihat rata-rata ukuran body candle (Open-Close) dari 5-10 candle terakhir. Tambahkan minimal 1.5x dari rata-rata ukuran candle tersebut sebagai jarak aman dari struktur terluar.
   - Jika asetnya sangat volatil (seperti BTC, atau harga di atas 10.000), SL harus jauh lebih lebar. Jika aset tenang (seperti EURUSD), SL bisa lebih tipis.
3. TP (TAKE PROFIT): Targetkan level probabilitas tinggi berikutnya (likuiditas, S/R).
4. RR (RISK:REWARD): WAJIB MINIMAL 1:2. Jika tidak memenuhi, kembalikan action = "WAIT". Jika RR di atas 1:5, pastikan TP-nya memang sangat jauh, BUKAN karena SL-nya terlalu mepet.
5. REASON (WAJIB BAHASA INDONESIA): Jelaskan secara logis dan profesional dalam BAHASA INDONESIA. Sebutkan alasan mengapa SL diletakkan di level tersebut berdasarkan struktur dan volatilitas candle.

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
                
                # Cek dinamis: Kalau harga di atas 10.000 (seperti BTC), jarak SL minimal 50 poin.
                # Kalau harga di bawah 10.000 (Gold, Forex), minimal 5 poin.
                min_risk = 50.0 if entry > 10000 else 5.0
                
                if risk < min_risk:
                     return {
                        "action": "WAIT", 
                        "reason": f"Sistem menolak setup: Jarak SL ({risk:.2f}) terlalu mepet untuk aset dengan harga {entry}. Rawan kena noise."
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
