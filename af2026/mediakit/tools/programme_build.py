"""Programma pieghevole A3: due SVG (esterno, interno) e un PDF fronte/retro per ogni combinazione di colore.

Piegatura: A3 verticale piegato a metà in orizzontale, poi a U in tre (chiuso 99 x 210 mm). Fronte-retro sul lato lungo.
- Lato esterno: riga alta capovolta = 3 copertina (97 mm), 2 aule, comitato e QR, 1 calendario dei due giorni;
                riga bassa = 4 (97 mm), 5, 6: 1 dicembre -> si vedono aprendo la U.
- Lato interno: girato di 180° (dietro la 4 c'è la 7), 30 novembre in sei mezze colonne allineate alle pieghe.
Testo completo, senza abbreviazioni.

Unità: 0,1 mm (foglio 2970 x 4200). Testo misurato sul font Inter vero, quindi a capo identici in browser e PDF.
Uso (da af2026mediakit):  ../.venv/bin/python tools/programme_build.py
"""
import base64, io, re, sys, tempfile
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
from programme_parse import parse                       # noqa: E402
import palette_build as PB                              # noqa: E402  (palette, font, logo, arte)

A = PB.A
OUT = PB.OUT
PT = 3.5278                                            # 1 pt in unità (0,1 mm)
W, H = 2970, 4200
FAM = {'400': 'Inter', '600': 'Inter-SemiBold', '700': 'Inter-Bold'}
GREY, GREY2, RULE = '#3A403D', '#3A403D', '#C9CFC9'

# ---------------------------------------------------------------- font e misure
from fontTools.ttLib import TTFont                     # noqa: E402
_FONTS = {w: TTFont(io.BytesIO(base64.b64decode(b))) for w, b in PB.FONTS.items()}
_CMAP = {w: f.getBestCmap() for w, f in _FONTS.items()}


def width(text, weight, size):
    f, cmap = _FONTS[weight], _CMAP[weight]
    hm, upm = f['hmtx'], f['head'].unitsPerEm
    text = text.replace('ğ', 'g').replace('Ğ', 'G')
    return sum(hm[cmap.get(ord(c), cmap[ord('?')])][0] for c in text) * size / upm


def wrap(text, weight, size, maxw):
    out, cur = [], ''
    for word in text.split():
        nxt = (cur + ' ' + word).strip()
        if cur and width(nxt, weight, size) > maxw:
            out.append(cur); cur = word
        else:
            cur = nxt
    if cur:
        out.append(cur)
    return out


FONT_CSS = ''.join(f"@font-face{{font-family:'{FAM[w]}';src:url(data:font/woff2;base64,{b}) format('woff2')}}"
                   for w, b in sorted(PB.FONTS.items()))


GB = 'ğ'


def T(x, y, text, weight='400', pt=7.5, fill='{{INK}}', anchor='start', extra=''):
    a = '' if anchor == 'start' else f' text-anchor="{anchor}"'
    out = (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FAM[weight]}" font-size="{pt * PT:.2f}" '
           f'fill="{fill}"{a}{extra}>{escape(text.replace(GB, "g"))}</text>')
    if 'ğ' in text:                       # il font ridotto non ha la ğ: g + breve disegnata
        s_ = pt * PT
        x0 = x - (width(text, weight, s_) if anchor == 'end' else width(text, weight, s_) / 2 if anchor == 'middle' else 0)
        sw = {'400': .075, '600': .09, '700': .1}[weight] * s_
        for i, c in enumerate(text):
            if c == 'ğ':
                cx = x0 + width(text[:i], weight, s_) + width('g', weight, s_) / 2
                out += (f'<path d="M{cx - .15 * s_:.1f},{y - .78 * s_:.1f}Q{cx:.1f},{y - .56 * s_:.1f} {cx + .15 * s_:.1f},{y - .78 * s_:.1f}" '
                        f'fill="none" stroke="{fill}" stroke-width="{sw:.2f}" stroke-linecap="round"/>')
    return out


# ---------------------------------------------------------------- stili del programma (pt)
S = {
    'day':     ('700', 12.0, '{{INK}}'),
    'room':    ('700', 9.0, '#FFFFFF'),          # nella scatola colorata
    'session': ('700', 8.2, '{{INK}}'),
    'chairs':  ('400', 7.3, GREY),          # disegnato inclinato (ITALIC)
    'time':    ('600', 7.3, '{{ACC2}}'),
    'title':   ('600', 7.8, '{{INK}}'),
    'names':   ('400', 7.3, GREY),
    'break':   ('400', 7.3, GREY2),
    'pause':   ('700', 7.4, '{{INK}}'),          # coffee / lunch break: riga in una scatola
    'note':    ('400', 7.1, GREY2),
    'gap':     ('400', 0, '{{INK}}'),            # spazio vuoto (altezza in 'gap_h')
}
LEAD = 1.20
GUTTER = 150          # colonna degli orari (ricalcolata in base al corpo: set_gutter)
GAP_H = {'after_session': 6, 'after_chairs': 10}     # spazio dopo il titolo del panel e dopo i chair
ROOM_BOX = 1.45       # altezza della scatola dell'aula (x interlinea)
PAUSE_BOX = 1.4       # altezza della scatola delle pause
BEFORE = {'room': 50, 'session': 36, 'item': 20}     # spazio prima di aula, panel, intervento
ITALIC = {'chairs'}


