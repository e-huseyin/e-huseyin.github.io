from pathlib import Path
import math,json,html,base64,shutil
ROOT=Path(__file__).resolve().parent.parent
A=ROOT/'assets'; (ROOT/'tools').mkdir(exist_ok=True)
panels=[
('From Fieldwork to Dissemination through FLOSS and FLOSH','Fieldwork','Acquisizione','Documentazione di scavo e continuità del dato fino alla disseminazione.',0),
('From Fragmented Data to Interoperable Knowledge: Semantic Technologies, Ontologies and Linked Open Data in Archaeology','Semantic knowledge','Struttura e verifica','Ontologie e Linked Open Data per integrare risorse e rendere esplicito il ragionamento.',1),
('OsteoArchaeology FLOS','Osteoarchaeology','Acquisizione','Strumenti aperti per lo studio, la conservazione e la condivisione dei resti biologici.',0),
('Beyond Visualisation: Assessing Uncertainty and Verifying Geometry in Hypothetical Virtual 3D Reconstructions','3D & uncertainty','Struttura e verifica','Incertezza interpretativa, verifica geometrica e documentazione delle ricostruzioni.',1),
('Artificial Intelligence in Archaeological Research: State of the Art, Limitations, and Advanced Applications','AI in research','Analisi e interpretazione','Valutazione critica dell’IA, riproducibilità e rapporto con i principi FOSS.',2),
('Artificial Intelligence and Digital Technologies for the Communication of Archaeological Heritage','AI & communication','Comunicazione e pratica','Comunicazione del patrimonio e accessibilità dei contenuti attraverso le tecnologie digitali.',3),
('Unlocking the Canopy, Locking the Data? LiDAR Archaeology and Its Quest for Open Science','LiDAR & openness','Acquisizione','Accesso ai dati LiDAR, rielaborazione e limiti della condivisione aperta.',0),
('Protocols for remote sensing in cultural heritage diagnostics','Remote sensing','Acquisizione','Protocolli di acquisizione e qualità delle procedure per la diagnostica del patrimonio.',0),
('FOSS beyond research: open source solutions in production for professional archaeology and heritage management','FOSS in practice','Comunicazione e pratica','Affidabilità e sostenibilità degli strumenti aperti nei contesti professionali.',3),
('FLOSS Geospatial Computing in Archaeology: Spatial Analysis, Modelling and Reproducible Workflows','Geospatial computing','Analisi e interpretazione','Analisi spaziale e flussi di lavoro geospaziali riproducibili.',2),
('Archaeological Landscapes as Socio-Ecological Systems: FLOSS-Based Modelling and Interpretation','Socio-ecological systems','Analisi e interpretazione','Modelli aperti per interpretare le relazioni fra paesaggi, società e ambiente.',2),
('Beyond the Site: R as an Open Tool for Critical Statistical and Spatial Analysis in Archaeology','R & critical analysis','Analisi e interpretazione','Analisi statistica e spaziale con R, assunzioni dei modelli e limiti del dato.',2),
]
(A/'panels.js').write_text('window.PANELS = '+json.dumps([dict(id=i+1,title=p[0],short=p[1],family=p[2],summary=p[3],cluster=p[4]) for i,p in enumerate(panels)],ensure_ascii=False,indent=2)+';\n')
fontcss=''
for w in [400,700]:
 f=A/'fonts'/f'inter-{w}.woff2'
 fontcss+=f"@font-face{{font-family:Inter;font-style:normal;font-weight:{w};src:url(data:font/woff2;base64,{base64.b64encode(f.read_bytes()).decode()}) format('woff2');}}"
INK='#252B29';PAPER='#F4F1E8';RED='#AC4B35';MUTED='#777D74'

def wrapsvg(body,w=900,h=660,title='Data Strata',embed=False):
 return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title"><title id="title">{html.escape(title)}</title><defs><style>{fontcss if embed else ''}text{{font-family:Inter,Arial,sans-serif}}</style></defs>{body}</svg>'''
def y_at(x,j,phase=0):
 return 155+j*16+67*math.sin((x/900)*math.pi*1.7+phase)*math.exp(-((x-400)/420)**2)+26*math.sin(x/140+j*.08)
# Positions are purely graphic. They carry panel IDs, not measured relationships.
node_specs=[(110,2),(245,6),(195,10),(385,3),(475,8),(625,14),(320,17),(555,2),(710,6),(805,11),(620,18),(810,18)]
def field(phase=0,active=0,number=True):
 s=''
 if number:s+=f'<text x="342" y="536" font-size="470" font-weight="700" fill="{RED}" opacity=".075" letter-spacing="-40">20</text>'
 for j in range(20):
  points=[(x,y_at(x,j,phase)) for x in range(15,901,5)]
  d='M'+' L'.join(f'{x:.1f},{y:.1f}' for x,y in points)
  s+=f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{1.65 if j%5==0 else 1.05}" opacity="{.76 if j%5==0 else .48}"/>'
 for i,(x,j) in enumerate(node_specs):
  y=y_at(x,j,phase)
  if active and active!=i+1:
   s+=f'<circle cx="{x}" cy="{y:.2f}" r="3.7" fill="{INK}" opacity=".32"/>'
  else:
   s+=f'<circle cx="{x}" cy="{y:.2f}" r="{9 if active else 5.5}" fill="{RED}" stroke="{PAPER}" stroke-width="2"/>'
   if active:s+=f'<circle cx="{x}" cy="{y:.2f}" r="19" fill="none" stroke="{RED}" stroke-width="1.2"/>'
  if not active:
   s+=f'<text x="{x+10}" y="{y-9:.2f}" font-size="12" fill="{RED}">{i+1:02}</text>'
 return s
