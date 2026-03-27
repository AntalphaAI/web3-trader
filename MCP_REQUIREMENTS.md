# Antalpha Swap 托管页 MCP 服务需求文档

> **版本**: v1.0 | **日期**: 2026-03-27 | **状态**: 需求评审

---

## 一、背景与目标

### 当前方案（临时）
AI Agent 生成 Swap 托管页 HTML → 上传到 Litterbox（第三方免费托管，72h 过期）→ 生成 QR 码发给用户。

### 问题
1. **Litterbox 不可控** — 第三方服务，随时可能下线/限速
2. **无品牌域名** — `litter.catbox.moe` 域名不可信，用户不敢打开
3. **无数据统计** — 无法追踪交易转化率、页面访问量
4. **72h 过期** — 链接失效后无法回溯

### 目标
搭建 Antalpha 自有域名的 Swap 托管页服务（如 `swap.antalpha.com`），提供：
- **可信 HTTPS 域名** — `https://swap.antalpha.com/tx/<id>`
- **MCP 协议接口** — AI Agent 通过 MCP tool 直接调用
- **永久/可控的链接有效期**
- **交易数据统计和审计**

---

## 二、MCP 接口设计

### 2.1 `swap_page_upload` — 上传 Swap 托管页

AI Agent 生成 HTML 后，通过此接口上传并获取公网 URL。

**输入参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `html_content` | string | ✅ | 完整的 HTML 页面内容 |
| `from_token` | string | ✅ | 卖出 Token 符号（如 `ETH`） |
| `to_token` | string | ✅ | 买入 Token 符号（如 `USDT`） |
| `from_amount` | string | ✅ | 卖出数量（如 `0.001`） |
| `to_amount` | string | ✅ | 预计获得数量（如 `2.06`） |
| `wallet_address` | string | ✅ | 用户钱包地址 |
| `chain_id` | number | ✅ | 链 ID（1=Ethereum） |
| `expire_hours` | number | ❌ | 链接有效期（默认 24h） |
| `tx_data` | object | ❌ | 原始交易数据（用于审计/统计） |

**输出：**

```json
{
  "url": "https://swap.antalpha.com/tx/abc123def",
  "short_id": "abc123def",
  "qr_code_url": "https://swap.antalpha.com/qr/abc123def.png",
  "expires_at": "2026-03-28T08:00:00Z"
}
```

**关键设计：**
- 服务端直接返回 QR 码图片的 URL（`qr_code_url`），Agent 不需要本地生成 QR
- `url` 是用户打开的 Swap 页面地址
- `short_id` 是唯一交易标识，可用于后续查询

---

### 2.2 `swap_page_status` — 查询托管页状态

**输入参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `short_id` | string | ✅ | 交易标识 |

**输出：**

```json
{
  "short_id": "abc123def",
  "status": "active",
  "created_at": "2026-03-27T08:00:00Z",
  "expires_at": "2026-03-28T08:00:00Z",
  "visit_count": 3,
  "wallet_connected": true,
  "tx_submitted": false,
  "tx_hash": null
}
```

**`status` 枚举值：**
- `active` — 页面可访问
- `expired` — 已过期
- `completed` — 用户已签名提交交易
- `cancelled` — 手动取消

---

### 2.3 `swap_quote` — 获取 Swap 报价（可选，替代本地 CLI）

将现有的 0x API 调用封装为 MCP 接口，统一管理 API Key。

**输入参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `from_token` | string | ✅ | 卖出 Token（符号或地址） |
| `to_token` | string | ✅ | 买入 Token（符号或地址） |
| `amount` | string | ✅ | 卖出数量 |
| `wallet_address` | string | ✅ | 用户钱包地址 |
| `chain_id` | number | ❌ | 链 ID（默认 1） |
| `slippage` | number | ❌ | 滑点百分比（默认 0.5） |

**输出：**

```json
{
  "from_token": "ETH",
  "to_token": "USDT",
  "from_amount": "0.001",
  "to_amount": "2.058",
  "min_buy_amount": "2.038",
  "price": "2058.00",
  "gas_estimate": 308000,
  "gas_price_gwei": "0.05",
  "route": [
    { "source": "Bebop", "proportion": "100%" }
  ],
  "tx": {
    "to": "0x000...734",
    "value": "1000000000000000",
    "data": "0x2213bc...",
    "gas": "308000",
    "gasPrice": "52892433"
  }
}
```

---

### 2.4 `swap_full` — 一站式 Swap（组合接口）

将 quote + 生成页面 + 上传托管 合并为一个调用，简化 Agent 工作流。

**输入参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `from_token` | string | ✅ | 卖出 Token |
| `to_token` | string | ✅ | 买入 Token |
| `amount` | string | ✅ | 卖出数量 |
| `wallet_address` | string | ✅ | 用户钱包地址 |
| `chain_id` | number | ❌ | 链 ID（默认 1） |

**输出：**

```json
{
  "quote": {
    "from_token": "ETH",
    "to_token": "USDT",
    "from_amount": "0.001",
    "to_amount": "2.058",
    "min_buy_amount": "2.038",
    "price": "2058.00"
  },
  "swap_page": {
    "url": "https://swap.antalpha.com/tx/abc123def",
    "qr_code_url": "https://swap.antalpha.com/qr/abc123def.png",
    "expires_at": "2026-03-28T08:00:00Z"
  }
}
```

**Agent 调用此接口后只需做两件事：**
1. 下载 `qr_code_url` 的图片
2. 用消息模板发送给用户

---

## 三、托管页服务端需求

### 3.1 技术架构

