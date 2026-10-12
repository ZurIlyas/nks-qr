#!/usr/bin/env python3
"""QR-карточки NKS space: 10 вариантов в стиле сайта.

    python build.py

Вшивает матрицу кода в card.html, снимает каждый вариант в Edge (1500×2115 px, формат A6),
проверяет, что код читается и ведёт на URL, и собирает страницу-галерею index.html."""
import shutil, subprocess, sys
from pathlib import Path
import cv2, numpy, segno

URL = 'https://zurilyas.github.io/nks-space/'
HERE = Path(__file__).resolve().parent
EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
NAMES = ['Классика', 'Орбита', 'Красная', 'Стикер', 'Талон', 'Полароид', 'Чёрная дыра', 'Гоночный номер', 'Минимал', 'Ленты']

# уровень коррекции H: код читается, даже если до 30% закрыто — это запас под логотип в центре
matrix = [''.join('1' if c else '0' for c in row) for row in segno.make(URL, error='h', boost_error=False).matrix]
tpl = (HERE / 'card.html').read_text(encoding='utf-8')
a = tpl.index('/*MATRIX*/') + len('/*MATRIX*/'); b = tpl.index(';', a)
(HERE / 'card.html').write_text(tpl[:a] + repr(matrix).replace("'", '"') + tpl[b:], encoding='utf-8')

out = HERE / 'png'
out.mkdir(exist_ok=True)
prof = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / '.edge'
det = cv2.QRCodeDetector()
rows = []
for i, name in enumerate(NAMES, 1):
    png = out / f'nks-qr-{i:02d}.png'
    png.unlink(missing_ok=True)
    subprocess.run([EDGE, '--headless', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=3',
                    '--window-size=500,705', '--virtual-time-budget=5000', f'--user-data-dir={prof}',
                    f'--screenshot={png}', f'{(HERE / "card.html").as_uri()}?v={i}'],
                   capture_output=True, timeout=120)
    # cv2.imread не открывает пути с кириллицей, поэтому читаем файл сами
    img = cv2.imdecode(numpy.fromfile(png, dtype=numpy.uint8), cv2.IMREAD_COLOR) if png.exists() else None
    # декодер OpenCV капризнее телефона, поэтому пробуем пять размеров: от печатного до «камера издалека»
    hits = 0
    if img is not None:
        for scale in (1, 0.7, 0.5, 0.35, 0.25):
            hits += det.detectAndDecode(cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA))[0] == URL
    ok = hits >= 2
    print(f'{i:02d} {name:16} {"читается" if ok else "НЕ ЧИТАЕТСЯ"} {hits}/5')
    rows.append((i, name, ok))
if prof == HERE / '.edge': shutil.rmtree(prof, ignore_errors=True)

cards = '\n'.join(f'''    <figure>
      <a href="png/nks-qr-{i:02d}.png" target="_blank"><img src="png/nks-qr-{i:02d}.png" alt="Вариант {i}: {n}" loading="lazy"></a>
      <figcaption><b>{i:02d}</b> {n}<a href="png/nks-qr-{i:02d}.png" download>скачать PNG</a></figcaption>
    </figure>''' for i, n, ok in rows if ok)
(HERE / 'index.html').write_text(f'''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>NKS space — QR на меню, 10 вариантов</title>
<link href="https://fonts.googleapis.com/css2?family=Russo+One&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
body {{ margin: 0; background: #0d0d0d; color: #f4efe6; font: 400 14px/1.5 "IBM Plex Mono", monospace; }}
main {{ max-width: 1400px; margin: 0 auto; padding: 40px 24px 80px; }}
h1 {{ font: 400 44px/1 "Russo One", sans-serif; text-transform: uppercase; margin: 0 0 12px; }}
h1 em {{ font-style: normal; color: #d32a20; }}
p {{ margin: 0 0 30px; color: #b9b2a6; max-width: 760px; }}
.grid {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 26px 20px; }}
figure {{ margin: 0; }}
img {{ display: block; width: 100%; border-radius: 10px; box-shadow: 0 14px 40px rgba(0, 0, 0, .6); transition: transform .25s; }}
a:hover img {{ transform: translateY(-4px) rotate(-1deg); }}
figcaption {{ display: flex; align-items: baseline; gap: 8px; margin-top: 12px; font: 400 15px/1.2 "Russo One", sans-serif; text-transform: uppercase; }}
figcaption b {{ color: #d32a20; font-weight: 400; }}
figcaption a {{ margin-left: auto; font: 400 12px/1 "IBM Plex Mono", monospace; text-transform: none; color: #f4efe6; border: 1px solid rgba(244, 239, 230, .4); border-radius: 999px; padding: 6px 10px; text-decoration: none; }}
figcaption a:hover {{ background: #f4efe6; color: #0d0d0d; }}
@media (max-width: 1100px) {{ .grid {{ grid-template-columns: repeat(3, 1fr); }} }}
@media (max-width: 640px) {{ .grid {{ grid-template-columns: repeat(2, 1fr); }} }}
</style>
</head>
<body>
<main>
  <h1>QR на меню — <em>10 вариантов</em></h1>
  <p>Код ведёт на {URL}. Каждая карточка — PNG 1500×2115 px, формат A6 (105×148 мм) в печатном качестве. Нажмите на картинку, чтобы открыть в полном размере, или «скачать PNG».</p>
  <div class="grid">
{cards}
  </div>
</main>
</body>
</html>
''', encoding='utf-8')
print('готово:', HERE / 'index.html', '— вариантов в галерее:', sum(ok for *_, ok in rows))
