# Antalpha Swap MCP Server — 部署交接文档

> **版本**: v1.0 | **日期**: 2026-03-27 | **交接对象**: 后端开发团队

---

## 一、项目概述

### 是什么
Antalpha Swap MCP Server 是一个为 AI Agent 提供 DEX Swap 交易托管页服务的后端系统。AI Agent 通过 MCP 协议调用接口，生成 Swap 交易页面并托管在 `ai.antalpha.com` 域名下，用户扫码或点链接即可在钱包中完成交易签名。

### 核心职责
1. **托管 Swap 页面** — 接收 Agent 生成的 HTML，分配短链 URL
2. **生成 QR 码** — 服务端渲染 QR 码图片
3. **DEX 报价** — 封装 0x Protocol API，统一管理 API Key
4. **交易状态追踪** — 记录页面访问、交易提交等事件

### 技术栈
| 组件 | 技术 |
|------|------|
| 运行时 | Node.js 22+ |
| 框架 | NestJS 11 + Express 5 |
| 数据库 | MySQL 8.0+（TypeORM） |
| 缓存 | Redis 7+（ioredis） |
| AI 协议 | @modelcontextprotocol/sdk |
| 校验 | Zod + nestjs-zod |
| QR 码 | qrcode（服务端 PNG 生成） |
| 包管理 | pnpm |

---

## 二、环境要求

### 基础环境
```bash
Node.js >= 22.0.0
pnpm >= 9.0.0
MySQL >= 8.0
Redis >= 7.0
```

### 环境变量（.env）
```bash
# ===== 服务配置 =====
PORT=3000
NODE_ENV=production

# ===== 数据库 =====
DB_HOST=localhost
DB_PORT=3306
DB_USERNAME=antalpha_swap
DB_PASSWORD=<your_password>
DB_DATABASE=antalpha_swap

# ===== Redis =====
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=<your_password>

# ===== 域名 =====
BASE_URL=https://ai.antalpha.com

# ===== API Keys =====
# 0x Protocol API Key（DEX 聚合报价）
ZEROEX_API_KEY=<your_0x_api_key>

# MCP 服务认证 Key（Agent 调用时携带）
MCP_API_KEY=<generate_a_strong_random_key>

# ===== 可选 =====
# Nacos 配置中心（如果使用）
# NACOS_SERVER=http://nacos:8848
# NACOS_NAMESPACE=production
```

---

## 三、数据库初始化

