import { Injectable } from "@nestjs/common";

export interface SmartSwapPageInput {
  typedData: Record<string, unknown>;
  orderInfo: Record<string, unknown>;
  engine: string;
  approveTarget: string;
  approveToken: string;
  needsWethWrap: boolean;
  wrapAmount: string;
  submitUrl: string;
  hostedUrl?: string;
  apiKey?: string;
  extension?: string;
  quoteId?: string;
}

export interface SmartSwapPageOutput {
  html: string;
  htmlSizeBytes: number;
  walletsSupported: string[];
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function jsonForScript(obj: unknown): string {
  return JSON.stringify(obj).replace(/</g, "\\u003c");
}


/** Smart Swap signing page — cyberpunk UI for Fusion EIP-712 signing. */
const SMART_SWAP_PAGE_SCRIPT = String.raw`
(function(){
  const c=document.getElementById('matrix'),x=c.getContext('2d');
  c.width=window.innerWidth;c.height=window.innerHeight;
  const cols=Math.floor(c.width/14),drops=Array(cols).fill(1);
  const chars='01アイウエオカキクケコサシスセソタチツテトナニヌネノ₿Ξ◆▸';
  function draw(){
    x.fillStyle='rgba(10,14,20,0.05)';x.fillRect(0,0,c.width,c.height);
    x.fillStyle='#00ffaa';x.font='12px monospace';
    for(let i=0;i<drops.length;i++){
      const t=chars[Math.floor(Math.random()*chars.length)];
      x.fillText(t,i*14,drops[i]*14);
      if(drops[i]*14>c.height&&Math.random()>0.975)drops[i]=0;
      drops[i]++;
    }
  }
  setInterval(draw,50);
  window.addEventListener('resize',()=>{c.width=innerWidth;c.height=innerHeight});
})();

const TYPED_DATA=__TYPED_DATA__;
const APPROVE_TARGET=__APPROVE_TARGET__;
const APPROVE_TOKEN=__APPROVE_TOKEN__;
const NEEDS_WRAP=__NEEDS_WRAP__;
const WRAP_AMOUNT=__WRAP_AMOUNT__;
const WETH_ADDR="0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2";
const SUBMIT_URL=__SUBMIT_URL__;
const API_KEY=__API_KEY__;
const ORDER_HASH=__ORDER_HASH__;
const EXTENSION=__EXTENSION__;
const QUOTE_ID=__QUOTE_ID__;

const ERC20_ALLOWANCE_SIG="0xdd62ed3e";
const ERC20_APPROVE_SIG="0x095ea7b3";
const MAX_UINT256="0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";

const hasDapp=typeof window.ethereum!=="undefined";
const pageUrl=window.location.href;
const rawUrl=pageUrl.replace(/^https?:\/\//,"");

let userAccount="";

if(hasDapp){
  document.getElementById("dappMode").style.display="block";
  initDappFlow();
}else{
  document.getElementById("walletMode").style.display="block";
  document.getElementById("mmBtn").href="https://metamask.app.link/dapp/"+rawUrl;
  document.getElementById("okxBtn").href="okx://wallet/dapp/details?dappUrl="+encodeURIComponent(pageUrl);
  document.getElementById("trustBtn").href="https://link.trustwallet.com/open_url?coin_id=60&url="+encodeURIComponent(pageUrl);
  document.getElementById("tpBtn").href="tpdapp://open?params="+encodeURIComponent(JSON.stringify({url:pageUrl,chain:"ETH"}));
}

async function initDappFlow(){
  try{
    const accts=await window.ethereum.request({method:"eth_requestAccounts"});
    userAccount=accts[0];
    const expectedMaker=(TYPED_DATA.message&&TYPED_DATA.message.maker)||"";
    if(expectedMaker&&userAccount.toLowerCase()!==expectedMaker.toLowerCase()){
      showErr("⚠️ Connected wallet ("+userAccount.slice(0,8)+"...) does not match order maker ("+expectedMaker.slice(0,8)+"...). Please switch to the correct account.");
    }
    document.getElementById("stepConnectStatus").textContent="✅ "+userAccount.slice(0,6)+"..."+userAccount.slice(-4);
    try{await window.ethereum.request({method:"wallet_switchEthereumChain",params:[{chainId:"0x1"}]})}catch(e){}
    await checkAllowance();
  }catch(e){
    showErr("Failed to connect wallet: "+(e.message||e));
  }
}

async function checkAllowance(){
  try{
    const owner=userAccount.slice(2).padStart(64,"0");
    const spender=APPROVE_TARGET.slice(2).padStart(64,"0");
    const data=ERC20_ALLOWANCE_SIG+owner+spender;
    const result=await window.ethereum.request({
      method:"eth_call",
      params:[{to:APPROVE_TOKEN,data:data},"latest"]
    });
    const allowance=BigInt(result);
    if(allowance>0n){
      document.getElementById("step1status").textContent="✅";
      document.getElementById("approveBtn").textContent="✅ APPROVED";
      document.getElementById("approveBtn").disabled=true;
      unlockNextStep();
    }else{
      document.getElementById("approveBtn").disabled=false;
    }
  }catch(e){
    document.getElementById("approveBtn").disabled=false;
  }
}

async function doApprove(){
  const btn=document.getElementById("approveBtn");
  btn.disabled=true;btn.textContent="⏳ WAITING...";
  hideStatus();
  try{
    const spender=APPROVE_TARGET.slice(2).padStart(64,"0");
    const zeroData=ERC20_APPROVE_SIG+spender+"0".repeat(64);
    const maxData=ERC20_APPROVE_SIG+spender+MAX_UINT256.slice(2);
    /* USDT requires approve(0) before approve(newValue) if current allowance > 0.
       We always reset to 0 first, then set max. Safe for all ERC-20s. */
    try{
      const resetTx=await window.ethereum.request({
        method:"eth_sendTransaction",
        params:[{from:userAccount,to:APPROVE_TOKEN,data:zeroData}]
      });
      btn.textContent="⏳ RESET OK, APPROVING...";
      /* Wait for reset tx to be mined before sending max approve */
      let mined=false;
      for(let i=0;i<60;i++){
        const r=await window.ethereum.request({method:"eth_getTransactionReceipt",params:[resetTx]});
        if(r){mined=true;break;}
        await new Promise(ok=>setTimeout(ok,2000));
      }
      if(!mined){showErr("Approve reset tx not mined in 2 min");btn.disabled=false;btn.textContent=__APPROVE_BTN_LABEL__;return;}
    }catch(resetErr){
      /* If reset fails (e.g. allowance was already 0), proceed with max approve */
    }
    await window.ethereum.request({
      method:"eth_sendTransaction",
      params:[{from:userAccount,to:APPROVE_TOKEN,data:maxData}]
    });
    document.getElementById("step1status").textContent="✅";
    btn.textContent="✅ APPROVED";
    unlockNextStep();
  }catch(e){
    showErr("Approve failed: "+(e.message||e));
    btn.disabled=false;btn.textContent=__APPROVE_BTN_LABEL__;
  }
}

async function doWrap(){
  const btn=document.getElementById("wrapBtn");
  btn.disabled=true;btn.textContent="⏳ WRAPPING...";
  hideStatus();
  try{
    const depositSig="0xd0e30db0";
    await window.ethereum.request({
      method:"eth_sendTransaction",
      params:[{from:userAccount,to:WETH_ADDR,value:"0x"+BigInt(WRAP_AMOUNT).toString(16),data:depositSig}]
    });
    document.getElementById("step2status").textContent="✅";
    btn.textContent="✅ WRAPPED";
    unlockNextStep();
  }catch(e){
    showErr("Wrap failed: "+(e.message||e));
    btn.disabled=false;btn.textContent="⚡ WRAP ETH";
  }
}

function unlockNextStep(){
  if(NEEDS_WRAP){
    const s1=document.getElementById("step1status").textContent;
    const s2=document.getElementById("step2status").textContent;
    if(s1==="✅"&&s2!=="✅"){
      document.getElementById("wrapBtn").disabled=false;
      document.getElementById("step2status").textContent="⏳";
      return;
    }
    if(s1==="✅"&&s2==="✅"){
      document.getElementById("signBtn").disabled=false;
      document.getElementById("stepSignStatus").textContent="⏳";
      return;
    }
  }else{
    const s1=document.getElementById("step1status").textContent;
    if(s1==="✅"){
      document.getElementById("signBtn").disabled=false;
      document.getElementById("stepSignStatus").textContent="⏳";
    }
  }
}

async function doSign(){
  const btn=document.getElementById("signBtn");
  btn.disabled=true;btn.textContent="⏳ WAITING FOR SIGNATURE...";
  hideStatus();
  try{
    const signature=await window.ethereum.request({
      method:"eth_signTypedData_v4",
      params:[userAccount,JSON.stringify(TYPED_DATA)]
    });
    document.getElementById("stepSignStatus").textContent="✅";

    if(SUBMIT_URL){
      btn.textContent="⏳ SUBMITTING ORDER...";
      try{
        const msg=TYPED_DATA.message||{};
        const submitBody={
          orderHash:ORDER_HASH,
          signature:signature,
          quoteId:QUOTE_ID,
          extension:EXTENSION,
          order:{
            salt:msg.salt||"0",
            maker:msg.maker||"",
            receiver:msg.receiver||"0x0000000000000000000000000000000000000000",
            makerAsset:msg.makerAsset||"",
            takerAsset:msg.takerAsset||"",
            makingAmount:msg.makingAmount||"0",
            takingAmount:msg.takingAmount||"0",
            makerTraits:msg.makerTraits||"0"
          }
        };
        const fetchHeaders={"Content-Type":"application/json"};
        if(API_KEY)fetchHeaders["Authorization"]="Bearer "+API_KEY;
        const resp=await fetch(SUBMIT_URL,{
          method:"POST",
          headers:fetchHeaders,
          body:JSON.stringify(submitBody)
        });
        if(resp.ok){
          showOk("✅ ORDER SUBMITTED — Active and waiting for fill");
          btn.textContent="✅ SUBMITTED";
        }else{
          const t=await resp.text();
          showErr("Submit failed: "+t+"\\n\\nDebug: signer="+userAccount+", maker="+msg.maker+", sig="+signature.slice(0,20)+"...");
          btn.textContent="📌 SIGN ORDER (FREE)";btn.disabled=false;
        }
      }catch(fe){
        showErr("Submit failed: "+(fe.message||fe));
        btn.textContent="📌 SIGN ORDER (FREE)";btn.disabled=false;
      }
    }else{
      showOk("✅ ORDER SIGNED — Signature: "+signature.slice(0,20)+"...");
      btn.textContent="✅ SIGNED";
    }
  }catch(e){
    showErr("Signature rejected: "+(e.message||e));
    btn.disabled=false;btn.textContent="📌 SIGN ORDER (FREE)";
    document.getElementById("stepSignStatus").textContent="⏳";
  }
}

function showErr(msg){const el=document.getElementById("err");el.textContent="❌ "+msg;el.style.display="block"}
function showOk(msg){const el=document.getElementById("ok");el.textContent=msg;el.style.display="block"}
function hideStatus(){document.getElementById("err").style.display="none";document.getElementById("ok").style.display="none"}
`;

@Injectable()
export class SmartSwapPageService {
  private readonly walletsSupported = ["MetaMask", "OKX Web3", "Trust Wallet", "TokenPocket"];