def set_gutter():
    global GUTTER
    GUTTER = round(width('00:00–00:00', S['time'][0], S['time'][1] * PT) + 26)


def lh(style, text=''):
    if style == 'gap':
        return GAP_H[text]
    if style == 'room':
        return S[style][1] * PT * LEAD * ROOM_BOX
    if style == 'pause':
        return S[style][1] * PT * LEAD * PAUSE_BOX
    return S[style][1] * PT * LEAD


class Unit:
    """Blocco che non si spezza tra due colonne."""
    def __init__(self, before):
        self.before, self.rows = before, []   # rows: (style, text, indent, gutter_text)

    def add(self, style, text, w, indent=0, gutter=None):
        wt, pt, _ = S[style]
        for i, line in enumerate(wrap(text, wt, pt * PT, w - indent)):
            self.rows.append((style, line, indent, gutter if i == 0 else None))

    @property
    def height(self):
        return sum(lh(r[0], r[1]) for r in self.rows)


def units_for_day(day, w):
    us = []
    u = Unit(0); u.add('day', day['date'], w); us.append(u)
    for room in day['rooms']:
        pending = Unit(BEFORE['room']); pending.rows.append(('room', room['name'], 0, None)); pending.rows.append(('gap', 'after_chairs', 0, None))
        for b in room['blocks']:
            u = pending or Unit(BEFORE['item'])
            pending = None
            if b['kind'] == 'session':
                u.before = max(u.before, BEFORE['session'])
                u.add('session', b['title'], w)
                if b.get('chairs'):
                    u.rows.append(('gap', 'after_session', 0, None))
                    u.add('chairs', 'Chair and introduction by ' + b['chairs'], w)
                u.rows.append(('gap', 'after_chairs', 0, None))
                pending = u          # resta unito all'intervento seguente
                continue
            if b['kind'] == 'item':
                if b.get('title'):
                    u.add('title', b['title'], w, GUTTER, b['time'])
                    u.add('names', b['names'], w, GUTTER)
                else:
                    u.add('title', b['names'], w, GUTTER, b['time'])
                if b.get('discussants'):
                    u.add('names', 'Discussants: ' + b['discussants'], w, GUTTER)
            elif b['kind'] == 'break':
                u.add('pause' if 'break' in b['text'].lower() else 'break', b['text'], w, GUTTER, b['time'])
            else:
                u.add('note', b['text'], w)
            us.append(u)
        if pending:
            us.append(pending)
    return us


def flow(units, frames):
    """Riempie le cornici in ordine; restituisce [(frame, [(unit, y)])] e le unità che non entrano."""
    placed, i = [], 0
    for fr in frames:
        y, rows = fr['y0'], []
        while i < len(units):
            u = units[i]
            top = y + (u.before if rows else 0)
            if top + u.height > fr['y1']:
                break
            rows.append((u, top)); y = top + u.height; i += 1
        placed.append((fr, rows))
    return placed, units[i:]


def draw_units(placed):
    out = []
    for fr, rows in placed:
        x0 = fr['x']
        for u, y in rows:
            for style, text, indent, gutter in u.rows:
                h = lh(style, text)
                if style == 'gap':
                    y += h; continue
                wt, pt, fill = S[style]
                if style == 'room':                       # aula: scatola piena nel colore di accento
                    out.append(f'<rect x="{x0}" y="{y:.1f}" width="{fr["w"]}" height="{h:.1f}" rx="10" fill="{{{{ACC2_BOX}}}}"/>')
                    out.append(T(x0 + 28, y + h / 2 + pt * PT * .36, text, wt, pt, fill))
                    if text in FLOOR_OF:
                        out.append(T(x0 + fr['w'] - 28, y + h / 2 + pt * PT * .36, FLOOR_OF[text], '600', pt * .78, fill, anchor='end'))
                    y += h; continue
                if style == 'pause':                      # coffee / lunch break: tutta la riga in una scatola chiara
                    out.append(f'<rect x="{x0 - 16}" y="{y + h * .08:.1f}" width="{fr["w"] + 32}" height="{h * .84:.1f}" rx="8" fill="{{{{ACC_FAINT2}}}}"/>')
                    base = y + h / 2 + pt * PT * .36
                    gw, gp, gf = S['time']
                    out.append(T(x0, base, gutter, gw, gp, gf))
                    out.append(T(x0 + indent, base, text, wt, pt, fill))
                    y += h; continue
                y += h
                base = y - h * .22
                if style in ITALIC:                       # corsivo simulato: inclinazione di 10°
                    t = T(0, 0, text, wt, pt, fill)
                    out.append(f'<g transform="translate({x0 + indent} {base:.1f}) skewX(-10)">{t}</g>')
                    continue
                if gutter:
                    gw, gp, gf = S['time']
                    out.append(T(x0, base, gutter, gw, gp, gf))
                out.append(T(x0 + indent, base, text, wt, pt, fill))
    return out


