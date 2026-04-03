import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { Inject, Injectable, Logger } from "@nestjs/common";
import { ConfigType } from "@nestjs/config";
import { z } from "zod/v3";

import {
  formatUnknownToolError,
  getMcpClientIp,
  type McpToolProvider,
  makeUnexpectedToolError,
} from "@antalpha/libs-shared";
import { SmartSwapService } from "../service/smart-swap.service";
import { SmartSwapPageService } from "../service/smart-swap-page.service";
import { SwapHtmlFileService } from "../service/swap-html-file.service";
import { SwapPageService } from "../service/swap-page.service";
import { web3TraderConfig } from "../service/web3-trader.config";
import { ZeroExService } from "../service/zeroex.service";

const tokenDesc = 'Token symbol (e.g. "ETH", "USDT") or ERC-20 contract address (0x-prefixed, 40 hex chars)';
const chainDesc = "EVM chain ID. Default 1 (Ethereum mainnet).";

const routeLegShape = {
  source: z.string(),
  proportion: z.string(),
};

const txShape = {
  to: z.string(),
  value: z.string(),
  data: z.string(),
  gas: z.string(),
  gasPrice: z.string(),
};

@Injectable()
export class Web3TraderTools implements McpToolProvider {
  private readonly logger = new Logger(Web3TraderTools.name);

  constructor(
    private readonly zeroEx: ZeroExService,
    private readonly swapPage: SwapPageService,
    private readonly swapHtmlFile: SwapHtmlFileService,
    private readonly smartSwap: SmartSwapService,
    private readonly smartSwapPage: SmartSwapPageService,
    @Inject(web3TraderConfig.KEY)
    private readonly wtCfg: ConfigType<typeof web3TraderConfig>,
  ) {}

