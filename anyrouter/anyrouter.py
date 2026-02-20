import sys
import os
import json
import random
import time
import asyncio
from curl_cffi import requests
from dotenv import load_dotenv
from telegram.notify import send_tg_notification

load_dotenv()

# --- Configuration ---
BASE_URL = 'https://anyrouter.top'
LOGIN_URL = f'{BASE_URL}/login'
USER_INFO_URL = f'{BASE_URL}/api/user/self'
CHECKIN_URL = f'{BASE_URL}/api/user/sign_in'
CONSOLE_URL = f'{BASE_URL}/console'

WAF_COOKIE_NAMES = ['acw_tc', 'cdn_sec_tc', 'acw_sc__v2']

BROWSER_ARGS = [
    '--disable-blink-features=AutomationControlled',
    '--disable-dev-shm-usage',
    '--no-sandbox',
]

USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/138.0.0.0 Safari/537.36'
)


async def get_waf_cookies():
    """Use Playwright to obtain WAF cookies by visiting the login page."""
    from playwright.async_api import async_playwright

    browser = None
    context = None

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=BROWSER_ARGS,
            )
            context = await browser.new_context(
                user_agent=USER_AGENT,
                viewport={'width': 1920, 'height': 1080},
            )
            page = await context.new_page()

            await page.goto(LOGIN_URL, wait_until='networkidle')
            try:
                await page.wait_for_function(
                    'document.readyState === "complete"', timeout=5000
                )
            except Exception:
                await page.wait_for_timeout(3000)

            cookies = await context.cookies()
            waf_cookies = {}
            for cookie in cookies:
                if cookie['name'] in WAF_COOKIE_NAMES:
                    waf_cookies[cookie['name']] = cookie['value']

            missing = [c for c in WAF_COOKIE_NAMES if c not in waf_cookies]
            if missing:
                raise RuntimeError(f"Missing WAF cookies: {missing}")

            return waf_cookies

    finally:
        if context:
            try:
                await context.close()
            except Exception:
                pass
        if browser:
            try:
                await browser.close()
            except Exception:
                pass


def parse_cookies(cookies_data):
    """Parse cookies from string or dict format."""
    if isinstance(cookies_data, dict):
        return cookies_data
    if isinstance(cookies_data, str):
        cookies_dict = {}
        for cookie in cookies_data.split(';'):
            if '=' not in cookie:
                continue
            key, value = cookie.strip().split('=', 1)
            cookies_dict[key] = value
        return cookies_dict
    return {}


def do_checkin(account_info, idx, waf_cookies):
    """Execute check-in for a single account."""
    cookies_data = account_info.get('cookies', '')
    api_user = account_info.get('api_user', '')
    account_name = account_info.get('name', f'Account {idx + 1}')

    if not api_user:
        raise ValueError(f"{account_name}: api_user is missing")

    # Build cookie string: WAF cookies + user session cookies
    waf_cookie_str = '; '.join(f'{k}={v}' for k, v in waf_cookies.items())
    if isinstance(cookies_data, dict):
        user_cookie_str = '; '.join(f'{k}={v}' for k, v in cookies_data.items())
    else:
        user_cookie_str = str(cookies_data)
    full_cookie = f'{waf_cookie_str}; {user_cookie_str}'.strip('; ')

    headers = {
        'User-Agent': USER_AGENT,
        'Referer': CONSOLE_URL,
        'Origin': BASE_URL,
        'new-api-user': api_user,
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Cookie': full_cookie,
    }

    # Step 1: Get user info (optional, for display)
    try:
        info_resp = requests.get(
            USER_INFO_URL,
            headers=headers,
            impersonate="chrome136",
            timeout=30,
        )
        if info_resp.status_code == 200:
            info_data = info_resp.json()
            if info_data.get('success'):
                user_data = info_data.get('data', {})
                quota = round(user_data.get('quota', 0) / 500000, 2)
                used = round(user_data.get('used_quota', 0) / 500000, 2)
                print(f"{account_name} quota: ${quota}, used: ${used}", flush=True)
    except Exception as e:
        print(f"{account_name} failed to get user info: {e}", flush=True)

    # Step 2: Execute check-in
    checkin_headers = headers.copy()
    checkin_headers['Content-Type'] = 'application/json'
    checkin_headers['X-Requested-With'] = 'XMLHttpRequest'

    response = requests.post(
        CHECKIN_URL,
        headers=checkin_headers,
        impersonate="chrome136",
        timeout=30,
    )

    print(f"{account_name} Status Code: {response.status_code}", flush=True)
    print(f"{account_name} Response: {response.text}", flush=True)

    if response.status_code != 200:
        return False, f"check-in failed, HTTP {response.status_code}"

    # Parse response
    try:
        result = response.json()
        if result.get('ret') == 1 or result.get('code') == 0 or result.get('success'):
            return True, "check-in successful"
        error_msg = result.get('msg', result.get('message', 'unknown error'))
        return False, f"check-in failed: {error_msg}"
    except json.JSONDecodeError:
        if 'success' in response.text.lower():
            return True, "check-in successful"
        return False, f"check-in failed, invalid response: {response.text[:200]}"


def main():
    # Load accounts from environment variable (JSON array)
    accounts_json = os.environ.get('ANYROUTER_ACCOUNTS', '').strip()
    if not accounts_json:
        raise ValueError("Environment variable ANYROUTER_ACCOUNTS is not set")

    accounts = json.loads(accounts_json)
    if not isinstance(accounts, list) or len(accounts) == 0:
        raise ValueError("ANYROUTER_ACCOUNTS must be a non-empty JSON array")

    # Validate accounts
    for i, acc in enumerate(accounts):
        if not acc.get('api_user'):
            raise ValueError(f"Account {i + 1}: 'api_user' field is required")
        if not acc.get('cookies'):
            raise ValueError(f"Account {i + 1}: 'cookies' field is required")

    # Get WAF cookies once (shared across all accounts)
    print("Obtaining WAF cookies via Playwright...", flush=True)
    waf_cookies = asyncio.run(get_waf_cookies())
    print(f"WAF cookies obtained: {list(waf_cookies.keys())}", flush=True)

    # Process each account
    for idx, account in enumerate(accounts):
        account_name = account.get('name', f'Account {idx + 1}')
        print(f"Processing {account_name}...", flush=True)

        random_delay = random.randint(1, 10)
        print(f"{account_name} waiting {random_delay}s...", flush=True)
        time.sleep(random_delay)

        try:
            success, message = do_checkin(account, idx, waf_cookies)
            msg = f"ANYROUTER {account_name} {message}"
            print(msg, flush=True)
            send_tg_notification(msg)
            if not success:
                sys.exit(1)
        except Exception as e:
            error_msg = f"ANYROUTER {account_name} error: {e}"
            print(error_msg, flush=True)
            send_tg_notification(error_msg)
            sys.exit(1)


if __name__ == '__main__':
    main()
