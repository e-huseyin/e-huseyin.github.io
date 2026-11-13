"""Crea tutte le stampe (tranne il programma) nelle tre combinazioni di colore.

Sorgenti (non modificare a mano i file generati):  assets/source/master-*.svg, assets/source/screensaver-master.html
Uscita:  assets/palette/<combinazione>/  ->  locandina-a0…a5.svg, logo.svg/.png, simbolo-20.svg/.png,
         qr-programma.svg/.png, badge-a6.svg, badge-a7.svg, screensaver.html
         assets/badge-templates.js  ->  modelli A6/A7 con segnaposto colore, usati dalla pagina

Cosa cambia rispetto ai master:
- 11 nodi invece di 12 (tolto il nodo 12)
- logo ARCHEO.FOSS2026: punto e «2026» sempre blu #027BFF
- colori: grafite -> INK, pesca -> ACC, nodi -> NODE, terracotta scura dei testi -> ACC2
- font Inter (400/600/700) incorporato in ogni SVG, preso dallo screensaver

Uso (dalla cartella af2026mediakit):  ../.venv/bin/python tools/palette_build.py
Richiede: fonttools, brotli, pillow.  Per i PNG di logo e simbolo usa qlmanage (macOS).
"""
import base64, io, json, math, re, shutil, subprocess, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
A = ROOT / 'assets'
SRC = A / 'source'
OUT = A / 'palette'
BLUE = '#027BFF'

PALETTES = {
    'grafite-pesca':    {'name': 'Grafite · Pesca',            'INK': '#252B29', 'ACC': '#D89277', 'NODE': '#D89277', 'ACC2': '#AC4B35'},
    'grafite-bordeaux': {'name': 'Grafite · Bordeaux · Blu',   'INK': '#252B29', 'ACC': '#762F3D', 'NODE': BLUE,      'ACC2': '#762F3D'},
    'nero-mattone':     {'name': 'Nero · Rosso mattone · Blu', 'INK': '#171717', 'ACC': '#A33B35', 'NODE': BLUE,      'ACC2': '#A33B35'},
}
POSTERS = {'a0': (841, 1189), 'a1': (594, 841), 'a2': (420, 594), 'a3': (297, 420), 'a4': (210, 297), 'a5': (148, 210)}

# ---------------------------------------------------------------- font
html_master = (SRC / 'screensaver-master.html').read_text(encoding='utf-8')
FONTS = {w: b for b, w in re.findall(
    r"@font-face\{font-family:AFInter;src:url\(data:font/woff2;base64,([^)]*)\) format\('woff2'\);font-weight:(\d+)", html_master)}
FONT_CSS = ''.join(f"@font-face{{font-family:Inter;src:url(data:font/woff2;base64,{b}) format('woff2');font-weight:{w}}}"
                   for w, b in sorted(FONTS.items()))
FONT_DEFS = f'<defs><style>{FONT_CSS}</style></defs>'


def text_width(text, size, weight='700', spacing=0.0):
    """Larghezza del testo in unità SVG, misurata sul font Inter vero."""
    from fontTools.ttLib import TTFont
    f = TTFont(io.BytesIO(base64.b64decode(FONTS[weight])))
    cmap, hmtx, upm = f.getBestCmap(), f['hmtx'], f['head'].unitsPerEm
    return sum(hmtx[cmap[ord(c)]][0] for c in text) * size / upm + spacing * (len(text) - 1)


# ---------------------------------------------------------------- trasformazioni comuni
WORD = f'ARCHEO<tspan fill="{BLUE}">.</tspan>FOSS'
WORD26 = WORD + f'<tspan fill="{BLUE}"> 2026</tspan>'


def tokenize(svg):
    """11 nodi + colori sostituiti da segnaposto."""
    svg = re.sub(r'<circle cx="810" cy="438\.31"[^>]*/>', '', svg)
    svg = re.sub(r'<text x="820" y="429\.31"[^>]*>12</text>', '', svg)
    svg = re.sub(r'(<circle [^>]*r="5\.5" )fill="#D89277"', r'\1fill="{{NODE}}"', svg)
    svg = re.sub(r'(<text [^>]*font-size="12" )fill="#D89277"', r'\1fill="{{NODE}}"', svg)
    svg = svg.replace('#D89277', '{{ACC}}').replace('#252B29', '{{INK}}').replace('#AC4B35', '{{ACC2}}')
    return svg.replace('12 numbered nodes', '11 numbered nodes')


