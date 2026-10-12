# ArcheoFOSS 2026 — Grafite — reveal.js konsept sunumu

19 slaytlık İtalyanca sunum. Data Strata / Open Network yaklaşımını, A4 ve A5 taslaklarını, program broşürü önerisini ve 12 panelin ortak görsel sistemini içerir. Konuşmacı notlarında Türkçe açıklamalar da bulunur.

## Hemen aç

ZIP’i çıkar ve `index.html` dosyasını Chrome, Edge veya Firefox ile aç. Sunum, grafikler ve yazıtipleri pakete dahildir. İnternet, npm veya bir derleme adımı gerekmez. Ok tuşlarıyla ilerle. Panel slaydındaki 12 düğme ve görsel katman düğmeleri kullanılabilir.

Konuşmacı görünümü için yerel sunucu veya GitHub Pages kullan. Terminalde paket klasörüne girdikten sonra:

```bash
python3 -m http.server 8000
```

Tarayıcıda `http://localhost:8000` adresini aç. `S` tuşuyla notlar açılır. Tarayıcı açılır pencereyi engellerse bu site için izin ver. `O` veya `Esc` slayt genel görünümünü, `F` tam ekranı açar. Dokunmatik ekranda yana kaydırabilirsin. Yoğun slaytlar telefonda yatay ekranda daha rahat okunur.

## İki renk seçeneği

Sunumun üst çubuğundaki **Palette → 1 · Bianco / 2 · Carta** düğmelerinden veya renk slaydındaki iki büyük seçenekten paleti değiştir. Seçim tüm slaytlara, A4/A5 afişlerine, panel grafiklerine ve SVG indirme bağlantılarına birlikte uygulanır; sayfa yenilendiğinde korunur.

1. **Bianco / Grafite / Pesca** (varsayılan): `#FFFFFF`, `#252B29`, `#D89277`. Üçüncü renk, orijinal 03/19 slaydındaki “per relazioni” vurgusundan alınmıştır.
2. **Carta / Grafite / Ossido**: `#F4F1E8`, `#252B29`, `#AC4B35`. İlk sunumun renkleri.

Seçili palet adres çubuğuna da eklenir: `?palette=bianco` veya `?palette=carta`. **PDF** düğmesi seçili paleti yazdırma görünümüne taşır. Paket içindeki `presentation.pdf` birinci paletin statik önizlemesidir. Varsayılan SVG’ler birinci palette, orijinal renklere sahip SVG’ler `assets/palettes/carta/` klasöründedir.

## GitHub Pages’te paylaş

### Zaten bir kişisel siten varsa

Mevcut ana sayfanı korumak için yayımlanan klasöründe `archeofoss-2026` adlı bir alt klasör oluştur. Bu paketin **içindeki** tüm dosya ve klasörleri oraya kopyala. Örnek adres: `https://KULLANICI.github.io/archeofoss-2026/`. Mevcut yayımlama ayarını kullanabilirsin. `assets` ve `vendor` klasörlerini eksiksiz taşı. Yollar göreli olduğu için sunum alt klasörde de çalışır.

### Yeni bir depo oluşturuyorsan

1. GitHub’da bir depo oluştur, örneğin `archeofoss-2026`.
2. Paketin içeriğini deponun köküne yükle. `index.html`, `assets` ve `vendor` aynı düzeyde olsun. Paket klasörünü fazladan bir üst klasör olarak yükleme.
3. `.nojekyll` dosyasını da ekle.
4. `Settings → Pages → Build and deployment` bölümünde `Source: Deploy from a branch` seç.
5. Yayımlanan dalı (genellikle `main`) ve `/(root)` seçip kaydet.
6. GitHub’ın gösterdiği Pages adresini aç. Yayımlamanın bitmesi birkaç dakika sürebilir.

Kaynak: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site

## PDF

Paket içinde `presentation.pdf` statik önizlemesi bulunur. İnteraktif seçimleri göstermez. Panel slaydında varsayılan 02 numaralı paneli gösterir.

Kendin yeniden PDF almak için Chrome/Chromium’da üstteki `PDF` bağlantısını aç veya sunum adresine `?print-pdf` ekle. `Cmd+P` / `Ctrl+P` ile yazdır, “PDF olarak kaydet”, yatay yön, kenar boşluğu yok ve arka plan grafikleri açık ayarlarını kullan.

Kaynak: https://revealjs.com/pdf-export/

