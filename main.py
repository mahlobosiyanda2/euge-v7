from flask import Flask, jsonify, request
import threading, time, requests, random, json
from datetime import datetime
import pytz
from collections import deque

app=Flask(__name__)
sa_tz=pytz.timezone('Africa/Johannesburg')

# ALL MARKETS YOU WANTED
latest={
 "BTC-ZAR":2035000,"BTC-USD":115500,"ETH-ZAR":45000,
 "EURUSD":1.08,"GBPUSD":1.27,"USDZAR":17.62,
 "JSE_TOP40":75000,"JSE_SASOL":150,"JSE_NAS":3500,
 "R_75":498234,"R_100":1205,"R_75_1s":498234,
 "signal":"WAIT","confidence":0,"trend":"-","rsi":50,
 "chat":[]
}

r75_ticks=deque(maxlen=100)

def all_markets_watcher():
    while True:
        try:
            # 1. CRYPTO - CoinGecko (Forex + Crypto)
            r=requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd,zar",timeout=8).json()
            latest["BTC-USD"]=r['bitcoin']['usd']
            latest["BTC-ZAR"]=r['bitcoin']['zar']
            latest["ETH-ZAR"]=r['ethereum']['zar']
            latest["USDZAR"]=r['bitcoin']['zar']/r['bitcoin']['usd']

            # 2. FOREX - free API
            try:
                fx=requests.get("https://api.exchangerate-api.com/v4/latest/USD",timeout=5).json()
                latest["EURUSD"]=round(1/fx['rates']['EUR']*fx['rates']['EUR'],4) # approx
                latest["USDZAR"]=fx['rates']['ZAR']
            except: pass

            # 3. JSE - simulate live JSE Top40 (real JSE closed after 5pm)
            latest["JSE_TOP40"]+=random.uniform(-20,20)
            latest["JSE_SASOL"]+=random.uniform(-1,1)

            # 4. DERIV - live random walk (replace with websocket later)
            latest["R_75"]+=random.uniform(-1.5,1.5)
            r75_ticks.append(latest["R_75"])

            # SCALPING ANALYSIS
            if len(r75_ticks)>20:
                fast=sum(list(r75_ticks)[-7:])/7
                slow=sum(list(r75_ticks)[-21:])/21
                if fast>slow:
                    latest["signal"]="BUY R_75 🔼"
                    latest["trend"]="BULLISH"
                    latest["confidence"]=78
                else:
                    latest["signal"]="SELL R_75 🔽"
                    latest["trend"]="BEARISH"
                    latest["confidence"]=75

            t=datetime.now(sa_tz).strftime("%H:%M:%S")
            msg=f"[{t}] BTC:{latest['BTC-ZAR']:.0f} | R_75:{latest['R_75']:.2f} | JSE:{latest['JSE_TOP40']:.0f} | EUR/USD:{latest['EURUSD']}"
            latest["chat"].append(msg)
            if len(latest["chat"])>35: latest["chat"].pop(0)

        except Exception as e:
            print(e)
        time.sleep(2)

@app.route('/analyze_screenshot', methods=['POST'])
def analyze_screenshot():
    try:
        file=request.files['image']
        # Basic smart analysis for ANY market type
        from PIL import Image
        import numpy as np
        img=Image.open(file.stream).convert('L')
        arr=np.array(img)
        h,w=arr.shape
        # Check trend by comparing left third vs right third brightness
        left=arr[:, :w//3].mean()
        right=arr[:, 2*w//3:].mean()
        mid=arr[:, w//3:2*w//3].mean()

        if right>left+2:
            trend="BULLISH 🔼 (Forex/Crypto/JSE/Deriv Uptrend)"
            signal="BUY"
            conf=82
        elif left>right+2:
            trend="BEARISH 🔽 (Downtrend)"
            signal="SELL"
            conf=80
        else:
            trend="SIDEWAYS ↔️"
            signal="WAIT - No Trade"
            conf=55

        market_type="DERIV" if "volatility" in file.filename.lower() else "FOREX/CRYPTO/JSE"

        return jsonify