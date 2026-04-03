/**
 * 0x allowance-holder API v2 — price / quote / gas hint / token list.
 */
import { Inject, Injectable, Logger, OnModuleInit } from "@nestjs/common";
import { ConfigType } from "@nestjs/config";
import axios, { type AxiosInstance } from "axios";

import { web3TraderConfig } from "./web3-trader.config";

export const TOKENS: Record<string, TokenMeta> = {
  // ── Native & Wrapped ──
  ETH: { address: "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", decimals: 18, name: "Ethereum" },
  WETH: { address: "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2", decimals: 18, name: "Wrapped Ether" },

  // ── Stablecoins ──
  USDT: { address: "0xdac17f958d2ee523a2206206994597c13d831ec7", decimals: 6, name: "Tether USD" },
  USDC: { address: "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", decimals: 6, name: "USD Coin" },
  DAI: { address: "0x6b175474e89094c44da98b954eedeac495271d0f", decimals: 18, name: "Dai Stablecoin" },
  FDUSD: { address: "0xc5f0f7b66764f6ec8c8dff7ba683102295e16409", decimals: 18, name: "First Digital USD" },
  TUSD: { address: "0x0000000000085d4780b73119b644ae5ecd22b376", decimals: 18, name: "TrueUSD" },
  USDD: { address: "0x0c10bf8fcb7bf5412187a595ab97a3609160b5c6", decimals: 18, name: "Decentralized USD" },
  PYUSD: { address: "0x6c3ea9036406852006290770bedfcaba0e23a0e8", decimals: 6, name: "PayPal USD" },
  FRAX: { address: "0x853d955acef822db058eb8505911ed77f175b99e", decimals: 18, name: "Frax" },
  USDE: { address: "0x4c9edd5852cd905f086c759e8383e09bff1e68b3", decimals: 18, name: "Ethena USDe" },
  // CRVUSD excluded: 1inch Fusion returns "use legacy mode" (not supported in Fusion v2)
  GHO: { address: "0x40d16fc0246ad3160ccc09b8d0d3a2cd28ae6c2f", decimals: 18, name: "Aave GHO" },
  LUSD: { address: "0x5f98805a4e8be255a32880fdec7f6728c6568ba0", decimals: 18, name: "Liquity USD" },

  // ── BTC Wrapped ──
  WBTC: { address: "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599", decimals: 8, name: "Wrapped BTC" },

  // ── ETH Liquid Staking ──
  STETH: { address: "0xae7ab96520de3a18e5e111b5eaab095312d7fe84", decimals: 18, name: "Lido Staked ETH" },
  WSTETH: { address: "0x7f39c581f595b53c5cb19bd0b3f8da6c935e2ca0", decimals: 18, name: "Wrapped stETH" },
  RETH: { address: "0xae78736cd615f374d3085123a210448e74fc6393", decimals: 18, name: "Rocket Pool ETH" },
  CBETH: { address: "0xbe9895146f7af43049ca1c1ae358b0541ea49704", decimals: 18, name: "Coinbase Wrapped Staked ETH" },
  // SFRXETH excluded: 1inch Fusion returns "cannot fetch price"

  // ── DeFi Blue Chips ──
  LINK: { address: "0x514910771af9ca656af840dff83e8264ecf986ca", decimals: 18, name: "Chainlink" },
  UNI: { address: "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984", decimals: 18, name: "Uniswap" },
  AAVE: { address: "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9", decimals: 18, name: "Aave" },
  MKR: { address: "0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2", decimals: 18, name: "Maker" },
  LDO: { address: "0x5a98fcbea516cf06857215779fd812ca3bef1b32", decimals: 18, name: "Lido DAO" },
  CRV: { address: "0xd533a949740bb3306d119cc777fa900ba034cd52", decimals: 18, name: "Curve DAO" },
  SNX: { address: "0xc011a73ee8576fb46f5e1c5751ca3b9fe0af2a6f", decimals: 18, name: "Synthetix" },
  COMP: { address: "0xc00e94cb662c3520282e6f5717214004a7f26888", decimals: 18, name: "Compound" },
  "1INCH": { address: "0x111111111117dc0aa78b770fa6a738034120c302", decimals: 18, name: "1inch" },
  SUSHI: { address: "0x6b3595068778dd592e39a122f4f5a5cf09c90fe2", decimals: 18, name: "SushiSwap" },
  RPL: { address: "0xd33526068d116ce69f19a9ee46f0bd304f21a51f", decimals: 18, name: "Rocket Pool" },
  ENS: { address: "0xc18360217d8f7ab5e7c516566761ea12ce7f9d72", decimals: 18, name: "Ethereum Name Service" },
  DYDX: { address: "0x92d6c1e31e14520e676a687f0a93788b716beff5", decimals: 18, name: "dYdX" },
  BAL: { address: "0xba100000625a3754423978a60c9317c58a424e3d", decimals: 18, name: "Balancer" },
  PENDLE: { address: "0x808507121b80c02388fad14726482e061b8da827", decimals: 18, name: "Pendle" },
  ENA: { address: "0x57e114b691db790c35207b2e685d4a43181e6061", decimals: 18, name: "Ethena" },
  FXS: { address: "0x3432b6a60d23ca0dfca7761b7ab56459d9c964d0", decimals: 18, name: "Frax Share" },

  // ── Layer 2 / Infra (ERC-20 on Ethereum Mainnet) ──
  ARB: { address: "0xb50721bcf8d664c30412cfbc6cf7a15145234ad1", decimals: 18, name: "Arbitrum" },
  MATIC: { address: "0x7d1afa7b718fb893db30a3abc0cfc608aacfebb0", decimals: 18, name: "Polygon" },
  GRT: { address: "0xc944e90c64b2c07662a292be6244bdf05cda44a7", decimals: 18, name: "The Graph" },
  FET: { address: "0xaea46a60368a7bd060eec7df8cba43b7ef41ad85", decimals: 18, name: "Fetch.AI" },
  IMX: { address: "0xf57e7e7c23978c3caec3c3548e3d615c346e79ff", decimals: 18, name: "ImmutableX" },
  RNDR: { address: "0x6de037ef9ad2725eb40118bb1702ebb27e4aeb24", decimals: 18, name: "Render Token" },
  EIGEN: { address: "0xec53bf9167f50cdeb3ae105f56099aaab9061f83", decimals: 18, name: "EigenLayer" },
  SSV: { address: "0x9d65ff81a3c488d585bbfb0bfe3c7707c7917f54", decimals: 18, name: "SSV Network" },

  // ── Metaverse / Gaming ──
  MANA: { address: "0x0f5d2fb29fb7d3cfee444a200298f468908cc942", decimals: 18, name: "Decentraland" },
  SAND: { address: "0x3845badade8e6dff049820680d1f14bd3903a5d0", decimals: 18, name: "The Sandbox" },
  APE: { address: "0x4d224452801aced8b2f0aebe155379bb5d594381", decimals: 18, name: "ApeCoin" },

  // ── Meme ──
  SHIB: { address: "0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce", decimals: 18, name: "Shiba Inu" },
  PEPE: { address: "0x6982508145454ce325ddbe47a25d4ec3d2311933", decimals: 18, name: "Pepe" },
  // FLOKI excluded: 1inch Fusion rejects "tokens with fee on transfers"
  BONE: { address: "0x9813037ee2218799597d83d4a5b6f3b6778218d9", decimals: 18, name: "Bone ShibaSwap" },

  // ── Others (high mcap) ──
  WLD: { address: "0x163f8c2467924be0ae7b5347228cabf260318753", decimals: 18, name: "Worldcoin" },
  // BLUR excluded: 1inch Fusion returns "cannot sync token"
};