def with_fonts(svg):
    return re.sub(r'(<svg\b[^>]*>)', lambda m: m.group(1) + FONT_DEFS, svg, count=1)


FAINT = .075                           # «20» chiaro dietro le linee: 7,5% del colore di accento


def faint(hexcol, a=FAINT):
    """Colore di accento mescolato al bianco: stesso aspetto della trasparenza, ma funziona anche nei PDF."""
    r, g, b = (int(hexcol[i:i + 2], 16) for i in (1, 3, 5))
    return '#%02X%02X%02X' % tuple(round(255 + (c - 255) * a) for c in (r, g, b))


def paint(tpl, p):
    tpl = tpl.replace('{{ACC_FAINT}}', faint(p['ACC']))
    tpl = re.sub(r'\{\{INK@([\d.]+)\}\}', lambda m: faint(p['INK'], float(m.group(1))), tpl)   # linee schiarite nei PDF
    tpl = tpl.replace('{{ACC_HALF}}', faint(p['ACC'], COL_OPACITY))      # capitello al 50% nei PDF
    for k in ('INK', 'ACC', 'NODE', 'ACC2'):
        tpl = tpl.replace('{{' + k + '}}', p[k])
    return tpl


# ---------------------------------------------------------------- modelli
def column(x, y, w, fill_attr):
    """Capitello (assets/source/master-colonna.svg), largo w, angolo in alto a sinistra in (x, y).
    Le linee prendono il colore del gruppo (fill_attr); il dettaglio bianco resta bianco."""
    src = (SRC / 'master-colonna.svg').read_text(encoding='utf-8')
    paths = ''.join(re.findall(r'<path\b[^>]*/>', src, flags=re.S)).replace('class="st0"', 'fill="#FFFFFF"')
    paths = re.sub(r'\s+', ' ', paths)
    k = w / 492
    return f'<g transform="translate({x:.1f} {y:.1f}) scale({k:.5f})" {fill_attr}>{paths}</g>'


# Blocco «20th EDITION» davanti al capitello: in alto allineato alle maiuscole del logo, a destra sul margine
CAP = 0.7275390625                     # altezza delle maiuscole di Inter / em
POSTER_RIGHT = 778                     # margine destro della locandina (840 - 62)
COL_W = 140                            # larghezza del capitello sulla locandina (unità della locandina)
COL_OPACITY = .5                       # capitello schiarito, così il testo davanti si legge
FB = 'font-family="AFInter,Inter,Arial,sans-serif" font-weight="700"'


def edition_block():
    """Capitello al 50% + «20th» (bianco con bordo) + «EDITION» sotto, centrati sull'asse del capitello.
    La base di EDITION coincide con il fondo del capitello. Coordinate locali: angolo in alto a sinistra = (0, 0),
    larghezza COL_W. Colore: {{ACC}}."""
    wc = COL_W
    hc = wc * 333.7 / 492
    cx = wc / 2
    size, esize, gap = 40, 9.5, 7
    w20 = text_width('20', size, '700', -4)
    yed = hc - .5
    y20 = yed - gap - CAP * esize
    x20 = cx - w20 / 2
    t20 = f'x="{x20:.1f}" y="{y20:.1f}" {FB} font-size="{size}" letter-spacing="-4" stroke-linejoin="round"'
    return (f'<g opacity="{COL_OPACITY}">' + column(0, 0, wc, 'fill="{{ACC}}"') + '</g>'
            f'<text {t20} fill="#FFFFFF" stroke="#FFFFFF" stroke-width="7">20</text>'
            f'<text {t20} fill="#FFFFFF" stroke="{{{{ACC}}}}" stroke-width="1.7">20</text>'
            f'<text x="{x20 + w20 + 2:.1f}" y="{y20 - size * .42:.1f}" {FB} font-size="{size * .34:.1f}" '
            f'fill="{{{{ACC}}}}" stroke="#FFFFFF" stroke-width="5" paint-order="stroke">th</text>'
            f'<text x="{cx + .8:.1f}" y="{yed:.1f}" text-anchor="middle" {FB} font-size="{esize}" letter-spacing="1.6" '
            f'fill="{{{{ACC}}}}" stroke="#FFFFFF" stroke-width="5" paint-order="stroke">EDITION</text>')


