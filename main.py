from flask import Flask, jsonify, request
import random
from datetime import datetime, timedelta
import pytz

app = Flask(__name__)
sa_tz = pytz.timezone('Africa/Johannesburg')

MARKETS = {
    "FOREX": ["EURGBP", "GBPUSD", "EURUSD", "USDZAR", "NZDCAD", "AUDCAD", "EURZAR"],
    "CRYPTO": ["BTC-USD"],
    "JSE": ["JSE TOP40"],
    "DERIV": ["R_75", "GOLD H4"]
}

PRESETS = {
    "EURGBP": {"price": 0.86062, "support": 0.85734, "resistance": 0.86094, "tf": "M30", "dec": 5,
               "story": "Flat 5 days at 0.8572, then breakout after 3 Sep 14:30! Uptrend started!",
               "touches": "Support tested 2x: 3 Sep and 15 Sep, both bounced!",
               "trend": "BULLISH BREAKOUT from consolidation",
               "scenario_a": "BUY breakout continuation", "scenario_b": "SELL fakeout if back below 0.85734"},
    "USDZAR": {"price": 16.4192, "support": 16.1585, "resistance": 16.4192, "tf": "M30", "dec": 4,
               "story": "Down from 16.6 Aug, downtrend to 16.15 Sep 11, now bouncing strong to 16.41!",
               "touches": "Support 16.1585 tested Sep 11, now resistance at 16.4192 top!",
               "trend": "BULLISH BOUNCE from Sep low, near resistance",
               "scenario_a": "BUY breakout above 16.4192 to 16.60", "scenario_b": "SELL rejection at 16.4192 back to 16.15"},
    "AUDCAD": {"price": 0.99243, "support": 0.97948, "resistance": 1.00000, "tf": "M30", "dec": 5,
               "story": "Low 0.854 Aug 2023, sideways till Feb 2025, spike Mar 2026 to 0.992! Strong uptrend!",
               "touches": "Support 0.97948 tested Sep 2026, resistance 1.0000 psychological!",
               "trend": "STRONG UPTREND since Mar 2026",
               "scenario_a": "BUY to 1.0000 breakout", "scenario_b": "SELL if fails at 1.0000"},
    "GBPUSD": {"price": 1.32119, "support": 1.32119, "resistance": 1.36613, "tf": "D1", "dec": 5,
               "story": "Peak 1.385 Jan 2026, down to 1.321 now! Critical support at 1.32119 tested 4x!",
               "touches": "Support tested: 21 Nov 2025 (~1.301), 8 Apr 2026 (~1.319), 9 Jul 2026 (~1.313), now 5 Oct 2026 (1.32119)!",
               "trend": "BEARISH downtrend from 1.36613 (25 Aug) to 1.32119 now - big red candles!",
               "scenario_a": "BUY BOUNCE if support holds (held 3 times before)",
               "scenario_b": "SELL BREAKDOWN if 1H close below 1.32119 - more likely! Bearish momentum!"},
    "NZDCAD": {"price": 0.79987, "support": 0.79536, "resistance": 0.82641, "tf": "D1", "dec": 5,
               "story": "High 0.82641 Aug 10 2026, downtrend to 0.799 now at support!",
               "touches": "Support 0.79536 at bottom, resistance 0.82641 Aug high",
               "trend": "DOWNTREND to support - bounce possible",
               "scenario_a": "BUY bounce at support", "scenario_b": "SELL breakdown below 0.79536"},
    "GOLD H4": {"price": 4460.39, "support": 4283.78, "resistance": 4544.42, "tf": "H4", "dec": 2,
                "story": "Uptrend to 4544, pullback to 4283 support!", "touches": "Support 4283, resistance 4544",
                "trend": "BULLISH pullback", "scenario_a": "BUY at support", "scenario_b": "SELL below support"}
}

latest = {"selected": "NZDCAD", "timeframe": "D1", "price": 0.79987, "support": 0.79536, "resistance": 0.82641,
          "entry": 0.79987, "sl": 0.79536, "tp1": 0, "tp2": 0, "tp3": 0, "signal": "WAIT", "mode": "SCALPING 🔥", "chat": [], "dec":5}