# ---------------------------------------------------------------- cornici
PAD = 70                                   # margine interno di ogni pannello
OUT_W = [970, 1000, 1000]                  # esterno, colonne da sinistra: la prima (97 mm) è l'aletta
IN_W = [970, 1000, 1000]                   # interno prima del giro di 180°: girato diventa 1000-1000-970, specchio dell'esterno
HEAD_IN = 310                              # spazio per l'intestazione del lato interno
FOLD = 2100


def inside_frames():
    fr, x = [], 0
    top = HEAD_IN + 60
    for w in IN_W:
        for y0, y1 in ((top, FOLD - 45), (FOLD + 60, H - 90)):
            fr.append({'x': x + PAD, 'w': w - 2 * PAD, 'y0': y0, 'y1': y1})
        x += w
    return fr


def outside_low_frames():
    fr, x = [], 0
    for w in OUT_W:
        fr.append({'x': x + PAD, 'w': w - 2 * PAD, 'y0': FOLD + 70, 'y1': H - 70})
        x += w
    return fr


WORKSHOP_NOTE = 'To register for a workshop, email covher.workshop@gmail.com with the workshop title and your full name.'
_parse = parse


def parse():
    """Come programme_parse.parse, ma la nota d'iscrizione ripetuta sotto ogni workshop compare una volta sola, alla fine."""
    days = _parse()
    for d in days:
        notes = [(r, b) for r in d['rooms'] for b in r['blocks'] if b['kind'] == 'note']
        if len(notes) > 1 and len({b['text'] for _, b in notes}) == 1:
            for r, b in notes[:-1]:
                r['blocks'].remove(b)
            notes[-1][1]['text'] = WORKSHOP_NOTE
    return days


def layout():
    set_gutter()
    days = parse()
    fi, fo = inside_frames(), outside_low_frames()
    tw = min(f['w'] for f in fi + fo)
    d1, d2 = units_for_day(days[0], tw), units_for_day(days[1], tw)
    p1, rest1 = flow(d1, fi)
    p2, rest2 = flow(d2, fo)
    return p1, rest1, p2, rest2


# ---------------------------------------------------------------- pannelli esterni (riga alta, capovolta)
BLUE = PB.BLUE


def logo_line(x, y, pt, two_lines=False):
    """ARCHEO.FOSS 2026 con punto e 2026 blu, in pezzi separati (anche per il PDF)."""
    size = pt * PT
    parts = [('ARCHEO', '{{INK}}'), ('.', BLUE), ('FOSS', '{{INK}}')]
    out, cx = [], x
    for txt, col in parts:
        out.append(T(cx, y, txt, '700', pt, col)); cx += width(txt, '700', size)
    if two_lines:
        out.append(T(x, y + size * 1.05, '2026', '700', pt, BLUE))
    else:
        out.append(T(cx + width(' ', '700', size), y, '2026', '700', pt, BLUE))
    return out


def paragraph(x, y, text, w, weight='400', pt=8.0, fill='{{INK}}', lead=1.3):
    out = []
    for line in wrap(text, weight, pt * PT, w):
        out.append(T(x, y, line, weight, pt, fill)); y += pt * PT * lead
    return out, y


COVER_W = OUT_W[0]                         # larghezza della copertina (colonna di sinistra, facciata 3)
COVER_GAP = 90                             # copertina: spazio (9 mm) loghi -> titolo
COVER_GAP2 = 140                           # copertina: spazio (14 mm) titolo -> sottotitolo
COVER_HEAD_H = 185                         # copertina: altezza del logo dell'università e del capitello


