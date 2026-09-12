let frame=null;
let paused=false;
let animationId=0;
let diskAngle=0;
let lastFrameAt=0;
let zoom=1;
let tZoom=1;
let panX=0;
let panY=0;
let velX=0;
let velY=0;
let panning=false;
let lastMX=0;
let lastMY=0;
const canvas=document.getElementById("c");
const ctx=canvas?canvas.getContext("2d"):null;
const hudEl=document.getElementById("hud");
const TWO_PI=Math.PI*2;
const FLAT=0.28;
let W=0;
let H=0;
let cx=0;
let cy=0;
let mouseX=0;
let mouseY=0;
let holding=false;
let holdTimer=null;
let background=null;
let tmp1=null; 

function clamp(v,low,high){
  return Math.max(low,Math.min(high,v));
}

function lerp(a,b,t){
  return a+(b-a)*clamp(t,0,1);
}

function rgba(r,g,b,a){
  return `rgba(${r},${g},${b},${a})`;
}

function seededRandom(seed){
  let value=seed|0;
  return function(){
    value=(value*1664525+1013904223)|0;
    return (value>>>0)/4294967296;
  };
}

function resize(){
  if(!canvas)return;
  W=window.innerWidth;
  H=window.innerHeight;
  canvas.width=W;
  canvas.height=H;
  cx=W*0.5;
  cy=H*0.5;
  background=null;
}

resize();
window.addEventListener("resize",resize);

async function pyCall(method,...args){
  const bridge=window.pywebview&&window.pywebview.api;
  if(!bridge||typeof bridge[method]!=="function")return null;

  try{
    return await bridge[method](...args);
  }catch(error){
    return null;
  }
}

async function pollFrame(){
  const next=await pyCall("get_frame");

  if(next!==null&&next!==undefined){
    try{
      frame=typeof next==="string"?JSON.parse(next):next;
      lastFrameAt=performance.now();
    }catch(error){}
  }

  window.setTimeout(pollFrame,38);
}

pollFrame();
function shadowRadius(core=null){
  const base=clamp(Math.min(W,H)*0.045,24,42);
  const mass=core&&Number.isFinite(Number(core.m))?Math.max(1,Number(core.m)):5;
  return clamp(base*Math.pow(mass/5,0.45),22,Math.min(W,H)*0.15)*zoom;
}

function nearScale(core){
  return shadowRadius(core)/Math.max(core&&core.rs?core.rs:0.05,0.0001);
}

function screenPoint(x,y){
  return[cx+panX+x*zoom,cy+panY+y*zoom];
}

function worldFromScreen(mx,my){
  return[(mx-cx-panX)/zoom,(my-cy-panY)/zoom];
}

function tempColor(v){
  const t=clamp(Number(v)||0,0,1);
  if(t<0.18){
    const f=t/0.18;
    return[Math.round(lerp(85,185,f)),Math.round(lerp(16,35,f)),Math.round(lerp(38,42,f))];
  }
  if(t<0.45){
    const f=(t-0.18)/0.27;
    return[Math.round(lerp(185,255,f)),Math.round(lerp(35,95,f)),Math.round(lerp(42,18,f))];
  }
  if(t<0.75){
    const f=(t-0.45)/0.3;
    return[255,Math.round(lerp(95,205,f)),Math.round(lerp(18,78,f))];
  }
  const f=(t-0.75)/0.25;
  return[255,Math.round(lerp(205,247,f)),Math.round(lerp(78,225,f))];
}

function starColor(h){
  if(h<0.23)return[170,200,255];
  if(h<0.48)return[215,225,255];
  if(h<0.72)return[255,246,220];
  return[255,192,145];
}

