"""c4 · Comparació C: prova de banda. Mapes MSB per canal (R, G, B) amb els factors per canal de zp_canal, a la zona només Vixen.
Encàrrec «comparacions», 11-10-2026.

Predeclarat (abans de mirar cap quocient):
  - canals natius de la càmera del compost: u_cam = A·u (msb_comu.canals_camera; exacte i lineal per píxel);
  - cel per canal amb la MATEIXA regla que el mapa (p1_cel_i_massa_aire.py): submostreig 4×, màscares d'estrelles (del verd),
    fantasma, protuberàncies i franja; (a) constant = mediana a r > 7,29 R☉; (b, adoptat) + pla ajustat al residu del perfil
    azimutal a r > 3,546 R☉. Prova: el verd ha de reproduir mapa/CEL.json;
  - MSB_c = fac_c·(c_cam − S_c)·E, amb E de k = 0,40 per als tres canals (al quocient s'anul·la gairebé del tot);
    fac_R = 2,633e-11 (interp), fac_G = 2,7714e-11, fac_B = 8,306e-11 (zp_canal/ZP_CANAL.json; el blau, NO UTILITZABLE);
  - zona: wv ≥ 0,99 (Vixen pura), 1,15 ≤ r < 1,90 R☉, cap bit de franja lunar, buit del limbe, sense dada, protuberància, fantasma;
  - anells 1,15–1,25 · 1,25–1,40 · 1,40–1,70 · 1,70–1,90 R☉; sectors de 10°;
  - per sector: q_s = mediana(MSB_R)/mediana(MSB_G); per anell: mediana dels q_s, IC amb bootstrap per sectors (blocs de 10°);
  - predicció per a dispersió de Thomson de llum solar: 1,00;
  - MSB_orange = 0,5·MSB_G + 0,5·MSB_R (pesos predeclarats); sistemàtica de banda amb w de 0,25 a 0,75.
La incertesa dels punts zero (bootstrap de zp_canal, post hoc) es dona a part: domina el resultat.
Escriu comparacions/banda/."""
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage as nd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cmp_comu as cc   # noqa: E402

mc = cc.mc
T0 = time.time()
OUT = cc.RES / 'banda'; OUT.mkdir(parents=True, exist_ok=True)
ZPJ = json.load(open(mc.RES / 'zp_canal/ZP_CANAL.json'))
SENS = json.load(open(mc.RES / 'zp_canal/SENSIBILITAT_ZP.json'))
FAC = {c: float(ZPJ['canals'][c]['fac']) for c in 'RGB'}
assert abs(FAC['G'] - mc.FAC_G) / mc.FAC_G < 1e-12
cau = mc.obre_cau()
F = cau['fusion_total_v42']; sup = cau['support_v42']; WV = cau['weight_vixen_v42']
g = mc.geo_llenc()
CANAL = {'R': 0, 'G': 1, 'B': 2}

# ---------------------------------------------------------------- 1. cel per canal (mateixa regla que p1)
s = 4
f = np.asarray(F[::s, ::s], np.float64)
sp = np.asarray(sup[::s, ::s])
yy, xx = np.mgrid[0:mc.H:s, 0:mc.W:s].astype(np.float64)
r, pa = g.polar(xx, yy)
u = (xx - mc.SOL_XY[0]) / mc.RSOL_PX; v = (yy - mc.SOL_XY[1]) / mc.RSOL_PX
dada = sp & np.all(np.isfinite(f), 2) & np.all(f > 0, 2)
CAM = mc.canals_camera(f)
del f
G = np.where(dada, CAM[..., 1], np.nan)
ghost = np.hypot(xx - mc.GHOST_XY[0], yy - mc.GHOST_XY[1]) < mc.GHOST_R_PX
Gf = np.where(dada, G, 0.0)
medf = nd.median_filter(Gf, size=9)
res = np.where(dada, G - medf, np.nan)
zona_soroll = dada & (r > 3.0) & ~ghost
sd = 1.4826 * np.nanmedian(np.abs(res[zona_soroll] - np.nanmedian(res[zona_soroll])))
est = nd.binary_dilation(dada & (r > 2.0) & (res > 6 * sd), iterations=2)
prom = np.zeros_like(dada)
for p0, dpa in mc.PROM_SECTORS:
    prom |= (np.abs((pa - p0 + 180) % 360 - 180) <= dpa) & (r < mc.PROM_RMAX)
