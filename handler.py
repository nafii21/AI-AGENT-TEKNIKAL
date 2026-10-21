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
        
        if action != "WAIT":
            text = (
                f"⚡ <b>[HERMES AGENT // ACTIVE DESK SETUP: {args.symbol}]</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📌 <i>Setup Trade Baru Terdeteksi!</i>\n\n"
                f"📊 Instrumen: {args.symbol} [{args.tf}]\n"
                f"🎯 Rekomendasi: <b>{emoji} {action}</b>\n"
                f"🏆 Grade: <b>{decision.get('grade', '-')}</b> | Keyakinan: <b>{decision.get('confidence', 0)}/10</b>\n"
                f"📉 Bias: <b>{decision.get('bias', '-')}</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🎯 Zona Entry: <b>{decision.get('entry_zone_min', '-')} - {decision.get('entry_zone_max', '-')}</b>\n"
                f"🛑 SL: <code>{decision.get('sl', '-')}</code>\n"
                f"💎 TP1: <code>{decision.get('tp1', '-')}</code> (RR {decision.get('rr_tp1', '-')})\n"
                f"💎 TP2: <code>{decision.get('tp2', '-')}</code> (RR {decision.get('rr_tp2', '-')})\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🧠 <b>Konteks H1:</b>\n<i>{decision.get('reason_h1', '-')}</i>\n\n"
                f"📊 <b>Konteks {args.tf}:</b>\n<i>{decision.get('reason_m15', '-')}</i>\n\n"
                f"💥 <b>Trigger Entry:</b>\n<i>{decision.get('trigger_m1', '-')}</i>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"⚠️ <b>Invalidasi:</b> {decision.get('invalidation', '-')}\n"
                f"⏱️ <b>Validitas Setup:</b> ~{decision.get('validity_mins', 45)} Menit\n"
                f"💰 <b>Harga Saat Ini:</b> {decision.get('current_price', '-')}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"{decision.get('tracker_msg', '')}\n"
                f"<i>⚠️ Bukan financial advice. Risk max 1%.</i>"
            )
        else:
            text = (
                f"⚪ <b>[HERMES AGENT // NO SETUP]</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📊 Instrumen: <b>{args.symbol}</b> [{args.tf}]\n"
                f"⚡ Status: <b>WAIT / NO TRADE</b>\n"
                f"🏆 Grade: {decision.get('grade', '-')} | Keyakinan: {decision.get('confidence', 0)}/10\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📉 <b>Kondisi Market:</b>\n{decision.get('reason', '-')}\n\n"
                f"{decision.get('tracker_msg', '')}\n"
                f"<i>⚠️ Bukan financial advice. Risk max 1%.</i>"
            )

        df_ohlcv = pd.DataFrame(decision.get("df_ohlcv", []))
        if not df_ohlcv.empty and action != "WAIT":
            chart_file = generate_chart(df_ohlcv, decision, args.symbol, args.tf)
            if chart_file and os.path.exists(chart_file):
                send_tg_photo(chart_file, text)
            else:
                send_tg_message(text)
        else:
            send_tg_message(text)

    except Exception as e:
        send_tg_message(f"❌ Gagal: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
