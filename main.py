from flask import Flask, jsonify, request, make_response
import random, requests
from datetime import datetime, timedelta
app = Flask(__name__)
VERSION="V42 TP 250-385-580 ONLY"
REAL={"EURUSD":1.13667,"NZDCAD":0.80014,"GOLD H4":4258.02,"BTC-USD":84264.85,"EURGBP":0.86062,"GBPUSD":1.32119,"USDZAR":16.4192,"AUDUSD":0.65234,"AUDCAD":0.99223}
BASE={"EURUSD":{"dec":5,"sup":1.13454,"res":1.13854,"name":"Euro vs US Dollar"},"NZDCAD":{"dec":5,"sup":0.79971,"res":0.80200,"name":"New Zealand Dollar vs Canadian Dollar"},"GOLD H4":{"dec":2,"sup":4249.34,"res":4267.34,"name":"Gold Spot"},"BTC-USD":{"dec":2,"sup":83000.00,"res":87140.42,"name":"Bitcoin vs US Dollar"},"EURGBP":{"dec":5,"sup":0.85734,"res":0.86094,"name":"Euro vs Great Britain Pound"},"GBPUSD":{"dec":5,"sup":1.31373,"res":1.32400,"name":"British Pound vs US Dollar"},"USDZAR":{"dec":4,"sup":16.2000,"res":16.6000,"name":"US Dollar vs South African Rand"},"AUDUSD":{"dec":5,"sup":0.64800,"res":0.65800,"name":"Australian Dollar vs US Dollar"},"AUDCAD":{"dec":5,"sup":0.97000,"res":1.00000,"name":"Australian Dollar vs Canadian Dollar"}}
latest={"selected":"USDZAR","tf":"D1","price":16.4192,"support":16.2000,"resistance":16.6000,"dec":4,"live":16.4192,"chat":[],"name":"US Dollar vs South African Rand"}
candles=[]
def get_live(m):
    try:
        if m=="BTC-USD":
            r=requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",timeout=3)
            return float(r.json()["bitcoin"]["usd"])
        mp={"EURGBP":("EUR","GBP"),"GBPUSD":("GBP","USD"),"NZDCAD":("NZD","CAD"),"AUDCAD":("AUD","CAD"),"AUDUSD":("AUD","USD"),"USDZAR":("USD","ZAR"),"EURUSD":("EUR","USD")}
        if m in mp:
            frm,to=mp[m]; r=requests.get(f"https://api.frankfurter.app/latest?from={frm}&to={to}",timeout=3); return float(r.json()["rates"][to])
    except: pass
    return REAL.get(m,16.4192)
def calc_tps(entry,sup,dec):
    dist=abs(entry-sup)
    if dist==0: dist=entry*0.001
    tp1=entry+dist*2.5
    tp2=entry+dist*3.85
    tp3=entry+dist*5.8
    pip_factor=10000 if dec>=4 else 100
    return tp1,tp2,tp3,dist,dist*pip_factor,(tp1-entry)*pip_factor,(tp2-entry)*pip_factor,(tp3-entry)*pip_factor
def build(m,tf,price):
    global candles; candles=[]
    vol=price*0.006 if "ZAR" in m else price*0.008 if m=="BTC-USD" else 15 if m=="GOLD H4" else 0.0012
    for i in range(90):
        p=price+random.uniform(-vol*1.5,vol*1.5); o=p+random.uniform(-vol*0.5,vol*0.5)
        h=max(o,p)+abs(random.uniform(0,vol*0.6)); l=min(o,p)-abs(random.uniform(0,vol*0.6))
        t=(datetime.now()-timedelta(days=(90-i))).strftime("%d %b") if tf=="D1" else (datetime.now()-timedelta(hours=(90-i)*4)).strftime("%H:%M")
        candles.append({"o":o,"h":h,"l":l,"c":p,"t":t})
    candles[-1]["c"]=price
    latest.update({"price":price,"live":price,"support":BASE.get(m,{}).get("sup",price*0.988),"resistance":BASE.get(m,{}).get("res",price*1.012),"selected":m,"tf":tf,"dec":BASE.get(m,{"dec":4})["dec"],"name":BASE.get(m,{}).get("name",m),"chat":[]})
build("USDZAR","D1",get_live("USDZAR"))
@app.route('/select',methods=['POST'])
def sel():
    d=request.json;m=d.get('market','USDZAR');tf=d.get('timeframe','D1');p=get_live(m);build(m,tf,p)
    resp=make_response(jsonify({"ok":True,"price":p,"version":VERSION})); resp.headers['Cache-Control']='no-store'; return resp
