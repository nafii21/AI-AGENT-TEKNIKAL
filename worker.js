export default {
  async fetch(request, env, ctx) {
    if (request.method !== "POST") return new Response("OK");
    const body = await request.json();

    if (body.message && body.message.text === "/start") {
      await sendTelegram(env.TELEGRAM_BOT_TOKEN, body.message.chat.id, 
        "🏛️ <b>HERMES Terminal Analyst</b>\n\nSilakan pilih aset:", getAssetsKeyboard());
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

      if (data[0] === "asset") {
        await sendTelegram(env.TELEGRAM_BOT_TOKEN, chatId, 
          `Anda memilih <b>${data[1]}</b>. Pilih Timeframe:`, getTimeframeKeyboard(data[1]));
      } 
      else if (data[0] === "tf") {
        const symbol = data[1], tf = data[2];
        await sendTelegram(env.TELEGRAM_BOT_TOKEN, chatId, 
          `⏳ Menghubungi GitHub Actions untuk menganalisa ${symbol} [${tf}]...\nMohon tunggu 1-2 menit.`);
        
        try {
          const ghResponse = await triggerGitHub(env.GITHUB_TOKEN, env.GITHUB_USER, env.GITHUB_REPO, symbol, tf);
          if (!ghResponse.ok) {
             const errText = await ghResponse.text();
             await sendTelegram(env.TELEGRAM_BOT_TOKEN, chatId, `❌ <b>Gagal nembak GitHub:</b>\nStatus: ${ghResponse.status}\nPesan: ${errText}`);
          }
        } catch (err) {
          await sendTelegram(env.TELEGRAM_BOT_TOKEN, chatId, `❌ <b>Error Sistem:</b>\n${err.message}`);
        }
      }
      else if (data[0] === "cmd") {
        const cmd = data[1];
        await sendTelegram(env.TELEGRAM_BOT_TOKEN, chatId, `⏳ Memproses perintah ${cmd}...`);
        await triggerGitHub(env.GITHUB_TOKEN, env.GITHUB_USER, env.GITHUB_REPO, null, null, cmd);
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

async function triggerGitHub(token, user, repo, symbol, tf, cmd = null, args = null) {
  const inputs = {};
  if (cmd) inputs.cmd = cmd;
  if (args) inputs.args = JSON.stringify(args);
  if (symbol) inputs.symbol = symbol;
  if (tf) inputs.tf = tf;

  return await fetch(`https://api.github.com/repos/${user}/${repo}/actions/workflows/agent.yml/dispatches`, {
    method: "POST",
    headers: { "Authorization": `Bearer ${token}`, "Accept": "application/vnd.github+json", "User-Agent": "Cloudflare" },
    body: JSON.stringify({ 
      ref: "main", 
      inputs: inputs 
    })
  });
}

function getAssetsKeyboard() {
  return { 
    inline_keyboard: [
      [{ text: "XAUUSD", callback_data: "asset|XAUUSD" }, { text: "NASDAQ", callback_data: "asset|NASDAQ" }],
      [{ text: "GBPUSD", callback_data: "asset|GBPUSD" }, { text: "USDJPY", callback_data: "asset|USDJPY" }],
      [{ text: "📖 Lihat Journal", callback_data: "cmd|journal" }]
    ] 
  };
}

function getTimeframeKeyboard(symbol) {
  return {
    inline_keyboard: [
      [{ text: "M15", callback_data: `tf|${symbol}|M15` }, { text: "H1", callback_data: `tf|${symbol}|H1` }],
      [{ text: "H4", callback_data: `tf|${symbol}|H4` }, { text: "D1", callback_data: `tf|${symbol}|D1` }]
    ]
  };
}
