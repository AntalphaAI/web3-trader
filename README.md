# @antalpha/web3-trader

DEX trading skill for the Antalpha AI MCP platform. Provides market swap (0x) and Smart Swap (1inch Fusion) capabilities.

## Quick Start

```bash
# Set environment variables
export ZEROEX_API_KEY="your-0x-api-key"
export ONEINCH_API_KEY="your-1inch-api-key"

# Start the MCP server (from monorepo root)
pnpm run start:dev
```

## Module Structure

```
libs/skills/web3-trader/src/
├── service/
│   ├── zeroex.service.ts          # 0x swap API client
│   ├── smart-swap.service.ts      # 1inch Fusion Smart Swap engine
│   ├── smart-swap-page.service.ts # Signing page HTML generator
│   ├── swap-page.service.ts       # Market swap page generator
│   ├── swap-html-file.service.ts  # HTML file writer
│   └── web3-trader.config.ts      # Environment config
├── tools/
│   └── web3-trader.tools.ts       # MCP tool definitions
├── web3-trader.module.ts          # NestJS module
└── index.ts                       # Public exports
```

## MCP Tools

### Market Swap (0x)

| Tool | Method | Description |
|------|--------|-------------|
| `swap-quote` | GET | Indicative price — no commitment |
| `swap-full` | GET | Firm quote with transaction calldata |
| `swap-tokens` | GET | List supported token symbols |
| `swap-gas` | GET | Current gas price (Gwei) |

### Smart Swap (1inch Fusion)

| Tool | Method | Description |
|------|--------|-------------|
| `smart-swap-create` | POST | Create a Fusion Dutch auction order |
| `smart-swap-list` | GET | List orders by wallet address |
| `smart-swap-status` | GET | Order status by hash |
| `smart-swap-cancel` | GET | Check cancellation status/options |

## Smart Swap Flow

```
1. Agent calls smart-swap-create(sell_token, buy_token, sell_amount, target_price, ...)
2. Server fetches Fusion quote → injects custom auctionEndAmount (user's floor price)
3. Server builds EIP-712 typed data + generates signing page HTML
4. Returns: typed_data, preview_url, qr_image_url
5. User opens signing page → connects wallet → signs EIP-712 → submits to Fusion relayer
6. Resolver network fills the order (user pays zero gas)
7. Agent checks status via smart-swap-status or smart-swap-list
```

## Smart Swap Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `sell_token` | string | Token to sell (symbol or 0x address) |
| `buy_token` | string | Token to buy (symbol or 0x address) |
| `sell_amount` | string | Amount to sell (human-readable, e.g. "0.1") |
| `target_price` | string | Floor price — minimum acceptable rate |
| `expiry` | string | Order expiry (e.g. "10m", "1h", default "10m") |
| `wallet` | string | Maker wallet address (0x...) |
| `engine` | string | Always "1inch" (default) |

## Signing Page

The signing page is a self-contained HTML file with:

- **Zero external dependencies** (no CDN, no Google Fonts)
- **4 wallet connectors**: MetaMask, OKX Web3, Trust Wallet, TokenPocket
- **DApp browser detection**: Auto-connects in wallet DApp browsers
- **USDT compatibility**: `approve(0)` → wait → `approve(max)` flow
- **Cyberpunk UI**: Dark theme, neon accents, step-by-step progress
- **Wallet validation**: Checks connected address matches order maker

## USDT Approve Handling

USDT requires `approve(0)` before setting a new allowance (if current > 0). The signing page automatically:

1. Checks current allowance
2. If > 0: sends `approve(0)`, waits for confirmation
3. Sends `approve(maxUint256)`
4. Proceeds to EIP-712 signing

This is safe for all ERC-20 tokens (only USDT-like tokens actually need the double approve).

## Token List

50 tokens supported on Ethereum mainnet. See `TOKENS` constant in `zeroex.service.ts`.

## Configuration

All config via environment variables (see `web3-trader.config.ts`):

```typescript
export const web3TraderConfig = registerAs("web3-trader", () => ({
  zeroExApiKey: process.env.ZEROEX_API_KEY ?? "",
  oneInchApiKey: process.env.ONEINCH_API_KEY ?? "",
  defaultChainId: Number(process.env.WEB3_TRADER_DEFAULT_CHAIN_ID ?? 1),
  defaultSlippageBps: Number(process.env.WEB3_TRADER_DEFAULT_SLIPPAGE_BPS ?? 100),
  swapHostBaseUrl: process.env.SWAP_HOST_BASE_URL ?? "https://api.0x.org/swap/allowance-holder",
  htmlOutputDir: process.env.WEB3_TRADER_HTML_OUTPUT_DIR ?? "/tmp/web3-trader-pages",
  publicBaseUrl: process.env.WEB3_TRADER_PUBLIC_BASE_URL ?? "",
}));
```

## Dependencies

- `@modelcontextprotocol/sdk` — MCP protocol
- `axios` — HTTP client
- `zod/v3` — Schema validation for MCP tools
- `@antalpha/libs-shared` — Shared utilities

## License

Proprietary — Antalpha AI
