"""Programma pieghevole A3: due SVG (esterno, interno) e un PDF fronte/retro per ogni combinazione di colore.

Piegatura: A3 verticale piegato a metà in orizzontale, poi a U in tre (chiuso 99 x 210 mm). Fronte-retro sul lato lungo.
- Lato esterno: riga alta capovolta = 3 copertina (97 mm), 2 aule, comitato e QR, 1 calendario dei due giorni;
                riga bassa = 4 (97 mm), 5, 6: 1 dicembre -> si vedono aprendo la U.
- Lato interno: girato di 180° (dietro la 4 c'è la 7), 30 novembre in sei mezze colonne allineate alle pieghe.
Testo completo, senza abbreviazioni.

Unità: 0,1 mm (foglio 2970 x 4200). Testo misurato sul font Inter vero, quindi a capo identici in browser e PDF.
Uso (da af2026mediakit):  ../.venv/bin/python tools/programme_build.py
"""
from contextlib import contextmanager
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
LINE_G, FILL_G = '#AEB4AF', '#EDEFED'      # contorni grigi e scatole grigio chiaro (meno rosso)

# ---------------------------------------------------------------- font e misure
from fontTools.ttLib import TTFont                     # noqa: E402
_FONTS = {w: TTFont(io.BytesIO(base64.b64decode(b))) for w, b in PB.FONTS.items()}
_CMAP = {w: f.getBestCmap() for w, f in _FONTS.items()}


def width(text, weight, size):
    f, cmap = _FONTS[weight], _CMAP[weight]
    hm, upm = f['hmtx'], f['head'].unitsPerEm
    text = text.replace('ğ', 'g').replace('Ğ', 'G').replace('\xa0', ' ')
    return sum(hm[cmap.get(ord(c), cmap[ord('?')])][0] for c in text) * size / upm


def wrap(text, weight, size, maxw):
    out, cur = [], ''
    for word in re.split(r'[ \t\n]+', text.strip()):   # lo spazio non divisibile (\xa0) tiene insieme le parole
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
    'room':    ('700', 11.0, '{{ACC2}}'),         # nome dell'aula in rosso, linea sottile sotto
    'session': ('700', 8.2, '{{INK}}'),
    'chairs':  ('400', 7.3, GREY),          # disegnato inclinato (ITALIC)
    'time':    ('600', 7.3, GREY),
    'title':   ('600', 7.8, '{{INK}}'),
    'names':   ('400', 7.3, GREY),
    'break':   ('400', 7.3, GREY2),
    'pause':   ('700', 7.4, '{{INK}}'),          # coffee / lunch break: riga in una scatola
    'note':    ('400', 7.1, GREY2),
    'gap':     ('400', 0, '{{INK}}'),            # spazio vuoto (altezza in 'gap_h')
}
LEAD = 1.20
GUTTER = 150          # colonna degli orari (ricalcolata in base al corpo: set_gutter)
GAP_H = {'after_session': 6, 'after_chairs': 10, 'box': 8}     # 'box': spazio sopra e sotto la cornice del panel     # spazio dopo il titolo del panel e dopo i chair
ROOM_BOX = 1.45       # altezza della scatola dell'aula (x interlinea)
PAUSE_BOX = 1.4       # altezza della scatola delle pause
BEFORE = {'room': 50, 'session': 50, 'item': 14}     # spazio prima di aula, panel, intervento
ITALIC = {'chairs'}
MIC_IND = 24          # rientro delle righe dei chair: a sinistra della prima c'è il microfono


def mic(x, base):
    """Microfono a linee (grigio scuro), alto come le maiuscole del chair; x = lato sinistro, base = linea di base."""
    return (f'<g transform="translate({x:.1f} {base - 18.5:.1f})" fill="none" stroke="{GREY}" stroke-width="1.7" stroke-linecap="round">'
            '<rect x="3" y="0" width="7" height="11" rx="3.5"/><path d="M0.5 7.5 a6 6 0 0 0 12 0"/>'
            '<line x1="6.5" y1="13.5" x2="6.5" y2="18"/><line x1="3" y1="18" x2="10" y2="18"/></g>')


DOT_IND = 24          # panel: rientro del titolo; nello spazio il puntino blu (come i nodi del logo: 11 nodi = 11 panel)
BOX_PAD = 14          # cornice a linea intorno a titolo del panel e chair: margine fuori dal testo


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
        self.inpanel = False                  # interventi di un panel: linea verticale a sinistra

    def add(self, style, text, w, indent=0, gutter=None, keep=None):
        wt, pt, _ = S[style]
        if keep:                                      # nomi da non spezzare: nome e cognome vanno insieme a capo
            text = text.replace(keep, ', '.join(n.replace(' ', '\xa0') for n in keep.split(', ')))
        for i, line in enumerate(wrap(text, wt, pt * PT, w - indent)):
            self.rows.append((style, line.replace('\xa0', ' '), indent, gutter if i == 0 else None))

    @property
    def height(self):
        return sum(lh(r[0], r[1]) for r in self.rows)


