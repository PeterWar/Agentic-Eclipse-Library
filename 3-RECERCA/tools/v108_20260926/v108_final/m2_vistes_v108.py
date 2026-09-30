"""m2 (V108 · v108_final) · Vistes del LLENÇ SENCER (mai retalls) dels composts PLE de m0 (pila de la V107 sense capes d'ajust), amb la MATEIXA
corba global per canal de les rondes de les zones negres (negres/vistes/corba_emulat_a_fusionat.npy; la Claredat local no s'hi reprodueix: la
comparació és justa perquè la corba és la mateixa per a tots). Làmines a 1/4 (2638 × 1877 per panell); llenços nets a 1/2.
  1 · LAMINA_V107_V108.jpg: dalt V107 | V108 | ln(V108/V107) ±0,15 (vermell = més clar, blau = més fosc); baix: zones negres de la V107 | de la
      V108 (vermell = negra amb les dues referències de cel, taronja = només A 6,5–8,5 R☉, groc = només B 5–5,6 R☉ dins del marc) | el mateix ±0,03.
  2 · MAPA_ZONES_NEGRES.jpg: el canvi de les zones negres amb la VARA FIXA (el cel de la V107) i amb el cel de cada versió: vermell = negra a la V107
      i ja no a la V108 (curada), porpra = negra a totes dues (queda), groc = nova a la V108.
  3 · COMBINACIO.jpg: ln(F/V107) | ln(N/V107) | ln(V108/V107) (±0,05) | interacció I = Δ_V108 − Δ_F − Δ_N (±0,005).
  4 · ESTIRADA_V107_V108.jpg: estirament fort (ln L entre ln 0,12 i ln 0,30) per veure el cel i la corona feble, i ln(V108/V107) ±5 % i ±15 %.
  (Gris a les diferències: fora de la dada, estrelles de la 202 i cantonada del logo.)
  + V107_llenc_sencer.png, V108_llenc_sencer.png i DIFERENCIA_V108_V107.png (a 1/2).
Ús: m2_vistes_v108.py   (després de m0 i de m1 Z i C)   Sortida: 4-RESULTATS/v108_20260926/v108_final/vistes/"""
import sys, json
from pathlib import Path
import numpy as np, cv2
R0 = Path(__file__).resolve().parents[4]
V8R = R0 / '4-RESULTATS/v108_20260926'; OUT = V8R / 'v108_final'; CO = OUT / 'composts'; VI = OUT / 'vistes'; VI.mkdir(exist_ok=True)
sys.path.insert(0, str(R0 / '3-RECERCA/tools/v108_20260926/negres'))
from comu_negres import W, H, SOL, RSOL, MARC, mascares   # noqa: E402
G2 = mascares((0, 0, W, H), 2); ok2 = G2['ok']
T = np.load(V8R / 'negres/vistes/corba_emulat_a_fusionat.npy'); XT = np.linspace(0, 1, T.shape[1])
def corba(C): return np.stack([np.interp(C[..., c], XT, T[c]) for c in range(3)], -1)
def a8(C): return (np.clip(C, 0, 1) * 255 + 0.5).astype(np.uint8)
def red(a): return cv2.resize(a, (a.shape[1] // 2, a.shape[0] // 2), interpolation=cv2.INTER_AREA)
def etiqueta(img, text):
    out = img.copy(); cv2.rectangle(out, (0, 0), (out.shape[1], 50), (0, 0, 0), -1)
    cv2.putText(out, text, (14, 35), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA); return out
def dif(dl, lim, valid=None):
    valid = VAL if valid is None else valid
    t = np.clip(dl / lim, -1, 1); d = np.zeros(dl.shape + (3,), np.float32)
    d[..., 0] = np.where(t > 0, 255, 255 * (1 + t)); d[..., 2] = np.where(t < 0, 255, 255 * (1 - t)); d[..., 1] = 255 * (1 - np.abs(t))
    d[~valid] = 40; return d.astype(np.uint8)
def guies(g):
    for rs in (1.3, 2.0, 3.0, 4.5): cv2.circle(g, (int(SOL[0] / 2), int(SOL[1] / 2)), int(rs * RSOL / 2), (80, 200, 255), 2)
    x0, y0, x1, y1 = [v // 2 for v in MARC]; cv2.rectangle(g, (x0, y0), (x1, y1), (255, 255, 255), 2); return g
def desa(nom, img, q=90): cv2.imwrite(str(VI / nom), cv2.cvtColor(img, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, q] if nom.endswith('.jpg') else [])
RGB = {p: np.asarray(np.load(CO / f'RGB2_{p}.npy', mmap_mode='r'), np.float32) for p in ('V107', 'V108')}
L2 = {p: np.ascontiguousarray(np.load(CO / f'L_{p}.npy', mmap_mode='r')[::2, ::2]) for p in ('V107', 'V108', 'F', 'N')}
V = {p: a8(corba(RGB[p])) for p in RGB}; del RGB
VAL = ok2 & (L2['V107'] > 2e-3) & (L2['V108'] > 2e-3)   # fora de la dada (cantonades sense base), gris
Z = np.load(OUT / 'ZONES_NEGRES_pas2.npz'); forma = tuple(Z['forma']); n = forma[0] * forma[1]
def zm(p, k): return np.unpackbits(Z[f'{p}__{k}'])[:n].reshape(forma).astype(bool)
rep = {}
# ---- 1 · làmina V107 | V108 | diferència, zones negres
dl = np.log(np.maximum(L2['V108'], 1e-3)) - np.log(np.maximum(L2['V107'], 1e-3))
def mapa(p, gris):
    nA, nB = zm(p, 'A'), zm(p, 'B'); g = np.repeat(gris[..., None], 3, 2).astype(np.float32) * 0.8
    g[nA & nB] = [235, 30, 30]; g[nA & ~nB] = [255, 150, 0]; g[nB & ~nA] = [250, 230, 0]; return guies(g.astype(np.uint8))
m7 = mapa('V107', cv2.cvtColor(V['V107'], cv2.COLOR_RGB2GRAY)); m8 = mapa('V108', cv2.cvtColor(V['V108'], cv2.COLOR_RGB2GRAY))
Z1 = json.loads((OUT / 'M1_Z_ZONES_NEGRES.json').read_text())['a1']
tA = {p: 100 * Z1[p]['A_cel_6.5-8.5']['total'] for p in ('V107', 'V108')}; tB = {p: 100 * Z1[p]['B_cel_5-5.6_marc']['total'] for p in ('V107', 'V108')}
f1 = np.concatenate([etiqueta(red(V['V107']), 'V107 (emulada, corba global)'), etiqueta(red(V['V108']), 'V108 = flat 2D v5 + genoll (mateixa corba)'),
                     etiqueta(red(dif(dl, 0.15)), 'ln(V108/V107)  vermell = mes clar, blau = mes fosc, +-0,15')], 1)
f2 = np.concatenate([etiqueta(red(m7), f'V107 zones negres: A {tA["V107"]:.1f} %  B {tB["V107"]:.1f} %'), etiqueta(red(m8), f'V108 zones negres: A {tA["V108"]:.1f} %  B {tB["V108"]:.1f} %'),
                     etiqueta(red(dif(dl, 0.03)), 'ln(V108/V107), +-0,03')], 1)
desa('LAMINA_V107_V108.jpg', np.concatenate([f1, f2], 0))
desa('V107_llenc_sencer.png', V['V107']); desa('V108_llenc_sencer.png', V['V108']); desa('DIFERENCIA_V108_V107.png', dif(dl, 0.15))
# ---- 2 · mapa del canvi de les zones negres (vara fixa i cel propi)
def canvi(k7, k8, gris):
    a, b = zm('V107', k7), zm('V108', k8); g = np.repeat(gris[..., None], 3, 2).astype(np.float32) * 0.7
    g[a & ~b] = [235, 30, 30]; g[a & b] = [150, 40, 200]; g[b & ~a] = [250, 230, 0]
    return guies(g.astype(np.uint8)), 100 * float((a & ~b).sum() / max(a.sum(), 1)), int(a.sum()), int(b.sum()), int((b & ~a).sum())
gris = cv2.cvtColor(V['V108'], cv2.COLOR_RGB2GRAY); panells = []
for k7, k8, et in (('A', 'Afix', 'cel A (6,5-8,5 R_sol), vara fixa de la V107'), ('B', 'Bfix', 'cel B (5-5,6 R_sol, marc), vara fixa de la V107'),
                   ('A', 'A', 'cel A, el de cada versio'), ('B', 'B', 'cel B, el de cada versio')):
    im, fc, na, nb, nn = canvi(k7, k8, gris); rep[f'{k7}_{k8}'] = dict(pc_curades=fc, px_V107=na, px_V108=nb, px_noves=nn)
    panells.append(etiqueta(red(im), f'{et}: vermell curada {fc:.0f} %, porpra queda, groc nova ({nn} px)'))
desa('MAPA_ZONES_NEGRES.jpg', np.concatenate([np.concatenate(panells[:2], 1), np.concatenate(panells[2:], 1)], 0))
# ---- 3 · la combinació
I = np.load(CO / 'I_interaccio_pas2.npy'); lv = np.log(np.maximum(L2['V107'], 1e-3))
dF = np.log(np.maximum(L2['F'], 1e-3)) - lv; dN = np.log(np.maximum(L2['N'], 1e-3)) - lv
c = [etiqueta(red(dif(dF, 0.05)), 'flat 2D v5 sol: ln(F/V107), +-0,05'), etiqueta(red(dif(dN, 0.05)), 'genoll sol (negres_v2): ln(N/V107), +-0,05'),
     etiqueta(red(dif(dl, 0.05)), 'V108: ln(V108/V107), +-0,05'), etiqueta(red(dif(I, 0.005)), 'interaccio: V108 - F - N (en ln), +-0,005')]
desa('COMBINACIO.jpg', np.concatenate([np.concatenate(c[:2], 1), np.concatenate(c[2:], 1)], 0))
rep['interaccio_pas2_max_abs'] = float(np.abs(I).max()); rep['interaccio_pas2_p99_9_abs'] = float(np.percentile(np.abs(I[ok2]), 99.9))
# ---- 4 · estirada
H2, W2 = L2['V107'].shape; dalt = []
for p, et in (('V107', 'V107 (ln L de 0,12 a 0,30)'), ('V108', 'V108 (ln L de 0,12 a 0,30)')):
    v = np.clip((np.log(np.maximum(L2[p], 1e-3)) - np.log(0.12)) / (np.log(0.30) - np.log(0.12)), 0, 1)
    im = np.repeat(cv2.resize((v * 255).astype(np.uint8), (W2 // 2, H2 // 2), interpolation=cv2.INTER_AREA)[..., None], 3, 2); dalt.append(etiqueta(im, et))
d = red(dif(dl, 0.05)); cv2.rectangle(d, (int(MARC[0] / 4), int(MARC[1] / 4)), (int(MARC[2] / 4), int(MARC[3] / 4)), (0, 200, 255), 2)
for rs in (3, 4.5, 5.5, 7): cv2.circle(d, (int(SOL[0] / 4), int(SOL[1] / 4)), int(rs * RSOL / 4), (0, 160, 0), 1)
d2 = red(dif(dl, 0.15)); cv2.rectangle(d2, (int(MARC[0] / 4), int(MARC[1] / 4)), (int(MARC[2] / 4), int(MARC[3] / 4)), (0, 200, 255), 2)
desa('ESTIRADA_V107_V108.jpg', np.concatenate([np.concatenate(dalt, 1), np.concatenate([etiqueta(d, 'ln(V108/V107), +-5 %; cercles 3 / 4,5 / 5,5 / 7 R_sol'), etiqueta(d2, 'ln(V108/V107), +-15 %')], 1)], 0))
(OUT / 'M2_VISTES.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1) + '\n'); print('FET', json.dumps(rep))
