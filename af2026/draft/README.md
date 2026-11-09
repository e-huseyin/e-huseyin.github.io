# ArcheoFOSS 2026 — Grafite — Data Strata / Open Network

Proposta di identità visiva in **19 slide reveal.js**, con prototipi A4/A5 in SVG e una serie grafica per i panel. Testi in italiano, note del relatore in italiano e turco. La guida completa in turco è in `README_TR.md`.

## Apertura

Aprire `index.html` nel browser. Software, font e immagini sono inclusi: nessuna dipendenza esterna e nessuna compilazione.

Per la vista relatore, avviare un server locale nella cartella del pacchetto:

```bash
python3 -m http.server 8000
```

Aprire `http://localhost:8000`. Frecce: navigazione. `O` / `Esc`: panoramica. `F`: schermo intero. `S`: note, con server locale o GitHub Pages e popup consentiti. Su telefono è consigliato l’orientamento orizzontale per le slide più dense.

## Due palette selezionabili

I pulsanti **Palette → 1 · Bianco / 2 · Carta** nella barra e i due pulsanti nella slide del colore cambiano insieme slide, manifesti A4/A5, grafica dei panel e SVG scaricabili. La scelta resta memorizzata e compare nell’URL.

1. **Bianco / Grafite / Pesca** (predefinita): `#FFFFFF`, `#252B29`, `#D89277`. L’accento riprende “per relazioni” nella slide 03/19 originale.
2. **Carta / Grafite / Ossido**: `#F4F1E8`, `#252B29`, `#AC4B35`, la palette originale.

È possibile condividere `?palette=bianco` o `?palette=carta`. Il collegamento **PDF** conserva la palette scelta. `presentation.pdf` mostra la prima opzione. Gli SVG predefiniti usano la prima palette; gli originali sono in `assets/palettes/carta/`.

## GitHub Pages

Se il sito personale esiste già, copiare il contenuto del pacchetto in una sottocartella del sito, ad esempio `archeofoss-2026/`, senza sostituire la home page. Tutti i percorsi sono relativi.

Per un repository nuovo, copiare il contenuto del pacchetto nella radice: `index.html`, `assets/`, `vendor/` e `.nojekyll`. Da **Settings → Pages**, scegliere **Deploy from a branch**, il ramo di pubblicazione e **/(root)**. Salvare e attendere il deployment. Non occorre una pipeline di build.

Documentazione: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site

## PDF e asset

`presentation.pdf` è un’anteprima statica, con il panel 02 selezionato. Per esportare di nuovo: aprire il collegamento PDF nella barra, stampare da Chrome/Chromium, salvare come PDF in orizzontale, senza margini e con grafica di sfondo attiva. https://revealjs.com/pdf-export/

SVG modificabili in `assets/`: `poster-a4.svg`, `poster-a5.svg`, `panel-card-*.svg`, `panel-field-*.svg`. I poster sono prototipi RGB senza abbondanza. Il PDF delle slide non è un esecutivo di stampa dei volantini.

## Modifica

Contenuto: `index.html`. Stile: `assets/theme.css`. Interazioni: `assets/app.js`. Titoli: `assets/panels.js`. Il generatore facoltativo `tools/build_assets.py` usa solo Python standard e rigenera gli SVG, sovrascrivendo eventuali modifiche manuali. I dati testuali del generatore e di `panels.js` vanno mantenuti coerenti. `presentation.pdf` va rigenerato dopo modifiche alle slide.

## Stato della proposta

Concept, famiglie tematiche e posizioni dei nodi sono scelte editoriali. Le curve non rappresentano dati misurati. La numerazione segue l’elenco della Call for papers e non l’ordine del programma. Il programma pieghevole è uno schema con segnaposto. Loghi, sala, diciture e contenuti definitivi richiedono conferma del comitato.

Fonti e licenze: `CREDITS.md`, `vendor/reveal/LICENSE`, `assets/fonts/*-LICENSE.txt`.

## Versione Grafite

Estrarre in una cartella nuova e aprire `archeofoss-2026-graphic/index.html`. Il piè di pagina mostra **GRAFITE**. La prima palette è **Bianco / Grafite / Pesca**: `#FFFFFF`, `#252B29`, `#D89277`. CSS, JavaScript e SVG utilizzano un parametro di versione per evitare gli asset precedenti nella cache.

## Due formati di programma

Nella slide **Programma pieghevole** (11/19), scegliere **Bi-fold A3 / A4** oppure **Tri-fold DL**. Entrambi i lati sono completi; **Anteprima completa** li ingrandisce. I due collegamenti SVG seguono formato e palette selezionati.

- Bi-fold: A3 420 × 297 mm aperto, A4 210 × 297 mm chiuso, quattro facciate. Una pagina interna per giorno, con i dodici titoli completi dei panel.
- Tri-fold DL: A4 297 × 210 mm aperto, 99 × 210 mm chiuso, tre pannelli e sei facciate, piega a fisarmonica/Z. Interno con due giornate sintetiche e mappa tematica; esterno con indice, informazioni e copertina.

Giorni, orari, relatori e sale sono da confermare; l’assegnazione dei panel serve soltanto a valutare la capienza. Non è un programma approvato. SVG RGB editabili senza abbondanza. Il parametro `fold=bifold` / `fold=dl` e il collegamento PDF conservano la scelta. I quattro SVG `assets/programme-*.svg` hanno copie nella palette Carta; `tools/build_programme.py` rigenera solo i programmi.
