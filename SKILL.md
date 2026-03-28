---
name: web3-trader
version: 1.0.3
description: DEX swap 交易技能。当用户提到 swap、兑换、卖出、买入、换成 USDT、交易 ETH、DEX 交易、代币兑换、token swap、sell ETH、buy USDT、交易代币等关键词时激活。通过 Antalpha AI DEX 聚合器查询价格、获取最优路由、生成交易数据。支持 MetaMask/OKX/Trust/TokenPocket 四大钱包。零托管，私钥不离开用户钱包。
metadata: {"openclaw":{"requires":{"bins":["python3"]},"mcp":{"antalpha-swap":{"url":"https://mcp-skills.ai.antalpha.com/mcp","tools":["swap-quote","swap-create-page","swap-tokens","swap-gas","swap-full"]}},"persistence":{"path":"~/.web3-trader/"},"security_notes":["本 Skill 仅生成交易数据，绝不接触私钥","用户必须在自己的钱包中审核并签名交易","交易涉及风险（滑点、Gas 波动）— 请只用闲钱交易"]}}
---

# Web3 Trader Skill

> **Zero Custody · AI Agent Native · Multi-Wallet · Cyberpunk UI**
>
> 由 Antalpha AI 提供聚合交易支持

---

## 两种运行模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| 🌐 **MCP 远程模式**（推荐） | 通过 Antalpha MCP Server 调用，服务端报价 + 页面托管 | 生产环境，无需本地配置 API Key |
| 🖥️ **本地 CLI 模式** | 通过 Python CLI 本地调用 0x API | 开发调试，离线环境 |

---

## MCP 远程模式（v1.0.1 新增）

### MCP Server 地址

```
https://mcp-skills.ai.antalpha.com/mcp
```

### 可用 MCP Tools

| Tool | 说明 |
|------|------|
| `swap-quote` | DEX 聚合报价（无 taker = 询价；有 taker = 含完整 tx data） |
| `swap-create-page` | 生成赛博朋克 Swap 页面（服务端托管，返回 preview_url） |
| `swap-tokens` | 支持的代币列表（可按符号/名称搜索） |
| `swap-gas` | 当前 Gas 价格 |
| `swap-full` | **一站式**：报价 + 生成页面 + 托管（单次调用，推荐） |

### Agent 工作流（MCP 模式，推荐）

```
用户: "帮我把 0.1 ETH 换成 USDT"
      │
      ▼
┌─ Agent 调用 MCP swap-full ─────────────────┐
│  sell_token=ETH, buy_token=USDT,            │
│  sell_amount=0.1, taker=0xUserWallet        │
│  → 返回 quote + preview_url + tx           │
└────────────┬───────────────────────────────┘
             │  (单次调用，服务端完成报价+页面生成+托管)
             ▼
┌─ Agent 发送消息给用户 ─────────────────────┐
│  交易预览 + preview_url 链接               │
│  🤖 由 Antalpha AI 提供聚合交易支持         │
└────────────┬───────────────────────────────┘
             │
             ▼
┌─ 用户点链接 ───────────────────────────────┐
│  打开 Antalpha 托管页 → 选择钱包            │
│  → 钱包内自动弹出签名 → 交易上链            │
└────────────────────────────────────────────┘
```

**相比 v1.0.0 的改进：**
- ~~5 步~~ → **1 次 MCP 调用 + 1 次消息发送**
- 无需本地生成 HTML / 上传到 Litterbox / 生成 QR 码
- Swap 页面托管在 `mcp-skills.ai.antalpha.com` 可信域名下
- Agent 无需配置 0x API Key（服务端统一管理）

### swap-full 调用示例

```json
{
  "tool": "swap-full",
  "arguments": {
    "sell_token": "ETH",
    "buy_token": "USDT",
    "sell_amount": "0.1",
    "taker": "0x81f9c401B0821B6E0a16BC7B1dF0F647F36211Dd"
  }
}
```

返回：
```json
{
  "quote": {
    "sell_token": "ETH",
    "buy_token": "USDT",
    "sell_amount": "0.1",
    "buy_amount": "198.12",
    "min_buy_amount": "196.14",
    "price": "1981.22",
    "route": [{"source": "Blackhole_CL", "proportion": "100.0%"}]
  },
  "swap_page": {
    "preview_url": "https://mcp-skills.ai.antalpha.com/web3-trader/preview/<id>",
    "wallets_supported": ["MetaMask", "OKX Web3", "Trust Wallet", "TokenPocket"]
  },
  "tx": { "to": "0x000...734", "value": "100000000000000000", "data": "0x..." }
}
```

