from flask import Flask, jsonify, request, make_response
import random, requests
from datetime import datetime, timedelta
app = Flask(__name__)
VERSION="V51 CHOOSE YOUR TEST"
REAL={"GBPUSD":1.3225,"EURJPY":179.89,"EURGBP":0.8607,"NZDCAD":0.80187,"AUDCAD":0.9937,"USDZAR":16.3654,"EURZAR":18.64130,"EURUSD":1.1385,"NZDJPY":89.51,"USDJPY":145.32,"GAUUSD":4258.02,"BTC-USD":84264.85,"BTC-ZAR":1385000,"LTCUSD":98.45,"ETCUSD":22.34}
BASE={"GBPUSD":{"dec":5,"sup":1.32034,"res":1.32400,"name":"GBP/USD"},"EURJPY":{"dec":3,"sup":179.811,"res":180.774,"name":"EUR/JPY"},"EURGBP":{"dec":5,"sup":0.85979,"res":0.86092,"name":"EUR/GBP"},"NZDCAD":{"dec":5,"sup":0.79861,"res":0.80159,"name":"NZD/CAD"},"AUDCAD":{"dec":5,"sup":0.98990,"res":0.99372,"name":"AUD/CAD"},"USDZAR":{"dec":4,"sup":16.3614,"res":16.4387,"name":"USD/ZAR"},"EURZAR":{"dec":4,"sup":18.62758,"res":18.69405,"name":"EUR/ZAR - YOUR CHOICE"},"EURUSD":{"dec":5,"sup":1.13673,"res":1.13854,"name":"EUR/USD"},"NZDJPY":{"dec":3,"sup":89.451,"res":89.992,"name":"NZD/JPY"},"USDJPY":{"dec":3,"sup":144.5,"res":146.0,"name":"USD/JPY"},"GAUUSD":{"dec":2,"sup":4249.34,"res":4267.34,"name":"GOLD/USD"},"BTC-USD":{"dec":2,"sup":83000.00,"res":87140.42,"name":"BTC/USD"},"BTC-ZAR":{"dec":2,"sup":1350000,"res":1420000,"name":"BTC/ZAR"},"LTCUSD":{"dec":2,"sup":95.0,"res":102.0,"name":"LTC/USD"},"ETCUSD":{"dec":2,"sup":21.0,"res":23.5,"name":"ETC/USD"}}
latest={"selected":"EURZAR","tf":"D1","price":18.64130,"support":18.62758,"resistance":18.69405,"dec":4,"live":18.64130,"chat":[],"name":"EUR/ZAR - YOUR CHOICE","manual_bias":"AUTO"}
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
    except: pass
    return REAL.get(m,18.64130)
def build(m,tf,price):
    global candles; candles=[]; sup=BASE.get(m,{}).get("sup",price*0.99); res=BASE.get(m,{}).get("res",price*1.01); base=price+ (2.0 if m=="EURZAR" else 0.027)
    for i in range(80):
        vol=(res-sup)*0.5 if m=="EURZAR" else (res-sup)*0.35
        if m in ["EURZAR","NZDCAD","EURJPY"]: base -= vol*0.12 + random.uniform(-vol*0.1,vol*0.05) if i<65 else random.uniform(-vol*0.2,vol*0.2)
        else: base += random.uniform(-vol*0.3,vol*0.3)
        c=base+random.uniform(-vol*0.2,vol*0.2)
        if i>=77: c=price+random.uniform(-vol*0.1,vol*0.1)
        if i==79: c=price
        o=c+random.uniform(-vol*0.2,vol*0.2); h=max(o,c)+abs(random.uniform(0,vol*0.6)); l=min(o,c)-abs(random.uniform(0,vol*0.6))
        candles.append({"o":o,"h":h,"l":l,"c":c,"t":(datetime.now()-timedelta(days=80-i)).strftime("%d %b")})
    latest.update({"price":price,"live":price,"support":sup,"resistance":res,"selected":m,"tf":tf,"dec":BASE.get(m,{"dec":4})["dec"],"name":BASE.get(m,{}).get("name",m),"chat":[f"[{datetime.now().strftime('%H:%M:%S')}] {m} {tf} V51 YOUR CHOICE MODE"]})
build("EURZAR","D1",get_live("EURZAR"))
def calc_tps(e,s,dec,is_buy):
    d=abs(e-s);
    if d==0: d=e*0.008
    if is_buy: tp1=e+d*2.5; tp2=e+d*3.85; tp3=e+d*5.8; sl=s
    else: sl=latest["resistance"] if latest["resistance"]>e else e+d; tp1=e-d*2.5; tp2=e-d*3.85; tp3=e-d*5.8
    pf=10000 if dec>=4 else 100
    if dec==3: pf=100
    return tp1,tp2,tp3,sl,d,d*pf,abs(tp1-e)*pf,abs(tp2-e)*pf,abs(tp3-e)*pf
