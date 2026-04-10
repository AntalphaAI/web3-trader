# 🔄 Web3 Trader Skill v2.0.3

> **AI-Native DEX Trading + Hyperliquid Perp | Zero Custody | Multi-Wallet | Cyberpunk UI**
>
> **AI 原生 DEX 交易 + Hyperliquid 永续合约 | 零托管 | 多钱包支持 | 赛博朋克 UI**
>
> Powered by Antalpha AI · v1 DEX Swap + v2 Hyperliquid CLOB & Perpetuals

---

## Install / 安装

```bash
openclaw skill install https://github.com/AntalphaAI/web3-trader
```

---

## Features / 功能特性

### v1 — DEX Swap (Antalpha AI Aggregator)
- 💱 Real-time DEX quotes and optimal routing via Antalpha AI Aggregator / 通过 Antalpha AI 聚合器获取实时 DEX 报价和最优路由
- 🌐 Cyberpunk-style swap pages (Matrix rain animation + scanline effects) / 赛博朋克风格兑换页面（矩阵雨动画 + 扫描线特效）
- 📱 4 major wallets: MetaMask, OKX Web3, Trust Wallet, TokenPocket / 支持 4 大主流钱包
- 🔒 Zero custody — private keys never leave the user's wallet / 零托管——私钥永远不离开用户钱包
- 🤖 MCP remote mode — one `swap-full` call does quote + page hosting + QR / MCP 远程模式——一次 `swap-full` 调用完成报价 + 页面托管 + 二维码

### v2 — Hyperliquid CLOB & Perpetuals (NEW / 新功能)
- 📈 True limit orders on Hyperliquid on-chain CLOB order book / Hyperliquid 链上 CLOB 订单簿真实限价单
- ♾️ Perpetual contracts — 229+ trading pairs, up to 40x leverage / 永续合约——229+ 交易对，最高 40 倍杠杆
- 🤖 Agent Wallet zero-custody mode — user signs `approveAgent` once, AI trades automatically / Agent 钱包零托管模式——用户只需签名一次 `approveAgent`，AI 自动交易
- 🛡️ 3-tier risk control — auto / single-confirm / double-confirm by trade size / 三级风控——按交易规模自动/单次/双重确认
- 💰 Pre-trade balance check — rejects orders before they fail / 交易前余额检查——提前拦截余额不足的订单
- 🔁 Order modify & fail-safe recovery — prevent duplicate fills / 订单修改与容错恢复——防止重复成交
- 📊 Full position management — TP/SL, close, funding rate queries / 完整仓位管理——止盈止损、平仓、资金费率查询

---

## Two Modes / 两种模式

| Mode / 模式 | Description / 说明 | Use Case / 适用场景 |
|------|-------------|----------|
| 🌐 **MCP Remote Mode** (Recommended / 推荐) | Antalpha MCP Server handles quote + page hosting / MCP 服务器处理报价和页面托管 | Production, no local API key needed / 生产环境，无需本地 API Key |
| 🖥️ **Local CLI Mode** (Fallback / 备选) | Python CLI calls 0x API locally / Python CLI 本地调用 0x API | Dev/debug, offline environments / 开发调试、离线环境 |

---

## MCP Server

```
https://mcp-skills.ai.antalpha.com/mcp
```

### Available MCP Tools (24 total) / MCP 工具列表（共 24 个）

#### v1 — DEX Swap (5 tools / 5 个工具)

| Tool / 工具 | Description / 说明 |
|------|-------------|
| `swap-full` | **One-shot**: quote + generate page + host → returns URL + QR / **一步完成**：报价 + 生成页面 + 托管 → 返回链接 + 二维码 |
| `swap-quote` | Get DEX aggregated quote / 获取 DEX 聚合报价 |
| `swap-create-page` | Generate and host a cyberpunk swap page / 生成并托管赛博朋克风格兑换页面 |
| `swap-tokens` | List supported tokens / 查看支持的代币列表 |
| `swap-gas` | Current gas price / 当前 Gas 价格 |

#### v1 — Smart Swap (4 tools / 4 个工具)