def text_path(text, weight, size, x, y, ls=0.0, anchor='start'):
    """Testo convertito in tracciato (il convertitore PDF non disegna i contorni dei testi)."""
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    f, cmap = _FONTS[weight], _CMAP[weight]
    gs, hm, k = f.getGlyphSet(), f['hmtx'], size / f['head'].unitsPerEm
    if anchor == 'middle':
        x -= (width(text, weight, size) + ls * (len(text) - 1)) / 2
    pen = SVGPathPen(gs)
    for c in text:
        g = cmap[ord(c)]
        gs[g].draw(TransformPen(pen, (k, 0, 0, -k, x, y)))
        x += hm[g][0] * k + ls
    return pen.getCommands()


def edition_block_pdf():
    """Stesso blocco «20th EDITION» della locandina (PB.edition_block), ma adatto al PDF: capitello col colore già
    schiarito al 50% invece della trasparenza, testi in tracciati, bordo bianco disegnato prima del testo."""
    wc = PB.COL_W; hc = wc * 333.7 / 492; cx = wc / 2
    size, esize, gap = 40, 9.5, 7
    w20 = PB.text_width('20', size, '700', -4)
    yed = hc - .5
    y20 = yed - gap - PB.CAP * esize
    x20 = cx - w20 / 2
    d20 = text_path('20', '700', size, x20, y20, -4)
    dth = text_path('th', '700', size * .34, x20 + w20 + 2, y20 - size * .42)
    ded = text_path('EDITION', '700', esize, cx + .8, yed, 1.6, 'middle')
    halo = 'fill="#FFFFFF" stroke="#FFFFFF" stroke-linejoin="round"'
    return (PB.column(0, 0, wc, 'fill="{{ACC_HALF}}"')
            + f'<path d="{d20}" {halo} stroke-width="7"/>'
            + f'<path d="{d20}" fill="#FFFFFF" stroke="{{{{ACC}}}}" stroke-width="1.7" stroke-linejoin="round"/>'
            + f'<path d="{dth}" {halo} stroke-width="5"/><path d="{dth}" fill="{{{{ACC}}}}"/>'
            + f'<path d="{ded}" {halo} stroke-width="5"/><path d="{ded}" fill="{{{{ACC}}}}"/>')


def art_group(end=(COVER_W - PAD) * 840 / COVER_W):
    """Linee stratigrafiche, 11 nodi e grande «20th» chiaro, dalla locandina (coordinate della locandina, larga 840);
    il «th» finisce al margine destro della copertina."""
    s = PB.tokenize((PB.SRC / 'master-poster.svg').read_text(encoding='utf-8'))
    i = s.index('<g transform="translate(20,312) scale(.87)">'); j = s.index('</g>', i) + 4
    g = PB.sub_20th(s[i:j], end)
    g = g.replace('font-weight="700"', f'font-family="{FAM["700"]}"')
    # «20» chiaro: colore già schiarito invece della trasparenza (il convertitore PDF ignora l'opacità dei testi)
    g, n = re.subn(r'fill="\{\{ACC\}\}"( [^>]*?)? opacity="\.075"', r'fill="{{ACC_FAINT}}"\1', g)
    assert n == 2, ('«20th» chiaro non trovato', n)
    # linee: colore già schiarito invece della trasparenza (il convertitore PDF ignora l'opacità dei tracciati)
    g, n = re.subn(r'stroke="\{\{INK\}\}"( [^>]*?) opacity="([\d.]+)"', r'stroke="{{INK@\2}}"\1', g)
    assert n == 20, ('linee non trovate', n)
    g = re.sub(r'<text (?![^>]*font-family)', f'<text font-family="{FAM["400"]}" ', g)
    return g


def panel_cover(w):
    # testata come la locandina: università a sinistra e capitello «20th EDITION» a destra, alti uguali;
    # sotto ARCHEO.FOSS 2026 su una riga a tutta larghezza e il sottotitolo, con spazi uguali (COVER_GAP)
    h, G, tw = COVER_HEAD_H, COVER_GAP, w - 2 * PAD
    logo = base64.b64encode(PB.UNIBO.read_bytes()).decode()
    k = h / (PB.COL_W * 333.7 / 492)
    out = [f'<image x="{PAD}" y="{PAD}" width="{h * PB.UNIBO_RATIO:.1f}" height="{h}" href="data:image/png;base64,{logo}"/>',
           f'<g transform="translate({w - PAD - PB.COL_W * k:.1f} {PAD}) scale({k:.4f})">{edition_block_pdf()}</g>']
    size = tw / width('ARCHEO.FOSS 2026', '700', 1)
    yt = PAD + h + G + PB.CAP * size
    out += logo_line(PAD, yt, size / PT)
    p, _ = paragraph(PAD, yt + COVER_GAP2 + PB.CAP * 9.5 * PT,
                     'International conference on open software, hardware, processes, data and formats in archaeological research',
                     tw, '400', 9.5)
    out += p
    sc = w / 840
    out.append(f'<g transform="translate(0 {1000 - 395 * sc - 120:.1f}) scale({sc:.4f})">{art_group()}</g>')
    out.append(T(PAD, 1590, '30 November – 1 December 2026', '700', 11.5))
    # VENUE come sulla locandina
    out.append(T(PAD, 1700, 'VENUE', '700', 6.5, '{{ACC}}', extra=' letter-spacing="3.8"'))
    out.append(T(PAD, 1755, 'Department of History and Cultures (DiSCi)', '600', 8.5))
    out.append(T(PAD, 1800, 'Alma Mater Studiorum – Università di Bologna', '400', 8))
    out.append(T(PAD, 1845, 'Piazza San Giovanni in Monte 2, 40124 Bologna, Italy', '400', 8))
    out.append(T(PAD, 1940, 'Conference programme', '700', 9, '{{ACC2}}'))
    out.append(T(PAD, 2010, 'www.archeofoss.org', '600', 8, '{{ACC}}'))
    return out


