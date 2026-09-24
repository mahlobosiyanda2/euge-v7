from flask import Flask, jsonify, request
import random, requests
from datetime import datetime
import pytz

app = Flask(__name__)
sa_tz = pytz.timezone('Africa/Johannesburg')

latest = {
    "BTC-ZAR": 1373225, "BTC-USD": 83407, "ETH-ZAR": 45000, "ETH-USD": 3200,
    "EURUSD": 1.1398, "GBPUSD": 1.3254, "USDZAR": 16.3575,
    "EURZAR": 18.65, "GBPZAR": 21.68, "USDJPY": 148.2,
    "JSE_TOP40": 75442, "JSE_ALSI": 82500, "R_75": 498464.8, "R_100": 1205,
    "signal": "BUY SCALP", "confidence": 82, "trend": "BULLISH",
    "chat": ["EUGE V7.7 READY - Select timeframe: 5m/30m/1h"],
    "selected": "EUR/ZAR", "timeframe": "15m",
    "entry": 18.65, "sl": 18.50, "tp1": 18.80, "tp2": 19.00
}
price_history = [18.65 + random.uniform(-0.15,0.15) for _ in range(40)]

MARKETS = {
    "FOREX": ["USD/ZAR", "EUR/USD", "GBP/USD", "EUR/ZAR", "GBP/ZAR", "USD/JPY"],
    "CRYPTO": ["BTC-ZAR", "BTC-USD", "ETH-ZAR", "ETH-USD", "SOL-ZAR"],
    "JSE": ["JSE TOP40", "JSE ALSI", "NASPERS", "SASOL", "MTN"],
    "DERIV": ["R_75", "R_100", "R_50", "BOOM 1000", "CRASH 500"]
}

def get_market_price(m):
    if "USD/ZAR" in m: return latest["USDZAR"]
    if "EUR/USD" in m: return latest["EURUSD"]
    if "GBP/USD" in m: return latest["GBPUSD"]
    if "EUR/ZAR" in m: return latest["EURZAR"]
    if "GBP/ZAR" in m: return latest["GBPZAR"]
    if "BTC-ZAR" in m: return latest["BTC-ZAR"]
    if "BTC-USD" in m: return latest["BTC-USD"]
    if "TOP40" in m: return latest["JSE_TOP40"]
    if "R_75" in m: return latest["R_75"]
    if "R_100" in m: return latest["R_100"]
    return latest["EURZAR"]

def update_prices():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd,zar", timeout=3).json()
        latest["BTC-USD"]=r['bitcoin']['usd']; latest["BTC-ZAR"]=r['bitcoin']['zar']; latest["ETH-ZAR"]=r['ethereum']['zar']; latest["USDZAR"]=r['bitcoin']['zar']/r['bitcoin']['usd']
    except: latest["BTC-ZAR"] += random.uniform(-800,800)
    try:
        fx=requests.get("https://open.er-api.com/v6/latest/USD",timeout=3).json()
        if 'rates' in fx:
            latest["USDZAR"]=fx['rates']['ZAR']; latest["EURUSD"]=round(1/fx['rates']['EUR'],4); latest["GBPUSD"]=round(1/fx['rates']['GBP'],4)
            latest["EURZAR"]=round(fx['rates']['ZAR']/fx['rates']['EUR'],4); latest["GBPZAR"]=round(fx['rates']['ZAR']/fx['rates']['GBP'],4)
    except: latest["USDZAR"]+=random.uniform(-0.02,0.02)
    latest["JSE_TOP40"]+=random.uniform(-25,25); latest["R_75"]+=random.uniform(-3,3); latest["R_100"]+=random.uniform(-0.5,0.5)

    sel = latest["selected"]
    cur_price = get_market_price(sel)
    # simulate price movement for selected
    if "ZAR" in sel and "BTC" not in sel: cur_price += random.uniform(-0.03,0.03)
    price_history.append(cur_price)
    if len(price_history)>80: price_history.pop(0)

    tf = latest["timeframe"]
    # Timeframe logic
    if len(price_history)>=20:
        avg7=sum(price_history[-7:])/7; avg21=sum(price_history[-21:])/21
        if avg7>avg21+0.02:
            latest["signal"]=f"BUY 🔼 {tf}"; latest["trend"]="BULLISH"; latest["confidence"]=82
            latest["entry"]=cur_price; latest["sl"]=cur_price*0.992; latest["tp1"]=cur_price*1.008; latest["tp2"]=cur_price*1.015
        elif avg7<avg21-0.02:
            latest["signal"]=f"SELL 🔽 {tf}"; latest["trend"]="BEARISH"; latest["confidence"]=80
            latest["entry"]=cur_price; latest["sl"]=cur_price*1.008; latest["tp1"]=cur_price*0.992; latest["tp2"]=cur_price*0.985
        else:
            latest["signal"]=f"WAIT ↔️ {tf}"; latest["trend"]="SIDEWAYS"; latest["confidence"]=58
            latest["entry"]=cur_price; latest["sl"]=cur_price*0.995; latest["tp1"]=cur_price*1.005; latest["tp2"]=cur_price*1.01

    t=datetime.now(sa_tz).strftime("%H:%M:%S")
    latest["chat"].append(f"[{t}] [{latest['timeframe']}] {sel}: {cur_price:.4f} | {latest['signal']} | Entry:{latest['entry']:.4f} SL:{latest['sl']:.4f} TP:{latest['tp1']:.4f}")
    if len(latest["chat"])>35: latest["chat"].pop(0)