  register(server: McpServer, filter?: Set<string>): void {
    const should = (name: string) => !filter || filter.has(name);

    if (should("swap-quote")) {
      server.registerTool(
        "swap-quote",
        {
          description:
            "Real-time DEX aggregated swap quote via 0x allowance-holder. Returns buy amount, min receive, gas, route; includes full tx (to/value/data/gas) when taker address is provided.",
          inputSchema: {
            sell_token: z.string().describe(tokenDesc),
            buy_token: z.string().describe(tokenDesc),
            sell_amount: z.string().describe('Sell amount in human-readable form (e.g. "0.001", "1000")'),
            taker: z
              .string()
              .optional()
              .describe(
                "Optional 0x wallet; when set, response includes firm quote transaction fields for eth_sendTransaction",
              ),
            chain_id: z.number().int().positive().optional().describe(chainDesc),
          },
          outputSchema: {
            sell_token: z.string(),
            buy_token: z.string(),
            sell_amount: z.string(),
            buy_amount: z.string(),
            min_buy_amount: z.string(),
            price: z.string(),
            gas_estimate: z.number(),
            gas_price_gwei: z.string(),
            route: z.array(z.object(routeLegShape)),
            liquidity_available: z.boolean(),
            tx: z.object(txShape).optional(),
          },
        },
        async (input) => {
          try {
            const hasTaker = Boolean(input.taker);
            const result = hasTaker
              ? await this.zeroEx.getQuote(
                  input.sell_token,
                  input.buy_token,
                  input.sell_amount,
                  input.taker as string,
                  input.chain_id,
                )
              : await this.zeroEx.getPrice(
                  input.sell_token,
                  input.buy_token,
                  input.sell_amount,
                  input.chain_id,
                  input.taker,
                );

            const structuredContent: Record<string, unknown> = {
              sell_token: result.sellToken,
              buy_token: result.buyToken,
              sell_amount: result.sellAmount,
              buy_amount: result.buyAmount,
              min_buy_amount: result.minBuyAmount,
              price: result.price,
              gas_estimate: result.gasEstimate,
              gas_price_gwei: result.gasPriceGwei,
              route: result.route,
              liquidity_available: result.liquidityAvailable,
            };
            if ("tx" in result) {
              structuredContent.tx = (result as { tx: unknown }).tx;
            }
            this.logIp("swap-quote");
            return this.ok(structuredContent);
          } catch (e) {
            return this.failSwapQuote(e);
          }
        },
      );
    }

    if (should("swap-create-page")) {
      server.registerTool(
        "swap-create-page",
        {
          description:
            "Firm 0x quote + cyberpunk swap page. HTML is written under WEB3_TRADER_HTML_OUTPUT_DIR; response preview_url is always this server's GET /web3-trader/preview/:file_id (use this to open the page and for wallet deeplinks). Optional hosted_url only changes the text URL printed in the page QR section; it does not change where the file is stored.",
          inputSchema: {
            sell_token: z.string().describe(tokenDesc),
            buy_token: z.string().describe(tokenDesc),
            sell_amount: z.string().describe("Human-readable sell amount"),
            taker: z
              .string()
              .regex(/^0x[a-fA-F0-9]{40}$/)
              .describe("Taker address (required for firm quote)"),
            chain_id: z.number().int().positive().optional().describe(chainDesc),
            hosted_url: z
              .string()
              .url()
              .optional()
              .describe(
                "Optional: URL shown in the page footer block only; actual page is still at preview_url on this service",
              ),
          },
          outputSchema: {
            preview_url: z.string().describe("Open in browser — same host as mcp-skills"),
            file_id: z.string().describe("Unique id; file is {file_id}.html under output dir"),
            html_size_bytes: z.number(),
            wallets_supported: z.array(z.string()),
            quote: z.object({
              sell_token: z.string(),
              buy_token: z.string(),
              sell_amount: z.string(),
              buy_amount: z.string(),
              min_buy_amount: z.string(),
              price: z.string(),
            }),
          },
        },
        async (input) => {
          try {
            const quote = await this.zeroEx.getQuote(
              input.sell_token,
              input.buy_token,
              input.sell_amount,
              input.taker,
              input.chain_id,
            );
            const { fileId, previewUrl } = this.swapHtmlFile.allocatePreviewTarget();
            const page = this.swapPage.generate({
              quote,
              hostedUrl: input.hosted_url ?? previewUrl,
            });
            await this.swapHtmlFile.writeHtmlForId(fileId, page.html);
            const structuredContent = {
              preview_url: previewUrl,
              file_id: fileId,
              html_size_bytes: page.htmlSizeBytes,
              wallets_supported: page.walletsSupported,
              quote: {
                sell_token: quote.sellToken,
                buy_token: quote.buyToken,
                sell_amount: quote.sellAmount,
                buy_amount: quote.buyAmount,
                min_buy_amount: quote.minBuyAmount,
                price: quote.price,
              },
            };
            this.logIp("swap-create-page");
            return this.ok(structuredContent as Record<string, unknown>);
          } catch (e) {
            return this.fail("swap-create-page", e);
          }
        },
      );
    }

    if (should("swap-tokens")) {
      server.registerTool(
        "swap-tokens",
        {
          description:
            "List built-in mainnet tokens (symbol, name, address, decimals). Optional search filters by symbol or name.",
          inputSchema: {
            chain_id: z.number().int().positive().optional().describe(chainDesc),
            search: z.string().optional().describe("Case-insensitive filter on symbol or name"),
          },
          outputSchema: {
            tokens: z.array(
              z.object({
                symbol: z.string(),
                name: z.string(),
                address: z.string(),
                decimals: z.number(),
              }),
            ),
            chain_id: z.number(),
          },
        },
        async (input) => {
          const tokens = this.zeroEx.listTokens(input.search);
          const structuredContent = {
            tokens: tokens.map((t) => ({
              symbol: t.symbol,
              name: t.name,
              address: t.address,
              decimals: t.decimals,
            })),
            chain_id: input.chain_id ?? 1,
          };
          this.logIp("swap-tokens");
          return this.ok(structuredContent as Record<string, unknown>);
        },
      );
    }

    if (should("swap-gas")) {
      server.registerTool(
        "swap-gas",
        {
          description:
            "Indicative gas price (Gwei) and gas units from a lightweight 0x price probe (USDC→WETH sample).",
          inputSchema: {
            chain_id: z.number().int().positive().optional().describe(chainDesc),
          },
          outputSchema: {
            gas_price_gwei: z.string(),
            estimated_gas: z.number(),
            estimated_cost_eth: z.string(),
          },
        },
        async (input) => {
          try {
            const info = await this.zeroEx.getGasInfo(input.chain_id);
            const costEth = (Number(info.gasPriceGwei) * info.estimatedGas * 1e-9).toFixed(6);
            const structuredContent = {
              gas_price_gwei: info.gasPriceGwei,
              estimated_gas: info.estimatedGas,
              estimated_cost_eth: costEth,
            };
            this.logIp("swap-gas");
            return this.ok(structuredContent as Record<string, unknown>);
          } catch (e) {
            return this.fail("swap-gas", e);
          }
        },
      );
    }

    if (should("swap-full")) {
      server.registerTool(
        "swap-full",
        {
          description:
            "One-shot firm quote + swap page HTML persisted to disk + preview_url on this server; includes tx for debugging. Share preview_url with the user (wallet deeplinks use this URL).",
          inputSchema: {
            sell_token: z.string().describe(tokenDesc),
            buy_token: z.string().describe(tokenDesc),
            sell_amount: z.string().describe("Human-readable sell amount"),
            taker: z
              .string()
              .regex(/^0x[a-fA-F0-9]{40}$/)
              .describe("Taker 0x address"),
            chain_id: z.number().int().positive().optional().describe(chainDesc),
            hosted_url: z.string().url().optional().describe("Optional future hosted URL for QR hint block"),
          },
          outputSchema: {
            quote: z.object({
              sell_token: z.string(),
              buy_token: z.string(),
              sell_amount: z.string(),
              buy_amount: z.string(),
              min_buy_amount: z.string(),
              price: z.string(),
              gas_estimate: z.number(),
              gas_price_gwei: z.string(),
              route: z.array(z.object(routeLegShape)),
            }),
            swap_page: z.object({
              preview_url: z.string(),
              file_id: z.string(),
              html_size_bytes: z.number(),
              wallets_supported: z.array(z.string()),
            }),
            tx: z.object(txShape),
          },
        },
        async (input) => {
          try {
            const quote = await this.zeroEx.getQuote(
              input.sell_token,
              input.buy_token,
              input.sell_amount,
              input.taker,
              input.chain_id,
            );
            const { fileId, previewUrl } = this.swapHtmlFile.allocatePreviewTarget();
            const page = this.swapPage.generate({
              quote,
              hostedUrl: input.hosted_url ?? previewUrl,
            });
            await this.swapHtmlFile.writeHtmlForId(fileId, page.html);
            const structuredContent = {
              quote: {
                sell_token: quote.sellToken,
                buy_token: quote.buyToken,
                sell_amount: quote.sellAmount,
                buy_amount: quote.buyAmount,
                min_buy_amount: quote.minBuyAmount,
                price: quote.price,
                gas_estimate: quote.gasEstimate,
                gas_price_gwei: quote.gasPriceGwei,
                route: quote.route,
              },
              swap_page: {
                preview_url: previewUrl,
                file_id: fileId,
                html_size_bytes: page.htmlSizeBytes,
                wallets_supported: page.walletsSupported,
              },
              tx: quote.tx,
            };
            this.logIp("swap-full");
            return this.ok(structuredContent as Record<string, unknown>);
          } catch (e) {
            return this.fail("swap-full", e);
          }
        },
      );
    }

    if (should("smart-swap-create")) {
      server.registerTool(
        "smart-swap-create",
        {
          description:
            "Create a Smart Swap order via 1inch Fusion (Dutch auction): EIP-712 typed data + cyberpunk signing page hosted at preview_url (same host as swap pages). Requires ONEINCH_API_KEY. engine=0x is not supported here.",
          inputSchema: {
            sell_token: z.string().describe(tokenDesc),
            buy_token: z.string().describe(tokenDesc),
            sell_amount: z.string().describe("Human-readable amount to sell"),
            target_price: z.string().describe("Target price: buy_token per 1 sell_token (human-readable)"),
            wallet: z
              .string()
              .regex(/^0x[a-fA-F0-9]{40}$/)
              .describe("Maker wallet address"),
            expiry: z.string().optional().describe('Order lifetime, e.g. "24h", "7d", "60m", or seconds as string'),
            engine: z.enum(["1inch", "0x"]).optional().describe("Only 1inch is implemented"),
            chain_id: z.number().int().positive().optional().describe(chainDesc),
          },
          outputSchema: {
            order: z.record(z.string(), z.unknown()),
            signing_page: z.object({
              preview_url: z.string(),
              file_id: z.string(),
              html_size_bytes: z.number(),
              wallets_supported: z.array(z.string()),
            }),
            pre_checks: z.object({
              needs_approve: z.boolean(),
              approve_target: z.string(),
              approve_token: z.string(),
              needs_weth_wrap: z.boolean(),
            }),
          },
        },
        async (input) => {
          try {
            if (input.engine === "0x") {
              return {
                content: [
                  {
                    type: "text" as const,
                    text: "smart-swap-create error: 0x engine is not implemented on this server; use engine 1inch (default).",
                  },
                ],
                isError: true as const,
              };
            }
            if (input.chain_id !== undefined && input.chain_id !== 1) {
              return {
                content: [
                  {
                    type: "text" as const,
                    text: "smart-swap-create error: Only chain_id=1 (Ethereum mainnet) is supported for Smart Swap in this build.",
                  },
                ],
                isError: true as const,
              };
            }
            this.smartSwap.assertConfigured();
            const built = await this.smartSwap.buildOrder({
              maker: input.wallet,
              sellToken: input.sell_token,
              buyToken: input.buy_token,
              sellAmountHuman: input.sell_amount,
              targetPrice: input.target_price,
              expiry: input.expiry ?? "24h",
            });
            const { fileId, previewUrl } = this.swapHtmlFile.allocatePreviewTarget();
            const page = this.smartSwapPage.generate({
              typedData: built.typedData,
              orderInfo: built.orderInfo,
              engine: "1inch Fusion",
              approveTarget: built.approveTarget,
              approveToken: built.approveToken,
              needsWethWrap: built.needsWethWrap,
              wrapAmount: built.wrapAmount,
              submitUrl: built.submitUrl,
              hostedUrl: previewUrl,
              apiKey: this.wtCfg.oneInchApiKey?.trim() || undefined,
              extension: built.extension,
              quoteId: built.quoteId,
            });
            await this.swapHtmlFile.writeHtmlForId(fileId, page.html);
            const orderOut = {
              order_hash: built.orderHash,
              sell_token: built.orderInfo.sell_token,
              buy_token: built.orderInfo.buy_token,
              sell_amount: built.orderInfo.sell_amount,
              buy_amount: built.orderInfo.buy_amount,
              target_price: built.orderInfo.target_price,
              expiry: built.orderInfo.expiry,
              expiry_human: built.orderInfo.expiry_human,
              engine: "1inch",
              status: "pending_signature",
            };
            // QR code URL for the agent to send alongside the link
            const qrImageUrl = previewUrl
              ? `https://api.qrserver.com/v1/create-qr-code/?size=256x256&data=${encodeURIComponent(previewUrl)}&margin=1`
              : undefined;
            const structuredContent = {
              order: orderOut,
              signing_page: {
                preview_url: previewUrl,
                qr_image_url: qrImageUrl,
                file_id: fileId,
                html_size_bytes: page.htmlSizeBytes,
                wallets_supported: page.walletsSupported,
              },
              pre_checks: {
                needs_approve: true,
                approve_target: built.approveTarget,
                approve_token: built.approveToken,
                needs_weth_wrap: built.needsWethWrap,
              },
            };
            this.logIp("smart-swap-create");
            return this.ok(structuredContent as Record<string, unknown>);
          } catch (e) {
            return this.fail("smart-swap-create", e);
          }
        },
      );
    }

    if (should("smart-swap-list")) {
      server.registerTool(
        "smart-swap-list",
        {
          description: "List Smart Swap orders for a wallet (active, filled, cancelled). Returns order details including status, fill history, and cancellation info.",
          inputSchema: {
            wallet: z.string().regex(/^0x[a-fA-F0-9]{40}$/),
            chain_id: z.number().int().positive().optional().describe(chainDesc),
          },
          outputSchema: {
            orders: z.array(z.record(z.string(), z.unknown())),
            total: z.number(),
          },
        },
        async (input) => {
          try {
            if (input.chain_id !== undefined && input.chain_id !== 1) {
              return {
                content: [{ type: "text" as const, text: "smart-swap-list error: Only chain_id=1 is supported." }],
                isError: true as const,
              };
            }
            this.smartSwap.assertConfigured();
            const { orders, total } = await this.smartSwap.listOrders(input.wallet);
            const normalized = orders.map((raw) => this.normalizeLimitOrderRow(raw));
            this.logIp("smart-swap-list");
            return this.ok({ orders: normalized, total } as Record<string, unknown>);
          } catch (e) {
            return this.fail("smart-swap-list", e);
          }
        },
      );
    }

    if (should("smart-swap-status")) {
      server.registerTool(
        "smart-swap-status",
        {
          description: "Get Smart Swap order status by order hash. Returns status (active/filled/cancelled/expired), fill details, and transaction hashes.",
          inputSchema: {
            order_hash: z.string().describe("0x-prefixed order hash"),
            chain_id: z.number().int().positive().optional().describe(chainDesc),
          },
          outputSchema: {
            order_hash: z.string(),
            status: z.string(),
            raw: z.record(z.string(), z.unknown()).optional(),
          },
        },
        async (input) => {
          try {
            if (input.chain_id !== undefined && input.chain_id !== 1) {
              return {
                content: [{ type: "text" as const, text: "smart-swap-status error: Only chain_id=1 is supported." }],
                isError: true as const,
              };
            }
            this.smartSwap.assertConfigured();
            const data = await this.smartSwap.getOrder(input.order_hash);
            const status = String(
              (data as { orderStatus?: string }).orderStatus ?? (data as { status?: string }).status ?? "unknown",
            );
            const structuredContent = {
              order_hash: input.order_hash.startsWith("0x") ? input.order_hash : `0x${input.order_hash}`,
              status,
              raw: data as Record<string, unknown>,
            };
            this.logIp("smart-swap-status");
            return this.ok(structuredContent as Record<string, unknown>);
          } catch (e) {
            return this.fail("smart-swap-status", e);
          }
        },
      );
    }

    if (should("smart-swap-cancel")) {
      server.registerTool(
        "smart-swap-cancel",
        {
          description:
            "Check Smart Swap order cancellation status. Fusion orders auto-expire after the auction window (3-10 min). Returns current order status — filled/expired orders are already finalized.",
          inputSchema: {
            order_hash: z.string(),
            wallet: z.string().regex(/^0x[a-fA-F0-9]{40}$/),
            chain_id: z.number().int().positive().optional().describe(chainDesc),
          },
          outputSchema: {
            order_hash: z.string(),
            wallet: z.string(),
            cancel_methods: z.array(z.object({ method: z.string(), description: z.string() })),
            router_contract: z.string(),
            note: z.string(),
          },
        },
        async (input) => {
          try {
            if (input.chain_id !== undefined && input.chain_id !== 1) {
              return {
                content: [{ type: "text" as const, text: "smart-swap-cancel error: Only chain_id=1 is supported." }],
                isError: true as const,
              };
            }

            const h = input.order_hash.startsWith("0x") ? input.order_hash : `0x${input.order_hash}`;

            // Check current order status before offering cancel options
            let currentStatus = "unknown";
            let cancelable = true;
            try {
              this.smartSwap.assertConfigured();
              const { orders } = await this.smartSwap.listOrders(input.wallet);
              const match = (orders as Array<Record<string, unknown>>).find(
                (o) => String(o.orderHash ?? "").toLowerCase() === h.toLowerCase(),
              );
              if (match) {
                currentStatus = String(match.status ?? "active");
                cancelable = match.cancelable !== false && currentStatus !== "filled" && currentStatus !== "cancelled" && currentStatus !== "expired";
              }
            } catch {
              /* best-effort status check */
            }

            if (!cancelable) {
              return this.ok({
                order_hash: h,
                wallet: input.wallet,
                status: currentStatus,
                cancelable: false,
                message: `Order is already ${currentStatus} — cannot be cancelled.`,
              } as Record<string, unknown>);
            }

            const structuredContent = {
              order_hash: h,
              wallet: input.wallet,
              status: currentStatus,
              cancelable: true,
              cancel_methods: [
                {
                  method: "wait_expiry",
                  description: "Wait for the order to expire naturally (no gas cost). Safest option.",
                },
                {
                  method: "on_chain",
                  description:
                    "Cancel immediately on-chain by calling the 1inch router (costs gas). Use the router contract below with the orderHash.",
                },
              ],
              router_contract: "0x111111125421cA6dc452d289314280a0f8842a65",
              etherscan_url: `https://etherscan.io/address/0x111111125421cA6dc452d289314280a0f8842a65#writeContract`,
              note: "On-chain cancellation requires a wallet transaction. The agent can generate a cancel transaction page similar to the signing page.",
            };
            this.logIp("smart-swap-cancel");
            return this.ok(structuredContent as Record<string, unknown>);
          } catch (e) {
            return this.fail("smart-swap-cancel", e);
          }
        },
      );
    }

    this.logger.log("Web3TraderTools v1.2 registered (swap-*, smart-swap-*)");
  }