def get_pro_analysis(m,p,sup,res,manual):
    if manual!="AUTO":
        bias=manual; conf=100
        reason=f"MANUAL TEST MODE: You chose {bias} for {m} to test Euge TP calculation. Live {p}, Sup {sup}, Res {res}"
        return bias,conf,reason
    if m=="EURZAR": return "BUY",68,f"EURZAR at triple bottom {sup}, price {p} holding support 3x, bullish reversal if breaks {res}"
    elif m=="NZDCAD": return "SELL",78,f"NZDCAD H4 downtrend, double top 0.829, breakdown -275p, bear flag 0.79987-0.80222"
    elif m=="GBPUSD": return "BUY",72,f"GBPUSD uptrend HH-HL"
    else: return "SELL",65,f"{m} bearish below {res}"

@app.route('/select',methods=['POST'])
def sel():
    d=request.json; m=d.get('market','EURZAR'); tf=d.get('timeframe','D1'); manual=d.get('bias','AUTO'); latest["manual_bias"]=manual
    p=get_live(m); build(m,tf,p)
    r=make_response(jsonify({"ok":True})); r.headers['Cache-Control']='no-store'; return r
@app.route('/candles')
def cnd():
    live=get_live(latest["selected"])
    if candles: candles[-1]["c"]=live
    latest["price"]=live
    bias,conf,_=get_pro_analysis(latest["selected"],live,latest["support"],latest["resistance"],latest["manual_bias"])
    is_buy=bias=="BUY"
    tp1,tp2,tp3,sl,dist,sl_p,tp1_p,tp2_p,tp3_p=calc_tps(live,latest["support"],latest["dec"],is_buy)
    r=make_response(jsonify({"candles":candles,"price":live,"support":latest["support"],"resistance":latest["resistance"],"entry":live,"sl":sl,"tp1":tp1,"tp2":tp2,"tp3":tp3,"sl_pips":sl_p,"tp1_pips":tp1_p,"tp2_pips":tp2_p,"tp3_pips":tp3_p,"signal":f"{bias} {latest['selected']} {conf}% | SL {sl_p:.0f}p TP1 {tp1_p:.0f}p TP2 {tp2_p:.0f}p TP3 {tp3_p:.0f}p","mode":f"{VERSION} {bias} {conf}% {latest['manual_bias']}","chat":latest["chat"],"selected":latest["selected"],"timeframe":latest["tf"],"dec":latest["dec"],"name":latest["name"],"version":VERSION,"bias":bias,"conf":conf,"manual":latest["manual_bias"]}))
    r.headers['Cache-Control']='no-store'; return r
@app.route('/analyze',methods=['POST'])
def ana():
    m=request.form.get('selected_market','EURZAR'); p=get_live(m); sup=BASE.get(m,{}).get("sup",p*0.99); res=BASE.get(m,{}).get("res",p*1.01); dec=BASE.get(m,{"dec":4})["dec"]; manual=request.form.get('manual_bias','AUTO')
    bias,conf,reason=get_pro_analysis(m,p,sup,res,manual)
    is_buy=bias=="BUY"
    tp1,tp2,tp3,sl,dist,sl_p,tp1_p,tp2_p,tp3_p=calc_tps(p,sup,dec,is_buy)
    fmt=f"{{:.{dec}f}}"
    analysis=f"""🔥 {VERSION} - YOUR CHOICE TEST 🔥
MARKET: {m} | LIVE: {fmt.format(p)} | SUP: {fmt.format(sup)} | RES: {fmt.format(res)} | MODE: {manual}
SIGNAL: {bias} {conf}%
REASON: {reason}
TRADE: ENTRY {fmt.format(p)} SL {fmt.format(sl)} {sl_p:.0f}p TP1 {fmt.format(tp1)} {tp1_p:.0f}p 250% TP2 {fmt.format(tp2)} {tp2_p:.0f}p 385% TP3 {fmt.format(tp3)} {tp3_p:.0f}p 580%
V51 - YOU CHOOSE!
"""
    r=make_response(jsonify({"analysis":analysis,"bias":bias})); r.headers['Cache-Control']='no-store'; return r