@app.route('/candles')
def cnd():
    sa_time=datetime.utcnow()+timedelta(hours=2)
    last=candles[-1]["c"] if candles else latest["price"]
    vm=0.06 if "ZAR" in latest["selected"] else 100 if latest["selected"]=="BTC-USD" else 0.0002
    live_real=get_live(latest["selected"])
    new_p=live_real if live_real and abs(live_real-last)>vm*0.2 else last+random.uniform(-vm,vm)
    if candles: candles[-1]["c"]=new_p; candles[-1]["h"]=max(candles[-1]["h"],new_p+vm*0.2); candles[-1]["l"]=min(candles[-1]["l"],new_p-vm*0.2)
    latest["price"]=new_p;latest["live"]=new_p
    tp1,tp2,tp3,dist,sl_p,tp1_p,tp2_p,tp3_p=calc_tps(new_p,latest["support"],latest["dec"])
    latest["chat"].append(f"[{sa_time.strftime('%H:%M:%S')}] {latest['selected']} TP1 250% {tp1_p:.0f}p | TP2 385% {tp2_p:.0f}p | TP3 580% {tp3_p:.0f}p")
    if len(latest["chat"])>15: latest["chat"].pop(0)
    resp=make_response(jsonify({"candles":candles,"price":new_p,"support":latest["support"],"resistance":latest["resistance"],"entry":new_p,"sl":latest["support"],"tp1":tp1,"tp2":tp2,"tp3":tp3,"dist":dist,"sl_pips":sl_p,"tp1_pips":tp1_p,"tp2_pips":tp2_p,"tp3_pips":tp3_p,"signal":f"BUY {latest['selected']} SL {sl_p:.0f}p TP1 250% {tp1_p:.0f}p","mode":f"SCALPING RR 1:2.5(250%) 1:3.85(385%) 1:5.8(580%)","chat":latest["chat"],"selected":latest["selected"],"timeframe":latest["tf"],"dec":latest["dec"],"name":latest["name"],"live_price":new_p,"version":VERSION}))
    resp.headers['Cache-Control']='no-store'; return resp
@app.route('/analyze',methods=['POST'])
def ana():
    m=request.form.get('selected_market','USDZAR') or latest.get('selected','USDZAR')
    p=get_live(m); sup=BASE.get(m,{}).get("sup",p*0.99); dec=BASE.get(m,{"dec":4})["dec"]
    tp1,tp2,tp3,dist,sl_p,tp1_p,tp2_p,tp3_p=calc_tps(p,sup,dec)
    fmt=f"{{:.{dec}f}}"; analysis=f"""{VERSION}
✅ {m} LIVE {fmt.format(p)}
SL 100% = {fmt.format(sup)} = {sl_p:.0f} pips

TP1 250% = {fmt.format(tp1)} = {tp1_p:.0f} pips [OLD 70% REMOVED]
TP2 385% = {fmt.format(tp2)} = {tp2_p:.0f} pips [OLD 120% REMOVED]
TP3 580% = {fmt.format(tp3)} = {tp3_p:.0f} pips [OLD 200% REMOVED]

RR: 1:2.5 | 1:3.85 | 1:5.8
"""
    resp=make_response(jsonify({"analysis":analysis,"version":VERSION})); resp.headers['Cache-Control']='no-store'; return resp
