"""Build editable programme concepts for both folds and both palettes.
Day/panel assignments are illustrative, not a confirmed programme.
DL uses an equal-panel accordion fold: three 99 x 210 mm panels.
"""
from pathlib import Path
import base64, html, json, textwrap
ROOT=Path(__file__).resolve().parent.parent
A=ROOT/'assets'
PANELS=json.loads((A/'panels.js').read_text().split('=',1)[1].strip().rstrip(';'))
FONT=''
for weight in [400,500,600,700]:
 data=base64.b64encode((A/'fonts'/f'inter-{weight}.woff2').read_bytes()).decode()
 FONT+=f"@font-face{{font-family:Inter;font-style:normal;font-weight:{weight};src:url(data:font/woff2;base64,{data}) format('woff2');}}"
PALETTES={'bianco':('#FFFFFF','#252B29','#D89277','#656D65','#CFD1C7'), 'carta':('#F4F1E8','#252B29','#AC4B35','#656D65','#CFD1C7')}

class Sheet:
 def __init__(self,palette,kind,side):
  self.paper,self.ink,self.accent,self.muted,self.rule=PALETTES[palette]
  self.kind=kind;self.side=side;self.palette=palette
  self.w,self.h=(1680,1188) if kind=='bifold' else (1188,840)
  self.pw=self.w//(2 if kind=='bifold' else 3)
  self.s=[f'<rect width="{self.w}" height="{self.h}" fill="{self.paper}"/>']
 def txt(self,x,y,s,fs=23,weight=400,color=None,extra=''):
  self.s.append(f'<text x="{x}" y="{y}" font-size="{fs}" font-weight="{weight}" fill="{color or self.ink}" {extra}>{html.escape(s)}</text>')
 def rule_at(self,x,y,w=None):
  self.s.append(f'<path d="M{x},{y}h{w or self.pw-112}" stroke="{self.rule}" stroke-width="1.1" fill="none"/>')
 def lines(self,x,y,s,fs=23,limit=55,color=None,weight=400,leading=None):
  for row in textwrap.wrap(s,width=limit,break_long_words=False,break_on_hyphens=False):
   self.txt(x,y,row,fs,weight,color);y+=leading or fs*1.28
  return y
 def graphic(self,x,y,w,h):
  src=A/'strata.svg' if self.palette=='bianco' else A/'palettes/carta/strata.svg'
  body=src.read_text().split('</defs>',1)[1].rsplit('</svg>',1)[0]
  self.s.append(f'<svg x="{x}" y="{y}" width="{w}" height="{h}" viewBox="0 0 900 660" preserveAspectRatio="xMidYMid meet">{body}</svg>')
 def footer(self,col,label):
  m=56 if self.kind=='bifold' else 32;x=col*self.pw+m
  self.rule_at(x,self.h-87,self.pw-2*m)
  self.txt(x,self.h-60,label,15 if self.kind=='bifold' else 12,400,self.muted)
  self.txt(x,self.h-32,'BOZZA · GIORNI E ORARI DA CONFERMARE',14 if self.kind=='bifold' else 11,400,self.muted)
 def day(self,col,date,panels,compact=False):
  m=56 if not compact else 32;x=col*self.pw+m;w=self.pw-2*m
  self.txt(x,66 if not compact else 45,'PROGRAMMA / INTERNO',15 if not compact else 12,400,self.accent, 'letter-spacing="1.5"')
  self.txt(x,143 if not compact else 109,date,55 if not compact else 34,600)
  self.txt(x,184 if not compact else 142,'ARcheoFOSS 2026'.replace('ARcheo','Archeo'),23 if not compact else 17)
  self.txt(x,222 if not compact else 174,'DISTRIBUZIONE INDICATIVA DEI PANEL',13 if not compact else 11,400,self.muted)
  y=266 if not compact else 208
  for p in panels:
   self.rule_at(x,y,w)
   self.txt(x,y+29 if not compact else y+22,f"{p['id']:02}",22 if not compact else 17,600,self.accent)
   tx=x+(54 if not compact else 34)
   end=self.lines(tx,y+29 if not compact else y+22,p['title'] if not compact else p['short'],23 if not compact else 19,54 if not compact else 28,weight=500,leading=29 if not compact else 25)
   self.txt(tx,end+7,'ORARIO / SALA / INTERVENTI DA INSERIRE' if not compact else 'ORARIO / SALA DA INSERIRE',12 if not compact else 10,400,self.muted)
   y=max(y+(116 if not compact else 88),end+38 if not compact else end+28)
  self.footer(col,'30 NOV — 01 DIC 2026 / BOLOGNA + ONLINE' if not compact else 'archeofoss.org/2026')
 def cover(self,col,compact=False):
  m=56 if not compact else 32;x=col*self.pw+m
  self.txt(x,66 if not compact else 45,'20ª EDIZIONE / PROGRAMMA',15 if not compact else 11,400,self.accent,'letter-spacing="1.2"')
  self.txt(x,172 if not compact else 128,'ArcheoFOSS',75 if not compact else 44,700,extra='letter-spacing="-3"' if not compact else 'letter-spacing="-2"')
  self.txt(x,265 if not compact else 183,'2026',67 if not compact else 48,400)
  self.lines(x,318 if not compact else 241,'Open software, hardware, processes, data and formats in archaeological research',24 if not compact else 17,51 if not compact else 32)
  self.graphic(col*self.pw+12,330 if not compact else 278,self.pw-24,526 if not compact else 320)
  y=910 if not compact else 645
  self.rule_at(x,y,self.pw-2*m)
  self.txt(x,y+53 if not compact else y+40,'30 NOVEMBRE',38 if not compact else 24,600)
  self.txt(x,y+98 if not compact else y+76,'1 DICEMBRE 2026',38 if not compact else 24,600)
  self.txt(x,y+146 if not compact else y+112,'Bologna + online',28 if not compact else 20)
  self.txt(x,self.h-50 if not compact else self.h-30,'archeofoss.org/2026',22 if not compact else 15,600,self.accent)
 def info(self,col,compact=False):
  m=56 if not compact else 32;x=col*self.pw+m
  self.txt(x,66 if not compact else 45,'ARCHEOFOSS 2026 / INFORMAZIONI',15 if not compact else 11,400,self.accent,'letter-spacing="1"')
  self.txt(x,146 if not compact else 111,'Partecipare.',54 if not compact else 37,600)
  blocks=[('BOLOGNA','Dipartimento di Storia e Culture · Alma Mater Studiorum – Università di Bologna'),('IN PRESENZA / ONLINE','Sala e collegamento online da aggiungere al programma definitivo.'),('PROGRAMMA COMPLETO','Titoli, relatori, orari e aggiornamenti sul sito del convegno.')]
  y=217 if not compact else 169
  for label,copy in blocks:
   self.rule_at(x,y,self.pw-2*m);self.txt(x,y+34 if not compact else y+25,label,18 if not compact else 13,600,self.accent)
   end=self.lines(x,y+79 if not compact else y+55,copy,25 if not compact else 18,55 if not compact else 32,leading=35 if not compact else 25)
   y=end+(45 if not compact else 33)
  if not compact:
   self.txt(x,y+8,'12 PANEL / UN CAMPO COMUNE',17,600,self.accent)
   y+=53
   for p in PANELS:
    px=x+(self.pw/2-25 if p['id']>6 else 0)
    yy=y+((p['id']-1)%6)*44
    self.txt(px,yy,f"{p['id']:02}",17,600,self.accent)
    short=p['short'] if len(p['short'])<=24 else p['short'][:22]+'…'
    self.txt(px+35,yy,short,18)
  else:
   self.txt(x,min(y+35,708),'archeofoss.org/2026',19,600,self.accent)
  self.footer(col,'PROPOSTA DI IMPAGINAZIONE / INFO DA CONFERMARE' if not compact else 'SEDE E COLLEGAMENTO DA CONFERMARE')
 def index(self,col):
  x=col*self.pw+32
  self.txt(x,45,'ARCHEOFOSS 2026 / INDICE',11,400,self.accent,'letter-spacing="1"')
  self.txt(x,111,'Dodici panel.',36,600)
  y=169
  for p in PANELS:
   self.rule_at(x,y,self.pw-64);self.txt(x,y+23,f"{p['id']:02}",16,600,self.accent)
   end=self.lines(x+34,y+23,p['short'],17,30,weight=500,leading=21)
   y=max(y+47,end+3)
  self.footer(col,'ETICHETTE BREVI / TITOLI COMPLETI ONLINE')
 def map(self,col):
  x=col*self.pw+32
  self.txt(x,45,'ORIENTARSI / MAPPA TEMATICA',11,400,self.accent,'letter-spacing="1"')
  self.txt(x,111,'Un campo',36,600);self.txt(x,153,'comune.',36,600)
  groups=[('Acquisizione','01 / 03 / 07 / 08'),('Struttura e verifica','02 / 04'),('Analisi e interpretazione','05 / 10 / 11 / 12'),('Comunicazione e pratica','06 / 09')]
  y=216
  for title,ids in groups:
   self.rule_at(x,y,self.pw-64)
   end=self.lines(x,y+28,title,21,27,weight=500,leading=27)
   self.txt(x,end+12,ids,17,400,self.accent);y=end+58
  self.graphic(col*self.pw+12,588,self.pw-24,155)
  self.footer(col,'RAGGRUPPAMENTO EDITORIALE / NON UFFICIALE')
 def save(self):
  folds=2 if self.kind=='bifold' else 3
  guides=''.join(f'<path d="M{self.pw*i},0V{self.h}" stroke="{self.rule}" stroke-width="1" stroke-dasharray="7 7"/>' for i in range(1,folds))
  desc='Due facciate interne, una per giorno, e copertina/retro esterni.' if folds==2 else 'Tre pannelli per lato, sei facciate, piega a fisarmonica. Due giorni sintetici e mappa tematica all’interno.'
  size=('420mm','297mm') if folds==2 else ('297mm','210mm')
  svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{size[0]}" height="{size[1]}" viewBox="0 0 {self.w} {self.h}" role="img" aria-labelledby="programme-title programme-desc"><title id="programme-title">ArcheoFOSS 2026 · {self.kind} · {self.side}</title><desc id="programme-desc">{html.escape(desc)} Distribuzione dei panel indicativa, orari e programma da confermare.</desc><defs><style>{FONT}text{{font-family:Inter,Arial,sans-serif}}</style></defs>'+''.join(self.s)+f'<g id="fold-guides">{guides}</g></svg>'
  dest=A if self.palette=='bianco' else A/'palettes/carta'
  dest.mkdir(parents=True,exist_ok=True)
  name=f'programme-{self.kind}-{self.side}.svg'
  (dest/name).write_text(svg)
  print(f'{self.palette}: {name}')

for palette in PALETTES:
 for kind in ['bifold','dl']:
  for side in ['outer','inner']:
   sheet=Sheet(palette,kind,side)
   if kind=='bifold':
    if side=='outer':sheet.info(0);sheet.cover(1)
    else:sheet.day(0,'30 novembre',PANELS[:6]);sheet.day(1,'1 dicembre',PANELS[6:])
   elif side=='outer':sheet.index(0);sheet.info(1,True);sheet.cover(2,True)
   else:sheet.day(0,'30 novembre',PANELS[:6],True);sheet.day(1,'1 dicembre',PANELS[6:],True);sheet.map(2)
   sheet.save()
