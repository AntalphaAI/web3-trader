import { registerAs } from "@nestjs/config";

export const web3TraderConfig = registerAs("web3Trader", () => ({
  /** 0x Protocol API key — required for DEX quotes */
  zeroExApiKey: process.env.ZEROEX_API_KEY ?? "",
  /** 1inch API key (Bearer) — required for Smart Swap MCP tools (Fusion + orderbook) */
  oneInchApiKey: process.env.ONEINCH_API_KEY ?? "",
  /** Default chain ID (1 = Ethereum mainnet) */
  defaultChainId: Number(process.env.WEB3_TRADER_DEFAULT_CHAIN_ID ?? 1),
  /** Max slippage in basis points (50 = 0.5%); reserved for future API wiring */
  defaultSlippageBps: Number(process.env.WEB3_TRADER_DEFAULT_SLIPPAGE_BPS ?? 50),
  /** Base URL hint when page is already hosted (optional QR section in HTML) */
  swapHostBaseUrl: process.env.SWAP_HOST_BASE_URL ?? "",
  /**
   * Directory for persisted swap HTML files (one file per generation, never overwritten).
   * Required for swap-create-page / swap-full preview URLs.
   */
  htmlOutputDir: process.env.WEB3_TRADER_HTML_OUTPUT_DIR ?? "",
  /**
   * Public origin for GET /web3-trader/preview/:id (e.g. https://swap.example.com).
   * Default: http://127.0.0.1:${PORT}
   */
  publicBaseUrl: process.env.WEB3_TRADER_PUBLIC_BASE_URL ?? "",
}));
