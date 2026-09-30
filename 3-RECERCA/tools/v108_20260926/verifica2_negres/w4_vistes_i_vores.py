"""w4 (V108 · verifica2_negres) · Vistes PRÒPIES del llenç sencer (pas 2 → 1/2) del compost emulat (w0): V107 i candidat estirats igual,
pas alt 6–64 px de ln L (±2 %) de tots dos i ln(cand/V107) (±3 %); i mesures de VORES: (a) salt de Δln L a la vora del domini dins del marc
(banda 0–150 px de la vora de la base contra 150–400 px), (b) anells: rms de la mitjana azimutal del pas alt radial (0,02–0,2 R☉) de ln L,
V107 contra candidat, per bandes. Ús: w4_vistes_i_vores.py [carpeta_candidat]"""
import sys, json
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent))
from w0_comu import *
CAND = Path(sys.argv[1]) if len(sys.argv) > 1 else R0 / '4-RESULTATS/v108_20260926/negres_v2/candidats_v4/CEL_G_MAX_T_e30_W_H0'
NOM = CAND.name; PAS = 2; V = OUT / 'vistes'
G = geo(pas=PAS); r, th, ok, marc, dl = G['r'], G['th'], G['ok'], G['marc'], G['dl']
L0 = np.load(OUT / 'L_V107_w0_pas2.npy'); L1 = np.load(OUT / f'L_{NOM}_w0_pas2.npy'); l0 = np.log(np.maximum(L0, 1e-3)); l1 = np.log(np.maximum(L1, 1e-3))
res = {}
# (a) vora del domini: distància a la vora de la base (sense erosió)
b = ((alfa(3, (0, 0, W, H), PAS) > 0.5) & (ras(3, (0, 0, W, H), PAS).max(-1) > 1e-3)).astype(np.uint8); dv = cv2.distanceTransform(b, cv2.DIST_L2, 5) * PAS
d = l1 - l0; vo = {}
for lloc, mm in {'dins_marc': marc, 'tot': np.ones_like(marc)}.items():
    for a_, b_ in ((0, 40), (40, 150), (150, 400), (400, 1000)):
        k = mm & (b > 0) & (dv >= a_) & (dv < b_) & (r > 4)
        if k.sum() > 100: vo.setdefault(lloc, {})[f'{a_}-{b_}px'] = dict(n=int(k.sum()), dlnL_p50=float(np.median(d[k])), dlnL_p5_p95=[float(np.percentile(d[k], 5)), float(np.percentile(d[k], 95))])
res['vora_domini'] = vo
# (b) anells: mitjana azimutal (bins de 1 px del llenç) del pas alt radial
ri = (r * RSOL).astype(int); m = ok & marc; an = {}
for nom, l in (('V107', l0), ('cand', l1)):
    hpv = l - cv2.GaussianBlur(l, (0, 0), 40)
    s = np.bincount(ri[m], hpv[m], minlength=ri.max() + 1); n = np.bincount(ri[m], minlength=ri.max() + 1); prof = s / np.maximum(n, 1)
    from scipy.ndimage import gaussian_filter1d
    hpr = prof - gaussian_filter1d(prof, 30)
    for a_, b_ in ((1.3, 2), (2, 3), (3, 4.5), (4.5, 7), (7, 9)):
        k = (np.arange(len(prof)) >= a_ * RSOL) & (np.arange(len(prof)) < b_ * RSOL) & (n > 500)
        an.setdefault(f'{a_:g}-{b_:g}', {})[nom] = float(np.sqrt(np.mean(hpr[k] ** 2)))
res['anells_rms_perfil_azimutal_hp'] = an
(OUT / f'W4_{NOM}.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
# vistes
fons = b > 0
def estira(L):
    x = np.log(np.maximum(L, 1e-3)); lo, hi = np.percentile(x[ok & marc & (r > 2)], [0.5, 99.5]); g = np.clip((x - lo) / (hi - lo), 0, 1) ** 0.8
    g = (g * 255).astype(np.uint8); g[~fons] = 0; return g
def lohi(L): x = np.log(np.maximum(L, 1e-3)); return np.percentile(x[ok & marc & (r > 2)], [0.5, 99.5])
lo, hi = lohi(L0)
def estira_fix(L):
    x = np.log(np.maximum(L, 1e-3)); g = (np.clip((x - lo) / (hi - lo), 0, 1) ** 0.8 * 255).astype(np.uint8); g[~fons] = 0; return g
def colors(x, lim):
    t = np.clip(x / lim, -1, 1); o = np.zeros(x.shape + (3,), np.uint8)
    o[..., 2] = (255 * np.where(t > 0, 1, 1 + t)).astype(np.uint8); o[..., 0] = (255 * np.where(t < 0, 1, 1 - t)).astype(np.uint8); o[..., 1] = (255 * (1 - np.abs(t))).astype(np.uint8)
    o[~fons] = 60; return o
def gr(g): return cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)
def hpv(l): return l - cv2.GaussianBlur(l, (0, 0), 32) - (l - cv2.GaussianBlur(l, (0, 0), 3))
def marca(img):
    o = img.copy(); cv2.rectangle(o, (MARC[0] // PAS, MARC[1] // PAS), (MARC[2] // PAS, MARC[3] // PAS), (0, 200, 255), 3)
    for rr in (2, 3, 4.5, 7): cv2.circle(o, (int(SOL[0] / PAS), int(SOL[1] / PAS)), int(rr * RSOL / PAS), (0, 160, 0), 1)
    return o
P = {'a_V107_estirada': gr(estira_fix(L0)), 'b_cand_estirada_mateixa_corba': gr(estira_fix(L1)),
     'c_V107_pasalt_6-64px_pm2pc': marca(colors(hpv(l0), 0.02)), 'd_cand_pasalt_6-64px_pm2pc': marca(colors(hpv(l1), 0.02)),
     'e_ln_cand_sobre_V107_pm3pc': marca(colors(l1 - l0, 0.03)), 'f_pasalt_de_la_diferencia_6-64px_pm1pc': marca(colors(hpv(l1) - hpv(l0), 0.01))}
for k, img in P.items():
    cv2.imwrite(str(V / f'W4_{NOM}_{k}.jpg'), img, [cv2.IMWRITE_JPEG_QUALITY, 92])
print(json.dumps(res, indent=1))
