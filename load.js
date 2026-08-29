let frame=null;
let paused=false;
const canvas=document.getElementById("c");
const ctx=canvas?canvas.getContext("2d"):null;
const hudEl=document.getElementById("hud");
let W=0,H=0,cx=0,cy=0;
let holding=false;
let holdTimer=null;
let lastMX=0,lastMY=0;
let mouseX=0,mouseY=0;
let diskAngle=0;
const DISK_TILT=0.22;
const TWO_PI=Math.PI*2;
let bgCanvas=null;
let bgW=0,bgH=0;

function resize(){
if(!canvas)return;
W=window.innerWidth;
H=window.innerHeight;
canvas.width=W;
canvas.height=H;
cx=W/2;cy=H/2;
bgCanvas=null;}
resize();
window.addEventListener("resize",resize);

async function pyCall(method){
if(!window.pywebview||!pywebview.api)return null;
try{return await pywebview.api[method]()}
catch(e){return null}}

async function pyCall1(method,a){
if(!window.pywebview||!pywebview.api)return null;
try{return await pywebview.api[method](a)}
catch(e){return null}






}

async function pyCall3(method,a,b,c){
if(!window.pywebview||!pywebview.api)return null;
try{return await pywebview.api[method](a,b,c)}
catch(e){return null}}
async function pollFrame(){
let d=await pyCall("get_frame");
if(d!=null&&d!=undefined){
try{frame=JSON.parse(d)}catch(e){}
}
setTimeout(pollFrame,16);}
pollFrame();
canvas.addEventListener("click",function(e){
let sx=e.clientX-cx;
let sy=e.clientY-cy;
pyCall3("add_mass_at",sx,sy,1.0);
});

canvas.addEventListener("mousedown",function(e){
if(e.button===0){
holding=true;
lastMX=e.clientX;lastMY=e.clientY;
holdTimer=setInterval(function(){
if(holding)pyCall3("add_mass_at",lastMX-cx,lastMY-cy,0.4);},70);}
});
canvas.addEventListener("mousemove",function(e){
lastMX=e.clientX;lastMY=e.clientY;
mouseX=e.clientX;mouseY=e.clientY;
});
window.addEventListener("mouseup",function(){
holding=false;
if(holdTimer){clearInterval(holdTimer);holdTimer=null}})
    ;
window.addEventListener("wheel",function(e){
let d=e.deltaY>0?-0.02:0.02;
pyCall1("adjust_spin",d);});

function togglePause(){
paused=!paused;
pyCall1("set_paused",paused);
document.getElementById("pbtn").textContent=paused?"play":"pause";}
function kill(){pyCall("stop_sim")}

function clamp(v,lo,hi){if(v<lo)return lo;if(v>hi)return hi;return v



}
function lerp(a,b,t){return a+(b-a)*clamp(t,0,1)}

function tempToRGB(t)
{
t=clamp(t,0,1);
let r,g,b;
if(t<0.15){let f=t/0.15;r=lerp(15,140,f);g=lerp(3,15,f);b=lerp(30,50,f)}
else if(t<0.35){let f=(t-0.15)/0.2;r=lerp(140,220,f);g=lerp(15,50,f);b=lerp(50,30,f)}
else if(t<0.55){let f=(t-0.35)/0.2;r=lerp(220,255,f);g=lerp(50,130,f);b=lerp(30,15,f)}
else if(t<0.75){let f=(t-0.55)/0.2;r=255;g=lerp(130,210,f);b=lerp(15,50,f)}
else{let f=(t-0.75)/0.25;r=lerp(255,230,f);g=lerp(210,240,f);b=lerp(50,200,f)}
return[Math.floor(r),Math.floor(g),Math.floor(b)];
}

function heatToColor(w,k){
if(k===1){let b=Math.floor(160+95*w);return[130,b,255]}
if(k===2)return[180,150,110];
let r=Math.floor(180+75*w);
let g=Math.floor(80+175*w);
let b=Math.floor(30+225*w);
return[r,g,b];}

function starHueColor(h){
if(h<0.2)return[160,185,255];
if(h<0.4)return[200,210,255];
if(h<0.6)return[255,245,220];
if(h<0.8)return[255,210,160];
return[255,170,130];
}

function rgba(r,g,b,a){return"rgba("+r+","+g+","+b+","+a+")"}