ROOMS = ['Aula Prodi', 'Aula Specola', 'Aula Morandi', 'Aula Capitani', 'Aula Gambi']
FLOORS = [('Ground floor', ['Aula Prodi', 'Aula Capitani']), ('First floor', ['Aula Gambi', 'Aula Morandi']),
          ('Second floor', ['Aula Specola'])]
FLOOR_OF = {r: f for f, rs in FLOORS for r in rs}
HOSTED_BY = ['DArchLab,', 'Digital Archaeology Laboratory,', 'Dipartimento di Storia Culture Civiltà,',
             'Alma Mater Studiorum – Università di Bologna']
ORGANISING = ['Department of History and Cultures, Alma Mater Studiorum University of Bologna', None,
              '• Cristiano Putzolu', '• Marco Cavalazzi', '• Paolo Forlin', '• Andrea Fiorini', None,
    '• Federico Fallavollita (Department of Architecture, Alma Mater Studiorum University of Bologna)',
    '• Tyler D. Johnson (University of Michigan)',
    '• Giacomo Landeschi (Lund University)',
    '• Michael Loy (Department of Classics and Ancient History, Durham University)',
    '• Sofia Pescarin (Institute of Heritage Science of the National Research Council of Italy)',
    '• Silvio Peroni (Department of Classical Philology and Italian Studies, Alma Mater Studiorum University of Bologna)',
    '• Valentina Presutti (Department of Modern Languages, Literatures, and Cultures, Alma Mater Studiorum University of Bologna)',
    '• Roberto Taglioretti (LabDig 3A Academy)',
]                                          # un solo comitato; None = riga vuota
BACK_K = 1.03                              # facciata 2: fattore sui corpi


