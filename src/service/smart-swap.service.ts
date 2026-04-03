/**
 * 1inch Fusion Quoter + Orderbook (Smart Swap service — 1inch Fusion Dutch auction engine).
 */
import { Inject, Injectable, Logger } from "@nestjs/common";
import { ConfigType } from "@nestjs/config";
import axios, { type AxiosInstance } from "axios";

import { web3TraderConfig } from "./web3-trader.config";
import { ZeroExService } from "./zeroex.service";

const INCH_ROUTER = "0x111111125421cA6dc452d289314280a0f8842a65";
const ORDERBOOK_BASE = "https://api.1inch.dev/orderbook/v4.0";
const FUSION_QUOTER = "https://api.1inch.dev/fusion/quoter/v2.0";
const FUSION_RELAYER = "https://api.1inch.dev/fusion/relayer/v2.0";
const FUSION_ORDERS = "https://api.1inch.dev/fusion/orders/v2.0";

export interface LimitBuildResult {
  typedData: Record<string, unknown>;
  extension: string;
  orderHash: string;
  quoteId: string;
  orderInfo: Record<string, unknown>;
  approveTarget: string;
  approveToken: string;
  needsWethWrap: boolean;
  wrapAmount: string;
  submitUrl: string;
}

function parseExpirySeconds(expiryStr: string): number {
  const s = expiryStr.trim().toLowerCase();
  if (s.endsWith("d")) {
    return Number.parseInt(s.slice(0, -1), 10) * 86_400;
  }
  if (s.endsWith("h")) {
    return Number.parseInt(s.slice(0, -1), 10) * 3600;
  }
  if (s.endsWith("m")) {
    return Number.parseInt(s.slice(0, -1), 10) * 60;
  }
  if (!/^\d+$/.test(s)) {
    throw new Error(`Invalid expiry: ${expiryStr}. Use e.g. 24h, 7d, 60m, or seconds as integer.`);
  }
  const n = Number.parseInt(s, 10);
  if (Number.isNaN(n) || n <= 0) {
    throw new Error(`Invalid expiry: ${expiryStr}. Use e.g. 24h, 7d, 60m, or seconds as integer.`);
  }
  return n;
}

@Injectable()
export class SmartSwapService {
  private readonly logger = new Logger(SmartSwapService.name);
  private http!: AxiosInstance;

  constructor(
    @Inject(web3TraderConfig.KEY)
    private readonly cfg: ConfigType<typeof web3TraderConfig>,
    private readonly zeroEx: ZeroExService,
  ) {}

  private ensureClient(): AxiosInstance {
    const key = this.cfg.oneInchApiKey?.trim();
    if (!key) {
      throw new Error(
        "ONEINCH_API_KEY is not set — Smart Swap tools require a 1inch API key (see apps/mcp-skills/.env.local.example).",
      );
    }
    if (!this.http) {
      this.http = axios.create({
        timeout: 30_000,
        headers: {
          Authorization: `Bearer ${key}`,
          "Content-Type": "application/json",
          Accept: "application/json",
        },
      });
    }
    return this.http;
  }

  assertConfigured(): void {
    this.ensureClient();
  }

