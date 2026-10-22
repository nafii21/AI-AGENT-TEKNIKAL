export default {
  async fetch(request, env, ctx) {
    if (request.method !== "POST") return new Response("OK");
    const body = await request.json();

    // 1. Handle command /start
    if (body.message && body.message.text === "/start") {
      await sendTelegram(env.TELEGRAM_BOT_TOKEN, body.message.chat.id, 
        "🏛️ <b>HERMES Universal Bot</b>\n\nSilakan pilih menu:", getMainMenu());
      return new Response("OK");
    }

    // 2. Handle Tombol (Callback Query)
    if (body.callback_query) {
      const cb = body.callback_query;
      const data = cb.data.split("|");
      const chatId = cb.message.chat.id;

      // Jawab callback biar loading di Telegram ilang
      await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/answerCallbackQuery`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ callback_query_id: cb.id, text: "Memproses..." })
      });

      // Menu 1: Analisa Market
      if (data[0] === "menu" && data[1] === "analisa") {
        await sendTelegram(env.TELEGRAM_BOT_TOKEN, chatId, 
          "Silakan pilih <b>Pair</b> yang ingin dianalisa:", getAssetsKeyboard());
      }
      // Menu 2: Journal
      else if (data[0] === "menu" && data[1] === "journal") {
        await sendTelegram(env.TELEGRAM_BOT_TOKEN, chatId, "⏳ Membuka Journal...");
        await triggerGitHub(env.GITHUB_TOKEN, env.GITHUB_USER, env.GITHUB_REPO, null, null, "journal");
      }
      // Pilih Pair -> Munculin Pilihan Timeframe
      else if (data[0] === "asset") {
        const symbol = data[1];
        await sendTelegram(env.TELEGRAM_BOT_TOKEN, chatId, 
          `Anda memilih <b>${symbol}</b>.\nPilih <b>Timeframe</b>:`, getTFKeyboard(symbol));
      } 
      // Pilih TF -> Tembak GitHub Actions
      else if (data[0] === "tf") {
        const symbol = data[1], tf = data[2];
        await sendTelegram(env.TELEGRAM_BOT_TOKEN, chatId, 
          `⏳ Menganalisa <b>${symbol}</b> [${tf}]...\nMohon tunggu 1-2 menit.`);
        await triggerGitHub(env.GITHUB_TOKEN, env.GITHUB_USER, env.GITHUB_REPO, symbol, tf, null);
      }
      
      return new Response("OK");
    }
    return new Response("OK");
  }
};

// --- FUNGSI BANTUAN ---

async function sendTelegram(token, chatId, text, replyMarkup = null) {
  const payload = { chat_id: chatId, text: text, parse_mode: "HTML" };
  if (replyMarkup) payload.reply_markup = replyMarkup;
  await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload)
  });
}

async function triggerGitHub(token, user, repo, symbol, tf, cmd = null) {
  const inputs = {};
  if (symbol) inputs.symbol = symbol;
  if (tf) inputs.tf = tf;
  if (cmd) inputs.cmd = cmd;

  return await fetch(`https://api.github.com/repos/${user}/${repo}/actions/workflows/agent.yml/dispatches`, {
    method: "POST",
    headers: { 
      "Authorization": `Bearer ${token}`, 
      "Accept": "application/vnd.github+json", 
      "User-Agent": "Cloudflare-Worker" 
    },
    body: JSON.stringify({ ref: "main", inputs: inputs })
  });
}

// --- FUNGSI KEYBOARD TELEGRAM ---

function getMainMenu() {
  return { inline_keyboard: [
    [{ text: "📊 1. Analisa Market", callback_data: "menu|analisa" }, { text: "📖 2. Journal", callback_data: "menu|journal" }]
  ]};
}

function getAssetsKeyboard() {
  return { inline_keyboard: [
    [{ text: "XAUUSD", callback_data: "asset|XAUUSD" }, { text: "EURUSD", callback_data: "asset|EURUSD" }],
    [{ text: "GBPUSD", callback_data: "asset|GBPUSD" }, { text: "USDJPY", callback_data: "asset|USDJPY" }],
    [{ text: "NASDAQ", callback_data: "asset|NASDAQ" }, { text: "BTCUSD", callback_data: "asset|BTCUSD" }]
  ]};
}

function getTFKeyboard(symbol) {
  return { inline_keyboard: [
    [{ text: "M5", callback_data: `tf|${symbol}|M5` }, { text: "M15", callback_data: `tf|${symbol}|M15` }],
    [{ text: "H1", callback_data: `tf|${symbol}|H1` }, { text: "H4", callback_data: `tf|${symbol}|H4` }],
    [{ text: "D1", callback_data: `tf|${symbol}|D1` }]
  ]};
}
