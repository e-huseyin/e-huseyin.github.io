# ArcheoFOSS 2026 — Media kit

One page. Open `index.html` in a browser. The buttons at the top right show one section at a time; the **Colori** menu at the top left changes the colour combination of the page and of every downloadable file.

| Button | Content | Files |
| --- | --- | --- |
| Locandina | Poster in six sizes, A0–A5, each with its own SVG download | `palette/<combination>/locandina-a0.svg` … `-a5.svg` |
| Programma | Folded A3 programme: half fold, then U-fold in three (closed 99 × 210 mm). Complete programme, no abbreviations. One 2-page PDF (page 1 outside, page 2 inside) plus the two SVGs, in the chosen colours | `palette/<combination>/programma-a3-fronte-retro.pdf`, `programma-esterno.svg`, `programma-interno.svg` |
| Logo | ARCHEO.FOSS 2026 logo and the 20th-edition symbol (20, strata, 11 nodes) | `palette/<combination>/logo.svg/.png`, `simbolo-20.svg/.png` |
| QR Code | One card per code, link written below. To add one, copy the `<figure class="qr-card">` block in `index.html` | `palette/<combination>/qr-programma.svg/.png` |
| Badge | A6 portrait (105 × 148 mm) or A7 landscape (105 × 74 mm): type name, affiliation and role, download the SVG | `badge-templates.js`, `palette/<combination>/badge-a6.svg`, `badge-a7.svg` |
| Screensaver | Animated cover for projection, single HTML file, works offline | `palette/<combination>/screensaver.html` |

## Colour combinations

| Combination | Text / lines | Accent | Nodes | Background |
| --- | --- | --- | --- | --- |
| Grafite · Pesca (`grafite-pesca`) | #252B29 | #D89277 | #D89277 | #FFFFFF |
| Grafite · Bordeaux · Blu (`grafite-bordeaux`) — **default** | #252B29 | #762F3D | #027BFF | #FFFFFF |
| Nero · Rosso mattone · Blu (`nero-mattone`) | #171717 | #A33B35 | #027BFF | #FFFFFF |

In every combination the logo is ARCHEO.FOSS 2026 with the dot and «2026» in electric blue #027BFF. Secondary greys (#656D65, #555D59) do not change.

## Programme (folded A3)

`tools/programme_build.py` lays out the full programme from `assets/source/programme.md` (latest version, from `programmeaggiornato.md`), measuring every line on the real Inter font, and writes the two SVGs and the PDF (Inter embedded) for each colour combination.

- Outside face: top row upside down = 04 flap «At a glance» (97 mm), 05 practical information with QR, 06 cover; bottom row 01–03 = 1 December with workshops (01 is 97 mm).
- Inside face: 30 November in three columns aligned with the folds; no text on the horizontal fold.
- Sizes: talk titles 7.5 pt, names and times 7 pt, «At a glance» 6.6 pt. Margins 7 mm, no bleed needed (nothing touches the edge).
- Chairs listed only by surname in the source are written in full (Andrea Simeoni; Marco Cavalazzi, Tyler Duane Johnson, Cristiano Putzolu).

Run `../.venv/bin/python tools/programme_build.py` after changing the programme; `--misura` only prints how full each column is.

## How the files are made

`tools/palette_build.py` builds everything in `assets/palette/` from the masters in `assets/source/` (`master-poster.svg`, `master-badge-a6.svg`, `master-logo-20.svg`, `master-qr.svg`, `master-colonna.svg`, `screensaver-master.html`). It removes node 12, sets the new logo, places the «20th EDITION» mark on the poster and the screensaver (Ionic capital `master-colonna.svg` at 50% in the accent colour, «20th» white with an accent outline and «EDITION» in front of it, centred on the capital, EDITION on the bottom line of the capital, top aligned with the logo; settings `COL_W`, `COL_OPACITY`), removes the node numbers (01–11) on the A5 poster and on both badges, where they would be 4–5 pt (only the dots remain; list in `NO_LABELS_POSTERS`), applies the three colour combinations and embeds the Inter font (taken from the screensaver) in every SVG. PNGs are made with Pillow (QR) and macOS `qlmanage` (logo, symbol). Run it again after changing a master:

```
../.venv/bin/python tools/palette_build.py
```

SVGs are RGB with no bleed: ask the print shop for a colour proof and bleed. Print at 100%.

Older files (reveal.js slides, old posters, panel cards, old brochure and scripts) were moved to `../af2026mediakit-archivio-2026-11-09/`; the full previous version is in `../af2026mediakit-backup-2026-11-09/`. The site needs only `index.html`, `assets/` and, to rebuild the files, `tools/` and `assets/source/`.

## Credits

- Font: Inter, © The Inter Project Authors, SIL Open Font License 1.1 (https://github.com/rsms/inter). Embedded in the SVG and PDF files.
- Programme content: ArcheoFOSS 2026 official programme (https://www.archeofoss.org/2026/programme).
- Media kit design: Hüseyin Erdoğan.