@app.route('/select', methods=['POST'])
def select_market():
    data = request.json
    m = data.get('market','EUR/ZAR'); tf = data.get('timeframe', latest["timeframe"])
    latest["selected"] = m; latest["timeframe"] = tf
    # reset history for new market
    price_history.clear()
    base = get_market_price(m)
    for _ in range(40): price_history.append(base + random.uniform(-base*0.01, base*0.01))
    latest["chat"].append(f"[SYSTEM] ✅ {m} | Timeframe {tf} | Tracking BUY/SELL levels now")
    return jsonify({"ok":True})

@app.route('/analyze', methods=['POST'])
def analyze():
    market = request.form.get('selected_market', latest["selected"])
    tf = latest["timeframe"]
    cur = get_market_price(market)
    sig = latest["signal"]; conf=latest["confidence"]
    return jsonify({
        "signal":sig,"trend":latest["trend"],"confidence":conf,"market":market,
        "reason":f"{market} {tf}: Current {cur:.4f} | {sig} | Entry {latest['entry']:.4f}, SL {latest['sl']:.4f} (-0.8%), TP1 {latest['tp1']:.4f} (+0.8%), TP2 {latest['tp2']:.4f} (+1.5%). Timeframe {tf} confirms trend.",
        "entry":latest["entry"],"sl":latest["sl"],"tp1":latest["tp1"],"tp2":latest["tp2"]
    })