function buildBgCanvas(){
if(W===0||H===0)return;
bgCanvas=document.createElement("canvas");
bgW=W;bgH=H;
bgCanvas.width=W;
bgCanvas.height=H;
let bgCtx=bgCanvas.getContext("2d");
bgCtx.fillStyle="#030408";
bgCtx.fillRect(0,0,W,H);
let bg=bgCtx.createRadialGradient(cx,cy,0,cx,cy,Math.max(W,H)*0.6);
bg.addColorStop(0,"rgba(8,10,22,1)");
bg.addColorStop(0.5,"rgba(4,5,12,1)");
bg.addColorStop(1,"rgba(2,2,5,1)");
bgCtx.fillStyle=bg;
bgCtx.fillRect(0,0,W,H);
let neb=bgCtx.createRadialGradient(W*0.3,H*0.4,0,W*0.3,H*0.4,W*0.35);
neb.addColorStop(0,"rgba(15,8,30,0.12)");
neb.addColorStop(1,"rgba(0,0,0,0)");
bgCtx.fillStyle=neb;
bgCtx.fillRect(0,0,W,H);
let neb2=bgCtx.createRadialGradient(W*1.3,H*1.1,0,W*1.3,H*1.1,W*0.3);
neb2.addColorStop(0,"rgba(8,12,25,0.1)");
neb2.addColorStop(1,"rgba(0,0,0,0)");
bgCtx.fillStyle=neb2;
bgCtx.fillRect(0,0,W,H);
let seed=42;
function pr(){seed=(seed*16807)%2147483647;return seed/2147483647}
for(let i=0;i<400;i++){
let x=pr()*W;
let y=pr()*H;
let br=pr()*0.1+0.015;
let sz=pr()*0.8+0.2;
let hue=pr();
let sr,sg,sb;
if(hue<0.25){sr=170;sg=190;sb=255}
else if(hue<0.5){sr=210;sg=215;sb=250}
else if(hue<0.75){sr=255;sg=240;sb=210}
else{sr=255;sg=190;sb=160}
bgCtx.beginPath();bgCtx.arc(x,y,sz,0,TWO_PI);
bgCtx.fillStyle="rgba("+sr+","+sg+","+sb+","+br+")";
bgCtx.fill();
if(br>0.08){
bgCtx.beginPath();bgCtx.arc(x,y,sz*3,0,TWO_PI);
bgCtx.fillStyle="rgba("+sr+","+sg+","+sb+","+(br*0.06)+")";
bgCtx.fill();
}
}
}

function drawCachedBg(){
if(!bgCanvas||bgW!==W||bgH!==H){
buildBgCanvas();
}
ctx.drawImage(bgCanvas,0,0,W,H);
}

function drawStars(stars){
for(let i=0;i<stars.length;i++){
let s=stars[i];
let px=cx+s.x;
let py=cy+s.y;
if(px<-5||px>W+5||py<-5||py>H+5)continue;
let a=Math.min(s.b,1.5);
if(s.c)a*=0.5;
let col=starHueColor(s.h);
let sz=s.s;
if(sz>1.2){
ctx.beginPath();ctx.arc(px,py,sz*2.5,0,TWO_PI);
ctx.fillStyle=rgba(col[0],col[1],col[2],a*0.04);ctx.fill();
}
ctx.beginPath();ctx.arc(px,py,sz,0,TWO_PI);
ctx.fillStyle=rgba(col[0],col[1],col[2],a*0.85);ctx.fill();
if(s.b>0.8&&!s.c){
ctx.beginPath();ctx.arc(px,py,sz*4,0,TWO_PI);
ctx.fillStyle=rgba(col[0],col[1],col[2],a*0.02);ctx.fill();
}
}
}

function drawRays(rays){
if(!rays)return;
for(let i=0;i<rays.length;i++){
let ray=rays[i];
let pts=ray.p;
if(pts.length<2)continue;
ctx.beginPath();
ctx.moveTo(cx+pts[0][0],cy+pts[0][1]);
for(let j=1;j<pts.length;j++){
ctx.lineTo(cx+pts[j][0],cy+pts[j][1]);
}
let al=ray.x?0.09:0.025;
ctx.strokeStyle="rgba(120,155,255,"+al+")";
ctx.lineWidth=0.4;ctx.stroke();
}
}

