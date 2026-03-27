# Antalpha Swap MCP Server — 需求规格

> **目标**：为 AI Agent 提供 DEX swap 交易的完整闭环服务，包含报价、交易页面托管、交易状态追踪。  
> **协议**：MCP (Model Context Protocol) — 标准 JSON-RPC over stdio/SSE  
> **版本**：v1.0 Draft  
> **日期**：2026-03-26

---

## 1. 背景与动机

### 当前方案（Skill 端临时方案）

```
Agent → 0x API 获取报价 → 本地生成 swap HTML → cloudflared 临时隧道 → QR 码 → 用户扫码
```

**问题**：
- 依赖 cloudflared 临时隧道，域名随机，不稳定
- 每次需要启动本地 HTTP 服务器
- 无法追踪交易状态
- 无品牌化体验

### 目标方案（Antalpha MCP Server）

```
Agent → MCP Server 获取报价 + 托管页面 → 返回短链 → QR 码 → 用户扫码 → MetaMask 签名
```

**优势**：
- 稳定域名（`swap.antalpha.com`）
- 一次 API 调用完成报价 + 页面生成
- 交易状态追踪
- 品牌化 UI

---

## 2. MCP Tools 定义

### 2.1 `swap_quote` — 获取报价

获取 DEX swap 实时报价。

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "sell_token": {
      "type": "string",
      "description": "卖出代币符号或合约地址",
      "examples": ["ETH", "USDT", "0xdac17f958d2ee523a2206206994597c13d831ec7"]
    },
    "buy_token": {
      "type": "string",
      "description": "买入代币符号或合约地址"
    },
    "sell_amount": {
      "type": "string",
      "description": "卖出数量（人类可读格式）",
      "examples": ["0.001", "1000"]
    },
    "chain_id": {
      "type": "integer",
      "description": "链 ID，默认 1 (Ethereum)",
      "default": 1
    },
    "taker": {
      "type": "string",
      "description": "交易者钱包地址（可选，提供后返回更精确的 gas 估算）"
    },
    "slippage_bps": {
      "type": "integer",
      "description": "滑点保护（基点），默认 50 = 0.5%",
      "default": 50
    }
  },
  "required": ["sell_token", "buy_token", "sell_amount"]
}
```

**Output:**
```json
{
  "sell_token": "ETH",
  "buy_token": "USDT",
  "sell_amount": "0.001",
  "buy_amount": "2.0835",
  "min_buy_amount": "2.0627",
  "price": "2083.54",
  "price_impact": "0.01",
  "gas_estimate": 301435,
  "gas_price_gwei": "0.32",
  "route": [
    {"source": "PancakeSwap_V2", "proportion": "100%"}
  ],
  "chain_id": 1,
  "expires_at": "2026-03-26T14:20:00Z",
  "quote_id": "q_abc123"
}
```

---

### 2.2 `swap_create_page` — 创建交易页面

基于报价创建托管的 swap 交易页面，返回短链。

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "sell_token": {
      "type": "string",
      "description": "卖出代币符号或地址"
    },
    "buy_token": {
      "type": "string",
      "description": "买入代币符号或地址"
    },
    "sell_amount": {
      "type": "string",
      "description": "卖出数量"
    },
    "taker": {
      "type": "string",
      "description": "交易者钱包地址（必填）"
    },
    "chain_id": {
      "type": "integer",
      "default": 1
    },
    "slippage_bps": {
      "type": "integer",
      "default": 50
    },
    "ttl_seconds": {
      "type": "integer",
      "description": "页面有效期（秒），默认 300（5分钟）",
      "default": 300
    }
  },
  "required": ["sell_token", "buy_token", "sell_amount", "taker"]
}
```

**Output:**
```json
{
  "page_url": "https://swap.antalpha.com/s/abc123",
  "page_id": "abc123",
  "expires_at": "2026-03-26T14:25:00Z",
  "quote": {
    "sell_token": "ETH",
    "buy_token": "USDT",
    "sell_amount": "0.001",
    "buy_amount": "2.0835",
    "min_buy_amount": "2.0627",
    "price": "2083.54"
  },
  "qr_code_url": "https://swap.antalpha.com/qr/abc123.png"
}
```

**说明**：
- 服务端获取实时报价 → 生成含完整交易数据的 HTML 页面 → 托管并返回短链
- 可选返回 `qr_code_url`（服务端生成的 QR 码图片）
- 页面过期后自动清理
- 页面包含 MetaMask deeplink + `eth_sendTransaction` 逻辑

---

### 2.3 `swap_status` — 查询交易状态

