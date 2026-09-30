"""w2 (V94) · Treu el biaix COHERENT dels primers píxels de dada de les WOW noves (l'1–2 px de la vora de la dada sortia clar: 0,58–0,68 en
comptes de 0,5; es veia com una línia fina clara arran del limbe a 112° i 136°, c1). Per a cada píxel amb dada a d ≤ 30 px: calaix de d cada
0,25 px i d'azimut cada 0,5°; mitjana del ràster (només dada) per calaix, suavitzada al llarg de l'arc (gaussiana σ 5°, circular); es resta
(mitjana − 0,5) amb pes 1 fins a 20 px i fosa fins a 30 px. Exacte al píxel: cap interpolació entre píxels amb dada i sense dada.
És processament de la sortida del filtre (resta un component coherent), no hi posa res inventat. Sortida: sobreescriu wow/<tag>_u16.npy
(en guarda la versió w1 com a <tag>_u16_w1.npy) i W2_BIAIX.json."""
import sys, json, time, hashlib, shutil
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v94_20260924'; OUT = SORT / 'wow'
sys.path.insert(0, str(Path(__file__).parent)); from wow_domini import smoothstep
o = json.loads((ARREL / '.coordination/claim.lock/owner.json').read_text()); assert o.get('serial_writes') == 'HELD'
def sha(p):
    with open(p, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
Q = np.load(ARREL / '4-RESULTATS/v88_20260923/A3A_franja_un_instant.npz'); cx, cy, R = [float(v) for v in Q['centre']]
M = int(R + 40); bx0, bx1, by0, by1 = int(cx) - M, int(cx) + M, int(cy) - M, int(cy) + M
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = np.hypot(xx - cx, yy - cy) - R; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
DB, TB = 0.25, 0.5; zona = (d > -2) & (d <= 30); di = np.floor((d + 2) / DB).astype(int); ti = np.floor(th / TB).astype(int) % int(360 / TB); ND, NTB = int(32 / DB) + 2, int(360 / TB)
wgt = (1 - smoothstep(d, 20, 30)).astype(np.float32); rep = {}
for tag in ('P05_WOW_bilateral', 'P04_WOW'):
    src = OUT / f'{tag}_u16_w1.npy'
    if not src.exists(): shutil.copy2(OUT / f'{tag}_u16.npy', src)
    u = np.load(src); al = np.load(OUT / f'{tag}_alfa_u16.npy'); X = u[by0:by1, bx0:bx1].astype(np.float32) / 65535; V = (al[by0:by1, bx0:bx1] > 32767) & zona
    s = np.zeros((ND, NTB)); n = np.zeros((ND, NTB)); np.add.at(s, (di[V], ti[V]), X[V] - 0.5); np.add.at(n, (di[V], ti[V]), 1)
    sg = 5.0 / TB; num = gaussian_filter1d(s, sg, axis=1, mode='wrap'); den = gaussian_filter1d(n, sg, axis=1, mode='wrap'); biaix = np.where(den > 0.5, num / np.maximum(den, 1e-9), 0)
    corr = np.zeros_like(X); corr[V] = biaix[di[V], ti[V]] * wgt[V]; Xn = np.where(V, X - corr, X)
    out = u.copy(); out[by0:by1, bx0:bx1] = np.round(np.clip(Xn, 0, 1) * 65535).astype(np.uint16); out[al <= 32767] = 32768; np.save(OUT / f'{tag}_u16.npy', out)
    prof = {f'{a0}-{a1}': [round(float(Xn[V & (th >= a0) & (th < a1) & (np.abs(d - dd) < 0.25)].mean()), 3) if (V & (th >= a0) & (th < a1) & (np.abs(d - dd) < 0.25)).any() else None for dd in (0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0)] for a0, a1 in ((105, 120), (60, 90), (240, 280))}
    rep[tag] = dict(sha256=sha(OUT / f'{tag}_u16.npy'), correccio_max=round(float(np.abs(corr).max()), 4), perfil_despres=prof); print(tag, json.dumps(rep[tag]), flush=True)
(SORT / 'W2_BIAIX.json').write_text(json.dumps(rep, ensure_ascii=False, indent=2) + '\n')
