import { Injectable } from "@nestjs/common";

import type { QuoteResult } from "./zeroex.service";

export interface SwapPageInput {
  quote: QuoteResult;
  hostedUrl?: string;
}

export interface SwapPageOutput {
  html: string;
  htmlSizeBytes: number;
  walletsSupported: string[];
}

@Injectable()
export class SwapPageService {
  generate(input: SwapPageInput): SwapPageOutput {
    const { quote, hostedUrl } = input;
    const { tx } = quote;

    const valueHex = tx.value && tx.value !== "0" ? `0x${BigInt(tx.value).toString(16)}` : "0x0";
    const gasHex = tx.gas ? `0x${BigInt(tx.gas).toString(16)}` : "0x0";

    let contractShort = "";
    if (tx.data && tx.data.length > 74) {
      const full = `0x${tx.data.slice(34, 74)}`;
      contractShort = `${full.slice(0, 6)}...${full.slice(-4)}`;
    }

    const fromAmount = quote.sellAmount;
    const toAmount = Number(quote.buyAmount).toFixed(4);
    const minBuy = Number(quote.minBuyAmount).toFixed(4);
    const price = Number(quote.price).toFixed(2);
    const fromToken = quote.sellToken;
    const toToken = quote.buyToken;

    const qrSection = hostedUrl
      ? `
    <div class="qr-section">
      <div class="qr-label">[ SCAN TO OPEN ]</div>
      <div class="qr-url">${this.escapeHtml(hostedUrl)}</div>
    </div>`
      : "";

    const qrCss = hostedUrl
      ? `.qr-section{text-align:center;margin-top:16px;padding-top:14px;border-top:1px solid var(--border)}
.qr-section .qr-label{font-size:10px;color:var(--dim);letter-spacing:1.5px;margin-bottom:8px;text-transform:uppercase}
.qr-url{font-size:9px;color:var(--dim);margin-top:6px;word-break:break-all;max-width:300px;margin-left:auto;margin-right:auto}`
      : "";

    const html = `<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>SWAP // ${this.escapeHtml(fromAmount)} ${this.escapeHtml(fromToken)} → ${this.escapeHtml(toToken)}</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:#0a0e14;--card:#0d1117;--border:#1a2332;
  --cyan:#00ffaa;--cyan2:#00d4ff;--purple:#a855f7;
  --text:#c9d1d9;--dim:#484f58;--warn:#f0b429;
  --green:#00ffaa;--red:#ff4757;
  --glow:0 0 20px rgba(0,255,170,0.15);
  --font:'SF Mono','Menlo','Consolas','Liberation Mono','Courier New',monospace;
}
body{
  font-family:var(--font);background:var(--bg);color:var(--text);
  min-height:100vh;display:flex;align-items:center;justify-content:center;
  padding:16px;overflow-x:hidden;position:relative;
}
#matrix{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;opacity:0.08;pointer-events:none}
.container{position:relative;z-index:1;width:100%;max-width:440px}
.card{
  background:var(--card);border:1px solid var(--border);border-radius:12px;
  padding:28px 24px;box-shadow:var(--glow);position:relative;overflow:hidden;
}
.card::before{
  content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,transparent,var(--cyan),var(--cyan2),var(--purple),transparent);
  animation:scanline 3s linear infinite;
}
@keyframes scanline{0%{transform:translateX(-100%)}100%{transform:translateX(100%)}}
.header{text-align:center;margin-bottom:20px}
.header h1{font-size:15px;font-weight:600;letter-spacing:2px;color:var(--cyan);text-transform:uppercase;text-shadow:0 0 12px rgba(0,255,170,0.4)}
.header .sub{color:var(--dim);font-size:11px;margin-top:4px;letter-spacing:1px}
.swap-visual{text-align:center;padding:16px 0;margin:12px 0;border:1px solid var(--border);border-radius:8px;background:rgba(0,255,170,0.02)}
.swap-visual .amount{font-size:22px;font-weight:700;color:#fff}
.swap-visual .token{font-size:13px;color:var(--cyan);margin-top:2px}
.swap-visual .arrow{font-size:18px;color:var(--purple);margin:8px 0;text-shadow:0 0 8px rgba(168,85,247,0.5)}
.swap-visual .receive{font-size:20px;font-weight:700;color:var(--cyan);text-shadow:0 0 10px rgba(0,255,170,0.3)}
.data-grid{margin:16px 0}
.data-row{display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid rgba(26,35,50,0.6);font-size:12px}
.data-row:last-child{border:none}
.data-row .k{color:var(--dim);text-transform:uppercase;letter-spacing:0.5px;font-size:11px}
.data-row .v{color:var(--text);font-weight:400;font-family:var(--font)}
.data-row .v.highlight{color:var(--cyan)}
.wallet-section{margin-top:20px}
.wallet-section .section-label{font-size:10px;color:var(--dim);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:10px;text-align:center}
.wallet-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.wallet-btn{display:flex;align-items:center;justify-content:center;gap:6px;padding:12px 8px;border:1px solid var(--border);border-radius:8px;background:rgba(13,17,23,0.8);color:var(--text);font-family:var(--font);font-size:11px;font-weight:600;cursor:pointer;transition:all 0.2s;text-decoration:none;letter-spacing:0.3px}
.wallet-btn:hover{border-color:var(--cyan);box-shadow:0 0 12px rgba(0,255,170,0.15);color:var(--cyan)}
.wallet-btn .icon{font-size:16px}
.wallet-btn.primary{grid-column:1/-1;border-color:var(--cyan);background:rgba(0,255,170,0.06);color:var(--cyan);padding:14px;font-size:12px}
.wallet-btn.primary:hover{background:rgba(0,255,170,0.12);box-shadow:0 0 20px rgba(0,255,170,0.2)}
.confirm-btn{display:block;width:100%;padding:16px;margin-top:20px;background:linear-gradient(135deg,rgba(0,255,170,0.15),rgba(0,212,255,0.1));border:1px solid var(--cyan);border-radius:8px;color:var(--cyan);font-family:var(--font);font-size:13px;font-weight:700;letter-spacing:1px;cursor:pointer;transition:all 0.2s;text-transform:uppercase}
.confirm-btn:hover{background:rgba(0,255,170,0.2);box-shadow:0 0 24px rgba(0,255,170,0.25)}
.confirm-btn:disabled{opacity:0.3;cursor:not-allowed;box-shadow:none}
.status{text-align:center;margin-top:10px;font-size:12px;display:none}
.status.err{color:var(--red)}.status.ok{color:var(--green)}
.warn-box{border:1px solid rgba(240,180,41,0.3);border-radius:6px;padding:10px;margin-top:14px;font-size:10px;color:var(--warn);text-align:center;line-height:1.5;background:rgba(240,180,41,0.04);letter-spacing:0.3px}
${qrCss}
.footer{text-align:center;margin-top:14px;font-size:9px;color:var(--dim);letter-spacing:0.5px}
.footer a{color:var(--dim);text-decoration:none}
.footer .pulse{display:inline-block;width:6px;height:6px;border-radius:50%;background:var(--cyan);margin-right:4px;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:0.3}50%{opacity:1}}
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
    <div class="amount">${this.escapeHtml(fromAmount)}</div>
    <div class="token">${this.escapeHtml(fromToken)}</div>
    <div class="arrow">⇣</div>
    <div class="receive">~${toAmount}</div>
    <div class="token">${this.escapeHtml(toToken)}</div>
  </div>
  <div class="data-grid">
    <div class="data-row"><span class="k">Min Receive</span><span class="v">${minBuy} ${this.escapeHtml(toToken)}</span></div>
    <div class="data-row"><span class="k">Price</span><span class="v highlight">1 ${this.escapeHtml(fromToken)} ≈ $${price}</span></div>
    <div class="data-row"><span class="k">Network</span><span class="v">Ethereum Mainnet</span></div>
    <div class="data-row"><span class="k">Contract address</span><span class="v" style="font-size:10px">${contractShort}</span></div>
  </div>
  <div id="dappMode" style="display:none">
    <button class="confirm-btn" id="confirmBtn" onclick="doSwap()">⚡ CONFIRM SWAP</button>
  </div>
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
  ${qrSection}
  <div class="footer"><span class="pulse"></span>ZERO CUSTODY · PRIVATE KEYS NEVER LEAVE WALLET · <a href="https://antalpha.com" target="_blank">ANTALPHA AI</a></div>
</div>
</div>
<script>
(function(){var c=document.getElementById('matrix'),x=c.getContext('2d');c.width=window.innerWidth;c.height=window.innerHeight;var cols=Math.floor(c.width/14),drops=Array(cols).fill(1);var chars='01アイウエオカキクケコサシスセソタチツテトナニヌネノ₿Ξ◆▸';function draw(){x.fillStyle='rgba(10,14,20,0.05)';x.fillRect(0,0,c.width,c.height);x.fillStyle='#00ffaa';x.font='12px monospace';for(var i=0;i<drops.length;i++){var t=chars[Math.floor(Math.random()*chars.length)];x.fillText(t,i*14,drops[i]*14);if(drops[i]*14>c.height&&Math.random()>0.975)drops[i]=0;drops[i]++}}setInterval(draw,50);window.addEventListener('resize',function(){c.width=innerWidth;c.height=innerHeight})})();
var TX={to:${JSON.stringify(tx.to)},value:${JSON.stringify(valueHex)},gas:${JSON.stringify(gasHex)},data:${JSON.stringify(tx.data)},chainId:"0x1"};
var hasDapp=typeof window.ethereum!=="undefined";
var pageUrl=window.location.href;
var rawUrl=pageUrl.replace(/^https?:\\/\\//,"");
if(hasDapp){document.getElementById("dappMode").style.display="block";var btn=document.getElementById("confirmBtn");btn.textContent="⏳ AUTO-EXECUTING IN 2s...";btn.disabled=true;setTimeout(function(){btn.disabled=false;btn.textContent="⚡ CONFIRM SWAP";doSwap()},2000)}else{document.getElementById("walletMode").style.display="block";document.getElementById("mmBtn").href="https://metamask.app.link/dapp/"+rawUrl;document.getElementById("okxBtn").href="okx://wallet/dapp/details?dappUrl="+encodeURIComponent(pageUrl);document.getElementById("trustBtn").href="https://link.trustwallet.com/open_url?coin_id=60&url="+encodeURIComponent(pageUrl);document.getElementById("tpBtn").href="tpdapp://open?params="+encodeURIComponent(JSON.stringify({url:pageUrl,chain:"ETH"}))}
async function doSwap(){var btn=document.getElementById("confirmBtn");var err=document.getElementById("err");var ok=document.getElementById("ok");err.style.display="none";ok.style.display="none";btn.disabled=true;btn.textContent="⏳ WAITING FOR SIGNATURE...";try{var accts=await window.ethereum.request({method:"eth_requestAccounts"});try{await window.ethereum.request({method:"wallet_switchEthereumChain",params:[{chainId:"0x1"}]})}catch(e){}var hash=await window.ethereum.request({method:"eth_sendTransaction",params:[{from:accts[0],...TX}]});ok.textContent="✅ TX SUBMITTED: "+hash.slice(0,20)+"...";ok.style.display="block";btn.textContent="✅ SUBMITTED"}catch(e){err.textContent="❌ "+(e.message||"TRANSACTION CANCELLED");err.style.display="block";btn.disabled=false;btn.textContent="⚡ CONFIRM SWAP"}}
</script>
</body>
</html>`;

    return {
      html,
      htmlSizeBytes: Buffer.byteLength(html, "utf-8"),
      walletsSupported: ["MetaMask", "OKX Web3", "Trust Wallet", "TokenPocket"],
    };
  }

  private escapeHtml(s: string): string {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
}