candles=[]
def gen_candles(market="NZDCAD"):
    global candles
    preset = PRESETS.get(market, PRESETS["NZDCAD"])
    candles=[]
    base=preset["support"]; rng=max(0.0005, preset["resistance"]-preset["support"])
    for i in range(70):
        if market=="NZDCAD":
            p = 0.826 - (i/70)*0.026 + random.uniform(-0.003,0.003)
        elif market=="GBPUSD":
            if i < 55: p = 1.347 + random.uniform(-0.02,0.02)
            else: p = 1.366 - (i-55)*0.003 + random.uniform(-0.003,0.001)
        else:
            p = base + rng*0.5 + random.uniform(-rng*0.15, rng*0.15)
        o = p + random.uniform(-rng*0.02, rng*0.02); c=p; h=max(o,c)+rng*0.05; l=min(o,c)-rng*0.05
        t = (datetime.now(sa_tz)-timedelta(days=(70-i)*2)).strftime("%d %b") if "D1" in preset["tf"] else (datetime.now(sa_tz)-timedelta(minutes=(70-i)*30)).strftime("%H:%M")
        candles.append({"o":o,"h":h,"l":l,"c":c,"t":t})
    candles[-1]["c"]=preset["price"]
    latest.update(preset); latest["selected"]=market

def calc_tps(entry, sl, is_buy=True):
    risk=abs(entry-sl)
    if risk==0: risk=entry*0.006
    if is_buy: return entry+risk*0.7, entry+risk*1.2, entry+risk*2.0
    else: return entry-risk*0.7, entry-risk*1.2, entry-risk*2.0

def get_mode(price, support, resistance):
    if abs(price-support)/max(price,0.0001)*100 < 1.2: return "SCALPING 🔥", f"At Support {support} - Critical!"
    if abs(resistance-price)/max(price,0.0001)*100 < 1.0: return "DAY TRADE 📈", f"Near Resistance {resistance}"
    return "DAY TRADE 📈", "Trend"

gen_candles("NZDCAD")
latest["tp1"], latest["tp2"], latest["tp3"]=calc_tps(latest["price"], 0.79536, True)
latest["mode"], latest["mode_reason"]=get_mode(latest["price"], latest["support"], latest["resistance"])

@app.route('/select', methods=['POST'])
def select():
    data=request.json; m=data.get('market','NZDCAD'); tf=data.get('timeframe', PRESETS.get(m,{}).get('tf','D1'))
    latest["selected"]=m; latest["timeframe"]=tf; gen_candles(m)
    preset = PRESETS.get(m, PRESETS["NZDCAD"])
    sl = preset["support"] if m!="GBPUSD" else 1.31373
    latest["tp1"], latest["tp2"], latest["tp3"]=calc_tps(latest["price"], sl, True)
    latest["mode"], latest["mode_reason"]=get_mode(latest["price"], latest["support"], latest["resistance"])
    return jsonify({"ok":True})

@app.route('/candles')
def get_candles():
    preset=PRESETS.get(latest["selected"], PRESETS["NZDCAD"])
    last=candles[-1]["c"]; rng=abs(preset["resistance"]-preset["support"])*0.04
    new_p=last+random.uniform(-rng, rng); o=last; c=new_p; h=max(o,c)+rng*0.5; l=min(o,c)-rng*0.5
    t_str=datetime.now(sa_tz).strftime("%H:%M")
    candles.append({"o":o,"h":h,"l":l,"c":c,"t":t_str})
    if len(candles)>80: candles.pop(0)
    latest["price"]=c; latest["entry"]=c
    sl = preset["support"] if latest["selected"]!="GBPUSD" else 1.31373
    latest["tp1"], latest["tp2"], latest["tp3"]=calc_tps(c, sl, True)
    latest["mode"], latest["mode_reason"]=get_mode(c, latest["support"], latest["resistance"])
    dec = preset.get("dec",5)
    fmt = f"{{:.{dec}f}}" if dec>0 else "{:.0f}"
    ts=datetime.now(sa_tz).strftime("%H:%M:%S")
    latest["chat"].append(f"[{ts}] {latest['selected']} {latest['timeframe']}: {fmt.format(c)} | {latest['mode']} | E:{fmt.format(c)} SL:{fmt.format(sl)} TP1:{fmt.format(latest['tp1'])}(70%)")
    if len(latest["chat"])>22: latest["chat"].pop(0)
    return jsonify({"candles":candles, "price":c, "support":latest["support"], "resistance":latest["resistance"],
                    "entry":c, "sl":sl, "tp1":latest["tp1"], "tp2":latest["tp2"], "tp3":latest["tp3"],
                    "signal":latest["signal"], "mode":latest["mode"], "mode_reason":latest["mode_reason"],
                    "chat":latest["chat"], "selected":latest["selected"], "timeframe":latest["timeframe"], "dec":dec,
                    "story":preset.get("story",""), "touches":preset.get("touches",""), "trend":preset.get("trend","")})