function buildBackground(){
  if(!ctx||W===0||H===0)return;

  background=document.createElement("canvas");
  background.width=W;
  background.height=H;

  const bg=background.getContext("2d");

  const base=bg.createRadialGradient(cx,cy,0,cx,cy,Math.max(W,H)*0.78);

  base.addColorStop(0,"#111326");
  base.addColorStop(0.42,"#070914");
  base.addColorStop(1,"#020207");

  bg.fillStyle=base;
  bg.fillRect(0,0,W,H);

  const violetCloud=bg.createRadialGradient(W*0.18,H*0.3,0,W*0.18,H*0.3,Math.max(W,H)*0.52);

  violetCloud.addColorStop(0,"rgba(78,47,133,0.16)");
  violetCloud.addColorStop(0.48,"rgba(35,26,76,0.06)");
  violetCloud.addColorStop(1,"rgba(0,0,0,0)");

  bg.fillStyle=violetCloud;
  bg.fillRect(0,0,W,H);

  const blueCloud=bg.createRadialGradient(W*0.86,H*0.78,0,W*0.86,H*0.78,Math.max(W,H)*0.44);

  blueCloud.addColorStop(0,"rgba(29,76,122,0.11)");
  blueCloud.addColorStop(0.5,"rgba(16,39,76,0.035)");
  blueCloud.addColorStop(1,"rgba(0,0,0,0)");

  bg.fillStyle=blueCloud;
  bg.fillRect(0,0,W,H);

  const random=seededRandom(71337);

  for(let i=0;i<520;i+=1){
    const x=random()*W;
    const y=random()*H;
    const size=0.25+random()*1.35;
    const brightness=0.12+random()*0.65;
    const color=starColor(random());

    bg.beginPath();
    bg.arc(x,y,size,0,TWO_PI);
    bg.fillStyle=rgba(color[0],color[1],color[2],brightness);
    bg.fill();

    if(size>1.05){
      bg.beginPath();
      bg.arc(x,y,size*4.5,0,TWO_PI);
      bg.fillStyle=rgba(color[0],color[1],color[2],brightness*0.035);
      bg.fill();
    }
  }
}

function drawBackground(){
  if(!background||background.width!==W||background.height!==H){
    buildBackground();
  }

  if(background){
    ctx.drawImage(background,0,0);
  }
}

function drawStars(stars){
  if(!stars)return;

  for(const star of stars){
    const[x,y]=screenPoint(star.x,star.y);

    if(x<-12||y<-12||x>W+12||y>H+12){
      continue;
    }

    const color=starColor(star.h||0);
    const brightness=clamp((star.b||0)*(star.c?0.7:1),0,1.5);
    const size=Math.max(0.35,(star.s||0.8)*Math.min(zoom,1.6));

    if(brightness>0.72){
      ctx.beginPath();
      ctx.arc(x,y,size*5.5,0,TWO_PI);
      ctx.fillStyle=rgba(color[0],color[1],color[2],brightness*0.035);
      ctx.fill();
    }

    ctx.beginPath();
    ctx.arc(x,y,size,0,TWO_PI);
    ctx.fillStyle=rgba(color[0],color[1],color[2],brightness*0.78);
    ctx.fill();
  }
}

function drawRays(rays){
  if(!rays)return;

  ctx.save();
  ctx.lineCap="round";

  for(const ray of rays){
    if(!ray.p||ray.p.length<2)continue;

    ctx.beginPath();
    ctx.moveTo(cx+panX+ray.p[0][0]*zoom,cy+panY+ray.p[0][1]*zoom);

    for(let i=1;i<ray.p.length;i+=1){
      ctx.lineTo(cx+panX+ray.p[i][0]*zoom,cy+panY+ray.p[i][1]*zoom);
    }

    ctx.strokeStyle=ray.x?"rgba(150,180,255,0.075)":"rgba(100,125,205,0.025)";

    ctx.lineWidth=ray.x?0.75:0.4;
    ctx.stroke();
  }

  ctx.restore();
}

function drawLensHalo(core){
  const[x,y]=screenPoint(core.x,core.y);
  const r=shadowRadius(core);

  ctx.save();
  ctx.translate(x,y);
  ctx.scale(1,0.98);

  const halo=ctx.createRadialGradient(0,0,r,0,0,r*3.2);

  halo.addColorStop(0,"rgba(120,154,255,0.15)");
  halo.addColorStop(0.24,"rgba(105,125,235,0.06)");
  halo.addColorStop(0.58,"rgba(73,74,180,0.025)");
  halo.addColorStop(1,"rgba(0,0,0,0)");

  ctx.beginPath();
  ctx.arc(0,0,r*3.2,0,TWO_PI);
  ctx.fillStyle=halo;
  ctx.fill();

  ctx.restore();
}