def panel_back(w):
    """Facciata 2, simmetrica e centrata: Rooms (scatole uguali, 3 + 2), Organising Committee, QR con il link,
    in fondo «Hosted by». I blocchi in alto hanno spazi uguali."""
    K = BACK_K
    cx, tw = w / 2, w - 2 * PAD
    L = lambda pt: pt * PT * 1.32
    blocks = []

    def lines(text, weight, pt, fill='{{INK}}'):
        return [(t, weight, pt, fill) for t in wrap(text, weight, pt * PT, tw)]
    lab = lambda t: [(t, '700', 7.8 * K, '{{ACC2}}')]
    # aule: scatole uguali, 3 sopra e 2 sotto, centrate
    rp = 7.6 * K
    names = [r for r in ROOMS]
    pw = max(width(n, '700', rp * PT) for n in names) + 70
    ph, gx, gy = rp * PT * 1.65, 22, 14
    fl_pt = 6.6 * K
    row_h = fl_pt * PT * 1.25 + ph + gy
    blocks.append(lab('Rooms') + [('ROOMS', '', 0, row_h * len(FLOORS) + 18 - gy)])
    org = [x for x in ORGANISING if x]
    dept, inner, outer = org[0], org[1:5], org[5:]
    b = lab('Organising Committee') + lines(dept, '400', 7.0 * K, GREY2)
    b += [('', '400', 3, '{{INK}}')] + [(n.lstrip('• '), '600', 7.8 * K, '{{INK}}') for n in inner] + [('', '400', 5, '{{INK}}')]
    for m in outer:
        name, aff = re.match(r'• (.*?) \((.*)\)$', m).groups()
        b += [(name, '600', 7.8 * K, '{{INK}}')] + lines(aff, '400', 6.8 * K, GREY2) + [('', '400', 1.6, '{{INK}}')]
    blocks.append(b)
    q = 280
    qr = (PB.SRC / 'master-qr.svg').read_text(encoding='utf-8').replace('#252B29', '{{INK}}')
    inner_qr = qr[qr.index('>') + 1:qr.rindex('</svg>')]
    # in fondo: «Hosted by»; sopra il QR con il link
    hosted = lab('Hosted by') + [(h.rstrip(','), '400', 7.8 * K, '{{INK}}') for h in HOSTED_BY]
    hh = sum(L(it[2]) for it in hosted)
    y_host = 2100 - PAD - hh + L(hosted[0][2]) - 5          # base della prima riga di «Hosted by»
    y_link = y_host - L(hosted[0][2]) - 55
    yq = y_link - 95 - (q - q * 4 / 37)
    top, bottom = PAD + 7.8 * K * PT * PB.CAP, yq + q * 4 / 37
    H = lambda it: it[3] if it[0] == 'ROOMS' else L(it[2])
    hs = [sum(H(it) for it in bl) for bl in blocks]
    gap = (bottom - top - sum(hs)) / (len(blocks) - 1 + .6)
    out, y = [], top
    for bl in blocks:
        for it in bl:
            t, wt, pt, fill = it
            if t == 'ROOMS':
                yy = y - L(7.8 * K) * .55 + 14
                for floor, row in FLOORS:
                    out.append(T(cx, yy + fl_pt * PT * .9, floor.upper(), '700', fl_pt, GREY2, anchor='middle', extra=' letter-spacing="3"'))
                    yy += fl_pt * PT * 1.25
                    x0 = cx - (len(row) * pw + (len(row) - 1) * gx) / 2
                    for i, n in enumerate(row):
                        x = x0 + i * (pw + gx)
                        out.append(f'<rect x="{x:.1f}" y="{yy:.1f}" width="{pw:.1f}" height="{ph:.1f}" rx="{ph / 2:.1f}" fill="{{{{ACC2_BOX}}}}"/>')
                        out.append(T(x + pw / 2, yy + ph / 2 + rp * PT * .36, n, '700', rp, '#FFFFFF', anchor='middle'))
                    yy += ph + gy
                y += fill
                continue
            if t:
                out.append(T(cx, y, t, wt, pt, fill, anchor='middle'))
            y += L(pt)
        y += gap
    assert gap > 30, ('facciata 2 troppo piena', gap)
    out.append(f'<g transform="translate({cx - q / 2:.1f} {yq:.1f}) scale({q / 37:.4f})">{inner_qr}</g>')
    out.append(T(cx, y_link - 40, 'Full programme online', '700', 8, anchor='middle'))
    out.append(T(cx, y_link, 'www.archeofoss.org/2026/programme', '400', 8, anchor='middle'))
    yy = y_host
    for t, wt, pt, fill in hosted:
        out.append(T(cx, yy, t, wt, pt, fill, anchor='middle')); yy += L(pt)
    return out



def glance(days):
    """Programma in breve: per ogni giorno, sessioni con orario e sala."""
    res = []
    for d in days:
        rows = []
        for room in d['rooms']:
            blocks = room['blocks']
            for i, b in enumerate(blocks):
                if b['kind'] != 'session':
                    continue
                times = []
                for nb in blocks[i + 1:]:
                    if nb['kind'] == 'session':
                        break
                    if nb.get('time'):
                        times.append(nb['time'])
                if not times:
                    continue
                t0, t1 = times[0].split('–')[0], times[-1].split('–')[1]
                rows.append((t0, f'{t0}–{t1}', room['name'], b['title']))
        rows.sort(key=lambda r: r[0])
        res.append((d['date'], rows))
    return res


# ---------------------------------------------------------------- facciata 1: calendario dei due giorni
WEEKDAY = {'30 November 2026': 'Monday', '1 December 2026': 'Tuesday'}
KEY = ('Keynote lecture', 'Welcome addresses', 'Opening remarks')     # momenti di tutto il convegno: riempiti
PT2 = 7.2                                  # corpo del calendario
PADT, PADB = 12, 12                           # margine sopra e sotto il testo nei blocchi
BG = 3                                     # metà dello spazio tra due blocchi
DAYGAP = 50                                # spazio tra i due giorni
PRODI_W = 1.5                              # la corsia di Aula Prodi è 1,5 volte le altre
BASE = .1                                 # altezza minima per minuto (le altezze seguono il testo, non la durata)


def short(title):
    t = title.replace('Panel: ', '')
    return t.split(':')[0].strip() if ':' in t else t


