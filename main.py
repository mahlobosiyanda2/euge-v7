from flask import Flask, jsonify
import threading, time, requests, json, websocket, numpy as np
from datetime import datetime
import pytz
from collections import deque

app=Flask(__name__)
sa_tz=pytz.timezone('Africa/Johannesburg')

# Storage for analysis
r75_ticks = deque(maxlen=100)
r100_ticks = deque(maxlen=100)
btc_history = deque(maxlen=100)

latest={
 "BTC-ZAR":2035000,"BTC-USD":115500,"USDZAR":17.62,
 "R_75":0,"R_100":0,"EURUSD":1.08,
 "signal":"WAIT","confidence":0,"prediction":0,"rsi":50,
 "ema_fast":0,"ema_slow":0,
 "chat":[]
}

def get_ema(prices, period):
    if len(prices) < period: return prices[-1] if prices else 0
    return np.mean(list(prices)[-period:])

def get_rsi(prices, period=14):
    if len(prices) < period+1: return 50
    deltas = np.diff(list(prices)[-period-1:])
    gains = deltas[deltas>0].mean() if len(deltas[deltas>0])>0 else 0
    losses = -deltas[deltas<0].mean() if len(deltas[deltas<0])>0 else 0
    if losses == 0: return 100
    rs = gains/losses
    return 100 - (100/(1+rs))

def predict_next(prices, steps=10):
    if len(prices) < 10: return prices[-1] if prices else 0
    x = np.arange(len(prices))
    y = np.array(list(prices))
    # linear regression for prediction
    slope = np.polyfit(x[-20:], y[-20:], 1)[0]
    return y[-1] + slope*steps

def analyze():
    while True:
        try:
            if len(r75_ticks) > 20:
                prices = list(r75_ticks)
                fast = get_ema(prices, 7)
                slow = get_ema(prices, 21)
                rsi = get_rsi(prices)
                pred = predict_next(prices, 10)

                latest["ema_fast"]=fast
                latest["ema_slow"]=slow
                latest["rsi"]=rsi
                latest["prediction"]=pred

                # SCALPING LOGIC
                signal = "WAIT"
                conf = 0

                if fast > slow and rsi < 30: # Oversold + bullish cross
                    signal = "BUY 🔼"
                    conf = 85
                elif fast < slow and rsi > 70: # Overbought + bearish cross
                    signal = "SELL 🔽"
                    conf = 85
                elif fast > slow and rsi < 50:
                    signal = "BUY (weak) 🔼"
                    conf = 60
                elif fast < slow and rsi > 50:
                    signal = "SELL (weak) 🔽"
                    conf = 60
                elif abs(pred - prices[-1]) > prices[-1]*0.002:
                    if pred > prices[-1]:
                        signal = f"PREDICT UP 📈"
                        conf = 70
                    else:
                        signal = f"PREDICT DOWN 📉"
                        conf = 70

                latest["signal"]=signal
                latest["confidence"]=conf

                if conf >= 85:
                    latest["chat"].append(f"[{datetime.now(sa_tz).strftime('%H:%M:%S')}] 🚨 SIGNAL: {signal} R_75={prices[-1]:.2f} RSI={rsi:.1f}")
        except Exception as e:
            print(f"analyze err {e}")
        time.sleep(1)

def coingecko_watcher():
 while True:
  try:
   r=requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd,zar",timeout=10).json()
   latest["BTC-USD"]=r['bitcoin']['usd']
   latest["BTC-ZAR"]=r['bitcoin']['zar']
   latest["USDZAR"]=r['bitcoin']['zar']/r['bitcoin']['usd']
   btc_history.append(r['bitcoin']['zar'])
  except:
   pass
  time.sleep(3)

def deriv_watcher():
 while True:
  try:
   def on_message(ws, msg):
    d=json.loads(msg)
    if 'tick' in d:
     sym=d['tick']['symbol']
     price=float(d['tick']['quote'])
     if sym=="R_75":
      r75_ticks.append(price)
      latest["R_75"]=price
     if sym=="R_100":
      r100_ticks.append(price)
      latest["R_100"]=price
     latest["chat"].append(f"[{datetime.now(sa_tz).strftime('%H:%M:%S')}] {sym}: {price:.2f}")
     if len(latest["chat"])>40: latest["chat"].pop(0)
   def on_open(ws):
    ws.send(json.dumps({"ticks":"R_75"}))
    time.sleep(0.3)
    ws.send(json.dumps({"ticks":"R_100"}))
   ws=websocket.WebSocketApp("wss://ws.derivws.com/websockets/v3?app_id=1089",on_message=on_message,on_open=on_open)
   ws.run_forever(ping_interval=20)
  except:
   time.sleep(3)

