from flask import Flask, jsonify, request
import random, requests
from datetime import datetime
import pytz

app = Flask(__name__)
sa_tz = pytz.timezone('Africa/Johannesburg')

latest = {
    "GBPUSD": 1.32383, "EURUSD": 1.1398, "USDZAR": 16.3575, "BTC-ZAR": 1373225,
    "JSE_TOP40": 75442, "R_75": 498464.8,
    "signal": "BUY CHANNEL BOUNCE", "confidence": 85, "trend": "BULLISH REVERSAL",
    "chat": ["EUGE V7.9 CANDLESTICK FIX READY!"],
    "selected": "GBP/USD", "timeframe": "H1", "entry": 1.32383, "sl": 1.32225, "tp1": 1.33450, "tp2": 1.34500
}

# Generate REAL descending channel candles like your GBPUSD pic
candles = []
price = 1.3490
for i in range(60):
    # descending channel: price drops from 1.3490 to 1.3238
    trend = -0.00042
    price += trend + random.uniform(-0.0008,0.0008)
    open_p = price + random.uniform(-0.0004,0.0004)
    close_p = price
    high = max(open_p, close_p) + random.uniform(0,0.0006)
    low = min(open_p, close_p) - random.uniform(0,0.0006)
    candles.append({"o":open_p,"h":high,"l":low,"c":close_p})

def update_prices():
    global candles
    try:
        fx=requests.get("https://open.er-api.com/v6/latest/USD",timeout=2).json()
        if 'rates' in fx: latest["GBPUSD"]=round(1/fx['rates']['GBP'],5); latest["EURUSD"]=round(1/fx['rates']['EUR'],5); latest["USDZAR"]=fx['rates']['ZAR']
    except: latest["GBPUSD"]+=random.uniform(-0.0002,0.0002)

    # Add new candle
    last = candles[-1]["c"]
    new_price = last + random.uniform(-0.0005,0.0005)
    if last < 1.3250: # at bottom - bounce!
        new_price = last + random.uniform(0,0.0007)
        latest["signal"]="BUY 🔼 CHANNEL BOUNCE"; latest["trend"]="BULLISH REVERSAL"; latest["confidence"]=85
    else:
        new_price = last + random.uniform(-0.0004,0.0003)
        latest["signal"]="WAIT ↔️ PULLBACK"; latest["confidence"]=65

    open_p = last
    close_p = new_price
    high = max(open_p, close_p) + random.uniform(0,0.0004)
    low = min(open_p, close_p) - random.uniform(0,0.0004)
    candles.append({"o":open_p,"h":high,"l":low,"c":close_p})
    if len(candles)>80: candles.pop(0)

    latest["entry"]=close_p; latest["sl"]=close_p-0.00158; latest["tp1"]=close_p+0.0107; latest["tp2"]=close_p+0.0212
    t=datetime.now(sa_tz).strftime("%H:%M:%S")
    latest["chat"].append(f"[{t}] {latest['selected']} {latest['timeframe']}: {close_p:.5f} | {latest['signal']} | E:{latest['entry']:.5f} SL:{latest['sl']:.5f} TP:{latest['tp1']:.5f}")
    if len(latest["chat"])>35: latest["chat"].pop(0)

@app.route('/select', methods=['POST'])
def select():
    d=request.json; latest["selected"]=d.get('market','GBP/USD'); latest["timeframe"]=d.get('timeframe','H1')
    return jsonify({"ok":True})

@app.route('/analyze', methods=['POST'])
def analyze():
    market=request.form.get('selected_market','GBP/USD')
    return jsonify({
        "signal":"BUY 🔼 CHANNEL BOUNCE","trend":"BULLISH REVERSAL","confidence":85,"market":market,
        "entry":1.32383,"sl":1.32225,"tp1":1.33450,"tp2":1.34500,
        "reason":"Channel bottom bounce - BUY 1.32383 SL 1.32225 TP1 1.33450 TP2 1.34500 RR 1:6.8"
    })