| Tool / 工具 | Description / 说明 |
|------|-------------|
| `smart-swap-create` | Create a smart swap order with auto-routing / 创建自动路由的智能兑换订单 |
| `smart-swap-list` | List active smart swap orders / 查看活跃的智能兑换订单 |
| `smart-swap-status` | Query smart swap order status / 查询智能兑换订单状态 |
| `smart-swap-cancel` | Cancel a smart swap order / 取消智能兑换订单 |

#### v2 — Hyperliquid (15 tools / 15 个工具)

| Tool / 工具 | Description / 说明 |
|------|-------------|
| `hl-price` | Real-time price for any trading pair / 任意交易对实时价格 |
| `hl-account` | Account info (balance, margin, equity) / 账户信息（余额、保证金、净值） |
| `hl-book` | Order book depth / 订单簿深度 |
| `hl-orders` | List open orders / 查看挂单列表 |
| `hl-positions` | List open positions / 查看持仓列表 |
| `hl-funding` | Funding rate rankings / 资金费率排行 |
| `hl-balance-check` | Pre-trade balance check (spot or perp) / 交易前余额检查（现货或永续） |
| `hl-limit-order` | Place CLOB limit order / 挂限价单 |
| `hl-market-order` | Place perpetual market order / 下永续合约市价单 |
| `hl-close` | One-click market close position / 一键市价平仓 |
| `hl-cancel` | Cancel open order / 撤销挂单 |
| `hl-leverage` | Set leverage for a trading pair / 设置交易对杠杆倍数 |
| `hl-tp-sl` | Set take-profit / stop-loss trigger orders / 设置止盈止损触发单 |
| `hl-modify-order` | Atomically modify price and size of open order / 原子性修改挂单价格和数量 |

---

## Architecture / 架构

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
│  (OpenClaw)  │  hl-limit-order     │  mcp-skills.ai.antalpha.com       │
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

---

## Quick Start / 快速开始

### Install / 安装

**推荐方式 / Recommended:**

```bash
openclaw skill install https://github.com/AntalphaAI/web3-trader
```

**手动克隆 / Manual Clone:**

```bash
git clone https://github.com/AntalphaAI/web3-trader.git
cd web3-trader
bash install.sh
```

### MCP Remote Mode (Recommended / 推荐)

No local setup needed. Configure in OpenClaw / 无需本地配置，直接在 OpenClaw 中添加：

```
MCP Server: https://mcp-skills.ai.antalpha.com/mcp
```

### v1 — DEX Swap Example / 兑换示例

```bash
# Query price / 查询价格
python3 scripts/trader_cli.py price --from ETH --to USDT --amount 0.1

# Generate swap page / 生成兑换页面
python3 scripts/trader_cli.py swap-page --from ETH --to USDT --amount 0.1 \
  --wallet 0xYourAddress -o swap.html --json
```

### v2 — Hyperliquid CLI

```bash
# Set up agent wallet / 配置 Agent 钱包
cp references/config.example.yaml ~/.web3-trader/config.yaml

# Check price / 查询价格
python3 scripts/hl_cli.py price ETH

# Place limit order / 下限价单
python3 scripts/hl_cli.py limit-order --symbol ETH --side buy --price 2000 --size 0.01

# Open perpetual long / 开多
python3 scripts/hl_cli.py market-order --symbol ETH --side buy --size 0.01 --leverage 5

# View positions / 查看持仓
python3 scripts/hl_cli.py positions

# Close position / 平仓
python3 scripts/hl_cli.py close --symbol ETH
```

---

## v2 Feature Details / v2 功能详解

### Agent Wallet (Zero Custody / 零托管)

User signs `approveAgent` once via `scripts/hl_approve_agent.html`. After that, the AI agent can trade autonomously — private keys never leave the user's wallet.

用户通过 `scripts/hl_approve_agent.html` 一次性签名 `approveAgent`，之后 AI Agent 即可自主交易——私钥始终不离开用户钱包。

```
User → MetaMask → sign approveAgent (EIP-712)
                       ↓
              Agent Wallet activated / Agent 钱包激活
                       ↓
AI Agent → hl-limit-order / hl-market-order → Hyperliquid CLOB
```

### 3-Tier Risk Control (v2.0.1) / 三级风控