function drawDiskGlow(core,rings){
  if(!rings||rings.length<2)return;

  const[x,y]=screenPoint(core.x,core.y);
  const outer=clamp(rings[rings.length-1].r*nearScale(core),shadowRadius(core)*1.3,Math.max(W,H)*0.72);

  ctx.save();
  ctx.translate(x,y);
  ctx.scale(1,FLAT);

  const glow=ctx.createRadialGradient(0,0,outer*0.1,0,0,outer);

  glow.addColorStop(0,"rgba(255,128,26,0.075)");
  glow.addColorStop(0.25,"rgba(255,82,18,0.045)");
  glow.addColorStop(0.55,"rgba(195,40,40,0.018)");
  glow.addColorStop(1,"rgba(0,0,0,0)");

  ctx.beginPath();
  ctx.arc(0,0,outer,0,TWO_PI);
  ctx.fillStyle=glow;
  ctx.fill();

  ctx.restore();
}
//the horible mess i was refering 2
function drawRingHalf(core,ring,index,total,start,end,alphaScale){
  const scale=nearScale(core);
  const radius=clamp(ring.r*scale,shadowRadius(core)*1.12,Math.max(W,H)*0.9);
  const f=clamp(ring.f??index/Math.max(1,total-1),0,1);
  const temp=clamp(ring.t??(1-f)*0.8,0,1);

  const color=tempColor(temp);
  const rotation=diskAngle*(0.55+(1-f)*0.8);
  const beta=clamp(0.46*Math.pow(1-f,0.45),0.08,0.46);

  ctx.save();
  ctx.translate(cx+panX+core.x*zoom,cy+panY+core.y*zoom);
  ctx.scale(1,FLAT);
  ctx.lineCap="round";

  for(let i=0;i<26;i+=1){
    const a1=start+(i/26)*(end-start)+rotation;
    const a2=start+((i+1)/26)*(end-start)+rotation;
    const mid=(a1+a2)*0.5;

    const turb=Math.sin(mid*5+index*1.7+diskAngle*3)*0.032;
    const r=radius*(1+turb*(1-f));

    const approach=0.35+0.65*Math.pow(Math.max(0,Math.cos(mid-0.25)),2);

    const doppler=Math.pow((1+beta*Math.cos(mid-0.25))/Math.sqrt(1-beta*beta),3);

    const alpha=clamp((0.018+temp*0.16)*approach*doppler*alphaScale,0,0.42);
    const width=Math.max(1.0,4.4-f*2.5);

    ctx.beginPath();
    ctx.ellipse(0,0,r,r,0,a1,a2);
    ctx.strokeStyle=rgba(color[0],color[1],color[2],alpha);
    ctx.lineWidth=width;
    ctx.stroke();
  }

  ctx.restore();
}