@app.route('/')
def home():
    html=f"""<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'><title>{VERSION}</title>
<style>
body{{background:#000;color:#fff;font-family:Arial;margin:0;padding:6px}}.card{{background:#111;border-radius:14px;padding:10px;margin:8px 0;border:1px solid #222}}
.signal{{padding:16px;border-radius:14px;text-align:center;font-weight:bold;font-size:16px}}.signal.sell{{background:#ff4444;color:#fff}}.signal.buy{{background:#00ff88;color:#000}}.signal.wait{{background:#ffaa00;color:#000}}
#chat{{height:200px;overflow-y:auto;background:#000;border-radius:10px;padding:10px;font-size:11px;color:#00ff88;border:2px solid #00ff88}}
.logo{{background:#000;border:2px solid #00ff88;border-radius:16px;padding:12px;text-align:center}}
.mgrid{{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:10px}}.mbox{{background:#111;border-radius:10px;padding:10px;border:2px solid #333;font-size:12px;font-weight:bold;cursor:pointer;text-align:center}}.mbox.active{{border-color:#00ff88;background:#002200}}
.trow{{display:flex;gap:6px;justify-content:center;margin-top:10px;flex-wrap:wrap}}.tbtn{{background:#111;color:#888;border:1px solid #333;padding:8px 14px;border-radius:20px;font-size:12px;font-weight:bold;cursor:pointer}}.tbtn.active{{background:#00ff88;color:#000}}
.brow{{display:flex;gap:6px;justify-content:center;margin-top:10px}}.bbtn{{padding:10px 16px;border-radius:10px;font-weight:bold;border:2px solid #333;cursor:pointer}}.bbtn.active{{border-color:#00ff88;background:#002200;color:#00ff88}}
.tps{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:10px}}.tpbox{{background:#111;border-radius:12px;padding:10px;text-align:center;border:2px solid #333;min-height:80px}}
#picker{{display:none;background:#111;border:2px solid #00ff88;border-radius:12px;padding:12px;margin:8px 0}}.pbtn{{background:#222;color:#fff;border:1px solid #444;padding:10px 14px;border-radius:8px;margin:4px}}
canvas{{display:block;width:100%;background:#fff;border-radius:12px;margin-top:10px;border:2px solid #00ff88}}
</style></head><body>
<div class='logo'><h1>EUGE ROBOT <span style='background:#00ff88;color:#000;padding:4px 8px;border-radius:6px;font-size:10px'>{VERSION}</span></h1><div style='color:#00ff88;font-weight:bold'>✅ YOU CHOOSE YOUR TEST - MANUAL MODE!</div>
<div class='mgrid'><div class='mbox active' id='bFOREX' onclick="openM('FOREX')">FOREX (11)</div><div class='mbox' id='bCRYPTO' onclick="openM('CRYPTO')">CRYPTO (4)</div></div>
<div class='trow'><button class='tbtn active' id='tfD1' onclick="setTF('D1')">D1</button><button class='tbtn' id='tfH4' onclick="setTF('H4')">H4</button><button class='tbtn' id='tfH1' onclick="setTF('H1')">H1</button><button class='tbtn' id='tfM15' onclick="setTF('M15')">M15</button></div>
<div class='brow'><button class='bbtn active' id='biasAUTO' onclick="setBias('AUTO')">🤖 AUTO PRO</button><button class='bbtn' id='biasBUY' onclick="setBias('BUY')">🟢 FORCE BUY</button><button class='bbtn' id='biasSELL' onclick="setBias('SELL')">🔴 FORCE SELL</button></div>
<div style='text-align:center;margin-top:8px;font-size:12px'>Selected: <span id='sel' style='color:#00ff88;font-weight:bold'>EURZAR</span> | <span id='selTF' style='color:#ffaa00'>D1</span> | <span id='biasTop' style='font-weight:bold;color:#00ff88'>BUY 68% AUTO</span> | <span id='topPrice' style='color:#ffaa00'>18.64130</span></div></div>
<div id='picker'><h4 id='pickerTitle' style='color:#00ff88'></h4><div id='pickerList' style='display:flex;flex-wrap:wrap'></div><button onclick="closeP()" style='background:#333;color:#fff;border:0;padding:6px 12px;border-radius:6px;margin-top:8px'>Close</button></div>
<div id='sig' class='signal buy'>🟢 BUY EURZAR 68% - YOUR CHOICE MODE</div>
<div class='card' style='border:2px solid #00ff88'><small>📈 <span id='chartLabel'>EURZAR D1</span> <span id='biasLabel' style='background:#00ff88;color:#000;padding:3px 8px;border-radius:6px'>BUY 68%</span></small> <small id='livePrice' style='float:right;color:#ffaa00'>18.64130 LIVE</small>
<canvas id='chart' height='500'></canvas>
<div class='tps'><div class='tpbox' style='border-color:#00ff88'><div style='font-size:10px;color:#00ff88'>ENTRY</div><b id='entryTxt' style='color:#00ff88;font-size:16px'>18.64130</b><div id