| Trade Value / 交易金额 | Confirmation Required / 确认方式 |
|-------------|----------------------|
| < $100 | Auto-execute / 自动执行 |
| $100 – $999 | Single confirmation / 单次确认 |
| ≥ $1000 or ≥ 10x leverage / ≥ $1000 或 ≥ 10 倍杠杆 | Double confirmation / 双重确认 |

### Supported Trading Pairs / 支持的交易对

| Category / 类别 | Examples / 示例 |
|----------|---------| 
| Perpetuals / 永续合约 | BTC, ETH, SOL, ARB, and 225+ more / 等 225+ 交易对 |
| Leverage / 杠杆倍数 | Up to 40x (pair-dependent) / 最高 40 倍（视交易对而定） |

---

## Supported Wallets / 支持的钱包

| Wallet / 钱包 | Protocol | Status / 状态 |
|--------|----------|--------|
| 🦊 MetaMask | `metamask.app.link/dapp/` | ✅ Verified |
| 💎 OKX Web3 | `okx://wallet/dapp/details` | ✅ Verified |
| 🛡️ Trust Wallet | `link.trustwallet.com/open_url` | ✅ Verified |
| 📱 TokenPocket | `tpdapp://open` | ✅ Verified |

---

## Project Structure / 项目结构

```
├── SKILL.md                        # Full skill spec (read by AI agent) / AI Agent 完整 Skill 规范
├── README.md                       # This file / 本文件
├── requirements.txt                # Python dependencies / Python 依赖
├── install.sh                      # One-click install script / 一键安装脚本
├── scripts/
│   ├── trader_cli.py               # v1 Swap CLI entry point / v1 兑换 CLI 入口
│   ├── zeroex_client.py            # Antalpha AI DEX API client / Antalpha AI DEX API 客户端
│   ├── swap_page_gen.py            # Cyberpunk swap page generator / 赛博朋克兑换页面生成器
│   ├── hl_client.py                # v2 Hyperliquid API client (agent wallet) / v2 Hyperliquid API 客户端
│   ├── hl_cli.py                   # v2 Hyperliquid CLI (18 commands) / v2 Hyperliquid CLI（18 条命令）
│   ├── hl_risk.py                  # v2.0.1 Risk engine (3-tier + balance check) / v2.0.1 风控引擎
│   ├── hl_approve_agent.html       # Agent Wallet authorization page / Agent 钱包授权页面
│   └── hl_transfer.html            # Spot↔Perp transfer page / 现货↔永续划转页面
├── references/
│   ├── config.example.yaml         # Config template / 配置模板
│   ├── HL_MCP_TOOLS_SPEC.md        # Hyperliquid MCP tools spec / Hyperliquid MCP 工具规范
│   ├── ANTALPHA_MCP_SERVER_SPEC.md # Antalpha MCP server spec / Antalpha MCP 服务规范
│   └── SECURITY.md                 # Security documentation / 安全文档
├── examples/
│   └── swap_usdt_eth.py            # Example swap script / 兑换示例脚本
└── tests/
    ├── test_zeroex_client.py
    ├── test_hl_client.py
    └── test_hl_integration.py
```

---

## Security / 安全性

| Layer / 层级 | Protection / 防护措施 |
|-------|-----------| 
| Private Keys / 私钥 | **Zero contact** — skill never holds, transmits, or stores any private key / **零接触**——Skill 从不持有、传输或存储任何私钥 |
| Agent Wallet / Agent 钱包 | EIP-712 signed authorization, user controls permissions / EIP-712 签名授权，用户掌控权限 |
| Transaction Data / 交易数据 | Generated by 0x Protocol with MEV protection (anti-sandwich) / 由 0x 协议生成，含 MEV 保护（防三明治攻击） |
| Slippage / 滑点 | Configurable max slippage (default 0.5%), `minBuyAmount` enforced on-chain / 可配置最大滑点（默认 0.5%），链上强制 `minBuyAmount` |
| Risk Control / 风控 | 3-tier confirmation prevents accidental large trades / 三级确认机制防止误操作大额交易 |
| Swap Pages / 兑换页面 | Self-contained HTML, no backend communication, no cookies, no tracking / 独立 HTML，无后端通信，无 Cookie，无追踪 |

---

## Changelog / 更新日志