def units_for_day(day, w):
    us = []
    u = Unit(0); u.add('day', day['date'], w); us.append(u)
    for room in day['rooms']:
        inpanel = False
        pending = Unit(BEFORE['room']); pending.rows.append(('room', room['name'], 0, None)); pending.rows.append(('gap', 'after_chairs', 0, None))
        for b in room['blocks']:
            u = pending or Unit(BEFORE['item'])
            pending = None
            if b['kind'] == 'session':
                u.before = max(u.before, BEFORE['session'])
                u.rows.append(('gap', 'box', 0, None))
                u.add('session', b['title'], w, DOT_IND if b['title'].startswith('Panel:') else 0)
                if b.get('chairs'):
                    u.rows.append(('gap', 'after_session', 0, None))
                    u.add('chairs', 'Chair and introduction by ' + b['chairs'], w, MIC_IND, keep=b['chairs'])   # rientro per il microfono
                u.rows.append(('gap', 'box', 0, None))
                u.rows.append(('gap', 'after_chairs', 0, None))
                pending = u          # resta unito all'intervento seguente
                u.inpanel = inpanel = True
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
                inpanel = False
                u.add('note', b['text'], w)
            u.inpanel = u.inpanel or inpanel
            us.append(u)
        if pending:
            us.append(pending)
    # una pausa resta nel panel (la linea la attraversa) solo se dopo continua lo stesso panel
    for i, u in enumerate(us):
        if u.inpanel and any(r[0] == 'pause' for r in u.rows):
            nx = us[i + 1] if i + 1 < len(us) else None
            u.inpanel = bool(nx and nx.inpanel and not any(r[0] in ('session', 'room') for r in nx.rows))
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
        line_end = None                                   # fine della linea del panel nell'unità precedente (stessa colonna)
        for u, y in rows:
            start = len(out)
            box, talk = None, None                        # box del panel [alto, basso]; interventi del panel [alto, basso]
            for style, text, indent, gutter in u.rows:
                h = lh(style, text)
                if style in ('session', 'chairs'):
                    box = [box[0] if box else y, y + h]
                elif u.inpanel and style not in ('gap', 'room'):
                    talk = [talk[0] if talk else y, y + h]
                if style == 'gap':
                    y += h; continue
                wt, pt, fill = S[style]
                if style == 'room':                       # aula: nome in rosso e linea sottile rossa sotto, piano in grigio
                    out.append(f'<line x1="{x0}" y1="{y + h - 4:.1f}" x2="{x0 + fr["w"]}" y2="{y + h - 4:.1f}" stroke="{{{{ACC2}}}}" stroke-width="4"/>')
                    out.append(T(x0, y + h / 2 + pt * PT * .36, text, wt, pt, fill))
                    if text in FLOOR_OF:
                        out.append(T(x0 + fr['w'], y + h / 2 + pt * PT * .36, FLOOR_OF[text], '600', pt * .66, GREY2, anchor='end'))
                    y += h; continue
                if style == 'pause':                      # coffee / lunch break: senza scatola, orario e testo in blu
                    base = y + h / 2 + pt * PT * .36
                    gw, gp, gf = S['time']
                    out.append(T(x0, base, gutter, gw, gp, '{{NODE}}'))
                    out.append(T(x0 + indent, base, text, wt, pt, '{{NODE}}'))
                    y += h; continue
                y += h
                base = y - h * .22
                if style in ITALIC:                       # corsivo simulato: inclinazione di 10°
                    t = T(0, 0, text, wt, pt, fill)
                    out.append(f'<g transform="translate({x0 + indent} {base:.1f}) skewX(-10)">{t}</g>')
                    if style == 'chairs' and text.startswith('Chair and introduction by'):
                        out.append(mic(x0, base))
                    continue
                if gutter:
                    gw, gp, gf = S['time']
                    out.append(T(x0, base, gutter, gw, gp, gf))
                out.append(T(x0 + indent, base, text, wt, pt, fill))
                if style == 'session' and text.startswith('Panel:'):   # puntino blu dei nodi
                    out.append(f'<circle cx="{x0 + 7:.1f}" cy="{base - pt * PT * .36:.1f}" r="7" fill="{{{{NODE}}}}"/>')
            if box:                                       # panel: box grigio chiaro, sotto il testo
                bx, by, bw, bh, r = x0 - BOX_PAD, box[0] - 9, fr['w'] + 2 * BOX_PAD, box[1] - box[0] + 17, 8
                rb = 0 if talk else r                     # se sotto scende la linea, angolo in basso a sinistra squadrato
                out.insert(start, f'<path d="M{bx + r:.1f} {by:.1f} H{bx + bw - r:.1f} A{r} {r} 0 0 1 {bx + bw:.1f} {by + r:.1f} '
                                  f'V{by + bh - r:.1f} A{r} {r} 0 0 1 {bx + bw - r:.1f} {by + bh:.1f} H{bx + rb:.1f} '
                                  f'{f"A{rb} {rb} 0 0 1 {bx:.1f} {by + bh - rb:.1f} " if rb else ""}V{by + r:.1f} A{r} {r} 0 0 1 {bx + r:.1f} {by:.1f} Z" fill="{FILL_G}"/>')
            if talk:                                      # interventi del panel: linea verticale grigia a sinistra
                y0 = box[1] + 8 if box else (line_end if line_end is not None else talk[0])
                xl = x0 - BOX_PAD + 1.25                  # bordo esterno della linea = bordo sinistro del box grigio
                out.append(f'<line x1="{xl:.2f}" y1="{y0:.1f}" x2="{xl:.2f}" y2="{talk[1]:.1f}" stroke="{LINE_G}" stroke-width="2.5"/>')
                line_end = talk[1]
            else:
                line_end = None
    return out


# ---------------------------------------------------------------- cornici
PAD = 40                                   # margine interno di ogni pannello (4 mm: la stampante aggiunge il suo)
OUT_W = [970, 1000, 1000]                  # esterno, colonne da sinistra: la prima (97 mm) è l'aletta
IN_W = [970, 1000, 1000]                   # interno prima del giro di 180°: girato diventa 1000-1000-970, specchio dell'esterno
HEAD_IN = 280                              # spazio per l'intestazione del lato interno
FOLD = 2100


def inside_frames():
    fr, x = [], 0
    top = HEAD_IN + 60
    for w in IN_W:
        for y0, y1 in ((top, FOLD - 45), (FOLD + 60, H - 60)):
            fr.append({'x': x + PAD, 'w': w - 2 * PAD, 'y0': y0, 'y1': y1})
        x += w
    return fr


def outside_low_frames():
    fr, x = [], 0
    for w in OUT_W:
        fr.append({'x': x + PAD, 'w': w - 2 * PAD, 'y0': FOLD + 70, 'y1': H - 40})
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


IN_SCALE = 1.04       # 30 novembre (lato interno): testi e spazi un po' più grandi, per riempire le colonne


@contextmanager
def scaled(F):
    """Corpi del programma e spazi verticali moltiplicati per F (anche la colonna degli orari); poi tutto torna com'era."""
    global S, BEFORE, GAP_H
    keep = S, BEFORE, GAP_H
    S = {k: (w, p * F, f) for k, (w, p, f) in S.items()}
    BEFORE = {k: v * F for k, v in BEFORE.items()}
    GAP_H = {k: v * F for k, v in GAP_H.items()}
    set_gutter()
    try:
        yield
    finally:
        S, BEFORE, GAP_H = keep
        set_gutter()