function drawDisk(core,rings){
  if(!core||!rings||rings.length<2)return;

  drawDiskGlow(core,rings);

  const ringStep=Math.max(1,Math.ceil(rings.length/7));
  const nVisible=Math.ceil(rings.length/ringStep);
  const innerR=shadowRadius(core)*1.12;
  const outerR=clamp(rings[rings.length-1].r*nearScale(core),innerR*2.2,Math.max(W,H)*0.78);

  ctx.save();
  ctx.translate(cx+panX+core.x*zoom,cy+panY+core.y*zoom);
  ctx.scale(1,FLAT);

  const connected=ctx.createRadialGradient(0,0,innerR*0.72,0,0,outerR);

  connected.addColorStop(0,"rgba(255,130,28,0.08)");
  connected.addColorStop(0.18,"rgba(255,74,20,0.075)");
  connected.addColorStop(0.42,"rgba(201,38,35,0.032)");
  connected.addColorStop(0.72,"rgba(111,24,45,0.012)");
  connected.addColorStop(1,"rgba(0,0,0,0)");

  ctx.beginPath();
  ctx.ellipse(0,0,outerR,outerR,0,0,TWO_PI);
  ctx.fillStyle=connected;
  ctx.fill();
  ctx.restore();

  for(let i=0,v=0;i<rings.length;i+=ringStep,v+=1){
    drawRingHalf(core,rings[i],v,nVisible,Math.PI,TWO_PI,0.42);
  }

  const inner=rings[Math.min(ringStep,rings.length-1)];
  const innerBand=clamp(inner.r*nearScale(core),shadowRadius(core)*1.1,900);

  ctx.save();
  ctx.translate(cx+panX+core.x*zoom,cy+panY+core.y*zoom);
  ctx.scale(1,FLAT);

  ctx.beginPath();
  ctx.ellipse(0,0,innerBand*1.03,innerBand*1.03,0,0,TWO_PI);

  ctx.strokeStyle="rgba(255,205,116,0.08)";
  ctx.lineWidth=Math.max(1.5,shadowRadius(core)*0.055);
  ctx.stroke();
  ctx.restore();

  for(let i=0,v=0;i<rings.length;i+=ringStep,v+=1){
    drawRingHalf(core,rings[i],v,nVisible,0,Math.PI,0.82);
  }

  //5 brightness streaks riding along the disk, no idea why 5 works better than 4
  ctx.save();
  ctx.translate(cx+panX+core.x*zoom,cy+panY+core.y*zoom);
  ctx.scale(1,FLAT);
  ctx.lineCap="round";
  const scale=nearScale(core);
  for(let i=0;i<5;i+=1){
    const ringIndex=Math.min(rings.length-1,(i+1)*ringStep*2);
    const t=ringIndex/Math.max(1,rings.length-1);
    const radius=clamp(rings[ringIndex].r*scale,shadowRadius(core)*1.35,Math.max(W,H)*0.78);
    const angle=diskAngle*(0.3+t)+i*2.17;
    const sweep=0.055+(1-t)*0.08;
    const color=tempColor(0.3+(1-t)*0.65);
    ctx.beginPath();
    ctx.ellipse(0,0,radius,radius,0,angle,angle+sweep);
    ctx.strokeStyle=rgba(color[0],color[1],color[2],0.018+(1-t)*0.032);
    ctx.lineWidth=0.8+(1-t)*1.5;
    ctx.stroke();
  }
  ctx.restore();
}
function drawTrails(particles,core){
  if(!particles)return;
  const scale=nearScale(core);
  ctx.save();
  ctx.lineCap="round";
  for(let pi=0;pi<particles.length;pi+=2){
    const p=particles[pi];
    if(p.k!==0||!p.t||p.t.length<2){
      continue;
    }
    const color=tempColor(p.w);
    for(let i=2;i<p.t.length;i+=2){
      const prev=p.t[i-1];
      const cur=p.t[i];
      const fade=(i/p.t.length)*0.12*(cur[2]||1);
      ctx.beginPath();
      ctx.moveTo(cx+panX+(prev[0]-core.x)*scale,cy+panY+(prev[1]-core.y)*scale*FLAT);
      ctx.lineTo(cx+panX+(cur[0]-core.x)*scale,cy+panY+(cur[1]-core.y)*scale*FLAT);
      ctx.strokeStyle=rgba(color[0],color[1],color[2],fade);
      ctx.lineWidth=Math.max(0.45,(p.s||1)*0.48);
      ctx.stroke();
    }
  }
  ctx.restore();
}
function drawJets(core){
  if(!core||core.m<3)return;
  const[x,y]=screenPoint(core.x,core.y);
  const length=clamp(105+core.m*18,120,Math.min(H*0.7,440))*zoom;
  const width=clamp(10+core.m*0.8,12,30)*zoom;
  const pulse=0.84+Math.sin(performance.now()*0.0022)*0.16;
  function jet(dir){
    const endY=y+dir*length;
    const gradient=ctx.createLinearGradient(x,y,x,endY);
    gradient.addColorStop(0,`rgba(145,185,255,${0.22*pulse})`);
    gradient.addColorStop(0.16,`rgba(101,153,255,${0.10*pulse})`);
    gradient.addColorStop(0.55,"rgba(70,110,220,0.025)");
    gradient.addColorStop(1,"rgba(25,40,100,0)");
    ctx.beginPath();
    ctx.moveTo(x-width,y);
    ctx.lineTo(x+width,y);
    ctx.lineTo(x+1.5,endY);
    ctx.lineTo(x-1.5,endY);
    ctx.closePath();
    ctx.fillStyle=gradient;
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(x,y);
    ctx.lineTo(x,endY*0.92+y*0.08);
    ctx.strokeStyle=`rgba(186,213,255,${0.06*pulse})`;
    ctx.lineWidth=1.2;
    ctx.stroke();
  }
  jet(-1);
  jet(1);
}
function drawRipples(ripples){
  if(!ripples)return;
  for(const ripple of ripples){
    const[x,y]=screenPoint(ripple.x,ripple.y);
    const alpha=clamp((ripple.a||0)*0.4,0,0.22);
    ctx.beginPath();
    ctx.arc(x,y,(ripple.r||0)*zoom,0,TWO_PI);
    ctx.strokeStyle=`rgba(100,154,255,${alpha})`;
    ctx.lineWidth=0.8;
    ctx.stroke();
  }
}