查询已创建的 swap 页面/交易状态。

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "page_id": {
      "type": "string",
      "description": "swap_create_page 返回的 page_id"
    },
    "tx_hash": {
      "type": "string",
      "description": "交易哈希（如果已知）"
    }
  },
  "oneOf": [
    {"required": ["page_id"]},
    {"required": ["tx_hash"]}
  ]
}
```

**Output:**
```json
{
  "page_id": "abc123",
  "status": "signed",
  "tx_hash": "0xabc...def",
  "block_number": 19876543,
  "confirmations": 3,
  "sell_amount": "0.001 ETH",
  "buy_amount": "2.0835 USDT",
  "actual_buy_amount": "2.0812 USDT",
  "gas_used": 287000,
  "etherscan_url": "https://etherscan.io/tx/0xabc...def"
}
```

**status 枚举**：
| 状态 | 说明 |
|------|------|
| `pending` | 页面已创建，等待用户操作 |
| `opened` | 用户已打开页面 |
| `signed` | 用户已签名，交易已提交 |
| `confirmed` | 交易已被区块确认 |
| `failed` | 交易失败 |
| `expired` | 页面已过期 |

---

### 2.4 `swap_tokens` — 支持的代币列表

返回指定链上支持的代币列表。

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "chain_id": {
      "type": "integer",
      "default": 1
    },
    "search": {
      "type": "string",
      "description": "搜索关键词（符号或名称）"
    }
  }
}
```

**Output:**
```json
{
  "tokens": [
    {"symbol": "ETH", "name": "Ethereum", "address": "0xeee...eee", "decimals": 18, "logo_url": "..."},
    {"symbol": "USDT", "name": "Tether", "address": "0xdac...ec7", "decimals": 6, "logo_url": "..."}
  ]
}
```

---

## 3. 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    Antalpha MCP Server                   │
│                                                         │
│  ┌─────────┐    ┌──────────┐    ┌───────────────────┐  │
│  │  MCP     │    │  Quote   │    │  Page Generator   │  │
│  │  Handler │───►│  Engine  │───►│  + Hosting         │  │
│  │ (stdio/  │    │ (0x API) │    │ (swap.antalpha.com)│  │
│  │  SSE)    │    └──────────┘    └───────────────────┘  │
│  └─────────┘                              │             │
│       │            ┌──────────┐           │             │
│       │            │  Status  │◄──────────┘             │
│       └───────────►│  Tracker │                         │
│                    │ (Redis)  │                         │
│                    └──────────┘                         │
└─────────────────────────────────────────────────────────┘
         ▲                                     │
         │ MCP Protocol                        │ HTTPS
         │ (JSON-RPC)                          ▼
