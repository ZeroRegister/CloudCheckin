#!/usr/bin/env python3
"""
Deepflood 自动签到脚本 - 青龙面板适配版
环境变量: DEEPFLOOD_COOKIE (多账号用 & 分隔)
"""
import sys
import os
from curl_cffi import requests
import random
import time

# Get COOKIE from environment variable
cookies = os.environ.get('DEEPFLOOD_COOKIE', '').strip()

if not cookies:
    print("❌ 错误: 环境变量 DEEPFLOOD_COOKIE 未设置")
    sys.exit(1)

# Split multiple cookies by & to form a list
cookie_list = cookies.split('&')

# Request headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0',
    'Origin': 'https://www.deepflood.com',
    'Referer': 'https://www.deepflood.com/board',
    'Content-Type': 'application/json',
}

print(f"🚀 Deepflood 签到开始，共 {len(cookie_list)} 个账号")

# Iterate over multiple account cookies for check-in
for idx, cookie in enumerate(cookie_list):
    print(f"\n📝 正在使用第 {idx+1} 个账号签到...")
    
    # Generate a random delay
    random_delay = random.randint(1, 10)
    print(f"⏳ 等待 {random_delay} 秒...")
    time.sleep(random_delay)

    # Add cookie to headers
    headers['Cookie'] = cookie.strip()
    
    try:
        # random=true means get a random bonus
        url = 'https://www.deepflood.com/api/attendance?random=true'
        response = requests.post(url, headers=headers, impersonate="chrome136")
        
        # Output the status code and response content
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        # Check if the check-in is successful based on the response content
        if response.status_code == 200:
            result = response.json() if response.text else {}
            if result.get('success') or result.get('message', '').find('已签到') >= 0:
                print(f"✅ Deepflood 账号 {idx+1} 签到成功!")
            else:
                print(f"✅ Deepflood 账号 {idx+1} 请求成功: {response.text}")
        else:
            print(f"❌ Deepflood 账号 {idx+1} 签到失败: {response.text}")
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ Deepflood 账号 {idx+1} 签到出错: {e}")
        sys.exit(1)

print("\n🎉 Deepflood 所有账号签到完成!")