  generate(input: SmartSwapPageInput): SmartSwapPageOutput {
    const oi = input.orderInfo;
    const sellToken = escapeHtml(String(oi.sell_token ?? ""));
    const buyToken = escapeHtml(String(oi.buy_token ?? ""));
    const sellAmount = escapeHtml(String(oi.sell_amount ?? ""));
    const buyAmount = escapeHtml(String(oi.buy_amount ?? ""));
    const targetPrice = escapeHtml(String(oi.target_price ?? ""));
    const expiry = escapeHtml(String(oi.expiry ?? ""));
    const expiryHuman = escapeHtml(String(oi.expiry_human ?? ""));
    const walletShort = escapeHtml(String(oi.wallet_short ?? ""));
    const engineDisplay = escapeHtml(input.engine);
    const fullOrderHash = String(oi.full_order_hash ?? oi.order_hash ?? "");

    const hostedUrlSafe = input.hostedUrl ? escapeHtml(input.hostedUrl) : "";

    // QR code is generated by the MCP tool / Agent side, not inside the signing page.
    const qrSection = "";
    const qrCss = "";

    const wrapStepHtml = input.needsWethWrap
      ? `
    <div class="step" id="step2">
      <div class="step-header"><span class="step-num">2</span><span class="step-title">WRAP ETH → WETH</span><span class="step-status" id="step2status">⏳</span></div>
      <div class="step-desc">Limit orders require WETH. This wraps your ETH (costs gas).</div>
      <button class="confirm-btn step-btn" id="wrapBtn" onclick="doWrap()" disabled>⚡ WRAP ETH</button>
    </div>`
      : "";
    const signStepNum = input.needsWethWrap ? "3" : "2";

    const needsWrapJs = input.needsWethWrap ? "true" : "false";
    const script = SMART_SWAP_PAGE_SCRIPT.replace("__TYPED_DATA__", jsonForScript(input.typedData))
      .replace("__APPROVE_TARGET__", JSON.stringify(input.approveTarget))
      .replace("__APPROVE_TOKEN__", JSON.stringify(input.approveToken))
      .replace("__NEEDS_WRAP__", needsWrapJs)
      .replace("__WRAP_AMOUNT__", JSON.stringify(input.wrapAmount))
      .replace("__SUBMIT_URL__", JSON.stringify(input.submitUrl))
      .replace("__API_KEY__", JSON.stringify(input.apiKey ?? ""))
      .replace("__ORDER_HASH__", JSON.stringify(fullOrderHash))
      .replace("__EXTENSION__", JSON.stringify(input.extension ?? ""))
      .replace("__QUOTE_ID__", JSON.stringify(input.quoteId ?? ""))
      .replace("__APPROVE_BTN_LABEL__", JSON.stringify(`⚡ APPROVE ${String(oi.sell_token ?? "")}`));

    const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>SMART SWAP // ${sellAmount} ${sellToken} → ${buyToken}</title>
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
  font-family:var(--font);
  background:var(--bg);color:var(--text);
  min-height:100vh;display:flex;align-items:center;justify-content:center;
  padding:16px;overflow-x:hidden;position:relative;
}
#matrix{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;opacity:0.08;pointer-events:none}
.container{position:relative;z-index:1;width:100%;max-width:440px}
.card{
  background:var(--card);border:1px solid var(--border);
  border-radius:12px;padding:28px 24px;
  box-shadow:var(--glow);position:relative;overflow:hidden;
}
.card::before{
  content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,transparent,var(--cyan),var(--cyan2),var(--purple),transparent);
  animation:scanline 3s linear infinite;
}
@keyframes scanline{0%{transform:translateX(-100%)}100%{transform:translateX(100%)}}
.header{text-align:center;margin-bottom:20px}
.header h1{
  font-size:15px;font-weight:600;letter-spacing:2px;
  color:var(--cyan);text-transform:uppercase;
  text-shadow:0 0 12px rgba(0,255,170,0.4);
}
.header .sub{color:var(--dim);font-size:11px;margin-top:4px;letter-spacing:1px}
.swap-visual{
  text-align:center;padding:16px 0;margin:12px 0;
  border:1px solid var(--border);border-radius:8px;
  background:rgba(0,255,170,0.02);
}
.swap-visual .amount{font-size:22px;font-weight:700;color:#fff}
.swap-visual .token{font-size:13px;color:var(--cyan);margin-top:2px}
.swap-visual .arrow{font-size:18px;color:var(--purple);margin:8px 0;text-shadow:0 0 8px rgba(168,85,247,0.5)}
.swap-visual .receive{font-size:20px;font-weight:700;color:var(--cyan);text-shadow:0 0 10px rgba(0,255,170,0.3)}
.data-grid{margin:16px 0}
.data-row{
  display:flex;justify-content:space-between;align-items:center;
  padding:8px 0;border-bottom:1px solid rgba(26,35,50,0.6);
  font-size:12px;
}
.data-row:last-child{border:none}
.data-row .k{color:var(--dim);text-transform:uppercase;letter-spacing:0.5px;font-size:11px}
.data-row .v{color:var(--text);font-weight:400;font-family:var(--font)}
.data-row .v.highlight{color:var(--cyan)}
.wallet-section{margin-top:20px}
.wallet-section .section-label{
  font-size:10px;color:var(--dim);text-transform:uppercase;
  letter-spacing:1.5px;margin-bottom:10px;text-align:center;
}
.wallet-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.wallet-btn{
  display:flex;align-items:center;justify-content:center;gap:6px;
  padding:12px 8px;border:1px solid var(--border);border-radius:8px;
  background:rgba(13,17,23,0.8);color:var(--text);
  font-family:var(--font);font-size:11px;font-weight:600;
  cursor:pointer;transition:all 0.2s;text-decoration:none;
  letter-spacing:0.3px;
}
.wallet-btn:hover{border-color:var(--cyan);box-shadow:0 0 12px rgba(0,255,170,0.15);color:var(--cyan)}
.wallet-btn.primary{
  grid-column:1/-1;border-color:var(--cyan);
  background:rgba(0,255,170,0.06);color:var(--cyan);
  padding:14px;font-size:12px;
}
.wallet-btn.primary:hover{background:rgba(0,255,170,0.12);box-shadow:0 0 20px rgba(0,255,170,0.2)}
.confirm-btn{
  display:block;width:100%;padding:14px;margin-top:8px;
  background:linear-gradient(135deg,rgba(0,255,170,0.15),rgba(0,212,255,0.1));
  border:1px solid var(--cyan);border-radius:8px;
  color:var(--cyan);font-family:var(--font);
  font-size:12px;font-weight:700;letter-spacing:1px;
  cursor:pointer;transition:all 0.2s;text-transform:uppercase;
}
.confirm-btn:hover{background:rgba(0,255,170,0.2);box-shadow:0 0 24px rgba(0,255,170,0.25)}
.confirm-btn:disabled{opacity:0.3;cursor:not-allowed;box-shadow:none}
.step{
  border:1px solid var(--border);border-radius:8px;padding:14px;margin-top:12px;
  background:rgba(13,17,23,0.5);
}
.step-header{display:flex;align-items:center;gap:8px;margin-bottom:6px}
.step-num{
  width:22px;height:22px;border-radius:50%;border:1px solid var(--cyan);
  display:flex;align-items:center;justify-content:center;
  font-size:11px;font-weight:700;color:var(--cyan);flex-shrink:0;
}
.step-title{font-size:11px;font-weight:600;letter-spacing:1px;text-transform:uppercase;color:var(--text);flex:1}
.step-status{font-size:14px}
.step-desc{font-size:10px;color:var(--dim);margin-bottom:8px;line-height:1.5}
.step-btn{margin-top:4px}
.status{text-align:center;margin-top:10px;font-size:12px;display:none}
.status.err{color:var(--red)}
.status.ok{color:var(--green)}
.warn-box{
  border:1px solid rgba(240,180,41,0.3);border-radius:6px;
  padding:10px;margin-top:14px;font-size:10px;
  color:var(--warn);text-align:center;line-height:1.5;
  background:rgba(240,180,41,0.04);letter-spacing:0.3px;
}
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
    <h1>📌 SMART SWAP</h1>
    <div class="sub">POWERED BY ANTALPHA AI // ZERO CUSTODY</div>
  </div>

  <div class="swap-visual">
    <div class="amount">${sellAmount}</div>
    <div class="token">${sellToken}</div>
    <div class="arrow">⇣</div>
    <div class="receive">${buyAmount}</div>
    <div class="token">${buyToken}</div>
  </div>

  <div class="data-grid">
    <div class="data-row"><span class="k">Target Price</span><span class="v highlight">1 ${sellToken} = ${targetPrice} ${buyToken}</span></div>
    <div class="data-row"><span class="k">Expires</span><span class="v">${expiry} (${expiryHuman})</span></div>
    <div class="data-row"><span class="k">Engine</span><span class="v">${engineDisplay}</span></div>
    <div class="data-row"><span class="k">Network</span><span class="v">Ethereum Mainnet</span></div>
    <div class="data-row"><span class="k">Wallet</span><span class="v" style="font-size:10px">${walletShort}</span></div>
  </div>

  <div id="dappMode" style="display:none">
    <div class="step" id="step1">
      <div class="step-header"><span class="step-num">1</span><span class="step-title">APPROVE ${sellToken}</span><span class="step-status" id="step1status">⏳</span></div>
      <div class="step-desc">Grant the Smart Swap contract permission to spend your ${sellToken}.</div>
      <button class="confirm-btn step-btn" id="approveBtn" onclick="doApprove()">⚡ APPROVE ${sellToken}</button>
    </div>
    ${wrapStepHtml}
    <div class="step" id="stepSign">
      <div class="step-header"><span class="step-num">${signStepNum}</span><span class="step-title">SIGN SMART SWAP</span><span class="step-status" id="stepSignStatus">🔒</span></div>
      <div class="step-desc">Sign the order with EIP-712. This does NOT cost gas.</div>
      <button class="confirm-btn step-btn" id="signBtn" onclick="doSign()" disabled>📌 SIGN ORDER (FREE)</button>
    </div>
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

  <div class="warn-box">⚠ SIGNING DOES NOT COST GAS — ORDER BECOMES ACTIVE AFTER SIGNATURE<br>CANCELLATION REQUIRES A GAS-CONSUMING ON-CHAIN TRANSACTION</div>

  ${qrSection}

  <div class="footer"><span class="pulse"></span>ZERO CUSTODY · PRIVATE KEYS NEVER LEAVE WALLET · <a href="https://antalpha.com" target="_blank">ANTALPHA AI</a></div>
</div>
</div>

<script>
${script}
</script>

</body>
</html>`;

    return {
      html,
      htmlSizeBytes: Buffer.byteLength(html, "utf8"),
      walletsSupported: this.walletsSupported,
    };
  }
}