def layout():
    set_gutter()
    days = parse()
    fi, fo = inside_frames(), outside_low_frames()
    tw = min(f['w'] for f in fi + fo)
    with scaled(IN_SCALE):                                 # le altezze si calcolano col corpo attivo: misura e disegno dentro scaled
        p1, rest1 = flow(units_for_day(days[0], tw), fi)
    p2, rest2 = flow(units_for_day(days[1], tw), fo)
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
COVER_HEAD_H = 185                         # copertina: altezza del capitello
COVER_LOGO_H = 215                         # copertina: altezza del logo Università di Bologna / DiSCi (un po' più grande)


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
    hl = COVER_LOGO_H                         # il capitello è centrato in altezza sul logo
    out = [f'<image x="{PAD}" y="{PAD}" width="{hl * PB.UNIBO_RATIO:.1f}" height="{hl}" href="data:image/png;base64,{logo}"/>',
           f'<g transform="translate({w - PAD - PB.COL_W * k:.1f} {PAD + (hl - h) / 2:.1f}) scale({k:.4f})">{edition_block_pdf()}</g>']
    h = max(h, hl)
    size = tw / width('ARCHEO.FOSS 2026', '700', 1)
    yt = PAD + h + G + PB.CAP * size
    out += logo_line(PAD, yt, size / PT)
    p, _ = paragraph(PAD, yt + COVER_GAP2 + PB.CAP * 9.5 * PT,
                     'International conference on open software, hardware, processes, data and formats in archaeological research',
                     tw, '400', 9.5)
    out += p
    sc = w / 840
    out.append(f'<g transform="translate(0 {1000 - 395 * sc - 120:.1f}) scale({sc:.4f})">{art_group()}</g>')
    full = lambda t, wt: tw / width(t, wt, PT)              # corpo che fa finire la riga esattamente al margine destro
    d = '30 November – 1 December 2026'
    out.append(T(PAD, 1580, d, '700', full(d, '700')))      # data a tutta larghezza, finisce come ARCHEO.FOSS 2026
    # Venue come titolo (come Rooms, Organising Committee, Hosted by), indirizzo più grande
    out.append(T(PAD, 1720, 'Venue', '700', 10, '{{ACC2}}'))
    out.append(T(PAD, 1782, 'Department of History and Cultures (DiSCi)', '600', 9.5))
    out.append(T(PAD, 1828, 'Alma Mater Studiorum – Università di Bologna', '400', 9))
    a = 'Piazza San Giovanni in Monte 2, 40124 Bologna, Italy'
    out.append(T(PAD, 1874, a, '400', 9))
    # Hosted by (spostato qui dalla facciata 2)
    out.append(T(PAD, 1980, 'Hosted by', '700', 10, '{{ACC2}}'))
    out.append(T(PAD, 2042, 'DArchLab – Digital Archaeology Laboratory', '600', 9.5))
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
NAME_PT, AFF_PT, ORG_SP = 8.6, 7.4, 5      # facciata 2: nomi del comitato, affiliazioni, spazio tra le persone


QR_BACK = [('master-qr.svg', 'PROGRAMME', 'archeofoss.org/2026/programme'),
           ('master-qr-teams.svg', 'ONLINE ON TEAMS', 'Microsoft Teams link')]     # facciata 2: due QR con cornice


def qr_framed(cx, yf, q, name, label, sub, fw=None):
    """QR (parte stampata larga q, senza il bordo bianco) dentro una cornice rosso mattone con didascalia,
    come sul retro del badge. yf = lato alto della cornice; restituisce (elementi, larghezza, altezza)."""
    src = (PB.SRC / name).read_text(encoding='utf-8').replace('#252B29', '{{INK}}')
    n = float(re.search(r'viewBox="0 0 ([\d.]+)', src).group(1))
    k = q / (n - 8)
    inner = re.sub(r'<rect [^>]*fill="#fff"/>', '', src[src.index('>') + 1:src.rindex('</svg>')], count=1)
    pad, fw = 26, fw or q + 150
    y_lab = yf + pad + q + 14 + 7.4 * PT * 1.25
    y_sub = y_lab + 6.2 * PT * 1.3
    fh = y_sub - yf + 26
    out = [f'<rect x="{cx - fw / 2:.1f}" y="{yf:.1f}" width="{fw:.1f}" height="{fh:.1f}" rx="16" fill="none" stroke="{LINE_G}" stroke-width="2.5"/>',
           f'<g transform="translate({cx - q / 2 - 4 * k:.2f} {yf + pad - 4 * k:.2f}) scale({k:.5f})">{inner}</g>',
           T(cx, y_lab, label, '700', 7.4, '{{INK}}', anchor='middle'),
           T(cx, y_sub, sub, '400', 6.2, GREY2, anchor='middle')]
    return out, fw, fh