function drawBlobs(blobs){
  if(!blobs)return;

  for(const blob of blobs){
    const[x,y]=screenPoint(blob.x,blob.y);
    const radius=(blob.r||5)*zoom;
    const color=[255,166,87];

    const glow=ctx.createRadialGradient(x,y,0,x,y,radius*4);

    glow.addColorStop(0,rgba(color[0],color[1],color[2],0.18));
    glow.addColorStop(0.45,rgba(color[0],color[1],color[2],0.045));
    glow.addColorStop(1,"rgba(0,0,0,0)");

    ctx.beginPath();
    ctx.arc(x,y,radius*4,0,TWO_PI);
    ctx.fillStyle=glow;
    ctx.fill();

    ctx.beginPath();
    ctx.arc(x,y,radius,0,TWO_PI);
    ctx.fillStyle=rgba(color[0],color[1],color[2],0.32);
    ctx.fill();

    ctx.strokeStyle=rgba(color[0],color[1],color[2],0.62);
    ctx.lineWidth=0.8;
    ctx.stroke();
  }
}

function drawPhotonRing(core){
  const[x,y]=screenPoint(core.x,core.y);
  const r=shadowRadius(core);
  const spin=clamp(core.spin||0,0,1);

  const pRatio=core.rs>0?core.ps/core.rs:1.5;
  const photonRadius=r*clamp(pRatio*0.86,1.22,1.38);

  const segments=64;

  ctx.save();
  ctx.translate(x,y);
  ctx.lineCap="round";

  for(let i=0;i<segments;i+=1){
    const a1=(i/segments)*TWO_PI;
    const a2=((i+1)/segments)*TWO_PI;

    const brightness=0.35+0.65*Math.pow(Math.max(0,Math.cos(a1-0.2)),3);
    const wobble=Math.sin(a1*3+diskAngle*2)*spin*0.7;

    ctx.beginPath();
    ctx.arc(0,0,photonRadius+wobble*0.04,a1,a2);

    ctx.strokeStyle=`rgba(205,220,255,${0.07+brightness*0.21})`;
    ctx.lineWidth=0.75+brightness*1.15;
    ctx.stroke();}
  ctx.restore();}
function drawBlackHole(core){
  if(!core)return;
  const[x,y]=screenPoint(core.x,core.y);
  const r=shadowRadius(core);
  drawPhotonRing(core);
  const shadowGlow=ctx.createRadialGradient(x,y,r*0.7,x,y,r*1.45);
  shadowGlow.addColorStop(0,"rgba(0,0,0,1)");
  shadowGlow.addColorStop(0.72,"rgba(0,0,2,1)");
  shadowGlow.addColorStop(0.9,"rgba(13,15,30,0.88)");
  shadowGlow.addColorStop(1,"rgba(70,80,180,0)");
  ctx.beginPath();
  ctx.arc(x,y,r*1.45,0,TWO_PI);
  ctx.fillStyle=shadowGlow;
  ctx.fill();
  ctx.beginPath();
  ctx.arc(x,y,r*1.005,0,TWO_PI);
  ctx.fillStyle="#000005";
  ctx.fill();
  ctx.beginPath();
  ctx.arc(x,y,r*0.98,0,TWO_PI);
  ctx.strokeStyle="rgba(0,0,0,0.95)";
  ctx.lineWidth=2;
  ctx.stroke();}
function drawVignette(){
  const vignette=ctx.createRadialGradient(cx,cy,Math.min(W,H)*0.24,cx,cy,Math.max(W,H)*0.72);
  vignette.addColorStop(0,"rgba(0,0,0,0)");
  vignette.addColorStop(0.72,"rgba(0,0,0,0.06)");
  vignette.addColorStop(1,"rgba(0,0,0,0.48)");
  ctx.fillStyle=vignette;
  ctx.fillRect(0,0,W,H);
}
function drawCrosshair(){
  if(!mouseX&&!mouseY)return;
  ctx.strokeStyle=paused?"rgba(255,255,255,0.18)":"rgba(255,255,255,0.055)";
  ctx.lineWidth=0.5;
  ctx.beginPath();
  ctx.moveTo(mouseX-8,mouseY);
  ctx.lineTo(mouseX-3,mouseY);
  ctx.moveTo(mouseX+3,mouseY);
  ctx.lineTo(mouseX+8,mouseY);
  ctx.moveTo(mouseX,mouseY-8);
  ctx.lineTo(mouseX,mouseY-3);
  ctx.moveTo(mouseX,mouseY+3);
  ctx.lineTo(mouseX,mouseY+8);
  ctx.stroke();}
