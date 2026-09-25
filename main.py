from flask import Flask, jsonify, request, make_response
import random, requests
from datetime import datetime, timedelta
app = Flask(__name__)
VERSION="V52 GAUUSD GRAM FIXED"
REAL={"GBPUSD":1.3225,"EURJPY":179.89,"EURGBP":0.8607,"NZDCAD":0.80187,"AUDCAD":0.9937,"USDZAR":16.3654,"EURZAR":18.64130,"EURUSD":1.1385,"NZDJPY":89.51,"USDJPY":145.32,"GAUUSD":137.355,"BTC-USD":84264.85,"BTC-ZAR":1385000,"LTCUSD":98.45,"ETCUSD":22.34}
BASE={"GBPUSD":{"dec":5,"sup":1.32034,"res":1.32400,"name":"GBP/USD"},"EURJPY":{"dec":3,"sup":179.811,"res":180.774,"name":"EUR/JPY"},"EURGBP":{"dec":5,"sup":0.85979,"res":0.86092,"name":"EUR/GBP"},"NZDCAD":{"dec":5,"sup":0.79861,"res":0.80159,"name":"NZD/CAD - SELL"},"AUDCAD":{"dec":5,"sup":0.98990,"res":0.99372,"name":"AUD/CAD"},"USDZAR":{"dec":4,"sup":16.3614,"res":16.4387,"name":"USD/ZAR"},"EURZAR":{"dec":4,"sup":18.62758,"res":18.69405,"name":"EUR/ZAR - BUY BOTTOM"},"EURUSD":{"dec":5,"sup":1.13673,"res":1.13854,"name":"EUR/USD"},"NZDJPY":{"dec":3,"sup":89.451,"res":89.992,"name":"NZD/JPY"},"USDJPY":{"dec":3,"sup":144.5,"res":146.0,"name":"USD/JPY"},"GAUUSD":{"dec":3,"sup":133.156,"res":141.876,"name":"Gold gram vs USD - 137.35 BUY"},"BTC-USD":{"dec":2,"sup":83000.00,"res":87140.42,"name":"BTC/USD"},"BTC-ZAR":{"dec":2,"sup":1350000,"res":1420000,"name":"BTC/ZAR"},"LTCUSD":{"dec":2,"sup":95.0,"res":102.0,"name":"LTC/USD"},"ETCUSD":{"dec":2,"sup":21.0,"res":23.5,"name":"ETC/USD"}}
latest={"selected":"GAUUSD","tf":"D1","price":137.355,"support":133.156,"resistance":141.876,"dec":3,"live":137.355,"chat":[],"name":"Gold gram vs USD - 137.35 BUY","manual_bias":"AUTO"}
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
            # Gold gram = Gold ounce / 31.1035, ounce ~ 4250 => gram ~136.6
            try:
                r=requests.get("https://api.frankfurter.app/latest?from=XAU&to=USD",timeout=4)
                if r.status_code==200:
                    # Frankfurter doesn't support XAU, fallback to coingecko
                    pass
            except: pass
            # Use live gold ounce /31.1035
            try:
                g=requests.get("https://api.coingecko.com/api/v3/simple/price?ids=pax-gold&vs_currencies=usd",timeout=4).json()
                ounce=float(g["pax-gold"]["usd"])
                return ounce/31.1035
            except:
                return 137.355
    except: pass
    return REAL.get(m,137.355)
def build(m,tf,price):
    global candles; candles=[]; sup=BASE.get(m,{}).get("sup",price*0.97); res=BASE.get(m,{}).get("res",price*1.03); base=price+ (20 if m=="EURZAR" else 42 if m=="GAUUSD" else 0.027)
    for i in range(80):
        vol=(res-sup)*0.5 if m in ["EURZAR","GAUUSD"] else (res-sup)*0.35
        if m in ["EURZAR","NZDCAD","EURJPY","GAUUSD"]:
            base -= vol*0.12 + random.uniform(-vol*0.1,vol*0.05) if i<65 else random.uniform(-vol*0.25,vol*0.25)
        else:
            base += random.uniform(-vol*0.3,vol*0.3)
        c=base+random.uniform(-vol*0.2,vol*0.2)
        if i>=77: c=price+random.uniform(-vol*0.1,vol*0.1)
        if i==79: c=price
        o=c+random.uniform(-