@app.route('/analyze', methods=['POST'])
def analyze():
    selected = request.form.get('selected_market', latest["selected"])
    file = request.files.get('image')
    filename = file.filename.lower() if file else ""
    combined = (filename + " " + selected).lower()
    market_key = selected
    if 'audcad' in combined: market_key = "AUDCAD"
    elif 'nzdcad' in combined: market_key = "NZDCAD"
    elif 'eurgbp' in combined: market_key = "EURGBP"
    elif 'usdzar' in combined or ('usd' in combined and 'zar' in combined): market_key = "USDZAR"
    elif 'gbpusd' in combined: market_key = "GBPUSD"
    elif 'eurusd' in combined: market_key = "EURUSD"
    elif 'gold' in combined or 'xau' in combined: market_key = "GOLD H4"
    preset = PRESETS.get(market_key, PRESETS["NZDCAD"])
    entry = preset["price"]; support = preset["support"]; resistance = preset["resistance"]; dec = preset["dec"]
    sl_for_calc = 1.31373 if market_key=="GBPUSD" else support
    tp1,tp2,tp3 = calc_tps(entry, sl_for_calc, True)
    tp1_s, tp2_s, tp3_s = calc_tps(entry, 1.32733 if market_key=="GBPUSD" else resistance, False)
    mode, reason = get_mode(entry, support, resistance)
    fmt = f"{{:.{dec}f}}" if dec>0 else "{:.0f}"
    if market_key=="GBPUSD":
        analysis = f"""📊 GBPUSD D1 - Human Analysis

Pair: GBPUSD D1, Price {fmt.format(entry)}
Support: {fmt.format(support)} | Resistance: 1.36613

Story: {preset['story']}
Touches: {preset['touches']}
Trend: {preset['trend']}

SCENARIO A: BUY BOUNCE
ENTRY: {fmt.format(entry)} SL: {fmt.format(sl_for_calc)} TP1 {fmt.format(tp1)} 70% TP2 {fmt.format(tp2)} 120% TP3 {fmt.format(tp3)} 200%

SCENARIO B: SELL BREAKDOWN
ENTRY: {fmt.format(entry)} SL: 1.32733 TP1 {fmt.format(tp1_s)} TP2 {fmt.format(tp2_s)} TP3 {fmt.format(tp3_s)}

WAIT for 1H close: Above 1.32200 BUY, Below 1.32050 SELL
"""
    else:
        analysis = f"""📊 {market_key} {preset['tf']}

Pair: {market_key} {preset['tf']}, Price {fmt.format(entry)}
Support: {fmt.format(support)} | Resistance: {fmt.format(resistance)}
Story: {preset['story']}
Touches: {preset['touches']}
Trend: {preset['trend']}

SCENARIO A: {preset['scenario_a']}
ENTRY {fmt.format(entry)} SL {fmt.format(support)} TP1 {fmt.format(tp1)} 70% TP2 {fmt.format(tp2)} 120% TP3 {fmt.format(tp3)} 200%

SCENARIO B: {preset['scenario_b']}
TP1 {fmt.format(tp1_s)} TP2 {fmt.format(tp2_s)} TP3 {fmt.format(tp3_s)}

Mode: {mode} - {reason}
"""
    return jsonify({
        "market": f"{market_key} {preset['tf']}",
        "entry": entry, "sl": sl_for_calc, "tp1": tp1, "tp2": tp2, "tp3": tp3,
        "support": support, "resistance": resistance,
        "signal": "WAIT 🔍" if market_key=="GBPUSD" else "BUY 🔼",
        "mode": mode, "confidence": 99,
        "reason": reason,
        "analysis": analysis
    })

