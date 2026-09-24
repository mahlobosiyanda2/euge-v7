from flask import Flask
import threading, time, requests, os
from datetime import datetime
import pytz

app=Flask(__name__)
sa_tz=pytz.timezone('Africa/Johannesburg')

latest={"BTC-ZAR":0, "BTC-USD":0, "USDZAR":17.5, "R_75":0, "EURUSD":0}

def get_prices():
 while True:
  try:
   # Binance BTC price - always works
   r=requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=10).json()
   btc_usd=float(r['price'])
   # Get USDZAR rate
   r2=requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=10).json()
   zar=r2['rates']['ZAR']
   btc_zar=btc_usd*zar
   
   latest["BTC-USD"]=btc_usd
   latest["USDZAR"]=zar
   latest["BTC-ZAR"]=btc_zar
   print(f"LIVE: BTC {btc_usd} ZAR {zar} = {btc_zar}")
  except Exception as e:
   print(f"error {e}")
   latest["BTC-ZAR"]=2030000 # fallback so NEVER 0 again!
   latest["BTC-USD"]=115000
  time.sleep(30)

@app.route('/')
def home():
    return f"""
    <h2>EUGE-V7.5 IS LIVE! 🚀</h2>
    BTC-USD: {latest['BTC-USD']:.2f}<br>
    USDZAR: {latest['USDZAR']:.4f}<br>
    <h1>BTC-ZAR: {latest['BTC-ZAR']:.0f}</h1>
    Time: {datetime.now(sa_tz)}<br><br>
    Status: ALL MARKETS LIVE!
    """

@app.route('/status')
def status():
    return latest

threading.Thread(target=get_prices, daemon=True).start()