# Locandina A4 (840 x 1188 unità; A4 = 0,25 mm per unità; gli altri formati sono in scala)
P_M = 40                               # margine unico su tutti i lati: 10 mm sull'A4
P_L, P_R = P_M, 840 - P_M              # la riga sopra la data va da P_L a P_R: è il riferimento per allineare tutto
P_BOT = 1188 - P_M                     # base dell'ultima riga
P_HEAD_H = 110                         # altezza del logo dell'università e del capitello in cima
P_GAP = 50                             # stesso spazio: loghi -> maiuscole del titolo e base del titolo -> maiuscole del sottotitolo
P_QR = 126                             # lato del QR compreso il suo bordo bianco (moduli visibili da 4 a 33 su 37)
UNIBO = SRC / 'logo-unibo-disci.png'   # logo università + dipartimento (2387 x 891 px), colori originali
UNIBO_RATIO = 2387 / 891
POSTER_SUB = ['International conference on open software, hardware,', 'processes, data and formats in archaeological research']
BIG_20TH_SCALE = .80                   # grande «20th» chiaro dietro le linee: 80% del vecchio «20»
BIG_20_END = 816                       # dove finiva il vecchio «20» (x sulla locandina): «20th» finisce lì


def fit_size(text, weight, ls_ratio, width):
    """Corpo che fa occupare al testo esattamente `width` (spaziatura tra lettere proporzionale al corpo)."""
    return 100 * width / text_width(text, 100, weight, -100 * ls_ratio)


def strata_y(x, j):
    """Formula delle 20 linee stratigrafiche (coincide con i tracciati del master, scarto < 0,1)."""
    return (155 + j * 16 + 67 * math.sin(x / 900 * math.pi * 1.7) * math.exp(-((x - 400) / 420) ** 2)
            + 26 * math.sin(x / 140 + j * .08))


def strata_paths(x0=-30, x1=950, step=5):
    """Le linee allungate oltre i bordi della locandina (il foglio le taglia esattamente al bordo)."""
    out = []
    for j in range(20):
        d = ' '.join(('M' if i == 0 else 'L') + f'{x:.1f},{strata_y(x, j):.1f}' for i, x in enumerate(range(x0, x1 + 1, step)))
        w, o = ('1.65', '0.76') if j % 5 == 0 else ('1.05', '0.48')
        out.append(f'<path d="{d}" fill="none" stroke="{{{{INK}}}}" stroke-width="{w}" opacity="{o}"/>')
    return ''.join(out)


def big_20th(end=BIG_20_END):
    """Grande «20th» chiaro (coordinate interne del gruppo dell'arte: scala .87, spostamento 20); finisce a `end`."""
    size = 470 * BIG_20TH_SCALE
    w20 = text_width('20', size, '700', -40)
    sth, gap = size * .34, size * .02
    wth = text_width('th', sth, '700')
    x = (end - 20) / .87 - (w20 + gap + wth)
    a = 'fill="{{ACC}}" opacity=".075"'
    return (f'<text x="{x:.1f}" y="536" font-size="{size:.1f}" font-weight="700" {a} letter-spacing="-40">20</text>'
            f'<text x="{x + w20 + gap:.1f}" y="{536 - size * .42:.1f}" font-size="{sth:.1f}" font-weight="700" {a}>th</text>')


OLD_20 = re.compile(r'<text x="342" y="536" font-size="470" font-weight="700" fill="\{\{ACC\}\}" opacity="\.075" letter-spacing="-40">20</text>')
BADGE_20_END = 990 / 1.36010363 + 32  # sui badge il «th» finisce 60 unità (6 mm) prima del bordo destro
SYMBOL_20_END = 806                    # simbolo: il «th» finisce 10 unità prima del bordo


