"""p1 (V109 · perles a la cadena) · Control (= V107) contra v108 (= V108), ETAPA PER ETAPA, a la zona de les perles de Baily
(limbe esquerre, PA 155–190° al voltant de la Lluna, just per sobre de la protuberància gran) i a la resta del limbe.

Etapes (totes de només lectura):
  LF      fotogrames de la caixa lunar (numerator; el weight i el distance_model són iguals): control = v98/cadena_raw/limb_frames_comuna,
          v108 = v108/flat2d_v5/limb_frames_flat2d (a9b amb el flat 2D). Per fotograma: quocient num_v108/num_control (= 1/C del flat 2D
          a la posició del sensor) a les perles, i la seva estructura; i si la perla hi és saturada (weight = 0).
  FONTS   fonts de la fusió (base_G, fusion_starless, vixen_starless): cadena_v98/d4 contra flat2d_v5/fusio/d4.
  FRANJA  a3d congelada (v108/franja_a3d contra control/franja) i p1 fràgils (v108/franja contra v108/franja_a3d): G, E, E_banda, E_net.
  LINEAL  linealitzada (base_G, fusion_starless, vixen_starless).
  BASE    f2b (base_v108_u16) i f2c (base_v108_final_u16).
  FILTRES els 16 ràsters de filtres_std (E1 41–44, E6 45–46, E4 47–49, E3 50–53, E2 54–56), el ganxo NRGF 41/42 (filtres_alt) i els muntats.
  ESTAT   L{id}_G de l'estat (r3 + REC de la 56 amb c0) i L3_RGB.
  COMPOST C1 (base + 10 filtres visibles, màscares de la V107), PLE (+ 305, 306, 258, 76, 224, 267, fins a la 239 exclosa) i FUSIONAT
          (el que desa el Photoshop, amb les capes d'ajust 239–244).

Mesures per etapa, zona (PERLES, RESTA del limbe) i banda de distància al limbe lunar d (px):
  dl_rms / dl_mitjana: rms i mitjana de ln(v108/control) (dades lineals i composts) o de (v108 − control)/65535 (ràsters u16 dels filtres, en %).
  per escala DoG (0,7–2, 1–4, 2–8 px): E_ctl, E_v108 (rms del detall), quocient, i β = Σ ΔD·D_ctl / Σ D_ctl² (la part del detall del control
  que la v108 treu (β < 0) o hi afegeix (β > 0)); la resta del canvi és ortogonal (textura nova o treta que no és el detall de la perla).
Per perla (17 pics de G de la franja del control a PA 155–190°, d 0–10 px, G > 10⁶): valor al pic (3 × 3), energia DoG 0,7–2 en un disc de
4 px i β local, a cada etapa.
Sortida: 4-RESULTATS/v109_perles_20260927/perles_cadena/P1_ETAPES.json (+ P1_PERLES.json amb la llista de perles i els perfils)."""
import sys, json, time
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent))
from comu_perles import R0, OUT, V8, CTL, V108, PSB7, PSB8, LLUNA, RLLUNA, fusionat, lum  # noqa: E402
from scipy.signal import find_peaks  # noqa: E402
cv2.setNumThreads(6)
T0 = time.time()
BX = (4677, 3077, 6077, 4477)                         # caixa lunar (x0, y0, x1, y1) = la de la franja i dels fotogrames
x0, y0, x1, y1 = BX
yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
D = np.hypot(xx - LLUNA[0], yy - LLUNA[1]) - RLLUNA
PA = np.degrees(np.arctan2(-(yy - LLUNA[1]), xx - LLUNA[0])) % 360
del yy, xx
BANDES = ((-5, 0), (0, 3), (3, 6), (6, 10), (10, 20), (20, 40), (40, 80))
ESC = ((0.7, 2.0), (1.0, 4.0), (2.0, 8.0))
ZPER = (PA >= 155) & (PA < 190); ZONES = dict(PERLES=ZPER, RESTA=~ZPER)
RING = (D >= -5) & (D < 80)


def ng(l, m, s):
    return cv2.GaussianBlur(l * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)


def detall(x, m, s1, s2):
    return ng(x, m, s1) - ng(x, m, s2)


