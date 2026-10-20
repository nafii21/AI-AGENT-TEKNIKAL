import os, argparse, httpx, json, traceback
from agent.core import analyze_market

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_tg(text):
    if not TOKEN or not CHAT_ID:
        print("Missing TG Token/Chat ID")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        httpx.post(url, json=payload, timeout=15)
    except Exception as e:
        print(f"Failed to send TG: {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--tf", required=True)
    args = parser.parse_args()

    # Kirim pesan loading
    send_tg(f"⏳ Menganalisa <b>{args.symbol}</b> [{args.tf}]...\nMohon tunggu sebentar, AI sedang bekerja.")

    try:
        decision = analyze_market(args.symbol, args.tf)
        
        if "error" in decision:
            send_tg(f"❌ Error: {decision['error']}")
            return

        action = decision.get("action", "WAIT")
        if action == "LONG":
            emoji = "🟢 BUY"
        elif action == "SHORT":
            emoji = "🔴 SELL"
        else:
            emoji = "⚪ WAIT / NO TRADE"
        
        confluence = decision.get('confluence', [])
        conf_str = ", ".join(confluence) if isinstance(confluence, list) else str(confluence)

        text = (
            f"⚡ <b>[HERMES AGENT // SMC AUDIT]</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📊 Instrumen: <b>{args.symbol}</b> [{args.tf}]\n"
            f"⚡ Rekomendasi: <b>{emoji}</b>\n"
            f"📍 Entry: <code>{decision.get('entry', '-')}</code>\n"
            f"🛑 SL: <code>{decision.get('sl', '-')}</code>\n"
            f"🎯 TP1: <code>{decision.get('tp1', '-')}</code> | TP2: <code>{decision.get('tp2', '-')}</code>\n"
            f"📊 RR: <b>{decision.get('rr', '-')}</b> | Conf: <b>{decision.get('confidence', 0)*100:.0f}%</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🧠 <b>Confluence:</b> {conf_str}\n"
            f"📝 <b>Setup:</b> {decision.get('setup', '-')}\n"
            f"🌏 <b>Context:</b> {decision.get('asian_context', '-')}\n"
            f"💡 <b>Reason:</b> {decision.get('reason', '-')}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"<i>⚠️ Bukan financial advice. Risk max 1%.</i>"
        )
        send_tg(text)
    except Exception as e:
        send_tg(f"❌ Gagal: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