export interface TokenMeta {
  address: string;
  decimals: number;
  name: string;
}

export interface PriceResult {
  sellToken: string;
  buyToken: string;
  sellAmount: string;
  buyAmount: string;
  minBuyAmount: string;
  price: string;
  gasEstimate: number;
  gasPriceGwei: string;
  route: Array<{ source: string; proportion: string }>;
  liquidityAvailable: boolean;
}

export interface QuoteResult extends PriceResult {
  tx: {
    to: string;
    value: string;
    data: string;
    gas: string;
    gasPrice: string;
  };
}

const DEFAULT_TAKER = "0x70a9f34f9b34c64957b9c401a97bfed35b95049e";

@Injectable()
export class ZeroExService implements OnModuleInit {
  private readonly logger = new Logger(ZeroExService.name);
  private http!: AxiosInstance;

  constructor(
    @Inject(web3TraderConfig.KEY)
    private readonly cfg: ConfigType<typeof web3TraderConfig>,
  ) {}

  onModuleInit(): void {
    if (!this.cfg.zeroExApiKey) {
      this.logger.warn("ZEROEX_API_KEY is not set — web3-trader quote/price calls will fail");
    }
    this.http = axios.create({
      baseURL: "https://api.0x.org/swap/allowance-holder",
      headers: {
        "0x-api-key": this.cfg.zeroExApiKey,
        "0x-version": "v2",
        Accept: "application/json",
      },
      timeout: 15_000,
    });
  }

  async getPrice(
    sellToken: string,
    buyToken: string,
    sellAmount: string,
    chainId?: number,
    taker?: string,
  ): Promise<PriceResult> {
    const sell = this.resolveToken(sellToken);
    const buy = this.resolveToken(buyToken);
    const sellWei = this.toWei(sellAmount, sell.decimals);

    const { data } = await this.http.get<Record<string, unknown>>("/price", {
      params: {
        chainId: chainId ?? this.cfg.defaultChainId,
        sellToken: sell.address,
        buyToken: buy.address,
        sellAmount: sellWei,
        taker: taker ?? DEFAULT_TAKER,
      },
    });

    return this.parsePriceResponse(data, sellToken, buyToken, sellAmount, buy.decimals);
  }