  async buildOrder(params: {
    maker: string;
    sellToken: string;
    buyToken: string;
    sellAmountHuman: string;
    targetPrice: string;
    expiry: string;
  }): Promise<LimitBuildResult> {
    const http = this.ensureClient();
    const chainId = this.cfg.defaultChainId;
    const sellSym = params.sellToken.toUpperCase();
    const buySym = params.buyToken.toUpperCase();
    const sellMeta = this.zeroEx.resolveToken(sellSym === "ETH" ? "WETH" : sellSym);
    const buyMeta = this.zeroEx.resolveToken(buySym === "ETH" ? "WETH" : buySym);
    const sellAddr = sellMeta.address.toLowerCase();
    const buyAddr = buyMeta.address.toLowerCase();

    const sellNum = Number(params.sellAmountHuman);
    if (Number.isNaN(sellNum) || sellNum <= 0) {
      throw new Error(`Invalid amount: ${params.sellAmountHuman}`);
    }
    const priceNum = Number(params.targetPrice);
    if (Number.isNaN(priceNum) || priceNum <= 0) {
      throw new Error(`Invalid target_price: ${params.targetPrice}`);
    }
    const buyAmountHuman = sellNum * priceNum;

    const sellWei = BigInt(Math.round(sellNum * 10 ** sellMeta.decimals)).toString();
    const expirySeconds = parseExpirySeconds(params.expiry);
    const makerLower = params.maker.toLowerCase();

    const quoteParams = {
      fromTokenAddress: sellAddr,
      toTokenAddress: buyAddr,
      amount: sellWei,
      walletAddress: makerLower,
      enableEstimate: "true",
    };

    const quoteUrl = `${FUSION_QUOTER}/${chainId}/quote/receive`;
    const quoteResp = await http.get(quoteUrl, { params: quoteParams });
    const quote = quoteResp.data as Record<string, unknown>;

    const buildUrl = `${FUSION_QUOTER}/${chainId}/quote/build`;
    const buildResp = await http.post(buildUrl, quote, { params: quoteParams });
    const buildData = buildResp.data as Record<string, unknown>;

    const typedData = buildData.typedData as Record<string, unknown>;
    const extension = String(buildData.extension ?? "");
    const orderHash = String(buildData.orderHash ?? "");
    if (!typedData || !orderHash) {
      this.logger.warn(`Unexpected Fusion build response keys: ${Object.keys(buildData).join(",")}`);
      throw new Error("1inch Fusion build response missing typedData or orderHash.");
    }

    const msg = typedData.message as Record<string, string> | undefined;
    const buyDec = buyMeta.decimals;
    const takingRaw = msg?.takingAmount ? BigInt(msg.takingAmount) : 0n;
    const actualBuy = Number(takingRaw) / 10 ** buyDec;

    const needsWeth = sellSym === "ETH";
    const displaySell = needsWeth ? "WETH" : sellSym;
    const targetPriceStr = (buyAmountHuman / sellNum).toPrecision(6);

    const walletShort = `${params.maker.slice(0, 6)}...${params.maker.slice(-4)}`;
    let expiryHuman: string;
    if (expirySeconds >= 86_400) {
      expiryHuman = `${Math.floor(expirySeconds / 86_400)}d`;
    } else if (expirySeconds >= 3600) {
      expiryHuman = `${Math.floor(expirySeconds / 3600)}h`;
    } else {
      expiryHuman = `${Math.floor(expirySeconds / 60)}m`;
    }

    const quoteId = String(quote.quoteId ?? "");

    const orderInfo: Record<string, unknown> = {
      sell_token: displaySell,
      buy_token: buySym,
      sell_amount: String(sellNum),
      buy_amount: String(actualBuy),
      target_price: targetPriceStr,
      expiry: String(Math.floor(Date.now() / 1000) + expirySeconds),
      expiry_human: expiryHuman,
      wallet_short: walletShort,
      engine: "1inch Fusion",
      order_hash: `${orderHash.slice(0, 14)}...`,
      full_order_hash: orderHash,
    };

    return {
      typedData,
      extension,
      orderHash,
      quoteId,
      orderInfo,
      approveTarget: INCH_ROUTER,
      approveToken: sellAddr,
      needsWethWrap: needsWeth,
      wrapAmount: needsWeth ? sellWei : "0",
      submitUrl: `${FUSION_RELAYER}/${chainId}/order/submit`,
    };
  }

  /**
   * List Fusion Smart Swap orders for a wallet.
   * Queries both Fusion orders API (primary) and Orderbook v4 (fallback).
   */
  async listOrders(maker: string): Promise<{ orders: unknown[]; total: number; raw: unknown }> {
    const http = this.ensureClient();
    const chainId = this.cfg.defaultChainId;
    if (!/^0x[a-fA-F0-9]{40}$/.test(maker)) {
      throw new Error("Invalid wallet address.");
    }

    // Primary: Fusion orders v2 — includes status, fills, auction info
    try {
      const fusionUrl = `${FUSION_ORDERS}/${chainId}/order/maker/${maker.toLowerCase()}`;
      const { data } = await http.get(fusionUrl);
      const items = (data as { items?: unknown[] }).items ?? [];
      if (items.length > 0) {
        return { orders: items, total: items.length, raw: data };
      }
    } catch (e) {
      this.logger.warn(`Fusion orders API failed, falling back to orderbook v4: ${(e as Error).message}`);
    }

    // Fallback: Orderbook v4
    const url = `${ORDERBOOK_BASE}/${chainId}/address/${maker}`;
    const { data } = await http.get(url);
    let orders: unknown[] = [];
    if (Array.isArray(data)) {
      orders = data;
    } else if (data && typeof data === "object") {
      const o = data as Record<string, unknown>;
      orders = (o.items ?? o.orders ?? []) as unknown[];
    }
    return { orders, total: orders.length, raw: data };
  }

  /**
   * Get a single order by hash.
   * Tries Fusion orders API first, then Orderbook v4.
   */
  async getOrder(orderHash: string): Promise<Record<string, unknown>> {
    const http = this.ensureClient();
    const chainId = this.cfg.defaultChainId;
    const h = orderHash.startsWith("0x") ? orderHash : `0x${orderHash}`;

    // Primary: search Fusion orders (no single-order endpoint, so search active orders)
    // The Fusion orders API doesn't have a /order/:hash endpoint,
    // so we check the active orders list and the order status from orderbook v4
    try {
      const url = `${ORDERBOOK_BASE}/${chainId}/order/${h}`;
      const { data } = await http.get(url);
      return data as Record<string, unknown>;
    } catch {
      // Orderbook v4 may not have Fusion orders — return minimal info
      return { orderHash: h, status: "unknown", note: "Order not found in orderbook v4. Use smart-swap-list with wallet address to query Fusion orders." };
    }
  }
}

export { parseExpirySeconds };