def panel_glance(w, days):
    """Facciata 1: calendario dei due giorni. Corsie per aula (aule in scatole colorate), panel come riquadri
    con il solo contorno, keynote / welcome / opening riempite con il colore trasparente (ACC2_KEY)."""
    """B2: calendario moderno, senza titolo. Data in stile calendario; corsie con l'aula in scatola;
    sessioni come blocchi tenui con barra laterale; keynote e saluti come blocchi pieni."""
    out, y = [], PAD + 10
    pt = PT2; lead = pt * PT * 1.18
    tm = lambda s: int(s[:2]) * 60 + int(s[3:5])
    GAP = 14
    for (date, rows), day in zip(glance(days), days):
        rooms = [r['name'] for r in day['rooms']]
        span = {}
        for _, times, room, _t in rows:
            a, b = tm(times[:5]), tm(times[6:])
            s0, s1 = span.get(room, (a, b)); span[room] = (min(s0, a), max(s1, b))
        lanes = []
        for room in rooms:
            if room not in span:
                continue
            for ln in lanes:
                if all(span[r][1] <= span[room][0] or span[room][1] <= span[r][0] for r in ln):
                    ln.append(room); break
            else:
                lanes.append([room])
        nl = len(lanes)
        wts = [PRODI_W if i == 0 else 1 for i in range(nl)]
        free = w - 2 * PAD - GAP * (nl - 1)
        LW = [free * k / sum(wts) for k in wts]
        LX = [PAD + sum(LW[:i]) + GAP * i for i in range(nl)]
        lane_of = {r: i for i, ln in enumerate(lanes) for r in ln}
        # data in stile calendario: numero grande + giorno, mese e anno
        num, rest = date.split(' ', 1)
        big = 19
        out.append(T(PAD, y + PB.CAP * big * PT, num, '700', big, '{{ACC2}}'))
        xr = PAD + width(num, '700', big * PT) + 22
        out.append(T(xr, y + PB.CAP * 6.8 * PT, WEEKDAY[date].upper(), '700', 6.8, '{{ACC2}}', extra=' letter-spacing="4"'))
        out.append(T(xr, y + PB.CAP * big * PT, rest, '600', 9, '{{INK}}'))
        y += PB.CAP * big * PT + 34
        # intestazione delle corsie
        hb = 7 * PT * 1.55
        for i, ln in enumerate(lanes):
            x, lw = LX[i], LW[i]
            label = ' · '.join(r.replace('Aula ', '') for r in ln)
            lp = min(7.2, 7.2 * (lw - 24) / width(label, '700', 7.2 * PT))
            out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{lw:.1f}" height="{hb:.1f}" rx="{hb / 2:.1f}" fill="{{{{ACC2_BOX}}}}"/>')
            out.append(T(x + lw / 2, y + hb / 2 + lp * PT * .36, label, '700', lp, '#FFFFFF', anchor='middle'))
        y += hb + 14
        blocks = []
        for _, times, room, title in rows:
            a, b = tm(times[:5]), tm(times[6:])
            lw = LW[lane_of[room]]
            lines = [l.replace('- ', '-') for l in wrap(short(title).replace('-', '- '), '400', pt * PT, lw - 46)]   # a capo anche dopo il trattino
            tw = width(times, '400', pt * .92 * PT)
            inline = width(lines[0], '400', pt * PT) + tw + 30 <= lw - 46     # orario sulla stessa riga, a destra
            n = len(lines) + (0 if inline else 1)
            need = PADT + .9 * pt * PT + (n - 1) * lead + .3 * pt * PT + PADB + 2 * BG
            blocks.append([a, b, lane_of[room], times, lines, need, short(title), inline])
        cuts = sorted({b[0] for b in blocks} | {b[1] for b in blocks})
        Y = {cuts[0]: y}
        for i, c in enumerate(cuts[1:], 1):
            Y[c] = Y[cuts[i - 1]] + (c - cuts[i - 1]) * BASE
            for a_, b_, _l, _t, _ls, need, _s, _i in blocks:
                if b_ == c:
                    Y[c] = max(Y[c], Y[a_] + need)
        for a, b, l, times, lines, need, title, inline in blocks:
            x, lw = LX[l], LW[l]
            y0, y1 = Y[a] + BG, Y[b] - BG
            key = title in KEY
            tcol, icol = '{{ACC2}}', '{{INK}}'
            if key:      # keynote, welcome, opening: riempite con il colore più trasparente
                out.append(f'<rect x="{x:.1f}" y="{y0:.1f}" width="{lw:.1f}" height="{y1 - y0:.1f}" rx="12" fill="{{{{ACC2_KEY}}}}"/>')
            else:        # panel: solo il contorno
                out.append(f'<rect x="{x + 1.5:.1f}" y="{y0 + 1.5:.1f}" width="{lw - 3:.1f}" height="{y1 - y0 - 3:.1f}" rx="11" fill="none" stroke="{{{{ACC2_BOX}}}}" stroke-width="3"/>')
            ty = y0 + PADT + pt * PT * .9
            if inline:
                out.append(T(x + lw - 18, ty, times, '400', pt * .92, tcol, anchor='end'))
            else:
                out.append(T(x + 26, ty, times, '400', pt * .92, tcol)); ty += lead
            for ln in lines:
                out.append(T(x + 26, ty, ln, '400', pt, icol)); ty += lead
        y = Y[cuts[-1]] + DAYGAP
    assert y - DAYGAP <= 2100 - PAD, f'calendario della facciata 1 troppo lungo: {round(y - DAYGAP)}'
    return out