valid = dada & ~ghost & ~est & ~prom & (np.hypot(xx - mc.LLUNA_XY[0], yy - mc.LLUNA_XY[1]) >= mc.R_BANDA_PX)
del res, medf, Gf
K76 = 959.0 / mc.RSOL_ARCSEC
r76 = r / K76
edges = np.arange(1.0, 13.0, 0.02)
kb = np.digitize(r76, edges) - 1
CEL = {}
for c, j in CANAL.items():
    X = np.where(dada, CAM[..., j], np.nan)
    c0 = float(np.median(X[valid & (r > 7.2 * K76)]))
    okb = valid & (kb >= 0) & (kb < len(edges) - 1)
    med = np.asarray(nd.median(X[okb], labels=kb[okb], index=np.arange(len(edges) - 1)), float)
    cnt = np.bincount(kb[okb], minlength=len(edges) - 1)[:len(edges) - 1]
    med[cnt < 30] = np.nan
    rc = 0.5 * (edges[1:] + edges[:-1]); okm = np.isfinite(med)
    base = np.interp(r76, rc[okm], med[okm])
    fb = valid & (r76 > 3.5)
    cb, *_ = np.linalg.lstsq(np.c_[np.ones(fb.sum()), u[fb], v[fb]], (X - base)[fb], rcond=None)
    CEL[c] = dict(c0=c0, gu=float(cb[1]), gv=float(cb[2]))
celmap = mc.coef_cel()
prova_cel_G = dict(c0=(CEL['G']['c0'], celmap['b']['c0']), gu=(CEL['G']['gu'], celmap['b']['gu']), gv=(CEL['G']['gv'], celmap['b']['gv']),
                   reprodueix=bool(np.allclose([CEL['G']['c0'], CEL['G']['gu'], CEL['G']['gv']],
                                               [celmap['b']['c0'], celmap['b']['gu'], celmap['b']['gv']], rtol=1e-9, atol=1e-9)))
print('cel per canal (ADU/s):', CEL, '\nprova verd contra CEL.json:', prova_cel_G, flush=True)
del CAM, G, r, pa, u, v, xx, yy, dada, valid, r76, kb

# ---------------------------------------------------------------- 2. mapes per canal a la zona Vixen (resolució plena)
RM = 1.95
ya, yb = int(mc.SOL_XY[1] - RM * 1.01 * mc.RSOL_PX), int(mc.SOL_XY[1] + RM * 1.01 * mc.RSOL_PX) + 1
xa, xb = int(mc.SOL_XY[0] - RM * 1.01 * mc.RSOL_PX), int(mc.SOL_XY[0] + RM * 1.01 * mc.RSOL_PX) + 1
Fz = np.asarray(F[ya:yb, xa:xb], np.float64)
wv = np.asarray(WV[ya:yb, xa:xb], np.float64)
fl = np.load(cc.PLE / 'flags_ple.npy', mmap_mode='r')[ya:yb, xa:xb]
yy = np.arange(ya, yb, dtype=np.float64)[:, None] * np.ones((1, xb - xa)); xx = np.ones((yb - ya, 1)) * np.arange(xa, xb, dtype=np.float64)[None, :]
r, pa = g.polar(xx, yy)
MA = mc.MassaAire()
E = mc.factor_extincio(mc.kasten_young(MA.altura_bloc(ya, yb, xa, xb)), MA.X_sol)
CAM = mc.canals_camera(Fz)
uu = (xx - mc.SOL_XY[0]) / mc.RSOL_PX; vv = (yy - mc.SOL_XY[1]) / mc.RSOL_PX
MSB = {}; MSBa = {}
for c, j in CANAL.items():
    S = CEL[c]['c0'] + CEL[c]['gu'] * uu + CEL[c]['gv'] * vv
    MSB[c] = FAC[c] * (CAM[..., j] - S) * E
    MSBa[c] = FAC[c] * (CAM[..., j] - CEL[c]['c0']) * E          # cel (a): només la constant
fracc_cel = {c: None for c in CANAL}
zona = ((np.asarray(fl) & cc.TOCA) == 0) & (wv >= mc.WV_SONY) & (r >= 1.15) & (r < 1.90) & np.all(np.isfinite(Fz), 2) & np.all(Fz > 0, 2)
for c, j in CANAL.items():
    zona &= np.isfinite(MSB[c])
