#!/usr/bin/env python3
"""Сборка автономной HTML-страницы чек-листа РКД из исходников.

    python build.py            собрать index.html и dist/rkd_pcb_checklist_v<версия>.html
    python build.py --check    проверить, что index.html соответствует исходникам (для CI)

Публичная сборка (index.html, dist/*_v<версия>.html) содержит только свободный шрифт
DejaVu Sans Condensed. Если в fonts/ лежит GOST_B.ttf (не хранится в репозитории),
дополнительно собирается dist/*_v<версия>_gost.html со встроенным шрифтом ГОСТ тип Б —
только для личного использования.
"""
import base64, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent
SRC, VENDOR, FONTS, DIST = ROOT / 'src', ROOT / 'vendor', ROOT / 'fonts', ROOT / 'dist'


def b64(path):
    return base64.b64encode(path.read_bytes()).decode('ascii')


def build(gost=None):
    app = (SRC / 'app.html').read_text(encoding='utf-8')
    jspdf = (VENDOR / 'jspdf.umd.min.js').read_text(encoding='utf-8')
    if '</script' in jspdf.lower():
        sys.exit('vendor/jspdf.umd.min.js содержит </script — встраивание невозможно')
    parts = {
        '/*@@JSPDF@@*/': '/* jsPDF 2.5.2 (MIT), встроен для автономной работы */\n' + jspdf,
        '/*@@FONTFB@@*/': b64(VENDOR / 'DejaVuSansCondensed.ttf'),
        '/*@@FONTB@@*/': b64(gost) if gost else '',
    }
    for key, val in parts.items():
        if app.count(key) != 1:
            sys.exit(f'Метка {key} должна встречаться в src/app.html ровно один раз')
        app = app.replace(key, val)
    return app


def version():
    m = re.search(r"const APP_VER = '([\d.]+)'", (SRC / 'app.html').read_text(encoding='utf-8'))
    if not m:
        sys.exit('APP_VER не найден в src/app.html')
    return m.group(1)


def main():
    ver, public = version(), build()
    if '--check' in sys.argv:
        current = (ROOT / 'index.html').read_text(encoding='utf-8') if (ROOT / 'index.html').exists() else ''
        if current != public:
            sys.exit('index.html устарел: выполните python build.py и закоммитьте результат')
        print(f'index.html актуален (версия {ver})')
        return
    (ROOT / 'index.html').write_text(public, encoding='utf-8')
    DIST.mkdir(exist_ok=True)
    out = [ROOT / 'index.html', DIST / f'rkd_pcb_checklist_v{ver}.html']
    out[1].write_text(public, encoding='utf-8')
    gost = FONTS / 'GOST_B.ttf'
    if gost.exists():
        out.append(DIST / f'rkd_pcb_checklist_v{ver}_gost.html')
        out[2].write_text(build(gost), encoding='utf-8')
    for p in out:
        print(f'{p.relative_to(ROOT)}  {p.stat().st_size / 1048576:.2f} МБ')


if __name__ == '__main__':
    main()
