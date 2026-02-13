import { checkInNodeSeek } from './nodeseek.js';
import { checkInDeepFlood } from './deepflood.js';
import { sendTelegramNotification } from './telegram.js';

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (url.pathname === '/checkin') {
      const results = await runAllCheckins(env);
      return new Response(JSON.stringify(results), {
        headers: { "Content-Type": "application/json" }
      });
    }

    return new Response("Check-in worker is running. Use /checkin to trigger manually.");
  },

  async scheduled(event, env, ctx) {
    console.log("⏰ Scheduled check-in trigger started");
    await runAllCheckins(env);
    console.log("✅ Scheduled check-in trigger finished");
  }
};

async function runAllCheckins(env) {
  const reports = [];
  let summaryText = "<b>🚀 CloudCheckin Report</b>\n\n";

  // 1. NodeSeek
  console.log("Starting NodeSeek check-in...");
  const nsResult = await checkInNodeSeek(env.NODESEEK_COOKIE);
  reports.push({ site: 'NodeSeek', ...nsResult });
  summaryText += nsResult.message + "\n";

  // 2. DeepFlood
  console.log("Starting DeepFlood check-in...");
  const dfResult = await checkInDeepFlood(env.DEEPFLOOD_COOKIE);
  reports.push({ site: 'DeepFlood', ...dfResult });
  summaryText += dfResult.message + "\n";

  // Send notification
  console.log("Sending Telegram notification...");
  await sendTelegramNotification(
    env.TELEGRAM_TOKEN,
    env.TELEGRAM_CHAT_ID,
    summaryText
  );

  return {
    time: new Date().toISOString(),
    results: reports
  };
}
