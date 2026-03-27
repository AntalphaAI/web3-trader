# 🔄 Web3 Trader Skill v1.0.0

> **AI Agent 原生 DEX 交易工具 | 零托管 | 四大钱包 | 赛博朋克 UI**
>
> 由 Antalpha AI 提供聚合交易支持

---

## 功能

- 💱 通过 Antalpha AI DEX 聚合器查询实时价格和最优路由
- 🌐 生成赛博朋克风格 Swap 托管页（Matrix 数字雨 + 扫描线动效）
- 📱 支持四大主流钱包：MetaMask、OKX Web3、Trust Wallet、TokenPocket
- ⚡ 钱包内置浏览器打开后自动弹出签名（2s 倒计时）
- 📷 自动生成 QR 码图片（青色码点 + 深色背景）
- 🔒 零托管 — 私钥永远不离开用户钱包

## 快速开始

```bash
# 安装依赖
pip install requests web3 qrcode pillow

# 配置 API key
cp references/config.example.yaml ~/.web3-trader/config.yaml

# 查询价格
python3 scripts/trader_cli.py price --from ETH --to USDT --amount 0.001

# 生成 Swap 页面
python3 scripts/trader_cli.py swap-page --from ETH --to USDT --amount 0.001 \
  --wallet 0xYourAddress -o swap.html --json
```

## 文件结构

```
├── SKILL.md                 # 完整 Skill 说明（Agent 读取）
├── MCP_REQUIREMENTS.md      # Antalpha MCP 服务需求文档
├── README.md                # 本文件
├── requirements.txt         # Python 依赖
├── scripts/
│   ├── trader_cli.py        # CLI 主入口
│   ├── zeroex_client.py     # Antalpha AI API 客户端
│   └── swap_page_gen.py     # 赛博朋克 Swap 页面生成器
├── references/
│   └── config.example.yaml  # 配置模板
└── tests/
    └── test_zeroex_client.py
```

## 支持的 Token

ETH, WETH, WBTC, USDT, USDC, DAI, LINK, UNI（Ethereum Mainnet）

## 安全

- 仅生成交易数据，不接触私钥
- 含 MEV 保护（anti-sandwich）
- 可配置最大滑点（默认 0.5%）
- 用户在钱包中审核后才签名

## License

MIT