### Agent 行为规则

1. **不说废话** — 不输出任何过程性旁白（如"上下文恢复完毕"、"先读 SKILL.md"、"MCP 远程模式调用中"等）。用户只需要看到交易预览结果。
2. **生成 QR 码** — 拿到 `preview_url` 后，用 `qrcode` 库生成 QR 码 PNG 图片，作为附件发送给用户，方便手机扫码。
3. **一条消息搞定** — 交易预览文字 + QR 码图片在同一条消息中发出。

### QR 码生成流程

```python
import qrcode
qr = qrcode.QRCode(box_size=10, border=3)
qr.add_data(preview_url)  # 从 swap-full 返回值获取
qr.make(fit=True)
img = qr.make_image(fill_color='#00ffaa', back_color='#0a0e14')
img.save('/tmp/swap_qr.png')
```

生成后将 QR 码图片复制到 `~/.openclaw/workspace/` 发送，发送后删除临时文件。

### 消息模板（MCP 模式）

```
⚡ <FROM> → <TO> Swap 交易预览

📊 <from_amount> <from_token> → ~<to_amount> <to_token>
💰 价格：1 <from_token> ≈ $<price>
🛡️ 最低获得：<min_buy_amount> <to_token>
⛓️ 网络：Ethereum Mainnet
🛣️ 路由：<route_source> (<proportion>)
👛 钱包：<wallet_short>

🔥 支持钱包：MetaMask | OKX Web3 | Trust Wallet | TokenPocket

📱 点击链接或扫描二维码，选择钱包确认交易：
🔗 <preview_url>
🤖 由 Antalpha AI 提供聚合交易支持
```

**⚠️ 强制规则：**
- 最后一行 `🤖 由 Antalpha AI 提供聚合交易支持` **必须包含**，不可省略
- `preview_url` 直接从 swap-full 返回值获取，无需额外处理
- **QR 码图片必须附带发送**，方便手机扫码
- **不输出任何过程性旁白**，只发交易预览

---

## 功能概览

| 能力 | 说明 |
|------|------|
| 💱 价格查询 | 实时查询任意 Token 对的 DEX 聚合价格 |
| 🛣️ 路由优化 | 获取最优 Swap 路由（自动拆单到多个 DEX） |
| 📦 交易构建 | 生成完整的链上交易数据（to/value/data/gas） |
| 🌐 Swap 托管页 | 赛博朋克风格 HTML，MCP 模式由服务端托管 |
| 📱 QR 码 | 根据 MCP 返回的 preview_url 生成 QR 码图片，随消息发送 |
| 🔗 EIP-681 | 导出标准 EIP-681 支付链接 |
| ⛽ Gas 查询 | 获取当前 Gas 价格 |

## 支持的钱包

| 钱包 | Deeplink 协议 | 状态 |
|------|--------------|------|
| 🦊 MetaMask | `metamask.app.link/dapp/` | ✅ 已验证 |
| 💎 OKX Web3 | `okx://wallet/dapp/details?dappUrl=` | ✅ 已验证 |
| 🛡️ Trust Wallet | `link.trustwallet.com/open_url?coin_id=60&url=` | ✅ 已验证 |
| 📱 TokenPocket | `tpdapp://open?params=` | ✅ 已验证 |

## 支持的 Token（Ethereum Mainnet）

| 类型 | Token |
|------|-------|
| 稳定币 | USDT, USDC, DAI |
| 原生/包装 | ETH, WETH, WBTC |
| DeFi | LINK, UNI |

---

## Quick Start

```bash
# 1. 配置 API key
cp references/config.example.yaml ~/.web3-trader/config.yaml
# 编辑填入你的 API key

# 2. 安装依赖
pip install requests web3 qrcode pillow

# 3. 查询价格
python3 scripts/trader_cli.py price --from ETH --to USDT --amount 0.001

# 4. 生成 Swap 托管页
python3 scripts/trader_cli.py swap-page --from ETH --to USDT --amount 0.001 \
  --wallet 0xYourWallet -o /tmp/swap.html --json
```

## CLI 命令

