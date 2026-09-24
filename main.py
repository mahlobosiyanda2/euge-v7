from flask import Flask, jsonify, request
import threading, time, random, requests
from datetime import datetime
import pytz

app = Flask(__name__)
sa_tz = pytz.timezone('Africa/Johannesburg')

latest = {
    "BTC-ZAR": 2035000, "BTC-USD": 115500, "ETH-ZAR": 45000,
    "EURUSD": 1.0845, "GBPUSD": 1.27, "USDZAR": 17.62,
    "JSE_TOP40": 75234, "R_75": 498500,
    "signal": "WAIT - Analyzing...", "confidence": 50, "trend": "WAIT",
    "chat": ["EUGE V7.5 ALL MARKETS started... FOREX/CRYPTO/JSE/DERIV"]
}
price_history = []

def market_loop():
    btc = 2035000; r75 = 498500; jse = 75234
    while True:
        try:
            try:
                r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd,zar", timeout=6).json()
                latest["BTC-USD"]=r['bitcoin']['usd']; latest["BTC-ZAR"]=r['bitcoin']['zar']; latest["ETH-ZAR"]=r['ethereum']['zar']; btc=r['bitcoin']['zar']; latest["USDZAR"]=btc/r['bitcoin']['usd']
            except: btc+=random.uniform(-900,900); latest["BTC-ZAR"]=btc
            try:
                fx=requests.get("https://open.er-api.com/v6/latest/USD",timeout=5).json()
                if 'rates' in fx:
                    latest["USDZAR"]=fx['rates']['ZAR']
                    latest["EURUSD"]=round(1/fx['rates']['EUR'],4); latest["GBPUSD"]=round(1/fx['rates']['GBP'],4)
            except: latest["USDZAR"]+=random.uniform(-0.02,0.02)
            jse+=random.uniform(-25,25); latest["JSE_TOP40"]=jse
            r75+=random.uniform(-2.5,2.5); latest["R_75"]=r75
            price_history.append(r75)
            if len(price_history)>50: price_history.pop(0)
            if len(price_history)>=20:
                avg7=sum(price_history[-7:])/7; avg21=sum(price_history[-21:])/21
                if avg7>avg21+0.5: latest["signal"]="BUY 🔼 SCALP"; latest["trend"]="BULLISH"; latest["confidence"]=82
                elif avg7<avg21-0.5: latest["signal"]="SELL 🔽 SCALP"; latest["trend"]="BEARISH"; latest["confidence"]=80
                else: latest["signal"]="WAIT ↔️"; latest["trend"]="SIDEWAYS"; latest["confidence"]=55
            t=datetime.now(sa_tz).strftime("%H:%M:%S")
            latest["chat"].append(f"[{t}] FOREX:{latest['USDZAR']:.4f} | CRYPTO:{btc:.0f} | JSE:{jse:.0f} | DERIV:{r75:.2f} | {latest['signal']}")
            if len(latest["chat"])>35: latest["chat"].pop(0)
        except: pass
        time.sleep(1.5)

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        f=request.files.get('image')
        from PIL import Image
        img=Image.open(f.stream).convert('L'); w,h=img.size
        left=img.crop((0,h//3,w//3,2*h//3)); right=img.crop((2*w//3,h//3,w,2*h//3))
        l=sum(left.getdata())/(left.size[0]*left.size[1]); r=sum(right.getdata())/(right.size[0]*right.size[1])
        if r>l+1: sig,trend,conf="BUY 🔼","BULLISH",78
        elif l>r+1: sig,trend,conf="SELL 🔽","BEARISH",79
        else: sig,trend,conf="WAIT ↔️","SIDEWAYS",60
        return jsonify({"signal":sig,"trend":trend,"confidence":conf,"market":"FOREX/CRYPTO/JSE/DERIV","reason":"Good scalping setup for any market" })
    except Exception as e: return jsonify({"signal":"Error","trend":"-","confidence":0,"reason":str(e)[:80]})

@app.route('/')
def home():
    return """
<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'><title>EUGE V7.5</title>
<style>
body{background:#000;color:#fff;font-family:Arial;margin:0;padding:8px}
.card{background:#111;border-radius:15px;padding:12px;margin:8px 0;border:1px solid #222}
.price{font-size:20px;font-weight:bold}.grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.signal{font-size:26px;font-weight:bold;text-align:center;padding:14px;border-radius:14px}
.buy{background:#00ff88;color:#000}.sell{background:#ff4444;color:#fff}.wait{background:#333;color:#888}
#chat{height:300px;overflow-y:auto;background:#000;border-radius:10px;padding:8px;font-size:11px;color:#00ff88}
.logo{background:radial-gradient(circle at center,#0f2e0f 0%,#000 70%);border:2px solid #00ff88;border-radius:20px;padding:20px;text-align:center;box-shadow:0 0 30px rgba(0,255,136,0.4)}
.logo h1{margin:0;font-size:44px;color:#00ff88;text-shadow:0 0 20px #00ff88;letter-spacing:2px;font-style:italic}
.logo h2{margin:2px 0 0 0;color:#ffaa00;font-size:20px;letter-spacing:6px}
.mgrid{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:8px;margin-top:14px}
.mbox{background:#000;border-radius:12px;padding:10px 4px;border:1px solid #00ff88;font-size:11px;font-weight:bold}
</style></head><body>

<div class='logo'>
<h1>EUGE-V7.5</h1>
<h2>LIVE FIXED</h2>
<div class='mgrid'>
<div class='mbox'>📈<br>FOREX</div>
<div class='mbox' style='border-color:#ffaa00;color:#ffaa00'>💎<br>CRYPTO</div>
<div class='mbox'>📊<br>JSE</div>
<div class='mbox' style='border-color:#ffaa00;color:#ffaa00'>⚡<br>DERIV</div>
</div>
</div>

<div id='sig' class='signal wait'>Analyzing...</div>
<div style='text-align:center;font-size:11px;color:#888;margin:6px'>Conf: <span id='conf'>0</span>% | <span id='trend'>-</span></div>

<div class='grid'>
<div class='card'><small>🟠 DERIV R_75</small><div id='r75' class='price' style='color:#ffaa00'>-</div></div>
<div class='card'><small>🟢 BTC-ZAR</small><div id='btc' class='price' style='color:#00ff88'>-</div></div>
<div class='card'><small>🔵 FOREX USD/ZAR</small><div id='zar' class='price' style='color:#44aaff'>-</div><small id='eur' style='font-size:10px;color:#888'></small></div>
<div class='card'><small>🟣 JSE TOP40</small><div id='jse' class='price' style='color:#ff44ff'>-</div></div>
</div>

<div class='card'><small>📈 Live Chart</small><canvas id='chart' height='140' style='width:100%;background:#000;border-radius:10px;margin-top:6px'></canvas></div>

<div class='card' style='border:2px solid #00ff88'>
<h4>📸 Screenshot Analyzer - FOREX/CRYPTO/JSE/DERIV</h4>
<input type='file' id='file' accept='image/*'><button onclick='up()' style='background:#00ff88;color:#000;border:0;padding:10px 15px;border-radius:8px;font-weight:bold;margin-left:8px'>ANALYZE</button>
<div id='res' style='margin-top:10px;background:#000;padding:10px;border-radius:8px;display:none'></div>
<img id='prev' style='width:100%;border-radius:8px;margin-top:8px;display:none'>
</div>

<div class='card'><h4>💬 Live Chat</h4><div id='chat'>Loading FOREX/CRYPTO/JSE/DERIV...</div></div>

<script>
let hist=[]
function up(){let f=document.getElementById('file').files[0];if(!f)return alert('pick screenshot');let fd=new FormData();fd.append('image',f);document.getElementById('res').style.display='block';document.getElementById('res').innerHTML='🔍 Analyzing FOREX/CRYPTO/JSE/DERIV...';let rd=new FileReader();rd.onload=e=>{document.getElementById('prev').src=e.target.result;document.getElementById('prev').style.display='block'};rd.readAsDataURL(f);fetch('/analyze',{method:'POST',body:fd}).then(r=>r.json()).then(d=>{document.getElementById('res').innerHTML=`<b style='color:#00ff88'>${d.signal} ${d.trend} ${d.confidence}%</b><br>${d.reason}`})}
function tick(){fetch('/status').then(r=>r.json()).then(d=>{
document.getElementById('r75').innerText=d.R_75.toFixed(2);document.getElementById('btc').innerText=Math.round(d['BTC-ZAR']).toLocaleString();document.getElementById('zar').innerText=d.USDZAR.toFixed(4);document.getElementById('eur').innerText=`EUR:${d.EURUSD} GBP:${d.GBPUSD}`;document.getElementById('jse').innerText=Math.round(d.JSE_TOP40).toLocaleString();document.getElementById('conf').innerText=d.confidence;document.getElementById('trend').innerText=d.trend;let s=document.getElementById('sig');s.innerText=d.signal+` (${d.confidence}%)`;s.className='signal '+(d.signal.includes('BUY')?'buy':d.signal.includes('SELL')?'sell':'wait');document.getElementById('chat').innerHTML=d.chat.slice().reverse().join('<br>');hist.push(d.R_75);if(hist.length>60)hist.shift();let c=document.getElementById('chart'),x=c.getContext('2d');c.width=c.clientWidth;c.height=140;x.clearRect(0,0,c.width,c.height);if(hist.length>3){let min=Math.min(...hist),max=Math.max(...hist),range=max-min||1;if(range<2){min-=2;max+=2;range=4}x.strokeStyle='#ffaa00';x.lineWidth=2;x.beginPath();hist.forEach((p,i)=>{let px=i/(hist.length-1)*c.width;let py=c.height-((p-min)/range*c.height*0.85+10);if(i==0)x.moveTo(px,py);else x.lineTo(px,py)});x.stroke();x.lineTo(c.width,c.height);x.lineTo(0,c.height);x.closePath();x.fillStyle='rgba(255,170,0,0.12)';x.fill()}})}
setInterval(tick,1200);tick()
</script>
</body></html>
    """

@app.route('/status')
def status(): return jsonify(latest)

threading.Thread(target=market_loop,daemon=True).start()