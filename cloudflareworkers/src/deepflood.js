/**
 * DeepFlood Check-in logic
 */

export async function checkInDeepFlood(cookie) {
  if (!cookie) {
    return { success: false, message: "No DEEPFLOOD_COOKIE provided" };
  }

  const now = new Date();
  const utc8Time = new Date(now.getTime() + 8 * 60 * 60 * 1000);
  let summaryMessage = utc8Time.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  }) + " from DeepFlood\n";

  const cookies = cookie.split('&');
  let allSuccess = true;
  let results = [];

  for (let i = 0; i < cookies.length; i++) {
    const singleCookie = cookies[i].trim();
    if (!singleCookie) continue;

    console.log(`🔄 Processing DeepFlood account ${i + 1}...`);

    // Random delay between 1 and 5 seconds to avoid detection but stay within CF limits
    if (i > 0) {
      const delay = Math.floor(Math.random() * 4000) + 1000;
      console.log(`Waiting for ${delay}ms...`);
      await new Promise(resolve => setTimeout(resolve, delay));
    }

    const result = await checkInAccount(singleCookie);
    results.push(result);
    summaryMessage += `Account ${i + 1}: ${result.message}\n`;
    if (!result.success) allSuccess = false;
  }

  return {
    success: allSuccess,
    message: summaryMessage,
    results: results
  };
}

async function checkInAccount(cookie) {
  const headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Content-Type': 'application/json',
    'Origin': 'https://www.deepflood.com',
    'Referer': 'https://www.deepflood.com/board',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
    'Cookie': cookie
  };

  try {
    const url = 'https://www.deepflood.com/api/attendance?random=true';
    const response = await fetch(url, {
      method: 'POST',
      headers: headers
    });

    const responseText = await response.text();

    if (response.status === 200) {
      try {
        const responseData = JSON.parse(responseText);
        let detailMessage = "✅ Success";
        if (responseData.message) {
          detailMessage += ` - ${responseData.message}`;
        }
        return { success: true, message: detailMessage };
      } catch (parseError) {
        return { success: true, message: "✅ Success (raw response)" };
      }
    } else {
      return { success: false, message: `❌ Failed (Status ${response.status}): ${responseText.substring(0, 50)}` };
    }
  } catch (error) {
    return { success: false, message: `💥 Error: ${error.message}` };
  }
}
