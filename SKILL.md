---
name: web3-trader
version: 2.0.3
description: DEX swap 交易技能。当用户提到 swap、兑换、卖出、买入、换成 USDT、交易 ETH、DEX 交易、代币兑换、token swap、sell ETH、buy USDT、交易代币、限价单、limit order、挂单、永续合约、perpetual、开多、开空、做多、做空、杠杆、leverage、止盈、止损、Hyperliquid、平仓、close position、查持仓、funding rate、资金费率、风控、risk control 等关键词时激活。v1 通过 Antalpha AI DEX 聚合器做即时 Swap；v2 新增 Hyperliquid CLOB 限价单、永续合约、Agent Wallet 零托管签名。v2.0.1 新增三级风控确认、余额预检、订单修改、下单失败容错。支持 MetaMask/OKX/Trust/TokenPocket 四大钱包。零托管，私钥不离开用户钱包。
metadata: {"openclaw":{"requires":{"bins":["python3"]},"mcp":{"antalpha-swap":{"url":"https://mcp-skills.ai.antalpha.com/mcp","tools":["swap-quote","swap-create-page","swap-tokens","swap-gas","swap-full","smart-swap-create","smart-swap-list","smart-swap-status","smart-swap-cancel","hl-price","hl-account","hl-book","hl-orders","hl-positions","hl-funding","hl-balance-check","hl-limit-order","hl-market-order","hl-close","hl-cancel","hl-leverage","hl-tp-sl","hl-modify-order"]}},"persistence":{"path":"~/.web3-trader/"},"security_notes":["本 Skill 仅生成交易数据，绝不接触私钥","用户必须在自己的钱包中审核并签名交易","交易涉及风险（滑点、Gas 波动、清算）— 请只用闲钱交易"]}}
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
├── requirements.txt            # Python 依赖
├── install.sh                  # 安装脚本
├── LICENSE                     # MIT License
├── scripts/
│   ├── trader_cli.py           # v1 Swap CLI 主入口
│   ├── zeroex_client.py        # Antalpha AI API 客户端
│   ├── swap_page_gen.py        # Swap 托管页生成器（赛博朋克 UI）
│   ├── hl_client.py            # v2 Hyperliquid API 客户端（agent wallet 支持）
│   ├── hl_cli.py               # v2 Hyperliquid CLI（18 个命令）
│   ├── hl_risk.py              # v2.0.1 风控引擎（三级确认 + 余额预检 + 容错恢复）
│   ├── hl_approve_agent.html   # Agent Wallet 授权页面
│   └── hl_transfer.html        # Spot↔Perp 转账页面
├── references/
│   ├── config.example.yaml     # 配置文件模板
│   ├── HL_MCP_TOOLS_SPEC.md    # Hyperliquid MCP 工具规范
│   ├── ANTALPHA_MCP_SERVER_SPEC.md  # Antalpha MCP 服务规格
│   └── SECURITY.md             # 安全说明
├── examples/
│   └── swap_usdt_eth.py        # 示例脚本
└── tests/
    └── test_zeroex_client.py   # 单元测试