def sub_20th(svg, end=BIG_20_END):
    """Sostituisce il grande «20» chiaro del master con «20th»."""
    svg, n = OLD_20.subn(lambda m: big_20th(end), svg)
    assert n == 1, ('grande 20 non trovato', n)
    return svg


def poster_tpl():
    """Locandina, testata 3: in cima università (sinistra) e capitello «20th EDITION» (destra); sotto ARCHEO.FOSS 2026
    a tutta larghezza; sottotitolo; linee ondulate al vivo con 11 pallini e grande «20th»; riga di riferimento;
    data a tutta riga; VENUE a sinistra e QR del programma a destra; archeofoss.org in basso."""
    F4 = 'font-family="Inter,Arial,sans-serif" font-weight="400"'
    F6 = 'font-family="Inter,Arial,sans-serif" font-weight="600"'
    F7 = 'font-family="Inter,Arial,sans-serif" font-weight="700"'
    L, R, M, BOT, W = P_L, P_R, P_M, P_BOT, P_R - P_L
    # arte del master: linee allungate fino ai bordi + grande «20th»
    master = tokenize((SRC / 'master-poster.svg').read_text(encoding='utf-8'))
    i = master.index('<g transform="translate(20,312) scale(.87)">'); j = master.index('</g>', i) + 4
    art, n3 = re.subn(r'<path d="M15\.0,[^"]+" fill="none" stroke="\{\{INK\}\}" stroke-width="[\d.]+" opacity="[\d.]+"/>', '', master[i:j])
    assert n3 == 20, ('linee non trovate', n3)
    art = art.replace('<g transform="translate(20,312) scale(.87)">', '<g transform="translate(20,312) scale(.87)">' + strata_paths(), 1)
    art = sub_20th(art)
    # testata
    H = P_HEAD_H
    k = H / (COL_W * 333.7 / 492)
    logo = base64.b64encode(UNIBO.read_bytes()).decode()
    s_t = fit_size('ARCHEO.FOSS 2026', '700', 1 / 20.5, W)
    y_t = M + H + P_GAP + CAP * s_t                        # base del titolo
    head = [
        f'<image x="{L}" y="{M}" width="{H * UNIBO_RATIO:.1f}" height="{H}" href="data:image/png;base64,{logo}"/>',
        f'<g transform="translate({R - COL_W * k:.1f} {M}) scale({k:.4f})">{edition_block()}</g>',
        f'<text x="{L}" y="{y_t:.1f}" {F7} font-size="{s_t:.2f}" letter-spacing="{-s_t / 20.5:.2f}" fill="{{{{INK}}}}">'
        f'{WORD}<tspan fill="{BLUE}"> 2026</tspan></text>',
        *[f'<text x="{L}" y="{y_t + P_GAP + CAP * 21 + 28 * n:.1f}" {F4} font-size="21" fill="{{{{INK}}}}">{t}</text>'
          for n, t in enumerate(POSTER_SUB)],
    ]
    # parte bassa: tutto allineato alla riga sopra la data
    ds = fit_size('30 November – 1 December 2026', '700', 1 / 44, W)
    y_date = BOT - 278 + 12 + CAP * ds          # la data resta dov'è
    rule = round(y_date - CAP * ds - P_GAP, 1)  # riga → data = P_GAP, come in testata
    qr = (SRC / 'master-qr.svg').read_text(encoding='utf-8').replace('#252B29', '{{INK}}')
    qr_inner = qr[qr.index('>') + 1:qr.rindex('</svg>')]
    foot = [
        f'<path d="M{L},{rule}H{R}" stroke="{{{{INK}}}}" stroke-width="1.2"/>',
        f'<text x="{L}" y="{y_date:.1f}" {F7} font-size="{ds:.2f}" letter-spacing="{-ds / 44:.2f}" fill="{{{{INK}}}}">30 November – 1 December 2026</text>',
        f'<text x="{L}" y="{BOT - 158}" {F7} font-size="12" letter-spacing="2" fill="{{{{ACC}}}}">VENUE</text>',
        f'<text x="{L}" y="{BOT - 128}" {F6} font-size="19" fill="{{{{INK}}}}">Department of History and Cultures (DiSCi)</text>',
        f'<text x="{L}" y="{BOT - 102}" {F4} font-size="17" fill="{{{{INK}}}}">Alma Mater Studiorum – Università di Bologna</text>',
        f'<text x="{L}" y="{BOT - 78}" {F4} font-size="17" fill="{{{{INK}}}}">Piazza San Giovanni in Monte 2, 40124 Bologna, Italy</text>',
        f'<text x="{L}" y="{BOT}" {F7} font-size="24" fill="{{{{ACC}}}}">archeofoss.org</text>',
        f'<text x="{R + 2}" y="{BOT - 158}" text-anchor="end" {F7} font-size="12" letter-spacing="2" fill="{{{{ACC}}}}">PROGRAMME</text>',
        f'<g transform="translate({R - P_QR * 33 / 37:.1f} {BOT - 150}) scale({P_QR / 37:.4f})">{qr_inner}</g>',
        f'<text x="{R}" y="{BOT}" text-anchor="end" {F4} font-size="13" fill="{{{{INK}}}}">archeofoss.org/2026/programme</text>',
    ]
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="210mm" height="297mm" viewBox="0 0 840 1188" role="img" '
           'aria-label="ArcheoFOSS 2026 poster"><rect width="840" height="1188" fill="#FFFFFF"/>'
           + ''.join(head) + f'<g font-family="Inter,Arial,sans-serif">{art}</g>' + ''.join(foot) + '</svg>')
    return with_fonts(svg)


