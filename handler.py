import os, argparse, httpx, json, pandas as pd
from agent.data import fetch_data
from agent.llm_layer import analyze
from agent.charting import generate_chart
from agent.journal import get_journals

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_tg(text):
    if TOKEN and CHAT_ID:
        httpx.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=15)

def send_photo(path, caption):
    if TOKEN and CHAT_ID:
        with open(path, "rb") as f:
            httpx.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", data={"chat_id": CHAT_ID, "caption": caption, "parse_mode": "HTML"}, files={"photo": f}, timeout=30)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol")
    parser.add_argument("--tf")
    parser.add_argument("--cmd")
    args = parser.parse_args()

    if args.cmd == "journal":
        rows = get_journals()
        send_tg("📖 Belum ada journal." if not rows else "📖 <b>Journal:</b> Fitur dalam pengembangan.")
        return

    if not args.symbol or not args.tf:
        send_tg("❌ Parameter Pair atau Timeframe kosong.")
        return

    try:
        # 1. Ambil Data
        df = fetch_data(args.symbol, args.tf)
        current_price = float(df["close"].iloc[-1])
        
        # 2. Analisa AI (OpenRouter)
        decision = analyze(df)
        
        action = decision.get("action", "WAIT")
        emoji = "🟢" if action == "BUY_LIMIT" else "🔴" if action == "SELL_LIMIT" else "⚪"
        
        # 3. Format Pesan
        if action != "WAIT":
            text = (
                f"⚡ <b>[HERMES UNIVERSAL SNIPER]</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📊 Pair: <b>{args.symbol}</b> [{args.tf}]\n"
                f"💰 Harga Saat Ini: <code>{current_price}</code>\n"
                f"🎯 Action: <b>{emoji} {action}</b>\n"
                f"📍 Entry: <code>{decision.get('entry_price', '-')}</code>\n"
                f"🛑 SL: <code>{decision.get('sl', '-')}</code>\n"
                f"💎 TP: <code>{decision.get('tp', '-')}</code>\n"
                f"📊 RR: <b>{decision.get('rr', '-')}</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"💡 <b>Reason:</b>\n{decision.get('reason', '-')}\n"
            )
        else:
            text = (
                f"⚪ <b>[HERMES SNIPER - WAIT]</b>\n"
                f"📊 Pair: <b>{args.symbol}</b> [{args.tf}]\n"
                f"💰 Harga Saat Ini: <code>{current_price}</code>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"💡 <b>Reason:</b>\n{decision.get('reason', '-')}\n"
            )

        # 4. Bikin Chart & Kirim
        if action != "WAIT":
            chart = generate_chart(df, decision, args.symbol, args.tf)
            if chart and os.path.exists(chart): send_photo(chart, text)
            else: send_tg(text)
        else:
            send_tg(text)

    except Exception as e:
        send_tg(f"❌ Gagal: {str(e)}")

if __name__ == "__main__":
    main()
