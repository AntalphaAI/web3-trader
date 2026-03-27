#!/usr/bin/env python3
"""
Swap Page Generator v2 - Cyberpunk-style swap page with multi-wallet support.

Features:
- Cyber/code aesthetic dark UI with animated matrix rain + glow effects
- Multi-wallet support: MetaMask, OKX Web3, Trust Wallet, TokenPocket
- Auto-detect dApp browser vs normal browser
- Embedded QR code (base64 inline) for direct scanning
- Auto-generate hosted URL QR when URL provided

Usage:
    from swap_page_gen import generate_swap_page
    html = generate_swap_page(tx_data, quote_data)
    html = generate_swap_page(tx_data, quote_data, hosted_url="https://...")
"""

import json
import base64
import io
from typing import Dict, Any, Optional

try:
    import qrcode
    from qrcode.image.pil import PilImage
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False


def _generate_qr_base64(data: str, box_size: int = 6) -> str:
    """Generate a QR code as base64 PNG data URI."""
    if not HAS_QRCODE:
        return ""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#00ffaa", back_color="#0a0e14")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def generate_swap_page(
    tx: Dict[str, Any],
    quote: Dict[str, Any],
    hosted_url: Optional[str] = None,
) -> str:
    """Generate a cyberpunk-style self-contained HTML swap page.

    Args:
        tx: Transaction data with keys: to, value, data, gas, gasPrice
        quote: Quote data with keys: from_token, to_token, from_amount,
               to_amount, min_buy_amount, price
        hosted_url: If provided, embed a QR code pointing to this URL

    Returns:
        Complete HTML string
    """
    value_hex = hex(int(tx.get("value", 0))) if tx.get("value") else "0x0"
    gas_hex = hex(int(tx.get("gas", 0))) if tx.get("gas") else "0x0"

    wallet_short = ""
    data_field = tx.get("data", "")
    if len(data_field) > 74:
        full_addr = "0x" + data_field[34:74]
        wallet_short = full_addr[:6] + "..." + full_addr[-4:]

    # Generate QR code for hosted URL (or placeholder)
    qr_data_uri = ""
    if hosted_url and HAS_QRCODE:
        qr_data_uri = _generate_qr_base64(hosted_url, box_size=6)

    from_amount = quote.get("from_amount", "")
    to_amount = quote.get("to_amount", 0)
    min_buy = quote.get("min_buy_amount", 0)
    price = quote.get("price", 0)
    from_token = quote.get("from_token", "")
    to_token = quote.get("to_token", "")

    qr_section = ""
    if qr_data_uri:
        qr_section = f'''
    <div class="qr-section">
      <div class="qr-label">[ SCAN TO OPEN ]</div>
      <img class="qr-img" src="{qr_data_uri}" alt="QR Code" />
      <div class="qr-url">{hosted_url}</div>
    </div>'''

    return f'''<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>SWAP // {from_amount} {from_token} → {to_token}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{
  --bg:#0a0e14;--card:#0d1117;--border:#1a2332;
  --cyan:#00ffaa;--cyan2:#00d4ff;--purple:#a855f7;
  --text:#c9d1d9;--dim:#484f58;--warn:#f0b429;
  --green:#00ffaa;--red:#ff4757;
  --glow:0 0 20px rgba(0,255,170,0.15);
  --font:'SF Mono','Menlo','Consolas','Liberation Mono','Courier New',monospace;
}}
body{{
  font-family:var(--font);
  background:var(--bg);color:var(--text);
  min-height:100vh;display:flex;align-items:center;justify-content:center;
  padding:16px;overflow-x:hidden;position:relative;
}}
/* Matrix rain canvas */
#matrix{{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;opacity:0.08;pointer-events:none}}
.container{{position:relative;z-index:1;width:100%;max-width:440px}}
.card{{
  background:var(--card);border:1px solid var(--border);
  border-radius:12px;padding:28px 24px;
  box-shadow:var(--glow);position:relative;overflow:hidden;
}}
.card::before{{
  content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,transparent,var(--cyan),var(--cyan2),var(--purple),transparent);
  animation:scanline 3s linear infinite;
}}
@keyframes scanline{{0%{{transform:translateX(-100%)}}100%{{transform:translateX(100%)}}}}

.header{{text-align:center;margin-bottom:20px}}
.header h1{{
  font-size:15px;font-weight:600;letter-spacing:2px;
  color:var(--cyan);text-transform:uppercase;
  text-shadow:0 0 12px rgba(0,255,170,0.4);
}}
.header .sub{{color:var(--dim);font-size:11px;margin-top:4px;letter-spacing:1px}}

.swap-visual{{
  text-align:center;padding:16px 0;margin:12px 0;
  border:1px solid var(--border);border-radius:8px;
  background:rgba(0,255,170,0.02);
}}
.swap-visual .amount{{font-size:22px;font-weight:700;color:#fff}}
.swap-visual .token{{font-size:13px;color:var(--cyan);margin-top:2px}}
.swap-visual .arrow{{font-size:18px;color:var(--purple);margin:8px 0;text-shadow:0 0 8px rgba(168,85,247,0.5)}}
.swap-visual .receive{{font-size:20px;font-weight:700;color:var(--cyan);text-shadow:0 0 10px rgba(0,255,170,0.3)}}

.data-grid{{margin:16px 0}}
.data-row{{
  display:flex;justify-content:space-between;align-items:center;
  padding:8px 0;border-bottom:1px solid rgba(26,35,50,0.6);
  font-size:12px;
}}
.data-row:last-child{{border:none}}
.data-row .k{{color:var(--dim);text-transform:uppercase;letter-spacing:0.5px;font-size:11px}}
.data-row .v{{color:var(--text);font-weight:400;font-family:var(--font)}}
.data-row .v.highlight{{color:var(--cyan)}}

/* Wallet buttons */
.wallet-section{{margin-top:20px}}
.wallet-section .section-label{{
  font-size:10px;color:var(--dim);text-transform:uppercase;
  letter-spacing:1.5px;margin-bottom:10px;text-align:center;
}}
.wallet-grid{{display:grid;grid-template-columns:1fr 1fr;gap:8px}}
.wallet-btn{{
  display:flex;align-items:center;justify-content:center;gap:6px;
  padding:12px 8px;border:1px solid var(--border);border-radius:8px;
  background:rgba(13,17,23,0.8);color:var(--text);
  font-family:var(--font);font-size:11px;font-weight:600;
  cursor:pointer;transition:all 0.2s;text-decoration:none;
  letter-spacing:0.3px;
}}
.wallet-btn:hover{{border-color:var(--cyan);box-shadow:0 0 12px rgba(0,255,170,0.15);color:var(--cyan)}}
.wallet-btn .icon{{font-size:16px}}
.wallet-btn.primary{{
  grid-column:1/-1;border-color:var(--cyan);
  background:rgba(0,255,170,0.06);color:var(--cyan);
  padding:14px;font-size:12px;
}}
.wallet-btn.primary:hover{{background:rgba(0,255,170,0.12);box-shadow:0 0 20px rgba(0,255,170,0.2)}}

/* dApp browser - single confirm button */
.confirm-btn{{
  display:block;width:100%;padding:16px;margin-top:20px;
  background:linear-gradient(135deg,rgba(0,255,170,0.15),rgba(0,212,255,0.1));
  border:1px solid var(--cyan);border-radius:8px;
  color:var(--cyan);font-family:var(--font);
  font-size:13px;font-weight:700;letter-spacing:1px;
  cursor:pointer;transition:all 0.2s;text-transform:uppercase;
}}
.confirm-btn:hover{{background:rgba(0,255,170,0.2);box-shadow:0 0 24px rgba(0,255,170,0.25)}}
.confirm-btn:disabled{{opacity:0.3;cursor:not-allowed;box-shadow:none}}

.status{{text-align:center;margin-top:10px;font-size:12px;display:none}}
.status.err{{color:var(--red)}}
.status.ok{{color:var(--green)}}

.warn-box{{
  border:1px solid rgba(240,180,41,0.3);border-radius:6px;
  padding:10px;margin-top:14px;font-size:10px;
  color:var(--warn);text-align:center;line-height:1.5;
  background:rgba(240,180,41,0.04);letter-spacing:0.3px;
}}

{qr_section and '.qr-section{text-align:center;margin-top:16px;padding-top:14px;border-top:1px solid var(--border)}' or ''}
.qr-section .qr-label{{font-size:10px;color:var(--dim);letter-spacing:1.5px;margin-bottom:8px;text-transform:uppercase}}
.qr-img{{width:160px;height:160px;border-radius:6px;border:1px solid var(--border);image-rendering:pixelated}}
.qr-url{{font-size:9px;color:var(--dim);margin-top:6px;word-break:break-all;max-width:300px;margin-left:auto;margin-right:auto}}

.footer{{text-align:center;margin-top:14px;font-size:9px;color:var(--dim);letter-spacing:0.5px}}
.footer a{{color:var(--dim);text-decoration:none}}
.footer .pulse{{display:inline-block;width:6px;height:6px;border-radius:50%;background:var(--cyan);margin-right:4px;animation:pulse 2s infinite}}
@keyframes pulse{{0%,100%{{opacity:0.3}}50%{{opacity:1}}}}
</style>
</head>
<body>
<canvas id="matrix"></canvas>
<div class="container">
<div class="card">
  <div class="header">
    <h1>⚡ SWAP EXECUTION</h1>
    <div class="sub">POWERED BY ANTALPHA AI // ZERO CUSTODY</div>
  </div>

  <div class="swap-visual">
    <div class="amount">{from_amount}</div>
    <div class="token">{from_token}</div>
    <div class="arrow">⇣</div>
    <div class="receive">~{to_amount:.4f}</div>
    <div class="token">{to_token}</div>
  </div>

  <div class="data-grid">
    <div class="data-row"><span class="k">Min Receive</span><span class="v">{min_buy:.4f} {to_token}</span></div>
    <div class="data-row"><span class="k">Price</span><span class="v highlight">1 {from_token} ≈ ${price:,.2f}</span></div>
    <div class="data-row"><span class="k">Network</span><span class="v">Ethereum Mainnet</span></div>
    <div class="data-row"><span class="k">Wallet</span><span class="v" style="font-size:10px">{wallet_short}</span></div>
  </div>

  <!-- dApp browser mode: single confirm button -->
  <div id="dappMode" style="display:none">
    <button class="confirm-btn" id="confirmBtn" onclick="doSwap()">⚡ CONFIRM SWAP</button>
  </div>

  <!-- Normal browser mode: wallet selection -->
  <div id="walletMode" style="display:none">
    <div class="wallet-section">
      <div class="section-label">Select Wallet to Continue</div>
      <div class="wallet-grid">
        <a class="wallet-btn primary" id="mmBtn" href="#">🦊 MetaMask</a>
        <a class="wallet-btn" id="okxBtn" href="#">💎 OKX Web3</a>
        <a class="wallet-btn" id="trustBtn" href="#">🛡️ Trust Wallet</a>
        <a class="wallet-btn" id="tpBtn" href="#">📱 TokenPocket</a>
      </div>
    </div>
  </div>

  <div class="status err" id="err"></div>
  <div class="status ok" id="ok"></div>

  <div class="warn-box">⚠ QUOTE EXPIRES SHORTLY — CONFIRM PROMPTLY<br>TRANSACTION WILL APPEAR IN WALLET FOR REVIEW</div>

  {qr_section}

  <div class="footer"><span class="pulse"></span>ZERO CUSTODY · PRIVATE KEYS NEVER LEAVE WALLET · <a href="https://antalpha.com" target="_blank">ANTALPHA AI</a></div>
</div>
</div>

<script>
// -- Matrix rain effect --
(function(){{
  const c=document.getElementById('matrix'),x=c.getContext('2d');
  c.width=window.innerWidth;c.height=window.innerHeight;
  const cols=Math.floor(c.width/14),drops=Array(cols).fill(1);
  const chars='01アイウエオカキクケコサシスセソタチツテトナニヌネノ₿Ξ◆▸';
  function draw(){{
    x.fillStyle='rgba(10,14,20,0.05)';x.fillRect(0,0,c.width,c.height);
    x.fillStyle='#00ffaa';x.font='12px monospace';
    for(let i=0;i<drops.length;i++){{
      const t=chars[Math.floor(Math.random()*chars.length)];
      x.fillText(t,i*14,drops[i]*14);
      if(drops[i]*14>c.height&&Math.random()>0.975)drops[i]=0;
      drops[i]++;
    }}
  }}
  setInterval(draw,50);
  window.addEventListener('resize',()=>{{c.width=innerWidth;c.height=innerHeight}});
}})();

// -- Transaction data --
const TX={{
  to:"{tx.get('to','')}",
  value:"{value_hex}",
  gas:"{gas_hex}",
  data:"{tx.get('data','')}",
  chainId:"0x1"
}};

// -- Detect environment --
const hasDapp=typeof window.ethereum!=="undefined";
const pageUrl=window.location.href;
const rawUrl=pageUrl.replace(/^https?:\\/\\//,"");

if(hasDapp){{
  // In dApp browser (MetaMask/OKX/Trust/TP internal browser)
  // Auto-execute swap after brief delay so user can see details
  document.getElementById("dappMode").style.display="block";
  const btn=document.getElementById("confirmBtn");
  btn.textContent="⏳ AUTO-EXECUTING IN 2s...";
  btn.disabled=true;
  setTimeout(()=>{{
    btn.disabled=false;
    btn.textContent="⚡ CONFIRM SWAP";
    doSwap();
  }},2000);
}}else{{
  document.getElementById("walletMode").style.display="block";
  // MetaMask deeplink
  document.getElementById("mmBtn").href="https://metamask.app.link/dapp/"+rawUrl;
  // OKX Web3 deeplink
  document.getElementById("okxBtn").href="okx://wallet/dapp/details?dappUrl="+encodeURIComponent(pageUrl);
  // Trust Wallet deeplink
  document.getElementById("trustBtn").href="https://link.trustwallet.com/open_url?coin_id=60&url="+encodeURIComponent(pageUrl);
  // TokenPocket deeplink
  document.getElementById("tpBtn").href="tpdapp://open?params="+encodeURIComponent(JSON.stringify({{url:pageUrl,chain:"ETH"}}));
}}

async function doSwap(){{
  const btn=document.getElementById("confirmBtn");
  const err=document.getElementById("err");
  const ok=document.getElementById("ok");
  err.style.display="none";ok.style.display="none";
  btn.disabled=true;btn.textContent="⏳ WAITING FOR SIGNATURE...";
  try{{
    const accts=await window.ethereum.request({{method:"eth_requestAccounts"}});
    try{{await window.ethereum.request({{method:"wallet_switchEthereumChain",params:[{{chainId:"0x1"}}]}})}}catch(e){{}}
    const hash=await window.ethereum.request({{
      method:"eth_sendTransaction",
      params:[{{from:accts[0],...TX}}]
    }});
    ok.textContent="✅ TX SUBMITTED: "+hash.slice(0,20)+"...";
    ok.style.display="block";
    btn.textContent="✅ SUBMITTED";
  }}catch(e){{
    err.textContent="❌ "+(e.message||"TRANSACTION CANCELLED");
    err.style.display="block";
    btn.disabled=false;btn.textContent="⚡ CONFIRM SWAP";
  }}
}}
</script>
</body>
</html>'''
