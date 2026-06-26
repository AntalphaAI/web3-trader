<!-- Language Navigation -->
<div align="center">

[🇺🇸 English](#english) · [🇨🇳 中文](#chinese)

</div>

---

<a name="english"></a>

# 🔄 Web3 Trader Skill v2.0.6

> **AI-Native DEX Trading + Hyperliquid Perp | Zero Custody | Multi-Wallet | Cyberpunk UI**
>
> Powered by Antalpha AI · v1 DEX Swap + v2 Hyperliquid CLOB & Perpetuals

## Install

```bash
openclaw skill install https://github.com/AntalphaAI/web3-trader
```

### Install via ClawHub

```bash
clawhub install web3-trader
```

## Features

### v1 — DEX Swap (Antalpha AI Aggregator)
- 💱 Real-time DEX quotes and optimal routing via Antalpha AI Aggregator
- 🌐 Cyberpunk-style swap pages (Matrix rain animation + scanline effects)
- 📱 4 major wallets: MetaMask, OKX Web3, Trust Wallet, TokenPocket
- 🔒 Zero custody — private keys never leave the user's wallet
- 🤖 MCP remote mode — one `swap-full` call does quote + page hosting + QR

### v2 — Hyperliquid CLOB & Perpetuals (NEW)
- 📈 True limit orders on Hyperliquid on-chain CLOB order book
- ♾️ Perpetual contracts — 229+ trading pairs, up to 40x leverage
- 🤖 Agent Wallet zero-custody mode — user signs `approveAgent` once, AI trades automatically
- 🛡️ 3-tier risk control — auto / single-confirm / double-confirm by trade size
- 💰 Pre-trade balance check — rejects orders before they fail
- 🔁 Order modify & fail-safe recovery — prevent duplicate fills
- 📊 Full position management — TP/SL, close, funding rate queries

## Two Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| 🌐 **MCP Remote Mode** (Recommended) | Antalpha MCP Server handles quote + page hosting | Production, no local API key needed |
| 🖥️ **Local CLI Mode** (Fallback) | Python CLI calls 0x API locally | Dev/debug, offline environments |

## MCP Server

```
https://mcp-skills.ai.antalpha.com/mcp
```

### Available MCP Tools (21 total)

#### v1 — DEX Swap (5 tools)

| Tool | Description |
|------|-------------|
| `swap-full` | **One-shot**: quote + generate page + host → returns URL + QR |
| `swap-quote` | Get DEX aggregated quote |
| `swap-create-page` | Generate and host a cyberpunk swap page |
| `swap-tokens` | List supported tokens |
| `swap-gas` | Current gas price |

#### v1 — Smart Swap (4 tools)

| Tool | Description |
|------|-------------|
| `smart-swap-create` | Create a smart swap order with auto-routing |
| `smart-swap-list` | List active smart swap orders |
| `smart-swap-status` | Query smart swap order status |
| `smart-swap-cancel` | Cancel a smart swap order |

#### v2 — Hyperliquid (12 tools)

| Tool | Description |
|------|-------------|
| `hyperliquid-market` | Market data — `view=price` (default: single/CSV/Top-10), `view=book` (order book depth, needs `coin`+`depth?`), `view=funding` (funding rate rankings, `limit?`/`coin?`) |
| `hyperliquid-account` | Account info (balance, margin, equity) |
| `hyperliquid-orders` | List open orders |
| `hyperliquid-positions` | List open positions |
| `hyperliquid-balance-check` | Pre-trade balance check (spot or perp) |
| `hyperliquid-limit-order` | Place CLOB limit order |
| `hyperliquid-market-order` | Place perpetual market order |
| `hyperliquid-close` | One-click market close position |
| `hyperliquid-cancel` | Cancel open order |
| `hyperliquid-leverage` | Set leverage for a trading pair |
| `hyperliquid-tp-sl` | Set take-profit / stop-loss trigger orders |
| `hyperliquid-modify-order` | Atomically modify price and size of open order |

## Architecture

### v1 — DEX Swap Flow

```
┌──────────────┐    MCP JSON-RPC    ┌──────────────────────────────────┐
│  AI Agent    │ ──────────────────► │  Antalpha MCP Server              │
│  (OpenClaw)  │  swap-full          │  mcp-skills.ai.antalpha.com       │
│              │ ◄────────────────── │                                    │
│              │  quote+preview_url  │  ├─ 0x API ── DEX Aggregation     │
└──────┬───────┘                     │  ├─ Page Gen ── Cyberpunk HTML    │
       │                             │  └─ Hosting ── URL + QR           │
       │  send preview_url + QR      └────────────────────────────────────┘
       ▼
┌──────────────┐   click/scan    ┌────────────────────┐
│  User        │ ──────────────► │  Hosted Swap Page   │
│  (mobile/PC) │                 │  (Cyberpunk UI)     │
└──────────────┘                 └────────┬───────────┘
                                          │ eth_sendTransaction
                                          ▼
                                 ┌────────────────────┐
                                 │  Wallet App         │
                                 │  Sign & Broadcast   │
                                 └────────────────────┘
```

### v2 — Hyperliquid Agent Wallet Flow

```
┌──────────────┐    MCP JSON-RPC    ┌──────────────────────────────────┐
│  AI Agent    │ ──────────────────► │  Antalpha MCP Server              │
│  (OpenClaw)  │  hyperliquid-limit-order     │  mcp-skills.ai.antalpha.com       │
│              │ ◄────────────────── │                                    │
│              │  order_id + status  │  ├─ hl_client.py ── Agent Wallet  │
└──────────────┘                     │  ├─ hl_risk.py ── 3-tier risk     │
                                     │  └─ Hyperliquid API ── CLOB       │
                                     └────────────────────────────────────┘
                                                    │
                                          Agent Wallet signs
                                         (user approved once)
                                                    │
                                                    ▼
                                     ┌──────────────────────────┐
                                     │  Hyperliquid Chain        │
                                     │  Order Book (CLOB)        │
                                     └──────────────────────────┘
```

## Quick Start

### Install

```bash
openclaw skill install https://github.com/AntalphaAI/web3-trader
```

### MCP Remote Mode (Recommended)

No local setup needed. Configure in OpenClaw:

```
MCP Server: https://mcp-skills.ai.antalpha.com/mcp
```

### v1 — DEX Swap Example

```bash
# Query price
python3 scripts/trader_cli.py price --from ETH --to USDT --amount 0.1

# Generate swap page
python3 scripts/trader_cli.py swap-page --from ETH --to USDT --amount 0.1 \
  --wallet 0xYourAddress -o swap.html --json
```

### v2 — Hyperliquid CLI

```bash
# Set up agent wallet
cp references/config.example.yaml ~/.web3-trader/config.yaml

# Check price
python3 scripts/hl_cli.py price ETH

# Place limit order
python3 scripts/hl_cli.py limit-order --symbol ETH --side buy --price 2000 --size 0.01

# Open perpetual long
python3 scripts/hl_cli.py market-order --symbol ETH --side buy --size 0.01 --leverage 5

# View positions
python3 scripts/hl_cli.py positions

# Close position
python3 scripts/hl_cli.py close --symbol ETH
```

## v2 Feature Details

### Agent Wallet (Zero Custody)

User signs `approveAgent` once via `scripts/hl_approve_agent.html`. After that, the AI agent can trade autonomously — private keys never leave the user's wallet.

```
User → MetaMask → sign approveAgent (EIP-712)
                       ↓
              Agent Wallet activated
                       ↓
AI Agent → hyperliquid-limit-order / hyperliquid-market-order → Hyperliquid CLOB
```

### 3-Tier Risk Control (v2.0.1)

| Trade Value | Confirmation Required |
|-------------|----------------------|
| < $100 | Auto-execute |
| $100 – $999 | Single confirmation |
| ≥ $1000 or ≥ 10x leverage | Double confirmation |

### Supported Trading Pairs

| Category | Examples |
|----------|---------| 
| Perpetuals | BTC, ETH, SOL, ARB, and 225+ more |
| Leverage | Up to 40x (pair-dependent) |

## Supported Wallets

| Wallet | Protocol | Status |
|--------|----------|--------|
| 🦊 MetaMask | `metamask.app.link/dapp/` | ✅ Verified |
| 💎 OKX Web3 | `okx://wallet/dapp/details` | ✅ Verified |
| 🛡️ Trust Wallet | `link.trustwallet.com/open_url` | ✅ Verified |
| 📱 TokenPocket | `tpdapp://open` | ✅ Verified |

## Project Structure

```
├── SKILL.md                        # Full skill spec (read by AI agent)
├── README.md                       # This file
├── requirements.txt                # Python dependencies
├── install.sh                      # One-click install script
├── scripts/
│   ├── trader_cli.py               # v1 Swap CLI entry point
│   ├── zeroex_client.py            # Antalpha AI DEX API client
│   ├── swap_page_gen.py            # Cyberpunk swap page generator
│   ├── hl_client.py                # v2 Hyperliquid API client (agent wallet)
│   ├── hl_cli.py                   # v2 Hyperliquid CLI (18 commands)
│   ├── hl_risk.py                  # v2.0.1 Risk engine (3-tier + balance check)
│   ├── hl_approve_agent.html       # Agent Wallet authorization page
│   └── hl_transfer.html            # Spot↔Perp transfer page
├── references/
│   ├── config.example.yaml         # Config template
│   ├── HL_MCP_TOOLS_SPEC.md        # Hyperliquid MCP tools spec
│   ├── ANTALPHA_MCP_SERVER_SPEC.md # Antalpha MCP server spec
│   └── SECURITY.md                 # Security documentation
├── examples/
│   └── swap_usdt_eth.py            # Example swap script
└── tests/
    ├── test_zeroex_client.py
    ├── test_hl_client.py
    └── test_hl_integration.py
```

## Security

| Layer | Protection |
|-------|-----------|
| Private Keys | **Zero contact** — skill never holds, transmits, or stores any private key |
| Agent Wallet | EIP-712 signed authorization, user controls permissions |
| Transaction Data | Generated by 0x Protocol with MEV protection (anti-sandwich) |
| Slippage | Configurable max slippage (default 0.5%), `minBuyAmount` enforced on-chain |
| Risk Control | 3-tier confirmation prevents accidental large trades |
| Swap Pages | Self-contained HTML, no backend communication, no cookies, no tracking |

## Changelog

### v2.0.6 (2026-06-26)
- ✅ Market tool merge — `hyperliquid-price` + `hyperliquid-book` + `hyperliquid-funding` merged into a single `hyperliquid-market` with a `view` param (`price` default / `book` needs `coin`+`depth?` / `funding` uses `limit?`+`coin?`); Hyperliquid count 14→12, total 23→21

### v2.0.4 (2026-06-15)
- ✅ MCP tool rename sync — 14 perpetual tools `hl-*` → `hyperliquid-*`, aligned with live MCP (`mcp-skills.ai.antalpha.com/mcp`); fixes perpetual calls breaking after the rename because the old tool names no longer exist
- ✅ Doc tool-count fix — total 24→23, Hyperliquid 15→14 (14 tools actual, matching the v2.0.2 correction)

### v2.0.3 (2026-04-07)
- ✅ MCP Tools full rollout — 24 tools fully configured (swap ×5 + smart-swap ×4 + hl ×15)
- ✅ SKILL.md comprehensive update — added full Hyperliquid feature docs, 3-tier risk control, balance check, fail-safe recovery
- ✅ Frontend structure reorganized — `scripts/`, `references/`, `tests/`, `examples/` standardized
- ✅ install.sh added — one-click install script with auto dependency setup
- ✅ Security docs `references/SECURITY.md` — zero-custody security documentation

### v2.0.2 (2026-04-06)
- ✅ Fix `get_asset_index` missing — `hl_client.py` adds asset lookup by name (BTC=0, ETH=1)
- ✅ MCP Module comment fix — tool count corrected from 12 → 14
- ✅ `cliPath` deployment docs — supports `HL_CLI_PATH` env override, added A/B config options

### v2.0.1 (2026-04-05)
- ✅ 3-tier risk confirmation — <$100 auto / $100-1000 single confirm / ≥$1000 or ≥10x double confirm
- ✅ Pre-trade balance check — checks margin available before order, rejects if insufficient
- ✅ Order modify — `modify-order` command for atomic price/size changes
- ✅ Fail-safe recovery — checks userFills after error to prevent duplicate orders
- ✅ New `hl_risk.py` — standalone risk engine module

### v2.0.0 (2026-04-05)
- ✅ Hyperliquid CLOB limit orders & perpetuals — v2 core new capability
- ✅ Agent Wallet zero-custody mode — user signs `approveAgent` once, AI agent trades automatically
- ✅ Mainnet end-to-end verified — limit order place/cancel, market buy/close all successful
- ✅ Unified Account compatible — auto-detect, no manual spot↔perp transfer needed

### v1.0.4 (2026-03-28)
- [P0] Fix XSS vulnerability in `swap_page_gen.py`
- [P0] Remove auto-execute in dApp browser
- [P1] Add `timeout=30s` to all HTTP requests
- [P2] Use `Decimal` for amount calculations

### v1.0.0 (2026-03-27)
- Initial release: Cyberpunk swap pages, 4 wallet support, full CLI toolchain

## License

MIT · Powered by Antalpha AI

---

<a name="chinese"></a>

# 🔄 Web3 Trader Skill v2.0.6（中文文档）

> **AI 原生 DEX 交易 + Hyperliquid 永续合约 | 零托管 | 多钱包支持 | 赛博朋克 UI**
>
> Powered by Antalpha AI · v1 DEX Swap + v2 Hyperliquid CLOB & 永续合约

## 安装

```bash
openclaw skill install https://github.com/AntalphaAI/web3-trader
```

### 通过 ClawHub 安装

```bash
clawhub install web3-trader
```

## 功能特性

### v1 — DEX Swap（Antalpha AI 聚合器）
- 💱 通过 Antalpha AI 聚合器获取实时 DEX 报价和最优路由
- 🌐 赛博朋克风格兑换页面（矩阵雨动画 + 扫描线特效）
- 📱 支持 4 大主流钱包：MetaMask、OKX Web3、Trust Wallet、TokenPocket
- 🔒 零托管——私钥永远不离开用户钱包
- 🤖 MCP 远程模式——一次 `swap-full` 调用完成报价 + 页面托管 + 二维码

### v2 — Hyperliquid CLOB & 永续合约（新功能）
- 📈 Hyperliquid 链上 CLOB 订单簿真实限价单
- ♾️ 永续合约——229+ 交易对，最高 40 倍杠杆
- 🤖 Agent 钱包零托管模式——用户只需签名一次 `approveAgent`，AI 自动交易
- 🛡️ 三级风控——按交易规模自动/单次/双重确认
- 💰 交易前余额检查——提前拦截余额不足的订单
- 🔁 订单修改与容错恢复——防止重复成交
- 📊 完整仓位管理——止盈止损、平仓、资金费率查询

## 两种模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| 🌐 **MCP 远程模式**（推荐） | MCP 服务器处理报价和页面托管 | 生产环境，无需本地 API Key |
| 🖥️ **本地 CLI 模式**（备选） | Python CLI 本地调用 0x API | 开发调试、离线环境 |

## MCP 服务器

```
https://mcp-skills.ai.antalpha.com/mcp
```

### MCP 工具列表（共 21 个）

#### v1 — DEX Swap（5 个工具）

| 工具 | 说明 |
|------|------|
| `swap-full` | **一步完成**：报价 + 生成页面 + 托管 → 返回链接 + 二维码 |
| `swap-quote` | 获取 DEX 聚合报价 |
| `swap-create-page` | 生成并托管赛博朋克风格兑换页面 |
| `swap-tokens` | 查看支持的代币列表 |
| `swap-gas` | 当前 Gas 价格 |

#### v1 — Smart Swap（4 个工具）

| 工具 | 说明 |
|------|------|
| `smart-swap-create` | 创建自动路由的智能兑换订单 |
| `smart-swap-list` | 查看活跃的智能兑换订单 |
| `smart-swap-status` | 查询智能兑换订单状态 |
| `smart-swap-cancel` | 取消智能兑换订单 |

#### v2 — Hyperliquid（12 个工具）

| 工具 | 说明 |
|------|------|
| `hyperliquid-market` | 行情数据——`view=price`（默认：单币/逗号分隔多币/Top-10）、`view=book`（订单簿深度，需 `coin`+`depth?`）、`view=funding`（资金费率排行，`limit?`/`coin?`） |
| `hyperliquid-account` | 账户信息（余额、保证金、净值） |
| `hyperliquid-orders` | 查看挂单列表 |
| `hyperliquid-positions` | 查看持仓列表 |
| `hyperliquid-balance-check` | 交易前余额检查（现货或永续） |
| `hyperliquid-limit-order` | 挂限价单 |
| `hyperliquid-market-order` | 下永续合约市价单 |
| `hyperliquid-close` | 一键市价平仓 |
| `hyperliquid-cancel` | 撤销挂单 |
| `hyperliquid-leverage` | 设置交易对杠杆倍数 |
| `hyperliquid-tp-sl` | 设置止盈止损触发单 |
| `hyperliquid-modify-order` | 原子性修改挂单价格和数量 |

## 快速开始

### 安装

```bash
openclaw skill install https://github.com/AntalphaAI/web3-trader
```

### 通过 ClawHub 安装

```bash
clawhub install web3-trader
```

### MCP 远程模式（推荐）

无需本地配置，直接在 OpenClaw 中添加：

```
MCP Server: https://mcp-skills.ai.antalpha.com/mcp
```

### v1 — 兑换示例

```bash
# 查询价格
python3 scripts/trader_cli.py price --from ETH --to USDT --amount 0.1

# 生成兑换页面
python3 scripts/trader_cli.py swap-page --from ETH --to USDT --amount 0.1 \
  --wallet 0xYourAddress -o swap.html --json
```

### v2 — Hyperliquid CLI

```bash
# 配置 Agent 钱包
cp references/config.example.yaml ~/.web3-trader/config.yaml

# 查询价格
python3 scripts/hl_cli.py price ETH

# 下限价单
python3 scripts/hl_cli.py limit-order --symbol ETH --side buy --price 2000 --size 0.01

# 开多
python3 scripts/hl_cli.py market-order --symbol ETH --side buy --size 0.01 --leverage 5

# 查看持仓
python3 scripts/hl_cli.py positions

# 平仓
python3 scripts/hl_cli.py close --symbol ETH
```

## v2 功能详解

### Agent 钱包（零托管）

用户通过 `scripts/hl_approve_agent.html` 一次性签名 `approveAgent`，之后 AI Agent 即可自主交易——私钥始终不离开用户钱包。

```
用户 → MetaMask → 签名 approveAgent (EIP-712)
                       ↓
              Agent 钱包激活
                       ↓
AI Agent → hyperliquid-limit-order / hyperliquid-market-order → Hyperliquid CLOB
```

### 三级风控（v2.0.1）

| 交易金额 | 确认方式 |
|----------|---------|
| < $100 | 自动执行 |
| $100 – $999 | 单次确认 |
| ≥ $1000 或 ≥ 10 倍杠杆 | 双重确认 |

### 支持的交易对

| 类别 | 示例 |
|------|------|
| 永续合约 | BTC、ETH、SOL、ARB 等 225+ 交易对 |
| 杠杆倍数 | 最高 40 倍（视交易对而定） |

## 支持的钱包

| 钱包 | 协议 | 状态 |
|------|------|------|
| 🦊 MetaMask | `metamask.app.link/dapp/` | ✅ 已验证 |
| 💎 OKX Web3 | `okx://wallet/dapp/details` | ✅ 已验证 |
| 🛡️ Trust Wallet | `link.trustwallet.com/open_url` | ✅ 已验证 |
| 📱 TokenPocket | `tpdapp://open` | ✅ 已验证 |

## 项目结构

```
├── SKILL.md                        # AI Agent 完整 Skill 规范
├── README.md                       # 本文件
├── requirements.txt                # Python 依赖
├── install.sh                      # 一键安装脚本
├── scripts/
│   ├── trader_cli.py               # v1 兑换 CLI 入口
│   ├── zeroex_client.py            # Antalpha AI DEX API 客户端
│   ├── swap_page_gen.py            # 赛博朋克兑换页面生成器
│   ├── hl_client.py                # v2 Hyperliquid API 客户端
│   ├── hl_cli.py                   # v2 Hyperliquid CLI（18 条命令）
│   ├── hl_risk.py                  # v2.0.1 风控引擎
│   ├── hl_approve_agent.html       # Agent 钱包授权页面
│   └── hl_transfer.html            # 现货↔永续划转页面
├── references/
│   ├── config.example.yaml         # 配置模板
│   ├── HL_MCP_TOOLS_SPEC.md        # Hyperliquid MCP 工具规范
│   ├── ANTALPHA_MCP_SERVER_SPEC.md # Antalpha MCP 服务规范
│   └── SECURITY.md                 # 安全文档
├── examples/
│   └── swap_usdt_eth.py            # 兑换示例脚本
└── tests/
    ├── test_zeroex_client.py
    ├── test_hl_client.py
    └── test_hl_integration.py
```

## 安全性

| 层级 | 防护措施 |
|------|---------|
| 私钥 | **零接触**——Skill 从不持有、传输或存储任何私钥 |
| Agent 钱包 | EIP-712 签名授权，用户掌控权限 |
| 交易数据 | 由 0x 协议生成，含 MEV 保护（防三明治攻击） |
| 滑点 | 可配置最大滑点（默认 0.5%），链上强制 `minBuyAmount` |
| 风控 | 三级确认机制防止误操作大额交易 |
| 兑换页面 | 独立 HTML，无后端通信，无 Cookie，无追踪 |

## 更新日志

### v2.0.6 (2026-06-26)
- ✅ 行情工具合并——`hyperliquid-price` + `hyperliquid-book` + `hyperliquid-funding` 合并为单个 `hyperliquid-market`，新增 `view` 参数（`price` 默认 / `book` 需 `coin`+`depth?` / `funding` 用 `limit?`+`coin?`）；Hyperliquid 14→12、总数 23→21

### v2.0.4 (2026-06-15)
- ✅ MCP 工具名同步改名——14 个永续工具 `hl-*` → `hyperliquid-*`，与线上 MCP 对齐，修复改名后永续调用断引用
- ✅ 文档工具计数修正——工具总数 24→23、Hyperliquid 15→14

### v2.0.3 (2026-04-07)
- ✅ MCP 工具全量上线——24 个工具完整配置（swap ×5 + smart-swap ×4 + hl ×15）
- ✅ SKILL.md 全面更新——补充 Hyperliquid 完整功能文档、三级风控、余额检查、容错恢复
- ✅ 前端目录结构标准化——`scripts/`、`references/`、`tests/`、`examples/` 统一规范
- ✅ 新增 install.sh——一键安装脚本，自动处理依赖
- ✅ 安全文档 `references/SECURITY.md`——零托管安全说明

### v2.0.1 (2026-04-05)
- ✅ 三级风控确认——<$100 自动 / $100-1000 单次 / ≥$1000 或 ≥10x 双重确认
- ✅ 交易前余额检查——提前拦截余额不足订单
- ✅ 订单修改——原子性修改价格和数量
- ✅ 容错恢复——防止重复成交

### v2.0.0 (2026-04-05)
- ✅ Hyperliquid CLOB 限价单 & 永续合约——v2 核心新能力
- ✅ Agent 钱包零托管模式——签名一次，AI 自主交易
- ✅ 主网端到端验证通过

### v1.0.0 (2026-03-27)
- 初始版本：赛博朋克兑换页面，4 大钱包支持，完整 CLI 工具链

## 许可证

MIT · Powered by Antalpha AI