| 命令 | 说明 |
|------|------|
| `price --from <token> --to <token> --amount <n>` | 查询价格 |
| `route --from <token> --to <token> --amount <n>` | 获取最优路由 |
| `build-tx --from --to --amount --wallet <addr>` | 构建交易数据 |
| `export --from --to --amount --wallet <addr>` | 导出 EIP-681 链接 |
| `swap-page --from --to --amount --wallet <addr> -o <file> [--url <url>]` | 生成 Swap 托管页 + QR 码 |
| `gas` | 查询 Gas 价格 |
| `tokens` | 列出支持的 Token |

所有命令支持 `--json` 输出机器可读格式。

---

## Agent 工作流（本地 CLI 模式，备用）

> ⚠️ **推荐使用 MCP 远程模式**（见上方），以下本地流程仅作为 MCP 不可用时的降级方案。

### Step 1: 生成 Swap 页面

```bash
python3 scripts/trader_cli.py swap-page \
  --from ETH --to USDT --amount 0.001 \
  --wallet 0xUserWalletAddress \
  -o /tmp/swap.html --json
```

### Step 2: 上传到托管服务

```bash
SWAP_URL=$(curl -s -F "reqtype=fileupload" -F "time=72h" \
  -F "fileToUpload=@/tmp/swap.html" \
  https://litterbox.catbox.moe/resources/internals/api.php)
```

### Step 3: 生成 QR 码

```python
import qrcode
qr = qrcode.QRCode(box_size=10, border=3)
qr.add_data(SWAP_URL)
qr.make(fit=True)
img = qr.make_image(fill_color='#00ffaa', back_color='#0a0e14')
img.save('/tmp/swap_qr.png')
```

### Step 4: 发送交易预览（同 MCP 模式消息模板）

---

## Swap 托管页技术细节

### UI 风格
- **赛博朋克/代码风格**：深色背景 + Matrix 数字雨动画
- **字体**：系统 monospace（SF Mono / Menlo / Consolas）
- **配色**：Cyan `#00ffaa` + Purple `#a855f7` + Deep Black `#0a0e14`
- **动效**：顶部扫描线、脉冲呼吸灯、矩阵雨背景

### 行为逻辑
- **普通浏览器打开**：显示四个钱包选择按钮（MetaMask/OKX/Trust/TP）
- **钱包内置浏览器打开**：检测到 `window.ethereum` 后，2 秒倒计时自动触发 `eth_sendTransaction`，直接弹出签名界面
- **自动链切换**：调用 `wallet_switchEthereumChain` 确保在 Ethereum Mainnet

### 自包含
- 零外部依赖（无 CDN、无 Google Fonts）
- 单个 HTML 文件，可离线打开
- 所有交易数据内嵌在 `<script>` 中

---

## 配置文件

```yaml
# ~/.web3-trader/config.yaml
api_keys:
  zeroex: "YOUR_API_KEY"        # Antalpha AI API key
chains:
  default: ethereum              # 默认链
risk:
  max_slippage: 0.5              # 最大滑点 0.5%
  max_amount_usdt: 10000         # 单笔最大金额（USDT 计）
```

## 架构图（MCP 模式）

```
┌──────────────────┐     MCP JSON-RPC     ┌────────────────────────────────┐
│   AI Agent       │ ────────────────────► │  Antalpha MCP Server           │
│   (OpenClaw)     │  swap-full            │  mcp-skills.ai.antalpha.com    │
│                  │ ◄──────────────────── │                                │
│                  │  quote + preview_url   │  ┌─ 0x API ──── DEX 聚合报价  │
└────────┬─────────┘                       │  ├─ Page Gen ── 赛博朋克 HTML  │
         │                                 │  └─ Hosting ─── 页面托管+URL   │
         │ 发送 preview_url                └────────────┬───────────────────┘
         ▼                                              │
┌──────────────────┐   点链接/扫码    ┌─────────────────┘
│   用户 (手机/PC)  │ ──────────────► │
└──────────────────┘                  ▼
                             ┌───────────────────────┐
                             │  Swap 托管页            │
                             │  (赛博朋克 UI)          │
                             │  自动检测钱包环境        │
                             └──────────┬────────────┘
                                        │ eth_sendTransaction
                                        ▼
                             ┌───────────────────────┐
                             │  钱包 App              │
                             │  MetaMask/OKX/Trust/TP │
                             │  签名 + 广播            │
                             └───────────────────────┘
```

