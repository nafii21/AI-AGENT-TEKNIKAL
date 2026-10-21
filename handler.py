import os, argparse, httpx, json, traceback, sys
from agent.core import analyze_market
from agent.journal import add_journal, get_journals

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_tg(text):
    if not TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    httpx.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=15)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", help="Symbol (XAUUSD/NASDAQ)")
    parser.add_argument("--tf", help="Timeframe")
    parser.add_argument("--cmd", help="Command (journal/addjournal)")
    parser.add_argument("--args", help="Argument tambahan (JSON string)")
    args = parser.parse_args()

    if args.cmd == "journal":
        rows = get_journals()
        if not rows:
            send_tg("📖 Belum ada catatan journal.")
        else:
            txt = "📖 <b>5 Catatan Journal Terakhir:</b>\n"
            for r in rows:
                txt += f"\n📅 {r[0]}\n💱 {r[1]} | {r[2]}\n📍 Entry: {r[3]} | SL: {r[4]} | TP: {r[5]}\n🏆 Result: <b>{r[6]}</b>\n📝 {r[7]}\n"
            send_tg(txt)
        return

    if args.cmd == "addjournal":
        data = json.loads(args.args)
        add_journal(data["symbol"], data["action"], data["entry"], data["sl"], data["tp"], data["result"], data["notes"])
        send_tg("✅ Journal berhasil disimpan!")
        return

    # --- Eksekusi Analisa Market ---
    if not args.symbol or not args.tf:
        send_tg("❌ Symbol atau Timeframe tidak valid.")
        return

    send_tg(f"⏳ Menganalisa <b>{args.symbol}</b> [{args.tf}]...\nMohon tunggu sebentar.")
    try:
        decision = analyze_market(args.symbol, args.tf)
        if "error" in decision:
            send_tg(f"❌ Error: {decision['error']}")
            return

        action = decision.get("action", "WAIT")
        emoji = "🟢" if action == "BUY_LIMIT" else "🔴" if action == "SELL_LIMIT" else "⚪"
        
        text = (
            f"{emoji} <b>[HERMES SNIPER // ICT + SMT + DXY]</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📊 Instrumen: <b>{args.symbol}</b> [{args.tf}]\n"
            f"⚡ Setup: <b>{action}</b>\n"
            f"📍 Entry Limit: <code>{decision.get('entry', '-')}</code>\n"
            f"🛑 SL: <code>{decision.get('sl', '-')}</code>\n"
            f"🎯 TP1: <code>{decision.get('tp1', '-')}</code> | TP2: <code>{decision.get('tp2', '-')}</code>\n"
            f"📊 RR: <b>{decision.get('rr', '-')}</b> | Conf: <b>{decision.get('confidence', 0)*100:.0f}%</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🧠 <b>ICT/SMT:</b> {decision.get('setup', '-')}\n"
            f"💡 <b>Reason:</b> {decision.get('reason', '-')}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{decision.get('tracker_msg', '')}\n"
            f"<i>⚠️ Bukan financial advice. Risk max 1%.</i>"
        )
        send_tg(text)
    except Exception as e:
        send_tg(f"❌ Gagal: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