### v2.0.3 (2026-04-07)
- ✅ **MCP Tools full rollout** — 24 tools fully configured (swap ×5 + smart-swap ×4 + hl ×15)
- ✅ **SKILL.md comprehensive update** — added full Hyperliquid feature docs, 3-tier risk control, balance check, fail-safe recovery
- ✅ **Frontend structure reorganized** — `scripts/`, `references/`, `tests/`, `examples/` standardized
- ✅ **install.sh added** — one-click install script with auto dependency setup
- ✅ **Security docs** `references/SECURITY.md` — zero-custody security documentation

### v2.0.2 (2026-04-06)
- ✅ **Fix `get_asset_index` missing** — `hl_client.py` adds asset lookup by name (BTC=0, ETH=1)
- ✅ **MCP Module comment fix** — tool count corrected from 12 → 14
- ✅ **`cliPath` deployment docs** — supports `HL_CLI_PATH` env override, added A/B config options

### v2.0.1 (2026-04-05)
- ✅ **3-tier risk confirmation** — <$100 auto / $100-1000 single confirm / ≥$1000 or ≥10x double confirm
- ✅ **Pre-trade balance check** — checks margin available before order, rejects if insufficient
- ✅ **Order modify** — `modify-order` command for atomic price/size changes
- ✅ **Fail-safe recovery** — checks userFills after error to prevent duplicate orders
- ✅ **New `hl_risk.py`** — standalone risk engine module

### v2.0.0 (2026-04-05)
- ✅ **Hyperliquid CLOB limit orders & perpetuals** — v2 core new capability
- ✅ **Agent Wallet zero-custody mode** — user signs `approveAgent` once, AI agent trades automatically
- ✅ **Mainnet end-to-end verified** — limit order place/cancel, market buy/close all successful
- ✅ **Unified Account compatible** — auto-detect, no manual spot↔perp transfer needed
- ✅ **Authorization page** `hl_approve_agent.html` + transfer page `hl_transfer.html`
- ✅ **MCP Tools spec** — `references/HL_MCP_TOOLS_SPEC.md`

### v1.0.4 (2026-03-28)
- **[P0]** Fix `examples/` and `tests/` using wrong parameter names (`wallet_address`/`slippage` → `taker`)
- **[P0]** Fix XSS vulnerability in `swap_page_gen.py` — all user-controlled data now escaped via `html.escape()`
- **[P0]** Remove auto-execute in dApp browser — users must explicitly click to confirm swap
- **[P1]** Add `timeout=30s` to all HTTP requests to prevent infinite hangs
- **[P1]** Preserve exception info in `get_gas_info()` error handling
- **[P1]** Add error handling for file write in `cmd_swap_page`
- **[P1]** Add missing `pyyaml` to `requirements.txt`
- **[P2]** Use `Decimal` for amount calculations instead of `float`
- **[P2]** Deduplicate `get_token_address` (alias to `_resolve_token`) and extract shared logic in `cmd_price`/`cmd_route`
- **[P2]** Fix HTML `lang=\"zh\"` → `lang=\"en\"`

### v1.0.3 (2026-03-28)
- Fix: `metadata` changed from multi-line YAML to single-line JSON (OpenClaw parser requirement)
- Fix: remove `ZEROEX_API_KEY` from `requires.env` (MCP mode doesn't need it; was causing load-time gating)
- Enhance: `description` now covers swap/兑换/卖出/买入/sell/buy/DEX trigger keywords for better intent matching

### v1.0.2 (2026-03-27)
- Agent behavior: no verbose output, only swap preview + QR code image
- QR code generated from MCP `preview_url` and sent as image attachment
- Updated message template with routing info

### v1.0.1 (2026-03-27)
- Antalpha MCP Server integration (`mcp-skills.ai.antalpha.com/mcp`)
- `swap-full` one-shot: quote + page generation + server hosting
- Swap pages hosted on trusted Antalpha domain
- Agent no longer needs local 0x API key

### v1.0.0 (2026-03-27)
- Cyberpunk swap pages (Matrix rain + scanline effects)
- 4 wallet support: MetaMask, OKX Web3, Trust Wallet, TokenPocket
- Auto-execute in wallet dApp browser (2s countdown)
- QR code generation (cyan on dark theme)
- Full CLI toolchain (price/route/build-tx/export/swap-page/gas/tokens)

---

## License

MIT

---

*Powered by Antalpha AI*
