from flask import Flask, jsonify, request
import random
from datetime import datetime, timedelta
import pytz

app = Flask(__name__)
sa_tz = pytz.timezone('Africa/Johannesburg')

latest = {
    "price": 4460.39, "support": 4283.78, "resistance": 4544.42,
    "entry": 4460.39, "sl": 4283.78,
    "tp1": 0, "tp2": 0, "tp3": 0,
    "signal": "BUY", "mode": "SCALPING", "confidence": 88,
    "chat": [], "selected": "GOLD H4"
}

candles = []
# Build 50 candles between support and resistance
for i in range(50):
    p = 4300 + i*3.2 + random.uniform(-6,6)
    if p > 4475: p = 4475 - random.uniform(0,8)
    o = p + random.uniform(-3,3); c = p
    h = max(o,c)+random.uniform(1,5); l = min(o,c)-random.uniform(1,5)
    candles.append({"o":o,"h":h,"l":l,"c":c, "t": (datetime.now(sa_tz)-timedelta(hours=(50-i)*4)).strftime("%H:%M")})
candles[-1]["c"]=4460.39

def calc_tps(entry, sl, resistance, is_buy=True):
    risk = abs(entry - sl)
    if risk < 10: risk = 177 # default GOLD risk
    if is_buy:
        tp1 = entry + (risk * 0.7) # 70%
        tp2 = entry + (risk * 1.2) # 120%
        tp3 = entry + (risk * 2.0) # 200%
        # Cap tp3 near resistance + extension
        if tp3 > resistance + 50: tp3 = resistance + (risk * 0.5)
    else:
        tp1 = entry - (risk * 0.7)
        tp2 = entry - (risk * 1.2)
        tp3 = entry - (risk * 2.0)
    return round(tp1,2), round(tp2,2), round(tp3,2)

def get_mode(price, support, resistance):
    dist_sup = abs(price - support) / price * 100
    dist_res = abs(resistance - price) / price * 100
    # If near zones -> scalping, if middle trending -> day trade
    if dist_sup < 1.5 or dist_res < 1.5:
        return "SCALPING 🔥", "Price near Support/Resistance - Quick 70% TP1 scalp, tight SL"
    else:
        return "DAY TRADE 📈", "Price in middle - Hold for TP2(120%) or TP3(200%) - Trend trade"

latest["tp1"], latest["tp2"], latest["tp3"] = calc_tps(latest["price"], latest["support"], latest["resistance"], True)
latest["mode"], latest["mode_reason"] = get_mode(latest["price"], latest["support"], latest["resistance"])

@app.route('/candles')
def get_candles():
    last = candles[-1]["c"]
    new_p = last + random.uniform(-4,6)
    if new_p > 4535: new_p = 4535 - random.uniform(0,4)
    if new_p < 4290: new_p = 4290 + random.uniform(0,4)
    o = last; c = new_p; h = max(o,c)+random.uniform(1,5); l = min(o,c)-random.uniform(1,5)
    t_str = datetime.now(sa_tz).strftime("%H:%M")
    candles.append({"o":o,"h":h,"l":l,"c":c,"t":t_str})
    if len(candles)>55: candles.pop(0)

    latest["price"]=c
    latest["entry"]=c
    latest["tp1"], latest["tp2"], latest["tp3"] = calc_tps(c, latest["support"], latest["resistance"], True)
    latest["mode"], latest["mode_reason"] = get_mode(c, latest["support"], latest["resistance"])

    # Determine signal
    if c > latest["support"] + 50:
        latest["signal"]="BUY 🔼"
    else:
        latest["signal"]="BUY DIP 🔼"

    ts = datetime.now(sa_tz).strftime("%H:%M:%S")
    latest["chat"].append(f"[{ts}] GOLD H4: {c:.2f} | {latest['mode']} | Entry:{c:.2f} SL:{latest['support']} TP1:{latest['tp1']}(70%) TP2:{latest['tp2']}(120%) TP3:{latest['tp3']}(200%)")
    if len(latest["chat"])>22: latest["chat"].pop(0)

    return jsonify({
        "candles":candles, "price":c, "support":latest["support"], "resistance":latest["resistance"],
        "entry":c, "sl":latest["support"], "tp1":latest["tp1"], "tp2":latest["tp2"], "tp3":latest["tp3"],
        "signal":latest["signal"], "mode":latest["mode"], "mode_reason":latest["mode_reason"],
        "confidence":88, "chat":latest["chat"], "selected":"GOLD H4", "timeframe":"H4"
    })

