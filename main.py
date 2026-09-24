from flask import Flask, jsonify
import random
from datetime import datetime
import pytz

app = Flask(__name__)
sa_tz = pytz.timezone('Africa/Johannesburg')

latest = {
    "price": 4392.60, "support": 4283.78, "resistance": 4544.42,
    "signal": "BUY", "confidence": 88, "trend": "BULLISH",
    "chat": ["EUGE V8.3 CLEAN - Only price + candles + support/resistance"], "selected": "GOLD H4", "timeframe": "H4"
}

# Clean GOLD candles - no noise
candles = []
# Support zone 4283, Resistance 4544, Price 4392 in middle - breakout
for i in range(50):
    if i < 20:
        p = 4320 + i*2 + random.uniform(-6,6)
    elif i < 35:
        p = 4285 + (i-20)*5 + random.uniform(-5,5)  # from support
    else:
        p = 4360 + (i-35)*4 + random.uniform(-4,4)  # to 4420+
    o = p + random.uniform(-4,4)
    c = p
    h = max(o,c)+random.uniform(1,6)
    l = min(o,c)-random.uniform(1,6)
    candles.append({"o":o,"h":h,"l":l,"c":c})
candles[-1]["c"]=4392.60

@app.route('/candles')
def get_candles():
    last = candles[-1]["c"]
    new_p = last + random.uniform(-3,5)
    o = last
    c = new_p
    h = max(o,c)+random.uniform(1,5)
    l = min(o,c)-random.uniform(1,5)
    candles.append({"o":o,"h":h,"l":l,"c":c})
    if len(candles)>55: candles.pop(0)
    
    latest["price"]=c
    t=datetime.now(sa_tz).strftime("%H:%M:%S")
    latest["chat"].append(f"[{t}] GOLD H4: {c:.2f} | Support: 4283.78 | Resistance: 4544.42 | Price between zones")
    if len(latest["chat"])>20: latest["chat"].pop(0)
    
    return jsonify({
        "candles":candles, "price":c, "support":4283.78, "resistance":4544.42,
        "signal":latest["signal"], "confidence":88, "trend":latest["trend"],
        "chat":latest["chat"], "selected":"GOLD H4", "timeframe":"H4"
    })

