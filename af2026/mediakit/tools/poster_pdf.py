"""PDF vettoriali delle locandine A0-A5 (font Inter incluso), dallo stesso modello degli SVG (palette_build.poster_tpl).

Il convertitore PDF (svglib) non gestisce trasparenze, spaziatura tra le lettere e bordi dei testi:
- capitello «20th EDITION»: versione per PDF (colore già schiarito, testi in tracciati: programme_build.edition_block_pdf);
- linee stratigrafiche e grande «20th» chiaro: colore già schiarito al posto dell'opacità; il «20th» resta sotto le linee;
- testi con spaziatura tra le lettere: una lettera per volta, nella posizione giusta.
Uso (da af2026mediakit):  ../.venv/bin/python tools/poster_pdf.py
"""
import base64, html, io, re, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import palette_build as PB          # noqa: E402
import programme_build as PG        # noqa: E402


def pdf_template(a5=False):
    s = PB.poster_tpl()
    if a5:
        s = PB.strip_labels(s)
    assert PB.edition_block() in s
    s = s.replace(PB.edition_block(), PG.edition_block_pdf())
    s, n = re.subn(r'stroke="\{\{INK\}\}"( [^>]*?) opacity="([\d.]+)"', r'stroke="{{INK@\2}}"\1', s)
    assert n == 20, ('linee', n)

    def letters(m):
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
        if a.get('text-anchor') == 'end':
            x -= sum(PG.width(t, wt, size) + ls * len(t) for t, _ in segs) - ls
        out = []
        for t, f in segs:
            for ch in t:
                if ch != ' ':
                    out.append(f'<text x="{x:.2f}" y="{y:.2f}" font-family="{PG.FAM[wt]}" font-size="{size:.2f}" fill="{f}">{html.escape(ch)}</text>')
                x += PG.width(ch, wt, size) + ls
        r = ''.join(out)
        return f'<g data-faint="1">{r}</g>' if faint else r

    s = re.sub(r'(<text\b[^>]*>)(.*?)</text>', letters, s, flags=re.S)
    faint = ''.join(re.findall(r'<g data-faint="1">.*?</g>', s))
    s = re.sub(r'<g data-faint="1">.*?</g>', '', s)
    art = '<g transform="translate(20,312) scale(.87)">'
    assert s.count(art) == 1 and faint
    s = s.replace(art, art + faint)                      # il «20th» chiaro sotto le linee
    for w, fam in PG.FAM.items():
        s = s.replace(f'font-family="Inter,Arial,sans-serif" font-weight="{w}"', f'font-family="{fam}"')
    s = re.sub(r'<text (?![^>]*font-family="Inter)', '<text font-family="Inter" ', s)
    return re.sub(r'<defs><style>.*?</style></defs>', '', s, count=1, flags=re.S)


def build():
    from svglib.svglib import svg2rlg
    from svglib.fonts import register_font
    from reportlab.pdfgen import canvas
    from reportlab.graphics import renderPDF
    from reportlab.lib.units import mm
    from fontTools.ttLib import TTFont
    tpl = {False: pdf_template(False), True: pdf_template(True)}
    with tempfile.TemporaryDirectory() as tmp:
        for w in PG._FONTS:
            ttf = Path(tmp) / f'{PG.FAM[w]}.ttf'
            f = TTFont(io.BytesIO(base64.b64decode(PB.FONTS[w]))); f.flavor = None; f.save(str(ttf))
            register_font(PG.FAM[w], str(ttf))
        for pid, pal in PB.PALETTES.items():
            for k, (wmm, hmm) in PB.POSTERS.items():
                src = Path(tmp) / 'p.svg'
                src.write_text(PB.paint(tpl[k in PB.NO_LABELS_POSTERS], pal), encoding='utf-8')
                d = svg2rlg(str(src))
                sc = wmm * mm / d.width
                d.scale(sc, sc); d.width *= sc; d.height *= sc
                out = PB.OUT / pid / f'locandina-{k}.pdf'
                c = canvas.Canvas(str(out), pagesize=(wmm * mm, hmm * mm))
                c.setTitle(f'ArcheoFOSS 2026 - Poster {k.upper()}')
                c.saveState(); p = c.beginPath(); p.rect(0, 0, wmm * mm, hmm * mm); c.clipPath(p, stroke=0, fill=0)
                renderPDF.draw(d, c, 0, (hmm * mm - d.height) / 2)
                c.restoreState(); c.showPage(); c.save()
            print('ok', pid)


if __name__ == '__main__':
    build()