def panel_back(w):
    """Facciata 2, tutto allineato a sinistra tranne i QR: Rooms come sezione dell'edificio (piani dall'alto,
    scatole con il solo contorno), Organising Committee (affiliazione sempre sotto i nomi), i due QR (programma e Teams)
    con cornice al centro, in fondo «Hosted by». I blocchi in alto hanno spazi uguali."""
    K = BACK_K
    cx, tw = w / 2, w - 2 * PAD
    L = lambda pt: pt * PT * 1.32
    blocks = []

    KEEP = 'Alma Mater Studiorum University of Bologna'     # non si spezza: se non entra va tutta a capo

    def lines(text, weight, pt, fill='{{INK}}'):
        words = [x for part in re.split(f'({KEEP})', text) for x in ([part] if part == KEEP else part.split())]
        out, cur = [], ''
        for wd in words:
            nxt = (cur + ' ' + wd).strip()
            if cur and width(nxt, weight, pt * PT) > tw:
                out.append(cur); cur = wd
            else:
                cur = nxt
        out.append(cur)
        return [(t, weight, pt, fill) for t in out]
    TP = 10 * K                                            # titoli (Rooms, Organising Committee, Hosted by): più grandi, in rosso
    lab = lambda t: [(t, '700', TP, '{{ACC2}}')]
    # aule: scatole uguali, una riga per piano
    rp = 7.6 * K
    names = [r for r in ROOMS]
    pw = max(width(n, '700', rp * PT) for n in names) + 70
    ph, gx, gy = rp * PT * 1.65, 22, 14
    fl_pt = 6.6 * K
    org = [x for x in ORGANISING if x]
    dept, inner, outer = org[0], org[1:5], org[5:]
    # comitato da sinistra: i quattro nomi del dipartimento e sotto la loro affiliazione, poi gli altri con la propria
    b = lab('Organising Committee') + [('', '400', 3, '{{INK}}')]
    NP, AP = NAME_PT * K, AFF_PT * K                        # nomi e affiliazioni (più grandi da quando «Hosted by» è in copertina)
    b += [(n.lstrip('• '), '600', NP, '{{INK}}') for n in inner] + lines(dept, '400', AP, GREY2) + [('', '400', 7, '{{INK}}')]
    for m in outer:
        name, aff = re.match(r'• (.*?) \((.*)\)$', m).groups()
        b += [(name, '600', NP, '{{INK}}')] + lines(aff, '400', AP, GREY2) + [('', '400', ORG_SP, '{{INK}}')]
    # aule in alto, prima del comitato
    blocks.insert(0, ('start', lab('Rooms') + [('ROOMS', '', 0, (ph + 30) * len(FLOORS) + 20)]))
    blocks.append(('start', b))
    # in fondo solo i due QR con la cornice («Hosted by» è in copertina, sotto Venue)
    q = 230
    _, fw, fh = qr_framed(0, 0, q, *QR_BACK[0])
    yf = 2100 - PAD - fh                                      # lato alto delle cornici
    top, bottom = PAD + TP * PT * PB.CAP, yf
    H = lambda it: it[3] if it[0] == 'ROOMS' else L(it[2])
    hs = [sum(H(it) for it in bl) for _, bl in blocks]
    gap = (bottom - top - sum(hs)) / (len(blocks) - 1 + .6)
    out, y = [], top
    for align, bl in blocks:
        for it in bl:
            t, wt, pt, fill = it
            if t == 'ROOMS':
                yy = y - L(TP) * .55 + 14
                band = ph + 30                                # sezione dell'edificio: 2° piano in alto, piano terra in basso
                labs = {'Second floor': '2nd floor', 'First floor': '1st floor', 'Ground floor': 'Ground floor'}
                lw = max(width(v.upper(), '700', fl_pt * PT) + 3 * len(v) for v in labs.values())
                xb = PAD + lw + 34
                x1 = w - PAD
                for floor, row in reversed(FLOORS):
                    out.append(T(PAD, yy + band / 2 + fl_pt * PT * .36, labs[floor].upper(), '700', fl_pt, GREY2, extra=' letter-spacing="3"'))
                    for i, n in enumerate(row):
                        x = xb + i * (pw + gx)
                        assert x + pw <= x1 + .5, ('aule troppo larghe', x + pw, x1)
                        out.append(f'<rect x="{x:.1f}" y="{yy + 15:.1f}" width="{pw:.1f}" height="{ph:.1f}" rx="{ph / 2:.1f}" fill="none" stroke="{LINE_G}" stroke-width="2.5"/>')
                        out.append(T(x + pw / 2, yy + 15 + ph / 2 + rp * PT * .36, n, '700', rp, '{{ACC2}}', anchor='middle'))
                    yy += band
                    ACC_T = '{{ACC2}}'
                    g = floor == 'Ground floor'                # solaio sottile, terreno spesso
                    out.append(f'<line x1="{PAD:.1f}" y1="{yy:.1f}" x2="{x1:.1f}" y2="{yy:.1f}" stroke="{ACC_T if g else LINE_G}" stroke-width="{5 if g else 1.6}"/>')
                y += fill
                continue
            if t:
                out.append(T(cx, y, t, wt, pt, fill, anchor='middle') if align == 'middle' else T(PAD, y, t, wt, pt, fill))
            y += L(pt)
        y += gap
    assert gap > 30, ('facciata 2 troppo piena', gap)
    sep = 40                                                  # spazio tra le due cornici
    fw2 = (tw - sep) / 2                                      # due cornici uguali, allineate ai margini del testo
    for i, qb in enumerate(QR_BACK):
        out += qr_framed(PAD + fw2 / 2 + i * (fw2 + sep), yf, q, *qb, fw=fw2)[0]
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
PT2 = 6.9                                  # corpo del calendario
PADT, PADB = 9, 9                             # margine sopra e sotto il testo nei blocchi
BG = 3                                     # metà dello spazio tra due blocchi
DAYGAP = 50                                # spazio tra i due giorni
PRODI_W = 1.3                              # la corsia di Aula Prodi è 1,3 volte le altre
NLANES = 3                                 # tre corsie in entrambi i giorni
CAL_DOT = 20                               # rientro del titolo del panel: nello spazio il puntino blu
BASE = 0                                 # altezza minima per minuto (le altezze seguono il testo, non la durata)


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
            for ln in ([] if len([r for r in rooms if r in span]) <= NLANES else lanes):   # se bastano, un'aula per corsia
                if all(span[r][1] <= span[room][0] or span[room][1] <= span[r][0] for r in ln):
                    ln.append(room); break
            else:
                lanes.append([room])
        assert len(lanes) <= NLANES, lanes
        nl = NLANES                                       # stesse corsie, stesse larghezze nei due giorni
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
            out.append(f'<line x1="{x:.1f}" y1="{y + hb - 2:.1f}" x2="{x + lw:.1f}" y2="{y + hb - 2:.1f}" stroke="{LINE_G}" stroke-width="2"/>')
            out.append(T(x + lw / 2, y + hb / 2 + lp * PT * .36, label, '700', lp, GREY, anchor='middle'))
        y += hb + 14
        blocks = []
        for _, times, room, title in rows:
            a, b = tm(times[:5]), tm(times[6:])
            lw = LW[lane_of[room]]
            ind = CAL_DOT if title.startswith('Panel:') else 0
            lines = [l.replace('- ', '-') for l in wrap(short(title).replace('-', '- '), '400', pt * PT, lw - 46 - ind)]   # a capo anche dopo il trattino
            inline = False                                # orario sempre sopra il titolo
            n = len(lines) + (0 if inline else 1)
            need = PADT + .9 * pt * PT + (n - 1) * lead + .3 * pt * PT + PADB + 2 * BG
            blocks.append([a, b, lane_of[room], times, lines, need, short(title), inline, ind])
        cuts = sorted({b[0] for b in blocks} | {b[1] for b in blocks})
        Y = {cuts[0]: y}
        for i, c in enumerate(cuts[1:], 1):
            Y[c] = Y[cuts[i - 1]] + (c - cuts[i - 1]) * BASE
            for a_, b_, _l, _t, _ls, need, _s, _i, _d in blocks:
                if b_ == c:
                    Y[c] = max(Y[c], Y[a_] + need)
        for a, b, l, times, lines, need, title, inline, ind in blocks:
            x, lw = LX[l], LW[l]
            y0, y1 = Y[a] + BG, Y[b] - BG
            key = title in KEY
            tcol, icol = GREY, '{{INK}}'
            if key:      # keynote, welcome, opening: riempite con il colore più trasparente
                out.append(f'<rect x="{x:.1f}" y="{y0:.1f}" width="{lw:.1f}" height="{y1 - y0:.1f}" rx="12" fill="{FILL_G}"/>')
            else:        # panel: solo il contorno
                out.append(f'<rect x="{x + 1.5:.1f}" y="{y0 + 1.5:.1f}" width="{lw - 3:.1f}" height="{y1 - y0 - 3:.1f}" rx="11" fill="none" stroke="{LINE_G}" stroke-width="2.5"/>')
            ty = y0 + PADT + pt * PT * .9
            if inline:
                out.append(T(x + lw - 18, ty, times, '400', pt * .92, tcol, anchor='end'))
            else:
                out.append(T(x + 26, ty, times, '400', pt * .92, tcol)); ty += lead
            if ind:                                       # panel: puntino blu dei nodi
                out.append(f'<circle cx="{x + 26 + 6:.1f}" cy="{ty - pt * PT * .36:.1f}" r="6" fill="{{{{NODE}}}}"/>')
            for ln in lines:
                out.append(T(x + 26 + ind, ty, ln, '400', pt, icol)); ty += lead
        y = Y[cuts[-1]] + DAYGAP
    assert y - DAYGAP <= 2100 - PAD, f'calendario della facciata 1 troppo lungo: {round(y - DAYGAP)}'
    return out