@app.route('/')
def home():
    html=f"""<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'><meta http-equiv='Cache-Control' content='no-cache, no-store, must-revalidate'><title>EUGE {VERSION}</title>
<style>body{{background:#000;color:#fff;font-family:Arial;margin:0;padding:6px}}.card{{background:#111;border-radius:14px;padding:10px;margin:6px 0;border:1px solid #222}}.signal{{background:#00ff88;color:#000;padding:10px;border-radius:12px;text-align:center;font-weight:bold}}.mode{{text-align:center;padding:7px;border-radius:10px;margin-top:5px;font-weight:bold;background:#ffaa00;color:#000}}#chat{{height:200px;overflow:auto;background:#000;border-radius:8px;padding:6px;font-size:10px;color:#00ff88;border:1px solid #222}}.logo{{background:#000;border:2px solid #00ff88;border-radius:16px;padding:10px;text-align:center}}.mgrid{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:5px;margin-top:6px}}.mbox{{background:#111;border-radius:8px;padding:8px 2px;border:2px solid #333;font-size:10px;font-weight:bold;cursor:pointer;text-align:center}}.mbox.active{{border-color:#00ff88}}.trow{{display:flex;gap:3px;margin-top:6px;flex-wrap:wrap;justify-content:center}}.tbtn{{background:#111;color:#888;border:1px solid #333;padding:5px 10px;border-radius:16px;font-size:10px;font-weight:bold;cursor:pointer}}.tbtn.active{{background:#00ff88;color:#000}}.tps{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:5px;margin-top:6px}}.tpbox{{background:#111;border-radius:8px;padding:6px;text-align:center;border:1px solid #333;min-height:68px}}.verified{{background:#00ff88;color:#000;padding:2px 5px;border-radius:5px;font-size:9px;font-weight:bold}}#picker{{display:none;background:#111;border:2px solid #00ff88;border-radius:10px;padding:8px;margin:6px 0}}.pbtn{{background:#222;color:#fff;border:1px solid #444;padding:8px 12px;border-radius:6px;margin:3px;font-size:11px}}</style></head><body>
<div class='logo'><h2>EUGE ROBOT <span class='verified'>{VERSION}</span></h2><div style='font-size:11px;color:#ffaa00'>CHANGED: 70%→250% | 120%→385% | 200%→580%</div>
<div class='mgrid'><div class='mbox active' id='bFOREX' onclick="openM('FOREX')">FOREX</div><div class='mbox' id='bCRYPTO' onclick="openM('CRYPTO')">CRYPTO</div><div class='mbox' id='bDERIV' onclick="openM('DERIV')">GOLD</div></div>
<div class='trow'><button class='tbtn' id='tfM15' onclick="setTF('M15')">M15</button><button class='tbtn' id='tfM30' onclick="setTF('M30')">M30</button><button class='tbtn active' id='tfD1' onclick="setTF('D1')">D1</button><button class='tbtn' id='tfH1' onclick="setTF('H1')">H1</button><button class='tbtn' id='tfH4' onclick="setTF('H4')">H4</button></div>
<div style='font-size:10px;color:#888;margin-top:4px;text-align:center'>Selected: <span id='sel' style='color:#00ff88;font-weight:bold'>USDZAR</span> | <span id='selTF' style='color:#ffaa00;font-weight:bold'>D1</span> | <span id='topPrice' style='color:#ffaa00'>16.4192</span></div></div>
<div id='picker'><h4 id='pickerTitle' style='color:#00ff88;margin:0 0 6px 0'></h4><div id='pickerList' style='display:flex;flex-wrap:wrap'></div><button onclick="closeP()" style='background:#333;color:#fff;border:0;padding:5px 10px;border-radius:5px;margin-top:6px'>Close</button></div>
<div id='sig' class='signal'>BUY - TP1 250% TP2 385% TP3 580% ONLY</div>
<div id='modeBox' class='mode'>TP1 250% | TP2 385% | TP3 580% - NO MORE 70/120/200</div>
<div class='card'><div style='display:flex;justify-content:space-between'><small>Live (<span id='chartLabel'>USDZAR D1</span>) <span class='verified'>{VERSION}</span></small><small id='livePrice' style='color:#ffaa00;font-weight:bold'>16.4192 LIVE</small></div><canvas id='chart' height='500' style='width:100%;background:#fff;border-radius:10px;margin-top:6px'></canvas>
<div class='tps'><div class='tpbox' style='border-color:#00ff88'><div style='font-size:9px;color:#00ff88'>ENTRY</div><b id='entryTxt' style='color:#00ff88'>16.4192</b><div style='font-size:8px;color:#888'>---</div></div><div class='tpbox' style='border-color:#ff4444'><div style='font-size:9px;color:#ff4444'>SL 100%</div><b id='slTxt' style='color:#ff4444'>16.2000</b><div id='slPips' style='font-size:10px;color:#ff4444;font-weight:bold'>2192 pips</div></div><div class='tpbox' style='border-color:#ffff00'><div style='font-size:9px;color:#ffff00;font-weight:bold'>TP1 250%</div><b id='tp1Txt' style='color:#ffff00'>16.96</b><div id='tp1Pips' style='font-size:10px;color:#ffff00;font-weight:bold'>5480 pips</div><div style='font-size:7px;color:#666;text-decoration:line-through'>OLD 70%</div></div></div>
<div class='tps' style='margin-top:4px'><div class='tpbox' style='border-color:#ffaa00'><div style='font-size:9px;color:#ffaa00;font-weight:bold'>TP2 385%</div><b id='tp2Txt' style='color:#ffaa00'>17.26</b><div id='tp2Pips' style='font-size:10px;color:#ffaa00;font-weight:bold'>8439 pips</div><div style='font-size:7px;color:#666;text-decoration:line-through'>OLD 120%</div></div><div class='tpbox' style='border-color:#00aaff'><div style='font-size:9px;color:#00aaff;font-weight:bold'>TP3 580%</div><b id='tp3Txt' style='color:#00aaff'>17.69</b><div id='tp3Pips' style='font-size:10px;color:#00aaff;font-weight:bold'>12713 pips</div><div style='font-size:7px;color:#666;text-decoration:line-through'>OLD 200%</div></div><div class='tpbox'><div style='font-size:8px'>RESIST</div><b id='resTxt' style='color:#ff4444'>16.6000</b><div id='distPips' style='font-size:8px;color:#00ff88'>V42 NEW %</div></div></div>
<div id='storyBox' style='margin-top:8px;background:#000;padding:8px;border-radius:6px;border:1px solid #00ff88;font-size:10px;color:#00ff88'>TPs 250% 385% 580%</div></div>
<div class='card'><h4 style='margin:0;font-size:14px'>Screenshot Analysis - {VERSION}</h4>
<input type='file' id='file' accept='image/*' style='font-size:11px;margin-top:6px;display:block'>
<img id='prev' style='width:100%;border-radius:8px;margin-top:8px;display:none;max-height:300px;object-fit:contain'>
<button onclick='up()' id='analyzeBtn' style='background:#00ff88;color:#000;border:0;padding:12px 16px;border-radius:10px;font-weight:bold;margin-top:8px;width:100%;font-size:14px'>🔍 ANALYZE {VERSION}</button>
<div id='res' style='margin-top:8px;background:#000;padding:10px;border-radius:6px;display:none;font-size:11px;white-space:pre-wrap;border:1px solid #00ff88;color:#00ff88;min-height:50px'></div></div>
<div class='card'><h4 style='margin:0 0 4px 0;font-size:14px'>Live Chat {VERSION}</h4><div id='chat'>Loading...</div></div>
<script>
let selectedMarket='USDZAR';let selectedTF='D1';let markets={{"FOREX":["EURUSD","GBPUSD","EURGBP","NZDCAD","AUDUSD","AUDCAD","USDZAR"],"CRYPTO":["BTC-USD"],"DERIV":["GOLD H4"]}};
function openM(t){{document.querySelectorAll('.mbox').forEach(b=>b.classList.remove('active'));document.getElementById('b'+t).classList.add('active');document.getElementById('picker').style.display='block';document.getElementById('pickerTitle').innerText=t+' - Choose:';let l=document.getElementById('pickerList');l.innerHTML='';(markets[t]||[]).forEach(m=>{{let b=document.createElement('button');b.className='pbtn';b.innerText=m;b.onclick=()=>{{selectM(m);}};l.appendChild(b);}});}}
function closeP(){{document.getElementById('picker').style.display='none';}}
function setTF(tf){{selectedTF=tf;document.querySelectorAll('.tbtn').forEach(b=>b.classList.remove('active'));let el=document.getElementById('tf'+tf);if(el) el.classList.add('active');fetch('/select',{{method:'POST',headers:{{'Content-Type':'application/json','Cache-Control':'no-cache'}},body:JSON.stringify({{market:selectedMarket,timeframe:tf}})}}).then(r=>r.json());}}
function selectM(m){{selectedMarket=m;document.getElementById('sel').innerText=m;closeP();fetch('/select',{{method:'POST',headers:{{'Content-Type':'application/json','Cache-Control':'no-cache'}},body:JSON.stringify({{market:m,timeframe:selectedTF}})}}).then(r=>r.json()).then(d=>{{document.getElementById('topPrice').innerText=d.price;}});}}
document.getElementById('file').addEventListener('change', function(e){{
  let f=e.target.files[0]; if(!f) return;
  let rd=new FileReader(); rd.onload=ev=>{{
    let img=document.getElementById('prev'); img.src=ev.target.result; img.style.display='block';
    document.getElementById('res').style.display='block'; document.getElementById('res').innerText='✅ '+f.name+' loaded - Press ANALYZE!';
  }}; rd.readAsDataURL(f);
}});
function up(){{
  let f=document.getElementById('file').files[0]; let resDiv=document.getElementById('res'); let btn=document.getElementById('analyzeBtn');
  resDiv.style.display='block'; resDiv.innerText='⏳ Analyzing...';
  btn.innerText='⏳ ANALYZING...'; btn.disabled=true;
  let fd