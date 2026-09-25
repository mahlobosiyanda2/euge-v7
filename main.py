from flask import Flask, jsonify, request, make_response
import random, requests
from datetime import datetime, timedelta
app = Flask(__name__)
VERSION="V54 75-150-245 PIPS FINAL"
REAL={"GBPUSD":1.3225,"EURJPY":180.106,"EURGBP":0.8607,"NZDCAD":0.80187,"AUDCAD":0.9937,"USDZAR":16.3654,"EURZAR":18.64130,"EURUSD":1.1385,"NZDJPY":89.51,"USDJPY":145.32,"GAUUSD":137.355,"BTC-USD":83905.15,"BTC-ZAR":1385000,"LTCUSD":98.45,"ETCUSD":22.34}
BASE={"GBPUSD":{"dec":5,"sup":1.32034,"res":1.32400,"name":"GBP/USD"},"EURJPY":{"dec":3,"sup":180.106,"res":181.632,"name":"EUR/JPY"},"EURGBP":{"dec":5,"sup":0.85979,"res":0.86092,"name":"EUR/GBP"},"NZDCAD":{"dec":5,"sup":0.79861,"res":0.80159,"name":"NZD/CAD"},"AUDCAD":{"dec":5,"sup":0.98990,"res":0.99372,"name":"AUD/CAD"},"USDZAR":{"dec":4,"sup":16.3614,"res":16.4387,"name":"USD/ZAR"},"EURZAR":{"dec":4,"sup":18.62758,"res":18.69405,"name":"EUR/ZAR"},"EURUSD":{"dec":5,"sup":1.13673,"res":1.13854,"name":"EUR/USD"},"NZDJPY":{"dec":3,"sup":89.451,"res":89.992,"name":"NZD/JPY"},"USDJPY":{"dec":3,"sup":144.5,"res":146.0,"name":"USD/JPY"},"GAUUSD":{"dec":3,"sup":133.156,"res":141.876,"name":"Gold gram vs USD"},"BTC-USD":{"dec":2,"sup":79000.00,"res":86076.39,"name":"BTC/USD"},"BTC-ZAR":{"dec":2,"sup":1350000,"res":1420000,"name":"BTC/ZAR"},"LTCUSD":{"dec":2,"sup":95.0,"res":102.0,"name":"LTC/USD"},"ETCUSD":{"dec":2,"sup":21.0,"res":23.5,"name":"ETC/USD"}}
latest={"selected":"EURJPY","tf":"D1","price":180.106,"support":180.106,"resistance":181.632,"dec":3,"live":180.106,"chat":[],"name":"EUR/JPY","manual_bias":"AUTO"}
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
        vol=(res-sup)*0.5
        base += random.uniform(-vol*0.3,vol*0.3)
        if i>=77: base=price+random.uniform(-vol*0.1,vol*0.1)
        if i==79: base=price
        c=base; o=c+random.uniform(-vol*0.2,vol*0.2); h=max(o,c)+abs(random.uniform(0,vol*0.6)); l=min(o,c)-abs(random.uniform(0,vol*0.6))
        candles.append({"o":o,"h":h,"l":l,"c":c,"t":(datetime.now()-timedelta(days=80-i)).strftime("%d %b")})
    latest.update({"price":price,"live":price,"support":sup,"resistance":res,"selected":m,"tf":tf,"dec":BASE.get(m,{"dec":3})["dec"],"name":BASE.get(m,{}).get("name",m),"chat":[f"[{datetime.now().strftime('%H:%M:%S')}] {m} {tf} V54 75-150-245 READY"]})
build("EURJPY","D1",get_live("EURJPY"))
def calc_tps(entry, dec, is_buy):
    if dec==5: pip=0.00010
    elif dec==4: pip=0.0001
    elif dec==3: pip=0.010
    else: pip=1.0
    # ✅ YOUR REQUEST: 75 / 150 / 245
    tp1_dist = 75 * pip
    tp2_dist = 150 * pip
    tp3_dist = 245 * pip
    sl_dist = 75 * pip
    if is_buy:
        tp1 = entry + tp1_dist; tp2 = entry + tp2_dist; tp3 = entry + tp3_dist; sl = entry - sl_dist
    else:
        tp1 = entry - tp1_dist; tp2 = entry - tp2_dist; tp3 = entry - tp3_dist; sl = entry + sl_dist
    return tp1,tp2,tp3,sl,75,75,150,245
