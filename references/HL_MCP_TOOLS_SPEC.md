# Hyperliquid MCP Tools Specification

> For registration on Antalpha MCP Server (`mcp-skills.ai.antalpha.com/mcp`)

## Tool Naming Convention

All Hyperliquid tools prefixed with `hl-` to avoid collision with existing `swap-*` tools.

## Tools

### 1. `hl-price` — Get asset price(s)

**Input:**
```json
{
  "coin": "ETH"           // optional — omit for top-10 prices
}
```

**Output:**
```json
{
  "coin": "ETH",
  "price": 2055.85,
  "timestamp": 1712345678
}
```

---

### 2. `hl-account` — Get account summary

**Input:**
```json
{
  "address": "0x81f9c4..."
}
```

**Output:**
```json
{
  "perp": { "account_value": "9.79", "margin_used": "0", "withdrawable": "9.79" },
  "positions": [...],
  "spot_balances": [{"coin": "USDC", "total": "9.79"}],
  "open_orders_count": 0
}
```

---

### 3. `hl-book` — Get L2 order book

**Input:**
```json
{
  "coin": "ETH",
  "depth": 10              // optional, default 10
}
```

---

### 4. `hl-limit-order` — Place a limit order

**Input:**
```json
{
  "coin": "ETH",
  "side": "buy",           // "buy" | "sell"
  "price": 2000.0,
  "size": 0.01,
  "tif": "Gtc",            // optional: "Gtc" | "Ioc" | "Alo"
  "reduce_only": false      // optional
}
```

**Output:**
```json
{
  "status": "ok",
  "oid": 370822664367,
  "type": "resting"         // or "filled"
}
```

---

### 5. `hl-market-order` — Place a market order

**Input:**
```json
{
  "coin": "ETH",
  "side": "buy",
  "size": 0.01,
  "slippage": 0.01          // optional, default 1%
}
```

---

### 6. `hl-close` — Close a position at market

**Input:**
```json
{
  "coin": "ETH",
  "slippage": 0.01
}
```

---

### 7. `hl-cancel` — Cancel an order

**Input:**
```json
{
  "coin": "ETH",
  "oid": 370822664367
}
```

---

### 8. `hl-leverage` — Set leverage

**Input:**
```json
{
  "coin": "ETH",
  "leverage": 10,
  "mode": "cross"           // "cross" | "isolated"
}
```

---

### 9. `hl-tp-sl` — Place take-profit / stop-loss

**Input:**
```json
{
  "coin": "ETH",
  "type": "tp",             // "tp" | "sl"
  "side": "sell",
  "trigger_price": 2200.0,
  "size": 0.01
}
```

---

### 10. `hl-funding` — Get funding rates

**Input:**
```json
{
  "limit": 20               // optional
}
```

---

### 11. `hl-orders` — Get open orders

**Input:**
```json
{
  "address": "0x..."
}
```

---

### 12. `hl-positions` — Get open positions

**Input:**
```json
{
  "address": "0x..."
}
```

---

## Authentication

For write operations (hl-limit-order, hl-market-order, hl-close, hl-cancel, hl-leverage, hl-tp-sl):

- Server-side uses Agent Wallet mode
- Agent key stored securely on MCP server (per-user)
- Owner address associated via `hl-authorize` setup flow

For read operations (hl-price, hl-account, hl-book, hl-funding, hl-orders, hl-positions):
- No authentication needed

## NestJS Implementation Notes

- Module: `libs/skills/hyperliquid/src/`
- Depends on: `hyperliquid` npm SDK or direct REST calls
- All tools use Zod v3 for MCP registration
- Tool naming: lowercase with hyphens, globally unique