  private normalizeLimitOrderRow(raw: unknown): Record<string, unknown> {
    if (!raw || typeof raw !== "object") {
      return { raw };
    }
    const o = raw as Record<string, unknown>;
    const data = (o.data as Record<string, unknown> | undefined) ?? (o.order as Record<string, unknown> | undefined) ?? o;
    const orderHash = String(o.orderHash ?? o.order_hash ?? "");
    const st = String(o.orderStatus ?? o.status ?? "unknown");

    // Resolve token symbols from addresses
    const makerAsset = String(data.makerAsset ?? o.makerAsset ?? "");
    const takerAsset = String(data.takerAsset ?? o.takerAsset ?? "");
    const sellSymbol = this.zeroEx.resolveSymbol(makerAsset);
    const buySymbol = this.zeroEx.resolveSymbol(takerAsset);
    const sellDecimals = this.zeroEx.resolveDecimals(makerAsset);
    const buyDecimals = this.zeroEx.resolveDecimals(takerAsset);

    const makerAmount = String(data.makingAmount ?? o.makerAmount ?? "0");
    const takerAmount = String(data.takingAmount ?? o.minTakerAmount ?? "0");
    const sellHuman = sellDecimals > 0 ? (Number(makerAmount) / 10 ** sellDecimals).toString() : makerAmount;
    const buyHuman = buyDecimals > 0 ? (Number(takerAmount) / 10 ** buyDecimals).toString() : takerAmount;

    // Fills info (Fusion v2)
    const fills = o.fills as Array<Record<string, unknown>> | undefined;
    const fillCount = fills?.length ?? 0;
    const filledAmount = fills?.reduce((sum, f) => sum + Number(f.filledMakerAmount ?? 0), 0) ?? 0;
    const filledHuman = sellDecimals > 0 ? (filledAmount / 10 ** sellDecimals).toString() : String(filledAmount);

    const result: Record<string, unknown> = {
      order_hash: orderHash,
      status: st,
      sell_token: sellSymbol || makerAsset,
      buy_token: buySymbol || takerAsset,
      sell_amount: sellHuman,
      buy_amount: buyHuman,
      filled_amount: filledHuman,
      fill_count: fillCount,
      created_at: o.createdAt,
      engine: "1inch",
    };

    // Include fill tx hashes if available
    if (fills && fills.length > 0) {
      result.fill_tx_hashes = fills.map((f) => f.txHash).filter(Boolean);
    }

    // Cancel info
    if (o.cancelTx) result.cancel_tx = o.cancelTx;
    if (o.cancelable !== undefined) result.cancelable = o.cancelable;

    return result;
  }

