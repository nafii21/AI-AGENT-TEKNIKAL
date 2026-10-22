import os, argparse, httpx, json, pandas as pd
from agent.core import analyze_market
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
    parser.add_argument("--bias_tf")
    parser.add_argument("--setup_tf")
    parser.add_argument("--cmd")
    args = parser.parse_args()

    if args.cmd == "journal":
        rows = get_journals()
        send_tg("📖 Belum ada journal." if not rows else "📖 <b>Journal:</b> (Data ada)")
        return

    if not args.symbol or not args.bias_tf or not args.setup_tf:
        send_tg("❌ Parameter tidak lengkap.")
        return

    try:
        decision = analyze_market(args.symbol, args.bias_tf, args.setup_tf)
        if "error" in decision:
            send_tg(f"❌ Error: {decision['error']}")
            return

        action = decision.get("action", "WAIT")
        emoji = "🟢" if action == "BUY_LIMIT" else "🔴" if action == "SELL_LIMIT" else "⚪"
        current_price = decision.get("current_price", "-")
        
        if action != "WAIT":
            text = (
                f"⚡ <b>[HERMES MSNR SNIPER]</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📊 Pair: <b>{args.symbol}</b>\n"
                f"🧭 Bias: {args.bias_tf} | Setup: {args.setup_tf}\n"
                f"💰 Harga Saat Ini: <code>{current_price}</code>\n"
                f"🎯 Action: <b>{emoji} {action}</b>\n"
                f"📍 Entry: <code>{decision.get('entry_price', '-')}</code>\n"
                f"🛑 SL: <code>{decision.get('sl', '-')}</code>\n"
                f"💎 TP1: <code>{decision.get('tp1', '-')}</code> | TP2: <code>{decision.get('tp2', '-')}</code>\n"
                f"📊 RR: <b>{decision.get('rr', '-')}</b> | Conf: <b>{decision.get('confidence', 0)}/10</b>\n"
                f"💡 <b>Reason:</b>\n{decision.get('reason', '-')}\n"
            )
        else:
            text = (
                f"⚪ <b>[HERMES MSNR SNIPER - WAIT]</b>\n"
                f"📊 Pair: <b>{args.symbol}</b>\n"
                f"🧭 Bias: {args.bias_tf} | Setup: {args.setup_tf}\n"
                f"💰 Harga Saat Ini: <code>{current_price}</code>\n"
                f"💡 {decision.get('reason', '-')}"
            )

        df_ohlcv = pd.DataFrame(decision.get("df_ohlcv", []))
        if not df_ohlcv.empty and action != "WAIT":
            chart = generate_chart(df_ohlcv, decision, args.symbol, args.setup_tf)
            if chart and os.path.exists(chart): send_photo(chart, text)
            else: send_tg(text)
        else:
            send_tg(text)

    except Exception as e:
        send_tg(f"❌ Gagal: {str(e)}")

if __name__ == "__main__":
    main()