```
                  ┌─────────────────────────┐
  AI Agent ──MCP──►  Antalpha Swap Service  │
                  │                         │
                  │  POST /api/swap-page    │──► 存储 HTML (S3/COS/DB)
                  │  GET  /tx/<id>          │──► 返回 HTML 页面
                  │  GET  /qr/<id>.png      │──► 返回 QR 码图片
                  │  GET  /api/status/<id>  │──► 返回状态 JSON
                  │                         │
                  └─────────────────────────┘
                           │
                    swap.antalpha.com
                    (HTTPS, CDN 加速)
```

### 3.2 域名与 SSL

- **域名**: `swap.antalpha.com`（或 `dex.antalpha.com`）
- **SSL**: 必须 HTTPS（Let's Encrypt / 云厂商证书）
- **CDN**: 推荐接入 CDN 加速（静态 HTML 页面，命中率高）

### 3.3 存储

- **HTML 页面**: 存入对象存储（COS/S3）或数据库
- **QR 码**: 服务端实时生成或缓存
- **元数据**: 存入数据库（交易信息、访问统计、状态）

### 3.4 URL 结构

| URL | 说明 |
|-----|------|
| `https://swap.antalpha.com/tx/<short_id>` | Swap 托管页（用户打开） |
| `https://swap.antalpha.com/qr/<short_id>.png` | QR 码图片 |
| `https://swap.antalpha.com/api/upload` | 上传接口（MCP 调用） |
| `https://swap.antalpha.com/api/status/<short_id>` | 状态查询 |

### 3.5 `short_id` 生成规则

- 8-12 位随机字符串（a-z0-9）
- 不可预测/不可枚举
- 示例: `a7f3x9k2`

### 3.6 安全要求

| 项目 | 要求 |
|------|------|
| 认证 | 上传接口需 API Key 认证（防滥用） |
| 限流 | 每个 API Key 每分钟最多 60 次上传 |
| HTML 清洗 | **不需要** — HTML 由 Agent 可信生成，非用户输入 |
| CORS | 允许钱包内置浏览器访问（`Access-Control-Allow-Origin: *`） |
| CSP | 允许 `unsafe-inline`（script/style 都内联在 HTML 中） |
| 过期 | 默认 24h，最长 72h，过期后返回友好提示页 |

### 3.7 过期页面处理

链接过期后，返回一个友好的过期提示页面（保持赛博风格）：

```
⏰ 该交易页面已过期
请在 AI 助手中重新发起交易获取最新报价。
```

---

## 四、页面回调（可选增强）

### 4.1 交易提交回调

托管页在用户成功提交交易后，可以回调通知服务端：

```javascript
// 用户签名成功后，页面 JS 调用
fetch('https://swap.antalpha.com/api/callback', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    short_id: '<id>',
    tx_hash: '<hash>',
    wallet: '<user_address>',
    timestamp: Date.now()
  })
});
```

这样 `swap_page_status` 接口就能返回 `tx_submitted: true` 和 `tx_hash`。

### 4.2 Agent 轮询（可选）

Agent 可以通过 `swap_page_status` 定期检查用户是否完成交易，主动通知用户：

```
✅ 交易已提交！TX Hash: 0xabc...def
🔍 查看详情: https://etherscan.io/tx/0xabc...def
```

---

## 五、开发排期建议

| 阶段 | 内容 | 预估工时 |
|------|------|---------|
| **P0** | 基础上传 + 托管页访问（`/api/upload` + `/tx/<id>`） | 1-2 天 |
| **P0** | QR 码生成（`/qr/<id>.png`） | 0.5 天 |
| **P0** | HTTPS + 域名配置 | 0.5 天 |
| **P1** | MCP 协议封装（OpenClaw MCP Server） | 1 天 |
| **P1** | `swap_full` 一站式接口 | 1 天 |
| **P1** | 状态查询 + 过期处理 | 0.5 天 |
| **P2** | 交易回调 + Agent 轮询通知 | 1 天 |
| **P2** | 访问统计 + 数据面板 | 1-2 天 |
| **P2** | 多链支持（BSC, Polygon, Arbitrum） | 2 天 |

**P0 最小可用版本约 2-3 天。**

---

## 六、MCP Server 配置示例

开发完成后，Agent 侧的 MCP 配置：

```json
{
  "mcpServers": {
    "antalpha-swap": {
      "url": "https://swap.antalpha.com/mcp",
      "apiKey": "${ANTALPHA_API_KEY}",
      "tools": [
        "swap_page_upload",
        "swap_page_status",
        "swap_quote",
        "swap_full"
      ]
    }
  }
}
```

Agent 调用变为：

```
用户: "帮我卖 0.001 ETH 为 USDT"

Agent:
1. 调用 MCP tool `swap_full(from=ETH, to=USDT, amount=0.001, wallet=0x...)`
2. 得到 { url, qr_code_url, quote }
3. 下载 qr_code_url 的图片
4. 用消息模板发送给用户
```

整个流程从 **5 步** 简化为 **1 次 MCP 调用 + 1 次消息发送**。

---

## 七、与现有 Skill 的关系

| 阶段 | Skill 职责 | MCP 服务职责 |
|------|-----------|-------------|
| **当前（v1.0）** | 本地生成 HTML + 上传 litterbox + 生成 QR | 无 |
| **Phase 1** | 本地生成 HTML + 调用 MCP 上传 | 托管 HTML + 生成 QR + 提供 URL |
| **Phase 2** | 调用 MCP `swap_full` 一站式 | 报价 + 生成页面 + 托管 + QR + 统计 |
| **Phase 3** | 仅负责消息模板和用户交互 | 完整交易引擎（多链、多 DEX） |

---

*文档由 McBit 生成 | 2026-03-27*
