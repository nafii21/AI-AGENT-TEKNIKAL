import os, argparse, httpx, json, traceback
import pandas as pd
from agent.core import analyze_market
from agent.charting import generate_chart
from agent.journal import get_journals

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_tg_message(text):
    if not TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    httpx.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=15)

def send_tg_photo(photo_path, caption):
    if not TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open(photo_path, "rb") as f:
        files = {"photo": f}
        data = {"chat_id": CHAT_ID, "caption": caption, "parse_mode": "HTML"}
        httpx.post(url, data=data, files=files, timeout=30)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol")
    parser.add_argument("--tf")
    parser.add_argument("--cmd")
    parser.add_argument("--args")
    args = parser.parse_args()

    if args.cmd == "journal":
        rows = get_journals()
        if not rows:
            send_tg_message("📖 Belum ada catatan journal.")
        else:
            txt = "📖 <b>5 Catatan Journal Terakhir:</b>\n"
            for r in rows:
                txt += f"\n📅 {r[0]}\n💱 {r[1]} | {r[2]}\n📍 Entry: {r[3]} | SL: {r[4]} | TP: {r[5]}\n🏆 Result: <b>{r[6]}</b>\n📝 {r[7]}\n"
            send_tg_message(txt)
        return

    if not args.symbol or not args.tf:
        send_tg_message("❌ Symbol atau Timeframe tidak valid.")
        return

    send_tg_message(f"⏳ Menganalisa <b>{args.symbol}</b> [{args.tf}]...\nMohon tunggu sebentar.")
    try:
        decision = analyze_market(args.symbol, args.tf)
        if "error" in decision:
            send_tg_message(f"❌ Error: {decision['error']}")
            return

        action = decision.get("action", "WAIT")
        emoji = "🟢" if action == "BUY_LIMIT" else "🔴" if action == "SELL_LIMIT" else "⚪"
        
        # Format Teks
        text = (
            f"{emoji} <b>[HERMES SNIPER // ICT + LIQUIDITY]</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📊 Instrumen: <b>{args.symbol}</b> [{args.tf}]\n"
            f"⚡ Setup: <b>{action}</b>\n"
            f"📍 Entry Limit: <code>{decision.get('entry', '-')}</code>\n"
            f"🛑 SL: <code>{decision.get('sl', '-')}</code>\n"
            f"🎯 TP1: <code>{decision.get('tp1', '-')}</code> | TP2: <code>{decision.get('tp2', '-')}</code>\n"
            f"📊 RR: <b>{decision.get('rr', '-')}</b> | Conf: <b>{decision.get('confidence', 0)*100:.0f}%</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📉 <b>Kondisi Market:</b>\n{decision.get('market_condition', '-')}\n\n"
            f"🧠 <b>Setup:</b> {decision.get('setup', '-')}\n"
            f"💡 <b>Reason:</b> {decision.get('reason', '-')}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{decision.get('tracker_msg', '')}\n"
            f"<i>⚠️ Bukan financial advice. Risk max 1%.</i>"
        )

        # Bikin Chart & Kirim
        df_ohlcv = pd.DataFrame(decision.get("df_ohlcv", []))
        if not df_ohlcv.empty:
            chart_file = generate_chart(df_ohlcv, decision, args.symbol, args.tf)
            if chart_file and os.path.exists(chart_file):
                send_tg_photo(chart_file, text)
            else:
                send_tg_message(text) # Fallback kalau gambar gagal dibuat
        else:
            send_tg_message(text)

    except Exception as e:
        send_tg_message(f"❌ Gagal: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
