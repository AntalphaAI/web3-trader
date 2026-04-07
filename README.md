# 🔄 Web3 Trader Skill v2.0.3

> **AI-Native DEX Trading + Hyperliquid Perp | Zero Custody | Multi-Wallet | Cyberpunk UI**
>
> Powered by Antalpha AI · v1 DEX Swap + v2 Hyperliquid CLOB & Perpetuals

---

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

---

## Two Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| 🌐 **MCP Remote Mode** (Recommended) | Antalpha MCP Server handles quote + page hosting | Production, no local API key needed |
| 🖥️ **Local CLI Mode** (Fallback) | Python CLI calls 0x API locally | Dev/debug, offline environments |

---

## MCP Server

```
https://mcp-skills.ai.antalpha.com/mcp
```

### Available MCP Tools (24 total)

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

#### v2 — Hyperliquid (15 tools)

| Tool | Description |
|------|-------------|
| `hl-price` | Real-time price for any trading pair |
| `hl-account` | Account info (balance, margin, equity) |
| `hl-book` | Order book depth |
| `hl-orders` | List open orders |
| `hl-positions` | List open positions |
| `hl-funding` | Funding rate rankings |
| `hl-balance-check` | Pre-trade balance check (spot or perp) |
| `hl-limit-order` | Place CLOB limit order |
| `hl-market-order` | Place perpetual market order |
| `hl-close` | One-click market close position |
| `hl-cancel` | Cancel open order |
| `hl-leverage` | Set leverage for a trading pair |
| `hl-tp-sl` | Set take-profit / stop-loss trigger orders |
| `hl-modify-order` | Atomically modify price and size of open order |

---

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

## Quick Start

### Install

```bash
git clone https://github.com/AntalphaAI/web3-trader.git
cd web3-trader
bash install.sh
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

---

## v2 Feature Details

### Agent Wallet (Zero Custody)

User signs `approveAgent` once via `scripts/hl_approve_agent.html`. After that, the AI agent can trade autonomously — private keys never leave the user's wallet.

```
User → MetaMask → sign approveAgent (EIP-712)
                       ↓
              Agent Wallet activated
                       ↓
AI Agent → hl-limit-order / hl-market-order → Hyperliquid CLOB
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

---

## Supported Wallets

| Wallet | Protocol | Status |
|--------|----------|--------|
| 🦊 MetaMask | `metamask.app.link/dapp/` | ✅ Verified |
| 💎 OKX Web3 | `okx://wallet/dapp/details` | ✅ Verified |
| 🛡️ Trust Wallet | `link.trustwallet.com/open_url` | ✅ Verified |
| 📱 TokenPocket | `tpdapp://open` | ✅ Verified |

---

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

---

## Security

| Layer | Protection |
|-------|-----------|
| Private Keys | **Zero contact** — skill never holds, transmits, or stores any private key |
| Agent Wallet | EIP-712 signed authorization, user controls permissions |
| Transaction Data | Generated by 0x Protocol with MEV protection (anti-sandwich) |
| Slippage | Configurable max slippage (default 0.5%), `minBuyAmount` enforced on-chain |
| Risk Control | 3-tier confirmation prevents accidental large trades |
| Swap Pages | Self-contained HTML, no backend communication, no cookies, no tracking |

---

## Changelog

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
- **[P2]** Fix HTML `lang="zh"` → `lang="en"`

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