def panel_agenda(w, days):
    """Facciata 1: agenda a righe. Per ogni giorno la data in stile calendario, poi una riga per sessione in ordine
    di orario: orario a sinistra, puntino blu se è un panel, titolo, aula in grigio a destra. Le sessioni in
    parallelo (orari che si sovrappongono) sono unite da una linea verticale sottile; keynote e saluti in grigio chiaro."""
    out, y = [], PAD + 10
    pt, tpt = AG_PT, AG_PT * .95
    lead = pt * PT * 1.22
    tm = lambda s: int(s[:2]) * 60 + int(s[3:5])
    tw = w - 2 * PAD
    TW = width('00:00–00:00', '600', tpt * PT) + 22          # colonna degli orari
    RW = max(width(r.replace('Aula ', ''), '600', tpt * PT) for r in ROOMS) + 18   # colonna delle aule
    XT = PAD + TW + DOT_IND                                   # inizio dei titoli
    for (date, rows), day in zip(glance(days), days):
        num, rest = date.split(' ', 1)
        big = 19
        out.append(T(PAD, y + PB.CAP * big * PT, num, '700', big, '{{ACC2}}'))
        xr = PAD + width(num, '700', big * PT) + 22
        out.append(T(xr, y + PB.CAP * 6.8 * PT, WEEKDAY[date].upper(), '700', 6.8, '{{ACC2}}', extra=' letter-spacing="4"'))
        out.append(T(xr, y + PB.CAP * big * PT, rest, '600', 9, '{{INK}}'))
        y += PB.CAP * big * PT + 30
        # gruppi di sessioni in parallelo (intervalli che si sovrappongono)
        # una riga per sessione, separate da una linea sottile (le sessioni in parallelo si leggono dagli orari e dalle aule)
        groups = [[r] for r in sorted(rows, key=lambda r: (tm(r[1][:5]), tm(r[1][6:])))]
        for gi, g in enumerate(groups):
            out.append(f'<line x1="{PAD:.1f}" y1="{y:.1f}" x2="{w - PAD:.1f}" y2="{y:.1f}" stroke="{RULE}" stroke-width="1.5"/>')
            y += AG_SP
            gy0 = y
            for _, times, room, title in g:
                t = short(title)
                lines = wrap(t, '600' if title.startswith('Panel:') else '400', pt * PT, w - PAD - 12 - RW - XT)
                h = len(lines) * lead
                base = y + pt * PT * .9
                if title in KEY:                              # keynote, welcome, opening: fondo grigio chiaro
                    out.append(f'<rect x="{XT - 12:.1f}" y="{y - 8:.1f}" width="{w - PAD - XT + 12:.1f}" height="{h + 12:.1f}" rx="6" fill="{FILL_G}"/>')
                out.append(T(PAD + (10 if len(g) > 1 else 0), base, times, '600', tpt, GREY))
                if title.startswith('Panel:'):
                    out.append(f'<circle cx="{PAD + TW + 7:.1f}" cy="{base - pt * PT * .36:.1f}" r="6.5" fill="{{{{NODE}}}}"/>')
                for i, ln in enumerate(lines):
                    out.append(T(XT, base + i * lead, ln, '600' if title.startswith('Panel:') else '400', pt, '{{INK}}'))
                out.append(T(w - PAD - 12, base, room.replace('Aula ', ''), '600', tpt, GREY2, anchor='end'))   # dentro il fondo grigio
                y += h + AG_IN
            y -= AG_IN
            if len(g) > 1:                                    # sessioni in parallelo: linea verticale sottile
                out.append(f'<line x1="{PAD + 1.5:.1f}" y1="{gy0:.1f}" x2="{PAD + 1.5:.1f}" y2="{y:.1f}" stroke="{LINE_G}" stroke-width="3"/>')
            y += AG_SP
        out.append(f'<line x1="{PAD:.1f}" y1="{y:.1f}" x2="{w - PAD:.1f}" y2="{y:.1f}" stroke="{RULE}" stroke-width="1.5"/>')
        y += DAYGAP + 20
    assert y - DAYGAP - 20 <= 2100 - PAD, f'agenda della facciata 1 troppo lunga: {round(y - DAYGAP - 20)}'
    return out


AG_PT, AG_SP, AG_IN = 8, 17, 10          # agenda: corpo, spazio sopra/sotto ogni gruppo, spazio tra righe dello stesso gruppo


BANDS = [('Morning', 0, 13 * 60), ('Afternoon', 13 * 60, 17 * 60 + 30), ('Evening', 17 * 60 + 30, 24 * 60)]
BD_PT, BD_GAP = 6.9, 12                    # fasce: corpo del testo, spazio tra le colonne delle aule
SPEAKER_OF = ('Keynote lecture', 'Workshop')               # sotto il titolo il nome di chi parla


