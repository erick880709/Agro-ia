# HTML Shell — Cronos (PersonalSoft Presentation)

Copy this boilerplate and replace `{ICON_BLUE}`, `{ICON_WHITE}`, `{TOTAL}`, `{TITLES_ARRAY}`, and `{SLIDES_HTML}`.

```html
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{PRESENTATION_TITLE} · PersonalSoft</title>
<link href="https://fonts.googleapis.com/css2?family=Reddit+Sans:wght@300;400;500;600;700;800;900&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
<style>
:root {
  --ps-font-heading: 'Space Grotesk', 'Reddit Sans', sans-serif;
  --ps-blue: #1470C0; --ps-navy: #0B1F3A; --ps-navy-mid: #263474;
  --ps-dark: #06203F; --ps-blue-light: #E6F1FC;
  --ps-text: #111827; --ps-muted: #6B7280; --ps-white: #FFFFFF;
  --ps-green: #1A7A4A; --ps-green-light: #EBF7F1;
  --ps-amber: #B87A00; --ps-amber-light: #FEF5E6;
  --ps-red: #B91C1C; --ps-red-light: #FEF2F2;
  --ps-teal: #0D9E7A; --ps-teal-light: #CCFBF1;
  --ps-gray: #F3F4F6; --ps-gray-b: #E5E7EB;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:100%;height:100%;overflow:hidden;background:#04101E;font-family:'Reddit Sans',sans-serif;cursor:none}

/* Laser cursor */
#laser{position:fixed;width:12px;height:12px;border-radius:50%;background:rgba(255,50,50,0.88);box-shadow:0 0 6px 2px rgba(255,50,50,0.35);pointer-events:none;z-index:9999;transform:translate(-50%,-50%)}
#ltrail{position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:9998}

/* Deck & slides */
#deck{width:100%;height:100%;position:relative}
.slide{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;align-items:flex-start;padding:44px 76px;opacity:0;pointer-events:none;transition:opacity 0.38s ease;background:var(--ps-white);overflow:hidden}
.slide.active{opacity:1;pointer-events:all}
.orb{position:absolute;border-radius:50%;background:var(--ps-blue-light);pointer-events:none}

/* Progress bar */
#pgbar{position:fixed;top:0;left:0;right:0;height:3px;background:rgba(11,31,58,0.12);z-index:999}
#pgfill{height:100%;background:var(--ps-blue);transition:width 0.38s ease}

/* Controls */
#ctrl{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);z-index:1000;display:flex;align-items:center;gap:4px;background:rgba(4,16,30,0.92);border:1px solid rgba(255,255,255,0.1);border-radius:40px;padding:7px 13px;backdrop-filter:blur(14px)}
.cbtn{background:none;border:none;color:rgba(255,255,255,0.62);cursor:none;font-size:12px;font-family:'Reddit Sans',sans-serif;padding:5px 9px;border-radius:20px;transition:all 0.15s;display:flex;align-items:center;gap:4px}
.cbtn:hover{background:rgba(255,255,255,0.1);color:white}
.cbtn svg{width:13px;height:13px;fill:none;stroke:currentColor;stroke-width:1.5;stroke-linecap:round;stroke-linejoin:round}
.cdiv{width:1px;height:17px;background:rgba(255,255,255,0.1);margin:0 2px}
#cnt{color:rgba(255,255,255,0.4);font-size:11px;min-width:38px;text-align:center}

/* Index panel */
#idx{position:fixed;inset:0;background:rgba(4,16,30,0.96);z-index:2000;display:none;flex-direction:column;align-items:center;justify-content:center;backdrop-filter:blur(8px)}
#idx.open{display:flex}
.idxg{display:grid;grid-template-columns:repeat(4,185px);gap:8px;margin-top:10px}
.idxi{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.09);border-radius:10px;padding:12px 14px;cursor:none;transition:all 0.2s}
.idxi:hover{background:rgba(20,112,192,0.2);border-color:rgba(20,112,192,0.4)}
.idxn{font-size:10px;color:var(--ps-blue);font-weight:700;margin-bottom:3px}
.idxt{font-size:11px;color:rgba(255,255,255,0.75);font-weight:500;line-height:1.3}

/* Keyboard hint */
#kbh{position:fixed;top:16px;right:20px;z-index:1000;display:flex;gap:5px;opacity:0.4}
#kbh:hover{opacity:0.9}
.kbd{background:rgba(0,0,0,0.5);border:1px solid rgba(255,255,255,0.18);border-radius:4px;padding:2px 6px;font-size:10px;color:rgba(255,255,255,0.65);font-family:'Reddit Sans',sans-serif}

/* Animation */
.anim{opacity:0;transform:translateY(14px);transition:opacity 0.4s ease,transform 0.4s ease}
.anim.in{opacity:1;transform:translateY(0)}

/* ── TYPOGRAPHY ── */
.tag{display:inline-block;padding:5px 13px;border-radius:20px;font-size:11px;font-weight:600;letter-spacing:0.6px;text-transform:uppercase}
.tag-b{background:var(--ps-blue-light);color:var(--ps-navy)}
.tag-g{background:var(--ps-green-light);color:var(--ps-green)}
.tag-a{background:var(--ps-amber-light);color:var(--ps-amber)}
.tag-t{background:var(--ps-teal-light);color:var(--ps-teal)}
.tag-dk{background:rgba(20,112,192,0.14);color:#6B9FE0}
.tag-r{background:var(--ps-red-light);color:var(--ps-red)}

.stitle{font-family:var(--ps-font-heading);font-weight:700;font-size:48px;line-height:1.06;color:var(--ps-text);margin:10px 0 9px}
.stitle span{color:var(--ps-blue)}
.stitle em{color:var(--ps-red);font-style:normal}
.ssub{font-weight:300;font-size:16px;color:var(--ps-muted);line-height:1.65;max-width:620px}

/* Dark slide overrides — apply via ID */
/* #s1, #s6 → background:var(--ps-dark) */
/* #s9 → background:var(--ps-navy) */

/* ── LOGO MARK ── */
.mk{display:flex;align-items:center;gap:8px;margin-bottom:22px}
.mk img{height:26px;width:auto}
.mk-word{font-weight:700;font-size:15px;color:var(--ps-text)}
.mk-word.lt{color:white}

/* ── PIPELINE ── */
.pipe{display:flex;align-items:stretch;width:100%;margin-top:12px}
.pb{flex:1;border:2px solid;border-radius:11px;padding:12px 12px;background:var(--ps-white)}
.pa{flex:0 0 22px;display:flex;align-items:center;justify-content:center;color:#D1D5DB;font-size:14px}
.pnum{font-size:9px;font-weight:700;letter-spacing:.9px;text-transform:uppercase;margin-bottom:4px;opacity:.8}
.pname{font-weight:700;font-size:12px;color:var(--ps-text);margin-bottom:4px;line-height:1.25}
.pdet{font-size:10.5px;color:var(--ps-muted);line-height:1.4}

/* ── STEP CARDS ── */
.srow{display:flex;gap:11px;width:100%;margin-top:8px}
.sc{flex:1;border-radius:13px;padding:16px 15px;border:1px solid var(--ps-gray-b);background:var(--ps-white);position:relative;overflow:hidden}
.sc::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;border-radius:13px 13px 0 0}
.sc.blue::before{background:var(--ps-blue)} .sc.teal::before{background:var(--ps-teal)}
.sc.green::before{background:var(--ps-green)} .sc.amber::before{background:var(--ps-amber)}
.scn{font-size:9px;font-weight:700;letter-spacing:.8px;text-transform:uppercase;margin-bottom:5px}
.scn.blue{color:var(--ps-blue)} .scn.teal{color:var(--ps-teal)}
.scn.green{color:var(--ps-green)} .scn.amber{color:var(--ps-amber)}
.scname{font-weight:700;font-size:13px;color:var(--ps-text);margin-bottom:6px;line-height:1.2}
.scbody{font-size:11.5px;color:var(--ps-muted);line-height:1.5}
.sctag{display:inline-block;background:var(--ps-gray);border-radius:5px;padding:2px 7px;font-size:9px;font-weight:500;color:var(--ps-muted);margin-top:5px;margin-right:3px}

/* ── KPI ── */
.krow{display:flex;gap:9px;margin-bottom:12px}
.kcard{flex:1;background:var(--ps-blue-light);border-radius:11px;padding:14px 12px;text-align:center}
.kn{font-weight:800;font-size:34px;color:var(--ps-navy);line-height:1}
.kl{font-size:10px;color:var(--ps-muted);margin-top:3px;line-height:1.3}

/* ── BARS ── */
.bgr{display:flex;align-items:center;gap:7px;margin-bottom:5px}
.blbl{font-size:10.5px;color:var(--ps-muted);width:115px;text-align:right;flex-shrink:0}
.bbg{flex:1;height:9px;background:#E9ECF2;border-radius:3px;overflow:hidden}
.bfil{height:100%;border-radius:3px;background:var(--ps-navy)}
.bval{font-size:10.5px;font-weight:700;color:var(--ps-navy);width:22px;text-align:right;flex-shrink:0}

/* ── INSIGHT ── */
.ins{background:var(--ps-green-light);border-radius:7px;padding:7px 11px;font-size:10.5px;color:var(--ps-green);margin-top:auto;line-height:1.4;font-weight:500}

/* ── DARK COLUMNS (brecha) ── */
.gcol{flex:1;border-radius:11px;padding:13px 15px}
.gcol.have{border:2px solid var(--ps-teal);background:rgba(13,158,122,0.06)}
.gcol.need{border:2px dashed rgba(255,255,255,0.18);background:rgba(255,255,255,0.03)}
.gctitle{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;margin-bottom:9px}
.gcitem{font-size:11.5px;line-height:1.4;margin-bottom:6px;display:flex;align-items:flex-start;gap:7px}

/* ── AZURE/TOOL CALLOUT ── */
.az{background:rgba(20,112,192,0.1);border:1px solid rgba(20,112,192,0.3);border-radius:9px;padding:11px 15px;margin-top:9px;border-left:4px solid var(--ps-blue)}
.aztitle{font-weight:700;font-size:12.5px;color:#7BBFFF;margin-bottom:4px}
.aztags{display:flex;gap:5px;flex-wrap:wrap}
.aztag{font-size:10px;color:rgba(255,255,255,0.62);background:rgba(20,112,192,0.18);padding:2px 8px;border-radius:4px;font-weight:500}
.aznote{font-size:10px;color:rgba(255,255,255,0.38);margin-top:5px;line-height:1.4}

/* ── NEXT STEPS (dark bg) ── */
.psgrid{display:grid;grid-template-columns:1fr 1fr;gap:9px;width:100%;margin-top:9px}
.pscard{border-radius:11px;padding:15px 17px}
.psperiod{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;opacity:.72;margin-bottom:4px}
.psname{font-weight:700;font-size:14px;margin-bottom:5px;line-height:1.2}
.psbody{font-size:11px;line-height:1.5;opacity:.78}

/* ── ITERATIVE BADGE ── */
.iter-badge{display:inline-flex;align-items:center;gap:5px;background:rgba(20,112,192,0.1);border:1px solid rgba(20,112,192,0.2);border-radius:20px;padding:4px 12px;font-size:10px;font-weight:600;color:var(--ps-blue);margin-bottom:10px}
</style>
</head>
<body>

<div id="laser"></div>
<canvas id="ltrail"></canvas>
<div id="pgbar"><div id="pgfill" style="width:{FIRST_WIDTH}%"></div></div>

<div id="kbh">
  <span class="kbd">← →</span>
  <span class="kbd">espacio</span>
  <span class="kbd">R reiniciar</span>
  <span class="kbd">I índice</span>
</div>

<div id="idx">
  <div style="font-size:11px;font-weight:700;color:rgba(255,255,255,0.32);letter-spacing:2px;text-transform:uppercase;margin-bottom:8px">Navegar a</div>
  <div class="idxg" id="idxg"></div>
  <div style="margin-top:16px;font-size:11px;color:rgba(255,255,255,0.28)">ESC o I para cerrar</div>
</div>

<div id="deck">
{SLIDES_HTML}
</div>

<!-- CONTROLS -->
<div id="ctrl">
  <button class="cbtn" id="bprev"><svg viewBox="0 0 16 16"><path d="M10 3L5 8l5 5"/></svg>Anterior</button>
  <div class="cdiv"></div>
  <span id="cnt">1 / {TOTAL}</span>
  <div class="cdiv"></div>
  <button class="cbtn" id="banim"><svg viewBox="0 0 16 16"><path d="M5 3l8 5-8 5V3z"/></svg>Animar</button>
  <div class="cdiv"></div>
  <button class="cbtn" id="breset"><svg viewBox="0 0 16 16"><path d="M2 8a6 6 0 1 1 1.5 4M2 12V8h4"/></svg>Reiniciar</button>
  <div class="cdiv"></div>
  <button class="cbtn" id="bnext">Siguiente<svg viewBox="0 0 16 16"><path d="M6 3l5 5-5 5"/></svg></button>
  <div class="cdiv"></div>
  <button class="cbtn" id="bidx"><svg viewBox="0 0 16 16"><path d="M2 4h12M2 8h12M2 12h12"/></svg>Índice</button>
</div>

<script>
const slides=document.querySelectorAll('.slide');
const total=slides.length;
let cur=0,step=0;
const titles={TITLES_ARRAY};

function getA(sl){return [...sl.querySelectorAll('[data-step]')].sort((a,b)=>+a.dataset.step - +b.dataset.step)}
function resetA(){getA(slides[cur]).forEach(el=>el.classList.remove('in'));step=0}
function playAll(){
  const e=getA(slides[cur]);
  e.forEach((el,i)=>setTimeout(()=>el.classList.add('in'),i*65));
  step=e.length;
}
function playNext(){
  const e=getA(slides[cur]);
  if(step<e.length){e[step].classList.add('in');step++;return true}
  return false;
}
function go(idx,ra){
  slides[cur].classList.remove('active');
  cur=(idx+total)%total;
  slides[cur].classList.add('active');
  step=0;
  if(ra!==false)resetA();
  document.getElementById('cnt').textContent=`${cur+1} / ${total}`;
  document.getElementById('pgfill').style.width=`${((cur+1)/total)*100}%`;
  setTimeout(()=>playAll(),120);
}

go(0,false);
setTimeout(()=>playAll(),280);

document.getElementById('bprev').addEventListener('click',()=>go(cur-1));
document.getElementById('bnext').addEventListener('click',()=>go(cur+1));
document.getElementById('banim').addEventListener('click',()=>{if(!playNext())go(cur+1)});
document.getElementById('breset').addEventListener('click',()=>{resetA();setTimeout(()=>{getA(slides[cur])[0]?.classList.add('in');step=1},50)});
document.getElementById('bidx').addEventListener('click',()=>document.getElementById('idx').classList.toggle('open'));

const idxg=document.getElementById('idxg');
titles.forEach((t,i)=>{
  const el=document.createElement('div');
  el.className='idxi';
  el.innerHTML=`<div class="idxn">${String(i+1).padStart(2,'0')}</div><div class="idxt">${t}</div>`;
  el.addEventListener('click',()=>{document.getElementById('idx').classList.remove('open');go(i)});
  idxg.appendChild(el);
});

document.addEventListener('keydown',e=>{
  if(e.key==='ArrowRight'||e.key==='ArrowDown')go(cur+1);
  if(e.key==='ArrowLeft'||e.key==='ArrowUp')go(cur-1);
  if(e.key===' '){e.preventDefault();if(!playNext())go(cur+1)}
  if(e.key==='r'||e.key==='R'){resetA();setTimeout(()=>{getA(slides[cur])[0]?.classList.add('in');step=1},50)}
  if(e.key==='i'||e.key==='I')document.getElementById('idx').classList.toggle('open');
  if(e.key==='Escape')document.getElementById('idx').classList.remove('open');
});

/* Laser */
const laser=document.getElementById('laser');
const canvas=document.getElementById('ltrail');
const ctx=canvas.getContext('2d');
canvas.width=window.innerWidth;canvas.height=window.innerHeight;
window.addEventListener('resize',()=>{canvas.width=window.innerWidth;canvas.height=window.innerHeight});
const trail=[];const TL=14;
document.addEventListener('mousemove',e=>{
  laser.style.left=e.clientX+'px';laser.style.top=e.clientY+'px';
  trail.push({x:e.clientX,y:e.clientY});
  if(trail.length>TL)trail.shift();
});
function draw(){
  ctx.clearRect(0,0,canvas.width,canvas.height);
  for(let i=1;i<trail.length;i++){
    const t=trail[i],p=trail[i-1];
    ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.lineTo(t.x,t.y);
    ctx.strokeStyle=`rgba(255,50,50,${(i/trail.length)*0.28})`;
    ctx.lineWidth=(i/trail.length)*4.5;
    ctx.lineCap='round';ctx.stroke();
  }
  requestAnimationFrame(draw);
}
draw();
</script>
</body>
</html>
```