function updateHud(info)


{
  if(!hudEl||!info)return;
  const age=performance.now()-lastFrameAt;
  let status="live";
  if(age>800)status="signal waiting";
  if(paused)status="simulation paused";
  let s="VOID / ACCRETION STUDY\n"+status+"\n\n";
  s+="particles  "+(info.np??0)+"\n";
  s+="matter     "+(info.nb??0)+"\n";
  s+="time       "+(info.tm??"0.00");
  if(info.lg&&info.lg.length){
    s+="\n\nlast event  "+info.lg[info.lg.length-1];
  }
  hudEl.textContent=s;}
let lastT=performance.now();

function render(now){
  if(!ctx||!canvas)return;

  animationId=requestAnimationFrame(render);

  const dtw=Math.min((now-lastT)/1000,0.05);
  lastT=now;

  zoom=lerp(zoom,tZoom,1-Math.pow(0.001,dtw));

  if(!panning&&(Math.abs(velX)>0.1||Math.abs(velY)>0.1)){
    panX+=velX*dtw;
    panY+=velY*dtw;
    velX*=Math.pow(0.02,dtw);
    velY*=Math.pow(0.02,dtw);
  }

  if(W===0||H===0)return;

  drawBackground();

  if(!frame||!frame.c){
    ctx.fillStyle="rgba(220,225,255,0.55)";
    ctx.font="12px monospace";
    ctx.textAlign="center";
    ctx.fillText("waiting for simulation",cx,cy);
    return;
  }

  const core=frame.c;
  const particles=frame.m||[];

  diskAngle+=paused?0.0008:0.0045;

  drawStars(frame.s);
  drawRays(frame.y);
  drawLensHalo(core);
  drawJets(core);
  drawDisk(core,frame.d);
  drawTrails(particles,core);
  drawRipples(frame.r);
  drawBlobs(frame.b);
  drawBlackHole(core);
  drawVignette();
  drawCrosshair();
  updateHud(frame.i);
}
render(performance.now());
function togglePause(){
  paused=!paused;
  pyCall("set_paused",paused);
  const button=document.getElementById("pbtn");
  if(button){
    button.textContent=paused?"play":"pause";}
}
function kill(){
  pyCall("stop_sim");}
window.togglePause=togglePause;
window.kill=kill;
canvas.addEventListener("mousemove",event=>{
  mouseX=event.clientX;
  mouseY=event.clientY;
  if(panning){
    const dx=event.clientX-lastMX;
    const dy=event.clientY-lastMY;
    panX+=dx;
    panY+=dy;
    velX=dx*60;
    velY=dy*60;
    lastMX=event.clientX;
    lastMY=event.clientY;
  }
});
canvas.addEventListener("click",event=>{
  const[wx,wy]=worldFromScreen(event.clientX,event.clientY);
  pyCall("add_mass_at",wx,wy,1.0);
});
canvas.addEventListener("mousedown",event=>{
  if(event.button===0){
    holding=true;
    holdTimer=window.setInterval(()=>{
      if(holding){
        const[wx,wy]=worldFromScreen(mouseX,mouseY);
        pyCall("add_mass_at",wx,wy,0.4);
      }
    },70);
  }else{
    panning=true;
    velX=0;
    velY=0;
    lastMX=event.clientX;
    lastMY=event.clientY;
    event.preventDefault();
  }
});

window.addEventListener("mouseup",()=>{
  holding=false;
  panning=false;

  if(holdTimer!==null){
    window.clearInterval(holdTimer);
    holdTimer=null;
  }
});
canvas.addEventListener("contextmenu",event=>event.preventDefault());
window.addEventListener("keydown",event=>{
  if(event.key==="q")pyCall("adjust_spin",0.03);
  if(event.key==="e")pyCall("adjust_spin",-0.03);
});

window.addEventListener("wheel",event=>{
  event.preventDefault();

  const wx=(event.clientX-cx-panX)/zoom;
  const wy=(event.clientY-cy-panY)/zoom;

  const f=event.deltaY<0?1.15:1/1.15;
  tZoom=clamp(tZoom*f,0.3,5);

  panX=event.clientX-cx-wx*tZoom;
  panY=event.clientY-cy-wy*tZoom;
},{passive:false});