def speakers(days):
    """{(data, aula, titolo): nome} per keynote e workshop: il nome del primo intervento dopo la sessione."""
    res = {}
    for d in days:
        for r in d['rooms']:
            bl = r['blocks']
            for i, b in enumerate(bl):
                if b['kind'] == 'session' and b['title'] in SPEAKER_OF:
                    nx = next((x for x in bl[i + 1:] if x['kind'] == 'item' and x.get('names')), None)
                    if nx:
                        res[(d['date'], r['name'], b['title'])] = re.sub(r'\s*\(.*?\)', '', nx['names']).strip()
    return res


def panel_bands(w, days):
    """Facciata 1: calendario per fasce. Ogni giorno: data in stile calendario, poi Morning / Afternoon / Evening
    (secondo l'orario d'inizio); in ogni fascia le aule affiancate, con le sessioni una sotto l'altra.
    Panel con il puntino blu; keynote e saluti su fondo grigio chiaro; per keynote e workshop anche il nome."""
    out, y = [], PAD + 10
    tm = lambda s: int(s[:2]) * 60 + int(s[3:5])
    tw = w - 2 * PAD
    pt = BD_PT
    lead = pt * PT * 1.18
    spk = speakers(days)
    for (date, rows), day in zip(glance(days), days):
        num, rest = date.split(' ', 1)
        big = 19
        out.append(T(PAD, y + PB.CAP * big * PT, num, '700', big, '{{ACC2}}'))
        xr = PAD + width(num, '700', big * PT) + 22
        out.append(T(xr, y + PB.CAP * 6.8 * PT, WEEKDAY[date].upper(), '700', 6.8, '{{ACC2}}', extra=' letter-spacing="4"'))
        out.append(T(xr, y + PB.CAP * big * PT, rest, '600', 9, '{{INK}}'))
        y += PB.CAP * big * PT + 22
        rooms = [r['name'] for r in day['rooms']]
        for name, b0, b1 in BANDS:
            br = [r for r in rows if b0 <= tm(r[1][:5]) < b1]
            if not br:
                continue
            used = [r for r in rooms if any(x[2] == r for x in br)]
            n = len(used)
            LW = (tw - BD_GAP * (n - 1)) / n
            out.append(T(PAD, y + 6.4 * PT * PB.CAP, name.upper(), '700', 6.4, '{{ACC2}}', extra=' letter-spacing="3"'))
            y += 6.4 * PT * PB.CAP + 8
            out.append(f'<line x1="{PAD:.1f}" y1="{y:.1f}" x2="{w - PAD:.1f}" y2="{y:.1f}" stroke="{RULE}" stroke-width="1.5"/>')
            y += 8
            hs = []
            for i, room in enumerate(used):
                x = PAD + i * (LW + BD_GAP)
                yy = y
                out.append(T(x, yy + pt * PT * .9, room.replace('Aula ', ''), '700', pt * .92, GREY))
                yy += lead + 2
                for _, times, r, title in br:
                    if r != room:
                        continue
                    panel = title.startswith('Panel:')
                    ind = 18 if panel else 0
                    lines = wrap(short(title), '400', pt * PT, LW - 24 - ind)
                    who = spk.get((date, room, title))
                    wl = wrap(who, '600', pt * PT, LW - 24) if who else []
                    h = 8 + lead * (1 + len(lines) + len(wl)) + 3
                    if short(title) in KEY:
                        out.append(f'<rect x="{x:.1f}" y="{yy:.1f}" width="{LW:.1f}" height="{h:.1f}" rx="8" fill="{FILL_G}"/>')
                    else:
                        out.append(f'<rect x="{x + 1.2:.1f}" y="{yy + 1.2:.1f}" width="{LW - 2.4:.1f}" height="{h - 2.4:.1f}" rx="8" fill="none" stroke="{LINE_G}" stroke-width="2.4"/>')
                    ty = yy + 6 + pt * PT * .9
                    out.append(T(x + 12, ty, times, '400', pt * .9, GREY)); ty += lead
                    if panel:
                        out.append(f'<circle cx="{x + 17:.1f}" cy="{ty - pt * PT * .36:.1f}" r="5" fill="{{{{NODE}}}}"/>')
                    for ln in lines:
                        out.append(T(x + 12 + ind, ty, ln, '400', pt, '{{INK}}')); ty += lead
                    for ln in wl:                                  # keynote e workshop: nome di chi parla
                        out.append(T(x + 12, ty, ln, '600', pt, '{{INK}}')); ty += lead
                    yy += h + 5
                hs.append(yy - y)
            y += max(hs) + 8
        y += 24
    assert y - 24 <= 2100 - PAD, f'calendario della facciata 1 troppo lungo: {round(y - 24)}'
    return out


# ---------------------------------------------------------------- facciata 1: calendario orizzontale
def _tm(s):
    return int(s[:2]) * 60 + int(s[3:5])


LBL = {'Welcome addresses': 'Welcome & opening', 'Opening remarks': 'Opening', 'Round-table discussion': 'Round table',
       'Book presentation': 'Book presentation'}

def break_icon(kind, cx, top, h=24):
    """icona a linea in blu, alta h, centrata in cx: tazzina (coffee) o forchetta e coltello (lunch)"""
    k = h / 24
    if kind == 'coffee':      # disegno in un riquadro 22 x 24
        d = ('<path d="M1 9 H15 V17 Q15 23 9 23 H7 Q1 23 1 17 Z"/>'
             '<path d="M15 11.5 Q20 11.5 20 15 Q20 18.5 15 18.5"/>'
             '<path d="M5.5 1.5 Q3.5 3.75 5.5 6"/><path d="M10.5 1.5 Q8.5 3.75 10.5 6"/>')
        w = 21
    else:                     # forchetta e coltello in un riquadro 18 x 24
        d = ('<path d="M1.5 1 V7 Q1.5 10 4.5 10 Q7.5 10 7.5 7 V1"/><path d="M4.5 1 V23"/>'
             '<path d="M15 23 V1 Q11 4 11 11 Q11 13 15 13"/>')
        w = 16
    return (f'<g transform="translate({cx - w * k / 2:.1f} {top:.1f}) scale({k:.3f})" fill="none" stroke="{{{{NODE}}}}" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{d}</g>')

