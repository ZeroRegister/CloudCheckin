/**
 * Telegram Notification logic
 */

export async function sendTelegramNotification(token, chatId, text) {
  if (!token || !chatId) {
    console.log("⚠️ Telegram token or chat ID not provided, skipping notification.");
    return;
  }

  const url = `https://api.telegram.org/bot${token}/sendMessage`;

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        chat_id: chatId,
        text: text,
        parse_mode: 'HTML'
      })
    });

    const result = await response.json();
    if (!result.ok) {
      console.error(`❌ Telegram notification failed: ${result.description}`);
    } else {
      console.log("✅ Telegram notification sent successfully.");
    }
  } catch (error) {
    console.error(`💥 Error sending Telegram notification: ${error.message}`);
  }
}