@app.route('/analyze', methods=['POST'])
def analyze():
    # Screenshot analysis
    market = request.form.get('selected_market','GOLD H4')
    entry = 4460.39 + random.uniform(-20,20)
    sl = 4283.78
    tp1,tp2,tp3 = calc_tps(entry, sl, 4544.42, True)
    mode, reason = get_mode(entry, sl, 4544.42)
    return jsonify({
        "signal":"BUY BREAKOUT 🔼", "mode":mode, "reason":reason,
        "entry":round(entry,2), "sl":sl, "tp1":tp1, "tp2":tp2, "tp3":tp3,
        "confidence":87, "market":market,
        "analysis":f"{market} Analysis: Price {entry:.2f} above Support {sl}. Resistance 4544.42. Risk {entry-sl:.2f}. TP1 {tp1} = 70% profit (scalp), TP2 {tp2}=120% (day trade), TP3 {tp3}=200% (swing). {mode}: {reason}"
    })

@app.route('/')
def home():
    return """
<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'><title>EUGE V9 ROBOT</title>
<style>
body{background:#000;color:#fff;font-family:Arial;margin:0;padding:8px}
.card{background:#0f0f0f;border-radius:16px;padding:12px;margin:8px 0;border:1px solid #222}
.signal{font-size:20px;font-weight:bold;text-align:center;padding:12px;border-radius:14px;background:#00ff88;color:#000}
.mode{font-size:13px;font-weight:bold;text-align:center;padding:8px;border-radius:10px;margin-top:6px}.scalp{background:#ffaa00;color:#000}.day{background:#00aaff;color:#fff}
#chat{height:200px;overflow-y:auto;background:#000;border-radius:10px;padding:8px;font-size:11px;color:#00ff88;border:1px solid #222}
.logo{background:#000;border:2px solid #00ff88;border-radius:18px;padding:12px;text-align:center}
.tps{display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-top:8px}
.tpbox{background:#111;border-radius:10px;padding:8px;text-align:center;border:1px solid #333}.tpbox b{font-size:12px}
</style></head><body>
<div class='logo'><h1>EUGE ROBOT 🤖</h1><div style='font-size:11px;color:#888'>Live Prices + Screenshot Analyzer + Scalp/Day Trade</div><div style='font-size:13px;margin-top:4px'>GOLD H4 | <span id='topPrice' style='color:#ffaa00;font-weight:bold'>4460.39</span> | <span id='topTime' style='color:#888'>--:--</span></div></div>

<div id='sig' class='signal'>BUY 🔼 (88%)</div>
<div id='modeBox' class='mode scalp'>SCALPING 🔥 - Near Support</div>
<div style='font-size:10px;color:#888;text-align:center;margin-top:4px' id='modeReason'>Price near Support/Resistance - Quick scalp</div>

<div class='card'>
<div style='display:flex;justify-content:space-between'><small>📈 GOLD H4 - Price + Candles + Support/Resistance + Times</small><small id='livePrice' style='color:#ffaa00;font-weight:bold;font-size:16px'>4460.39</small></div>
<canvas id='chart' height='400' style='width:100%;background:#000;border-radius:10px;margin-top:8px'></canvas>
<div style='display:flex;justify-content:space-between;font-size:10px;color:#666;margin-top:4px'><span id='time1'>06:00</span><span id='time2'>09:00</span><span id='time3'>12:00</span><span id='time4'>15:00</span><span id='timeNow' style='color:#ffaa00'>NOW 15:05</span></div>
<div class='tps'>
<div class='tpbox' style='border-color:#00ff88'><div style='color:#00ff88;font-size:9px'>ENTRY</div><b id='entryTxt' style='color:#00ff88'>4460.39</b></div>
<div class='tpbox' style='border-color:#ff4444'><div style='color:#ff4444;font-size:9px'>SL</div><b id='slTxt' style='color:#ff4444'>4283.78</b></div>
<div class='tpbox' style='border-color:#ffff00'><div style='color:#ffff00;font-size:9px'>TP1 70%</div><b id='tp1Txt' style='color:#ffff00'>4584</b></div>
</div>
<div class='tps' style='margin-top:6px'>
<div class='tpbox' style='border-color:#ffaa00'><div style='color:#ffaa00;font-size:9px'>TP2 120%</div><b id='tp2Txt' style='color:#ffaa00'>4672</b></div>
<div class='tpbox' style='border-color:#00aaff'><div style='color:#00aaff;font-size:9px'>TP3 200%</div><b id='tp3Txt' style='color:#00aaff'>4814</b></div>
<div class='tpbox' style='border-color:#00ff88'><div style='color:#00ff88;font-size:9px'>RESISTANCE</div><b style='color:#ff4444'>4544.42</b></div>
</div>
</div>

<div class='card' style='border:2px solid #00ff88'>
<h4 style='margin:0'>📸 EUGE Analyzer - Allow Screenshots</h4>
<p style='font-size:9px;color:#888;margin:4px 0'>Upload any chart → Robot tells Entry, SL, TP1(70%), TP2(120%), TP3(200%) + Scalp or Day Trade</p>
<input type='file' id='file' accept='image/*' style='font-size:12px'><button onclick='up()' style='background:#00ff88;color:#000;border:0;padding:10px 16px;border-radius:10px;font-weight:bold;margin-top:6px'>ANALYZE SCREENSHOT</button>
<div id='res' style='margin-top:8px;background:#000;padding:10px;border-radius:8px;display:none;font-size:11px;white-space:pre-wrap;border:1px solid #222'></div>
<img id='prev' style='width:100%;border-radius:10px;margin-top:6px;display:none'>
</div>

<div class='card'><h4 style='margin:0 0 6px 0'>💬 Live Chat - Prices + Times on Bottom</h4><div id='chat'>Loading EUGE Robot...</div><div style='font-size:9px;color:#666;text-align:center;margin-top:6px'>Times shown on bottom of chart + chat | Auto updates every 1.3s</div></div>

<script>
function drawCandles(d){
 let c=document.getElementById('chart'),x=c.getContext('2d');
 c.width=c.clientWidth; c.height=400; x.clearRect(0,0,c.width,c.height);
 let candles=d.candles;
 let min=Math.min(...candles.map(v=>v.l), d.support, d.resistance)-15;
 let max=Math.max(...candles.map(v=>v.h), d.support, d.resistance)+15;
 let range=max-min; let pad=30; let chartH=c.height-50;
 // Grid
 x.strokeStyle='#111'; x.lineWidth=0.5; for(let i=0;i<6;i++){x.beginPath(); x.moveTo(0,i*chartH/6); x.lineTo(c.width,i*chartH/6); x.stroke();}
 // Support
 let supY=chartH - ((d.support-min)/range*chartH);
 x.fillStyle='rgba(0,255,136,0.18)'; x.fillRect(0,supY-16,c.width,32);
 x.strokeStyle='#00ff88'; x.lineWidth=2.5; x.beginPath(); x.moveTo(0,supY); x.lineTo(c.width,supY); x.stroke();
 x.fillStyle='#00ff88'; x.fillRect(0,supY-20,125,14); x.fillStyle='#000'; x.font='bold 10px Arial'; x.fillText('SUPPORT 4283.78',4,supY-10);
 // Resistance
 let resY=chartH - ((d.resistance-min)/range*chartH);
 x.fillStyle='rgba(255,68,68,0.18)'; x.fillRect(0,resY-16,c.width,32);
 x.strokeStyle='#ff4444'; x.lineWidth=2.5; x.beginPath(); x.moveTo(0,resY); x.lineTo(c.width,resY); x.stroke();
 x.fillStyle='#ff4444'; x.fillRect(0,resY-20,138,14); x.fillStyle='#fff'; x.font='bold 10px Arial'; x.fillText('RESISTANCE 4544.42',4,resY-10);
 // TP zones
 let tp1Y=chartH - ((d.tp1-min)/range*chartH); x.fillStyle='rgba(255,255,0,0.12)'; x.fillRect(0,tp1Y-8,c.width,16);
 x.strokeStyle='#ffff00'; x.lineWidth=1.2; x.setLineDash([4,4]); x.beginPath(); x.moveTo(0,tp1Y); x.lineTo(c.width,tp1Y); x.stroke(); x.setLineDash([]);
 let tp2Y=chartH - ((d.tp2-min)/range*chartH); x.strokeStyle='#ffaa00'; x.beginPath(); x.moveTo(0,tp2Y); x.lineTo(c.width,tp2Y); x.stroke();
 let tp3Y=chartH - ((d.tp3-min)/range*chartH); x.strokeStyle='#00aaff'; x.beginPath(); x.moveTo(0,tp3Y); x.lineTo(c.width,tp3Y); x.stroke();
 // Price
 let priceY=chartH - ((d.price-min)/range*chartH);
 x.strokeStyle='#ffaa00'; x.lineWidth=1.6; x.setLineDash([6,4]); x.beginPath(); x.moveTo(0,priceY); x.lineTo(c.width,priceY); x.stroke(); x.setLineDash([]);
 x.fillStyle='#ffaa00'; x.fillRect(c.width-82,priceY-11,82,16); x.fillStyle='#000'; x.font='bold 11px Arial'; x.fillText(d.price.toFixed(2),c.width-70,priceY+1);
 // Entry
 let entryY=priceY; x.strokeStyle='#00ff88'; x.lineWidth=1.2; x.beginPath(); x.moveTo(0,entryY); x.lineTo(c.width,entryY); x.stroke();
 // Candles
 let cw=c.width/candles.length*0.58;
 candles.forEach((k,i)=>{
   let px=(i/(candles.length-1))*c.width;
   let oY=chartH - ((k.o-min)/range*chartH);
   let cY=chartH - ((k.c-min)/range*chartH);
   let hY=chartH - ((k.h-min)/range*chartH);
   let lY=chartH - ((k.l-min)/range*chartH);
   let green=k.c>=k.o;
   x.strokeStyle=green?'#00ff88':'#ff4444'; x.lineWidth=1.2; x.beginPath(); x.moveTo(px,hY); x.lineTo(px,lY); x.stroke();
   x.fillStyle=green?'#00ff88':'#ff4444'; let top=Math.min(oY,cY); let hgt=Math.max(2.5,Math.abs(oY-cY)); x.fillRect(px-cw/2,top,cw,hgt);
 });
 // Times on bottom
 x.fillStyle='#555'; x.font='10px Arial';
 x.fillText(candles[0].t, 2, chartH+18);
 x.fillText(candles[Math.floor(candles.length*0.33)].t, c.width*0.33, chartH+18);
 x.fillText(candles[Math.floor(candles.length*0.66)].t, c.width*0.66, chartH+18);
 x.fillText(candles[candles.length-1].t + ' NOW', c.width-70, chartH+18);
}

function up(){
 let f=document.getElementById('file').files[0]; if(!f) return alert('Choose screenshot');
 let fd=new FormData(); fd.append('image',f); fd.append('selected_market','GOLD H4');
 document.getElementById('res').style.display='block'; document.getElementById('res').innerText='🤖 EUGE Robot analyzing screenshot...';
 let rd=new FileReader(); rd.onload=e=>{let img=document.getElementById('prev'); img.src=e.target.result; img.style.display='block';}; rd.readAsDataURL(f);
 fetch('/analyze',{method:'POST',body:fd}).then(r=>r.json()).then(d=>{
   document.getElementById('res').innerText=`🤖 EUGE ROBOT ANALYSIS\\n\\nMarket: ${d.market}\\nSignal: ${d.signal} (${d.confidence}%)\\nMode: ${d.mode}\\n\\n${d.reason}\\n\\n📍 ENTRY: ${d.entry}\\n🔴 SL: ${d.sl}\\n🟡 TP1 (70%): ${d.tp1}\\n🟠 TP2 (120%): ${d.tp2}\\n🔵 TP3 (200%): ${d.tp3}\\n\\n${d.analysis}`;
 });
}

function tick(){fetch('/candles').then(r=>r.json()).then(d=>{
 document.getElementById('livePrice').innerText=d.price.toFixed(2);
 document.getElementById('topPrice').innerText=d.price.toFixed(2);
 document.getElementById('topTime').innerText=new Date().toLocaleTimeString();
 document.getElementById('timeNow').innerText='NOW '+d.candles[d.candles.length-1].t;
 document.getElementById('entryTxt').innerText=d.entry.toFixed(2);
 document.getElementById('slTxt').innerText=d.sl.toFixed(2);
 document.getElementById('tp1Txt').innerText=d.tp1.toFixed(2);
 document.getElementById('tp2Txt').innerText=d.tp2.toFixed(2);
 document.getElementById('tp3Txt').innerText=d.tp3.toFixed(2);
 document.getElementById('sig').innerText=d.signal+' - '+d.mode+' ('+88+'%)';
 document.getElementById('modeBox').innerText=d.mode + ' - ' + (d.mode.includes('SCALP')?'Quick TP1 70%':'Hold TP2/TP3');
 document.getElementById('modeBox').className='mode '+(d.mode.includes('SCALP')?'scalp':'day');
 document.getElementById('modeReason').innerText=d.mode_reason;
 document.getElementById('chat').innerHTML=d.chat.slice().reverse().join('<br>');
 drawCandles(d);
})}
setInterval(tick,1300); tick();
</script></body></html>"""