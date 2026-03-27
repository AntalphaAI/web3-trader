# ⚡ 5 分钟快速上手

## 步骤 1：安装

```bash
tar -xzf web3-trader-v0.2.0.tar.gz -C ~/.openclaw/workspace/skills/
cd ~/.openclaw/workspace/skills/web3-trader
./install.sh
```

## 步骤 2：配置 API Key

```bash
nano ~/.web3-trader/config.yaml
```

填入你的 API Key：

```yaml
api_keys:
  zeroex: "YOUR_API_KEY_HERE"
```

## 步骤 3：查询价格

```bash
python3 scripts/trader_cli.py price --from ETH --to USDT --amount 0.001
```

## 步骤 4：生成 Swap 页面

```bash
# 生成 swap 页面
python3 scripts/trader_cli.py swap-page \
  --from ETH --to USDT --amount 0.001 \
  --wallet 0xYourWalletAddress \
  -o swap.html

# 托管到公网（临时方案）
python3 -m http.server 8899 &
cloudflared tunnel --url http://127.0.0.1:8899
# 输出类似：https://xxx-xxx.trycloudflare.com

# 生成 QR 码
python3 -c "
import qrcode
url = 'https://xxx-xxx.trycloudflare.com/swap.html'
qr = qrcode.make(url)
qr.save('swap_qr.png')
print(f'QR saved: {url}')
"
```

## 步骤 5：扫码交易

1. 用手机扫描 QR 码
2. 浏览器打开页面 → 点击「🦊 在 MetaMask 中打开」
3. MetaMask 内置浏览器加载页面 → 点击「🔄 确认 Swap」
4. MetaMask 弹出交易 → 审核 → 签名 → 完成 ✅

## 其他命令

```bash
# 查看最优路由
python3 scripts/trader_cli.py route --from USDT --to ETH --amount 1000

# 构建交易数据（高级）
python3 scripts/trader_cli.py build-tx --from ETH --to USDT --amount 0.001 --wallet 0xYour

# 导出 EIP-681 链接（高级）
python3 scripts/trader_cli.py export --from ETH --to USDT --amount 0.001 --wallet 0xYour

# 查看 Gas 价格
python3 scripts/trader_cli.py gas

# 支持的代币列表
python3 scripts/trader_cli.py tokens
```

## 所有命令支持 JSON 输出

```bash
python3 scripts/trader_cli.py price --from ETH --to USDT --amount 0.001 --json
```
