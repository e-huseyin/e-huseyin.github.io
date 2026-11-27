"""Badge nominativi in PDF: fogli A4 verticali con 8 badge A7 orizzontali (2 colonne x 4 righe, 105 x 74 mm).

Dati: ../Catering List.xlsx, foglio «Persone» (Nome, Cognome, Affiliazione, Stato). Nessuna tipologia sul badge.
Si stampano tutte le persone tranne «Rinuncia» e l'elenco EXCLUDE, in ordine alfabetico di cognome.
--retro aggiunge dopo ogni foglio il retro (data, QR programma e Teams, luogo), speculare per la stampa sul lato lungo.
Il modello è lo stesso di palette_build.badge_a7_model_tpl (badge definitivo); per il PDF (svglib) trasparenze e spaziature
tra le lettere sono rese come in tools/poster_pdf.py.

Uso (da af2026mediakit):  ../.venv/bin/python -I tools/badge_pdf.py [quanti] [uscita.pdf]
  quanti: numero di persone (predefinito tutte)
"""
import base64, html, io, re, sys, tempfile, unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import palette_build as PB          # noqa: E402
import programme_build as PG        # noqa: E402

XLSX = PB.ROOT.parent / 'Catering List.xlsx'
OUT = PB.ROOT.parent / 'badge-stampa'
BW, BH = 105, 74                    # mm, A7 orizzontale
PAGE_W, PAGE_H = 210, 297           # mm, A4 verticale
COLS, ROWS = 2, 4
TOP = (PAGE_H - ROWS * BH) / 2      # 0,5 mm sopra e sotto
MAXW = 1050 - 2 * 44                # larghezza utile del testo nel badge (unità del modello)
AFF_PRINT = {'University of Bologna': 'Alma Mater Studiorum - Università di Bologna'}   # come scrivere l'ente sul badge


def norm(s):
    return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower().strip()


EXCLUDE = set()                     # nomi da non stampare (minuscolo, senza accenti: «nome cognome»)
NAME_PRINT = {'Huseyin Erdoğan': 'Huseyin Erdogan', 'Hüseyin Erdoğan': 'Huseyin Erdogan'}     # come scrivere il nome sul badge (il Catering List resta com'è)


def people():
    """Tutte le persone del foglio, tranne «Rinuncia» e EXCLUDE. Senza affiliazione: badge con il solo nome."""
    import openpyxl
    ws = openpyxl.load_workbook(XLSX, read_only=True)['Persone']
    hdr = next(ws.iter_rows(min_row=2, max_row=2, values_only=True))
    ix = {h: i for i, h in enumerate(hdr)}
    out = []
    for r in ws.iter_rows(min_row=3, values_only=True):
        cog, aff = (r[ix['Cognome']] or '').strip(), (r[ix['Affiliazione']] or '').strip()
        nome = ' '.join((r[ix['Nome']] or '').split())
        if not cog or r[ix['Stato']] == 'Rinuncia' or norm(f'{nome} {cog}') in EXCLUDE:
            continue
        full = f'{nome} {cog}'.strip()
        out.append({'name': NAME_PRINT.get(full, full), 'aff': aff, 'key': (norm(cog), norm(nome))})
    return sorted(out, key=lambda p: p['key'])


def fit(text, weight, size, minsize, ls=0.0):
    """Corpo del testo ridotto finché sta nella larghezza utile (ls: spaziatura tra le lettere)."""
    while size > minsize and PG.width(text, weight, size) + ls * (len(text) - 1) > MAXW:
        size -= 1
    return size


def letters(m):
    """Testi con spaziatura tra le lettere o trasparenti: una lettera per volta (come tools/poster_pdf.py)."""
    tag, body = m.group(1), m.group(2)
    a = dict(re.findall(r'([\w-]+)="([^"]*)"', tag))
    faint = a.get('opacity') == '.075'
    if 'letter-spacing' not in a and not faint:
        return m.group(0)
    fill = '{{ACC_FAINT}}' if faint else a.get('fill', '#000')
    wt, size, ls = a.get('font-weight', '400'), float(a['font-size']), float(a.get('letter-spacing', 0))
    segs, pos = [], 0
    for t in re.finditer(r'<tspan fill="([^"]+)">(.*?)</tspan>', body):
        segs.append((html.unescape(body[pos:t.start()]), fill)); segs.append((html.unescape(t.group(2)), t.group(1))); pos = t.end()
    segs.append((html.unescape(body[pos:]), fill))
    x, y = float(a['x']), float(a['y'])
    total = sum(PG.width(t, wt, size) + ls * len(t) for t, _ in segs) - ls
    if a.get('text-anchor') == 'end':
        x -= total
    elif a.get('text-anchor') == 'middle':
        x -= total / 2
    out = []
    for t, f in segs:
        for ch in t:
            if ch != ' ':
                out.append(f'<text x="{x:.2f}" y="{y:.2f}" font-family="{PG.FAM[wt]}" font-size="{size:.2f}" fill="{f}">{html.escape(ch)}</text>')
            x += PG.width(ch, wt, size) + ls
    r = ''.join(out)
    return f'<g data-faint="1">{r}</g>' if faint else r


