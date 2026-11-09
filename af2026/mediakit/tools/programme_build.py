"""Programma pieghevole A3: due SVG (esterno, interno) e un PDF fronte/retro per ogni combinazione di colore.

Piegatura: A3 verticale piegato a metà in orizzontale, poi a U in tre (chiuso 99 x 210 mm).
- Lato esterno: riga alta capovolta = 04 aletta (97 mm), 05 retro, 06 copertina;
                riga bassa = 01 (97 mm), 02, 03 -> si vedono aprendo la U.
- Lato interno: foglio intero, tre colonne allineate alle pieghe (la stretta è dietro 01, a destra).
Contenuti: 30 novembre sul lato interno, 1 dicembre sui pannelli 01-03. Testo completo, senza abbreviazioni.

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
GREY, GREY2, RULE = '#555D59', '#656D65', '#C9CFC9'

# ---------------------------------------------------------------- font e misure
from fontTools.ttLib import TTFont                     # noqa: E402
_FONTS = {w: TTFont(io.BytesIO(base64.b64decode(b))) for w, b in PB.FONTS.items()}
_CMAP = {w: f.getBestCmap() for w, f in _FONTS.items()}


def width(text, weight, size):
    f, cmap = _FONTS[weight], _CMAP[weight]
    hm, upm = f['hmtx'], f['head'].unitsPerEm
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


def T(x, y, text, weight='400', pt=7.5, fill='{{INK}}', anchor='start', extra=''):
    a = '' if anchor == 'start' else f' text-anchor="{anchor}"'
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FAM[weight]}" font-size="{pt * PT:.2f}" '
            f'fill="{fill}"{a}{extra}>{escape(text)}</text>')


# ---------------------------------------------------------------- stili del programma (pt)
S = {
    'day':     ('700', 13.0, '{{INK}}'),
    'room':    ('700', 9.0, '{{ACC2}}'),
    'session': ('700', 7.8, '{{INK}}'),
    'chairs':  ('400', 7.0, GREY),
    'time':    ('600', 7.0, '{{ACC2}}'),
    'title':   ('600', 7.5, '{{INK}}'),
    'names':   ('400', 7.0, GREY),
    'break':   ('400', 7.0, GREY2),
    'note':    ('400', 7.0, GREY2),
}
LEAD = 1.20
GUTTER = 175          # colonna degli orari


def lh(style):
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
        return sum(lh(r[0]) for r in self.rows)


def units_for_day(day, w):
    us = []
    u = Unit(0); u.add('day', day['date'], w); us.append(u)
    for room in day['rooms']:
        pending = Unit(62); pending.rows.append(('room', room['name'], 0, None))
        for b in room['blocks']:
            u = pending or Unit(22)
            pending = None
            if b['kind'] == 'session':
                u.before = max(u.before, 34)
                u.add('session', b['title'], w)
                if b.get('chairs'):
                    u.add('chairs', 'Chair and introduction by ' + b['chairs'], w)
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
                u.add('break', b['text'], w, GUTTER, b['time'])
            else:
                u.add('note', b['text'], w, GUTTER)
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
                wt, pt, fill = S[style]
                y += lh(style)
                base = y - lh(style) * .22
                if style == 'room':
                    out.append(f'<line x1="{x0}" y1="{base - lh(style) * .95:.1f}" x2="{x0 + fr["w"]}" y2="{base - lh(style) * .95:.1f}" stroke="{RULE}" stroke-width="3"/>')
                if gutter:
                    gw, gp, gf = S['time']
                    out.append(T(x0, base, gutter, gw, gp, gf))
                out.append(T(x0 + indent, base, text, wt, pt, fill))
    return out


# ---------------------------------------------------------------- cornici
PAD = 70                                   # margine interno di ogni pannello
OUT_W = [970, 1000, 1000]                  # esterno: 04/01 più stretti (aletta)
IN_W = [1000, 1000, 970]                   # interno: specchio dell'esterno
HEAD_IN = 400                              # spazio per l'intestazione del lato interno
FOLD = 2100


def inside_frames():
    fr, x = [], 0
    for w in IN_W:
        for y0, y1 in ((HEAD_IN, FOLD - 45), (FOLD + 60, H - 90)):
            fr.append({'x': x + PAD, 'w': w - 2 * PAD, 'y0': y0, 'y1': y1})
        x += w
    return fr


def outside_low_frames():
    fr, x = [], 0
    for w in OUT_W:
        fr.append({'x': x + PAD, 'w': w - 2 * PAD, 'y0': FOLD + 70, 'y1': H - 70})
        x += w
    return fr


def layout():
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


def art_group():
    """Linee stratigrafiche, 11 nodi e «20» chiaro, dalla locandina (coordinate della locandina, larga 840)."""
    s = PB.tokenize((PB.SRC / 'master-poster.svg').read_text(encoding='utf-8'))
    i = s.index('<g transform="translate(20,312) scale(.87)">'); j = s.index('</g>', i) + 4
    g = s[i:j]
    g = g.replace('font-weight="700"', f'font-family="{FAM["700"]}"')
    # «20» chiaro: colore già schiarito invece della trasparenza (il convertitore PDF ignora l'opacità dei testi)
    g, n = re.subn(r'fill="\{\{ACC\}\}"( [^>]*?)? opacity="\.075"', r'fill="{{ACC_FAINT}}"\1', g)
    assert n == 1, ('«20» chiaro non trovato', n)
    g = re.sub(r'<text (?![^>]*font-family)', f'<text font-family="{FAM["400"]}" ', g)
    return g


def panel_cover(w):
    out = logo_line(PAD, 300, 26, two_lines=True)
    out.append(T(PAD, 520, '20th edition', '700', 9.5, '{{ACC2}}'))
    p, _ = paragraph(PAD, 640, 'International conference on open software, hardware, processes, data and formats in archaeological research',
                     w - 2 * PAD, '400', 9.5)
    out += p
    sc = w / 840
    out.append(f'<g transform="translate(0 {1000 - 395 * sc:.1f}) scale({sc:.4f})">{art_group()}</g>')
    out.append(T(PAD, 1740, '30 November – 1 December 2026', '700', 11.5))
    out.append(T(PAD, 1810, 'Bologna', '400', 11.5))
    out.append(T(PAD, 1930, 'Conference programme', '700', 9, '{{ACC2}}'))
    out.append(T(PAD, 2010, 'www.archeofoss.org', '600', 8, '{{ACC}}'))
    return out


def label_text(out, y, label, text, w, pt=8.0):
    out.append(T(PAD, y, label, '700', pt, '{{ACC2}}'))
    p, y = paragraph(PAD, y + pt * PT * 1.35, text, w - 2 * PAD, '400', pt)
    out += p
    return y + 70


def panel_back(w):
    out, y = [], 260
    out.append(T(PAD, y - 90, 'Practical information', '700', 12)); y += 40
    y = label_text(out, y, 'Venue', 'Dipartimento di Storia Culture Civiltà, Alma Mater Studiorum Università di Bologna, '
                   'Piazza San Giovanni in Monte 2, 40124 Bologna, Italy', w)
    y = label_text(out, y, 'Rooms', 'Aula Prodi, Aula Specola, Aula Morandi, Aula Capitani, Aula Gambi', w)
    y = label_text(out, y, 'Hosted by', 'DArchLab – Digital Archaeology Laboratory, Dipartimento di Storia Culture Civiltà, '
                   'Alma Mater Studiorum Università di Bologna', w)
    y = label_text(out, y, 'With the contribution of', 'Dipartimento di Storia Culture Civiltà, Alma Mater Studiorum Università di Bologna', w)
    y = label_text(out, y, 'Contact', 'darchlab@unibo.it', w)
    qr = (PB.SRC / 'master-qr.svg').read_text(encoding='utf-8').replace('#252B29', '{{INK}}')
    inner = qr[qr.index('>') + 1:qr.rindex('</svg>')]
    q = 380
    out.append(f'<g transform="translate({PAD} {2100 - 120 - q}) scale({q / 37:.4f})">{inner}</g>')
    out.append(T(PAD + q + 40, 2100 - 120 - q + 150, 'Full programme online', '700', 8))
    p, _ = paragraph(PAD + q + 40, 2100 - 120 - q + 210, 'www.archeofoss.org/2026/programme', w - 2 * PAD - q - 40, '400', 8)
    out += p
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


def panel_glance(w, days):
    out, y = [], 170
    out.append(T(PAD, y, 'At a glance', '700', 12)); y += 110
    for date, rows in glance(days):
        out.append(T(PAD, y, date, '700', 9, '{{ACC2}}')); y += 75
        for _, times, room, title in rows:
            # orario nella colonna a sinistra, sala e titolo a destra
            out.append(T(PAD, y, times, '600', 6.6, '{{ACC2}}'))
            p, y = paragraph(PAD + GUTTER, y, f'{room} · {title}', w - 2 * PAD - GUTTER, '400', 6.6, '{{INK}}', 1.2)
            out += p; y += 14
        y += 40
    assert y < 2060, f'«At a glance» troppo lungo: {y}'
    return out


# ---------------------------------------------------------------- facciate
def svg_doc(body, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="420mm" viewBox="0 0 {W} {H}" role="img" aria-label="{label}">'
            f'<defs><style>{FONT_CSS}</style></defs><rect x="0" y="0" width="{W}" height="{H}" fill="#FFFFFF"/>'
            + ''.join(body) + '</svg>')


def inside_face(p1):
    body = logo_line(PAD, 230, 22)
    body.append(T(PAD, 330, 'Conference programme · 30 November – 1 December 2026 · Bologna', '400', 10))
    body += draw_units(p1)
    fr, rows = p1[-1]
    u, yy = rows[-1]
    y = yy + u.height + 120
    p, _ = paragraph(fr['x'], y, 'The programme of 1 December 2026 and the workshops are on the three panels of the other side.',
                     fr['w'], '400', 7, GREY2)
    body += p
    return svg_doc(body, 'ArcheoFOSS 2026 programme, inside')


def outside_face(p2, days):
    body = draw_units(p2)
    x = 0
    for w, maker in zip(OUT_W, (lambda w: panel_glance(w, days), panel_back, panel_cover)):
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
