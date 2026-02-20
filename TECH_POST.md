# [技术] Github Actions + Telegram Bot 实现 Nodeseek + Deepflood 自动签到与通知

解放双手，从自动化签到开始。本文将介绍如何利用 Github Actions 的免费计算资源，配合 Python 脚本和 Telegram Bot，实现 **Nodeseek** 和 **Deepflood** 的每日自动签到，并实时推送签到结果（包含今日奖励及余额）到你的手机。

**项目地址**: [ZeroRegister/CloudCheckin](https://github.com/ZeroRegister/CloudCheckin) (欢迎 Fork & Star)

## 🌟 特性

*   **零成本**: 完全利用 Github Actions 免费额度，无需购买服务器。
*   **高成功率**: 针对 Nodeseek 和 Deepflood 的反爬机制（如 Cloudflare 验证），使用了 `curl_cffi` 模拟真实浏览器指纹（Chrome 136），大幅提高签到成功率。
*   **多账号支持**: 支持同时配置多个账号，批量签到。
*   **实时通知**: 签到结果（成功/重复/失败）直接推送到 Telegram，并显示 Nodeseek 的**今日奖励**及**当前总鸡腿数**。
*   **智能容错**: 即使手动签到过，脚本也会优雅处理，不会报错中断。
*   **隐私安全**: 所有敏感信息（Cookie、Token）均存储在 Github Secrets 中，代码中不包含任何个人数据。

## 🚀 快速开始

只需简单几步，即可拥有你自己的自动签到机器人。

### 第一步：Fork 项目

1.  访问项目仓库：[ZeroRegister/CloudCheckin](https://github.com/ZeroRegister/CloudCheckin)
2.  点击右上角的 **Fork** 按钮，将仓库复制到你自己的 Github 账号下。

### 第二步：准备 Telegram Bot (用于接收通知)

如果你还没有 Bot，请按以下步骤获取：

1.  **获取 Token**: 在 Telegram 中搜索 `@BotFather`，发送 `/newbot`，按提示创建机器人。完成后你会获得一串 **API Token**（例如 `123456:ABC-DEF...`）。
2.  **获取 Chat ID**: 在 Telegram 中搜索 `@userinfobot`，点击开始，它会返回你的 **Id**（一串数字，例如 `123456789`）。
3.  **激活机器人**: **重要！** 在 Telegram 中找到你刚才创建的机器人，随便发一条消息（如 `hello`）给它，否则它无法主动给你发消息。

### 第三步：配置 Github Secrets

为了保护你的 Cookie 不被泄露，我们需要将其配置在仓库的 Secrets 中。

1.  进入你 Fork 后的仓库页面。
2.  点击 **Settings** -> 左侧边栏 **Secrets and variables** -> **Actions**。
3.  点击 **New repository secret**，依次添加以下 4 个变量：

| Secret Name | 说明 | 示例值 |
| :--- | :--- | :--- |
| `NODESEEK_COOKIE` | Nodeseek 的 Cookie | `如果你有多个账号，用 & 分隔` |
| `DEEPFLOOD_COOKIE` | Deepflood 的 Cookie | `user1_cookie&user2_cookie` |
| `TELEGRAM_TOKEN` | 刚才获取的 Bot Token | `123456:ABC-DEF...` |
| `TELEGRAM_CHAT_ID` | 刚才获取的数字 ID | `123456789` |

> **如何获取 Cookie?**
> 在浏览器打开对应网站，按 `F12` 打开开发者工具，刷新页面，在 `Network` 标签页找到第一个请求，复制 `Request Headers` 中的 `Cookie` 值即可。

### 第四步：启用 Github Actions

1.  点击仓库顶部的 **Actions** 选项卡。
2.  由于是 Fork 的仓库，Actions 默认可能被禁用，请点击绿色按钮 **I understand my workflows, go ahead and enable them**。
3.  在左侧选择 **Auto Check-in (NodeSeek & DeepFlood)**。
4.  点击右侧的 **Run workflow** -> **Run workflow** 按钮进行首次手动测试。

如果配置正确，你的 Telegram 马上就会收到签到结果推送！🎉

## ⚙️ 进阶配置

### 修改签到时间

默认签到时间为 **北京时间每天早上 8:05**。
如果你想修改时间，可以编辑 `.github/workflows/checkin.yml` 文件：

```yaml
on:
  schedule:
    # 每天 UTC 时间 0:05 运行 (即北京时间 8:05)
    - cron: '5 0 * * *'
```

### 查看日志

如果签到失败，可以在 Actions 页面点击对应的运行记录，查看详细日志排查问题。

## 🛠️ 技术实现细节

本项目使用了以下核心技术栈：

*   **Python 3.10**: 脚本语言。
*   **curl_cffi**: 关键库。用于模拟浏览器 TLS 指纹，绕过 Cloudflare 等反爬验证。
*   **Github Actions**: CI/CD 平台，作为免费的定时任务调度器。

### 核心逻辑展示 (以 Nodeseek 为例)

```python
# 使用 curl_cffi 模拟 Chrome 136 指纹，防止被识别为机器人
response = requests.post(
    'https://www.nodeseek.com/api/attendance?random=true',
    headers=headers,
    impersonate="chrome136"
)

# 智能判断响应结果
if response.status_code == 200:
    # 签到成功，尝试获取奖励信息
    ...
elif "请勿重复操作" in response.text:
    # 优雅处理重复签到，不报错
    info_message = "今日已签到"
    ...
```

---

如果你觉得这个项目对你有帮助，欢迎点个 **Star** ⭐️ 支持一下！
如有问题，欢迎提 Issue 反馈。
