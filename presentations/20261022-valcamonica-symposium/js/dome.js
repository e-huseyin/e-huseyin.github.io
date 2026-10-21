/* Perspective RTI acquisition explainer. Geometry is illustrative, not calibration data. */
window.RevealDome = (() => {
  const NS = 'http://www.w3.org/2000/svg';
  function init(reveal) {
    document.querySelectorAll('[data-rti-dome]').forEach(host => {
      const slide = host.closest('section'), svg = host.querySelector('svg');
      const output = host.querySelector('output'), play = host.querySelector('[data-play]');
      const progress = host.querySelector('progress'), rotation = host.querySelector('[data-orbit]');
      const speed = host.querySelector('[data-speed]');
      const reduce = matchMedia('(prefers-reduced-motion: reduce)');
      let frame = 0, timer = null, angle = 0, tilt = 28 * Math.PI / 180;
      let drag = null, dragged = false, zoom = 1;
      const elevationControl = host.querySelector("[data-tilt]");
      const tiers = [15,25,35,45,55,65];
      const leds = tiers.flatMap((e,t) => Array.from({length:8},(_,a) => ({e,t,a,phi:a*Math.PI/4})));
      function el(tag, attrs, parent=svg) {
        const n=document.createElementNS(NS,tag);
        Object.entries(attrs).forEach(([k,v])=>n.setAttribute(k,v)); parent.appendChild(n); return n;
      }
      function project(x,y,z) {
        const c=Math.cos(angle),s=Math.sin(angle), X=x*c-y*s,Y=x*s+y*c;
        const surfaceExtent = (Math.abs(s)*320 + Math.abs(c)*205)*Math.sin(tilt);
        const scale = Math.min(1,205/Math.max(1,surfaceExtent));
        return [385+X*scale,340+(Y*Math.sin(tilt)-z*Math.cos(tilt))*scale,Y*Math.cos(tilt)+z*Math.sin(tilt)];
      }
      function point(e,phi) { const a=e*Math.PI/180; return project(260*Math.cos(a)*Math.cos(phi),260*Math.cos(a)*Math.sin(phi),260*Math.sin(a)); }
      function path(points,closed=false) {return points.map((p,i)=>(i?'L':'M')+p[0].toFixed(2)+','+p[1].toFixed(2)).join(' ')+(closed?'Z':'');}
      const defs=el('defs',{});
      defs.innerHTML=`
        <linearGradient id="dome-metal" x1="0" y1="0" x2="1" y2=".8"><stop stop-color="#dbe5e7" stop-opacity=".13"/><stop offset=".5" stop-color="#718184" stop-opacity=".02"/><stop offset="1" stop-color="#6eb98c" stop-opacity=".09"/></linearGradient>
        <radialGradient id="dome-pool"><stop stop-color="#fff0bd" stop-opacity=".16"/><stop offset=".45" stop-color="#ffe6a2" stop-opacity=".065"/><stop offset="1" stop-color="#e1dc64" stop-opacity="0"/></radialGradient>
        <linearGradient id="dome-beam"><stop stop-color="#fff7d4" stop-opacity=".12"/><stop offset="1" stop-color="#ffecb0" stop-opacity=".015"/></linearGradient>
        <linearGradient id="camera-metal" x1="0" y1="0" x2=".9" y2="1"><stop stop-color="#494e4b"/><stop offset=".22" stop-color="#343935"/><stop offset=".58" stop-color="#242827"/><stop offset=".83" stop-color="#424943"/><stop offset="1" stop-color="#232625"/></linearGradient>
        <linearGradient id="camera-charcoal" x1="0" y1="0" x2=".8" y2="1"><stop stop-color="#555653"/><stop offset=".18" stop-color="#3d403d"/><stop offset=".42" stop-color="#282828"/><stop offset=".72" stop-color="#414642"/><stop offset="1" stop-color="#252826"/></linearGradient><pattern id="camera-leather" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="4" fill="#292d2a"/><path d="M0 1L2 0 4 2M1 4L2 2 4 3" stroke="#515950" stroke-width=".45" fill="none" opacity=".42"/></pattern><radialGradient id="lens-glass"><stop stop-color="#050d16"/><stop offset=".4" stop-color="#143238"/><stop offset=".65" stop-color="#315468"/><stop offset=".8" stop-color="#111b2b"/><stop offset="1" stop-color="#5b7780"/></radialGradient>
        <radialGradient id="sphere-chrome" cx=".45" cy=".4"><stop stop-color="#202a2c"/><stop offset=".6" stop-color="#0b1215"/><stop offset=".88" stop-color="#05090b"/><stop offset="1" stop-color="#343e41"/></radialGradient>
        <filter id="dome-glow" x="-150%" y="-150%" width="400%" height="400%"><feGaussianBlur stdDeviation="4"/></filter>
        <filter id="recess-soft-edge" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation=".45"/></filter>
        <pattern id="dome-stone" width="53" height="37" patternUnits="userSpaceOnUse"><path d="M2 8l18 5 12-8M7 29l19-6 23 10" fill="none" stroke="#cbd1cf" opacity=".13"/><circle cx="39" cy="16" r="1" fill="#111817" opacity=".3"/></pattern>`;
      const scene=el('g',{});
      const recessDepth=2.6; // Illustrative scene units, not measured incision depth.
      function applyZoom(){
        const anchor=project(0,0,-recessDepth/2);
        scene.setAttribute('transform',`translate(${anchor[0]} ${anchor[1]}) scale(${zoom}) translate(${-anchor[0]} ${-anchor[1]})`);
        svg.setAttribute('aria-label',`Interactive RTI dome, zoom ${Math.round(zoom*100)} percent. Scroll to zoom towards the goat; drag to orbit; double-click or press 0 to reset zoom.`);
      }
      function setZoom(next){zoom=Math.max(1,Math.min(4,next));applyZoom();}
      svg.setAttribute('tabindex','0');
      svg.addEventListener('wheel',e=>{
        e.preventDefault();e.stopPropagation();
        const pixels=e.deltaY*(e.deltaMode===1?16:e.deltaMode===2?460:1);
        setZoom(zoom*Math.exp(-Math.max(-150,Math.min(150,pixels))*.002));
      },{passive:false});
      svg.addEventListener('dblclick',e=>{e.preventDefault();e.stopPropagation();setZoom(1);});
      const oval=(cx,cy,rx,ry,n=32)=>Array.from({length:n},(_,i)=>[cx+rx*Math.cos(i/n*2*Math.PI),cy+ry*Math.sin(i/n*2*Math.PI)]);
      // Preserve the supplied tracing's pecked edges, islands and interior holes.
      const goat = window.RupeGoatContours.contours;
      const compound = (transform) => goat.map(shape => path(shape.map(transform),true)).join(' ');
      const recessClip=el('clipPath',{id:'goat-recess-opening',clipPathUnits:'userSpaceOnUse'},defs);
      const opening=el('path',{'clip-rule':'evenodd'},recessClip);
      const shadowMask=el('mask',{id:'goat-recess-shadow',maskUnits:'userSpaceOnUse',maskContentUnits:'userSpaceOnUse',x:-1000,y:-1000,width:3000,height:3000,'mask-type':'luminance'},defs);
      el('rect',{x:-1000,y:-1000,width:3000,height:3000,fill:'white'},shadowMask);
      const litFloor=el('path',{fill:'black','fill-rule':'evenodd',filter:'url(#recess-soft-edge)','data-lit-floor':''},shadowMask);
      // Airborne light stops at the solid rock silhouette. Its illumination
      // on the stone is drawn separately, so a beam cannot show through it.
      const beamMask=el('mask',{id:'dome-solid-rock',maskUnits:'userSpaceOnUse',maskContentUnits:'userSpaceOnUse',x:-1000,y:-1000,width:3000,height:3000,'mask-type':'luminance'},defs);
      el('rect',{x:-1000,y:-1000,width:3000,height:3000,fill:'white'},beamMask);
      const solidRock=el('path',{fill:'black','data-solid-rock-occlusion':''},beamMask);
      const sphereGradient=el('radialGradient',{id:'sphere-reflection',cx:'.5',cy:'.5',r:'.27'},defs);
      [{offset:0,'stop-color':'#fffdf0','stop-opacity':1},{offset:.15,'stop-color':'#fff6d1','stop-opacity':.95},{offset:.35,'stop-color':'#dce8dc','stop-opacity':.28},{offset:1,'stop-color':'#b4c5c2','stop-opacity':0}].forEach(a=>el('stop',a,sphereGradient));
      function normalize(v){const n=Math.hypot(...v)||1;return v.map(k=>k/n);}
      const dot=(a,b)=>a.reduce((sum,x,i)=>sum+x*b[i],0);
      function hull(points){
        const pts=points.slice().sort((a,b)=>a[0]-b[0]||a[1]-b[1]);
        const cross=(a,b,c)=>(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);
        const half=list=>{const h=[];list.forEach(q=>{while(h.length>1&&cross(h[h.length-2],h[h.length-1],q)<=0)h.pop();h.push(q);});return h;};
        const lo=half(pts),hi=half(pts.slice().reverse());return [...lo.slice(0,-1),...hi.slice(0,-1)];
      }
      function draw() {
        scene.replaceChildren();
        const active=leds[frame-1];
        const rad=active?active.e*Math.PI/180:Math.PI/4;
        const light=active?[260*Math.cos(rad)*Math.cos(active.phi),260*Math.cos(rad)*Math.sin(active.phi),260*Math.sin(rad)]:[-180,-140,200];
        const poly=(points,attrs,parent=scene)=>el('path',{d:path(points.map(p=>project(...p)),true),...attrs},parent);
        const rock=[[-320,-205,0],[320,-205,0],[320,205,0],[-320,205,0]];
        solidRock.setAttribute('d',path(hull([...rock,...rock.map(([x,y])=>[x,y,-12])].map(p=>project(...p))),true));
        const edges=rock.map((p,i)=>[p,rock[(i+1)%4],[rock[(i+1)%4][0],rock[(i+1)%4][1],-12],[p[0],p[1],-12]]);
        edges.forEach(face=>poly(face,{fill:'#303936','fill-opacity':.72,stroke:'#53615a','stroke-opacity':.3,'stroke-width':.7}));
        poly(rock,{fill:'#58625e','fill-opacity':.82,stroke:'#83908a','stroke-opacity':.4,'stroke-width':.8});
        poly(rock,{fill:'url(#dome-stone)',opacity:.65});
        // The illumination pool lies on the surface and therefore follows both orbit axes.
        const ground=el('g',{},scene);
        poly(oval(0,0,150,130,56).map(([x,y])=>[x,y,.1]),{fill:'url(#dome-pool)',opacity:active?1:.25},ground);
        // Cut into z=0: the original tracing defines the aperture. Its complete
        // pecked contours and holes clip the floor, inner walls and shadows.
        const aperture=compound(([x,y])=>project(x,y,0));
        const floor=compound(([x,y])=>project(x,y,-recessDepth));
        opening.setAttribute('d',aperture);
        // A ray from the LED through the rim reaches the lower floor farther
        // from the light. Only that projected opening is illuminated; the
        // surrounding rock shadows the remaining floor inside the incision.
        const cast=([x,y])=>{const t=(light[2]+recessDepth)/light[2];return [light[0]+(x-light[0])*t,light[1]+(y-light[1])*t,-recessDepth];};
        litFloor.setAttribute('d',compound(p=>project(...cast(p))));
        const recess=el('g',{'clip-path':'url(#goat-recess-opening)','data-goat-recess':'','data-floor-z':-recessDepth,'data-rock-base-z':-12},scene);
        const floorValue=Math.round(157+22*Math.sin(rad));
        // An opaque stone backing seals every pecked mark, including narrow
        // parts where the lowered floor is hidden by the viewing angle.
        el('path',{d:aperture,fill:`rgb(${floorValue-6},${floorValue-7},${floorValue-19})`,'fill-opacity':1,'fill-rule':'evenodd','data-recess-backing':''},recess);
        el('path',{d:floor,fill:`rgb(${floorValue+5},${floorValue+2},${floorValue-12})`,'fill-opacity':1,'fill-rule':'evenodd','data-recess-floor':''},recess);
        el('path',{d:floor,fill:'url(#dome-stone)',opacity:.18,'fill-rule':'evenodd'},recess);
        el('path',{d:floor,fill:'#3c4035',opacity:active?.48:.22,'fill-rule':'evenodd',mask:'url(#goat-recess-shadow)','data-recess-shadow':''},recess);
        const faces=[];
        goat.forEach(shape=>{
          for(let i=0;i<shape.length;i++){
            const a=shape[i],b=shape[(i+1)%shape.length],dx=b[0]-a[0],dy=b[1]-a[1];
            // The source contour winding keeps the pecked area to the left,
            // including around islands: cavity normals face into that area.
            const len=Math.hypot(dx,dy)||1;
            const incoming=normalize([light[0]-(a[0]+b[0])/2,light[1]-(a[1]+b[1])/2,light[2]+recessDepth/2]);
            const lit=Math.max(0,(-dy*incoming[0]+dx*incoming[1])/len);
            const v=Math.round(112+lit*48);
            const pts=[[...a,0],[...b,0],[...b,-recessDepth],[...a,-recessDepth]];
            faces.push({pts,fill:`rgb(${v},${v+5},${v+1})`,depth:pts.reduce((n,p)=>n+project(...p)[2],0)/4});
          }
        });
        const walls=el('g',{'data-recess-walls':''},recess);
        faces.sort((a,b)=>a.depth-b.depth).forEach(f=>poly(f.pts,{fill:f.fill,stroke:f.fill,'stroke-width':.25},walls));
        el('path',{d:aperture,fill:'none',stroke:'#bfc8b7','stroke-opacity':.25,'stroke-width':.25,'data-recess-rim':''},recess);
        // Mirror-sphere highlight: the visible normal bisects light and observer directions.
        const sphereCenter=[175,85,14],sphere=project(...sphereCenter);
        const sphereRight=project(sphereCenter[0]+14*Math.cos(angle),sphereCenter[1]-14*Math.sin(angle),sphereCenter[2]);
        const radius=Math.hypot(sphereRight[0]-sphere[0],sphereRight[1]-sphere[1]);
        const right=[Math.cos(angle),-Math.sin(angle),0];
        const up=[-Math.sin(angle)*Math.sin(tilt),-Math.cos(angle)*Math.sin(tilt),Math.cos(tilt)];
        const view=[Math.sin(angle)*Math.cos(tilt),Math.cos(angle)*Math.cos(tilt),Math.sin(tilt)];
        const toLight=normalize(light.map((v,i)=>v-sphereCenter[i]));
        const half=normalize(toLight.map((v,i)=>v+view[i]));
        const hx=dot(half,right),hy=-dot(half,up);
        sphereGradient.setAttribute('cx',.5+hx*.5);sphereGradient.setAttribute('cy',.5+hy*.5);
        // Calibration sphere intentionally has no ground shadow; retain the moving reflection.
        el('circle',{cx:sphere[0],cy:sphere[1],r:radius,fill:'url(#sphere-chrome)',stroke:'#576266','stroke-width':.6},scene);
        el('circle',{cx:sphere[0],cy:sphere[1],r:radius,fill:'url(#sphere-reflection)',opacity:active?1:.18},scene);
        el('circle',{cx:sphere[0]+hx*radius,cy:sphere[1]+hy*radius,r:1.5,fill:'#fffbea',opacity:active?1:0,'data-sphere-highlight':''},scene);
        const boundary=[];
        for(let e=0;e<=90;e+=5)for(let a=0;a<360;a+=5)boundary.push(point(e,a*Math.PI/180));
        el('path',{d:path(hull(boundary),true),fill:'url(#dome-metal)',class:'d-shell'},scene);
        tiers.forEach(e=>el('path',{d:path(Array.from({length:65},(_,i)=>point(e,i/64*2*Math.PI)),true),class:'d-ring'},scene));
        for(let a=0;a<8;a++)el('path',{d:path(Array.from({length:35},(_,i)=>point(i/34*90,a*Math.PI/4))),class:'d-meridian'},scene);
        if(active){
          const q=point(active.e,active.phi), cone=el('g',{'pointer-events':'none',mask:'url(#dome-solid-rock)','data-light-beam':''},scene);
          // Soft, overlapping light volumes rather than a hard triangle or dashed ray.
          [1,.76,.5].forEach((k,i)=>{
            const rim=oval(0,0,110*k,90*k,40).map(([x,y])=>project(x,y,.6));
            el('path',{d:path(hull([q,...rim]),true),fill:'url(#dome-beam)',opacity:.3+i*.15},cone);
          });
          const target=project(0,0,-recessDepth);
          el('line',{x1:q[0],y1:q[1],x2:target[0],y2:target[1],stroke:'#fff2bd','stroke-width':1,opacity:.14},cone);
        }
        leds.map((l,i)=>({...l,i,p:point(l.e,l.phi)})).sort((a,b)=>a.p[2]-b.p[2]).forEach(l=>{
          const on=l.i===frame-1,done=l.i<frame-1;
          if(on){el('circle',{cx:l.p[0],cy:l.p[1],r:17,fill:'#fff0a9',opacity:.7,filter:'url(#dome-glow)'},scene);}
          const n=el('circle',{cx:l.p[0],cy:l.p[1],r:on?6:4.4,class:'d-led'+(on?' active':done?' captured':''),'data-led':l.i,role:'button',tabindex:0,'aria-label':`Inspect LED ${l.i+1}, elevation ${l.e} degrees, azimuth ${l.a*45} degrees`},scene);
          el('title',{},n).textContent=`LED ${l.i+1} · ${l.e}° elevation · ${l.a*45}° azimuth`;
          if(on)el('circle',{cx:l.p[0],cy:l.p[1],r:2.5,fill:'#fffceb','pointer-events':'none'},scene);
        });
        // Camera body, grip, controls and lens are world-space geometry: they rotate with the dome.
        const camera=el('g',{opacity:tilt>Math.PI/3?.24:1,'data-camera':''},scene);
        // Reference-inspired Infinity charcoal mirrorless body with separate matte and coated materials. All parts share a depth-sorted mesh.
        const cameraFaces=[];
        const face=(pts,fill,stroke='#59635a',width=.55)=>cameraFaces.push({pts,fill,stroke,width,depth:pts.reduce((n,p)=>n+project(...p)[2],0)/pts.length});
        const rounded=(x,y,w,h,r)=>{
          const pts=[];
          [[x+w-r,y+r,-90],[x+w-r,y+h-r,0],[x+r,y+h-r,90],[x+r,y+r,180]].forEach(([cx,cy,start])=>{
            for(let i=0;i<=5;i++){const a=(start+i*18)*Math.PI/180;pts.push([cx+r*Math.cos(a),cy+r*Math.sin(a)]);}
          });return pts;
        };
        const extrude=(shape,z0,z1,fill,cap=fill)=>{
          shape.forEach((a,i)=>{const b=shape[(i+1)%shape.length];face([[...a,z0],[...b,z0],[...b,z1],[...a,z1]],fill);});
          face(shape.map(p=>[...p,z0]),cap);face(shape.map(p=>[...p,z1]),cap);
        };
        extrude(rounded(-64,-32,128,64,10),292,334,'url(#camera-leather)');
        // Satin charcoal top plate, dark trim and a matte textured grip.
        extrude(rounded(-64,-33,128,22,7),291,336,'url(#camera-charcoal)');
        extrude(rounded(-64,26,128,7,3),291,335,'url(#camera-charcoal)');
        extrude(rounded(40,-9,25,36,9),286,337,'url(#camera-leather)');
        // Raised viewfinder prism and accessory shoe on the charcoal shoulder.
        const prism=[[-26,-33,294],[26,-33,294],[20,-51,306],[-20,-51,306],[-26,-33,334],[26,-33,334],[20,-51,328],[-20,-51,328]];
        [[0,1,2,3],[4,7,6,5],[0,4,5,1],[1,5,6,2],[2,6,7,3],[3,7,4,0]].forEach(ix=>face(ix.map(i=>prism[i]),'url(#camera-charcoal)'));
        face([[-13,-52,309],[13,-52,309],[13,-52,325],[-13,-52,325]],'#2c332d');
        [-16,13].forEach(x=>face([[x,-53,307],[x+3,-53,307],[x+3,-53,329],[x,-53,329]],'#5a645c'));
        // Rear LCD, bezel, eye cup and navigation buttons.
        extrude(rounded(-49,-14,74,37,3),334,336,'#0c1218','#111a22');
        face([[-45,-10,336.1],[21,-10,336.1],[21,19,336.1],[-45,19,336.1]],'#25424b','#39474d',.45);
        face([[-42,-8,336.2],[18,-8,336.2],[-42,17,336.2]],'#3e6068','#3e6068',0);
        extrude(rounded(-17,-40,34,20,4),334,341,'#171e23','#0b1117');
        const cylinder=(z1,z2,r1,r2,fill,segments=56)=>{
          const a=oval(0,0,r1,r1,segments),b=oval(0,0,r2,r2,segments);
          for(let i=0;i<segments;i++){
            const j=(i+1)%segments;
            face([[...a[i],z1],[...a[j],z1],[...b[j],z2],[...b[i],z2]],fill,'#252c32',.3);
          }
          face(a.map(p=>[...p,z1]),fill);face(b.map(p=>[...p,z2]),fill);
        };
        // Top dials: concentric metal caps, knurled rims and engraved index marks.
        const dial=(cx,cz,r,y0=-34)=>{
          const shape=oval(cx,cz,r,r,40);
          shape.forEach((a,i)=>{const b=shape[(i+1)%shape.length];face([[a[0],y0,a[1]],[b[0],y0,b[1]],[b[0],y0-5,b[1]],[a[0],y0-5,a[1]]],'#363c37','#3b4247',.5);});
          face(shape.map(([x,z])=>[x,y0-5,z]),'url(#camera-charcoal)');
          for(let i=0;i<12;i++){
            const a=i*Math.PI/6;
            const p=[cx+Math.cos(a)*(r-1),y0-5.1,cz+Math.sin(a)*(r-1)];
            const q=[cx+Math.cos(a)*(r-3),y0-5.1,cz+Math.sin(a)*(r-3)];
            face([p,q,[q[0]+.35,q[1],q[2]+.35]],'#62696b','#62696b',.35);
          }
        };
        dial(-44,317,12);dial(43,317,13);dial(23,326,5,-35);
        [0,1,2].forEach(i=>face(oval(34,5+i*8,2.3,2.3,16).map(([x,y])=>[x,y,337]),'#4b554c'));
        face(oval(48,6,6,6,24).map(([x,y])=>[x,y,338]),'#2d352f','#69776b');
        // Bayonet mount, aperture ring, broad ribbed zoom ring and front filter thread.
        cylinder(292,286,27,29,'#49554c');cylinder(286,278,29,30,'#303a33');
        cylinder(278,252,30,32,'url(#camera-metal)');
        for(let z=253;z<278;z+=2)cylinder(z,z+.6,32,32,'#28332c');
        // Fine longitudinal grip flutes, projected as world-space strips.
        for(let i=0;i<64;i++){
          const a=i/64*2*Math.PI,b=a+.012;
          face([[32*Math.cos(a),32*Math.sin(a),252],[32*Math.cos(b),32*Math.sin(b),252],[30*Math.cos(b),30*Math.sin(b),278],[30*Math.cos(a),30*Math.sin(a),278]],'#59675a','#59675a',.25);
        }
        cylinder(252,245,32,33,'#2b342f');cylinder(245,241,33,32,'#46524a');cylinder(241,237,32,31,'#2c3934');
        face(oval(0,0,28,28,64).map(([x,y])=>[x,y,236.8]),'url(#lens-glass)','#708991',1);
        face(oval(0,0,22,22,56).map(([x,y])=>[x,y,236.7]),'url(#lens-glass)','#3b5963',.6);
        face(oval(-8,-7,8,3,28).map(([x,y])=>[x,y,236.6]),'#34535f','#34535f',0);
        face(oval(8,6,4,2,20).map(([x,y])=>[x,y,236.5]),'#172d46','#172d46',0);
        cameraFaces.sort((a,b)=>a.depth-b.depth).forEach(f=>poly(f.pts,{fill:f.fill,stroke:f.stroke,'stroke-width':f.width,'stroke-linejoin':'round'},camera));
        // Strap anchors and a status lamp.
        [-68,68].forEach(x=>{
          const pts=oval(0,310,4,7,24).map(([y,z])=>project(x,y,z));
          el('path',{d:path(pts,true),fill:'none',stroke:'#778378','stroke-width':1.4},camera);
        });
        const status=project(56,-14,337);el('circle',{cx:status[0],cy:status[1],r:1.7,fill:active?'#e1dc64':'#6eb98c'},camera);
        const dimA=project(-260,215,0),dimB=project(260,215,0);
        el('path',{d:path([dimA,dimB]),class:'d-dimension'},scene);
        el('text',{x:385,y:Math.max(dimA[1],dimB[1])+28,'text-anchor':'middle',class:'d-caption'},scene).textContent='Ø 46 cm';
        const time=frame*3;
        output.textContent=`${String(frame).padStart(2,'0')} / 48`;
        host.querySelector('[data-elevation]').textContent=active?`${active.e}° / ${active.a*45}°`:'— / —';
        host.querySelector('[data-field-time]').textContent=`${Math.floor(time/60)}:${String(time%60).padStart(2,'0')}`;
        progress.value=frame;
        applyZoom();
      }
      function stop(){clearTimeout(timer);timer=null;play.textContent=frame===48?'↻ Replay':'▶ Run sequence';play.setAttribute('aria-pressed','false');}
      function tick(){if(frame>=48){stop();return;}frame++;draw();if(frame===48){stop();return;}timer=setTimeout(tick,+speed.value);}
      function run(){if(timer){stop();return;}if(frame===48)frame=0;play.textContent='Ⅱ Pause';play.setAttribute('aria-pressed','true');timer=setTimeout(tick,30);}
      play.addEventListener('click',run);
      host.querySelector('[data-step]').addEventListener('click',()=>{stop();frame=frame%48+1;draw();});
      host.querySelector('[data-reset]').addEventListener('click',()=>{frame=0;stop();draw();});
      rotation.addEventListener('input',()=>{angle=+rotation.value*Math.PI/180;draw();});
      elevationControl.addEventListener('input',()=>{tilt=+elevationControl.value*Math.PI/180;draw();});
      host.querySelector('[data-surface-view]').addEventListener('click',()=>{tilt=72*Math.PI/180;angle=-20*Math.PI/180;rotation.value=-20;elevationControl.value=72;draw();});
      svg.addEventListener('pointerdown',e=>{if(e.button!==0)return;drag={x:e.clientX,y:e.clientY,angle,tilt};dragged=false;svg.setPointerCapture(e.pointerId);});
      svg.addEventListener('pointermove',e=>{
        if(!drag)return;
        const dx=e.clientX-drag.x,dy=e.clientY-drag.y;
        if(Math.hypot(dx,dy)>4)dragged=true;
        if(!dragged)return;
        angle=drag.angle+dx*.008;tilt=Math.max(12*Math.PI/180,Math.min(78*Math.PI/180,drag.tilt-dy*.006));
        rotation.value=((angle*180/Math.PI+180)%360+360)%360-180;elevationControl.value=tilt*180/Math.PI;draw();
      });
      const endDrag=()=>{drag=null;};
      svg.addEventListener('pointerup',endDrag);svg.addEventListener('pointercancel',endDrag);svg.addEventListener('lostpointercapture',endDrag);
      svg.addEventListener('click',e=>{if(dragged){dragged=false;return;}const n=e.target.closest('[data-led]');if(n){stop();frame=+n.dataset.led+1;draw();}});
      svg.addEventListener('keydown',e=>{if(e.target===svg&&['+','=','-','_','0'].includes(e.key)){e.preventDefault();e.stopPropagation();setZoom(e.key==='0'?1:zoom*(e.key==='-'||e.key==='_'?1/1.2:1.2));return;}if(['Enter',' '].includes(e.key)&&e.target.hasAttribute('data-led')){e.preventDefault();stop();frame=+e.target.dataset.led+1;draw();svg.querySelector(`[data-led="${frame-1}"]`)?.focus();}});
      host.addEventListener('keydown',e=>e.stopPropagation());
      reveal.on('slidechanged',e=>{if(e.previousSlide===slide)stop();});
      document.addEventListener('visibilitychange',()=>{if(document.hidden)stop();});
      reveal.on('pdf-ready',()=>{stop();zoom=1;frame=48;draw();});
      if(reduce.matches||location.search.includes('print-pdf'))frame=48;
      draw();
    });
  }
  return {id:'rupe-dome',init};
})();