# Numeri dei nodi (01–11): troppo piccoli sui formati piccoli (4–5 pt), quindi lì restano solo i pallini.
NO_LABELS_POSTERS = {'a5'}             # locandine senza numeri
LABEL_RE = r'<text x="[\d.]+" y="[\d.]+" font-size="12" fill="\{\{NODE\}\}">\d\d</text>'


def strip_labels(svg):
    svg, n = re.subn(LABEL_RE, '', svg)
    assert n == 11, ('numeri dei nodi trovati', n)
    return svg


def badge_a6_tpl():
    s = sub_20th(strip_labels(tokenize((SRC / 'master-badge-a6.svg').read_text(encoding='utf-8'))), BADGE_20_END)
    assert '>ArcheoFOSS 2026</text>' in s
    return with_fonts(s.replace('>ArcheoFOSS 2026</text>', f'>{WORD26}</text>', 1))


def badge_a7_tpl(a6_tokens):
    F = 'font-family="Inter,Arial,sans-serif"'
    art = a6_tokens[a6_tokens.index('<g transform="translate(0 345)'):a6_tokens.index('<text id="badge-name"')]
    art = sub_20th(art, BADGE_20_END)
    # Fascia a tutta larghezza, schiacciata in verticale (KY) per stare tra intestazione (y<122) e nome (y>578).
    # Cerchi ed etichette dei nodi vengono tolti dal gruppo e ridisegnati senza deformazione.
    S, T, KY = 1.36010363, 196, 1.06
    SY = KY / .87                                      # scala verticale del gruppo esterno
    nodes = re.findall(r'<circle cx="([\d.]+)" cy="([\d.]+)" r="5\.5"[^>]*/>', art)
    labels = re.findall(r'<text x="[\d.]+" y="[\d.]+" font-size="12" fill="\{\{NODE\}\}">(\d\d)</text>', art)
    art = re.sub(r'<circle [^>]*r="5\.5"[^>]*/>', '', art)
    art = re.sub(r'<text x="[\d.]+" y="[\d.]+" font-size="12" fill="\{\{NODE\}\}">\d\d</text>', '', art)
    art = art.replace('translate(0 345) scale(1.36010363) translate(-32 -394)',
                      f'translate(0 {T}) scale({S} {SY:.6f}) translate(-32 -451.2)', 1)
    k = .87 * S
    for (cx, cy), lab in zip(nodes, labels):
        X = (20 + .87 * float(cx) - 32) * S
        Y = T + (312 + .87 * float(cy) - 451.2) * SY
        art += f'<circle cx="{X:.2f}" cy="{Y:.2f}" r="{5.5 * k:.2f}" fill="{{{{NODE}}}}" stroke="#FFFFFF" stroke-width="{2 * k:.2f}"/>'
        # numeri dei nodi non disegnati: sul badge sarebbero circa 4 pt
    assert len(nodes) == len(labels) == 11, (len(nodes), len(labels))
    q = a6_tokens.index('<g transform="translate(430 1282)')
    qr = a6_tokens[q:a6_tokens.index('</g>', q) + 4].replace(
        'translate(430 1282) scale(5.135135135)', 'translate(850 560) scale(4.054054054)', 1)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="105mm" height="74mm" viewBox="0 0 1050 740" role="img" '
           'aria-label="ArcheoFOSS 2026 A7 landscape badge, customizable name affiliation role">'
           '<rect x="0" y="0" width="1050" height="740" fill="#FFFFFF"/>' + art +
           f'<text x="56" y="88" {F} font-size="42" font-weight="700" fill="{{{{INK}}}}">{WORD26}</text>'
           f'<text x="56" y="124" {F} font-size="24" font-weight="600" fill="{{{{ACC2}}}}">20th edition</text>'
           f'<text x="994" y="56" text-anchor="end" {F} font-size="23" font-weight="600" fill="{{{{INK}}}}">30 Nov – 1 Dec 2026 · Bologna</text>'
           f'<text x="994" y="84" text-anchor="end" {F} font-size="20" fill="#656D65">Department of History and Cultures (DiSCi)</text>'
           f'<text x="994" y="110" text-anchor="end" {F} font-size="20" fill="#656D65">Piazza San Giovanni in Monte 2</text>'
           f'<text id="badge-name" x="56" y="626" {F} font-size="56" font-weight="700" fill="{{{{INK}}}}">YOUR NAME</text>'
           f'<text id="badge-affiliation" x="56" y="666" {F} font-size="26" font-weight="400" fill="#555D59">YOUR AFFILIATION</text>'
           f'<text id="badge-role" x="56" y="720" {F} font-size="24" font-weight="700" fill="{{{{ACC2}}}}" letter-spacing="1.2">PARTICIPANT</text>'
           + qr + '\n</svg>')
    return with_fonts(svg)