# ---------------------------------------------------------------- facciate
def svg_doc(body, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="420mm" viewBox="0 0 {W} {H}" role="img" aria-label="{label}">'
            f'<defs><style>{FONT_CSS}</style></defs><rect x="0" y="0" width="{W}" height="{H}" fill="#FFFFFF"/>'
            + ''.join(body) + '</svg>')


def inside_face(p1):
    body = logo_line(PAD, 230, 22)
    body += draw_units(p1)
    fr, rows = p1[-1]
    u, yy = rows[-1]
    y = yy + u.height + 120
    p, _ = paragraph(fr['x'], y, 'The programme of 1 December 2026 and the workshops are on the three panels of the other side.',
                     fr['w'], '400', 7, GREY2)
    body += p
    # interno girato di 180°: stampando fronte-retro sul lato lungo, dietro la facciata 4 c'è la 7
    return svg_doc([f'<g transform="rotate(180 {W / 2} {H / 2})">', *body, '</g>'], 'ArcheoFOSS 2026 programme, inside')


def outside_face(p2, days):
    body = draw_units(p2)
    x = 0
    # riga alta capovolta, da sinistra: 3 copertina, 2 informazioni pratiche, 1 «At a glance»; riga bassa 4-5-6 = 1 dicembre
    for w, maker in zip(OUT_W, (panel_cover, panel_back, lambda w: panel_glance(w, days))):
        # pannello capovolto: (lx, ly) -> (x + w - lx, 2100 - ly)
        body.append(f'<g transform="translate({x + w} {FOLD}) rotate(180)">' + ''.join(maker(w)) + '</g>')
        x += w
    return svg_doc(body, 'ArcheoFOSS 2026 programme, outside')


# ---------------------------------------------------------------- PDF
def make_pdf(svg_out, svg_in, pdf_path, tmpdir):
    from svglib.svglib import svg2rlg
    from svglib.fonts import register_font
    from reportlab.pdfgen import canvas
    from reportlab.graphics import renderPDF
    from reportlab.lib.units import mm
    for w, f in _FONTS.items():
        ttf = Path(tmpdir) / f'{FAM[w]}.ttf'
        if not ttf.exists():
            f2 = TTFont(io.BytesIO(base64.b64decode(PB.FONTS[w]))); f2.flavor = None; f2.save(str(ttf))
        register_font(FAM[w], str(ttf))
    c = canvas.Canvas(str(pdf_path), pagesize=(297 * mm, 420 * mm))
    c.setTitle('ArcheoFOSS 2026 - Programme A3 - outside and inside')
    for svg in (svg_out, svg_in):
        tmp = Path(tmpdir) / 'face.svg'
        tmp.write_text(re.sub(r'<defs><style>.*?</style></defs>', '', svg, count=1, flags=re.S), encoding='utf-8')
        d = svg2rlg(str(tmp))
        sx, sy = 297 * mm / d.width, 420 * mm / d.height
        d.scale(sx, sy); d.width *= sx; d.height *= sy
        renderPDF.draw(d, c, 0, 0); c.showPage()
    c.save()


def build():
    p1, r1, p2, r2 = layout()
    assert not r1 and not r2, 'il programma non entra'
    days = parse()
    tpl_in, tpl_out = inside_face(p1), outside_face(p2, days)
    with tempfile.TemporaryDirectory() as tmp:
        for pid, pal in PB.PALETTES.items():
            d = OUT / pid; d.mkdir(parents=True, exist_ok=True)
            si, so = PB.paint(tpl_in, pal), PB.paint(tpl_out, pal)
            (d / 'programma-interno.svg').write_text(si, encoding='utf-8')
            (d / 'programma-esterno.svg').write_text(so, encoding='utf-8')
            make_pdf(so, si, d / 'programma-a3-fronte-retro.pdf', tmp)
            print('ok', pid)


if __name__ == '__main__' and '--misura' in sys.argv:
    p1, r1, p2, r2 = layout()
    def used(p):
        return [round(((rows[-1][1] + rows[-1][0].height) - fr['y0']) / (fr['y1'] - fr['y0']) * 100) if rows else 0 for fr, rows in p]
    print('30 novembre (interno, 6 mezze colonne): riempimento %', used(p1), '| non entrano:', len(r1))
    print('1 dicembre (pannelli 01-03): riempimento %', used(p2), '| non entrano:', len(r2))


if __name__ == '__main__' and '--misura' not in sys.argv:
    build()