function drawDiskGlow(core){
if(!core||!frame)return;
let rings=frame.d;
if(rings.length<2)return;
let outerR=rings[rings.length-1].r;
let px=cx+core.x;
let py=cy+core.y;
ctx.save();ctx.translate(px,py);ctx.scale(1,DISK_TILT);
let g=ctx.createRadialGradient(0,0,core.rs*0.8,0,0,outerR*1.8);
g.addColorStop(0,"rgba(255,160,60,0.08)");
g.addColorStop(0.3,"rgba(255,120,40,0.04)");
g.addColorStop(0.6,"rgba(200,80,30,0.015)");
g.addColorStop(1,"rgba(0,0,0,0)");
ctx.beginPath();ctx.arc(0,0,outerR*1.8,0,TWO_PI);
ctx.fillStyle=g;ctx.fill();
ctx.restore();
let g2=ctx.createRadialGradient(px,py,core.rs,px,py,outerR*2.5);
g2.addColorStop(0,"rgba(255,200,100,0.03)");
g2.addColorStop(0.4,"rgba(255,150,70,0.01)");
g2.addColorStop(1,"rgba(0,0,0,0)");
ctx.beginPath();ctx.arc(px,py,outerR*2.5,0,TWO_PI);
ctx.fillStyle=g2;ctx.fill();
}

function drawDiskRings(rings,core){
if(!rings||!core)return;
let px=cx+core.x;
let py=cy+core.y;
diskAngle+=0.002;
for(let i=0;i<rings.length;i++){
let ring=rings[i];
let r=ring.r;
let temp=ring.t;
let col=tempToRGB(temp);
let a=Math.min(temp*0.12,0.08);
ctx.save();ctx.translate(px,py);ctx.scale(1,DISK_TILT);
ctx.beginPath();ctx.arc(0,0,r,0,TWO_PI);
ctx.strokeStyle=rgba(col[0],col[1],col[2],a);
ctx.lineWidth=1.5;ctx.stroke();
if(temp>0.25){
ctx.beginPath();ctx.arc(0,0,r,0,TWO_PI);
ctx.strokeStyle=rgba(col[0],col[1],col[2],a*0.25);
ctx.lineWidth=6;ctx.stroke();
}
if(temp>0.5){
ctx.beginPath();ctx.arc(0,0,r,0,TWO_PI);
ctx.strokeStyle=rgba(col[0],col[1],col[2],a*0.08);
ctx.lineWidth=14;ctx.stroke();
}
ctx.restore();
}
}

function drawDopplerDisk(rings,core){
if(!rings||!core||rings.length<4)return;
let px=cx+core.x;
let py=cy+core.y;
let innerR=rings[0].r;
let outerR=rings[rings.length-1].r;
let segments=120;
for(let i=0;i<segments;i++){
let angle1=(i/segments)*TWO_PI+diskAngle;
let angle2=((i+1)/segments)*TWO_PI+diskAngle;
let midAngle=(angle1+angle2)/2;
let rFrac=0.5+0.5*Math.sin(midAngle*3+diskAngle*5);
let r=innerR+rFrac*(outerR-innerR);
let idx=clamp(Math.floor(rFrac*(rings.length-1)),0,rings.length-1);
let temp=rings[idx].t;
let col=tempToRGB(temp);
let doppler=0.6+0.4*Math.cos(midAngle);
let a=Math.min(temp*0.06,0.04)*doppler;
let x1=px+r*Math.cos(angle1);
let y1=py+r*Math.sin(angle1)*DISK_TILT;
let x2=px+r*Math.cos(angle2);
let y2=py+r*Math.sin(angle2)*DISK_TILT;
ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);
ctx.strokeStyle=rgba(col[0],col[1],col[2],a);
ctx.lineWidth=3;ctx.stroke();
}
}

function drawDiskWarpBack(rings,core){
if(!rings||!core||rings.length<2)return;
let px=cx+core.x;
let py=cy+core.y;
let innerR=rings[0].r;
let outerR=rings[rings.length-1].r;
let segments=80;
for(let i=0;i<segments;i++){
let angle1=Math.PI+(i/segments)*Math.PI+diskAngle*0.5;
let angle2=Math.PI+((i+1)/segments)*Math.PI+diskAngle*0.5;
let midAngle=(angle1+angle2)/2;
let rFrac=0.3+0.7*((Math.sin(midAngle*2)+1)/2);
let r=innerR+rFrac*(outerR-innerR);
let idx=clamp(Math.floor(rFrac*(rings.length-1)),0,rings.length-1);
let temp=rings[idx].t*0.7;
let col=tempToRGB(temp);
let warp=core.rs*0.8*(1-rFrac);
let x1=px+r*Math.cos(angle1);
let y1=py-r*Math.sin(angle1)*DISK_TILT*0.5-warp;
let x2=px+r*Math.cos(angle2);
let y2=py-r*Math.sin(angle2)*DISK_TILT*0.5-warp;
let a=Math.min(temp*0.04,0.025);
ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);
ctx.strokeStyle=rgba(col[0],col[1],col[2],a);
ctx.lineWidth=2;ctx.stroke();
}
}