def badge_svg(p):
    s = PB.badge_a7_model_tpl(PB.BADGE_FILL)
    s = s.replace(PB.edition_block(), PG.edition_block_pdf())
    s, n = re.subn(r'stroke="\{\{INK\}\}"( [^>]*?) opacity="([\d.]+)"', r'stroke="{{INK@\2}}"\1', s)
    assert n == 20, ('linee', n)
    # nome al centro; affiliazione in maiuscolo vicino alla fascia (nessuna tipologia)
    aff = AFF_PRINT.get(p['aff'], p['aff']).upper()
    ns, as_ = fit(p['name'], '700', 72, 40), fit(aff, '700', 28, 18, 1.2)
    s = re.sub(r'font-size="72"( fill="[^"]+">)YOUR NAME<', lambda m: f'font-size="{ns}"{m.group(1)}{html.escape(p["name"])}<', s)
    s, n = re.subn(r'font-size="28"( letter-spacing="1\.2" fill="\{\{ACC2\}\}">)YOUR AFFILIATION<',
                   lambda m: f'font-size="{as_}"{m.group(1)}{html.escape(aff)}<', s)
    assert n == 1 and 'YOUR NAME' not in s and 'PARTICIPANT' not in s
    s = re.sub(r'(<text\b[^>]*>)(.*?)</text>', letters, s, flags=re.S)
    faint = ''.join(re.findall(r'<g data-faint="1">.*?</g>', s))
    s = re.sub(r'<g data-faint="1">.*?</g>', '', s)
    art = '<g transform="translate(20,312) scale(.87)">'
    assert s.count(art) == 1 and faint
    s = s.replace(art, art + faint)                      # il «20th» chiaro sotto le linee
    for w, fam in PG.FAM.items():
        s = s.replace(f'font-family="Inter,Arial,sans-serif" font-weight="{w}"', f'font-family="{fam}"')
    s = re.sub(r'<text (?![^>]*font-family="Inter)', '<text font-family="Inter" ', s)
    s = re.sub(r'<defs><style>.*?</style></defs>', '', s, count=1, flags=re.S)
    return PB.paint(s, next(iter(PB.PALETTES.values())))


def qr_group(name, x, y, size):
    """QR del kit (assets/source/master-qr*.svg): la parte stampata (senza i 4 moduli di bordo bianco) è larga size,
    con l'angolo in alto a sinistra in (x, y); così i due QR sembrano grandi uguali."""
    src = (PB.SRC / name).read_text(encoding='utf-8')
    n = float(re.search(r'viewBox="0 0 ([\d.]+)', src).group(1))
    k = size / (n - 8)
    inner = src[src.index('>') + 1:src.rindex('</svg>')].replace(' shape-rendering="crispEdges"', '')
    inner = re.sub(r'<rect [^>]*fill="#fff"/>', '', inner, count=1)     # fondo bianco già sotto: non copre la cornice
    return f'<g transform="translate({x - 4 * k:.2f} {y - 4 * k:.2f}) scale({k:.5f})">{inner}</g>'


