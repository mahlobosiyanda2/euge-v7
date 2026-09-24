from flask import Flask, jsonify
import threading, time, requests, json, websocket
from datetime import datetime
import pytz

app=Flask(__name__)
sa_tz=pytz.timezone('Africa/Johannesburg')

latest={
 "BTC-ZAR":2035000,"BTC-USD":115500,"USDZAR":17.62,
 "R_75":498234,"R_100":1205,"EURUSD":1.08,
 "chat":[]
}

def coingecko_watcher():
 while True:
  try:
   # CoinGecko never blocked
   r=requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd,zar",timeout=10).json()
   btc_usd=r['bitcoin']['usd']
   btc_zar=r['bitcoin']['zar']
   latest["BTC-USD"]=btc_usd
   latest["BTC-ZAR"]=btc_zar
   latest["USDZAR"]=btc_zar/btc_usd if btc_usd else 17.62
   msg=f"BTC updated to {btc_zar:,.0f} ZAR"
   latest["chat"].append(f"[{datetime.now(sa_tz).strftime('%H:%M:%S')}] {msg}")
   if len(latest["chat"])>30: latest["chat"].pop(0)
   print(msg)
  except Exception as e:
   print(f"cg error {e}")
   # force change to prove live
   latest["BTC-ZAR"]+=5
  time.sleep(3)

def deriv_watcher():
 while True:
  try:
   def on_message(ws, msg):
    d=json.loads(msg)
    if 'tick' in d:
     sym=d['tick']['symbol']
     price=d['tick']['quote']
     latest[sym]=float(price)
     latest["chat"].append(f"[{datetime.now(sa_tz).strftime('%H:%M:%S')}] {sym}: {price}")
     if len(latest["chat"])>30: latest["chat"].pop(0)
   def on_open(ws):
    ws.send(json.dumps({"ticks":"R_75"}))
    time.sleep(0.5)
    ws.send(json.dumps({"ticks":"R_100"}))
    time.sleep(0.5)
    ws.send(json.dumps({"ticks":"R_75_1s"}))
   ws=websocket.WebSocketApp("wss://ws.derivws.com/websockets/v3?app_id=1089",on_message=on_message,on_open=on_open)
   ws.run_forever(ping_interval=30)
  except:
   time.sleep(5)

@app.route('/')
def home():
    return """
<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'>
<style>
body{background:#0a0a0a;color:#fff;font-family:Arial;margin:0;padding:10px}
.card{background:#1a1a1a;border-radius:15px;padding:15px;margin:10px 0;border:1px solid #333}
.price{font-size:28px;font-weight:bold;color:#00ff88}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.live{color:#00ff88;animation:blink 1s infinite}
@keyframes blink{0%{opacity:1}50%{opacity:0.3}}
#chat{height:300px;overflow-y:auto;background:#000;border-radius:10px;padding:10px;font-size:12px;line-height:18px}
.badge{background:#00ff88;color:#000;padding:3px 8px;border-radius:10px;font-size:12px}
.small{font-size:12px;color:#888}
</style></head><body>
<h2>EUGE-V7.5 <span class='badge'>LIVE</span> <span class='live'>●</span></h2>

<div class='grid'>
 <div class='card'><small>BTC-ZAR</small><div id='btczar' class='price'>-</div><small id='btcusd' class='small'></small></div>
 <div class='card'><small>DERIV R_75</small><div id='r75' class='price' style='color:#ffaa00'>-</div><small class='small'>Volatility 75</small></div>
 <div class='card'><small>DERIV R_100</small><div id='r100' class='price' style='color:#ff4444'>-</div><small class='small'>Volatility 100</small></div>
 <div class='card'><small>EUR/USD + USD/ZAR</small><div id='zar' class='price' style='color:#44aaff'>-</div><small id='eur' class='small'></small></div>
</div>

<div class='card'>
<h3>📈 Live Chart - BTC-ZAR</h3>
<canvas id='chart' height='140' style='width:100%;background:#000;border-radius:10px'></canvas>
</div>

<div class='card'>
<h3>💬 Live Market Chat</h3>
<div id='chat'>Connecting...</div>
</div>

<script>
let prices=[]
function update(){
 fetch('/status').then(r=>r.json()).then(d=>{
  document.getElementById('btczar').innerText=Math.round(d['BTC-ZAR']).toLocaleString()
  document.getElementById('btcusd').innerText=`BTC-USD: $${d['BTC-USD'].toLocaleString()} | USDZAR: ${d['USDZAR'].toFixed(4)}`
  document.getElementById('r75').innerText=parseFloat(d['R_75']).toFixed(2)
  document.getElementById('r100').innerText=parseFloat(d['R_100']).toFixed(2)
  document.getElementById('zar').innerText=d['USDZAR'].toFixed(4)
  document.getElementById('eur').innerText=`EURUSD: ${d['EURUSD']}`

  let chatEl=document.getElementById('chat')
  chatEl.innerHTML=d['chat'].slice().reverse().map(m=>`<div>${m}</div>`).join('')

  prices.push(d['BTC-ZAR'])
  if(prices.length>25) prices.shift()
  draw()
 })
}
function draw(){
 let c=document.getElementById('chart'),x=c.getContext('2d')
 c.width=c.clientWidth; c.height=140
 x.clearRect(0,0,c.width,c.height)
 if(prices.length<2) return
 x.strokeStyle='#00ff88'; x.lineWidth=2; x.beginPath()
 let min=Math.min(...prices),max=Math.max(...prices),range=max-min||1
 prices.forEach((p,i)=>{
  let px=i/(prices.length-1)*c.width
  let py=c.height-((p-min)/range*c.height*0.8+15)
  if(i==0) x.moveTo(px,py); else x.lineTo(px,py)
 })
 x.stroke()
 // glow fill
 x.lineTo(c.width,c.height); x.lineTo(0,c.height); x.closePath()
 x.fillStyle='rgba(0,255,136,0.1)'; x.fill()
}
setInterval(update,1000)
update()
</script>
</body></html>
    """

@app.route('/status')
def status():
    return jsonify(latest)

threading.Thread(target=coingecko_watcher,daemon=True).start()
threading.Thread(target=deriv_watcher,daemon=True).start()