  private logIp(tool: string) {
    this.logger.log(`${tool} client_ip=${getMcpClientIp() ?? "undefined"}`);
  }

  private ok(structuredContent: Record<string, unknown>) {
    return {
      content: [{ type: "text" as const, text: JSON.stringify(structuredContent, null, 2) }],
      structuredContent,
    };
  }

  private fail(tool: string, e: unknown) {
    const friendly = this.toFriendlyCommonMessage(e);
    if (friendly) {
      this.logger.warn(`[${tool}] friendly_error detail=${formatUnknownToolError(e)}`);
      return {
        content: [{ type: "text" as const, text: `${tool} error: ${friendly}` }],
        isError: true as const,
      };
    }
    const result = makeUnexpectedToolError({
      tool,
      error: e,
      logger: this.logger,
      userMessage: `${tool} error: Unable to process request at this time. Please try again later.`,
    });
    return result.response;
  }

  private failSwapQuote(e: unknown) {
    const friendly = this.toFriendlySwapQuoteMessage(e);
    if (friendly) {
      this.logger.warn(`[swap-quote] friendly_error detail=${formatUnknownToolError(e)}`);
      return {
        content: [{ type: "text" as const, text: `swap-quote error: ${friendly}` }],
        isError: true as const,
      };
    }
    return makeUnexpectedToolError({
      tool: "swap-quote",
      error: e,
      logger: this.logger,
      logTag: "quote_failed",
      userMessage: "Unable to fetch swap quote at this time. Please try again later.",
    }).response;
  }