(A/'strata.svg').write_text(wrapsvg(field(),title='Venti linee e dodici segni: composizione generativa simbolica'))
(A/'strata-plain.svg').write_text(wrapsvg(field(number=False),title='Campo di linee stratificate'))
for n in range(1,13):
 (A/f'panel-field-{n:02}.svg').write_text(wrapsvg(field(active=n,number=False),title=f'Variante grafica del panel {n:02}'))

def poster(size='a4',panel=None):
 w,h=(840,1188) if size=='a4' else (592,840)
 f=w/840
 def txt(x,y,text,fs=24,weight=400,fill=INK,extra=''):
  return f'<text x="{x}" y="{y}" font-size="{fs}" font-weight="{weight}" fill="{fill}" {extra}>{html.escape(text)}</text>'
 s=f'<rect width="{w}" height="{h}" fill="{PAPER}"/>'
 s+=f'<g transform="scale({f})">'
 s+=txt(62,67,'PROPOSTA DI IDENTITÀ VISIVA',13,400,MUTED, 'letter-spacing="2"')
 s+=txt(62,158,'ArcheoFOSS',82,700,INK,'letter-spacing="-4"')
 s+=txt(66,219,'2026',62,400)
 s+=txt(682,212,'20',74,700,RED)
 s+=txt(664,241,'EDIZIONE',11,400,RED,'letter-spacing="2"')
 s+=txt(65,282,'Open software, hardware, processes,',21)
 s+=txt(65,310,'data and formats in archaeological research',21)
 s+=f'<g transform="translate(20,312) scale(.87)">{field(active=panel or 0,number=not bool(panel))}</g>'
 s+=f'<path d="M65,901H775" stroke="{INK}" stroke-width="1.2"/>'
 s+=txt(65,955,'30 NOV — 01 DIC 2026',39,700)
 s+=txt(65,1004,'Bologna + online',27)
 if size=='a4':
  s+=txt(65,1046,'Dipartimento di Storia e Culture',18)
  s+=txt(65,1073,'Alma Mater Studiorum – Università di Bologna',18)
 else:
  s+=txt(65,1046,'Università di Bologna',20)
 s+=txt(65,1135,'archeofoss.org',22,700,RED)
 s+=txt(470,1135,'BOZZA / LOGHI DA CONFERMARE',11,400,MUTED)
 s+='</g>'
 result=wrapsvg(s,w,h,f'ArcheoFOSS 2026, bozza {size.upper()}',embed=True)
 physical=('210mm','297mm') if size=='a4' else ('148mm','210mm')
 return result.replace(f'width="{w}" height="{h}"',f'width="{physical[0]}" height="{physical[1]}"',1)
(A/'poster-a4.svg').write_text(poster())
(A/'poster-a5.svg').write_text(poster('a5'))
for n in [2,7,12]:
 p=panels[n-1]
 s=f'<rect width="700" height="900" fill="{PAPER}"/>'
 s+=f'<text x="42" y="61" font-size="22" font-weight="700" fill="{INK}">ArcheoFOSS 2026</text>'
 s+=f'<text x="42" y="166" font-size="100" font-weight="700" fill="{RED}">{n:02}</text>'
 s+=f'<g transform="translate(0,185) scale(.77)">{field(active=n,number=False)}</g>'
 words=p[1].split();lines=[''];
 for word in words:
  if len(lines[-1]+word)>22:lines.append('')
  lines[-1]+=(' ' if lines[-1] else '')+word
 for i,l in enumerate(lines):s+=f'<text x="42" y="{746+i*41}" font-size="35" font-weight="700" fill="{INK}">{html.escape(l)}</text>'
 s+=f'<text x="42" y="855" font-size="15" fill="{MUTED}">30 NOV — 01 DIC 2026 / BOLOGNA + ONLINE</text>'
 (A/f'panel-card-{n:02}.svg').write_text(wrapsvg(s,700,900,'Variante di concept: '+p[1],embed=True))
print('SVG assets and panel dataset built.')

# Preserve the original assets as option 2, then create option 1 at the default paths.
# Existing geometry and embedded fonts are identical between palettes.
legacy=A/'palettes'/'carta';legacy.mkdir(parents=True,exist_ok=True)
(A/'favicon.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" fill="#F4F1E8"/><text x="6" y="44" fill="#AC4B35" font-family="Arial,sans-serif" font-size="39" font-weight="700">20</text></svg>')
colors={'#F4F1E8':'#FFFFFF','#252B29':'#252B29','#AC4B35':'#D89277','#777D74':'#656D65','#656D65':'#656D65','#CFD1C7':'#CFD1C7'}
for svg in sorted(A.glob('*.svg')):
 shutil.copy2(svg,legacy/svg.name)
 content=svg.read_text()
 for old,new in colors.items():content=content.replace(old,new)
 svg.write_text(content)
print('Both palettes built: 1 Bianco / Grafite / Pesca; 2 Carta / Grafite / Ossido.')

# Programme concepts depend on the existing field graphics and dataset.
import runpy
runpy.run_path(str(ROOT/"tools"/"build_programme.py"),run_name="__main__")
