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
import base64, io, json, re, shutil, subprocess, tempfile
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


def poster_tpl():
    s = tokenize((SRC / 'master-poster.svg').read_text(encoding='utf-8'))
    s = s.replace('letter-spacing="-4">ArcheoFOSS</text>', f'letter-spacing="-4">{WORD}</text>', 1)
    s = re.sub(r'(<text x="66" y="219"[^>]*)fill="\{\{INK\}\}"([^>]*>)2026</text>', rf'\1fill="{BLUE}"\g<2>2026</text>', s, count=1)
    assert WORD in s and re.search(rf'fill="{BLUE}"[^>]*>2026</text>', s), 'titolo locandina non trovato'
    top = 158 - CAP * 82                                   # parte alta di ARCHEO.FOSS
    s, n1 = re.subn(r'<text x="682" y="212"[^>]*>20</text>', '', s)
    s, n2 = re.subn(r'<text x="664" y="241"[^>]*>EDIZIONE</text>', '', s)
    assert n1 == n2 == 1, ('20/EDIZIONE non trovati', n1, n2)
    s = s.replace('</svg>', f'<g transform="translate({POSTER_RIGHT - COL_W} {top:.1f})">{edition_block()}</g></svg>', 1)
    return with_fonts(s)


# Numeri dei nodi (01–11): troppo piccoli sui formati piccoli (4–5 pt), quindi lì restano solo i pallini.
NO_LABELS_POSTERS = {'a5'}             # locandine senza numeri
LABEL_RE = r'<text x="[\d.]+" y="[\d.]+" font-size="12" fill="\{\{NODE\}\}">\d\d</text>'


def strip_labels(svg):
    svg, n = re.subn(LABEL_RE, '', svg)
    assert n == 11, ('numeri dei nodi trovati', n)
    return svg


def badge_a6_tpl():
    s = strip_labels(tokenize((SRC / 'master-badge-a6.svg').read_text(encoding='utf-8')))
    assert '>ArcheoFOSS 2026</text>' in s
    return with_fonts(s.replace('>ArcheoFOSS 2026</text>', f'>{WORD26}</text>', 1))


def badge_a7_tpl(a6_tokens):
    F = 'font-family="Inter,Arial,sans-serif"'
    art = a6_tokens[a6_tokens.index('<g transform="translate(0 345)'):a6_tokens.index('<text id="badge-name"')]
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
    return with_fonts(tokenize((SRC / 'master-logo-20.svg').read_text(encoding='utf-8')))


def qr_tpl():
    return (SRC / 'master-qr.svg').read_text(encoding='utf-8').replace('#252B29', '{{INK}}')


def screensaver(p):
    s = html_master
    s = s.replace(':root{color-scheme:light;--paper:#fff;--ink:#252B29;--accent:#D89277}',
                  f':root{{color-scheme:light;--paper:#fff;--ink:{p["INK"]};--accent:{p["ACC"]};--node:{p["NODE"]}}}', 1)
    s = s.replace('.node-dot{fill:var(--accent)', '.node-dot{fill:var(--node)', 1)
    s = s.replace('.node-label{fill:var(--accent)', '.node-label{fill:var(--node)', 1)
    s = s.replace(',\n  {u:.889,line:11},{u:.680,line:15},{u:.901,line:18}', ',\n  {u:.889,line:11},{u:.680,line:15}', 1)
    s = s.replace('for(let i=0;i<12;i++){', 'for(let i=0;i<11;i++){', 1)
    s = s.replace('<text class="brand" x="104" y="193">ArcheoFOSS</text>', f'<text class="brand" x="104" y="193">{WORD}</text>', 1)
    s = s.replace('.year{font-size:109px;font-weight:400;letter-spacing:-3px;fill:var(--ink)}',
                  f'.year{{font-size:109px;font-weight:400;letter-spacing:-3px;fill:{BLUE}}}', 1)
    top = 193 - CAP * 155                                  # parte alta di ARCHEO.FOSS nello screensaver
    k = 155 / 82                                           # stessa proporzione logo/blocco della locandina
    right = 1920 - 104                                     # margine destro = margine sinistro del logo
    n = s.count('<text class="edition-number"') + s.count('<text class="edition-label"')
    s = re.sub(r'\s*<text class="edition-(?:number|label)"[^>]*>[^<]*</text>', '', s)
    blk = edition_block().replace('{{ACC}}', p['ACC'])
    s = s.replace('<g id="typography">', f'<g id="typography"><g transform="translate({right - COL_W * k:.1f} {top:.1f}) scale({k:.4f})">{blk}</g>', 1)
    assert n == 2 and 'EDITION</text></g>' in s, 'screensaver: 20/EDITION non trovati'
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
