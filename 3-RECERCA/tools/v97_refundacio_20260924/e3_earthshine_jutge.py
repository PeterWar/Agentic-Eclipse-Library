"""e3 (V97) · L'Earthshine: combinació Vixen (e1) + Sony A (e2) al marc de la Lluna, i el jutge contra la V88 (capa 258).
Combinació: la Sony s'escala a la Vixen amb la mediana del quocient G al disc (d < −30 px); pesos inversos a la variància del soroll de cada apilat
(MAD del DoG σ0,7–2 al disc, d < −60 px). Res no es farceix: on un apilat no té dada, només compta l'altre; on cap en té, sense dada.
Jutge (el de research/126–127): correlació amb LROC (capa 62 de la V96, «Compara LROC · alineada V58»), per bandes (DoG en ln de la
lluminància), a l'interior del disc (d < −24 px, on la V88 és la 225 de Pere), i el soroll σ (DoG σ0,7–2) relatiu al senyal de banda.
S/N per banda ≈ r/√(1 − r²) (LROC no és fotomètric: serveix per comparar candidats entre ells, no com a valor absolut).
Porta de Codex: S/N ≥ 1,10 × V88 a les bandes on hi ha senyal (4–64 px); si no, es queda la V88. Ús: e3_earthshine_jutge.py <carpeta earthshine_v97>"""
import sys, json
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent))
from jutge_comu import ARREL, RES, LLUNA, RLLUNA, desa, corr
D = Path(sys.argv[1])
V = np.load(D / 'E1_earthshine_lineal.npz'); S = np.load(D / 'E2_sony_lluna.npz'); y0, y1, x0, x1 = [int(v) for v in V['box']]
assert [int(v) for v in S['box']] == [y0, y1, x0, x1]
yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32); d = np.hypot(xx - LLUNA[0], yy - LLUNA[1]) - RLLUNA
Ev, Wv = V['E'].astype(np.float32), V['W'].astype(np.float32); Es, Ws = S['E'].astype(np.float32), S['W'].astype(np.float32)
L = lambda E: (0.25 * E[..., 0] + 0.5 * E[..., 1] + 0.25 * E[..., 2]).astype(np.float32)
okv = Wv[..., 1] > 0; oks = Ws[..., 1] > 0; disc30 = (d < -30) & okv & oks
esc = float(np.median(Ev[..., 1][disc30] / np.maximum(Es[..., 1][disc30], 1e-12))); Es = Es * esc
def soroll(x, m): g = cv2.GaussianBlur(x, (0, 0), 0.7) - cv2.GaussianBlur(x, (0, 0), 2.0); v = g[m]; return float(1.4826 * np.median(np.abs(v - np.median(v))))
disc60 = (d < -60) & okv & oks; sv, ss_ = soroll(L(Ev), disc60), soroll(L(Es), disc60); wv, ws = 1 / sv ** 2, 1 / ss_ ** 2
Wc = wv * okv + ws * oks; Ec = np.where((Wc > 0)[..., None], (wv * okv[..., None] * Ev + ws * oks[..., None] * Es) / np.maximum(Wc, 1e-30)[..., None], 0).astype(np.float32)
# referències: V88 (258) i LROC (62), extretes de la V96
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917')); from psb69 import PSB
p = PSB(str(ARREL / '1-PHOTOSHOP/V96.psb'))
def capa(lid):
    return np.stack([p.channel_box(lid, c, (x0, y0, x1, y1)) for c in range(3)], -1).astype(np.float32) / 65535, p.channel_box(lid, -1, (x0, y0, x1, y1)).astype(np.float32) / 65535
E88, A88 = capa(258); LR, ALR = capa(62)
interior = (d < -24) & (A88 > 0.99) & (ALR > 0.5); zona_s = interior & okv & oks
bandes = [(2, 4), (4, 8), (8, 16), (16, 32), (32, 64)]
def per_bandes(img, m):
    lx = np.log(np.maximum(img, 1e-6)).astype(np.float32); lr = np.log(np.maximum(L(LR), 1e-6)).astype(np.float32); out = {}
    for a, b in bandes:
        da = cv2.GaussianBlur(lx, (0, 0), a) - cv2.GaussianBlur(lx, (0, 0), b); dr = cv2.GaussianBlur(lr, (0, 0), a) - cv2.GaussianBlur(lr, (0, 0), b)
        r = corr(da, dr, m); out[f'{a}-{b}'] = dict(r=r, sn=r / np.sqrt(max(1 - r * r, 1e-6)))
    return out
cands = {'V88 (258)': L(E88), 'Vixen (e1)': L(Ev), 'Sony A (e2)': L(Es), 'Vixen+Sony (1/σ²)': L(Ec)}
res = {k: per_bandes(v, zona_s) for k, v in cands.items()}
guany = {b: res['Vixen+Sony (1/σ²)'][b]['sn'] / max(res['V88 (258)'][b]['sn'], 1e-9) for b in [f'{a}-{c}' for a, c in bandes]}
porta = all(guany[b] >= 1.10 for b in ('4-8', '8-16', '16-32', '32-64'))
out = dict(escala_sony_a_vixen=esc, soroll_vixen=sv, soroll_sony=ss_, pes_relatiu_sony=ws / (wv + ws), px_zona=int(zona_s.sum()), resultats=res, guany_sn_combinat_sobre_V88=guany,
           porta_codex_1p10=porta, decisio='la combinació substitueix la V88' if porta else 'es queda la V88 (la combinació no arriba a ×1,10 a totes les bandes 4–64 px)')
np.savez_compressed(D / 'E3_combinat.npz', box=np.array([y0, y1, x0, x1]), E=Ec, W=Wc.astype(np.float32))
desa(D / 'E3_EARTHSHINE_JUTGE.json', out)
for k, v in res.items(): print(f'{k:20s}', ' '.join(f"{b}: r {x['r']:.3f}" for b, x in v.items()))
print('guany S/N combinat/V88:', {b: round(g, 2) for b, g in guany.items()}, '· pes Sony', round(ws / (wv + ws), 2), '·', out['decisio'])