function drawJetGlow(core){
if(!core||core.m<3)return;
let px=cx+core.x;
let py=cy+core.y;
let intensity=clamp((core.m-3)*0.025,0,0.12);
let jetLen=core.rs*18;
let spread=6+core.m*0.5;
let topG=ctx.createLinearGradient(px,py,px,py-jetLen);
topG.addColorStop(0,"rgba(100,140,255,"+intensity+")");
topG.addColorStop(0.15,"rgba(90,130,255,"+(intensity*0.5)+")");
topG.addColorStop(0.4,"rgba(80,120,255,"+(intensity*0.15)+")");
topG.addColorStop(1,"rgba(60,100,255,0)");
ctx.beginPath();
ctx.moveTo(px-spread,py);ctx.lineTo(px+spread,py);
ctx.lineTo(px+2,py-jetLen);ctx.lineTo(px-2,py-jetLen);
ctx.closePath();ctx.fillStyle=topG;ctx.fill();
let topCore=ctx.createLinearGradient(px,py,px,py-jetLen*0.3);
topCore.addColorStop(0,"rgba(180,200,255,"+(intensity*0.4)+")");
topCore.addColorStop(1,"rgba(120,160,255,0)");
ctx.beginPath();
ctx.moveTo(px-2,py);ctx.lineTo(px+2,py);
ctx.lineTo(px+0.5,py-jetLen*0.3);ctx.lineTo(px-0.5,py-jetLen*0.3);
ctx.closePath();ctx.fillStyle=topCore;ctx.fill();
let botG=ctx.createLinearGradient(px,py,px,py+jetLen);
botG.addColorStop(0,"rgba(100,140,255,"+intensity+")");
botG.addColorStop(0.15,"rgba(90,130,255,"+(intensity*0.5)+")");
botG.addColorStop(0.4,"rgba(80,120,255,"+(intensity*0.15)+")");
botG.addColorStop(1,"rgba(60,100,255,0)");
ctx.beginPath();
ctx.moveTo(px-spread,py);ctx.lineTo(px+spread,py);
ctx.lineTo(px+2,py+jetLen);ctx.lineTo(px-2,py+jetLen);
ctx.closePath();ctx.fillStyle=botG;ctx.fill();
let botCore=ctx.createLinearGradient(px,py,px,py+jetLen*0.3);
botCore.addColorStop(0,"rgba(180,200,255,"+(intensity*0.4)+")");
botCore.addColorStop(1,"rgba(120,160,255,0)");
ctx.beginPath();
ctx.moveTo(px-2,py);ctx.lineTo(px+2,py);
ctx.lineTo(px+0.5,py+jetLen*0.3);ctx.lineTo(px-0.5,py+jetLen*0.3);
ctx.closePath();ctx.fillStyle=botCore;ctx.fill();
}

function drawRipples(rips){
if(!rips)return;
for(let i=0;i<rips.length;i++){
let rp=rips[i];
ctx.beginPath();ctx.arc(cx+rp.x,cy+rp.y,rp.r,0,TWO_PI);
ctx.strokeStyle="rgba(90,140,255,"+(rp.a*0.3)+")";
ctx.lineWidth=0.8;ctx.stroke();
if(rp.a>0.1){
ctx.beginPath();ctx.arc(cx+rp.x,cy+rp.y,rp.r,0,TWO_PI);
ctx.strokeStyle="rgba(90,140,255,"+(rp.a*0.08)+")";
ctx.lineWidth=4;ctx.stroke();
}
}
}

function drawTrails(particles){
for(let i=0;i<particles.length;i++){
let p=particles[i];
let tr=p.t;
if(tr.length<2)continue;
let col=heatToColor(p.w,p.k);
for(let j=1;j<tr.length;j++){
let prev=tr[j-1];
let curr=tr[j];
let alpha=curr[2]*(j/tr.length)*0.2;
if(alpha<0.005)continue;
ctx.beginPath();
ctx.moveTo(cx+prev[0],cy+prev[1]);
ctx.lineTo(cx+curr[0],cy+curr[1]);
ctx.strokeStyle=rgba(col[0],col[1],col[2],alpha);
ctx.lineWidth=p.s*0.5;ctx.stroke();
}
}
}