@app.route('/')
def home():
    return """
<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'><title>EUGE V8.3 CLEAN</title>
<style>
body{background:#000;color:#fff;font-family:Arial;margin:0;padding:8px}
.card{background:#0e0e0e;border-radius:15px;padding:12px;margin:8px 0;border:1px solid #222}
.signal{font-size:22px;font-weight:bold;text-align:center;padding:14px;border-radius:14px;background:#00ff88;color:#000}
#chat{height:180px;overflow-y:auto;background:#000;border-radius:10px;padding:8px;font-size:11px;color:#00ff88}
.logo{background:#000;border:2px solid #00ff88;border-radius:20px;padding:12px;text-align:center}
.logo h1{margin:0;font-size:30px;color:#00ff88;font-style:italic}
</style></head><body>
<div class='logo'><h1>EUGE-V7.5</h1><div style='font-size:11px;margin-top:6px;color:#888'>CLEAN - Only Candles + Support/Resistance</div><div style='font-size:12px;margin-top:4px'>GOLD H4 | Price: <span id='topPrice' style='color:#ffaa00;font-weight:bold'>4392.60</span></div></div>

<div id='sig' class='signal'>BUY (88%) - Above Support</div>

<div class='card'>
<div style='display:flex;justify-content:space-between'><small>📈 GOLD H4 - CLEAN</small><small id='livePrice' style='color:#ffaa00;font-weight:bold;font-size:16px'>4392.60</small></div>
<canvas id='chart' height='360' style='width:100%;background:#000;border-radius:10px;margin-top:8px'></canvas>
<div style='display:flex;justify-content:space-between;font-size:11px;margin-top:8px'>
<span style='color:#00ff88'>🟩 SUPPORT: 4283.78</span>
<span style='color:#ff4444'>🟥 RESISTANCE: 4544.42</span>
</div>
</div>

<div class='card'><h4 style='margin:0 0 6px 0'>💬 Live</h4><div id='chat'>Loading...</div></div>

<script>
function drawCandles(d){
 let c=document.getElementById('chart'),x=c.getContext('2d');
 c.width=c.clientWidth; c.height=360; x.clearRect(0,0,c.width,c.height);
 let candles=d.candles;
 let min=Math.min(...candles.map(v=>v.l)), max=Math.max(...candles.map(v=>v.h));
 let range=max-min; if(range<30) range=80;
 let pad=30; let chartH=c.height-pad*2;
 
 // Grid - very light
 x.strokeStyle='#111'; x.lineWidth=0.5;
 for(let i=0;i<5;i++){x.beginPath(); x.moveTo(0,i*c.height/5); x.lineTo(c.width,i*c.height/5); x.stroke();}

 // SUPPORT ZONE - Green transparent
 let supY=c.height-((d.support-min)/range*chartH+pad);
 x.fillStyle='rgba(0,255,136,0.15)'; x.fillRect(0,supY-15,c.width,30);
 x.strokeStyle='#00ff88'; x.lineWidth=2; x.beginPath(); x.moveTo(0,supY); x.lineTo(c.width,supY); x.stroke();
 x.fillStyle='#00ff88'; x.font='bold 11px Arial'; x.fillText('SUPPORT 4283.78',8,supY-18);

 // RESISTANCE ZONE - Red transparent
 let resY=c.height-((d.resistance-min)/range*chartH+pad);
 x.fillStyle='rgba(255,68,68,0.15)'; x.fillRect(0,resY-15,c.width,30);
 x.strokeStyle='#ff4444'; x.lineWidth=2; x.beginPath(); x.moveTo(0,resY); x.lineTo(c.width,resY); x.stroke();
 x.fillStyle='#ff4444'; x.font='bold 11px Arial'; x.fillText('RESISTANCE 4544.42',8,resY-18);

 // PRICE LINE - Orange
 let priceY=c.height-((d.price-min)/range*chartH+pad);
 x.strokeStyle='#ffaa00'; x.lineWidth=1.5; x.setLineDash([5,4]); x.beginPath(); x.moveTo(0,priceY); x.lineTo(c.width,priceY); x.stroke(); x.setLineDash([]);
 x.fillStyle='#ffaa00'; x.fillRect(c.width-75,priceY-10,75,14); x.fillStyle='#000'; x.font='bold 11px Arial'; x.fillText(d.price.toFixed(2),c.width-65,priceY);

 // CANDLES ONLY - Clean!
 let cw=c.width/candles.length*0.65;
 candles.forEach((k,i)=>{
   let px=(i/(candles.length-1))*c.width;
   let oY=c.height-((k.o-min)/range*chartH+pad);
   let cY=c.height-((k.c-min)/range*chartH+pad);
   let hY=c.height-((k.h-min)/range*chartH+pad);
   let lY=c.height-((k.l-min)/range*chartH+pad);
   let green=k.c>=k.o;
   // Wick
   x.strokeStyle=green?'#00ff88':'#ff4444'; x.lineWidth=1.2;
   x.beginPath(); x.moveTo(px,hY); x.lineTo(px,lY); x.stroke();
   // Body
   x.fillStyle=green?'#00ff88':'#ff4444';
   let top=Math.min(oY,cY); let hgt=Math.max(3,Math.abs(oY-cY));
   x.fillRect(px-cw/2,top,cw,hgt);
 });
}

function tick(){fetch('/candles').then(r=>r.json()).then(d=>{
 document.getElementById('livePrice').innerText=d.price.toFixed(2);
 document.getElementById('topPrice').innerText=d.price.toFixed(2);
 document.getElementById('chat').innerHTML=d.chat.slice().reverse().join('<br>');
 drawCandles(d);
})}
setInterval(tick,1300); tick();
</script></body></html>"""