# ------------------------------------------------------------------ les perles: pics de G de la franja del control
fb = np.load(CTL / 'franja/A3C_franja_silueta.npz'); G7 = fb['G'].astype(np.float32)
th = np.radians(np.arange(150, 205, 0.02)); dd = np.arange(-4, 15, 0.25)
XP = (LLUNA[0] - x0 + np.cos(th)[None, :] * (RLLUNA + dd[:, None])).astype(np.float32)
YP = (LLUNA[1] - y0 - np.sin(th)[None, :] * (RLLUNA + dd[:, None])).astype(np.float32)
PG = cv2.remap(G7, XP, YP, cv2.INTER_LINEAR); kk = (dd >= 0) & (dd <= 10)
pg = PG[kk].max(0); dg = dd[kk][PG[kk].argmax(0)]; pa_ = np.degrees(th)
pk, _ = find_peaks(np.log(np.maximum(pg, 1)), prominence=0.15, distance=15)
PERLES = []
for i in pk:
    if not (155 <= pa_[i] < 190 and pg[i] > 1e6): continue
    xp = LLUNA[0] + np.cos(th[i]) * (RLLUNA + dg[i]); yp = LLUNA[1] - np.sin(th[i]) * (RLLUNA + dg[i])
    # el píxel més brillant de G a ±1 px
    ix, iy = int(round(xp)) - x0, int(round(yp)) - y0; w = G7[iy - 1:iy + 2, ix - 1:ix + 2]; j = np.unravel_index(np.argmax(w), w.shape)
    PERLES.append(dict(id=len(PERLES) + 1, PA=round(float(pa_[i]), 2), d=round(float(dg[i]), 2), x=int(ix + j[1] - 1 + x0), y=int(iy + j[0] - 1 + y0), G_franja=float(pg[i])))
print('perles', len(PERLES), [(p['PA'], p['x'], p['y']) for p in PERLES], flush=True)
yyb, xxb = np.mgrid[-4:5, -4:5]; DISC = (xxb ** 2 + yyb ** 2) <= 16


def mesura(a, b, tipus, valid=None):
    """a (control), b (v108): arrays 2D de la caixa. tipus 'ln' (dades lineals o composts: ln) o 'u16' (ràsters dels filtres: x/65535)."""
    a = np.asarray(a, np.float32); b = np.asarray(b, np.float32)
    if tipus == 'ln':
        m = (np.isfinite(a) & np.isfinite(b) & (a > 0) & (b > 0))
        if valid is not None: m &= valid
        la = np.where(m, np.log(np.maximum(a, 1e-12)), 0).astype(np.float32); lb = np.where(m, np.log(np.maximum(b, 1e-12)), 0).astype(np.float32)
        dl = lb - la; fac = 1.0
    else:
        m = np.ones(a.shape, bool) if valid is None else valid.copy()
        la = (a / 65535).astype(np.float32); lb = (b / 65535).astype(np.float32); dl = lb - la; fac = 100.0
    mf = m.astype(np.float32); res = {'identic': bool(np.array_equal(a, b)), 'n_dif': int((a != b).sum())}
    if res['identic']:
        return res
    DA = {s: detall(la, mf, *s) for s in ESC}; DB = {s: detall(lb, mf, *s) for s in ESC}
    for zn, Z in ZONES.items():
        o = {}
        for bd in BANDES:
            k = Z & m & (D >= bd[0]) & (D < bd[1])
            if k.sum() < 30: continue
            x = dl[k]; e = dict(n=int(k.sum()), dl_rms=round(fac * float(np.sqrt(np.mean(x.astype(np.float64) ** 2))), 5), dl_mitjana=round(fac * float(x.mean()), 5))
            for s in ESC:
                da = DA[s][k].astype(np.float64); db = DB[s][k].astype(np.float64); ea = np.sqrt(np.mean(da ** 2)); eb = np.sqrt(np.mean(db ** 2))
                beta = float(((db - da) * da).sum() / max((da * da).sum(), 1e-30)); orto = (db - da) - beta * da
                e[f'{s[0]:g}-{s[1]:g}'] = dict(E_ctl=float(ea), quocient=round(float(eb / max(ea, 1e-30)), 4), beta=round(beta, 4),
                                                orto_rel=round(float(np.sqrt(np.mean(orto ** 2)) / max(ea, 1e-30)), 4))
            o[f'{bd[0]}..{bd[1]}'] = e
        res[zn] = o
    pp = []
    for p in PERLES:
        cx, cy = p['x'] - x0, p['y'] - y0; sl = (slice(cy - 4, cy + 5), slice(cx - 4, cx + 5)); mm = DISC & m[sl]
        s = ESC[0]; da = DA[s][sl][mm].astype(np.float64); db = DB[s][sl][mm].astype(np.float64)
        v = dict(id=p['id'], pic=round(fac * float(np.mean(dl[cy - 1:cy + 2, cx - 1:cx + 2])), 5),
                 E_q=round(float(np.sqrt((db ** 2).sum() / max((da ** 2).sum(), 1e-30))), 4),
                 beta=round(float(((db - da) * da).sum() / max((da * da).sum(), 1e-30)), 4))
        if tipus == 'ln': v['pic_ctl'] = float(np.exp(np.mean(la[cy - 1:cy + 2, cx - 1:cx + 2])))
        else: v['pic_ctl'] = float(np.mean(a[cy - 1:cy + 2, cx - 1:cx + 2]))
        pp.append(v)
    res['perles'] = pp
    res['perles_resum'] = dict(pic_mediana=round(float(np.median([v['pic'] for v in pp])), 5), pic_min=round(float(min(v['pic'] for v in pp)), 5),
                               pic_max=round(float(max(v['pic'] for v in pp)), 5), E_q_mediana=round(float(np.median([v['E_q'] for v in pp])), 4),
                               E_q_min=round(float(min(v['E_q'] for v in pp)), 4), beta_mediana=round(float(np.median([v['beta'] for v in pp])), 4))
    return res


