export default {
  async fetch(request, env, ctx) {
    if (request.method !== "POST") return new Response("OK");
    const body = await request.json();

    if (body.message && body.message.text === "/start") {
      await sendTelegram(env.TELEGRAM_BOT_TOKEN, body.message.chat.id, 
        "🏛️ <b>HERMES MSNR Sniper</b>\n\nSilakan pilih menu:", getMainMenu());
      return new Response("OK");
    }

    if (body.callback_query) {
      const cb = body.callback_query;
      const data = cb.data.split("|");
      const chatId = cb.message.chat.id;

      await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/answerCallbackQuery`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ callback_query_id: cb.id, text: "Memproses..." })
      });

      // 1. Menu Analisa -> Munculin Pilihan Pair
      if (data[0] === "menu" && data[1] === "analisa") {
        await sendTelegram(env.TELEGRAM_BOT_TOKEN, chatId, 
          "Pilih <b>Pair</b> yang ingin dianalisa:", getPairsKeyboard());
      }
      // 2. Pilih Pair -> Munculin Pilihan Bias
      else if (data[0] === "pair") {
        const symbol = data[1];
        await sendTelegram(env.TELEGRAM_BOT_TOKEN, chatId, 
          `Anda memilih <b>${symbol}</b>.\nPilih <b>Timeframe Bias</b>:`, getBiasKeyboard(symbol));
      }
      // 3. Pilih Bias -> Tembak GitHub
      else if (data[0] === "bias") {
        const symbol = data[1];
        const biasTF = data[2]; 
        let setupTF = "";
        if (biasTF === "H4") setupTF = "M15";
        if (biasTF === "H1") setupTF = "M5";
        if (biasTF === "M15") setupTF = "M1";

        await sendTelegram(env.TELEGRAM_BOT_TOKEN, chatId, 
          `⏳ Menganalisa <b>${symbol}</b> | Bias: <b>${biasTF}</b> | Setup: <b>${setupTF}</b>...\nMohon tunggu.`);
        
        await triggerGitHub(env.GITHUB_TOKEN, env.GITHUB_USER, env.GITHUB_REPO, symbol, biasTF, setupTF);
      }
      else if (data[0] === "menu" && data[1] === "journal") {
        await sendTelegram(env.TELEGRAM_BOT_TOKEN, chatId, "⏳ Membuka Journal...");
        await triggerGitHub(env.GITHUB_TOKEN, env.GITHUB_USER, env.GITHUB_REPO, null, null, null, "journal");
      }
      return new Response("OK");
    }
    return new Response("OK");
  }
};

async function sendTelegram(token, chatId, text, replyMarkup = null) {
  const payload = { chat_id: chatId, text: text, parse_mode: "HTML" };
  if (replyMarkup) payload.reply_markup = replyMarkup;
  await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload)
  });
}

async function triggerGitHub(token, user, repo, symbol, bias_tf, setup_tf, cmd = null) {
  const inputs = {};
  if (symbol) inputs.symbol = symbol;
  if (bias_tf) inputs.bias_tf = bias_tf;
  if (setup_tf) inputs.setup_tf = setup_tf;
  if (cmd) inputs.cmd = cmd;

  return await fetch(`https://api.github.com/repos/${user}/${repo}/actions/workflows/agent.yml/dispatches`, {
    method: "POST",
    headers: { "Authorization": `Bearer ${token}`, "Accept": "application/vnd.github+json", "User-Agent": "Cloudflare" },
    body: JSON.stringify({ ref: "main", inputs: inputs })
  });
}

function getMainMenu() {
  return { inline_keyboard: [
    [{ text: "📊 1. Analisa Market", callback_data: "menu|analisa" }, { text: "📖 2. Journal", callback_data: "menu|journal" }]
  ]};
}

function getPairsKeyboard() {
  return { inline_keyboard: [
    [{ text: "XAUUSD", callback_data: "pair|XAUUSD" }, { text: "GBPUSD", callback_data: "pair|GBPUSD" }],
    [{ text: "USDJPY", callback_data: "pair|USDJPY" }, { text: "BTCUSD", callback_data: "pair|BTCUSD" }]
  ]};
}

function getBiasKeyboard(symbol) {
  return { inline_keyboard: [
    [{ text: "Bias H4 (Setup M15)", callback_data: `bias|${symbol}|H4` }],
    [{ text: "Bias H1 (Setup M5)", callback_data: `bias|${symbol}|H1` }],
    [{ text: "Bias M15 (Setup M1)", callback_data: `bias|${symbol}|M15` }]
  ]};
}
