from flask import Flask, jsonify
import threading, time, requests
from datetime import datetime
import pytz

app=Flask(__name__)
sa_tz=pytz.timezone('Africa/Johannesburg')

latest={"BTC-ZAR":2035000,"BTC-USD":115500,"USDZAR":17.62,"R_75":0}
history=[]

def get_prices():
 while True:
  try:
   r=requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",timeout=10).json()
   btc=float(r['price'])
   r2=requests.get("https://api.exchangerate-api.com/v4/latest/USD",timeout=10).json()
   zar=r2['rates']['ZAR']
   latest["BTC-USD"]=btc
   latest["USDZAR"]=zar
   latest["BTC-ZAR"]=btc*zar
   history.append({"t":datetime.now(sa_tz).strftime("%H:%M:%S"),"p":btc*zar})
   if len(history)>50: history.pop(0)
  except: pass
  time.sleep(5)

@app.route('/')
def home():
    return """
<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'>
<style>
body{background:#0a0a0a;color:#fff;font-family:Arial;margin:0;padding:10px}
.card{background:#1a1a1a;border-radius:15px;padding:15px;margin:10px 0;border:1px solid #333}
.price{font-size:32px;font-weight:bold;color:#00ff88}
.live{color:#00ff88;animation:blink 1s infinite}
@keyframes blink{0%{opacity:1}50%{opacity:0.3}}
#chat{height:200px;overflow-y:auto;background:#000;border-radius:10px;padding:10px;font-size:13px}
.badge{background:#00ff88;color:#000;padding:3px 8px;border-radius:10px;font-size:12px}
</style></head><body>
<h2>EUGE-V7.5 <span class='badge'>LIVE</span> <span class='live'>● LIVE</span></h2>

<div class='card'>
<small>BTC-ZAR</small><div id='btczar' class='price'>2035000</div>
<small>BTC-USD: <span id='btcusd'>115500</span> | USDZAR: <span id='zar'>17.62</span></small>
</div>

<div class='card'>
<h3>📈 Live Chart</h3>
<canvas id='chart' height='120' style='width:100%;background:#000;border-radius:10px'></canvas>
</div>

<div class='card'>
<h3>💬 Live Price Chat</h3>
<div id='chat'></div>
</div>

<script>
let prices=[]
function update(){
 fetch('/status').then(r=>r.json()).then(d=>{
  document.getElementById('btczar').innerText=Math.round(d['BTC-ZAR']).toLocaleString()
  document.getElementById('btcusd').innerText=d['BTC-USD'].toFixed(2)
  document.getElementById('zar').innerText=d['USDZAR'].toFixed(4)
  let chat=document.getElementById('chat')
  let now=new Date().toLocaleTimeString()
  chat.innerHTML=`<div>[${now}] BTC-ZAR: ${Math.round(d['BTC-ZAR']).toLocaleString()} | ${d['BTC-USD'].toFixed(2)} USD</div>`+chat.innerHTML
  prices.push(d['BTC-ZAR'])
  if(prices.length>20) prices.shift()
  draw()
 })
}
function draw(){
 let c=document.getElementById('chart'),x=c.getContext('2d')
 c.width=c.clientWidth; c.height=120
 x.clearRect(0,0,c.width,c.height)
 x.strokeStyle='#00ff88'; x.lineWidth=2; x.beginPath()
 let min=Math.min(...prices),max=Math.max(...prices)
 prices.forEach((p,i)=>{
  let px=i/(prices.length-1)*c.width
  let py=c.height-((p-min)/(max-min||1)*c.height*0.8+10)
  if(i==0) x.moveTo(px,py); else x.lineTo(px,py)
 })
 x.stroke()
}
setInterval(update,2000)
update()
</script>
</body></html>
    """

@app.route('/status')
def status():
    return jsonify(latest)

threading.Thread(target=get_prices,daemon=True).start()