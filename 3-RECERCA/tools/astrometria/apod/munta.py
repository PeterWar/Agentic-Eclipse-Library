#!/usr/bin/env python3
"""Munta APOD_submission.html («Stars Beside an Eclipsed Sun»).

Plantilla: apod.tpl.html, al costat d'aquest script (font escrita a mà, 33,8 KB).
Figures:   figA.svg / figB.svg de comu.work("apod") (les fa figures.py); si no hi
           són, es fan servir les còpies del rescat que hi ha al costat de l'script.
Imatges:   imgs.json de comu.work("apod") (el fa munta_video.sh: JPEG 2400 px,
           mp4 i poster en data-URI base64).
Sortida:   comu.work("apod")/apod.html i la còpia comu.apod()/APOD_submission.html.

Abans (16-08) tot era relatiu al cwd del scratchpad 604fa71e; el contingut
generat és el mateix.
"""
import json
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu  # noqa: E402

AQUI = Path(__file__).resolve().parent
W = comu.work("apod")


def svg(nom):
    p = W / nom
    if not p.exists():
        print(f"  {nom}: no és a {W}; agafo la còpia del rescat de {AQUI}")
        p = AQUI / nom
    return open(p, encoding='utf-8').read()


h = open(AQUI / 'apod.tpl.html', encoding='utf-8').read()
figs = {'__FIG_A__': svg('figA.svg'),
        '__FIG_B__': svg('figB.svg')}
for k, v in figs.items():
    assert k in h, k
    h = h.replace(k, v)
# tot el text no-ASCII a entitats numeriques: immune a qualsevol charset
h = ''.join(c if ord(c) < 128 else f'&#{ord(c)};' for c in h)
u = json.load(open(W / 'imgs.json'))
for k, v in (('__VIXEN_NET__', u['vixen_net']), ('__VIXEN_MARK__', u['vixen_mark']),
             ('__SONY_NET__', u['sony_net']), ('__SONY_MARK__', u['sony_mark']),
             ('__VIDEO__', u['video']), ('__POSTER__', u['poster'])):
    assert k in h, k
    h = h.replace(k, v)
sortida = W / 'apod.html'
open(sortida, 'w', encoding='utf-8').write(h)
final = comu.apod() / 'APOD_submission.html'
shutil.copyfile(sortida, final)
print(f'{sortida} {os.path.getsize(sortida)/1024/1024:.2f} MB · '
      f'placeholders: {re.findall(r"__[A-Z_]+__", h)}\n→ {final}')
