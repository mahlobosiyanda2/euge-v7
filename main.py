import yfinance as yf, websocket, json, threading, time, os
from flask import Flask
from twilio.rest import Client
from datetime import datetime
import pytz

app=Flask(__name__)
TWILIO_SID=os.getenv("TWILIO_SID")
TWILIO_TOKEN=os.getenv("TWILIO_TOKEN")
MY_WA="whatsapp:+27671455798"
TWILIO_WA="whatsapp:+14155238886"
sa_tz=pytz.timezone('Africa/Johannesburg')

# ALL YOUR MARKETS - NOT JUST BTC!
latest={
 "R_75": 0,
 "R_100": 0,
 "BTC-USD": 0,
 "BTC-ZAR": 0,
 "EURUSD": 0,
 "USDZAR": 0,
 "JSE-TOP40": 0
}

def send_wa(t):
 try: Client(TWILIO_SID,TWILIO_TOKEN).messages.create(from_=TWILIO_WA,to=MY_WA,body=t)
 except Exception as e: print(e)

def forex_crypto_watcher():
 while True:
  try:
   # Forex + Crypto + USDZAR
   btc = yf.download("BTC-USD", period="1d", interval="5m", progress=False)['Close'].iloc[-1]
   zar = yf.download("ZAR=X", period="1d", interval="5m", progress=False)['Close'].iloc[-1]
   eurusd = yf.download("EURUSD=X", period="1d", interval="5m", progress=False)['Close'].iloc[-1]

   latest["BTC-USD"]=float(btc)
   latest["USDZAR"]=float(zar)
   latest["BTC-ZAR"]=float(btc*zar)
   latest["EURUSD"]=float(eurusd)
   print(f"Updated: BTC {btc} | ZAR {zar}")
  except Exception as e:
   print(f"Forex error {e}")
  time.sleep(60)

def deriv_watcher():
 # Deriv R_75 / R_100 live via websocket
 while True:
  try:
   def on_message(ws, msg):
    d=json.loads(msg)
    if 'tick' in d:
     sym=d['tick']['symbol']
     price=d['tick']['quote']
     if sym in latest:
      latest[sym]=float(price)
   def on_open(ws):
    ws.send(json.dumps({"ticks":"R_75"}))
    ws.send(json.dumps({"ticks":"R_100"}))
   ws=websocket.WebSocketApp("wss://ws.derivws.com/websockets/v3?app_id=1089", on_message=on_message, on_open=on_open)
   ws.run_forever()
  except:
   time.sleep(5)

@app.route('/')
def home():
    return f"""
    <h2>EUGE-V7.5 IS LIVE! 🚀</h2>
    <b>Time:</b> {datetime.now(sa_tz)}<br><br>
    <b>Deriv:</b> R_75={latest['R_75']} | R_100={latest['R_100']}<br>
    <b>Crypto:</b> BTC-USD={latest['BTC-USD']:.2f} | BTC-ZAR={latest['BTC-ZAR']:.0f}<br>
    <b>Forex:</b> EURUSD={latest['EURUSD']} | USDZAR={latest['USDZAR']:.4f}<br>
    <b>Status:</b> ALL SYSTEMS LIVE!
    """

@app.route('/status')
def status():
    return latest

# Start BOTH watchers
threading.Thread(target=forex_crypto_watcher, daemon=True).start()
threading.Thread(target=deriv_watcher, daemon=True).start()