function drawParticles(particles){
for(let i=0;i<particles.length;i++){
let p=particles[i];
let px=cx+p.x;
let py=cy+p.y;
if(px<-10||px>W+10||py<-10||py>H+10)continue;
let col=heatToColor(p.w,p.k);
let a=clamp(p.b,0,1);
ctx.beginPath();ctx.arc(px,py,p.s,0,TWO_PI);
ctx.fillStyle=rgba(col[0],col[1],col[2],a);ctx.fill();
if(p.w>0.5&&p.b>0.4&&p.k!==2){
ctx.beginPath();ctx.arc(px,py,p.s*3.5,0,TWO_PI);
ctx.fillStyle=rgba(col[0],col[1],col[2],a*0.04);ctx.fill();
}
if(p.k===1&&p.b>0.3){
ctx.beginPath();ctx.arc(px,py,p.s*5,0,TWO_PI);
ctx.fillStyle="rgba(120,160,255,"+(a*0.02)+")";ctx.fill();
}
}
}

function drawBlobs(blobList){
if(!blobList)return;
for(let i=0;i<blobList.length;i++){
let b=blobList[i];
let px=cx+b.x;
let py=cy+b.y;
let r=b.r;
let pulse=1+0.05*Math.sin(performance.now()*0.003+b.h*10);
let dr=r*pulse;
let g=ctx.createRadialGradient(px,py,0,px,py,dr*2.5);
let cr,cg,cb;
if(b.h<0.33){cr=255;cg=180;cb=100}
else if(b.h<0.66){cr=180;cg=210;cb=255}
else{cr=170;cg=255;cb=170}
g.addColorStop(0,rgba(cr,cg,cb,0.12));
g.addColorStop(0.5,rgba(cr,cg,cb,0.03));
g.addColorStop(1,rgba(cr,cg,cb,0));
ctx.beginPath();ctx.arc(px,py,dr*2.5,0,TWO_PI);
ctx.fillStyle=g;ctx.fill();
ctx.beginPath();ctx.arc(px,py,dr,0,TWO_PI);
ctx.fillStyle=rgba(cr,cg,cb,0.3);ctx.fill();
ctx.strokeStyle=rgba(cr,cg,cb,0.5);
ctx.lineWidth=0.8;ctx.stroke();
ctx.beginPath();ctx.arc(px,py,dr*0.4,0,TWO_PI);
ctx.fillStyle=rgba(255,255,255,0.1);ctx.fill();
}
}

function drawBlackHole(core){
if(!core)return;
let px=cx+core.x;
let py=cy+core.y;
let rs=core.rs;
let ps=core.ps;
let isco=core.isco;
for(let i=8;i>=0;i--){
let gr=rs*(2+i*1.2);
let al=0.03-i*0.003;
ctx.beginPath();ctx.arc(px,py,gr,0,TWO_PI);
ctx.fillStyle="rgba(40,50,100,"+Math.max(al,0.001)+")";
ctx.fill();
}
ctx.beginPath();ctx.arc(px,py,isco,0,TWO_PI);
ctx.strokeStyle="rgba(100,130,255,0.02)";
ctx.lineWidth=0.4;
ctx.setLineDash([4,8]);ctx.stroke();ctx.setLineDash([]);
ctx.beginPath();ctx.arc(px,py,ps,0,TWO_PI);
ctx.strokeStyle="rgba(200,215,255,0.07)";
ctx.lineWidth=1;ctx.stroke();
ctx.beginPath();ctx.arc(px,py,ps+1.5,0,TWO_PI);
ctx.strokeStyle="rgba(200,215,255,0.015)";
ctx.lineWidth=3;ctx.stroke();
let photonGlow=ctx.createRadialGradient(px,py,ps*0.9,px,py,ps*1.4);
photonGlow.addColorStop(0,"rgba(220,230,255,0.1)");
photonGlow.addColorStop(0.4,"rgba(180,200,255,0.04)");
photonGlow.addColorStop(1,"rgba(0,0,0,0)");
ctx.beginPath();ctx.arc(px,py,ps*1.4,0,TWO_PI);
ctx.fillStyle=photonGlow;ctx.fill();
let shadow=ctx.createRadialGradient(px,py,rs*0.1,px,py,rs*1.2);
shadow.addColorStop(0,"rgba(0,0,0,1)");
shadow.addColorStop(0.75,"rgba(0,0,0,0.99)");
shadow.addColorStop(0.92,"rgba(0,0,0,0.7)");
shadow.addColorStop(1,"rgba(0,0,0,0)");
ctx.beginPath();ctx.arc(px,py,rs*1.2,0,TWO_PI);
ctx.fillStyle=shadow;ctx.fill();
ctx.beginPath();ctx.arc(px,py,rs*1.02,0,TWO_PI);
ctx.fillStyle="#000";ctx.fill();
ctx.beginPath();ctx.arc(px,py,rs*1.02,0,TWO_PI);
ctx.strokeStyle="rgba(0,0,0,0.9)";
ctx.lineWidth=2;ctx.stroke();
let edge=ctx.createRadialGradient(px,py,rs*0.8,px,py,rs*1.1);
edge.addColorStop(0,"rgba(0,0,0,0)");
edge.addColorStop(0.6,"rgba(0,0,0,0)");
edge.addColorStop(0.85,"rgba(25,30,50,0.12)");
edge.addColorStop(1,"rgba(0,0,0,0)");
ctx.beginPath();ctx.arc(px,py,rs*1.1,0,TWO_PI);
ctx.fillStyle=edge;ctx.fill();
}

