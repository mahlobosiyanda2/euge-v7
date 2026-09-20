import yfinance as yf, websocket, json, threading, time, os
from flask import Flask
from twilio.rest import Client
from datetime import datetime
import pytz
app=Flask(__name__)
TWILIO_SID=os.getenv("TWILIO_SID")
TWILIO_TOKEN=os.getenv("TWILIO_TOKEN")
MY_WA="whatsapp:+27671455798"
TWILIO_WA="whatsapp:+14155238886"
latest={"R_75":0,"BTCZAR":0}
sa_tz=pytz.timezone('Africa/Johannesburg')
BTCZAR_ZONE=1287075
def send_wa(t):
 try: Client(TWILIO_SID,TWILIO_TOKEN).messages.create(from_=TWILIO_WA,to=MY_WA,body=t)
 except Exception as e: print(e)
def market_watcher():
 a=False
 while True:
  try:
   b=yf.download("BTC-ZAR",period="1d",interval="5m")['Close'].iloc[-1]
   latest["BTCZAR"]=b
   if b<BTCZAR_ZONE and not a:
    send_wa(f"🚨 BTC/ZAR BROKE 1287075 -> {b:,.0f} SELL");a=True
   if b>BTCZAR_ZONE+50000 and a:
    send_wa(f"🔥 BTC/ZAR BOUNCE -> {b:,.0f} BUY");a=False
  except: pass
  time.sleep(300)
def jse_opener():
 d=False
 while True:
  now=datetime.now(sa_tz)
  if now.weekday()<5 and now.hour==9 and now.minute==0 and not d:
   try:
    m=yf.download("MTN.JO",period="1d",interval="1m")['Close'].iloc[-1]
    send_wa(f"🔔 JSE OPEN MTN:R{m:.2f} V75:{latest.get('R_75')} BTC:R{latest.get('BTCZAR',0):,.0f}");d=True
   except: pass
  if now.hour!=9: d=False
  time.sleep(60)
def deriv_listener():
 def on_message(ws,msg):
  dd=json.loads(msg)
  if 'tick' in dd:
   latest[dd['tick']['symbol']]=dd['tick']['quote']
   if dd['tick']['symbol']=="R_75" and dd['tick']['quote']<45500:
    send_wa(f"🚨 V75 BREAK 45816 -> {dd['tick']['quote']}")
 def on_open(ws):
  for s in ["R_75","BOOM1000","CRASH1000"]: ws.send(json.dumps({"ticks":s}))
 ws=websocket.WebSocketApp("wss://ws.derivws.com/websockets/v3?app_id=1089",on_message=on_message,on_open=on_open)
 ws.run_forever()
@app.route("/whatsapp",methods=['POST'])
def wa():
 from twilio.twiml.messaging_response import MessagingResponse
 r=MessagingResponse(); r.message(f"LIVE V75:{latest.get('R_75')} BTC:{latest.get('BTCZAR',0):,.0f}")
 return str(r)
if __name__=="__main__":
 threading.Thread(target=deriv_listener,daemon=True).start()
 threading.Thread(target=jse_opener,daemon=True).start()
 threading.Thread(target=market_watcher,daemon=True).start()
 app.run(host="0.0.0.0",port=5000)