def cropc(path, c=None, key=None):
    if key is not None:
        a = np.load(path)[key]; a = a if c is None else a[..., c]; return np.asarray(a, np.float32)
    a = np.load(path, mmap_mode='r')[y0:y1, x0:x1]
    return np.asarray(a if c is None else a[..., c], np.float32)


R = {'perles': PERLES, 'bandes_px': BANDES, 'escales_DoG': ESC, 'caixa': BX}
def fa(nom, a, b, tipus='ln', valid=None):
    t = time.time(); R[nom] = mesura(a, b, tipus, valid)
    r = R[nom]; s = 'IDÈNTIC' if r['identic'] else f"perles: pic {r['perles_resum']['pic_mediana']} E_q {r['perles_resum']['E_q_mediana']} β {r['perles_resum']['beta_mediana']}"
    print(f'{nom:34s} {s}  ({time.time() - t:.1f} s)', flush=True)


# ------------------------------------------------------------------ LF: fotogrames de la caixa lunar
LFA = R0 / '4-RESULTATS/v98_20260925/cadena_raw/limb_frames_comuna'; LFB = V8 / 'flat2d_v5/limb_frames_flat2d'
na = np.load(LFA / 'numerator.npy', mmap_mode='r'); nb = np.load(LFB / 'numerator.npy', mmap_mode='r'); wt = np.load(LFA / 'weight.npy', mmap_mode='r')
meta = json.loads((LFA / 'METADATA.json').read_text())['frames']
lf = []; sumA = np.zeros((1400, 1400), np.float64); sumB = np.zeros((1400, 1400), np.float64); sumW = np.zeros((1400, 1400), np.float64)
for i in range(na.shape[0]):
    a = np.asarray(na[i, ..., 1], np.float32); b = np.asarray(nb[i, ..., 1], np.float32); w = np.asarray(wt[i, ..., 1], np.float32)
    ok = (w > 0) & (a > 0) & (b > 0); rq = np.where(ok, np.log(np.maximum(b, 1e-12) / np.maximum(a, 1e-12)), 0)
    kz = ok & ZPER & (D >= 0) & (D < 10)
    per = []
    for p in PERLES:
        cx, cy = p['x'] - x0, p['y'] - y0
        per.append(dict(id=p['id'], w=float(w[cy, cx]), lnq=round(float(rq[cy, cx]), 5) if ok[cy, cx] else None))
    lf.append(dict(i=i, nom=meta[i]['name'], t=meta[i]['time'], exp=meta[i]['exposure'], n_zona=int(kz.sum()),
                   lnq_zona_rms=round(float(np.sqrt(np.mean(rq[kz] ** 2))), 5) if kz.any() else None,
                   lnq_zona_mitjana=round(float(rq[kz].mean()), 5) if kz.any() else None,
                   perles_saturades_o_sense_pes=sum(1 for v in per if v['w'] <= 0), perles=per))
    sumA += np.where(w > 0, a, 0); sumB += np.where(w > 0, b, 0); sumW += w
R['LF_per_fotograma'] = lf
fa('LF_suma_G (Σnum, pes>0)', sumA, sumB, valid=sumW > 0)
del sumA, sumB, sumW