  private toFriendlySwapQuoteMessage(e: unknown): string | null {
    const msg = e instanceof Error ? e.message : String(e);
    const lower = msg.toLowerCase();
    if (msg.startsWith("Unsupported token:")) {
      return "不支持的代币，请使用 swap-tokens 工具查看支持的代币列表，或传入合法 ERC-20 合约地址。";
    }
    if (msg.startsWith("Invalid amount:")) {
      return "卖出数量无效，请输入大于 0 的数字，例如 0.01。";
    }
    if (lower.includes("timeout") || lower.includes("econnaborted")) {
      return "报价服务请求超时，请稍后重试。";
    }
    if (lower.includes("429") || lower.includes("rate limit")) {
      return "报价请求过于频繁，请稍后重试。";
    }
    if (
      lower.includes("401") ||
      lower.includes("403") ||
      lower.includes("zeroex_api_key") ||
      lower.includes("api key")
    ) {
      return "报价服务暂时不可用，请稍后重试。";
    }
    return null;
  }

  private toFriendlyCommonMessage(e: unknown): string | null {
    const msg = e instanceof Error ? e.message : String(e);
    const lower = msg.toLowerCase();

    if (msg.startsWith("Unsupported token:")) {
      return "不支持的代币，请使用 swap-tokens 工具查看支持的代币列表，或传入合法 ERC-20 合约地址。";
    }
    if (msg.startsWith("Invalid amount:")) {
      return "卖出数量无效，请输入大于 0 的数字，例如 0.01。";
    }
    if (msg.includes("WEB3_TRADER_HTML_OUTPUT_DIR is not set")) {
      return "服务端未配置页面输出目录，请联系管理员检查 WEB3_TRADER_HTML_OUTPUT_DIR。";
    }
    if (lower.includes("invalid file id") || lower.includes("invalid path")) {
      return "页面文件标识无效，请重新生成后再访问。";
    }
    if (lower.includes("timeout") || lower.includes("econnaborted")) {
      return "请求超时，请稍后重试。";
    }
    if (lower.includes("429") || lower.includes("rate limit")) {
      return "请求过于频繁，请稍后重试。";
    }
    if (msg.includes("ONEINCH_API_KEY")) {
      return "限价单服务未配置 ONEINCH_API_KEY，请在环境变量或 Nacos 中配置后重试。";
    }
    if (
      lower.includes("401") ||
      lower.includes("403") ||
      lower.includes("zeroex_api_key") ||
      lower.includes("api key")
    ) {
      return "服务暂时不可用，请稍后重试。";
    }
    return null;
  }
}