def logo_tpl():
    """Logo: ARCHEO.FOSS2026 su una riga, misurato sul font."""
    size, ls = 120, -4
    w = text_width('ARCHEO.FOSS 2026', size, '700', ls)
    W, H = round(w + 40), 160
    return with_fonts(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="ARCHEO.FOSS 2026">'
        f'<text x="20" y="128" font-family="Inter,Arial,sans-serif" font-size="{size}" font-weight="700" letter-spacing="{ls}" '
        f'fill="{{{{INK}}}}">{WORD26}</text></svg>')


def symbol_tpl():
    return with_fonts(sub_20th(tokenize((SRC / 'master-logo-20.svg').read_text(encoding='utf-8')), SYMBOL_20_END))


def qr_tpl():
    return (SRC / 'master-qr.svg').read_text(encoding='utf-8').replace('#252B29', '{{INK}}')


SS_TITLE = .60                         # screensaver: titolo al 60% della larghezza tra i margini
SS_SUB = 34                            # screensaver: corpo del sottotitolo (px)


def screensaver(p):
    s = html_master
    s = s.replace(':root{color-scheme:light;--paper:#fff;--ink:#252B29;--accent:#D89277}',
                  f':root{{color-scheme:light;--paper:#fff;--ink:{p["INK"]};--accent:{p["ACC"]};--node:{p["NODE"]}}}', 1)
    s = s.replace('.node-dot{fill:var(--accent)', '.node-dot{fill:var(--node)', 1)
    s = s.replace('.node-label{fill:var(--accent)', '.node-label{fill:var(--node)', 1)
    s = s.replace(',\n  {u:.889,line:11},{u:.680,line:15},{u:.901,line:18}', ',\n  {u:.889,line:11},{u:.680,line:15}', 1)
    s = s.replace('for(let i=0;i<12;i++){', 'for(let i=0;i<11;i++){', 1)
    # una riga: ARCHEO.FOSS 2026 a sinistra; a destra università e capitello alti uguali (il capitello sul margine);
    # maiuscole del titolo centrate sull'altezza dei loghi; sotto il sottotitolo
    L, R, top, H, G, GL = 104, 1920 - 104, 90, 120, 50, 48
    st = fit_size('ARCHEO.FOSS 2026', '700', 1 / 20.5, R - L) * SS_TITLE
    yt = top + (H + CAP * st) / 2
    ys = top + H + G + CAP * SS_SUB
    k = H / (COL_W * 333.7 / 492)
    cw, uw = COL_W * k, H * UNIBO_RATIO
    logo = base64.b64encode(UNIBO.read_bytes()).decode()
    blk = edition_block().replace('{{ACC}}', p['ACC'])
    typo = (f'<g id="typography">'
            f'<text x="{L}" y="{yt:.1f}" font-size="{st:.1f}" font-weight="700" letter-spacing="{-st / 20.5:.2f}" fill="var(--ink)">'
            f'{WORD}<tspan fill="{BLUE}"> 2026</tspan></text>'
            f'<image x="{R - cw - GL - uw:.1f}" y="{top}" width="{uw:.1f}" height="{H}" href="data:image/png;base64,{logo}"/>'
            f'<g transform="translate({R - cw:.1f} {top}) scale({k:.4f})">{blk}</g>'
            + ''.join(f'<text class="subtitle" x="{L}" y="{ys + SS_SUB * 1.35 * n:.1f}" style="font-size:{SS_SUB}px">{t}</text>'
                      for n, t in enumerate(POSTER_SUB)) + '</g>')
    assert L + text_width('ARCHEO.FOSS 2026', st, '700', -st / 20.5) < R - cw - GL - uw - 60, 'screensaver: titolo e loghi si toccano'
    i = s.index('<g id="typography">'); j = s.index('</g>', s.index('class="edition-label"')) + 4
    s = s[:i] + typo + s[j:]
    # grande «20th» chiaro al posto del «20», all'80%, finisce al margine destro
    size, ls = 650 * BIG_20TH_SCALE, -48 * BIG_20TH_SCALE
    w20 = text_width('20', size, '700', ls)
    sth, gap = size * .34, size * .02
    x = R - (w20 + gap + text_width('th', sth, '700'))
    wm = (f'<text class="watermark" x="{x:.1f}" y="1050" style="font-size:{size:.0f}px;font-weight:700;letter-spacing:{ls:.1f}px" aria-hidden="true">20</text>'
          f'<text class="watermark" x="{x + w20 + gap:.1f}" y="{1050 - size * .42:.1f}" style="font-size:{sth:.0f}px;font-weight:700;letter-spacing:0" aria-hidden="true">th</text>')
    s, n = re.subn(r'<text class="watermark" x="1088" y="1050" aria-hidden="true">20</text>', wm, s)
    assert n == 1 and 'EDITION</text></g>' in s and 'class="brand"' not in s, 'screensaver: testata o 20 non trovati'
    for old in ('i<11', WORD, '--node:', 'fill:var(--node)', '{u:.680,line:15}\n'):
        assert old in s, old
    return s


