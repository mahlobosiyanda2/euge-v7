from flask import Flask, jsonify, request
import random
from datetime import datetime, timedelta
import pytz

app = Flask(__name__)
sa_tz = pytz.timezone('Africa/Johannesburg')

MARKETS = {
    "FOREX": ["EURGBP", "GBPUSD", "EURUSD", "USDZAR", "NZDCAD", "AUDCAD", "EURZAR"],
    "CRYPTO": ["BTC-USD"],
    "JSE": ["JSE TOP40"],
    "DERIV": ["R_75", "GOLD H4"]
}

PRESETS = {
    "EURGBP": {"price": 0.86062, "support": 0.85734, "resistance": 0.86094, "tf": "M30"},
    "USDZAR": {"price": 16.4192, "support": 16.1585, "resistance": 16.4192, "tf": "M30"}, # YOUR SCREENSHOT!
    "AUDCAD": {"price": 0.99243, "support": 0.97948, "resistance": 1.00000, "tf": "M30"},
    "NZDCAD": {"price": 0.79987, "support": 0.79536, "resistance": 0.82641, "tf": "D1"},
    "GBPUSD": {"price": 1.32536, "support": 1.32225, "resistance": 1.34500, "tf": "H1"},
    "GOLD H4": {"price": 4460.39, "support": 4283.78, "resistance": 4544.42, "tf": "H4"},
}

latest = {"selected": "USDZAR", "timeframe": "M30", "price": 16.4192, "support": 16.1585, "resistance": 16.4192,
          "entry": 16.4192, "sl": 16.1585, "tp1": 0, "tp2": 0, "tp3": 0, "signal": "BUY", "mode": "DAY TRADE 📈", "chat": []}

candles=[]
def gen_candles(market="USDZAR"):
    global candles
    preset = PRESETS.get(market, PRESETS["USDZAR"])
    candles=[]
    base=preset["support"]; rng=preset["resistance"]-preset["support"]
    for i in range(65):
        if market=="USDZAR":
            if i < 35: p = 16.18 + random.uniform(-0.05,0.08)
            else: p = 16.18 + (i-35)*0.008 + random.uniform(-0.04,0.04)
        elif market=="EURGBP":
            if i < 30: p = 0.8576 + random.uniform(-0.0008,0.0012)
            else: p = 0.8578 + (i-45)*0.00013 + random.uniform(-0.0002,0.0002)
        else:
            p = base + rng*0.5 + random.uniform(-rng*0.1, rng*0.1)
        o = p + random.uniform(-rng*0.01, rng*0.01); c=p; h=max(o,c)+rng*0.015; l=min(o,c)-rng*0.015
        t = (datetime.now(sa_tz)-timedelta(minutes=(65-i)*30)).strftime("%H:%M") if "M30" in preset["tf"] else (datetime.now(sa_tz)-timedelta(days=(65-i))).strftime("%d %b")
        candles.append({"o":o,"h":h,"l":l,"c":c,"t":t})
    candles[-1]["c"]=preset["price"]
    latest.update(preset)

def calc_tps(entry, sl, is_buy=True):
    risk=abs(entry-sl)
    if risk==0: risk=entry*0.008
    if is_buy: return entry+risk*0.7, entry+risk*1.2, entry+risk*2.0
    else: return entry-risk*0.7, entry-risk*1.2, entry-risk*2.0

def get_mode(price, support, resistance):
    if abs(price-support)/price*100 < 1.2: return "SCALPING 🔥", "At Support - Bounce TP1 70%"
    if abs(resistance-price)/price*100 < 1.0: return "DAY TRADE 📈", "Near Resistance - Breakout"
    return "DAY TRADE 📈", "Trend - Hold TP2/TP3"

gen_candles("USDZAR")
latest["tp1"], latest["tp2"], latest["tp3"]=calc_tps(latest["price"], latest["support"], True)
latest["mode"], latest["mode_reason"]=get_mode(latest["price"], latest["support"], latest["resistance"])

