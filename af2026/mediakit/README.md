# ArcheoFOSS 2026 — Media kit

One page. Open `index.html` in a browser. The buttons at the top right show one section at a time. The kit has one colour combination, Nero · Rosso mattone · Blu; downloaded files keep their exact names (e.g. `logo-archeofoss.png`).

| Button | Content | Files |
| --- | --- | --- |
| Locandina | Poster in six sizes, A0–A5, each with its own SVG and PDF download (English text, University of Bologna / DiSCi logo, programme QR) | `palette/nero-mattone/locandina-a0.svg` … `-a5.svg`, `locandina-a0.pdf` … `-a5.pdf` |
| Programma | Folded A3 programme: half fold, then U-fold in three (closed 99 × 210 mm). Complete programme, no abbreviations. One 2-page PDF (page 1 outside, page 2 inside) plus the two SVGs, in the chosen colours | `palette/nero-mattone/programma-a3-fronte-retro.pdf`, `programma-esterno.svg`, `programma-interno.svg` |
| Logo | ARCHEO.FOSS 2026 logo, the University of Bologna + ARCHEO.FOSS 2026 logo (seal as high-resolution PNG `logo-unibo-sigillo.png`, as tall as the capitals; text as vector outlines), the 20th-edition symbol (20th, strata, 11 nodes) and the «20th EDITION» capital (the same as on the poster) | `palette/nero-mattone/logo-archeofoss.svg/.png`, `logo-archeofoss-unibo.svg/.png`, `logo-simbolo-20.svg/.png`, `logo-capitello-20th.svg/.png` |
| QR Code | One card per code, link written below. To add one, copy the `<figure class="qr-card">` block in `index.html` | `palette/nero-mattone/QR-programme.svg/.png`, `QR-teams.svg/.png` (Teams event link; master `assets/source/master-qr-teams.svg` made with `tools/qr_make.py "<link>" <file>`, no external library) |
| Badge | A7 landscape (105 × 74 mm) in four models: A7-01, A7-02, A7-03 (UniBo / DiSCi logo, ARCHEO.FOSS 2026 and the capital at the top, light strata, the name in the centre in graphite, rosso mattone or blue with the affiliation below, the role just above a rosso mattone band at the bottom) and A7-04 (name, affiliation, role, QR). Type the data and download the SVG; the A6 badge was removed | `badge-templates.js`, `palette/nero-mattone/badge-A7-01.svg` … `badge-A7-04.svg` |
| Screensaver | Animated cover for projection, single HTML file, works offline | `palette/nero-mattone/Screensaver.html` |
| Teams | Microsoft Teams event images: banner 1840 × 460 px (left, with 36 px margins: University of Bologna / DiSCi logo and the «20th EDITION» capital in one row, then title, subtitle and date; right: poster strata with the large «20th») and logo 800 × 800 px (ARCHEO. / FOSS / 2026 on three lines with 60 px margins, smaller strata lower down); PNG at the exact pixel size (twice Teams' 920 × 230 and more than twice 280 × 280; drawn 4× larger and reduced, lossless, sRGB profile embedded), plus SVG | `palette/nero-mattone/teams-banner.png/.svg`, `teams-logo.png/.svg` |

## Colours

| Combination | Text / lines | Accent | Nodes | Background |
| --- | --- | --- | --- | --- |
| Nero · Rosso mattone · Blu (`nero-mattone`) | #171717 | #A33B35 | #027BFF | #FFFFFF |

The logo is ARCHEO.FOSS 2026 with the dot and «2026» in electric blue #027BFF. The two other combinations (Grafite · Bordeaux, Grafite · Pesca) were removed on 2026-11-18; their colours can be added back in `PALETTES` (`tools/palette_build.py`).

## Programme (folded A3)

`tools/programme_build.py` lays out the full programme from `assets/source/programme.md` (latest version, from `programmeaggiornato.md`), measuring every line on the real Inter font, and writes the two SVGs and the PDF (Inter embedded) for each colour combination.

Panels are numbered as on the sheet: outside top row 3-2-1, bottom row 4-5-6; inside 7-12. Print double-sided, flipping on the **long edge**.

- Outside face, top row (upside down, so it reads upright after the half fold): 3 cover (left, 97 mm), 2 rooms, committee and QR, 1 overview of the two days. Bottom row 4-5-6: 1 December with the workshops (4 is 97 mm).
- Inside face: rotated 180°, so panel 7 is behind panel 4. 30 November in six half-columns aligned with the folds; no text on the horizontal fold.
- Panel 3 (cover): University of Bologna / DiSCi logo and the «20th EDITION» capital, same height (18.5 mm); ARCHEO.FOSS 2026 on one line; subtitle (9 mm and 14 mm gaps, `COVER_GAP`, `COVER_GAP2`); strata with the large pale «20th»; date; VENUE block as on the poster. In the PDF the capital uses the colour already lightened to 50% and its texts are outlines.
- Panel 2: centred, no title; Rooms as equal boxes grouped by floor (Ground floor: Prodi, Capitani; First floor: Gambi, Morandi; Second floor: Specola; `FLOORS`), Organising Committee (names in semibold, affiliation below in grey), QR with «Full programme online» and the link, «Hosted by» at the bottom (`BACK_K` scales the text).
- Panel 1: calendar of the two days, one lane per room (rooms in coloured boxes; rooms that never overlap share a lane); panels as outlined boxes, keynotes, welcome and opening filled with a light tint; text in regular weight. Blocks are as tall as their text, not as their duration; sessions at the same time sit side by side.
- Programme (30 Nov and 1 Dec): each room in a box in the combination's colour (72%) with its floor on the right, coffee and lunch breaks in a light box across the row, chairs in italic (slanted: the embedded Inter has no italic), extra space after panel titles and chairs, dark grey text. Sizes: talk titles 7.8 pt, names, chairs and times 7.3 pt, panel titles 8.2 pt, calendar 7.2 pt. The repeated workshop registration note appears once. Margins 7 mm, no bleed needed.
- Names: the embedded Inter has no «ğ»: it is drawn as «g» plus a breve (Hüseyin Erdoğan).
- Chairs listed only by surname in the source are written in full (Andrea Simeoni; Marco Cavalazzi, Tyler Duane Johnson, Cristiano Putzolu).

Run `../.venv/bin/python tools/programme_build.py` after changing the programme; `--misura` only prints how full each column is.

## How the files are made

`tools/palette_build.py` builds everything in `assets/palette/` from the masters in `assets/source/` (`master-poster.svg`, `master-badge-a6.svg`, `master-logo-20.svg`, `master-qr.svg`, `master-colonna.svg`, `logo-unibo-disci.png`, `screensaver-master.html`). It removes node 12, sets the new logo, places the «20th EDITION» mark on the poster and the screensaver (screensaver header in one row: ARCHEO.FOSS 2026 on the left at 60% of the width `SS_TITLE`, University logo and capital on the right with the same height, subtitle below; Ionic capital `master-colonna.svg` at 50% in the accent colour, «20th» white with an accent outline and «EDITION» in front of it, centred on the capital, EDITION on the bottom line of the capital, top aligned with the logo; settings `COL_W`, `COL_OPACITY`), lays out the poster (`poster_tpl`: University of Bologna / DiSCi logo `logo-unibo-disci.png` top left and the capital top right at the same height, ARCHEO.FOSS 2026 full width below, subtitle, strata band, a reference line above the date, the date full line width, VENUE on the left and the programme QR on the right aligned to the line ends, archeofoss.org; one 10 mm margin on every side, settings `P_M`, `P_HEAD_H`, `P_QR`), extends the strata lines to the left and right edges of the sheet (same formula as the master, `strata_paths`) and adds «th» to the large pale «20» behind them (`BIG_20TH_SCALE` = 80%; the same «20th» is used on the symbol, both badges and the screensaver, ending inside the edge), removes the node numbers (01–11) on the A5 poster and on both badges, where they would be 4–5 pt (only the dots remain; list in `NO_LABELS_POSTERS`), applies the three colour combinations and embeds the Inter font (taken from the screensaver) in every SVG. PNGs are made with Pillow (QR) and macOS `qlmanage` (logo, symbol). Run it again after changing a master:

```
../.venv/bin/python tools/palette_build.py
```

Poster PDFs (vector, Inter embedded, exact page size) are made from the same template by `tools/poster_pdf.py`; run it after `palette_build.py`:

```
../.venv/bin/python tools/poster_pdf.py
```

The PDF converter ignores transparency, letter spacing and text outlines, so for the PDF the capital uses the colour already lightened, the strata and the pale «20th» use lightened colours instead of opacity, and spaced texts are placed letter by letter.

SVGs are RGB with no bleed: ask the print shop for a colour proof and bleed. On the poster the strata lines touch the left and right edges, so bleed (usually 3 mm) and a safety margin for the text are needed. Print at 100%.

Older files (reveal.js slides, old posters, panel cards, old brochure and scripts) were moved to `../af2026mediakit-archivio-2026-11-09/`; the full previous version is in `../af2026mediakit-backup-2026-11-09/`. The site needs only `index.html`, `assets/` and, to rebuild the files, `tools/` and `assets/source/`.

## Credits

- Font: Inter, © The Inter Project Authors, SIL Open Font License 1.1 (https://github.com/rsms/inter). Embedded in the SVG and PDF files.
- Programme content: ArcheoFOSS 2026 official programme (https://www.archeofoss.org/2026/programme).
- Media kit design: Hüseyin Erdoğan.