# ---------------------------------------------------------------- PNG
def qr_png(svg, path, scale=40):
    from PIL import Image, ImageDraw
    ink = re.search(r'fill="(#[0-9A-Fa-f]{6})"', svg.split('<path', 1)[1]).group(1)
    d = re.search(r'<path d="([^"]+)"', svg).group(1)
    n = 37
    img = Image.new('RGB', (n * scale, n * scale), 'white'); dr = ImageDraw.Draw(img)
    for x, y in re.findall(r'M(\d+) (\d+)h1v1h-1z', d):
        x, y = int(x), int(y)
        dr.rectangle([x * scale, y * scale, (x + 1) * scale - 1, (y + 1) * scale - 1], fill=ink)
    img.save(path)


def svg_png(svg_path, png_path, px=2400):
    """PNG con qlmanage (motore di anteprima di macOS); ritaglia il bianco intorno."""
    from PIL import Image, ImageChops
    # qlmanage disegna in un quadrato e taglia le immagini larghe: metto l'SVG al centro di una tela quadrata
    svg = svg_path.read_text(encoding='utf-8')
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', svg).group(1).split()]
    side = max(vb[2], vb[3])
    sq = f'{vb[0] - (side - vb[2]) / 2} {vb[1] - (side - vb[3]) / 2} {side} {side}'
    root = re.search(r'<svg\b[^>]*>', svg).group(0)
    new_root = re.sub(r'\s(width|height|viewBox)="[^"]*"', '', root).replace('<svg', f'<svg width="{side}" height="{side}" viewBox="{sq}"', 1)
    with tempfile.TemporaryDirectory() as tmp:
        sq_path = Path(tmp) / svg_path.name
        sq_path.write_text(svg.replace(root, new_root, 1), encoding='utf-8')
        subprocess.run(['qlmanage', '-t', '-s', str(px), '-o', tmp, str(sq_path)], check=True, capture_output=True)
        img = Image.open(Path(tmp) / (svg_path.name + '.png')).convert('RGB')
    bg = Image.new('RGB', img.size, 'white')
    box = ImageChops.difference(img, bg).getbbox()
    if box:
        pad = 24
        img = img.crop((max(box[0] - pad, 0), max(box[1] - pad, 0), min(box[2] + pad, img.width), min(box[3] + pad, img.height)))
    img.save(png_path)