@app.route('/')
def home():
    return """
<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'>
<style>
body{background:#0a0a0a;color:#fff;font-family:Arial;margin:0;padding:8px}
.card{background:#1a1a1a;border-radius:15px;padding:12px;margin:8px 0;border:1px solid #333}
.price{font-size:26px;font-weight:bold;color:#00ff88}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.signal{font-size:32px;font-weight:bold;text-align:center;padding:15px;border-radius:15px;margin:10px 0}
.buy{background:#00ff88;color:#000}
.sell{background:#ff4444;color:#fff}
.wait{background:#333;color:#888}
#chat{height:250px;overflow-y:auto;background:#000;border-radius:10px;padding:8px;font-size:11px}
.badge{background:#00ff88;color:#000;padding:3px 8px;border-radius:10px;font-size:11px}
.small{font-size:11px;color:#888}
</style></head><body>
<h3>EUGE-V7.5 SCALPER <span class='badge'>LIVE</span></h3>

<div id='sig' class='signal wait'>WAIT - Analyzing...</div>
<div class='card' style='text-align:center'>
<small>PREDICTION (next 10s)</small><div id='pred' class='price' style='color:#ffaa00'>-</div>
<small>Confidence: <span id='conf'>0</span>% | RSI: <span id='rsi'>0</span> | EMA7 vs EMA21</small>
</div>

<div class='grid'>
 <div class='card'><small>R_75</small><div id='r75' class='price' style='color:#ffaa00'>-</div><small id='ema' class='small'></small></div>
 <div class='card'><small>BTC-ZAR</small><div id='btczar' class='price'>-</div><small id='btcusd' class='small'></small></div>
</div>

<div class='card'><canvas id='chart' height='130' style='width:100%;background:#000;border-radius:10px'></canvas></div>
<div class='card'><h4>💬 AI Analysis Chat</h4><div id='chat'></div></div>

<script>
let prices=[]
function update(){
 fetch('/status').then(r=>r.json()).then(d=>{
  document.getElementById('r75').innerText=parseFloat(d['R_75']).toFixed(2)
  document.getElementById('btczar').innerText=Math.round(d['BTC-ZAR']).toLocaleString()
  document.getElementById('btcusd').innerText=`$${Math.round(d['BTC-USD']).toLocaleString()}`
  document.getElementById('pred').innerText=parseFloat(d['prediction']).toFixed(2)
  document.getElementById('conf').innerText=d['confidence']
  document.getElementById('rsi').innerText=parseFloat(d['rsi']).toFixed(1)
  document.getElementById('ema').innerText=`EMA7:${d['ema_fast'].toFixed(2)} EMA21:${d['ema_slow'].toFixed(2)}`

  let s=document.getElementById('sig')
  s.innerText=d['signal'] + ` (${d['confidence']}%)`
  s.className='signal '+(d['signal'].includes('BUY')?'buy':d['signal'].includes('SELL')?'sell':'wait')

  document.getElementById('chat').innerHTML=d['chat'].slice().reverse().join('<br>')
  prices.push(d['R_75'])
  if(prices.length>30) prices.shift()
  draw()
 })
}
function draw(){
 let c=document.getElementById('chart'),x=c.getContext('2d')
 c.width=c.clientWidth; c.height=130
 x.clearRect(0,0,c.width,c.height)
 if(prices.length<2) return
 let min=Math.min(...prices),max=Math.max(...prices),range=max-min||1
 x.strokeStyle='#ffaa00'; x.lineWidth=2; x.beginPath()
 prices.forEach((p,i)=>{
  let px=i/(prices.length-1)*c.width
  let py=c.height-((p-min)/range*c.height*0.8+10)
  if(i==0) x.moveTo(px,py); else x.lineTo(px,py)
 })
 x.stroke()
}
setInterval(update,800)
update()
</script>
</body></html>
    """

@app.route('/status')
def status():
    return jsonify(latest)

threading.Thread(target=coingecko_watcher,daemon=True).start()
threading.Thread(target=deriv_watcher,daemon=True).start()
threading.Thread(target=analyze,daemon=True).start()