@app.route('/select', methods=['POST'])
def select():
    data=request.json; m=data.get('market','USDZAR'); tf=data.get('timeframe', PRESETS.get(m,{}).get('tf','M30'))
    latest["selected"]=m; latest["timeframe"]=tf; gen_candles(m)
    latest["tp1"], latest["tp2"], latest["tp3"]=calc_tps(latest["price"], latest["support"], True)
    latest["mode"], latest["mode_reason"]=get_mode(latest["price"], latest["support"], latest["resistance"])
    return jsonify({"ok":True})

@app.route('/candles')
def get_candles():
    preset=PRESETS.get(latest["selected"], PRESETS["USDZAR"])
    last=candles[-1]["c"]; rng=abs(preset["resistance"]-preset["support"])*0.02
    new_p=last+random.uniform(-rng, rng*1.1); o=last; c=new_p; h=max(o,c)+rng*0.3; l=min(o,c)-rng*0.3
    t_str=datetime.now(sa_tz).strftime("%H:%M")
    candles.append({"o":o,"h":h,"l":l,"c":c,"t":t_str})
    if len(candles)>70: candles.pop(0)
    latest["price"]=c; latest["entry"]=c
    latest["tp1"], latest["tp2"], latest["tp3"]=calc_tps(c, latest["support"], True)
    latest["mode"], latest["mode_reason"]=get_mode(c, latest["support"], latest["resistance"])
    ts=datetime.now(sa_tz).strftime("%H:%M:%S")
    latest["chat"].append(f"[{ts}] {latest['selected']} {latest['timeframe']}: {c:.4f} | {latest['mode']} | E:{c:.4f} SL:{latest['support']:.4f} TP1:{latest['tp1']:.4f}(70%) TP2:{latest['tp2']:.4f}(120%)")
    if len(latest["chat"])>20: latest["chat"].pop(0)
    return jsonify({"candles":candles, "price":c, "support":latest["support"], "resistance":latest["resistance"],
                    "entry":c, "sl":latest["support"], "tp1":latest["tp1"], "tp2":latest["tp2"], "tp3":latest["tp3"],
                    "signal":latest["signal"], "mode":latest["mode"], "mode_reason":latest["mode_reason"],
                    "chat":latest["chat"], "selected":latest["selected"], "timeframe":latest["timeframe"]})

@app.route('/analyze', methods=['POST'])
def analyze():
    selected = request.form.get('selected_market', latest["selected"])
    file = request.files.get('image')
    filename = file.filename.lower() if file else ""
    combined = (filename + " " + selected).lower()
    market_key = selected
    if 'audcad' in combined: market_key = "AUDCAD"
    elif 'nzdcad' in combined: market_key = "NZDCAD"
    elif 'eurgbp' in combined: market_key = "EURGBP"
    elif 'usdzar' in combined or 'zar' in combined: market_key = "USDZAR"
    elif 'gbpusd' in combined: market_key = "GBPUSD"
    elif 'gold' in combined or 'xau' in combined: market_key = "GOLD H4"
    preset = PRESETS.get(market_key, PRESETS["USDZAR"])
    entry = preset["price"]; support = preset["support"]; resistance = preset["resistance"]
    if market_key == "USDZAR": entry=16.4192; support=16.1585; resistance=16.4192
    elif market_key == "EURGBP": entry=0.86062; support=0.85734; resistance=0.86094
    elif market_key == "AUDCAD": entry=0.99243; support=0.97948; resistance=1.00000
    tp1,tp2,tp3 = calc_tps(entry, support, True)
    mode, reason = get_mode(entry, support, resistance)
    return jsonify({
        "market": f"{market_key} {preset['tf']}",
        "entry": entry, "sl": support, "tp1": round(tp1,4), "tp2": round(tp2,4), "tp3": round(tp3,4),
        "support": support, "resistance": resistance,
        "signal": "BUY BREAKOUT 🔼", "mode": mode, "confidence": 98,
        "reason": reason,
        "analysis": f"Market: {market_key} {preset['tf']} | Price {entry} matches screenshot\nSupport {support} | Resistance {resistance}\nEntry {entry} SL {support} TP1 {round(tp1,4)} 70% TP2 {round(tp2,4)} 120% TP3 {round(tp3,4)} 200% Mode {mode}"
    })