# ---------------------------------------------------------------- costruzione
def main():
    poster, logo, symbol, qr = poster_tpl(), logo_tpl(), symbol_tpl(), qr_tpl()
    a6_tokens = tokenize((SRC / 'master-badge-a6.svg').read_text(encoding='utf-8'))
    a6, a7 = badge_a6_tpl(), badge_a7_tpl(a6_tokens)
    # non svuota la cartella: i file del programma (tools/programme_build.py) restano
    for pid, p in PALETTES.items():
        d = OUT / pid; d.mkdir(parents=True, exist_ok=True)
        for k, (w, h) in POSTERS.items():
            tpl = strip_labels(poster) if k in NO_LABELS_POSTERS else poster
            s = re.sub(r'width="[\d.]+mm" height="[\d.]+mm"', f'width="{w}mm" height="{h}mm"', paint(tpl, p), count=1)
            (d / f'locandina-{k}.svg').write_text(s, encoding='utf-8')
        for name, tpl in (('logo', logo), ('simbolo-20', symbol), ('qr-programma', qr), ('badge-a6', a6), ('badge-a7', a7)):
            (d / f'{name}.svg').write_text(paint(tpl, p), encoding='utf-8')
        (d / 'screensaver.html').write_text(screensaver(p), encoding='utf-8')
        qr_png(paint(qr, p), d / 'qr-programma.png')
        for name in ('logo', 'simbolo-20'):
            svg_png(d / f'{name}.svg', d / f'{name}.png')
    js = ('window.AF26_PALETTES=' + json.dumps({k: {x: v[x] for x in ('name', 'INK', 'ACC', 'NODE', 'ACC2')} for k, v in PALETTES.items()}, ensure_ascii=False) + ';\n'
          'window.AF26_BADGE={a6:' + json.dumps(a6) + ',a7:' + json.dumps(a7) + '};\n')
    (A / 'badge-templates.js').write_text(js, encoding='utf-8')
    print('ok', [p.name for p in sorted(OUT.iterdir())], len(list(OUT.rglob('*'))), 'file')
    print('larghezza logo locandina ARCHEO.FOSS @82:', round(62 + text_width('ARCHEO.FOSS', 82, '700', -4)), '(il "20" inizia a 682)')
    print('larghezza titolo A7 @42:', round(56 + text_width('ARCHEO.FOSS 2026', 42, '700')), '(il blocco a destra inizia a circa',
          round(994 - text_width('Department of History and Cultures (DiSCi)', 20, '400')), ')')
    print('larghezza titolo A6 @70:', round(text_width('ARCHEO.FOSS 2026', 70, '700')), 'su 1050')
    print('screensaver ARCHEO.FOSS @155:', round(104 + text_width('ARCHEO.FOSS', 155, '700', -8)), '(il "20" a destra è centrato a 1770)')


if __name__ == '__main__':
    main()