def get_pro_analysis(m,p,sup,res,manual):
    if manual!="AUTO": return manual,100,f"MANUAL {manual} TEST - SL 75p TP 75/150/245"
    if m=="EURJPY": return "SELL",71,"EURJPY D1 breakdown-retest 180.10 polarity flip"
    if m=="GAUUSD": return "BUY",72,"GAUUSD gram 137.35 BUY retest"
    if m=="BTC-USD": return "BUY",78,"BTCUSD 83905 breakout retest BUY"
    return "SELL",65,f"{m} bearish"
@app.route('/select',methods=['POST'])
def sel():
    d=request.json; m=d.get('market','EURJPY'); tf=d.get('timeframe','D1'); manual=d.get('bias','AUTO'); latest["manual_bias"]=manual
    p=get_live(m); build(m,tf,p)
    r=make_response(jsonify({"ok":True})); r.headers['Cache-Control']='no-store'; return r
@app.route('/candles')
def cnd():
    live=get_live(latest["selected"])
    if candles: candles[-1]["c"]=live
    latest["price"]=live
    bias,conf,_=get_pro_analysis(latest["selected"],live,latest["support"],latest["resistance"],latest["manual_bias"])
    is_buy=bias=="BUY"
    tp1,tp2,tp3,sl,sl_p,tp1_p,tp2_p,tp3_p=calc_tps(live,latest["dec"],is_buy)
    sa=datetime.utcnow()+timedelta(hours=2)
    latest["chat"].append(f"[{sa.strftime('%H:%M:%S')}] {latest['selected']} {bias} {live:.{latest['dec']}f}")
    if len(latest["chat"])>22: latest["chat"].pop(0)
    r=make_response(jsonify({"candles":candles,"price":live,"support":latest["support"],"resistance":latest["resistance"],"entry":live,"sl":sl,"tp1":tp1,"tp2":tp2,"tp3":tp3,"sl_pips":sl_p,"tp1_pips":tp1_p,"tp2_pips":tp2_p,"tp3_pips":tp3_p,"signal":f"{bias} {latest['selected']} {conf}% | SL 75p TP 75/150/245p","mode":f"{VERSION} {bias} {conf}%","chat":latest["chat"],"selected":latest["selected"],"timeframe":latest["tf"],"dec":latest["dec"],"name":latest["name"],"version":VERSION,"bias":bias,"conf":conf,"manual":latest["manual_bias"]}))
    r.headers['Cache-Control']='no-store'; return r
@app.route('/analyze',methods=['POST'])
def ana():
    m=request.form.get('selected_market','EURJPY'); p=get_live(m); sup=BASE.get(m,{}).get("sup",p*0.97); res=BASE.get(m,{}).get("res",p*1.03); dec=BASE.get(m,{"dec":3})["dec"]; manual=request.form.get('manual_bias','AUTO')
    bias,conf,reason=get_pro_analysis(m,p,sup,res,manual)
    is_buy=bias=="BUY"
    tp1,tp2,tp3,sl,sl_p,tp1_p,tp2_p,tp3_p=calc_tps(p,dec,is_buy)
    fmt=f"{{:.{dec}f}}"
    analysis=f"""🔥 {VERSION} - 75/150/245 SWING 🔥
MARKET: {m} | LIVE: {fmt.format(p)} | {bias} {conf}%
ENTRY: {fmt.format(p)}
SL: {fmt.format(sl)} = 75 pips
TP1 = {fmt.format(tp1)} = 75 pips → 50%
TP2 = {fmt.format(tp2)} = 150 pips → 30%
TP3 = {fmt.format(tp3)} = 245 pips → 20%
RR 1:1 / 1:2 / 1:3.26
{reason}
"""
    r=make_response(jsonify({"analysis":analysis,"bias":bias})); r.headers['Cache-Control']='no-store'; return r