  async getQuote(
    sellToken: string,
    buyToken: string,
    sellAmount: string,
    taker: string,
    chainId?: number,
  ): Promise<QuoteResult> {
    const sell = this.resolveToken(sellToken);
    const buy = this.resolveToken(buyToken);
    const sellWei = this.toWei(sellAmount, sell.decimals);

    const { data } = await this.http.get<Record<string, unknown>>("/quote", {
      params: {
        chainId: chainId ?? this.cfg.defaultChainId,
        sellToken: sell.address,
        buyToken: buy.address,
        sellAmount: sellWei,
        taker,
      },
    });

    const base = this.parsePriceResponse(data, sellToken, buyToken, sellAmount, buy.decimals);
    const txRaw = data.transaction as Record<string, string> | undefined;
    const tx = txRaw ?? {};

    return {
      ...base,
      tx: {
        to: tx.to ?? "",
        value: tx.value ?? "0",
        data: tx.data ?? "",
        gas: String(tx.gas ?? data.gas ?? "0"),
        gasPrice: String(tx.gasPrice ?? data.gasPrice ?? "0"),
      },
    };
  }

  async getGasInfo(chainId?: number): Promise<{ gasPriceGwei: string; estimatedGas: number }> {
    const { data } = await this.http.get<Record<string, unknown>>("/price", {
      params: {
        chainId: chainId ?? this.cfg.defaultChainId,
        sellToken: TOKENS.USDC.address,
        buyToken: TOKENS.WETH.address,
        sellAmount: "1000000",
        taker: DEFAULT_TAKER,
      },
    });
    const gpWei = Number(data.gasPrice ?? 0);
    return {
      gasPriceGwei: (gpWei / 1e9).toFixed(2),
      estimatedGas: Number(data.gas ?? 0),
    };
  }

  listTokens(search?: string): Array<TokenMeta & { symbol: string }> {
    const entries = Object.entries(TOKENS).map(([symbol, meta]) => ({ symbol, ...meta }));
    if (!search) {
      return entries;
    }
    const q = search.toLowerCase();
    return entries.filter((t) => t.symbol.toLowerCase().includes(q) || t.name.toLowerCase().includes(q));
  }

  resolveToken(symbolOrAddress: string): TokenMeta {
    const upper = symbolOrAddress.toUpperCase();
    if (TOKENS[upper]) {
      return TOKENS[upper];
    }
    if (/^0x[a-fA-F0-9]{40}$/.test(symbolOrAddress)) {
      const found = Object.values(TOKENS).find((t) => t.address.toLowerCase() === symbolOrAddress.toLowerCase());
      if (found) {
        return found;
      }
      return { address: symbolOrAddress.toLowerCase(), decimals: 18, name: "Unknown" };
    }
    throw new Error(
      `Unsupported token: ${symbolOrAddress}. Use swap-tokens tool to see the full list, or pass a valid 0x-prefixed ERC-20 address.`,
    );
  }

  /** Resolve a contract address to its symbol, or return empty string if unknown. */
  resolveSymbol(address: string): string {
    if (!address || !/^0x[a-fA-F0-9]{40}$/.test(address)) return "";
    const entry = Object.entries(TOKENS).find(([, t]) => t.address.toLowerCase() === address.toLowerCase());
    return entry ? entry[0] : "";
  }

  /** Resolve a contract address to its decimals (default 18 if unknown). */
  resolveDecimals(address: string): number {
    if (!address || !/^0x[a-fA-F0-9]{40}$/.test(address)) return 18;
    const found = Object.values(TOKENS).find((t) => t.address.toLowerCase() === address.toLowerCase());
    return found ? found.decimals : 18;
  }

  private toWei(humanAmount: string, decimals: number): string {
    const num = Number(humanAmount);
    if (Number.isNaN(num) || num <= 0) {
      throw new Error(`Invalid amount: ${humanAmount}`);
    }
    return BigInt(Math.round(num * 10 ** decimals)).toString();
  }

  private parsePriceResponse(
    data: Record<string, unknown>,
    sellToken: string,
    buyToken: string,
    sellAmount: string,
    buyDecimals: number,
  ): PriceResult {
    const buyAmountRaw = Number(data.buyAmount ?? 0) / 10 ** buyDecimals;
    const sellNum = Number(sellAmount);
    const price = sellNum > 0 ? buyAmountRaw / sellNum : 0;
    const minBuy = Number(data.minBuyAmount ?? 0) / 10 ** buyDecimals;

    const routeObj = data.route as { fills?: Array<Record<string, unknown>> } | undefined;
    const route = (routeObj?.fills ?? []).map((f) => ({
      source: String(f.source ?? "Unknown"),
      proportion: `${(Number(f.proportionBps ?? 0) / 100).toFixed(1)}%`,
    }));

    const gpWei = Number(data.gasPrice ?? 0);

    return {
      sellToken: sellToken.toUpperCase(),
      buyToken: buyToken.toUpperCase(),
      sellAmount,
      buyAmount: buyAmountRaw.toFixed(6),
      minBuyAmount: minBuy.toFixed(6),
      price: price.toFixed(4),
      gasEstimate: Number(data.gas ?? 0),
      gasPriceGwei: (gpWei / 1e9).toFixed(2),
      route,
      liquidityAvailable: Boolean(data.liquidityAvailable),
    };
  }
}