def back_svg():
    """Retro del badge: titolo, QR del programma e QR di Teams con le didascalie, data e luogo. Niente al bordo:
    nella stampa fronte/retro il retro può spostarsi di 1-2 mm."""
    W, H, Q, y0 = 1050, 740, 270, 170
    xs = (W / 2 - Q - 75, W / 2 + 75)                        # due QR da 27 mm, 15 mm tra loro
    B, R, SB = PG.FAM['700'], PG.FAM['400'], PG.FAM['600']
    t = lambda x, y, txt, fam, size, fill: (f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" font-family="{fam}" '
                                            f'font-size="{size}" fill="{fill}">{html.escape(txt)}</text>')
    # in alto la data, al centro i due QR nelle cornici, sotto il luogo (senza titolo)
    body = [f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>', t(W / 2, 104, '30 November – 1 December 2026', B, 36, '{{INK}}')]
    for x, name, lab, sub in ((xs[0], 'master-qr.svg', 'PROGRAMME', 'archeofoss.org/2026/programme'),
                              (xs[1], 'master-qr-teams.svg', 'ONLINE ON TEAMS', 'Microsoft Teams link')):
        body += [f'<rect x="{x - 40}" y="{y0 - 22}" width="{Q + 80}" height="{Q + 124}" rx="18" fill="none" stroke="{{{{ACC2}}}}" stroke-width="3"/>',
                 qr_group(name, x, y0, Q), t(x + Q / 2, y0 + Q + 46, lab, B, 26, '{{ACC2}}'), t(x + Q / 2, y0 + Q + 80, sub, R, 20, '#555D59')]
    body += [t(W / 2, 608, 'Department of History and Cultures – University of Bologna', SB, 27, '{{INK}}'),   # venue
             t(W / 2, 646, 'Piazza San Giovanni in Monte 2, 40124 Bologna', R, 27, '#3F4643')]
    s = (f'<svg xmlns="http://www.w3.org/2000/svg" width="105mm" height="74mm" viewBox="0 0 {W} {H}">' + ''.join(body) + '</svg>')
    s = re.sub(r'(<text\b[^>]*letter-spacing[^>]*>)(.*?)</text>', letters, s, flags=re.S)   # titolo lettera per lettera
    return PB.paint(s.replace('#252B29', '{{INK}}'), next(iter(PB.PALETTES.values())))


def build(n=None, out=None, back=False):
    from svglib.svglib import svg2rlg
    from svglib.fonts import register_font
    from reportlab.pdfgen import canvas
    from reportlab.graphics import renderPDF
    from reportlab.lib.units import mm
    from fontTools.ttLib import TTFont
    ps = people()[:n] if n else people()
    OUT.mkdir(exist_ok=True)
    out = Path(out) if out else OUT / f'badge-{len(ps)}.pdf'
    c = canvas.Canvas(str(out), pagesize=(PAGE_W * mm, PAGE_H * mm))
    c.setTitle('ArcheoFOSS 2026 - Badge A7')
    with tempfile.TemporaryDirectory() as tmp:
        for w in PG._FONTS:
            ttf = Path(tmp) / f'{PG.FAM[w]}.ttf'
            f = TTFont(io.BytesIO(base64.b64decode(PB.FONTS[w]))); f.flavor = None; f.save(str(ttf))
            register_font(PG.FAM[w], str(ttf))
        def drawing(svg):
            src = Path(tmp) / 'b.svg'
            src.write_text(svg, encoding='utf-8')
            d = svg2rlg(str(src))
            sc = BW * mm / d.width
            d.scale(sc, sc); d.width *= sc; d.height *= sc
            return d

        def place(d, col, row):
            x, y = col * BW * mm, (PAGE_H - TOP - (row + 1) * BH) * mm
            c.saveState(); pth = c.beginPath(); pth.rect(x, y, BW * mm, BH * mm); c.clipPath(pth, stroke=0, fill=0)
            renderPDF.draw(d, c, x, y)
            c.restoreState()

        rear = drawing(back_svg()) if back else None
        per = COLS * ROWS
        for s0 in range(0, len(ps), per):
            sheet = ps[s0:s0 + per]
            for k, p in enumerate(sheet):
                place(drawing(badge_svg(p)), k % COLS, k // COLS)
            cut_lines(c, mm)
            c.showPage()
            if back:
                # retro: colonne scambiate, così stampando fronte/retro sul lato lungo ogni retro cade dietro il suo fronte
                for k in range(len(sheet)):
                    place(rear, COLS - 1 - k % COLS, k // COLS)
                c.showPage()
        c.save()
    print('ok', out, len(ps), 'badge', [p['name'] for p in ps])
    return out


def cut_lines(c, mm):
    """Linee di taglio sottili e grigie sui bordi dei badge."""
    c.saveState(); c.setStrokeColorRGB(.72, .72, .72); c.setLineWidth(.25)
    for col in range(COLS + 1):
        c.line(col * BW * mm, TOP * mm, col * BW * mm, (PAGE_H - TOP) * mm)
    for row in range(ROWS + 1):
        y = (TOP + row * BH) * mm
        c.line(0, y, PAGE_W * mm, y)
    c.restoreState()


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a != '--retro']
    build(int(args[0]) if args else None, args[1] if len(args) > 1 else None, back='--retro' in sys.argv)
