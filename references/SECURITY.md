# Security Guidelines

## 🔒 Security Model

This skill follows a **zero-custody** security model:

```
┌─────────────────┐
│  Web3 Trader    │  → Generates transaction data ONLY
│     Skill       │  → Never sees private keys
└─────────────────┘
         │
         ▼
┌─────────────────┐
│  Your Wallet    │  → You review the transaction
│  (MetaMask,     │  → You sign with your key
│   Hardware)     │  → You broadcast
└─────────────────┘
```

## ✅ What This Skill Does

- Queries 0x API for optimal swap routes
- Builds transaction data (to, data, value, gas)
- Generates EIP-681 payment links
- Logs transactions locally (optional)

## ❌ What This Skill Does NOT Do

- **Never handles private keys**
- **Never signs transactions**
- **Never broadcasts transactions**
- **Never stores API keys in code**

## 🛡️ Security Best Practices

### 1. Protect Your API Key

```yaml
# ~/.web3-trader/config.yaml
api_keys:
  zeroex: "YOUR_KEY_HERE"  # Keep this file private!
```

- Set file permissions: `chmod 600 ~/.web3-trader/config.yaml`
- Never commit config.yaml to git
- Consider using environment variables in production

### 2. Always Review Transactions

Before signing any transaction:

1. **Check the route** - Does it match your expectation?
2. **Verify amounts** - Are from/to amounts correct?
3. **Review slippage** - Is it within your tolerance?
4. **Check gas** - Is gas price reasonable?

### 3. Use Testnet First

Before trading real funds:

```bash
# Test with small amounts first
python3 scripts/trader_cli.py route --from USDT --to ETH --amount 10
```

### 4. Enable Audit Logging

```yaml
# ~/.web3-trader/config.yaml
logging:
  enabled: true
  path: ~/.web3-trader/tx_log.jsonl
```

Review logs periodically for unusual activity.

### 5. Set Risk Limits

```yaml
risk:
  max_slippage: 0.5        # Reject if slippage > 0.5%
  max_amount_usdt: 10000   # Reject if trade > $10k
```

## ⚠️ Known Risks

| Risk | Mitigation |
|------|------------|
| **Smart Contract Risk** | 0x audits partner contracts, but bugs possible |
| **Slippage** | Set max slippage, use limit orders for large trades |
| **MEV/Front-running** | 0x includes built-in MEV protection |
| **API Key Leakage** | Keep config.yaml secure, use env vars |
| **Phishing** | Only download from official sources |

## 🚨 If Something Goes Wrong

1. **Stop trading immediately**
2. **Revoke API key** at https://0x.org/dashboard
3. **Review logs** at `~/.web3-trader/tx_log.jsonl`
4. **Report issues** to the skill maintainer

## 📚 Additional Resources

- [0x Security](https://docs.0x.org/0x-swap-api/security)
- [EIP-681 Standard](https://eips.ethereum.org/EIPS/eip-681)
- [Wallet Security Best Practices](https://www.coinbase.com/learn/crypto-basics/how-to-keep-crypto-safe)