## 安全模型

| 层级 | 保障 |
|------|------|
| 私钥 | **零接触** — Skill 不持有、不传输、不存储任何私钥 |
| 交易数据 | 由 0x Protocol 生成，包含 MEV 保护（anti-sandwich） |
| 滑点 | 可配置最大滑点（默认 0.5%），`minBuyAmount` 链上强制执行 |
| 审核 | 用户在钱包中看到完整交易详情后才签名 |
| 托管页 | 自包含 HTML，无后端通信，无 cookie，无追踪 |

## 依赖

```
requests>=2.28.0    # HTTP 客户端
web3>=6.0.0         # Web3 工具（地址校验等）
qrcode>=7.0         # QR 码生成
pillow>=9.0         # QR 码图片渲染
```

## 文件结构

```
web3-trader/
├── SKILL.md                    # 本文件 — Skill 说明
├── README.md                   # 项目概述
├── MCP_REQUIREMENTS.md         # MCP 托管服务需求文档
├── requirements.txt            # Python 依赖
├── install.sh                  # 安装脚本
├── LICENSE                     # MIT License
├── scripts/
│   ├── trader_cli.py           # CLI 主入口
│   ├── zeroex_client.py        # Antalpha AI API 客户端
│   └── swap_page_gen.py        # Swap 托管页生成器（赛博朋克 UI）
├── references/
│   ├── config.example.yaml     # 配置文件模板
│   ├── ANTALPHA_MCP_SERVER_SPEC.md  # Antalpha MCP 服务规格
│   └── SECURITY.md             # 安全说明
├── examples/
│   └── swap_usdt_eth.py        # 示例脚本
└── tests/
    └── test_zeroex_client.py   # 单元测试
```

## 版本历史

### v1.0.3 (2026-03-28)
- ✅ **修复技能注册失败**：metadata 从多行 YAML 改为 single-line JSON（符合 OpenClaw 解析要求）
- ✅ **移除 ZEROEX_API_KEY 硬性依赖**：MCP 模式不需要本地 API Key，requires.env 不再声明它，避免 load-time 被过滤
- ✅ **description 关键词增强**：覆盖 swap/兑换/卖出/买入/sell/buy/DEX 等触发词，提升意图匹配命中率

### v1.0.2 (2026-03-27)
- ✅ **Agent 行为优化**：不输出过程性旁白，用户只看到交易预览结果
- ✅ **QR 码随消息发送**：根据 MCP 返回的 preview_url 生成赛博朋克风格 QR 码 PNG，作为图片附件发送
- ✅ 消息模板更新：新增路由信息、"扫描二维码"提示
- ✅ 一条消息搞定：交易预览文字 + QR 码图片同时发出

### v1.0.1 (2026-03-27)
- ✅ **接入 Antalpha MCP Server**（`mcp-skills.ai.antalpha.com/mcp`）
- ✅ 新增 MCP 远程模式：swap-quote / swap-create-page / swap-tokens / swap-gas / swap-full
- ✅ swap-full 一站式调用：报价 + 页面生成 + 服务端托管（1 次调用替代原 5 步流程）
- ✅ Swap 页面托管在 Antalpha 可信域名下，不再依赖 Litterbox
- ✅ Agent 无需本地配置 0x API Key（MCP Server 统一管理）
- ✅ 已验证全部 7 个 MCP Tools 调通（test-ping / swap-quote / swap-create-page / swap-tokens / swap-gas / swap-full / multi-source-token-list）
- ✅ 本地 CLI 模式保留为降级方案

### v1.0.0 (2026-03-27)
- ✅ 赛博朋克风格 Swap 托管页（Matrix 数字雨 + 扫描线动效）
- ✅ 四大钱包支持：MetaMask、OKX Web3、Trust Wallet、TokenPocket
- ✅ 钱包内置浏览器自动执行交易（2s 倒计时后自动弹签名）
- ✅ QR 码生成（青色码点 + 深色背景）
- ✅ Litterbox 临时托管方案（72h 有效）
- ✅ 交易预览消息模板（含 Antalpha AI 品牌标识）
- ✅ 零外部依赖（无 Google Fonts/CDN）
- ✅ 完整 CLI 工具链（price/route/build-tx/export/swap-page/gas/tokens）
