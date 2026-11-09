/* No build step, fetch, analytics or external assets. */
(function(){
'use strict';
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const programmeFormats={
 bifold:{label:'Bi-fold A3 / A4',spec:'A3 aperto 420 × 297 mm → A4 chiuso. Quattro facciate; un giorno per pagina interna.'},
 dl:{label:'Tri-fold DL',spec:'A4 aperto 297 × 210 mm → DL 99 × 210 mm. Tre pannelli, sei facciate; due giorni in sintesi.'}
};
const requestedFold=new URLSearchParams(location.search).get('fold');
let activeProgramme=Object.hasOwn(programmeFormats,requestedFold)?requestedFold:'bifold';
function updatePrintLink(){document.getElementById('pdf-link').href='?print-pdf&palette='+activePalette+'&fold='+activeProgramme;}
const paletteDefinitions={
 bianco:{number:1,names:{paper:'Bianco',ink:'Grafite',accent:'Pesca'},colors:{paper:'#FFFFFF',ink:'#252B29',accent:'#D89277'}},
 carta:{number:2,names:{paper:'Carta',ink:'Grafite',accent:'Ossido'},colors:{paper:'#F4F1E8',ink:'#252B29',accent:'#AC4B35'}}
};
const paletteStorageKey='archeofoss2026-palette';
const requestedPalette=new URLSearchParams(location.search).get('palette');
let activePalette=Object.hasOwn(paletteDefinitions,requestedPalette)?requestedPalette:'bianco';
function paletteAsset(name){return (activePalette==='carta'?'assets/palettes/carta/':'assets/')+name+'?v=programme-graphic';}
document.querySelectorAll('img[src^="assets/"][src$=".svg"],a[href^="assets/"][href$=".svg"],link[rel="icon"]').forEach(el=>{
 const attribute=el.tagName==='IMG'?'src':'href';el.dataset.paletteAsset=el.getAttribute(attribute).split('/').pop();
});
function applyPalette(id){
 if(!Object.hasOwn(paletteDefinitions,id))return;
 activePalette=id;const palette=paletteDefinitions[id];document.documentElement.dataset.palette=id;
 document.querySelectorAll('[data-palette-choice]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.paletteChoice===id)));
 document.querySelectorAll('[data-palette-name]').forEach(el=>el.textContent=palette.names[el.dataset.paletteName]);
 document.querySelectorAll('[data-palette-code]').forEach(el=>el.textContent=palette.colors[el.dataset.paletteCode]);
 document.querySelectorAll('[data-palette-asset]').forEach(el=>el.setAttribute(el.tagName==='IMG'?'src':'href',paletteAsset(el.dataset.paletteAsset)));
 document.querySelectorAll('.dark-slide').forEach(el=>el.dataset.backgroundColor=palette.colors.ink);
 document.querySelector('meta[name="theme-color"]').content=palette.colors.paper;
 document.getElementById('palette-status').textContent=`Palette attiva: ${palette.number} · ${palette.names.paper} / ${palette.names.ink} / ${palette.names.accent}.`;
 updatePrintLink();
 try{localStorage.setItem(paletteStorageKey,id);}catch(e){}
 try{const url=new URL(location.href);url.searchParams.set('palette',id);history.replaceState(history.state,'',url);}catch(e){}
 if(window.Reveal&&Reveal.isReady())Reveal.sync();
}
document.querySelectorAll('[data-palette-choice]').forEach(b=>b.addEventListener('click',()=>applyPalette(b.dataset.paletteChoice)));
applyPalette(activePalette);
function chooseProgramme(id){
 if(!Object.hasOwn(programmeFormats,id))return;
 activeProgramme=id;const info=programmeFormats[id];
 document.querySelectorAll('[data-programme-format]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.programmeFormat===id)));
 document.querySelectorAll('[data-programme-side]').forEach(el=>{const name=`programme-${id}-${el.dataset.programmeSide}.svg`;el.dataset.paletteAsset=name;el.src=paletteAsset(name);el.alt=info.label+' · '+(el.dataset.programmeSide==='outer'?'esterno completo':'interno completo');});
 document.querySelectorAll('[data-programme-download]').forEach(el=>{const name=`programme-${id}-${el.dataset.programmeDownload}.svg`;el.dataset.paletteAsset=name;el.href=paletteAsset(name);el.download=name;});
 document.getElementById('programme-spec').textContent=info.spec;
 document.getElementById('programme-dialog-title').textContent='Programma · '+info.label;
 document.getElementById('programme-dialog-spec').textContent=info.spec;
 document.getElementById('programme-outer').parentElement.querySelector('figcaption').textContent=id==='dl'?'ESTERNO / TRE PANNELLI':'ESTERNO / COPERTINA + RETRO';
 document.getElementById('programme-inner').parentElement.querySelector('figcaption').textContent=id==='dl'?'INTERNO / DUE GIORNATE + MAPPA':'INTERNO / DUE GIORNATE';
 updatePrintLink();
 try{const url=new URL(location.href);url.searchParams.set('fold',id);history.replaceState(history.state,'',url);}catch(e){}
}
document.querySelectorAll('[data-programme-format]').forEach(b=>b.addEventListener('click',()=>chooseProgramme(b.dataset.programmeFormat)));
chooseProgramme(activeProgramme);
const programmeDialog=document.getElementById('programme-dialog');
document.getElementById('programme-open').addEventListener('click',()=>{programmeDialog.showModal();programmeDialog.scrollTop=0;});
document.getElementById('programme-close').addEventListener('click',()=>programmeDialog.close());
programmeDialog.addEventListener('keydown',e=>{e.stopPropagation();if(e.key==='Escape'){e.preventDefault();programmeDialog.close();}});
programmeDialog.addEventListener('click',e=>{if(e.target===programmeDialog){const r=programmeDialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)programmeDialog.close();}});
const selector=document.getElementById('panel-selector');
selector.innerHTML=PANELS.map(p=>`<button type="button" data-panel="${p.id}" aria-pressed="${p.id===2}" aria-label="Panel ${p.id}: ${esc(p.title)}"><span>${String(p.id).padStart(2,'0')}</span><strong>${esc(p.short)}</strong></button>`).join('');
function choosePanel(id){
 const p=PANELS.find(p=>p.id===id);if(!p)return;
 selector.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.panel)===id)));
 document.getElementById('panel-id').textContent=String(id).padStart(2,'0');
 document.getElementById('panel-family').textContent=p.family;
 document.getElementById('panel-title').textContent=p.title;
 document.getElementById('panel-summary').textContent=p.summary;
 const panelArt=document.getElementById('panel-art');panelArt.dataset.paletteAsset=`panel-field-${String(id).padStart(2,'0')}.svg`;panelArt.src=paletteAsset(panelArt.dataset.paletteAsset);
}
selector.addEventListener('click',e=>{const b=e.target.closest('[data-panel]');if(b)choosePanel(Number(b.dataset.panel));});choosePanel(2);
[1,2].forEach(i=>{document.getElementById('official-list-'+i).innerHTML=PANELS.slice((i-1)*6,i*6).map(p=>`<div><span>${String(p.id).padStart(2,'0')}</span><p>${esc(p.title)}</p></div>`).join('');});
const yAt=(x,j)=>155+j*16+67*Math.sin(x/900*Math.PI*1.7)*Math.exp(-Math.pow((x-400)/420,2))+26*Math.sin(x/140+j*.08);
const nodes=[[110,2],[245,6],[195,10],[385,3],[475,8],[625,14],[320,17],[555,2],[710,6],[805,11],[620,18],[810,18]];
let layers='',grid='',dots='';
for(let j=0;j<20;j++){let d='';for(let x=15;x<=900;x+=5)d+=(x===15?'M':' L')+x+','+yAt(x,j).toFixed(2);layers+=`<path d="${d}" fill="none" stroke="var(--ink)" stroke-width="${j%5===0?1.65:1.05}" opacity="${j%5===0?.76:.48}"/>`;}
for(let x=60;x<880;x+=120)grid+=`<path d="M${x},85 V555" stroke="var(--line)" stroke-width=".8"/>`;
for(let y=100;y<580;y+=100)grid+=`<path d="M30,${y} H885" stroke="var(--line)" stroke-width=".8"/>`;
nodes.forEach(([x,j],i)=>{const y=yAt(x,j);dots+=`<circle cx="${x}" cy="${y}" r="5.5" fill="var(--oxide)" stroke="var(--paper)" stroke-width="2"/><text x="${x+10}" y="${y-9}" font-family="IBM Plex Mono,monospace" font-size="12" fill="var(--oxide)">${String(i+1).padStart(2,'0')}</text>`;});
document.getElementById('grammar-svg').innerHTML=`<g data-visual-layer="grid">${grid}</g><g data-visual-layer="layers">${layers}</g><g data-visual-layer="nodes">${dots}</g>`;
document.querySelectorAll('[data-layer]').forEach(b=>b.addEventListener('click',()=>{const visible=b.getAttribute('aria-pressed')!=='true';b.setAttribute('aria-pressed',String(visible));document.querySelector(`[data-visual-layer="${b.dataset.layer}"]`).style.visibility=visible?'visible':'hidden';}));
function keepPrintCanvas(){
 if(!new URLSearchParams(location.search).has('print-pdf'))return;
 document.querySelectorAll('.reveal .slides section').forEach(s=>{
  const styles={width:'1600px',height:'900px',padding:s.classList.contains('cover')?'104px 88px 72px':'78px 88px 72px','box-sizing':'border-box',position:'relative',top:'0px',left:'0px'};
  Object.entries(styles).forEach(([key,value])=>s.style.setProperty(key,value,'important'));
 });
}
Reveal.on('ready',keepPrintCanvas);Reveal.on('pdf-ready',keepPrintCanvas);
const reduced=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
Reveal.initialize({width:1600,height:900,margin:.015,minScale:.12,maxScale:1.6,hash:true,history:true,center:false,controls:true,progress:true,slideNumber:false,transition:reduced?'none':'fade',transitionSpeed:'fast',backgroundTransition:'none',navigationMode:'linear',view:'slide',pdfSeparateFragments:false,pdfMaxPagesPerSlide:1,showNotes:false,plugins:[RevealNotes]});
function update(){
 const current=Reveal.getCurrentSlide();document.body.classList.toggle('dark-ui',current&&current.classList.contains('dark-slide'));
 const slides=Reveal.getSlides();document.getElementById('slide-count').textContent=String(slides.indexOf(current)+1).padStart(2,'0')+' / '+String(slides.length).padStart(2,'0');
}
Reveal.on('ready',update);Reveal.on('slidechanged',update);
document.getElementById('overview').addEventListener('click',()=>Reveal.toggleOverview());
document.getElementById('fullscreen').addEventListener('click',()=>{if(document.fullscreenElement){document.exitFullscreen?.();}else{document.documentElement.requestFullscreen?.().catch(()=>{});}});
const dialog=document.getElementById('help-dialog');document.getElementById('help').addEventListener('click',()=>dialog.showModal());dialog.querySelector('.dialog-close').addEventListener('click',()=>dialog.close());dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close();}});
})();