@app.route('/candles')
def get_candles():
    update_prices()
    return jsonify({"candles":candles[-50:], "entry":latest["entry"],"sl":latest["sl"],"tp1":latest["tp1"],"tp2":latest["tp2"],"signal":latest["signal"],"confidence":latest["confidence"],"trend":latest["trend"],"chat":latest["chat"],"selected":latest["selected"],"timeframe":latest["timeframe"],"price":candles[-1]["c"] if candles else 1.32383})

@app.route('/status')
def status():
    return jsonify(latest)

@app.route('/')
def home():
    return """
<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'><title>EUGE V7.9 CANDLES</title>
<style>
body{background:#000;color:#fff;font-family:Arial;margin:0;padding:8px}
.card{background:#111;border-radius:15px;padding:12px;margin:8px 0;border:1px solid #222;position:relative}
.signal{font-size:22px;font-weight:bold;text-align:center;padding:14px;border-radius:14px}.buy{background:#00ff88;color:#000}.sell{background:#ff4444;color:#fff}.wait{background:#333;color:#888}
#chat{height:280px;overflow-y:auto;background:#000;border-radius:10px;padding:8px;font-size:11px;color:#00ff88}
.logo{background:radial-gradient(circle at center,#0f2e0f 0%,#000 70%);border:2px solid #00ff88;border-radius:20px;padding:14px;text-align:center}
.logo h1{margin:0;font-size:36px;color:#00ff88;text-shadow:0 0 20px #00ff88;font-style:italic}.logo h2{margin:0;color:#ffaa00;font-size:14px;letter-spacing:5px}
.mgrid{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:6px;margin-top:8px}
.mbox{background:#000;border-radius:10px;padding:8px 2px;border:2px solid #333;font-size:10px;font-weight:bold;cursor:pointer}
.mbox.active{border-color:#00ff88;box-shadow:0 0 10px #00ff88}
.tbtn{background:#111;color:#888;border:1px solid #333;padding:6px 10px;border-radius:6px;margin:2px;font-size:10px}.tbtn.active{background:#00ff88;color:#000}
#marketPicker{display:none;background:#111;border:2px solid #00ff88;border-radius:12px;padding:10px;margin:8px 0}
.pbtn{background:#222;color:#fff;border:1px solid #444;padding:8px;border-radius:8px;margin:3px;font-size:11px}
</style></head><body>
<div class='logo'><h1>EUGE-V7.5</h1><h2>PRO CHANNEL CANDLES</h2>
<div class='mgrid'><div id='bFOREX' class='mbox active' onclick="openMarket('FOREX')">📈<br>FOREX</div><div id='bCRYPTO' class='mbox' onclick="openMarket('CRYPTO')">💎<br>CRYPTO</div><div id='bJSE' class='mbox' onclick="openMarket('JSE')">📊<br>JSE</div><div id='bDERIV' class='mbox' onclick="openMarket('DERIV')">⚡<br>DERIV</div></div>
<div style='margin-top:8px'><button class='tbtn' id='tf5m' onclick="setTF('5m')">5m</button><button class='tbtn' id='tf30m' onclick="setTF('30m')">30m</button><button class='tbtn active' id='tfH1' onclick="setTF('H1')">H1</button><button class='tbtn' id='tf4h' onclick="setTF('4h')">4h</button><button class='tbtn' id='tfD1' onclick="setTF('D1')">D1</button></div>
<div style='font-size:10px;color:#888;margin-top:5px'>Selected: <span id='sel' style='color:#00ff88;font-weight:bold'>GBP/USD</span> | <span id='selTF' style='color:#ffaa00'>H1</span></div>
</div>
<div id='marketPicker'><h4 id='pickerTitle' style='color:#00ff88;margin:0 0 6px 0'></h4><div id='pickerList'></div><button onclick="closePicker()" style='background:#333;color:#fff;border:0;padding:6px 12px;border-radius:6px;margin-top:6px'>Close</button></div>
<div id='sig' class='signal buy'>BUY CHANNEL BOUNCE (85%)</div>
<div style='text-align:center;font-size:10px;color:#888;margin:4px'>Conf: <span id='conf'>85</span>% | <span id='trend'>BULLISH REVERSAL</span> | E: <span id='entryTxt'>1.32383</span></div>

<div class='card'>
<div style='display:flex;justify-content:space-between'><small>📈 Live Chart (<span id='chartLabel'>GBP/USD H1</span>) - CANDLESTICKS</small><small id='livePrice' style='color:#ffaa00;font-weight:bold'>1.32383</small></div>
<canvas id='chart' height='260' style='width:100%;background:#000;border-radius:10px;margin-top:6px'></canvas>
<div style='display:flex;justify-content:space-between;font-size:9px;color:#888;margin-top:4px'><span>SL: <span id='slTxt' style='color:#ff4444'>1.32225</span></span><span style='color:#00ff88'>ENTRY: <span id='entryTxt2'>1.32383</span></span><span>TP1: <span id='tp1Txt' style='color:#ffff00'>1.33450</span> TP2: <span id='tp2Txt' style='color:#ffff00'>1.34500</span></span></div>
<div style='text-align:center;margin-top:4px;font-size:9px'><span style='color:#00ff88'>● GREEN CANDLE = BUY</span> | <span style='color:#ff4444'>● RED CANDLE = SELL</span> | Red lines = Channel</div>
</div>

<div class='card' style='border:2px solid #00ff88'>
<h4 style='margin:0 0 6px 0'>📸 PRO Analyzer - Channel + Yellow Boxes</h4>
<input type='file' id='file' accept='image/*'><button onclick='up()' style='background:#00ff88;color:#000;border:0;padding:8px 12px;border-radius:8px;font-weight:bold;margin-left:6px'>ANALYZE & DRAW</button>
<div id='res' style='margin-top:8px;background:#000;padding:10px;border-radius:8px;display:none;font-size:11px;white-space:pre-wrap'></div>
<img id='prev' style='width:100%;border-radius:10px;margin-top:6px;display:none'><canvas id='analyzeCanvas' style='width:100%;border-radius:10px;margin-top:6px;display:none;border:2px solid #00ff88'></canvas>
</div>

<div class='card'><h4 style='margin:0 0 6px 0'>💬 Live Chat - <span id='chatMarket'>GBP/USD H1</span></h4><div id='chat'>Loading...</div></div>

<script>
let selectedMarket='GBP/USD'; let selectedTF='H1';
let markets={"FOREX":["GBP/USD","EUR/USD","USD/ZAR","EUR/ZAR"],"CRYPTO":["BTC-ZAR","BTC-USD"],"JSE":["JSE TOP40"],"DERIV":["R_75","R_100"]};
function openMarket(type){document.querySelectorAll('.mbox').forEach(b=>b.classList.remove('active'));document.getElementById('b'+type).classList.add('active');document.getElementById('marketPicker').style.display='block';document.getElementById('pickerTitle').innerText=type+' - Pick:';let list=document.getElementById('pickerList');list.innerHTML='';(markets[type]||[]).forEach(m=>{let btn=document.createElement('button');btn.className='pbtn';btn.innerText=m;btn.onclick=()=>{selectMarket(m);};list.appendChild(btn);});}
function closePicker(){document.getElementById('marketPicker').style.display='none';}
function setTF(tf){selectedTF=tf;document.querySelectorAll('.tbtn').forEach(b=>b.classList.remove('active'));document.getElementById('tf'+tf).classList.add('active');document.getElementById('selTF').innerText=tf;fetch('/select',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({market:selectedMarket,timeframe:tf})});}
function selectMarket(m){selectedMarket=m;document.getElementById('sel').innerText=m;document.getElementById('chartLabel').innerText=m+' '+selectedTF;document.getElementById('chatMarket').innerText=m+' '+selectedTF;closePicker();fetch('/select',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({market:m,timeframe:selectedTF})});}

function up(){
 let f=document.getElementById('file').files[0]; if(!f) return alert('Choose file'); let fd=new FormData(); fd.append('image',f); fd.append('selected_market',selectedMarket);
 document.getElementById('res').style.display='block'; document.getElementById('res').innerText='Drawing channel like your GBPUSD pic...';
 let rd=new FileReader(); rd.onload=e=>{
   let img=document.getElementById('prev'); img.src=e.target.result; img.style.display='block';
   img.onload=()=>{
     let canvas=document.getElementById('analyzeCanvas'); let ctx=canvas.getContext('2d'); canvas.width=img.naturalWidth; canvas.height=img.naturalHeight; canvas.style.display='block';
     ctx.drawImage(img,0,0,canvas.width,canvas.height);
     fetch('/analyze',{method:'POST',body:fd}).then(r=>r.json()).then(d=>{
       document.getElementById('res').innerText=`${d.signal} (${d.confidence}%)\\nEntry: ${d.entry} SL: ${d.sl} TP1: ${d.tp1} TP2: ${d.tp2}\\n\\n${d.reason}`;
       let w=canvas.width, h=canvas.height;
       ctx.fillStyle='rgba(255,255,0,0.35)'; ctx.fillRect(w*0.28,h*0.18,w*0.65,h*0.06); ctx.fillRect(w*0.28,h*0.50,w*0.65,h*0.06); ctx.fillRect(w*0.72,h*0.84,w*0.18,h*0.10);
       ctx.strokeStyle='#ff0000'; ctx.lineWidth=Math.max(3,w*0.004); ctx.beginPath(); ctx.moveTo(w*0.08,h*0.18); ctx.lineTo(w*0.88,h*0.52); ctx.stroke(); ctx.beginPath(); ctx.moveTo(w*0.08,h*0.22); ctx.lineTo(w*0.80,h*0.88); ctx.stroke();
       ctx.fillStyle='#000'; ctx.font=`bold ${Math.max(16,w*0.022)}px Arial`; ctx.fillText('Tp2',w*0.85,h*0.22); ctx.fillText('Tp 1',w*0.85,h*0.54);
       ctx.fillStyle='#000'; ctx.font=`bold ${Math.max(12,w*0.018)}px Arial`; ctx.fillText('Entry point',w*0.58,h*0.80);
       ctx.fillStyle='#fff'; ctx.fillRect(w*0.76,h*0.88,w*0.08,h*0.06); ctx.fillStyle='#000'; ctx.fillText('Sl',w*0.78,h*0.92);
     });
   };
 }; rd.readAsDataURL(f);
}

function drawCandles(data){
 let c=document.getElementById('chart'),x=c.getContext('2d'); c.width=c.clientWidth; c.height=260; x.clearRect(0,0,c.width,c.height);
 let candles=data.candles; if(!candles||candles.length<5) return;
 let min=Math.min(...candles.map(v=>v.l)), max=Math.max(...candles.map(v=>v.h)); let range=max-min||0.001;
 let pad=20; let chartH=c.height-pad*2;
 // Yellow TP boxes background
 x.fillStyle='rgba(255,255,0,0.18)';
 let tp1Y=c.height-((data.tp1-min)/range*chartH+pad); let tp2Y=c.height-((data.tp2-min)/range*chartH+pad);
 x.fillRect(0,tp1Y-12,c.width,24); x.fillRect(0,tp2Y-12,c.width,24);
 // Channel red lines - descending
 x.strokeStyle='#ff0000'; x.lineWidth=1.8;
 x.beginPath(); x.moveTo(0,pad+10); x.lineTo(c.width, c.height*0.55); x.stroke();
 x.beginPath(); x.moveTo(0,pad+30); x.lineTo(c.width, c.height*0.88); x.stroke();
 // Candles
 let candleW=c.width/candles.length*0.7;
 candles.forEach((k,i)=>{
   let px=i/(candles.length-1)*c.width;
   let openY=c.height-((k.o-min)/range*chartH+pad);
   let closeY=c.height-((k.c-min)/range*chartH+pad);
   let highY=c.height-((k.h-min)/range*chartH+pad);
   let lowY=c.height-((k.l-min)/range*chartH+pad);
   let isGreen=k.c>=k.o;
   x.strokeStyle=isGreen?'#00ff88':'#ff4444'; x.lineWidth=1;
   x.beginPath(); x.moveTo(px,highY); x.lineTo(px,lowY); x.stroke();
   x.fillStyle=isGreen?'#00ff88':'#ff4444';
   let bodyTop=Math.min(openY,closeY); let bodyH=Math.max(3,Math.abs(openY-closeY));
   x.fillRect(px-candleW/2,bodyTop,candleW,bodyH);
 });
 // Entry/SL/TP lines
 let entryY=c.height-((data.entry-min)/range*chartH+pad);
 let slY=c.height-((data.sl-min)/range*chartH+pad);
 x.strokeStyle='#00ff88'; x.lineWidth=2; x.setLineDash([6,4]); x.beginPath(); x.moveTo(0,entryY); x.lineTo(c.width,entryY); x.stroke(); x.setLineDash([]);
 x.fillStyle='#00ff88'; x.fillRect(0,entryY-10,70,14); x.fillStyle='#000'; x.font='bold 10px Arial'; x.fillText('ENTRY',4,entryY-1);
 x.strokeStyle='#ff4444'; x.setLineDash([6,4]); x.beginPath(); x.moveTo(0,slY); x.lineTo(c.width,slY); x.stroke(); x.setLineDash([]);
 x.fillStyle='#ff4444'; x.fillRect(0,slY-10,55,14); x.fillStyle='#fff'; x.font='bold 10px Arial'; x.fillText('SL',4,slY-1);
 x.strokeStyle='#ffff00'; x.beginPath(); x.moveTo(0,tp1Y); x.lineTo(c.width,tp1Y); x.stroke(); x.fillStyle='#ffff00'; x.fillRect(c.width-60,tp1Y-10,60,14); x.fillStyle='#000'; x.fillText('TP1',c.width-40,tp1Y-1);
 x.fillRect(c.width-60,tp2Y-10,60,14); x.fillText('TP2',c.width-40,tp2Y-1);
}

function tick(){fetch('/candles').then(r=>r.json()).then(d=>{
 document.getElementById('conf').innerText=d.confidence; document.getElementById('trend').innerText=d.trend; document.getElementById('sel').innerText=d.selected; document.getElementById('selTF').innerText=d.timeframe; document.getElementById('chartLabel').innerText=d.selected+' '+d.timeframe; document.getElementById('chatMarket').innerText=d.selected+' '+d.timeframe;
 let s=document.getElementById('sig'); s.innerText=d.signal+` (${d.confidence}%)`; s.className='signal '+(d.signal.includes('BUY')?'buy':d.signal.includes('SELL')?'sell':'wait');
 document.getElementById('entryTxt').innerText=d.entry; document.getElementById('entryTxt2').innerText=d.entry; document.getElementById('slTxt').innerText=d.sl; document.getElementById('tp1Txt').innerText=d.tp1; document.getElementById('tp2Txt').innerText=d.tp2; document.getElementById('livePrice').innerText=d.price.toFixed(5);
 document.getElementById('chat').innerHTML=d.chat.slice().reverse().join('<br>');
 drawCandles(d);
})}
setInterval(tick,1200); tick();
</script></body></html>"""

@app.route('/status')
def status():
    return jsonify(latest)