# ------------------------------------------------------------------ FONTS, FRANJA, LINEAL
FA = R0 / '4-RESULTATS/v98_20260925/cadena_v98/d4/products/sources'; FB = V8 / 'flat2d_v5/fusio/d4/products/sources'
fa('FONTS base_G', cropc(FA / 'base_G.npy'), cropc(FB / 'base_G.npy'))
fa('FONTS fusion_starless G', cropc(FA / 'fusion_starless.npy', 1), cropc(FB / 'fusion_starless.npy', 1))
fa('FONTS vixen_starless G', cropc(FA / 'vixen_starless.npy', 1), cropc(FB / 'vixen_starless.npy', 1))
FRC = CTL / 'franja/A3C_franja_silueta.npz'; FRA = V108 / 'franja_a3d/A3C_franja_silueta.npz'; FRV = V108 / 'franja/A3C_franja_silueta.npz'
for k, c in (('G', None), ('E', 1), ('E_net', 1), ('E_banda', 1), ('F', 1), ('V', None)):
    fa(f'FRANJA a3d {k}', cropc(FRC, c, k), cropc(FRA, c, k))
    fa(f'FRANJA p1 {k}', cropc(FRA, c, k), cropc(FRV, c, k))
fa('FRANJA total G (control → v108)', cropc(FRC, None, 'G'), cropc(FRV, None, 'G'))
for f, c in (('base_G', None), ('fusion_starless', 1), ('vixen_starless', 1)):
    fa(f'LINEAL {f}', cropc(CTL / f'lineal/{f}.npy', c), cropc(V108 / f'lineal/{f}.npy', c))

# ------------------------------------------------------------------ BASE
for f in ('base_v108_u16', 'base_v108_final_u16'):
    for c, cn in ((0, 'R'), (1, 'G'), (2, 'B')):
        fa(f'BASE {f} {cn}', cropc(CTL / f'base/{f}.npy', c), cropc(V108 / f'base/{f}.npy', c), 'u16')

# ------------------------------------------------------------------ FILTRES, ESTAT
TAG = {41: 'P01_NRGF', 42: 'P01_NRGF_extrap', 43: 'P02_RHEF', 44: 'P02b_RHEF_ups0.35', 45: 'P02c_RHEF_local60_native', 46: 'P02d_RHEF_local30_native',
       47: '03', 48: '03v30', 49: '07', 50: '01', 51: '04', 52: '05', 53: '06', 54: 'P03_MGN', 55: 'P04_WOW', 56: 'P05_WOW_bilateral'}
ETAPA = {41: 'E1', 42: 'E1', 43: 'E1', 44: 'E1', 45: 'E6', 46: 'E6', 47: 'E4', 48: 'E4', 49: 'E4', 50: 'E3', 51: 'E3', 52: 'E3', 53: 'E3', 54: 'E2', 55: 'E2', 56: 'E2'}
ALT = V108 / 'filtres_alt/alt_41_42/CEL_G_MAX_T_e30_W_H0'
for lid, tg in TAG.items():
    a = cropc(CTL / f'filtres_std/filtres/{tg}_u16.npy'); b = cropc(V108 / f'filtres_std/filtres/{tg}_u16.npy')
    fa(f'FILTRE {lid} std {ETAPA[lid]}', a, b, 'u16')
    if lid in (41, 42):
        fa(f'FILTRE {lid} ganxo NRGF (std v108 → ganxo)', b, cropc(ALT / f'{tg}_u16.npy'), 'u16')
    fa(f'ESTAT L{lid}_G', cropc(CTL / f'estat_v108/L{lid}_G.npy'), cropc(V108 / f'estat_v108/L{lid}_G.npy'), 'u16')
for c, cn in ((0, 'R'), (1, 'G'), (2, 'B')):
    fa(f'ESTAT L3_RGB {cn}', cropc(CTL / 'estat_v108/L3_RGB.npy', c), cropc(V108 / 'estat_v108/L3_RGB.npy', c), 'u16')

# ------------------------------------------------------------------ COMPOSTS
CO = V8 / 'v108_final/composts'
fa('COMPOST C1 (base + 10 filtres)', cropc(CO / 'C1_V107.npy'), cropc(CO / 'C1_V108.npy'))
fa('COMPOST PLE (+ capes de Pere, sense ajust)', cropc(CO / 'L_V107.npy'), cropc(CO / 'L_V108.npy'))
fa('COMPOST FUSIONAT (Photoshop, amb ajust)', lum(fusionat(PSB7, BX)), lum(fusionat(PSB8, BX)))

(OUT / 'P1_ETAPES.json').write_text(json.dumps(R, ensure_ascii=False, indent=1, default=lambda x: x.item() if isinstance(x, np.generic) else str(x)) + '\n')
print('fet', round(time.time() - T0), 's')
