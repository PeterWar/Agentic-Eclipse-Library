"""m5 (V108 · final) · Contrast plomall/buit («flamarada») al compost FUSIONAT del Photoshop, V107 contra V108, SENSE el gradient del cel: per a cada anell
(0,1 R☉ d'ample) es treu de ln L la seva tendència suau al llarg de l'arc (harmònics m ≤ 3, que és on viu el gradient dalt/baix que el CEL treu a propòsit) i es mesura
p90 − p10 del que queda (els plomalls i els buits). També per sectors de 90°. Només lectura. Sortida: v108_final/M5_FLAMARADA_FUSIONAT.json"""
import sys, json, struct
from pathlib import Path
import numpy as np, cv2
R0 = Path(__file__).resolve().parents[4]
SOL = (5361.768, 3775.748); RS = 440.603
def fusionat(p):
    with open(p, 'rb') as f:
        hdr = f.read(26); nch = struct.unpack('>H', hdr[12:14])[0]; h, w = struct.unpack('>II', hdr[14:22])
        n = struct.unpack('>I', f.read(4))[0]; f.seek(n, 1); n = struct.unpack('>I', f.read(4))[0]; f.seek(n, 1); n = struct.unpack('>Q', f.read(8))[0]; f.seek(n, 1)
        pos = f.tell(); assert struct.unpack('>H', f.read(2))[0] == 0
    mm = np.memmap(p, dtype='>u2', mode='r', offset=pos + 2, shape=(nch, h, w))
    return np.stack([np.asarray(mm[c], np.float32) / 65535 for c in range(3)], -1)
nth = 3600; th = np.linspace(0, 2 * np.pi, nth, endpoint=False)
radis = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5]
def perfils(C):
    L = (C[..., 0] + 2 * C[..., 1] + C[..., 2]) / 4; out = {}
    for rr in radis:
        rs = RS * (rr + np.linspace(-0.05, 0.05, 9))[:, None]
        X = (SOL[0] + rs * np.cos(th)[None, :]).astype(np.float32); Y = (SOL[1] - rs * np.sin(th)[None, :]).astype(np.float32)
        v = cv2.remap(L, X, Y, cv2.INTER_LINEAR, borderValue=0).mean(0); out[rr] = v
    return out
def treu_harm(v, mmax=3):
    ok = v > 1e-3; lv = np.log(np.maximum(v, 1e-4)); A = np.stack([np.ones(nth)] + [f(k * th) for k in range(1, mmax + 1) for f in (np.cos, np.sin)], 1)
    c, *_ = np.linalg.lstsq(A[ok], lv[ok], rcond=None); return np.where(ok, lv - A @ c, np.nan), ok
P7 = perfils(fusionat(R0 / '1-PHOTOSHOP/V107.psb')); P8 = perfils(fusionat(R0 / '1-PHOTOSHOP/V108.psb'))
rep = {'global': {}, 'sectors_90': {}, 'correlacio_perfils': {}}
degs = np.degrees(th)
for rr in radis:
    d7, ok7 = treu_harm(P7[rr]); d8, ok8 = treu_harm(P8[rr]); ok = ok7 & ok8 & np.isfinite(d7) & np.isfinite(d8)
    sp = lambda d, m: float(np.diff(np.nanpercentile(d[m], [10, 90]))[0])
    rep['global'][str(rr)] = round(sp(d8, ok) / sp(d7, ok), 3)
    rep['correlacio_perfils'][str(rr)] = round(float(np.corrcoef(d7[ok], d8[ok])[0, 1]), 3)
    rep['sectors_90'][str(rr)] = {f'{a}-{a+90}': round(sp(d8, ok & (degs >= a) & (degs < a + 90)) / sp(d7, ok & (degs >= a) & (degs < a + 90)), 3) for a in (0, 90, 180, 270) if (ok & (degs >= a) & (degs < a + 90)).sum() > 200}
O = R0 / '4-RESULTATS/v108_20260926/v108_final/M5_FLAMARADA_FUSIONAT.json'; O.write_text(json.dumps(rep, ensure_ascii=False, indent=1)); print(json.dumps(rep, ensure_ascii=False, indent=1))
