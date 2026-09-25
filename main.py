from flask import Flask, jsonify, request, make_response
import random, requests
from datetime import datetime, timedelta
app = Flask(__name__)
VERSION="V53 15-30-45 PIPS"
REAL={"GBPUSD":1.3225,"EURJPY":180.106,"EURGBP":0.8607,"NZDCAD":0.80187,"AUDCAD":0.9937,"USDZAR":16.3654,"EURZAR":18.64130,"EURUSD":1.1385,"NZDJPY":89.51,"USDJPY":145.32,"GAUUSD":137.355,"BTC-USD":83905.15,"BTC-ZAR":1385000,"LTCUSD":98.45,"ETCUSD":22.34}
BASE={"GBPUSD":{"dec":5,"sup":1.32034,"res":1.32400,"name":"GBP/USD"},"EURJPY":{"dec":3,"sup":180.106,"res":181.632,"name":"EUR/JPY - SELL 180.10"},"EURGBP":{"dec":5,"sup":0.85979,"res":0.86092,"name":"EUR/GBP"},"NZDCAD":{"dec":5,"sup":0.79861,"res":0.80159,"name":"NZD/CAD"},"AUDCAD":{"dec":5,"sup":0.98990,"res":0.99372,"name":"AUD/CAD"},"USDZAR":{"dec":4,"sup":16.3614,"res":16.4387,"name":"USD/ZAR"},"EURZAR":{"dec":4,"sup":18.62758,"res":18.69405,"name":"EUR/ZAR"},"EURUSD":{"dec":5,"sup":1.13673,"res":1.13854,"name":"EUR/USD"},"NZDJPY":{"dec":3,"sup":89.451,"res":89.992,"name":"NZD/JPY"},"USDJPY":{"dec":3,"sup":144.5,"res":146.0,"name":"USD/JPY"},"GAUUSD":{"dec":3,"sup":133.156,"res":141.876,"name":"Gold gram - BUY 137.35"},"BTC-USD":{"dec":2,"sup":79000.00,"res":86076.39,"name":"BTC/USD - BUY 83905"},"BTC-ZAR":{"dec":2,"sup":1350000,"res":1420000,"name":"BTC/ZAR"},"LTCUSD":{"dec":2,"sup":95.0,"res":102.0,"name":"LTC/USD"},"ETCUSD":{"dec":2,"sup":21.0,"res":23.5,"name":"ETC/USD"}}
latest={"selected":"EURJPY","tf":"D1","price":180.106,"support":180.106,"resistance":181.632,"dec":3,"live":180.106,"chat":[],"name":"EUR/JPY - SELL 180.10","manual_bias":"AUTO"}
candles=[]
def get_live(m):
    try:
        if m in ["BTC-USD","LTCUSD","ETCUSD","BTC-ZAR"]:
            ids={"BTC-USD":"bitcoin","LTCUSD":"litecoin","ETCUSD":"ethereum-classic","BTC-ZAR":"bitcoin"}[m]
            r=requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd",timeout=4).json()
            p=float(list(r.values())[0]["usd"])
            if m=="BTC-ZAR":
                uz=requests.get("https://api.frankfurter.app/latest?from=USD&to=ZAR",timeout=4).json()["rates"]["ZAR"]; return p*float(uz)
            return p
        mp={"GBPUSD":("GBP","USD"),"EURJPY":("EUR","JPY"),"EURGBP":("EUR","GBP"),"NZDCAD":("NZD","CAD"),"AUDCAD":("AUD","CAD"),"USDZAR":("USD","ZAR"),"EURZAR":("EUR","ZAR"),"EURUSD":("EUR","USD"),"NZDJPY":("NZD","JPY"),"USDJPY":("USD","JPY")}
        if m in mp:
            frm,to=mp[m]; r=requests.get(f"https://api.frankfurter.app/latest?from={frm}&to={to}",timeout=5); return float(r.json()["rates"][to])
        if m=="GAUUSD":
            try:
                g=requests.get("https://api.coingecko.com/api/v3/simple/price?ids=pax-gold&vs_currencies=usd",timeout=4).json()
                return float(g["pax-gold"]["usd"])/31.1035
            except: return 137.355
    except: pass
    return REAL.get(m,180.106)

def build(m,tf,price):
    global candles; candles=[]; sup=BASE.get(m,{}).get("sup",price*0.97); res=BASE.get(m,{}).get("res",price*1.03); base=price
    for i in range(80):
        vol=(res-sup)*0.5 if dec:=BASE.get(m,{"dec":3})["dec"]>=4 else (res-sup)*0.4
        base += random.uniform(-vol*0.3,vol*0.3)
        if i>=77: base=price+random.uniform(-vol*0.1,vol*0.1)
        if i==79: base=price
        c=base; o=c+random.uniform(-vol*0.2,vol*0.2); h=max(o,c)+abs(random.uniform(0,vol*0.6)); l=min(o,c)-abs(random.uniform(0,vol*0.6))
        candles.append({"o":o,"h":h,"l":l,"c":c,"t":(datetime.now()-timedelta(days=80-i)).strftime("%d %b")})
    latest.update({"price":price,"live":price,"support":sup,"resistance":res,"selected":m,"tf":tf,"dec":BASE.get(m,{"dec":3})["dec"],"name":BASE.get(m,{}).get("name",m),"chat":[f"[{datetime.now().strftime('%H:%M:%S')}] {m} {tf} V53 15-30-45 READY"]})

build("EURJPY","D1",get_live("EURJPY"))

# 🔥 NEW TP LOGIC — 15p 30p 45p FIXED 🔥
def calc_tps(entry, dec, is_buy):
    # Pip value by market
    # dec 5 = 0.00010 = 10 pips per 0.001, dec 3 JPY = 0.010 = 1 pip, dec 2