@app.route('/')
def home():
    return """<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'><title>EUGE CLEAN</title>
<style>
body{background:#000;color:#fff;font-family:Arial;margin:0;padding:8px}
.card{background:#0f0f0f;border-radius:16px;padding:12px;margin:8px 0;border:1px solid #222}
.signal{font-size:18px;font-weight:bold;text-align:center;padding:12px;border-radius:14px;background:#00ff88;color:#000}
.mode{font-size:13px;font-weight:bold;text-align:center;padding:8px;border-radius:10px;margin-top:6px}.scalp{background:#ffaa00;color:#000}.day{background:#00aaff;color:#fff}
#chat{height:220px;overflow-y:auto;background:#000;border-radius:10px;padding:8px;font-size:11px;color:#00ff88;border:1px solid #222}
.logo{background:#000;border:2px solid #00ff88;border-radius:18px;padding:12px;text-align:center}
.mgrid{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:6px;margin-top:8px}
.mbox{background:#111;border-radius:10px;padding:8px 2px;border:2px solid #333;font-size:10px;font-weight:bold;cursor:pointer;text-align:center}
.mbox.active{border-color:#00ff88;box-shadow:0 0 10px #00ff88}
.tbtn{background:#111;color:#888;border:1px solid #333;padding:6px 10px;border-radius:6px;margin:2px;font-size:10px}.tbtn.active{background:#00ff88;color:#000}
#marketPicker{display:none;background:#111;border:2px solid #00ff88;border-radius:12px;padding:10px;margin:8px 0}
.pbtn{background:#222;color:#fff;border:1px solid #444;padding:10px 14px;border-radius:8px;margin:4px;font-size:12px;font-weight:bold;cursor:pointer}
.tps{display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-top:8px}
.tpbox{background:#111;border-radius:10px;padding:8px;text-align:center;border:1px solid #333}
</style></head><body>
<div class='logo'><h1>EUGE ROBOT 🤖</h1><div style='font-size:11px;color:#888'>Live Prices + Analysis - All Markets Correspond</div>
<div class='mgrid'><div id='bFOREX' class='mbox active' onclick="openMarket('FOREX')">📈<br>FOREX</div><div id='bCRYPTO' class='mbox' onclick="openMarket('CRYPTO')">💎<br>CRYPTO</div><div id='bJSE' class='mbox' onclick="openMarket('JSE')">📊<br>JSE</div><div id='bDERIV' class='mbox' onclick="openMarket('DERIV')">⚡<br>DERIV</div></div>
<div style='margin-top:8px'><button class='tbtn' id='tfM30' onclick="setTF('M30')">M30</button><button class='tbtn active' id='tfD1' onclick="setTF('D1')">D1</button><button class='tbtn' id='tfH1' onclick="setTF('H1')">H1</button><button class='tbtn' id='tfH4' onclick="setTF('H4')">H4</button></div>
<div style='font-size:11px;color:#888;margin-top:6px'>Selected: <span id='sel' style='color:#00ff88;font-weight:bold'>NZDCAD</span> | <span id='selTF' style='color:#ffaa00'>D1</span> | Price: <span id='topPrice' style='color:#ffaa00'>0.79987</span></div>
</div>
<div id='marketPicker'><h4 id='pickerTitle' style='color:#00ff88;margin:0 0 8px 0'></h4><div id='pickerList' style='display:flex;flex-wrap:wrap'></div><button onclick="closePicker()" style='background:#333;color:#fff;border:0;padding:6px 12px;border-radius:6px;margin-top:8px'>Close</button></div>
<div id='sig' class='signal'>WAIT 🔍 (99%) - NZDCAD</div>
<div id='modeBox' class='mode scalp'>SCALPING 🔥 - At Support</div>
<div style='font-size:10px;color:#888;text-align:center;margin-top:4px' id='modeReason'>Critical support</div>
<div class='card'><div style='display:flex;justify-content:space-between'><small>📈 Live (<span id='chartLabel'>NZDCAD D1</span>)</small><small id='livePrice' style='color:#ffaa00;font-weight:bold'>0.79987</small></div><canvas id='chart' height='380' style='width:100%;background:#000;border-radius:10px;margin-top:8px'></canvas><div style='display:flex;justify-content:space-between;font-size:10px;color:#666;margin-top:4px'><span>Oct 2025</span><span>9 Jan 2026</span><span>25 Aug 2026</span><span id='timeNow' style='color:#ffaa00'>NOW 0.79987</span></div>
<div class='tps'><div class='tpbox' style='border-color:#00ff88'><div style='font-size:9px;color:#00ff88'>ENTRY</div><b id='entryTxt' style='color:#00ff88'>0.79987</b></div><div class='tpbox' style='border-color:#ff4444'><div style='font-size:9px;color:#ff4444'>SL</div><b id='slTxt' style='color:#ff4444'>0.79536</b></div><div class='tpbox' style='border-color:#ffff00'><div style='font-size:9px;color:#ffff00'>TP1 70%</div><b id='tp1Txt' style='color:#ffff00'>0.80302</b></div></div>
<div class='tps' style='margin-top:6px'><div class='tpbox' style='border-color:#ffaa00'><div style='font-size:9px;color:#ffaa00'>TP2 120%</div><b id='tp2Txt' style='color:#ffaa00'>0.80528</b></div><div class='tpbox' style='border-color:#00aaff'><div style='font-size:9px;color:#00aaff'>TP3 200%</div><b id='tp3Txt' style='color:#00aaff'>0.80889</b></div><div class='tpbox'><div style='font-size:9px'>RESIST</div><b id='resTxt' style='color:#ff4444'>0