┌─────────────────┐                  ┌─────────────────┐
│   AI Agent      │                  │   User Wallet   │
│   (OpenClaw)    │                  │   (MetaMask)    │
└─────────────────┘                  └─────────────────┘
```

### 核心组件

| 组件 | 职责 | 技术栈建议 |
|------|------|------------|
| **MCP Handler** | 接收/响应 MCP 请求 | Node.js / Python + MCP SDK |
| **Quote Engine** | 调用 0x API 获取报价 | HTTP client, 缓存热门对 |
| **Page Generator** | 生成 swap HTML 页面 | 模板引擎，静态文件存储 |
| **Page Hosting** | 托管生成的页面，提供短链 | Nginx / CDN / S3 |
| **Status Tracker** | 追踪页面访问和交易状态 | Redis + Etherscan API |
| **QR Generator** | 生成 QR 码图片 | qrcode 库 |

---

## 4. Swap 页面规格

### 4.1 页面功能

- 显示交易详情（代币、数量、价格、路由、gas）
- 自动检测 dApp 浏览器 vs 普通浏览器
- 普通浏览器：显示「🦊 在 MetaMask 中打开」按钮（metamask.app.link deeplink）
- MetaMask 内置浏览器：显示「🔄 确认 Swap」按钮
- 点击后通过 `eth_sendTransaction` 调用 MetaMask 签名
- 交易提交后显示 tx hash + Etherscan 链接
- 过期后显示"报价已过期，请重新获取"

### 4.2 页面模板参数

```javascript
const PAGE_DATA = {
  tx: {
    to: "0x...",       // Router 合约地址
    value: "0x...",    // ETH value (hex)
    data: "0x...",     // calldata (hex)
    gas: "0x...",      // gas limit (hex)
    chainId: "0x1"     // chain ID (hex)
  },
  quote: {
    sellToken: "ETH",
    buyToken: "USDT",
    sellAmount: "0.001",
    buyAmount: "2.0835",
    minBuyAmount: "2.0627",
    price: "2083.54",
    route: "PancakeSwap V2 100%"
  },
  meta: {
    pageId: "abc123",
    expiresAt: 1774538000,
    statusEndpoint: "https://swap.antalpha.com/api/status/abc123"
  }
};
```

### 4.3 状态上报

页面在关键节点向服务端上报状态：
- 页面加载 → `POST /api/status/{pageId}` `{event: "opened"}`
- 交易签名 → `POST /api/status/{pageId}` `{event: "signed", txHash: "0x..."}`
- 交易确认/失败 → 服务端通过 Etherscan API 轮询

---

## 5. API 端点（非 MCP，供页面使用）

| 端点 | 方法 | 说明 |
|------|------|------|
| `GET /s/{pageId}` | GET | 渲染 swap 页面 |
| `GET /qr/{pageId}.png` | GET | 返回 QR 码图片 |
| `POST /api/status/{pageId}` | POST | 页面状态上报 |
| `GET /api/status/{pageId}` | GET | 查询页面/交易状态 |

---

## 6. 安全考虑

### 6.1 零托管

- 服务端 **不** 接触用户私钥
- 交易数据在服务端生成，但签名必须在用户钱包完成
- 页面通过 `eth_sendTransaction` 调用钱包，钱包显示完整交易内容供用户审核

### 6.2 页面安全

- 页面有 TTL，过期自动删除
- pageId 使用不可猜测的随机值（UUID v4 或 nanoid）
- 页面内容签名验证（防篡改）
- HTTPS only

### 6.3 速率限制

- 每个 API key 每分钟最多 60 次 `swap_quote`
- 每个 API key 每分钟最多 20 次 `swap_create_page`
- 页面访问无限制

---

## 7. MCP Server 配置示例

### mcporter 配置

```json
{
  "mcpServers": {
    "antalpha-swap": {
      "command": "npx",
      "args": ["-y", "@antalpha/swap-mcp-server"],
      "env": {
        "ANTALPHA_API_KEY": "your-api-key",
        "ZEROX_API_KEY": "your-0x-key"
      }
    }
  }
}
```

### SSE 模式（远程）

```json
{
  "mcpServers": {
    "antalpha-swap": {
      "url": "https://mcp.antalpha.com/swap/sse",
      "headers": {
        "Authorization": "Bearer your-api-key"
      }
    }
  }
}
```

---

## 8. Agent 集成示例

### OpenClaw Skill 调用流程

```python
# 1. Agent 收到用户请求："帮我把 0.001 ETH 换成 USDT"

# 2. 调用 MCP: swap_create_page
result = mcp_call("antalpha-swap", "swap_create_page", {
    "sell_token": "ETH",
    "buy_token": "USDT", 
    "sell_amount": "0.001",
    "taker": "0x81f9c401B0821B6E0a16BC7B1dF0F647F36211Dd"
})

# 3. 返回给用户
# result.page_url = "https://swap.antalpha.com/s/abc123"
# result.qr_code_url = "https://swap.antalpha.com/qr/abc123.png"
# Agent 生成 QR 码或直接发链接给用户

# 4. 用户扫码 → MetaMask 签名 → 交易完成

# 5. (可选) 查询交易状态
status = mcp_call("antalpha-swap", "swap_status", {
    "page_id": "abc123"
})
# status.status = "confirmed"
# status.tx_hash = "0x..."
```

---

## 9. 开发里程碑

| 阶段 | 范围 | 预期时间 |
|------|------|----------|
| **P0** | `swap_quote` + `swap_create_page` + 页面托管 | 1 周 |
| **P1** | `swap_status` + 交易追踪 + QR 码生成 | 1 周 |
| **P2** | 多链支持 (Arbitrum, Base, Optimism) | 2 周 |
| **P3** | WalletConnect 集成 + 更多钱包支持 | 2 周 |

### P0 最小可用版本

只需实现：
1. `swap_create_page` — 调用 0x API + 生成 HTML + 托管 + 返回短链
2. 页面渲染 — 含 MetaMask deeplink + eth_sendTransaction
3. QR 码 — 服务端生成

这已经能完成 Agent → 用户的完整交易闭环。

---

## 10. 与现有服务的关系

| 现有服务 | 关系 |
|----------|------|
| Antalpha RWA MCP | 并列，RWA 负责投资产品，Swap 负责 DEX 交易 |
| 0x API | 下游依赖，Swap Server 内部调用 0x 获取报价和交易数据 |
| OpenClaw web3-trader skill | 上游客户端，Skill 通过 MCP 调用 Swap Server |

Swap MCP Server 发布后，web3-trader skill 将从直接调用 0x API 迁移到调用 Antalpha Swap MCP Server，获得：
- 无需在客户端配置 0x API key
- 自动页面托管（不再需要 cloudflared）
- 交易状态追踪
- 统一品牌体验