# prova: el verd d'aquí és el del mapa (mateix píxel)
msb_map = np.load(cc.PLE / 'msb_ple.npy', mmap_mode='r')[ya:yb, xa:xb]
dif = np.abs(MSB['G'][zona] / np.asarray(msb_map)[zona] - 1)
prova_verd_mapa = dict(max_dif_relativa=float(np.nanmax(dif)), p99=float(np.nanpercentile(dif, 99)))
print('prova verd = mapa:', prova_verd_mapa, flush=True)
for c, j in CANAL.items():
    S = CEL[c]['c0'] + CEL[c]['gu'] * uu + CEL[c]['gv'] * vv
    fracc_cel[c] = {f'{a}-{b}': float(np.median((S / CAM[..., j])[zona & (r >= a) & (r < b)])) for a, b in ((1.15, 1.25), (1.7, 1.9))}

ANB = [(1.15, 1.25), (1.25, 1.40), (1.40, 1.70), (1.70, 1.90)]
key = np.full(r.shape, -1, np.int64)
for i, (a, b) in enumerate(ANB):
    m = zona & (r >= a) & (r < b)
    key[m] = i * 36 + (np.floor(pa[m] / 10).astype(np.int64) % 36)
ng = len(ANB) * 36
med = {}; meda = {}
for c in CANAL:
    n, q = cc.percentils_grup(key.ravel(), MSB[c].ravel(), ng); med[c] = q[50].reshape(len(ANB), 36)
    _, q = cc.percentils_grup(key.ravel(), MSBa[c].ravel(), ng); meda[c] = q[50].reshape(len(ANB), 36)
npx = n.reshape(len(ANB), 36)
_, qpx = cc.percentils_grup(key.ravel(), (MSB['R'] / MSB['G']).ravel(), ng); qpx = qpx[50].reshape(len(ANB), 36)

bootf = SENS['r6']['bootstrap_conjunt']['F_sol_R_sobre_G']                  # F☉R/F☉G (bootstrap per estrelles, post hoc)
rel_fac = FAC['R'] / FAC['G']                                              # = F☉G/F☉R adoptat
fac_ratio_boot = {k: 1.0 / bootf[k] for k in ('p16', 'p50', 'p84', 'p2_5', 'p97_5')}


def anell_stats(num, den, min_px=200, nboot=2000, llavor=11):
    out = []
    rng = np.random.default_rng(llavor)
    for i in range(len(ANB)):
        ok = (npx[i] >= min_px) & np.isfinite(num[i]) & np.isfinite(den[i]) & (den[i] > 0)
        qs = num[i][ok] / den[i][ok]
        if ok.sum() < 6:
            out.append(dict(anell=list(ANB[i]), sectors=int(ok.sum()))); continue
        bs = [np.median(rng.choice(qs, qs.size)) for _ in range(nboot)]
        out.append(dict(anell=list(ANB[i]), sectors=int(ok.sum()), mediana=float(np.median(qs)),
                        ic68=[float(np.percentile(bs, 16)), float(np.percentile(bs, 84))], ic95=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
                        dispersio_entre_sectors=float(1.4826 * np.median(np.abs(qs - np.median(qs)))),
                        min=float(qs.min()), max=float(qs.max())))
    return out


RG = anell_stats(med['R'], med['G']); BG = anell_stats(med['B'], med['G']); RGa = anell_stats(meda['R'], meda['G']); BGa = anell_stats(meda['B'], meda['G'])
RGpx = []
for i in range(len(ANB)):
    ok = (npx[i] >= 200) & np.isfinite(qpx[i])
    RGpx.append(dict(anell=list(ANB[i]), mediana_dels_sectors_del_quocient_per_pixel=float(np.median(qpx[i][ok]))))
orange = []
for d in RG:
    if 'mediana' not in d:
        continue
    q = d['mediana']
    orange.append(dict(anell=d['anell'], q_R_G=q, MSB_orange_sobre_MSB_G=0.5 * (1 + q), diferencia_percent=50 * (q - 1),
                       sistematica_banda_w_025_075_percent=25 * abs(q - 1),
                       amb_bootstrap_ZP_p50=0.5 * (1 + q * fac_ratio_boot['p50'] / rel_fac),
                       amb_bootstrap_ZP_68=[0.5 * (1 + q * fac_ratio_boot['p84'] / rel_fac), 0.5 * (1 + q * fac_ratio_boot['p16'] / rel_fac)]))
