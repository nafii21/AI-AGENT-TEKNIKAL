import os, argparse, httpx, json, traceback
import pandas as pd
from agent.core import analyze_market
from agent.charting import generate_chart
from agent.journal import get_journals

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def clean_html(text):
    # Ngebersihin karakter < dan > biar ga dianggap tag HTML sama Telegram
    if not text: return "-"
    return str(text).replace("<", "&lt;").replace(">", "&gt;")

def send_tg_message(text):
    if not TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    # Telegram max 4096 karakter per pesan
    if len(text) > 4000:
        text = text[:4000] + "\n\n<i>(Pesan dipotong karena terlalu panjang)</i>"
        
    try:
        resp = httpx.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=15)
        if not resp.is_success:
            print(f"Telegram Error (Message): {resp.text}")
    except Exception as e:
        print(f"Gagal kirim pesan: {e}")

def send_tg_photo(photo_path, caption):
    if not TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    
    # Telegram max 1024 karakter untuk caption gambar
    if len(caption) > 1000:
        # Kalau caption kepanjangan, kirim gambar tanpa teks, lalu kirim teksnya terpisah
        safe_caption = "📊 <b>Chart Analysis</b>\n<i>(Detail teks menyusul di pesan bawah)</i>"
    else:
        safe_caption = caption

    try:
        with open(photo_path, "rb") as f:
            files = {"photo": f}
            data = {"chat_id": CHAT_ID, "caption": safe_caption, "parse_mode": "HTML"}
            resp = httpx.post(url, data=data, files=files, timeout=30)
            
            if not resp.is_success:
                print(f"Telegram Error (Photo): {resp.text}")
                # Fallback kirim teks aja kalau gambar gagal
                send_tg_message(caption)
                return
    except Exception as e:
        print(f"Gagal kirim foto: {e}")
        send_tg_message(caption)
        return

    # Kalau caption tadi dipotong, kirim sisa teksnya
    if len(caption) > 1000:
        send_tg_message(caption)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol")
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

    if not args.symbol:
        send_tg_message("❌ Symbol tidak valid.")
        return

    try:
        decision = analyze_market(args.symbol)
        if "error" in decision:
            send_tg_message(f"❌ Error: {clean_html(decision['error'])}")
            return

        action = decision.get("action", "WAIT")
        emoji = "🟢" if action == "BUY_LIMIT" else "🔴" if action == "SELL_LIMIT" else "⚪"
        
        # Bersihin output dari AI pakai clean_html
        reason = clean_html(decision.get('reason', '-'))
        reason_h1 = clean_html(decision.get('reason_h1', '-'))
        reason_m15 = clean_html(decision.get('reason_m15', '-'))
        trigger_m1 = clean_html(decision.get('trigger_m1', '-'))
        invalidation = clean_html(decision.get('invalidation', '-'))

        if action != "WAIT":
            text = (
                f"⚡ <b>[HERMES AGENT // ACTIVE DESK SETUP: {args.symbol}]</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📌 <i>Setup Trade Sedang AKTIF & VALID di desk.</i>\n\n"
                f"📊 Instrumen: {args.symbol} [MTF]\n"
                f"🎯 Rekomendasi: <b>{emoji} {action}</b>\n"
                f"🏆 Grade: <b>{decision.get('grade', '-')}</b> | Keyakinan: <b>{decision.get('confidence', 0)}/10</b>\n"
                f"📉 Bias: <b>{decision.get('bias', '-')}</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🎯 POI Dipantau: <b>{decision.get('entry_zone_min', '-')} - {decision.get('entry_zone_max', '-')}</b>\n"
                f"🛑 SL: <code>{decision.get('sl', '-')}</code>\n"
                f"💎 TP1: <code>{decision.get('tp1', '-')}</code> (RR {decision.get('rr_tp1', '-')})\n"
                f"💎 TP2: <code>{decision.get('tp2', '-')}</code> (RR {decision.get('rr_tp2', '-')})\n"
                f"⏳ Status Live: <b>PENDING POI (STANDBY ENTRY)</b>\n"
                f"💰 Harga Saat Ini: {decision.get('current_price', '-')}\n"
                f"⏱️ Sisa Validitas Setup: ~{decision.get('validity_mins', 45)} Menit\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🧠 <b>Konteks H1:</b>\n<i>{reason_h1}</i>\n\n"
                f"📊 <b>Konteks M15:</b>\n<i>{reason_m15}</i>\n\n"
                f"💥 <b>Pemicu Entri (Trigger M1):</b>\n<i>{trigger_m1}</i>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"⚠️ <b>Invalidasi:</b> {invalidation}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"{decision.get('tracker_msg', '')}\n"
                f"<i>⚠️ Bukan financial advice. Risk max 1%.</i>"
            )
        else:
            text = (
                f"⚪ <b>[HERMES AGENT // NO SETUP REPORT: {args.symbol}]</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📊 Instrumen: <b>{args.symbol}</b> [MTF]\n"
                f"⚡ Status: <b>WAIT / NO TRADE</b>\n"
                f"🏆 Grade: {decision.get('grade', '-')} | Keyakinan: {decision.get('confidence', 0)}/10\n"
                f"📉 Bias H1: <b>{decision.get('bias', '-')}</b>\n"
                f"💰 Harga Saat Ini: <b>{decision.get('current_price', '-')}</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🔍 <b>Kenapa Tidak Entry?</b>\n"
                f"{reason}\n\n"
                f"🧠 <b>Audit H1 (Makro):</b>\n"
                f"<i>{reason_h1}</i>\n\n"
                f"📊 <b>Audit M15 (Setup):</b>\n"
                f"<i>{reason_m15}</i>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"<i>Garis Biru = BSL | Garis Oranye = SSL</i>\n"
                f"{decision.get('tracker_msg', '')}\n"
                f"<i>⚠️ Bot sedang mengawasi market. Tunggu setup Grade A berikutnya.</i>"
            )

        df_ohlcv = pd.DataFrame(decision.get("df_ohlcv", []))
        if not df_ohlcv.empty:
            chart_file = generate_chart(df_ohlcv, decision, args.symbol, "M15")
            if chart_file and os.path.exists(chart_file):
                send_tg_photo(chart_file, text)
            else:
                send_tg_message(text)
        else:
            send_tg_message(text)

    except Exception as e:
        send_tg_message(f"❌ Gagal: {clean_html(str(e))}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