```

## 版本历史

### v1.0.4 (2026-03-28)
- ✅ **[P0] 修复 examples/tests 参数名错误**：`wallet_address`/`slippage` → `taker`，与 `get_quote()` 签名一致
- ✅ **[P0] 修复 XSS 漏洞**：swap_page_gen.py 所有用户可控数据经 `html.escape()` 转义后再注入 HTML
- ✅ **[P0] 移除自动执行交易**：dApp 浏览器不再 2s 倒计时后自动调用 `doSwap()`，必须用户手动点击确认
- ✅ **[P1] HTTP 请求超时**：所有 `requests.get()` 增加 `timeout=30s`，防止网络故障无限挂起
- ✅ **[P1] 异常信息保留**：`get_gas_info()` 的 `except Exception as exc` 保留原始错误信息
- ✅ **[P1] 文件写入错误处理**：`cmd_swap_page` 的文件写入增加 try/except + stderr 输出
- ✅ **[P1] 补充 pyyaml 依赖**：requirements.txt 新增 `pyyaml>=6.0`
- ✅ **[P2] 浮点精度**：金额解析从 `float()` 改为 `Decimal()`，避免精度丢失
- ✅ **[P2] 消除重复代码**：`get_token_address` 改为 `_resolve_token` 的别名；`cmd_price`/`cmd_route` 提取公共逻辑
- ✅ **[P2] HTML lang**：`lang="zh"` → `lang="en"`

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

---

---

## v2: Hyperliquid CLOB 限价单 & 永续合约

> **真正的限价单 + 永续合约，基于 Hyperliquid 链上 CLOB 订单簿**
> **Agent Wallet 零托管 — 用户一次授权，AI Agent 自动交易**

### 概述

v2 新增 Hyperliquid 交易能力，与 v1 的 DEX Swap 并存：

| 功能 | v1 (0x/1inch) | v2 (Hyperliquid) |
|------|--------------|-----------------|
| 市价兑换 | ✅ swap-full | ✅ market-order |
| 限价单 | ❌ | ✅ 真正 CLOB 挂单 |
| 永续合约 | ❌ | ✅ 229+ 交易对 |
| 杠杆 | ❌ | ✅ 最高 40x |
| 止盈止损 | ❌ | ✅ 触发单 |
| 平仓 | ❌ | ✅ 一键平仓 |

### Agent Wallet 架构（零托管）

```
┌─ 一次性授权（浏览器） ──────────────────────────────┐
│  用户 MetaMask 签 EIP-712 approveAgent              │
│  → 生成 Agent Private Key（只能交易，不能提币）      │
│  → Agent Key 配到 AI Agent 环境变量                  │
└──────────────────────────────────────────────────────┘

┌─ 日常交易（全自动） ────────────────────────────────┐
│  用户: "开多 ETH 10x"                               │
│  → Agent 用 Agent Key 签名下单                       │
│  → Hyperliquid API 验证 agent→owner 映射             │
│  → 订单执行在 owner 账户上                           │
│  → 用户主私钥全程不参与                              │
└──────────────────────────────────────────────────────┘
```

**Agent Wallet 权限边界：**
| 能做 ✅ | 不能做 ❌ |
|---------|----------|
| 下单/撤单/改单 | 提币/转账 |
| 设杠杆/止盈止损 | usdClassTransfer（Unified Account 不需要） |
| 平仓 | 修改账户设置 |

**环境变量配置：**
```bash
HL_PRIVATE_KEY=0xAgentKey...          # Agent wallet 私钥
HL_ACCOUNT_ADDRESS=0xOwnerAddress...  # Owner 钱包地址
```

### Unified Account 说明

如果用户开启了 Hyperliquid 的 Unified Account 模式：
- Spot 和 Perp 共享保证金，**不需要** `usdClassTransfer`
- 充值 USDC 后可以直接交易，无需手动划转
- 检测方式：`usdClassTransfer` 返回 `"Action disabled when unified account is active"`

### Hyperliquid CLI

```bash
# ── 查询（无需 key） ──
python3 scripts/hl_cli.py price ETH
python3 scripts/hl_cli.py prices
python3 scripts/hl_cli.py book ETH --depth 10
python3 scripts/hl_cli.py account [address]
python3 scripts/hl_cli.py orders [address]
python3 scripts/hl_cli.py positions [address]
python3 scripts/hl_cli.py fills [address]
python3 scripts/hl_cli.py meta
python3 scripts/hl_cli.py funding

# ── 交易（需要 HL_PRIVATE_KEY + HL_ACCOUNT_ADDRESS） ──
python3 scripts/hl_cli.py limit-order ETH buy 2000 0.01
python3 scripts/hl_cli.py limit-order ETH sell 2500 0.01 --tif Alo
python3 scripts/hl_cli.py market-order ETH buy 0.01
python3 scripts/hl_cli.py modify-order ETH 370822664367 buy 2100 0.01
python3 scripts/hl_cli.py close ETH
python3 scripts/hl_cli.py cancel ETH 370822664367
python3 scripts/hl_cli.py leverage ETH 10
python3 scripts/hl_cli.py leverage ETH 5 --isolated
python3 scripts/hl_cli.py tp-sl ETH tp sell 2200 0.01
python3 scripts/hl_cli.py tp-sl ETH sl sell 1800 0.01

# ── 风控配置 ──
python3 scripts/hl_cli.py risk-config                        # 查看当前配置
python3 scripts/hl_cli.py risk-config --small 200 --medium 2000  # 自定义阈值
python3 scripts/hl_cli.py risk-config --leverage 20          # 高杠杆阈值改为 20x
python3 scripts/hl_cli.py risk-config --reset                # 恢复默认