function drawHUD(info){
if(!info||!hudEl)return;
let lines=[];
lines.push("particles "+info.np);
lines.push("blobs "+info.nb);
lines.push("T_h "+info.ht);
lines.push("L_h "+info.hl);
lines.push("tidal "+info.td);
lines.push("edd "+info.edd);
if(info.qnm)lines.push("qnm "+info.qnm);
lines.push("t "+info.tm);
if(info.lg){
for(let i=0;i<info.lg.length;i++){
lines.push("> "+info.lg[i]);
}
}
hudEl.textContent=lines.join("\n");
}

function drawVignette(){
let g=ctx.createRadialGradient(cx,cy,Math.min(W,H)*0.35,cx,cy,Math.max(W,H)*0.7);
g.addColorStop(0,"rgba(0,0,0,0)");
g.addColorStop(1,"rgba(0,0,0,0.35)");
ctx.fillStyle=g;ctx.fillRect(0,0,W,H);
}

function drawScanlines(){
ctx.fillStyle="rgba(0,0,0,0.025)";
for(let y=0;y<H;y+=3){
ctx.fillRect(0,y,W,1);
}
}

function drawCrosshair(){
let a=paused?0.15:0.04;
ctx.strokeStyle="rgba(255,255,255,"+a+")";
ctx.lineWidth=0.5;
ctx.beginPath();
ctx.moveTo(mouseX-8,mouseY);ctx.lineTo(mouseX-3,mouseY);
ctx.moveTo(mouseX+3,mouseY);ctx.lineTo(mouseX+8,mouseY);
ctx.moveTo(mouseX,mouseY-8);ctx.lineTo(mouseX,mouseY-3);
ctx.moveTo(mouseX,mouseY+3);ctx.lineTo(mouseX,mouseY+8);
ctx.stroke();
}
function render(){
if(!ctx||!canvas)return;
if(W===0||H===0){requestAnimationFrame(render);return}
drawCachedBg();
if(!frame){
ctx.fillStyle="rgba(255,255,255,0.08)";
ctx.font="13px monospace";
ctx.textAlign="center";
ctx.fillText("connecting...",cx,cy);
requestAnimationFrame(render);
return;
}
let core=frame.c;
let stars=frame.s;
let rays=frame.y;
let disk=frame.d;
let rips=frame.r;
let parts=frame.m;
let blobs=frame.b;
let info=frame.i;
drawStars(stars);
if(rays)drawRays(rays);
drawDiskGlow(core);
drawDiskWarpBack(disk,core);
drawDiskRings(disk,core);
drawDopplerDisk(disk,core);
drawJetGlow(core);
drawRipples(rips);
drawTrails(parts);
drawParticles(parts);
drawBlobs(blobs);
drawBlackHole(core);
drawVignette();
drawScanlines();
drawCrosshair();
drawHUD(info);
requestAnimationFrame(render);
}
render();