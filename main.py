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
latest={"R_75":0,"BTCZAR":0}
sa_tz=pytz.timezone('Africa/Johannesburg')
BTCZAR_ZONE=1287075

def send_wa(t):
 try: Client(TWILIO_SID,TWILIO_TOKEN).messages.create(from_=TWILIO_WA,to=MY_WA,body=t)
 except Exception as e: print(e)

def market_watcher():
 a=False
 while True:
  try:
   b=yf.download("BTC-ZAR",period="1d",interval="5m")['Close'].iloc[-1]
   latest["BTCZAR"]=b
   if b<BTCZAR_ZONE and not a:
    send_wa(f"🚨 BTC/ZAR BROKE 1287075 -> {b:,.0f} SELL");a=True
  except: pass
  time.sleep(60)

# --- THIS IS THE FIX YOU WERE MISSING ---
@app.route('/')
def home():
    return f"EUGE-V7 IS LIVE! 🚀 BTC: {latest['BTCZAR']:.0f} | Time: {datetime.now(sa_tz)}"

@app.route('/status')
def status():
    return latest

# Start bot in background
threading.Thread(target=market_watcher, daemon=True).start()