## Template variables to replace

| Variable | What to put |
|----------|-------------|
| `{PRESENTATION_TITLE}` | e.g. `IA para los Servicios` |
| `{TOTAL}` | number of slides, e.g. `9` |
| `{FIRST_WIDTH}` | `100/total` rounded, e.g. `11.1` for 9 slides |
| `{TITLES_ARRAY}` | JS array literal e.g. `['Portada','Estrategia IA',...]` |
| `{SLIDES_HTML}` | All `<section class="slide" ...>` elements |
| `{ICON_BLUE}` | Base64 data URI from `assets/icons.json` |
| `{ICON_WHITE}` | Base64 data URI from `assets/icons.json` |

## Slide section template

```html
<section class="slide" id="sN" data-title="Slide Title">
  <!-- decorative background orb (optional) -->
  <div class="orb" style="width:380px;height:380px;right:-80px;top:-80px;opacity:0.22"></div>
  
  <!-- logo mark — FIRST animated element, always data-step="0" -->
  <div class="mk anim" data-step="0">
    <img src="{ICON_BLUE_OR_WHITE}" style="height:26px;width:auto" alt="PersonalSoft">
    <span class="mk-word [lt]">PersonalSoft</span>
  </div>
  
  <!-- tag pill — data-step="1" -->
  <div class="tag tag-b anim" data-step="1">Tag text</div>
  
  <!-- headline — data-step="2" -->
  <h2 class="stitle anim" data-step="2">Title <span>accent</span></h2>
  
  <!-- main content — data-step="3" -->
  <div class="anim" data-step="3">
    <!-- cards, pipeline, KPIs, etc. -->
  </div>
  
  <!-- secondary content — data-step="4" (optional) -->
  <div class="anim" data-step="4">
    <!-- insight, callout, etc. -->
  </div>
</section>
```
