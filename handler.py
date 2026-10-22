import os, argparse, httpx, json, pandas as pd
from datetime import datetime, timedelta
from agent.data import fetch_data
from agent.llm_layer import analyze
from agent.charting import generate_chart
from agent.journal import get_journals, add_journal, get_monthly_stats, has_active_setup

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_tg(text):
    if TOKEN and CHAT_ID:
        httpx.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=15)

def send_photo(path, caption):
    if TOKEN and CHAT_ID:
        with open(path, "rb") as f:
            httpx.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", data={"chat_id": CHAT_ID, "caption": caption, "parse_mode": "HTML"}, files={"photo": f}, timeout=30)

def to_wib(utc_str):
    """Fungsi buat ngubah jam UTC ke WIB (UTC+7)"""
    try:
        dt_utc = datetime.strptime(utc_str, "%Y-%m-%d %H:%M:%S")
        dt_wib = dt_utc + timedelta(hours=7)
        return dt_wib.strftime("%Y-%m-%d %H:%M WIB")
    except:
        return utc_str

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol")
    parser.add_argument("--tf")
    parser.add_argument("--cmd")
    args = parser.parse_args()

    # --- FITUR LIHAT JOURNAL ---
    if args.cmd == "journal":
        rows = get_journals()
        stats = get_monthly_stats()
        if not rows:
            send_tg("📖 Belum ada catatan journal.")
        else:
            txt = f"📊 <b>PERFORMA BULAN {stats['month'].upper()}</b>\n✅ TP: <b>{stats['tp']}</b> | ❌ SL: <b>{stats['sl']}</b>\n🎯 Winrate: <b>{stats['winrate']}%</b>\n━━━━━━━━━━━━━━━━━━\n📖 <b>5 Catatan Terakhir:</b>\n"
            for r in rows:
                wib_time = to_wib(r.get('timestamp', '-'))
                txt += (
                    f"\n📅 {wib_time}\n"
                    f"💱 {r.get('symbol', '-')} | {r.get('action', '-')}\n"
                    f"📍 Entry: {r.get('entry', '-')} | SL: {r.get('sl', '-')} | TP: {r.get('tp', '-')}\n"
                    f"🏆 Status: <b>{r.get('result', '-')}</b>\n"
                    f"📝 {r.get('notes', '-')[:100]}...\n"
                )
            send_tg(txt)
        return

    # --- FITUR AUTO-SCAN (CRON JOB) ---
    if args.cmd == "cron":
        targets = [("XAUUSD", "M15"), ("NASDAQ", "M15")]
        for symbol, tf in targets:
            if has_active_setup(symbol):
                print(f"[{symbol}] Setup masih PENDING. Skip.")
                continue
            
            try:
                df = fetch_data(symbol, tf)
                decision = analyze(df)
                action = decision.get("action", "WAIT")
                
                if action in ("BUY_LIMIT", "SELL_LIMIT"):
                    entry, sl, tp = decision.get('entry_price', 0), decision.get('sl', 0), decision.get('tp', 0)
                    reason = decision.get('reason', '-')
                    
                    add_journal(symbol, action, entry, sl, tp, "PENDING", reason)
                    
                    emoji = "🟢" if action == "BUY_LIMIT" else "🔴"
                    text = (
                        f"⚡ <b>[AUTO-SCAN HERMES]</b>\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"📊 Pair: <b>{symbol}</b> [{tf}]\n"
                        f"💰 Harga Saat Ini: <code>{float(df['close'].iloc[-1])}</code>\n"
                        f"🎯 Action: <b>{emoji} {action}</b>\n"
                        f"📍 Entry: <code>{entry}</code>\n"
                        f"🛑 SL: <code>{sl}</code>\n"
                        f"💎 TP: <code>{tp}</code>\n"
                        f"📊 RR: <b>{decision.get('rr', '-')}</b>\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"💡 <b>Reason:</b>\n{reason}\n"
                    )
                    chart = generate_chart(df, decision, symbol, tf)
                    if chart and os.path.exists(chart): send_photo(chart, text)
                    else: send_tg(text)
                else:
                    print(f"[{symbol}] WAIT. Notifikasi tidak dikirim.")
            except Exception as e:
                print(f"[{symbol}] Error: {str(e)}")
        return

    # --- FITUR MANUAL (DARI TELEGRAM) ---
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
            entry, sl, tp = decision.get('entry_price', 0), decision.get('sl', 0), decision.get('tp', 0)
            reason = decision.get('reason', '-')
            add_journal(args.symbol, action, entry, sl, tp, "PENDING", reason)
            
            text = (
                f"⚡ <b>[HERMES SNIPER MANUAL]</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📊 Pair: <b>{args.symbol}</b> [{args.tf}]\n"
                f"💰 Harga Saat Ini: <code>{current_price}</code>\n"
                f"🎯 Action: <b>{emoji} {action}</b>\n"
                f"📍 Entry: <code>{entry}</code>\n"
                f"🛑 SL: <code>{sl}</code>\n"
                f"💎 TP: <code>{tp}</code>\n"
                f"📊 RR: <b>{decision.get('rr', '-')}</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"💡 <b>Reason:</b>\n{reason}"
            )
            chart = generate_chart(df, decision, args.symbol, args.tf)
            if chart and os.path.exists(chart): send_photo(chart, text)
            else: send_tg(text)
        else:
            text = (
                f"⚪ <b>[HERMES SNIPER - WAIT]</b>\n"
                f"📊 Pair: <b>{args.symbol}</b> [{args.tf}]\n"
                f"💰 Harga Saat Ini: <code>{current_price}</code>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"💡 <b>Reason:</b>\n{decision.get('reason', '-')}\n"
            )
            send_tg(text)
    except Exception as e:
        send_tg(f"❌ Gagal: {str(e)}")

if __name__ == "__main__":
    main()