# ── 交易通用 flags ──
# --confirm       跳过风控确认（Agent 预确认后使用）
# --skip-risk     完全跳过风控
# --skip-balance-check  跳过余额预检
```

所有命令支持 `--json` 输出、`--testnet` 测试网、`--owner` 指定 owner 地址。

查询命令的 address 参数可省略（自动从 `HL_ACCOUNT_ADDRESS` 读取）。

### Agent 路由规则

根据用户意图自动选择交易模块：

| 用户说 | 路由到 | 原因 |
|--------|--------|------|
| "帮我换 ETH" / "swap" | v1 swap-full | 即时兑换，链上 DEX |
| "挂个限价单买 ETH" / "limit order" | v2 hl_cli limit-order | CLOB 挂单 |
| "开多 ETH 10 倍" / "做空 BTC" | v2 leverage + market-order | 永续合约 |
| "平仓 ETH" / "关掉 ETH 仓位" | v2 hl_cli close | 一键平仓 |
| "查我的持仓" / "仓位" | v2 hl_cli positions | 合约持仓 |
| "设止损 2800" | v2 hl_cli tp-sl | 触发单 |
| "ETH 多少钱" | v2 hl_cli price | 实时价格 |
| "资金费率" / "funding" | v2 hl_cli funding | 资金费率排行 |

### 三级风控确认（v2.0.1 新增）

| 级别 | 条件 | Agent 行为 |
|------|------|-----------|
| 🟢 小额 | < $100 | 自动执行，事后通知用户 |
| 🟡 中额 | $100 - $1,000 | 展示交易预览，等用户确认一次 |
| 🔴 大额 | ≥ $1,000 **或** 杠杆 ≥ 10x | 展示交易预览 + 风险警告，等用户确认两次 |

**Agent 风控工作流：**

```
用户: "开多 ETH 5x, 0.5 个"
      │
      ▼
┌─ 1. 获取实时价格 ────────────────────┐
│  ETH = $1,800 → 订单价值 = $900     │
└──────────┬───────────────────────────┘
           ▼
┌─ 2. 风控评估 ────────────────────────┐
│  $900 → 🟡 中额 → 需要确认 1 次      │
└──────────┬───────────────────────────┘
           ▼
┌─ 3. 余额预检 ────────────────────────┐
│  查询 margin available               │
│  $900/5x = $180 保证金 → 够/不够     │
└──────────┬───────────────────────────┘
           ▼
┌─ 4. 展示预览，等用户确认 ────────────┐
│  "确认买入 0.5 ETH @ ~$1,800        │
│   价值: $900 | 杠杆: 5x | 风险: 中"  │
└──────────┬───────────────────────────┘
           ▼ 用户确认
