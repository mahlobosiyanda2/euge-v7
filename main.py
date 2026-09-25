function draw(d){
 let c=document.getElementById('chart'),x=c.getContext('2d');
 c.width=c.clientWidth; c.height=420;
 x.clearRect(0,0,c.width,c.height);
 let cs=d.candles;
 if(cs.length<2) return;
 let min=Math.min(...cs.map(v=>v.l), d.support, d.resistance)*0.999;
 let max=Math.max(...cs.map(v=>v.h), d.support, d.resistance)*1.001;
 let range=max-min || 0.001;
 let H=c.height-50, W=c.width-70;
 // Grid
 x.strokeStyle='#1a1a1a'; x.lineWidth=0.5;
 for(let i=0;i<6;i++){let y=i*H/6; x.beginPath(); x.moveTo(0,y); x.lineTo(W,y); x.stroke(); let price=max-(i/6)*range; x.fillStyle='#888'; x.font='10px Arial'; x.fillText(price.toFixed(d.dec), W+5, y+4);}
 // Support
 let supY=H - ((d.support-min)/range*H);
 x.strokeStyle='#00ff88'; x.setLineDash([5,5]); x.lineWidth=1.5; x.beginPath(); x.moveTo(0,supY); x.lineTo(W,supY); x.stroke(); x.setLineDash([]);
 x.fillStyle='#00ff88'; x.fillRect(W-2,supY-12,62,14); x.fillStyle='#000'; x.font='bold 10px Arial'; x.fillText('SUP '+d.support.toFixed(d.dec), W+2, supY-2);
 // Resistance
 let resY=H - ((d.resistance-min)/range*H);
 x.strokeStyle='#ff4444'; x.setLineDash([5,5]); x.beginPath(); x.moveTo(0,resY); x.lineTo(W,resY); x.stroke(); x.setLineDash([]);
 x.fillStyle='#ff4444'; x.fillRect(W-2,resY-12,62,14); x.fillStyle='#fff'; x.fillText('RES '+d.resistance.toFixed(d.dec), W+2, resY-2);
 // Candles - NO FLAT!
 let cw=Math.max(3, W/cs.length*0.7);
 cs.forEach((k,i)=>{
  let px=(i/(cs.length-1))*W;
  let oY=H - ((k.o-min)/range*H);
  let cY=H - ((k.c-min)/range*H);
  let hY=H - ((k.h-min)/range*H);
  let lY=H - ((k.l-min)/range*H);
  let green=k.c>=k.o;
  x.strokeStyle=green?'#00ff88':'#ff4444'; x.lineWidth=1;
  x.beginPath(); x.moveTo(px,hY); x.lineTo(px,lY); x.stroke();
  x.fillStyle=green?'#00ff88':'#ff4444';
  let top=Math.min(oY,cY); let hg=Math.max(3,Math.abs(oY-cY));
  x.fillRect(px-cw/2,top,cw,hg);
 });
 // Live price label left
 x.fillStyle='#ffaa00'; x.font='bold 12px Arial'; x.fillText('LIVE '+d.price.toFixed(d.dec), 10, 16);
}