### 建库
```sql
CREATE DATABASE IF NOT EXISTS antalpha_swap
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

### 建表（TypeORM 会自动同步，以下供参考）
```sql
CREATE TABLE swap_page (
  id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  short_id      VARCHAR(12) NOT NULL UNIQUE,
  html_content  LONGTEXT NOT NULL,
  from_token    VARCHAR(20) NOT NULL,
  to_token      VARCHAR(20) NOT NULL,
  from_amount   VARCHAR(50) NOT NULL,
  to_amount     VARCHAR(50) NOT NULL,
  wallet_address VARCHAR(42) NOT NULL,
  chain_id      INT NOT NULL DEFAULT 1,
  status        ENUM('active', 'expired', 'completed', 'cancelled') DEFAULT 'active',
  visit_count   INT UNSIGNED DEFAULT 0,
  tx_hash       VARCHAR(66) DEFAULT NULL,
  tx_data       JSON DEFAULT NULL,
  expires_at    DATETIME NOT NULL,
  created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  INDEX idx_short_id (short_id),
  INDEX idx_status (status),
  INDEX idx_expires_at (expires_at),
  INDEX idx_wallet (wallet_address)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 四、部署步骤

### 4.1 获取代码
```bash
# 从代码仓库拉取
git clone <repo_url> antalpha-swap-mcp
cd antalpha-swap-mcp
```

### 4.2 安装依赖
```bash
pnpm install
```

### 4.3 配置环境
```bash
cp .env.example .env
# 编辑 .env 填入实际配置
vim .env
```

### 4.4 数据库迁移
```bash
# TypeORM 自动同步（开发/首次部署）
pnpm build
node dist/main.js --migrate
# 或者手动执行上面的 SQL
```

### 4.5 构建
```bash
pnpm build
```

### 4.6 启动
```bash
# 生产模式
NODE_ENV=production node dist/main.js

# 或使用 PM2
pm2 start dist/main.js --name antalpha-swap-mcp -i 2
```

### 4.7 Docker 部署（推荐）
```bash
# 构建镜像
docker build -t antalpha-swap-mcp:latest -f docker/Dockerfile .

# 运行
docker run -d \
  --name antalpha-swap-mcp \
  -p 3000:3000 \
  --env-file .env \
  --restart unless-stopped \
  antalpha-swap-mcp:latest
```

---

## 五、Nginx 反向代理配置

```nginx
server {
    listen 443 ssl http2;
    server_name ai.antalpha.com;

    ssl_certificate     /etc/ssl/certs/ai.antalpha.com.pem;
    ssl_certificate_key /etc/ssl/private/ai.antalpha.com.key;

    # Swap 托管页（用户访问）
    location /tx/ {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 允许钱包内置浏览器
        add_header Access-Control-Allow-Origin * always;
        add_header X-Content-Type-Options nosniff always;
    }

    # QR 码图片（缓存 1h）
    location /qr/ {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_cache_valid 200 1h;
        add_header Cache-Control "public, max-age=3600";
    }

    # MCP 接口（需认证）
    location /mcp {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 120s;

        # SSE 支持
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
        proxy_buffering off;
    }

    # 交易回调
    location /api/callback {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        add_header Access-Control-Allow-Origin * always;
        add_header Access-Control-Allow-Methods "POST, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Content-Type" always;
    }
}
```

---

## 六、接口清单

### MCP Tools（Agent 调用）

| Tool | 说明 | 优先级 |
|------|------|--------|
| `swap_page_upload` | 上传 HTML → 返回 URL + QR | P0 |
| `swap_page_status` | 查询页面状态 | P1 |
| `swap_quote` | 获取 DEX 报价 | P1 |
| `swap_full` | 一站式（报价+生成+上传） | P1 |

### HTTP 路由（用户/浏览器访问）

| 路由 | 方法 | 说明 |
|------|------|------|
| `/tx/:shortId` | GET | 返回 Swap HTML 页面 |
| `/qr/:shortId.png` | GET | 返回 QR 码 PNG 图片 |
| `/api/callback` | POST | 交易提交回调 |
| `/health` | GET | 健康检查 |

---

## 七、MCP 接入指南（给 AI Agent 配置）

部署完成后，在 OpenClaw 或其他 MCP 客户端中配置：

```json
{
  "mcpServers": {
    "antalpha-swap": {
      "url": "https://ai.antalpha.com/mcp",
      "headers": {
        "Authorization": "Bearer <MCP_API_KEY>"
      }
    }
  }
}
```

---

## 八、监控与运维

### 健康检查
```bash
curl https://ai.antalpha.com/health
# 期望返回: {"status":"ok","db":"connected","redis":"connected"}
```

### 日志
```bash
# PM2
pm2 logs antalpha-swap-mcp

# Docker
docker logs -f antalpha-swap-mcp
```

### 定时清理过期记录
建议添加 cron 任务，定期清理过期超过 7 天的记录：
```bash
# 每天凌晨 3 点清理
0 3 * * * mysql -u antalpha_swap -p'xxx' antalpha_swap -e "DELETE FROM swap_page WHERE status='expired' AND expires_at < NOW() - INTERVAL 7 DAY;"
```

### Redis 限流 Key 格式
```
rate:mcp:<api_key>:<minute_timestamp>
```
TTL = 60s，自动过期。

---

## 九、测试验证

### 1. 测试上传
```bash
curl -X POST https://ai.antalpha.com/api/swap-page \
  -H "Authorization: Bearer <MCP_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "html_content": "<html><body><h1>Test</h1></body></html>",
    "from_token": "ETH",
    "to_token": "USDT",
    "from_amount": "0.001",
    "to_amount": "2.06",
    "wallet_address": "0x81f9c401B0821B6E0a16BC7B1dF0F647F36211Dd",
    "chain_id": 1
  }'
```

### 2. 测试访问
```bash
# 打开浏览器访问返回的 URL
open https://ai.antalpha.com/tx/<short_id>
```

### 3. 测试 QR 码
```bash
curl -o test_qr.png https://ai.antalpha.com/qr/<short_id>.png
open test_qr.png
```

---

## 十、常见问题

| 问题 | 解决方案 |
|------|---------|
| 页面显示为纯文本 | 检查 Nginx Content-Type 是否为 `text/html`，检查 CSP 是否允许 `unsafe-inline` |
| QR 码加载慢 | 开启 Nginx 缓存（`proxy_cache_valid 200 1h`） |
| MCP 连接超时 | 检查 Nginx SSE 配置（`proxy_buffering off`） |
| 钱包打开页面白屏 | 确认无外部 CDN 依赖（HTML 是自包含的），检查 CORS 头 |
| 限流被触发 | 检查 Redis 是否正常，调整 `RATE_LIMIT_PER_MINUTE` 配置 |

---

*文档由 McBit 生成 | 2026-03-27 | 配合 `antalpha-swap-mcp/` 源码使用*
