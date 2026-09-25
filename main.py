from flask import Flask, jsonify, request, make_response
import random, requests
from datetime import datetime, timedelta
app = Flask(__name__)
VERSION="V46 CANDLESTICK CHART BACK"
REAL={"BTC-USD":84264.85,"USDZAR":16.4192,"EURUSD":1.13667,"NZDCAD":0.80014,"GOLD H4":4258.02,"AUDUSD":0.65234,"EURGBP":0.86062,"GBPUSD":1.32119}
BASE={"BTC-USD":{"dec":2,"sup":83000.00,"res":87140.42,"name":"Bitcoin vs US Dollar"},"USDZAR":{"dec":4,"sup":16.2000,"res":16.6000,"name":"US Dollar vs South African Rand"},"EURUSD":{"dec":5,"sup":1.13454,"res":1.13854,"name":"Euro vs US Dollar"},"NZDCAD":{"dec":5,"sup":0.79971,"res":0.80200,"name":"New Zealand Dollar vs Canadian Dollar"},"GOLD H4":{"dec":2,"sup":4249.34,"res":4267.34,"name":"Gold Spot"},"AUDUSD":{"dec":5,"sup":0.64800,"res":0.65800,"name":"Australian Dollar vs US Dollar"},"EURGBP":{"dec":5,"sup":0.85734,"res":0.86094,"name":"Euro vs Great Britain Pound"},"GBPUSD":{"dec":5,"sup":1.31373,"res":1.32400,"name":"British Pound vs US Dollar"}}
latest={"selected":"BTC-USD","tf":"D1","price":84264.85,"support":83000.00,"resistance":87140.42,"dec":2,"live":84264.85,"chat":[],"name":"Bitcoin vs US Dollar"}
candles=[]
def get_live(m):
    try:
        if m=="BTC-USD":
            r=requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",timeout=4)
            return float(r.json()["bitcoin"]["usd"])
        mp={"EURGBP":("EUR","GBP"),"GBPUSD":("GBP","USD"),"NZDCAD":("NZD","CAD"),"AUDCAD":("AUD","CAD"),"AUDUSD":("AUD","USD"),"USDZAR":("USD","ZAR"),"EURUSD":("EUR","USD")}
        if m in mp:
            frm,to=mp[m]; r=requests.get(f"https://api.frankfurter.app/latest?from={frm}&to={to}",timeout=4); return float(r.json()["rates"][to])
    except: pass
    return REAL.get(m,84264.85)
def fetch_binance(m,tf):
    try:
        if m=="BTC-USD":
            im={"D1":"1d","H4":"4h","H1":"1h","M15":"15m","M30":"30m"}.get(tf,"1d")
            r=requests.get(f"https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval={im}&limit=80",timeout=5)
            data=r.json(); cs=[]
            for k in data:
                o=float(k[1]); h=float(k[2]); l=float(k[3]); c=float(k[4])
                ts=int(k[0])/1000; t=datetime.fromtimestamp(ts).strftime("%d %b %H:%M" if tf!="D1" else "%d %b")
                cs.append({"o":o,"h":h,"l":l,"c":c,"t":t})
            return cs
    except: pass
    return None
def build(m,tf,price):
    global candles
    real=fetch_binance(m,tf)
    if real and len(real)>10:
        candles=real
        candles[-1]["c"]=price
        candles[-1]["h"]=max(candles[-1]["h"],price)
        candles[-1]["l"]=min(candles[-1]["l"],price)
    else:
        candles=[]; vol=price*0.008 if m=="BTC-USD" else price*0.006
        base=price
        for i in range(80):
            # trending walk to match real
            change=random.uniform(-vol*0.6,vol*0.8)
            base+=change*0.2
            c=base+random.uniform(-vol*0.3,vol*0.3)
            if i==79: c=price
            o=c+random.uniform(-vol*0.2,vol*0.2)
            h=max(o,c)+abs(random.uniform(0,vol*0.5))
            l=min(o,c)-abs(random.uniform(0,vol*0.5))
            t=(datetime.now()-timedelta(days=80-i)).strftime("%d %b") if tf=="D1" else (datetime.now()-timedelta(hours=(80-i)*4)).strftime("%H:%M")
            candles.append({"o":o,"h":h,"l":l,"c":c,"t":t})
    latest.update({"price":price,"live":price,"support":BASE.get(m,{}).get("sup",price*0.98),"resistance":BASE.get(m,{}).get("res",price*1.02),"selected":m,"tf":tf,"dec":BASE.get(m,{"dec":2})["dec"],"name":BASE.get(m,{}).get("name",m),"chat":[f"[{datetime.now().strftime('%H:%M:%S')}] {m} {tf} CANDLESTICK CHART BUYILE! TP1 250% | TP2 385% | TP3 580%"]})