def columns(W, H, days, pt=6.4):
    """Calendario (W x H, poi ruotato): i due giorni affiancati; per ogni giorno le aule in colonna (nomi in rosso,
    centrati in testa; aule che non si sovrappongono condividono la colonna) e gli orari 09-19 verso il basso; blocchi
    alti quanto la durata. Un'aula con una sola sessione che cade dentro una sessione più lunga (Capitani dentro
    Protocols) va in una scatola dentro quella, un po' a destra, che si allunga se serve. Nei blocchi delle aule che
    condividono la colonna: orario a sinistra e nome dell'aula a destra, sopra una linea sottile. Panel con il puntino
    blu, keynote e saluti su grigio chiaro, nome per keynote e workshop. Coffee e lunch break in blu nella colonna delle ore: inizio, icona, fine."""
    out = []; spk = speakers(days); warn = []
    T0, T1 = 9 * 60, 19 * 60
    DG = 70                                                  # spazio tra i due giorni
    TC = 116                                                 # colonna delle ore (e delle pause, in blu)
    GX = 10
    def merged(rows):                                        # unisci saluti; corsie: aule che non si sovrappongono nella stessa colonna
        rows = list(rows)
        w_ = [r for r in rows if short(r[3]) in ('Welcome addresses', 'Opening remarks')]
        if len(w_) == 2:
            rows = [r for r in rows if r not in w_] + [(w_[0][0], w_[0][1][:6] + w_[1][1][6:], w_[0][2], 'Welcome addresses')]
        return rows
    def all_lanes(rows, rooms):
        span = {}
        for _, t, r, _x in rows:
            a, b = _tm(t[:5]), _tm(t[6:]); s0, s1 = span.get(r, (a, b)); span[r] = (min(s0, a), max(s1, b))
        lanes = []
        for r in [r for r in rooms if r in span]:
            for ln in lanes:
                if all(span[q][1] <= span[r][0] or span[r][1] <= span[q][0] for q in ln): ln.append(r); break
            else: lanes.append([r])
        # un'aula con una sola sessione che cade dentro una sessione più lunga di un'altra colonna: la sua scatola va
        # dentro quella (nello spazio libero sotto il testo), così la colonna sparisce
        nest = {}
        for ln in list(lanes):
            if len(ln) != 1: continue
            r = ln[0]; mine = [x for x in rows if x[2] == r]
            if len(mine) != 1: continue
            a, b = _tm(mine[0][1][:5]), _tm(mine[0][1][6:])
            host = next((x for x in rows if x[2] != r and _tm(x[1][:5]) < a and b <= _tm(x[1][6:]) and x[2] not in nest.values()), None)
            if host:
                lanes.remove(ln); next(l for l in lanes if host[2] in l).append(r); nest[r] = host[1]
        return lanes, nest
    data = [(date, merged(rows), day) for (date, rows), day in zip(glance(days), days)]
    LNN = [all_lanes(rows, [r['name'] for r in day['rooms']]) for _, rows, day in data]
    LN = [l for l, _n in LNN]
    unit = (W - 2 * PAD - DG - 2 * TC - GX * sum(len(l) - 1 for l in LN)) / sum(len(l) for l in LN)   # stessa larghezza di colonna nei due giorni
    DWs = [TC + len(l) * unit + GX * (len(l) - 1) for l in LN]
    for di, (date, rows, day) in enumerate(data):
        DW = DWs[di]
        x0d = PAD + sum(DWs[:di]) + DG * di
        y = PAD
        big = 9.5
        out.append(T(x0d, y + PB.CAP * big * PT, date, '700', big, '{{INK}}'))
        out.append(T(x0d + width(date, '700', big * PT) + 18, y + PB.CAP * big * PT, WEEKDAY[date], '700', big, '{{INK}}'))
        y += PB.CAP * big * PT + 46
        lanes, nest = LNN[di]
        host_end = {(lambda r: next(x for x in rows if x[2] == r)[1])(r): None for r in nest}
        cut = {}                                             # sessione ospite: fin dove può andare il suo testo
        for r, ht in nest.items():
            cut[ht] = _tm(next(x for x in rows if x[2] == r)[1][:5])
        rows = sorted(rows, key=lambda x: x[2] in nest)      # le scatole annidate per ultime, sopra
        lane_of = {r: i for i, ln in enumerate(lanes) for r in ln}
        nl = len(lanes)
        LW = (DW - TC - GX * (nl - 1)) / nl
        LX = [x0d + TC + i * (LW + GX) for i in range(nl)]
        nblk = lambda r: sum(1 for x in rows if x[2] == r)
        # nome in testa alla colonna; in una colonna condivisa solo l'aula con più sessioni, le altre dentro il blocco
        head = {i: (ln[0] if len(ln) == 1 else next((r for r in ln if nblk(r) > 1), None)) for i, ln in enumerate(lanes)}
        for i, ln in enumerate(lanes):                      # in testa alla colonna tutte le sue aule
            out.append(T(LX[i] + LW / 2, y, ' · '.join(ln), '700', pt * .95, '{{ACC2}}', anchor='middle'))   # al centro della colonna
        y += 18
        y0g = y; K = (H - PAD - y0g) / (T1 - T0); Y = lambda m: y0g + (m - T0) * K
        brk_ = sorted({(b['time'], b['text']) for r_ in day['rooms'] for b in r_['blocks'] if b['kind'] == 'break' and 'break' in b['text'].lower()})
        for h in range(T0, T1 + 1, 30):                      # righe delle ore e delle mezz'ore
            out.insert(0, f'<line x1="{x0d + TC - 8:.1f}" y1="{Y(h):.1f}" x2="{x0d + DW:.1f}" y2="{Y(h):.1f}" stroke="{RULE if h % 60 == 0 else "#E8EBE8"}" stroke-width="1.2"/>')
            if h % 60 == 0 and not any(Y(_tm(b_[0][:5])) - 22 <= Y(h) <= Y(_tm(b_[0][:5])) + 7 + 38 + 6 + 5.2 * PT * .72 + 24 for b_ in brk_):   # niente ora sotto la scritta di una pausa
                out.append(T(x0d, Y(h) + 5.2 * PT * .36, f'{h // 60:02d}:00', '600', 5.2, GREY2))
        # pause di tutto il convegno: nella colonna delle ore, in blu, inizio, icona (tazzina / forchetta e coltello), fine
        IH = 38                                              # altezza delle icone delle pause
        for t_, txt in brk_:
            a_ = _tm(t_[:5])
            b0 = Y(a_) + 5.2 * PT * .36; wt_ = width(t_[:5], '700', 5.2 * PT)
            out.append(T(x0d, b0, t_[:5], '700', 5.2, '{{NODE}}'))
            out.append(break_icon('coffee' if 'coffee' in txt.lower() else 'lunch', x0d + wt_ / 2, b0 + 7, IH))   # icona al centro sotto l'orario
            out.append(T(x0d, b0 + 7 + IH + 6 + 5.2 * PT * .72, t_[6:11], '700', 5.2, '{{NODE}}'))   # orario di fine sotto l'icona
        lead = pt * PT * 1.18
        inside = set()                                      # aule con il nome dentro il blocco (nessuno spazio sopra)
        for i, ln in enumerate(lanes):                      # aula che condivide la colonna: nome subito sopra il suo primo blocco
            for r in ln:
                if r != head[i]:
                    inside.add(r)                           # nome dentro il blocco, come prima riga
        for _, times, room, title in rows:
            a, b = _tm(times[:5]), _tm(times[6:])
            x = LX[lane_of[room]]; ya, yb = Y(a) + 2, Y(b) - 2; hh = yb - ya
            LWb = LW
            if room in nest:                                  # scatola annidata: rientrata dentro la sessione ospite
                x += 22; LWb = LW + 16                    # un po' a destra: si vede che è un'altra aula
            hh_text = (Y(cut[times]) - 4 - ya) if times in cut else hh
            st = short(title); lab = LBL.get(st, st); who = spk.get((date, room, title))
            panel = title.startswith('Panel:'); ind = 15 if panel else 0
            if room in nest:                                  # scatola annidata: testo come gli altri, la scatola si allunga
                ind_ = 15 if title.startswith('Panel:') else 0
                need = pt * PT * 1.25 + 11 + 4 + pt * PT * 1.18 * len(wrap(lab, '400', pt * PT, LWb - 18 - ind_)) + 8
                yb = max(yb, ya + need); hh = yb - ya; hh_text = hh
            if st in KEY:
                out.append(f'<rect x="{x:.1f}" y="{ya:.1f}" width="{LWb:.1f}" height="{hh:.1f}" rx="7" fill="{FILL_G}"/>')
            else:
                out.append(f'<rect x="{x + 1.2:.1f}" y="{ya + 1.2:.1f}" width="{LWb - 2.4:.1f}" height="{hh - 2.4:.1f}" rx="7" fill="#FFFFFF" stroke="{LINE_G}" stroke-width="2.2"/>')
            if room in inside:                                # nome dell'aula come prima riga del blocco
                out.append(T(x + 9, ya + 5 + pt * PT * .95, times, '400', pt * .9, GREY))                       # orario a sinistra, come negli altri
                out.append(T(x + LWb - 9, ya + 5 + pt * PT * .95, room, '700', pt * .95, '{{ACC2}}', anchor='end'))   # nome dell'aula a destra
                yl_ = ya + pt * PT * 1.25 + 9
                out.append(f'<line x1="{x + 9:.1f}" y1="{yl_:.1f}" x2="{x + LWb - 9:.1f}" y2="{yl_:.1f}" stroke="{LINE_G}" stroke-width="1.5"/>')
                ya = yl_ + 2; hh = yb - ya; hh_text = hh
            # testo: prima prova orario sopra; se non entra, orario sulla stessa riga del titolo; poi corpo più piccolo
            for p_ in (pt, pt * .93, pt * .86, pt * .8):
                ld = p_ * PT * 1.18
                tl = wrap(lab, '400', p_ * PT, LWb - 18 - ind); wl = wrap(who, '600', p_ * PT, LWb - 18) if who else []
                if room in inside:                            # orario già sulla riga dell'aula
                    if 4 + ld * (len(tl) + len(wl)) <= hh_text + 2:
                        mode = 'senza'; break
                    continue
                if 8 + ld * (1 + len(tl) + len(wl)) <= hh_text + 2:
                    mode = 'sopra'; break
                tl1 = wrap(times[:5] + '  ' + lab, '400', p_ * PT, LWb - 18 - ind)
                if 8 + ld * (len(tl1) + len(wl)) <= hh_text + 2:
                    mode = 'riga'; break
            else:
                warn.append(st)
                mode = 'senza' if room in inside else 'riga'
            ty = ya + (2 if mode == 'senza' else 5) + p_ * PT * .9
            if mode == 'sopra':
                out.append(T(x + 9, ty, times, '400', p_ * .9, GREY)); ty += ld
                lines = tl
            elif mode == 'senza':
                lines = tl
            else:
                lines = tl1
            if panel:
                out.append(f'<circle cx="{x + 14:.1f}" cy="{ty - p_ * PT * .36:.1f}" r="4.6" fill="{{{{NODE}}}}"/>')
            for i, l_ in enumerate(lines):
                if mode == 'riga' and i == 0:                # orario in grigio davanti al titolo
                    tt = times[:5] + '  '
                    out.append(T(x + 9 + ind, ty, tt, '400', p_ * .9, GREY))
                    out.append(T(x + 9 + ind + width(tt, '400', p_ * .9 * PT), ty, l_[5:].lstrip(), '400', p_, '{{INK}}'))
                else:
                    out.append(T(x + 9 + ind, ty, l_, '400', p_, '{{INK}}'))
                ty += ld
            for l_ in wl:
                out.append(T(x + 9, ty, l_, '600', p_, '{{INK}}')); ty += ld
    assert not warn, ('calendario: testo che non entra', warn)
    return out


def panel_timeline(w, days):
    """Facciata 1: il calendario orizzontale ruotato di 90° in senso orario (si legge girando il pieghevole)."""
    return [f'<g transform="translate({w} 0) rotate(90)">', *columns(2100, w, days), '</g>']


# ---------------------------------------------------------------- facciate
def svg_doc(body, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="420mm" viewBox="0 0 {W} {H}" role="img" aria-label="{label}">'
            f'<defs><style>{FONT_CSS}</style></defs><rect x="0" y="0" width="{W}" height="{H}" fill="#FFFFFF"/>'
            + ''.join(body) + '</svg>')


def inside_face(p1):
    body = logo_line(PAD, 200, 22)
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
    for w, maker in zip(OUT_W, (panel_cover, panel_back, lambda w: panel_timeline(w, days))):
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
    with scaled(IN_SCALE):
        tpl_in = inside_face(p1)
    tpl_out = outside_face(p2, days)
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
    with scaled(IN_SCALE):
        print('30 novembre (interno, 6 mezze colonne): riempimento %', used(p1), '| non entrano:', len(r1))
    print('1 dicembre (pannelli 01-03): riempimento %', used(p2), '| non entrano:', len(r2))


if __name__ == '__main__' and '--misura' not in sys.argv:
    build()