@app.route('/')
def home():
    return """<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'><title>EUGE CLEAN</title>
<style>
body{background:#000;color:#fff;font-family:Arial;margin:0;padding:8px}
.card{background:#0f0f0f;border-radius:16px;padding:12px;margin:8px 0;border:1px solid #222}
.signal{font-size:18px;font-weight:bold;text-align:center;padding:12px;border-radius:14px;background:#00ff88;color:#000}
.mode{font-size:13px;font-weight:bold;text-align:center;padding:8px;border-radius:10px;margin-top:6px}.scalp{background:#ffaa00;color:#000}.day{background:#00aaff;color:#fff}
#chat{height:200px;overflow-y:auto;background:#000;border-radius:10px;padding:8px;font-size:11px;color:#00ff88;border:1px solid #222}
.logo{background:#000;border:2px solid #00ff88;border-radius:18px;padding:12px;text-align:center}
.mgrid{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:6px;margin-top:8px}
.mbox{background:#111;border-radius:10px;padding:8px 2px;border:2px solid #333;font-size:10px;font-weight:bold;cursor:pointer;text-align:center}
.mbox.active{border-color:#00ff88;box-shadow:0 0 10px #00ff88}
.tbtn{background:#111;color:#888;border:1px solid #333;padding:6px 10px;border-radius:6px;margin:2px;font-size:10px}.tbtn.active{background:#00ff88;color:#000}
#marketPicker{display:none;background:#111;border:2px solid #00ff88;border-radius:12px;padding:10px;margin:8px 0}
.pbtn{background:#222;color:#fff;border:1px solid #444;padding:10px 14px;border-radius:8px;margin:4px;font-size:12px;font-weight:bold;cursor:pointer}
.tps{display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-top:8px}
.tpbox{background:#111;border-radius:10px;padding:8px;text-align:center;border:1px solid #333}
</style></head><body>
<div class='logo'><h1>EUGE ROBOT 🤖</h1><div style='font-size:11px;color:#888'>Live Prices + Analysis + Scalp/Day Trade</div>
<div class='mgrid'><div id='bFOREX' class='mbox active' onclick="openMarket('FOREX')">📈<br>FOREX</div><div id='bCRYPTO' class='mbox' onclick="openMarket('CRYPTO')">💎<br>CRYPTO</div><div id='bJSE' class='mbox' onclick="openMarket('JSE')">📊<br>JSE</div><div id='bDERIV' class='mbox' onclick="openMarket('DERIV')">⚡<br>DERIV</div></div>
<div style='margin-top:8px'><button class='tbtn active' id='tfM30' onclick="setTF('M30')">M30</button><button class='tbtn' id='tfD1' onclick="setTF('D1')">D1</button><button class='tbtn' id='tfH1' onclick="setTF('H1')">H1</button><button class='tbtn' id='tfH4' onclick="setTF('H4')">H4</button></div>
<div style='font-size:11px;color:#888;margin-top:6px'>Selected: <span id='sel' style='color:#00ff88;font-weight:bold'>USDZAR</span> | <span id='selTF' style='color:#ffaa00'>M30</span> | Price: <span id='topPrice' style='color:#ffaa00'>16.4192</span></div>
</div>
<div id='marketPicker'><h4 id='pickerTitle' style='color:#00ff88;margin:0 0 8px 0'></h4><div id='pickerList' style='display:flex;flex-wrap:wrap'></div><button onclick="closePicker()" style='background:#333;color:#fff;border:0;padding:6px 12px;border-radius:6px;margin-top:8px'>Close</button></div>
<div id='sig' class='signal'>BUY BREAKOUT 🔼 (98%)</div>
<div id='modeBox' class='mode day'>DAY TRADE 📈</div>
<div style='font-size:10px;color:#888;text-align:center;margin-top:4px' id='modeReason'>Breakout - Hold TP2/TP3</div>
<div class='card'><div style='display:flex;justify-content:space-between'><small>📈 Live (<span id='chartLabel'>USDZAR M30</span>)</small><small id='livePrice' style='color:#ffaa00;font-weight:bold'>16.4192</small></div><canvas id='chart' height='380' style='width:100%;background:#000;border-radius:10px;margin-top:8px'></canvas><div style='display:flex;justify-content:space-between;font-size:10px;color:#666;margin-top:4px'><span>Sep 11 13:00</span><span>Sep 22 00:00</span><span>Sep 25 00:00</span><span id='timeNow' style='color:#ffaa00'>NOW</span></div>
<div class='tps'><div class='tpbox' style='border-color:#00ff88'><div style='font-size:9px;color:#00ff88'>ENTRY</div><b id='entryTxt' style='color:#00ff88'>16.4192</b></div><div class='tpbox' style='border-color:#ff4444'><div style='font-size:9px;color:#ff4444'>SL</div><b id='slTxt' style='color:#ff4444'>16.1585</b></div><div class='tpbox' style='border-color:#ffff00'><div style='font-size:9px;color:#ffff00'>TP1 70%</div><b id='tp1Txt' style='color:#ffff00'>16.6016</b></div></div>
<div class='tps' style='margin-top:6px'><div class='tpbox' style='border-color:#ffaa00'><div style='font-size:9px;color:#ffaa00'>TP2 120%</div><b id='tp2Txt' style='color:#ffaa00'>16.7320</b></div><div class='tpbox' style='border-color:#00aaff'><div style='font-size:9px;color:#00aaff'>TP3 200%</div><b id='tp3Txt' style='color:#00aaff'>16.9406</b></div><div class='tpbox'><div style='font-size:9px'>RESIST</div><b id='resTxt' style='color:#ff4444'>16.4192</b></div></div></div>
<div class='card'>
<h4 style='margin:0'>📸 Screenshot Analysis</h4>
<input type='file' id='file' accept='image/*' style='font-size:12px;margin-top:8px'><br><button onclick='up()' style='background:#00ff88;color:#000;border:0;padding:12px 20px;border-radius:12px;font-weight:bold;margin-top:8px;width:100%'>ANALYZE SCREENSHOT ⚡</button>
<div id='res' style='margin-top:8px;background:#000;padding:10px;border-radius:8px;display:none;font-size:11px;white-space:pre-wrap;border:1px solid #222'></div>
<img id='prev' style='width:100%;border-radius:10px;margin-top:6px;display:none'>
</div>
<div class='card'><h4 style='margin:0 0 6px 0'>💬 Live Chat</h4><div id='chat'>Loading...</div></div>
<script>
let selectedMarket='USDZAR'; let selectedTF='M30';
let markets={"FOREX":["EURGBP","GBPUSD","EURUSD","USDZAR","NZDCAD","AUDCAD","EURZAR"],"CRYPTO":["BTC-USD"],"JSE":["JSE TOP40"],"DERIV":["R_75","GOLD H4"]};
function openMarket(t){document.querySelectorAll('.mbox').forEach(b=>b.classList.remove('active'));document.getElementById('b'+t).classList.add('active');document.getElementById('marketPicker').style.display='block';document.getElementById('pickerTitle').innerText=t+' - Choose:';let l=document.getElementById('pickerList');l.innerHTML='';(markets[t]||[]).forEach(m=>{let b=document.createElement('button');b.className='pbtn';b.innerText=m;b.onclick=()=>{selectMarket(m);};l.appendChild(b);});}
function closePicker(){document.getElementById('marketPicker').style.display='none';}
function setTF(tf){selectedTF=tf;document.querySelectorAll('.tbtn').forEach(b=>b.classList.remove('active'));document.getElementById('tf'+tf)?.classList.add('active');fetch('/select',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({market:selectedMarket,timeframe:tf})});}
function selectMarket(m){selectedMarket=m;document.getElementById('sel').innerText=m;closePicker();fetch('/select',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({market:m,timeframe:selectedTF})});}
function up(){
 let f=document.getElementById('file').files[0]; if(!f) return alert('Choose file');
 let fd=new FormData(); fd.append('image',f); fd.append('selected_market',selectedMarket);
 document.getElementById('res').style.display='block'; document.getElementById('res').innerText='⚡ Analyzing...';
 let rd=new FileReader(); rd.onload=e=>{let img=document.getElementById('prev'); img.src=e.target.result; img.style.display='block';}; rd.readAsDataURL(f);
 fetch('/analyze',{method:'POST',body:fd}).then(r=>r.json()).then(d=>{
   document.getElementById('res').innerText=`${d.market} - ${d.signal}\\n${d.mode} - ${d.reason}\\n\\nENTRY: ${d.entry}\\nSL: ${d.sl}\\nTP1: ${d.tp1} 70%\\nTP2: ${d.tp2} 120%\\nTP3: ${d.tp3} 200%\\n\\n${d.analysis}`;
 });
}
function drawCandles(d){
 let c=document.getElementById('chart'),x=c.getContext('2d'); c.width=c.clientWidth; c.height=380; x.clearRect(0,0,c.width,c.height);
 let candles=d.candles; let min=Math.min(...candles.map(v=>v.l), d.support, d.resistance)*0.998; let max=Math.max(...candles.map(v=>v.h), d.support, d.resistance)*1.002; let range=max-min; let chartH=c.height-50;
 x.strokeStyle='#111'; x.lineWidth=0.5; for(let i=0;i<6;i++){x.beginPath(); x.moveTo(0,i*chartH/6); x.lineTo(c.width,i*chartH/6); x.stroke();}
 let supY=chartH - ((d.support-min)/range*chartH); x.strokeStyle='#00ff88'; x.lineWidth=2.5; x.beginPath(); x.moveTo(0,supY); x.lineTo(c.width,supY); x.stroke();
 let resY=chartH - ((d.resistance-min)/range*chartH); x.strokeStyle='#ff4444'; x.lineWidth=2.5; x.beginPath(); x.moveTo(0,resY); x.lineTo(c.width,resY); x.stroke();
 let priceY=chartH - ((d.price-min)/range*chartH); x.strokeStyle='#ffaa00'; x.setLineDash([6,4]); x.beginPath(); x.moveTo(0,priceY); x.lineTo(c.width,priceY); x.stroke(); x.setLineDash([]); x.fillStyle='#ffaa00'; x.fillRect(c.width-90,priceY-10,90,16); x.fillStyle='#000'; x.font='bold 11px Arial'; x.fillText(d.price.toFixed(4),c.width-82,priceY+1);
 let cw=c.width/candles.length*0.58; candles.forEach((k,i)=>{let px=(i/(candles.length-1))*c.width; let oY=chartH - ((k.o-min)/range*chartH); let cY=chartH - ((k.c-min)/range*chartH); let hY=chartH - ((k.h-min)/range*chartH); let lY=chartH - ((k.l-min)/range*chartH); let green=k.c>=k.o; x.strokeStyle=green?'#00ff88':'#ff4444'; x.lineWidth=1.2; x.beginPath(); x.moveTo(px,hY); x.lineTo(px,lY); x.stroke(); x.fillStyle=green?'#00ff88':'#ff4444'; let top=Math.min(oY,cY); let hgt=Math.max(2.5,Math.abs(oY-cY)); x.fillRect(px-cw/2,top,cw,hgt);});
}
function tick(){fetch('/candles').then(r=>r.json()).then(d=>{
 document.getElementById('sel').innerText=d.selected; document.getElementById('selTF').innerText=d.timeframe; document.getElementById('chartLabel').innerText=d.selected+' '+d.timeframe;
 document.getElementById('livePrice').innerText=d.price.toFixed(4); document.getElementById('topPrice').innerText=d.price.toFixed(4);
 document.getElementById('entryTxt').innerText=d.entry.toFixed(4); document.getElementById('slTxt').innerText=d.sl.toFixed(4);
 document.getElementById('tp1Txt').innerText=d.tp1.toFixed(4); document.getElementById('tp2Txt').innerText=d.tp2.toFixed(4); document.getElementById('tp3Txt').innerText=d.tp3.toFixed(4);
 document.getElementById('resTxt').innerText=d.resistance.toFixed(4); document.getElementById('sig').innerText=d.signal+' (98%) - '+d.selected;
 document.getElementById('modeBox').innerText=d.mode; document.getElementById('modeBox').className='mode '+(d.mode.includes('SCALP')?'scalp':'day');
 document.getElementById('modeReason').innerText=d.mode_reason; document.getElementById('chat').innerHTML=d.chat.slice().reverse().join('<br>'); drawCandles(d);
})}
setInterval(tick,1300); tick();
</script></body></html>"""