build("BTC-USD","D1",get_live("BTC-USD"))
def calc_tps(e,s,dec):
    d=abs(e-s);
    if d==0: d=e*0.01
    tp1=e+d*2.5; tp2=e+d*3.85; tp3=e+d*5.8
    pf=10000 if dec>=4 else 100
    return tp1,tp2,tp3,d,d*pf,(tp1-e)*pf,(tp2-e)*pf,(tp3-e)*pf
@app.route('/select',methods=['POST'])
def sel():
    d=request.json; m=d.get('market','BTC-USD'); tf=d.get('timeframe','D1'); p=get_live(m); build(m,tf,p)
    r=make_response(jsonify({"ok":True})); r.headers['Cache-Control']='no-store'; return r
@app.route('/candles')
def cnd():
    live=get_live(latest["selected"])
    if candles: candles[-1]["c"]=live; candles[-1]["h"]=max(candles[-1]["h"],live); candles[-1]["l"]=min(candles[-1]["l"],live)
    latest["price"]=live
    tp1,tp2,tp3,dist,sl_p,tp1_p,tp2_p,tp3_p=calc_tps(live,latest["support"],latest["dec"])
    sa=datetime.utcnow()+timedelta(hours=2)
    latest["chat"].append(f"[{sa.strftime('%H:%M:%S')}] {latest['selected']} {live:.{latest['dec']}f} | SL {sl_p:.0f}p | TP1 250% {tp1_p:.0f}p | TP2 385% {tp2_p:.0f}p | TP3 580% {tp3_p:.0f}p")
    if len(latest["chat"])>20: latest["chat"].pop(0)
    r=make_response(jsonify({"candles":candles,"price":live,"support":latest["support"],"resistance":latest["resistance"],"entry":live,"sl":latest["support"],"tp1":tp1,"tp2":tp2,"tp3":tp3,"sl_pips":sl_p,"tp1_pips":tp1_p,"tp2_pips":tp2_p,"tp3_pips":tp3_p,"signal":f"BUY {latest['selected']} TP1 250% {tp1_p:.0f}pips TP2 385% {tp2_p:.0f}pips TP3 580% {tp3_p:.0f}pips","mode":f"{VERSION}","chat":latest["chat"],"selected":latest["selected"],"timeframe":latest["tf"],"dec":latest["dec"],"name":latest["name"],"version":VERSION}))
    r.headers['Cache-Control']='no-store'; return r
@app.route('/analyze',methods=['POST'])
def ana():
    m=request.form.get('selected_market','BTC-USD'); p=get_live(m); sup=BASE.get(m,{}).get("sup",p*0.98); dec=BASE.get(m,{"dec":2})["dec"]
    tp1,tp2,tp3,dist,sl_p,tp1_p,tp2_p,tp3_p=calc_tps(p,sup,dec); fmt=f"{{:.{dec}f}}"
    analysis=f"""{VERSION}
✅ {m} LIVE {fmt.format(p)}
SL 100% = {fmt.format(sup)} = {sl_p:.0f} pips
TP1 250% = {fmt.format(tp1)} = {tp1_p:.0f} pips
TP2 385% = {fmt.format(tp2)} = {tp2_p:.0f} pips
TP3 580% = {fmt.format(tp3)} = {tp3_p:.0f} pips
CHART: CANDLESTICK BUYILE!
"""
    r=make_response(jsonify({"analysis":analysis})); r.headers['Cache-Control']='no-store'; return r
@app.route('/')
def home():
    html=f"""<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'><meta http-equiv='Cache-Control' content='no-cache'><title>{VERSION}</title>
<style>
body{{background:#000;color:#fff;font-family:Arial;margin:0;padding:6px}}
.card{{background:#111;border-radius:14px;padding:10