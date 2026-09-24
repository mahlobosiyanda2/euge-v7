from flask import Flask, jsonify, request
import random, requests
from datetime import datetime
app = Flask(__name__)
REAL={"EURUSD":1.13667,"NZDCAD":0.80052,"GOLD H4":4258.02,"BTC-USD":84264.85,"EURGBP":0.86062,"GBPUSD":1.32119,"USDZAR":16.4192}
BASE={"EURUSD":{"dec":5,"sup":1.13454,"res":1.18354},"NZDCAD":{"dec":5,"sup":0.79536,"res":0.82641},"GOLD H4":{"dec":2,"sup":4249.34,"res":4367.34},"BTC-USD":{"dec":2,"sup":83000,"res":87123}}
latest={"selected":"EURUSD","price":1.13667,"support":1.13454,"resistance":1.18354,"dec":5,"live":1.13667,"chat":[]}
candles=[]
def get_live(m):
    try:
        if m=="BTC-USD":
            r=requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",timeout=4)
            return float(r.json()["bitcoin"]["usd"])
        if m=="GOLD H4":
            try:
                r=requests.get("https://api.gold-api.com/price/XAU",timeout=4)
                p=float(r.json().get("price",0))
                if 2000<p<6000: return p
            except: pass
            return 4258.02
        if m=="EURUSD":
            r=requests.get("https://api.frankfurter.app/latest?from=EUR&to=USD",timeout=4)
            rate=float(r.json()["rates"]["USD"])
            if 1.0<rate<1.3: return rate
            return 1.13667
        if m=="NZDCAD":
            r=requests.get("https://api.frankfurter.app/latest?from=NZD&to=CAD",timeout=4)
            return float(r.json()["rates"]["CAD"])
    except: pass
    return REAL.get(m,1.13667)
def build(m,price):
    global candles
    candles=[]
    sup=BASE.get(m,{}).get("sup",price*0.997)
    res=BASE.get(m,{}).get("res",price*1.02)
    for i in range(70):
        if m=="EURUSD":
            if i<20: p=1.181+random.uniform(-0.005,0.005)
            elif i<50: p=1.136+random.uniform(-0.008,0.02)
            else: p=price+random.uniform(-0.003,0.003)
        else: p=price+random.uniform(-(res-sup)*0.15,(res-sup)*0.15)
        o=p+random.uniform(-0.001,0.001)
        candles.append({"o":o,"h":max(o,p)+(res-sup)*0.04,"l":min(o,p)-(res-sup)*0.04,"c":p,"t":datetime.now().strftime("%H:%M")})
    candles[-1]["c"]=price
    latest["price"]=price;latest["live"]=price;latest["support"]=sup;latest["resistance"]=res;latest["selected"]=m;latest["dec"]=BASE.get(m,{"dec":5})["dec"]
    latest["chat"]=[] 
build("EURUSD",get_live("EURUSD"))
@app.route('/select',methods=['POST'])
def sel():
   