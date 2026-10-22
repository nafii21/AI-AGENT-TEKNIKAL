import os, argparse, httpx, json, pandas as pd
from agent.data import fetch_data
from agent.llm_layer import analyze
from agent.charting import generate_chart
from agent.journal import get_journals, add_journal, get_monthly_stats # Import fungsi baru

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

    # --- FITUR LIHAT JOURNAL & STATISTIK ---
    if args.cmd == "journal":
        rows = get_journals()
        
        # Ambil statistik bulan ini
        stats = get_monthly_stats()
        
        if not rows:
            send_tg("📖 Belum ada catatan journal.")
        else:
            txt = (
                f"📊 <b>PERFORMA BULAN {stats['month'].upper()}</b>\n"
                f"✅ TP Hit: <b>{stats['tp']}</b> kali\n"
                f"❌ SL Hit: <b>{stats['sl']}</b> kali\n"
                f"🎯 Winrate: <b>{stats['winrate']}%</b> (dari {stats['total']} trade)\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📖 <b>5 Catatan Journal Terakhir:</b>\n"
            )
            for r in rows:
                txt += (
                    f"\n📅 {r.get('timestamp', '-')}\n"
                    f"💱 {r.get('symbol', '-')} | {r.get('action', '-')}\n"
                    f"📍 Entry: {r.get('entry', '-')} | SL: {r.get('sl', '-')} | TP: {r.get('tp', '-')}\n"
                    f"🏆 Status: <b>{r.get('result', '-')}</b>\n"
                    f"📝 {r.get('notes', '-')}\n"
                )
            send_tg(txt)
        return

    if not args.symbol or not args.tf:
        send_tg("❌ Parameter Pair atau Timeframe kosong.")
        return

    try:
        df = fetch_data(args.symbol, args.tf)
        current_price = float(df["close"].iloc[-1])
        
        decision = analyze(df)
        action = decision.get("action", "WAIT")
        emoji = "🟢" if action == "BUY_LIMIT" else "🔴" if action == "SELL_LIMIT" else "⚪"
        
        if action != "WAIT":
            entry = decision.get('entry_price', 0)
            sl = decision.get('sl', 0)
            tp = decision.get('tp', 0)
            reason = decision.get('reason', '-')
            
            add_journal(
                symbol=args.symbol,
                action=action,
                entry=entry,
                sl=sl,
                tp=tp,
                result="PENDING",
                notes=reason
            )
            
            text = (
                f"⚡ <b>[HERMES UNIVERSAL SNIPER]</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📊 Pair: <b>{args.symbol}</b> [{args.tf}]\n"
                f"💰 Harga Saat Ini: <code>{current_price}</code>\n"
                f"🎯 Action: <b>{emoji} {action}</b>\n"
                f"📍 Entry: <code>{entry}</code>\n"
                f"🛑 SL: <code>{sl}</code>\n"
                f"💎 TP: <code>{tp}</code>\n"
                f"📊 RR: <b>{decision.get('rr', '-')}</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"💡 <b>Reason:</b>\n{reason}\n"
                f"📝 <i>(Setup otomatis disimpan ke Journal)</i>"
            )
        else:
            text = (
                f"⚪ <b>[HERMES SNIPER - WAIT]</b>\n"
                f"📊 Pair: <b>{args.symbol}</b> [{args.tf}]\n"
                f"💰 Harga Saat Ini: <code>{current_price}</code>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"💡 <b>Reason:</b>\n{decision.get('reason', '-')}\n"
            )

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