## Dosyaları değiştir

- `index.html`: slayt metinleri ve İtalyanca/Türkçe konuşmacı notları.
- `assets/theme.css`: renkler, tipografi ve yerleşim.
- `assets/app.js`: reveal.js ayarları ve etkileşimler.
- `assets/panels.js`: 12 panelin başlıkları, kısa etiketleri ve editoryal aileleri.
- `assets/poster-a4.svg`, `assets/poster-a5.svg`: düzenlenebilir afiş taslakları.
- `assets/panel-card-*.svg`: üç panel için tasarım örnekleri.
- `assets/panel-field-*.svg`: 12 panelin görsel alan varyantları.
- `tools/build_assets.py`: isteğe bağlı, yalnızca Python standart kütüphanesiyle vektör dosyalarını yeniden üretir. Yeniden üretme, SVG’lere elle yapılan değişikliklerin üzerine yazar. Kaynak metinler script ve panels.js içinde ayrı bulunduğundan değişiklikleri tutarlı tut.
- `CREDITS.md`: kaynaklar ve üçüncü taraf lisansları.

SVG dosyaları Inkscape veya Illustrator ile açılabilir. Bağımsız SVG’lerde Inter yazıtipi gömülüdür. Düzenleme sırasında yazıtipi değiştirme uyarısı gelirse Inter kur veya fontu koruyarak dışa aktar.

## Taslağın sınırları

Konsept çalışma adı, dört panel ailesi ve geometrik ilişkiler tasarım önerisidir. Eğriler gerçek ölçüm verisi değildir. Panel numaraları kaynak sırasını izler; resmî program sırası değildir. Program maketindeki panel/gün eşleşmeleri ve saat kutuları yer tutucudur. Kurumsal logolar ile kesin salon bilgileri eklenecek.

Afiş SVG’leri RGB konsept taslaklarıdır; taşma payı, matbaa renk profili ve PDF/X ayarları içermez. Baskı öncesi gerçek boyutta prova ve kurum onayı gerekir. Sunum resmî olarak onaylanmış konferans görsel kimliği değildir.

## Grafite sürümünü aç

Bu paketi yeni bir klasöre çıkar ve `archeofoss-2026-graphic/index.html` dosyasını aç. Sunumun alt bilgisinde **GRAFITE** görünecek. Birinci seçenek **Bianco / Grafite / Pesca**: `#FFFFFF`, `#252B29`, `#D89277`. Yeni dosyaları GitHub Pages’te mevcut sunumla aynı yere yüklediğinde CSS, JavaScript ve grafikler sürüm parametresiyle yeniden yüklenir.

## Program broşürünün iki biçimi

11/19 numaralı **Programma pieghevole** slaydında **1 · Bi-fold A3 / A4** veya **2 · Tri-fold DL** seç. Her biçimin dış ve iç yüzü eksiksiz gösterilir. **Anteprima completa** iki yüzü büyük boyutta açar; **Scarica esterno SVG** ve **Scarica interno SVG** seçili paletin dosyalarını indirir.

- **İkili:** A3 420 × 297 mm açık, A4 210 × 297 mm kapalı; dört yüzey. İki iç A4 sayfası birer güne ayrılır. 12 panelin tam başlıkları örnek olarak yerleştirilmiştir.
- **DL üçlü:** A4 297 × 210 mm açık, 99 × 210 mm kapalı; üç panel, altı yüzey. Eşit panelli akordeon/Z katlama önerisi. İç yüzde iki günlük kısa panel etiketleri ve tematik harita; dış yüzde panel dizini, bilgiler ve kapak bulunur.

Gün/panel dağılımı yerleşimi göstermek içindir; saat, salon ve konuşmacı bilgisi kesin programdan eklenecektir. Bütün bildirilerin özetleri bu kısa broşürlere sığdırılmaya çalışılmamıştır. SVG’ler düzenlenebilir RGB taslaklarıdır, baskı taşması içermez. `fold=bifold` veya `fold=dl` URL parametresi ve PDF bağlantısı seçili biçimi korur.

Dosyalar: `assets/programme-bifold-outer.svg`, `assets/programme-bifold-inner.svg`, `assets/programme-dl-outer.svg`, `assets/programme-dl-inner.svg`. Carta paleti `assets/palettes/carta/` altında aynı dosya adlarıyla bulunur. `tools/build_programme.py` sadece broşürleri yeniden üretir.