with open(OUT / 'quocients_per_sector.csv', 'w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['r_in', 'r_out', 'pa_from', 'pa_to', 'n_px', 'MSB_R', 'MSB_G', 'MSB_B', 'R_over_G', 'B_over_G', 'R_over_G_skyA'])
    for i, (a, b) in enumerate(ANB):
        for k in range(36):
            w.writerow([a, b, k * 10, k * 10 + 10, int(npx[i, k]), f"{med['R'][i, k]:.5e}", f"{med['G'][i, k]:.5e}", f"{med['B'][i, k]:.5e}",
                        f"{med['R'][i, k] / med['G'][i, k]:.4f}", f"{med['B'][i, k] / med['G'][i, k]:.4f}", f"{meda['R'][i, k] / meda['G'][i, k]:.4f}"])
entr = {cc.rel(cc.PLE / 'flags_ple.npy'): cc.sha256(cc.PLE / 'flags_ple.npy'), cc.rel(cc.PLE / 'msb_ple.npy'): cc.sha256(cc.PLE / 'msb_ple.npy'),
        cc.rel(mc.RES / 'zp_canal/ZP_CANAL.json'): cc.sha256(mc.RES / 'zp_canal/ZP_CANAL.json'),
        cc.rel(mc.RES / 'zp_canal/SENSIBILITAT_ZP.json'): cc.sha256(mc.RES / 'zp_canal/SENSIBILITAT_ZP.json'),
        'fusion_total_v42.npy (Paperera)': mc.SHA_CAU['fusion_total_v42.npy'] + ' (B3_V42_FROZEN; verificat pel mapa)',
        'support_v42.npy': mc.SHA_CAU['support_v42.npy'], 'weight_vixen_v42.npy': mc.SHA_CAU['weight_vixen_v42.npy']}
json.dump(dict(guio=cc.rel(__file__), data=time.strftime('%Y-%m-%dT%H:%M:%S'), factors=FAC, fac_R_sobre_fac_G=rel_fac,
               fac_R_sobre_fac_G_bootstrap=fac_ratio_boot, cel_per_canal_adu=CEL, prova_cel_verd=prova_cel_G, prova_verd_mapa=prova_verd_mapa,
               fraccio_cel_del_total=fracc_cel, anells=ANB,
               R_sobre_G=RG, B_sobre_G_NO_UTILITZABLE=BG, R_sobre_G_cel_constant=RGa, B_sobre_G_cel_constant=BGa, R_sobre_G_per_pixel=RGpx,
               R_sobre_G_amb_bootstrap_ZP={d['anell'][0]: dict(adoptat=d.get('mediana'),
                                                              p50=d.get('mediana', np.nan) * fac_ratio_boot['p50'] / rel_fac,
                                                              ic68=[d.get('mediana', np.nan) * fac_ratio_boot['p84'] / rel_fac,
                                                                    d.get('mediana', np.nan) * fac_ratio_boot['p16'] / rel_fac],
                                                              ic95=[d.get('mediana', np.nan) * fac_ratio_boot['p97_5'] / rel_fac,
                                                                    d.get('mediana', np.nan) * fac_ratio_boot['p2_5'] / rel_fac]) for d in RG},
               orange=orange, prediccio_thomson=1.0,
               avisos=['El blau no és utilitzable (zp_canal): es dona només per completesa.',
                       'Els factors per canal són per a píxels sense flat; el compost porta flat per canal. La diferència de normalització del flat '
                       'entre R i G al lloc del Sol NO s\'ha mesurat (també val per al verd, acceptat a ±10 %).',
                       'E igual per als tres canals (k = 0,40): el quocient no depèn de l\'extinció diferencial entre canals, que no es coneix.'],
               entrades_sha256=entr, segons=round(time.time() - T0, 1)),
          open(OUT / 'BANDA.json', 'w'), indent=1, ensure_ascii=False, default=float)
print('R/G:', json.dumps(RG, indent=0)); print('B/G:', json.dumps(BG, indent=0)); print('R/G cel a:', json.dumps(RGa, indent=0))
print('orange:', json.dumps(orange, indent=0)); print('fracció de cel:', fracc_cel)
print(f'fet ({time.time() - T0:.0f} s)')