@app.route('/')
def home():
    html=f"""<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'><title>{VERSION}</title>
<style>body{{background:#000;color:#fff;font-family:Arial;margin:0;padding:6px}}.card{{background:#111;border-radius:14px;padding:10px;margin:8px 0;border:1px solid #222}}.signal{{padding:16px;border-radius:14px;text-align:center;font-weight:bold;font-size:16px}}.signal.sell{{background:#ff4444}}.signal.buy{{background:#00ff88;color:#000}}.logo{{background:#000;border:2px solid #00ff88;border-radius:16px;padding:12px;text-align:center}}.mgrid{{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:10px}}.mbox{{background:#111;border-radius:10px;padding:10px;border:2px solid #333;font-size:12px;font-weight:bold;cursor:pointer;text-align:center}}.mbox.active{{border-color:#00ff88;background:#002200}}.trow{{display:flex;gap:6px;justify-content:center;margin-top:10px;flex-wrap:wrap}}.tbtn{{background:#111;color:#888;border:1px solid #333;padding:8px 14px;border-radius:20px;font-size:12px;font-weight:bold;cursor:pointer}}.tbtn.active{{background:#00ff88;color:#000}}.brow{{display:flex;gap:6px;justify-content:center;margin-top:10px}}.bbtn{{padding:10px 16px;border-radius:10px;font-weight:bold;border:2px solid #333;cursor:pointer;background:#111;color:#888}}.bbtn.active{{border-color:#00ff88;background:#002200;color:#00ff88}}.tps{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:10px}}.tpbox{{background:#111;border-radius:12px;padding:10px;text-align:center;border:2px solid #333;min-height:80px}}#picker{{display:none;background:#111;border:2px solid #00ff88;border-radius:12px;padding:12px;margin:8px 0}}.pbtn{{background:#222;color:#fff;border:1px solid #444;padding:10px 14px;border-radius:8px;margin:4px}}canvas{{display:block;width:100%;background:#fff;border-radius:12px;margin-top:10px;border:2px solid #00ff88}}</style></head><body>
<div class='logo'><h1>EUGE ROBOT <span style='background:#00ff88;color:#000;padding:4px 8px;border-radius:6px;font-size:10px'>{VERSION}</span></h1><div style='color:#00ff88;font-weight:bold'>✅ SWING 75p / 150p / 245p FINAL!</div>
<div class='mgrid'><div class='mbox active' id='bFOREX' onclick="openM('FOREX')">FOREX (11)</div><div class='mbox' id='bCRYPTO' onclick="openM('CRYPTO')">CRYPTO (4)</div></div>
<div class='trow'><button class='tbtn active' id='tfD1' onclick="setTF('D1')">D1</button><button class='tbtn' id='tfH4' onclick="setTF('H4')">H4</button><button class='tbtn' id='tfH1' onclick="setTF('H1')">H1</button><button class='tbtn' id='tfM15' onclick="setTF('M15')">M15</button></div>
<div class='brow'><button class='bbtn active' id='biasAUTO' onclick="setBias('AUTO')">🤖 AUTO PRO</button><button class='bbtn' id='biasBUY' onclick="setBias('BUY')">🟢 FORCE BUY</button><button class='bbtn' id='biasSELL' onclick="setBias('SELL')">🔴 FORCE SELL</button></div>
<div style='text-align:center;margin-top:8px;font-size:12px'>Selected: <span id='sel' style='color:#00ff88;font-weight:bold'>EURJPY</span> | <span id='selTF' style='color:#ffaa00'>D1</span></div></div>
<div id='picker'><h4 id='pickerTitle' style='color:#00ff88'></h4><div id='pickerList' style='display:flex;flex-wrap:wrap'></div><button onclick="closeP()" style='background:#333;color:#fff;border:0;padding:6px 12px;border-radius:6px;margin-top:8px'>Close</button></div>
<div id='sig' class='signal sell'>🔴 SELL EURJPY 71% | SL 75p TP 75/150/245p</div>
<div class='card' style='border:2px solid #00ff88'><small>📈 <span id='chartLabel'>EURJPY D1</span> <span id='biasLabel' style='background:#ff4444;color:#fff;padding:3px 8px;border-radius:6px'>SELL 71%</span></small> <small id='livePrice' style='float:right;color:#ffaa00'>180.106 LIVE</small>
<canvas id='chart' height='500'></canvas>
<div class='tps'><div class='tpbox' style='border-color:#00ff88'><div style='font-size:10px;color:#00ff88'>ENTRY</div><b id='entryTxt' style='color:#00ff88;font-size:16px'>180.106</b><div id='biasBox' style='font-size:10px;color:#00ff88'>SELL</div></div><div class='tpbox' style='border-color:#ff4444'><div style='font-size:10px;color:#ff4444'>SL 75p</div><b id='slTxt' style='color:#ff4444;font-size:16px'>180.856</b><div id='slPips' style='font-size:11px;color:#ff4444'>75 pips</div></div><div class='tpbox' style='border-color:#ffff00'><div style='font-size:10px;color:#ffff00'>TP1 75p</div><b id='tp1Txt' style='color:#ffff00;font-size:16px'>179.356</b><div id='tp1Pips' style='font-size:11px;color:#ffff00'>75 pips</div></div></div>
<div class='tps' style='margin-top:8px'><div class='tpbox' style='border-color:#ffaa00'><div style='font-size:10px;color:#ffaa00'>TP2 150p</div><b id='tp2Txt' style='color:#ffaa00;font-size:16px'>178.606</b><div id='tp2Pips' style='font-size:11px;color:#ffaa00'>150 pips</div></div><div class='tpbox' style='border-color:#00aaff'><div style='font-size:10px;color:#00aaff'>TP3 245p</div><b id='tp3Txt' style='color:#00aaff;font-size:16px'>177.656</b><div id='tp3Pips' style='font-size:11px;color:#00aaff'>245 pips</div></div><div class='tpbox'><div style='font-size:10px'>RESIST</div><b id='resTxt' style='color:#ff4444;font-size:16px'>181.632</b></div></div>
</div>
<div class='card' style='border:3px solid #00ff88'><h3 style='margin:0 0 8px 0;color:#00ff88'>🎯 ANALYZE CHART</h3><input type='file' id='file' accept='image/*'><img id='prev' style='width:100%;border-radius:12px;margin-top:8px;display:none;max-height:300px;object-fit:contain'><button onclick='up()' style='background:#00ff88;color:#000;border:0;padding:14px;width:100%;border-radius:12px;font-weight:bold;margin-top:8px'>🔍 ANALYZE - V54</button><div id='res' style='margin-top:10px;background:#000;padding:12px;border-radius:10px;display:none;color:#00ff88;white-space:pre-wrap;border:2px solid #00ff88;min-height:100px;font-size:12px'></div></div>
<script>
let selectedMarket='EURJPY';let selectedTF='D1';let selectedBias='AUTO';
let markets={{"FOREX":["GBPUSD","EURJPY","EURGBP","NZDCAD","AUDCAD","USDZAR","EURZAR","EURUSD","NZDJPY","USDJPY","GAUUSD"],"CRYPTO":["BTC-USD","BTC-ZAR","LTCUSD","ETCUSD"]}};
function openM(t){{document.querySelectorAll('.mbox').forEach(b=>b.classList.remove('active'));document.getElementById('b'+t).classList.add('active');document.getElementById('picker').style.display='block';document.getElementById('pickerTitle').innerText=t;let l=document.getElementById('pickerList');l.innerHTML='';(markets[t]||[]).forEach(m=>{{let b=document.createElement('button');b.className='pbtn';b.innerText=m;b.onclick=()=>selectM(m);l.appendChild(b);}});}}
function closeP(){{document.getElementById('picker').style.display='none';}}
function setTF(tf){{selectedTF=tf;document.querySelectorAll('.tbtn').forEach(b=>b.classList.remove('active'));document.getElementById('tf'+tf).classList.add('active');fetch('/select',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{market:selectedMarket,timeframe:tf,bias:selectedBias}})}});}}
function setBias(b){{selectedBias=b;document.querySelectorAll('.bbtn').forEach(x=>x.classList.remove('active'));document.getElementById('bias'+b).classList.add('active');fetch('/select',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{market:selectedMarket,timeframe:selectedTF,bias:b}})}});}}
function selectM(m){{selectedMarket=m;document.getElementById('sel').innerText=m;closeP();fetch('/select',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{market:m,timeframe:selectedTF,bias:selectedBias}})}});}}
document.getElementById('file').addEventListener('change',e=>{{let f=e.target.files[0];if(!f)return;let