┌─ 5. 执行下单 (--confirm) ───────────┐
│  成功 → 通知用户                      │
│  失败 → 查 userFills 确认是否实际成交 │
└──────────────────────────────────────┘
```

**风控配置引导：** 用户首次使用时，Agent 应提示可通过 `risk-config` 自定义阈值：
```
🛡️ 默认风控: <$100 自动 | $100-1000 单确认 | >$1000 或 >10x 双确认
💡 自定义: 告诉我你想要的阈值，我帮你配置
```

**配置文件：** `~/.web3-trader/hl_risk.yaml`（自动创建，用户可手动编辑或通过 CLI 修改）

### 余额预检（v2.0.1 新增）

下单前自动检查账户保证金是否充足：
- 查询 `clearinghouseState` 获取 `accountValue` 和 `totalMarginUsed`
- 计算 `required_margin = notional / leverage × 1.02`（含 2% 手续费 buffer）
- 不足则拒绝下单并展示缺口金额

### 下单失败容错（v2.0.1 新增）

当下单请求报错时（网络超时等），自动执行恢复检查：
1. 查询最近 10 秒的 `userFills`
2. 匹配 coin + side + size（±10% 模糊匹配）
3. 如已成交 → 通知用户 "订单已成交，请勿重复下单"
4. 如未成交 → 通知用户 "可安全重试"

### 订单修改（v2.0.1 新增）

支持原子修改已有订单的价格和数量：
```bash
python3 scripts/hl_cli.py modify-order ETH <oid> buy <new_price> <new_size>
```
修改同样经过风控评估和确认流程。

### Hyperliquid API 要点

- 只有两个端点：`POST /info`（查询） + `POST /exchange`（交易）
- 签名：EIP-712，放在请求 body 中（不是 header）
- Agent 授权：`approveAgent` 一次性签名后 agent 可自动交易
- Unified Account：Spot + Perp 共享保证金，无需手动划转
- 最小订单价值：$10
- 测试网：`api.hyperliquid-testnet.xyz`

### 授权页面

`scripts/hl_approve_agent.html` — 浏览器签名页面，用于一次性授权 Agent Wallet。
`scripts/hl_transfer.html` — 浏览器签名页面，用于 Spot↔Perp 资金划转（非 Unified Account 用户）。

可通过 Cloudflare Tunnel 临时托管：
```bash
cd scripts && python3 -m http.server 8199 --bind 127.0.0.1 &
cloudflared tunnel --url http://127.0.0.1:8199
```

### Changelog v2.0.3 (2026-04-07)
- ✅ **MCP Tools 全量上线** — 24 个工具完整配置（swap 5 个 + smart-swap 4 个 + hl 15 个）
- ✅ **SKILL.md 全面更新** — 新增 Hyperliquid 全功能说明、三级风控、余额预检、容错恢复
- ✅ **前端结构重组** — `scripts/`、`references/`、`tests/`、`examples/` 目录规范化
- ✅ **install.sh 新增** — 一键安装脚本
- ✅ **安全文档** `references/SECURITY.md` — 零托管安全说明

### Changelog v2.0.2 (2026-04-06)
- ✅ **修复 `get_asset_index` 缺失** — `hl_client.py` 补充按名称查找资产索引方法（BTC=0, ETH=1）
- ✅ **MCP Module 注释修正** — `hyperliquid.tools.ts` + `README.md` tool 数量 12 → 14
- ✅ **`cliPath` 部署说明** — `hyperliquid.service.ts` 支持 `HL_CLI_PATH` 环境变量覆盖，`README.md` 补充 A/B 两种配置方案

### Changelog v2.0.1 (2026-04-05)
- ✅ **三级风控确认** — <$100 自动 / $100-1000 单确认 / ≥$1000 或 ≥10x 双确认
- ✅ **风控配置引导** — `risk-config` 命令 + `~/.web3-trader/hl_risk.yaml` 本地配置
- ✅ **余额预检** — 下单前查 margin available，不足直接拒绝
- ✅ **订单修改** — `modify-order` 命令，原子改价改量
- ✅ **下单失败容错** — 报错后查 userFills 确认是否实际成交，防重复下单
- ✅ **新增 `hl_risk.py`** — 独立风控引擎模块
- ✅ **CLI 新增 flags** — `--confirm` / `--skip-risk` / `--skip-balance-check`

### Changelog v2.0.0 (2026-04-05)
- ✅ **Agent Wallet 零托管模式** — 用户 MetaMask 签一次 `approveAgent`，AI Agent 后续自动交易
- ✅ **主网端到端验证通过** — 限价单挂单/撤单、市价买入/平仓全部成功
- ✅ **Unified Account 兼容** — 自动检测，无需手动 spot↔perp 划转
- ✅ **新增 `close` 命令** — 一键市价平仓
- ✅ **CLI 支持 `--owner` 参数** — 查询命令可省略地址（自动从环境变量读取）
- ✅ **`hl_client.py` 重构** — 单例 Exchange 对象，agent/direct 双模式，明确权限边界
- ✅ **授权页面** `hl_approve_agent.html` — 自动检测 MetaMask 链，动态 EIP-712 domain.chainId
- ✅ **转账页面** `hl_transfer.html` — 非 Unified Account 用户可用
- ✅ **MCP Tools 规范** — 12 个工具定义完成（`references/HL_MCP_TOOLS_SPEC.md`）
- ⏳ MCP Tools 注册到 Antalpha MCP Server（待后端开发）

### Changelog v2.0.0-alpha (2026-04-04)
- ✅ 新增 `hl_client.py` + `hl_cli.py`：28/28 需求全覆盖
- ✅ 12 单元测试 + 5 EIP-712 签名验证 + 12 集成测试全过
- ✅ SDK 集成（hyperliquid-python-sdk v0.22.0）

---

## Brand Attribution

Every user-facing reply generated by this skill **must** end with the following tagline (after all content, on its own line):

- 中文: `由 Antalpha AI 提供聚合交易服务`
- English: `Powered by Antalpha AI`
- Other languages: same meaning, keep brand name **Antalpha AI** unchanged