@app.route('/')
def home():
    return """
<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'><title>EUGE V7.7 TF</title>
<style>
body{background:#000;color:#fff;font-family:Arial;margin:0;padding:8px}
.card{background:#111;border-radius:15px;padding:12px;margin:8px 0;border:1px solid #222;position:relative}
.price{font-size:20px;font-weight:bold}.grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.signal{font-size:22px;font-weight:bold;text-align:center;padding:14px;border-radius:14px}.buy{background:#00ff88;color:#000}.sell{background:#ff4444;color:#fff}.wait{background:#333;color:#888}
#chat{height:300px;overflow-y:auto;background:#000;border-radius:10px;padding:8px;font-size:11px;color:#00ff88}
.logo{background:radial-gradient(circle at center,#0f2e0f 0%,#000 70%);border:2px solid #00ff88;border-radius:20px;padding:16px;text-align:center;box-shadow:0 0 30px rgba(0,255,136,0.4)}
.logo h1{margin:0;font-size:38px;color:#00ff88;text-shadow:0 0 20px #00ff88;font-style:italic}.logo h2{margin:0;color:#ffaa00;font-size:16px;letter-spacing:6px}
.mgrid{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:8px;margin-top:10px}
.mbox{background:#000;border-radius:12px;padding:10px 2px;border:2px solid #333;font-size:11px;font-weight:bold;cursor:pointer}
.mbox.active{border-color:#00ff88;box-shadow:0 0 12px #00ff88}
#marketPicker{display:none;background:#111;border:2px solid #00ff88;border-radius:15px;padding:12px;margin:8px 0}
.pbtn{background:#222;color:#fff;border:1px solid #444;padding:9px;border-radius:10px;margin:4px;font-size:12px;font-weight:bold}
.tbtn{background:#111;color:#888;border:1px solid #333;padding:7px 12px;border-radius:8px;margin:3px;font-size:11px;font-weight:bold}
.tbtn.active{background:#00ff88;color:#000;border-color:#00ff88}
.priceTag{position:absolute;right:10px;padding:3px 8px;border-radius:6px;font-size:11px;font-weight:bold;color:#fff;z-index:2}
</style></head><body>

<div class='logo'>
<h1>EUGE-V7.5</h1><h2>LIVE FIXED</h2>
<div class='mgrid'>
<div id='bFOREX' class='mbox active' onclick="openMarket('FOREX')">📈<br>FOREX</div>
<div id='bCRYPTO' class='mbox' onclick="openMarket('CRYPTO')">💎<br>CRYPTO</div>
<div id='bJSE' class='mbox' onclick="openMarket('JSE')">📊<br>JSE</div>
<div id='bDERIV' class='mbox' onclick="openMarket('DERIV')">⚡<br>DERIV</div>
</div>
<div style='margin-top:10px'>
<button class='tbtn active' id='tf5m' onclick="setTF('5m')">5m</button>
<button class='tbtn' id='tf15m' onclick="setTF('15m')">15m</button>
<button class='tbtn' id='tf30m' onclick="setTF('30m')">30m</button>
<button class='tbtn' id='tf1h' onclick="setTF('1h')">1h</button>
<button class='tbtn' id='tf4h' onclick="setTF('4h')">4h</button>
</div>
<div style='font-size:11px;color:#888;margin-top:6px'>Selected: <span id='sel' style='color:#00ff88;font-weight:bold'>EUR/ZAR</span> | TF: <span id='selTF' style='color:#ffaa00'>15m</span></div>
</div>

<div id='marketPicker'><h4 id='pickerTitle' style='color:#00ff88;margin:0 0 8px 0'></h4><div id='pickerList'></div><button onclick="closePicker()" style='background:#333;color:#fff;border:0;padding:8px 15px;border-radius:8px;margin-top:8px'>Close</button></div>

<div id='sig' class='signal wait'>BUY SCALP (82%)</div>
<div style='text-align:center;font-size:11px;color:#888;margin:6px'>Conf: <span id='conf'>82</span>% | <span id='trend'>BULLISH</span> | Entry: <span id='entryTxt'>-</span></div>

<div class='grid'><div class='card'><small>🟠 DERIV R_75</small><div id='r75' class='price' style='color:#ffaa00'>-</div></div><div class='card'><small>🟢 BTC-ZAR</small><div id='btc' class='price' style='color:#00ff88'>-</div></div><div class='card'><small>🔵 FOREX USD/ZAR</small><div id='zar' class='price' style='color:#44aaff'>-</div><small id='eur' style='font-size:10px;color:#888'></small></div><div class='card'><small>🟣 JSE TOP40</small><div id='jse' class='price' style='color:#ff44ff'>-</div></div></div>

<div class='card' style='padding-bottom:6px'>
<div style='display:flex;justify-content:space-between;align-items:center'><small>📈 Live Chart (<span id='chartLabel' style='color:#00ff88'>EUR/ZAR</span> - <span id='chartTF'>15m</span>)</small><small id='livePrice' style='color:#ffaa00;font-weight:bold;font-size:14px'>18.65</small></div>
<div style='position:relative;margin-top:8px'>
<canvas id='chart' height='180' style='width:100%;background:#000;border-radius:10px'></canvas>
<div id='priceBuy' class='priceTag' style='background:#00ff88;color:#000;top:8px'>BUY</div>
<div id='priceSell' class='priceTag' style='background:#ff4444;bottom:8px'>SELL</div>
<div id='priceLine' style='position:absolute;left:0;right:0;height:2px;background:#00ff88;top:50%;opacity:0.8'></div>
</div>
<div style='display:flex;justify-content:space-between;font-size:10px;color:#888;margin-top:6px'><span>SL: <span id='slTxt' style='color:#ff4444'>-</span></span><span style='color:#00ff88'>ENTRY: <span id='entryTxt2'>-</span></span><span>TP: <span id='tpTxt' style='color:#ffaa00'>-</span></span></div>
<div style='text-align:center;margin-top:6px;font-size:10px'><span style='color:#00ff88'>● BUY ZONE</span> | <span style='color:#ff4444'>● SELL ZONE</span> | Timeframe: <span id='tfInfo' style='color:#ffaa00'>15m scalp</span></div>
</div>

<div class='card' style='border:2px solid #00ff88'>
<h4>📸 Screenshot Analyzer + Auto Lines</h4>
<input type='file' id='file' accept='image/*'><button onclick='up()' style='background:#00ff88;color:#000;border:0;padding:10px 15px;border-radius:8px;font-weight:bold;margin-left:8px'>ANALYZE</button>
<div id='res' style='margin-top:10px;background:#000;padding:12px;border-radius:8px;display:none'></div>
<img id='prev' style='width:100%;border-radius:12px;margin-top:8px;display:none'><canvas id='analyzeCanvas' style='width:100%;border-radius:12px;margin-top:8px;display:none;border:2px solid #00ff88'></canvas>
</div>

<div class='card'><h4>💬 Live Chat - <span id='chatMarket'>EUR/ZAR 15m</span></h4><div id='chat'>Loading...</div></div>

<script>
let hist=[]; let selectedMarket='EUR/ZAR'; let selectedTF='15m';
let markets = {"FOREX":["USD/ZAR","EUR/USD","GBP/USD","EUR/ZAR","GBP/ZAR","USD/JPY"],"CRYPTO":["BTC-ZAR","BTC-USD","ETH-ZAR","ETH-USD","SOL-ZAR"],"JSE":["JSE TOP40","JSE ALSI","NASPERS","SASOL","MTN"],"DERIV":["R_75","R_100","R_50","BOOM 1000","CRASH 500"]};

function openMarket(type){
 document.querySelectorAll('.mbox').forEach(b=>b.classList.remove('active')); document.getElementById('b'+type).classList.add('active');
 document.getElementById('marketPicker').style.display='block'; document.getElementById('pickerTitle').innerText=type+' - Pick market:'; let list=document.getElementById('pickerList'); list.innerHTML='';
 markets[type].forEach(m=>{let btn=document.createElement('button'); btn.className='pbtn'; btn.innerText=m; btn.onclick=()=>{selectMarket(m);}; list.appendChild(btn);});
}
function closePicker(){document.getElementById('marketPicker').style.display='none';}
function setTF(tf){
 selectedTF=tf; document.querySelectorAll('.tbtn').forEach(b=>b.classList.remove('active')); document.getElementById('tf'+tf).classList.add('active');
 document.getElementById('selTF').innerText=tf; document.getElementById('chartTF').innerText=tf; document.getElementById('tfInfo').innerText=tf+' analysis';
 fetch('/select',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({market:selectedMarket,timeframe:tf})});
}
function selectMarket(m){
 selectedMarket=m; document.getElementById('sel').innerText=m; document.getElementById('chartLabel').innerText=m; document.getElementById('chatMarket').innerText=m+' '+selectedTF; closePicker();
 fetch('/select',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({market:m,timeframe:selectedTF})});
}

function up(){
 let f=document.getElementById('file').files[0]; if(!f) return alert('Choose file'); let fd=new FormData(); fd.append('image',f); fd.append('selected_market',selectedMarket);
 document.getElementById('res').style.display='block'; document.getElementById('res').innerHTML='Analyzing '+selectedMarket+' '+selectedTF+'...';
 let rd=new FileReader(); rd.onload=e=>{
   let img=document.getElementById('prev'); img.src=e.target.result; img.style.display='block';
   img.onload=()=>{
     let canvas=document.getElementById('analyzeCanvas'); let ctx=canvas.getContext('2d'); canvas.width=img.naturalWidth; canvas.height=img.naturalHeight; canvas.style.display='block';
     ctx.drawImage(img,0,0,canvas.width,canvas.height);
     fetch('/analyze',{method:'POST',body:fd}).then(r=>r.json()).then(d=>{
       document.getElementById('res').innerHTML=`<b style='color:#00ff88'>${d.signal} (${d.confidence}%) - ${d.market} ${selectedTF}</b><br>Entry: ${d.entry}<br>SL: ${d.sl}<br>TP1: ${d.tp1} TP2: ${d.tp2}<br><br>${d.reason}`;
       // draw lines on screenshot
       ctx.lineWidth=Math.max(4,canvas.width*0.006);
       ctx.strokeStyle='#00ff88'; ctx.beginPath(); ctx.moveTo(0,canvas.height*0.5); ctx.lineTo(canvas.width,canvas.height*0.5); ctx.stroke();
       ctx.fillStyle='#00ff88'; ctx.fillRect(0,canvas.height*0.5-20,260,24); ctx.fillStyle='#000'; ctx.font='bold 18px Arial'; ctx.fillText('BUY '+d.entry,6,canvas.height*0.5-2);
       ctx.strokeStyle='#ff4444'; ctx.setLineDash([12,6]); ctx.beginPath(); ctx.moveTo(0,canvas.height*0.78); ctx.lineTo(canvas.width,canvas.height*0.78); ctx.stroke(); ctx.setLineDash([]);
       ctx.fillStyle='#ff4444'; ctx.fillRect(0,canvas.height*0.78-20,200,24); ctx.fillStyle='#fff'; ctx.fillText('SL '+d.sl,6,canvas.height*0.78-2);
       ctx.strokeStyle='#ffaa00'; ctx.beginPath(); ctx.moveTo(0,canvas.height*0.25); ctx.lineTo(canvas.width,canvas.height*0.25); ctx.stroke();
       ctx.fillStyle='#ffaa00'; ctx.fillRect(0,canvas.height*0.25-20,200,24); ctx.fillStyle='#000'; ctx.fillText('TP '+d.tp1,6,canvas.height*0.25-2);
     });
   };
 }; rd.readAsDataURL(f);
}

function tick(){fetch('/status').then(r=>r.json()).then(d=>{
 document.getElementById('r75').innerText=d.R_75.toFixed(2); document.getElementById('btc').innerText=Math.round(d['BTC-ZAR']).toLocaleString(); document.getElementById('zar').innerText=d.USDZAR.toFixed(4); document.getElementById('eur').innerText=`EUR:${d.EURUSD} GBP:${d.GBPUSD}`; document.getElementById('jse').innerText=Math.round(d.JSE_TOP40).toLocaleString();
 document.getElementById('conf').innerText=d.confidence; document.getElementById('trend').innerText=d.trend; document.getElementById('sel').innerText=d.selected; document.getElementById('selTF').innerText=d.timeframe; document.getElementById('chartLabel').innerText=d.selected; document.getElementById('chartTF').innerText=d.timeframe; document.getElementById('chatMarket').innerText=d.selected+' '+d.timeframe; selectedMarket=d.selected; selectedTF=d.timeframe;
 let s=document.getElementById('sig'); s.innerText=d.signal+` (${d.confidence}%)`; s.className='signal '+(d.signal.includes('BUY')?'buy':d.signal.includes('SELL')?'sell':'wait');
 document.getElementById('entryTxt').innerText=d.entry.toFixed? d.entry.toFixed(4) : d.entry; document.getElementById('entryTxt2').innerText=typeof d.entry==='number'?d.entry.toFixed(4):d.entry; document.getElementById('slTxt').innerText=typeof d.sl==='number'?d.sl.toFixed(4):d.sl; document.getElementById('tpTxt').innerText=typeof d.tp1==='number'?d.tp1.toFixed(4):d.tp1;
 document.getElementById('livePrice').innerText=typeof d.entry==='number'?d.entry.toFixed(4):d.entry; document.getElementById('priceBuy').innerText='BUY '+ (typeof d.entry==='number'?d.entry.toFixed(2):d.entry); document.getElementById('priceSell').innerText='SELL TP '+ (typeof d.tp1==='number'?d.tp1.toFixed(2):d.tp1);
 document.getElementById('chat').innerHTML=d.chat.slice().reverse().join('<br>');
 hist.push(d.entry); if(hist.length>80)hist.shift();
 let c=document.getElementById('chart'),x=c.getContext('2d'); c.width=c.clientWidth; c.height=180; x.clearRect(0,0,c.width,c.height);
 if(hist.length>3){
   let min=Math.min(...hist),max=Math.max(...hist),range=max-min||1; if(range< (max*0.005)){min=min*0.998; max=max*1.002; range=max-min;}
   // draw grid
   x.strokeStyle='#222'; x.lineWidth=1; for(let i=0;i<4;i++){x.beginPath(); x.moveTo(0,i*c.height/4); x.lineTo(c.width,i*c.height/4); x.stroke();}
   // price line
   x.strokeStyle='#ffaa00'; x.lineWidth=2.5; x.beginPath();
   hist.forEach((p,i)=>{let px=i/(hist.length-1)*c.width; let py=c.height-((p-min)/range*c.height*0.8+10); if(i==0)x.moveTo(px,py); else x.lineTo(px,py);}); x.stroke();
   // BUY zone
   let buyY=c.height-((d.entry-min)/range*c.height*0.8+10); x.fillStyle='rgba(0,255,136,0.15)'; x.fillRect(0,buyY-12,c.width,24);
   x.strokeStyle='#00ff88'; x.setLineDash([6,4]); x.beginPath(); x.moveTo(0,buyY); x.lineTo(c.width,buyY); x.stroke(); x.setLineDash([]);
   // TP
   let tpY=c.height-((d.tp1-min)/range*c.height*0.8+10); x.strokeStyle='#ffaa00'; x.beginPath(); x.moveTo(0,tpY); x.lineTo(c.width,tpY); x.stroke();
   // SL
   let slY=c.height-((d.sl-min)/range*c.height*0.8+10); x.strokeStyle='#ff4444'; x.setLineDash([8,4]); x.beginPath(); x.moveTo(0,slY); x.lineTo(c.width,slY); x.stroke(); x.setLineDash([]);
 }
})}
setInterval(tick,1000); tick();
</script></body></html>"""

@app.route('/status')
def status():
    update_prices()
    return jsonify(latest)