"""vn2 (V108 · verificador de «negres») · Anàlisi del RÀSTER de la 41 (i la 42) sense compondre res:
  · reproducció: el CEL_TER_Q regenerat a regen/ ha de ser bit a bit el de l'agent; V107_Q regenerat = filtres_v103;
  · descomposició del canvi: Δ_CEL = CEL_Q − V107 (el cel fora del numerador) i Δ_TER = CEL_TER_Q − CEL_Q (el terra);
  · zona del limbe (< 40 px de la Lluna de presentació) i control nul (1,3–2 R☉; i sectors sense zones negres);
  · energia per escales (DoG) i contrast plomall/buit (p90 − p10 i part positiva/negativa del pas alt 2–64 px) de u, per bandes;
  · anells: rms de la mitjana per anell (1 px) de Δ passada per un pas alt radial; línies/costures: vista de Δ del llenç sencer.
Sortida: 4-RESULTATS/v108_20260926/verifica_negres/VN2.json i vistes/*.png"""
import sys, json
from pathlib import Path
import numpy as np, cv2
from scipy.ndimage import gaussian_filter1d
R0 = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(R0 / '3-RECERCA/tools/v97_refundacio_20260924'))
from jutge_comu import W, H, SOL, RSOL, LLUNA, RLLUNA, MARC
OUT = R0 / '4-RESULTATS/v108_20260926/verifica_negres'; VIS = OUT / 'vistes'; VIS.mkdir(parents=True, exist_ok=True)
ORIG = R0 / '4-RESULTATS/v103_banda_20260926/E/filtres_v103/filtres'
AG = R0 / '4-RESULTATS/v108_20260926/negres/candidats/CEL_TER_Q'; RG = OUT / 'regen'
res = {}
def ld(p): return np.load(p).astype(np.float32) / 65535
# reproducció
for tag in ('P01_NRGF', 'P01_NRGF_extrap'):
    res[f'repro_{tag}'] = dict(CEL_TER_Q_regen_igual_agent=bool(np.array_equal(np.load(AG / f'{tag}_u16.npy'), np.load(RG / 'CEL_TER_Q' / f'{tag}_u16.npy'))),
                               V107_regen_igual_filtres_v103=bool(np.array_equal(np.load(ORIG / f'{tag}_u16.npy'), np.load(RG / 'V107_Q' / f'{tag}_u16.npy'))),
                               alfa_igual=bool(np.array_equal(np.load(ORIG / f'{tag}_alfa_u16.npy'), np.load(AG / f'{tag}_alfa_u16.npy'))))
print(json.dumps(res), flush=True)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
r = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL; th = np.degrees(np.arctan2(-(yy - SOL[1]), xx - SOL[0])) % 360
dlimb = np.hypot(xx - LLUNA[0], yy - LLUNA[1]) - RLLUNA; del xx, yy
alfa = np.load(ORIG / 'P01_NRGF_alfa_u16.npy') > 0
BANDES = [(1.02, 1.3), (1.3, 2), (2, 3), (3, 4.5), (4.5, 7), (7, 9)]
u0 = ld(ORIG / 'P01_NRGF_u16.npy'); u1 = ld(AG / 'P01_NRGF_u16.npy'); uc = ld(RG / 'CEL_Q' / 'P01_NRGF_u16.npy')
dC = uc - u0; dT = u1 - uc; dA = u1 - u0
m40 = alfa & (dlimb < 40)
res['limbe_<40px'] = dict(px=int(m40.sum()), max_abs_dA=float(np.abs(dA[m40]).max()), max_abs_dC=float(np.abs(dC[m40]).max()), max_abs_dT=float(np.abs(dT[m40]).max()))
tb = {}
for a, b in BANDES:
    m = alfa & (r >= a) & (r < b) & (dlimb >= 40)
    tb[f'{a:g}-{b:g}'] = dict(mitj_dA=float(dA[m].mean()), mitj_abs_dA=float(np.abs(dA[m]).mean()), p99_abs_dA=float(np.percentile(np.abs(dA[m]), 99)),
                              mitj_dC=float(dC[m].mean()), mitj_abs_dC=float(np.abs(dC[m]).mean()), mitj_dT=float(dT[m].mean()),
                              frac_TER_actiu=float((dT[m] > 1 / 512).mean()), sd_u0=float(u0[m].std()), sd_u1=float(u1[m].std()))
res['per_bandes'] = tb
# control nul: sectors de baix (225–315°) a 1,3–3 R☉, on no hi ha zones negres
m = alfa & (r >= 1.3) & (r < 3) & (th >= 225) & (th < 315) & (dlimb >= 40)
res['control_nul_baix_1.3-3'] = dict(mitj_abs_dA=float(np.abs(dA[m]).mean()), p99=float(np.percentile(np.abs(dA[m]), 99)), mitj_dA=float(dA[m].mean()))
# on actua el terra: sobre quins valors de u0 (quantils per banda)
for a, b in ((2, 3), (3, 4.5)):
    m = alfa & (r >= a) & (r < b) & (dlimb >= 40); q = np.percentile(uc[m], [5, 10, 25, 50, 75, 90])
    act = dT[m] > 1 / 512
    res[f'terra_{a:g}-{b:g}'] = dict(quantils_u_CEL=[float(v) for v in q], u_CEL_mitjana_on_actua=float(uc[m][act].mean()) if act.any() else None,
                                     frac_del_decil_fosc_aixecat=float((dT[m][uc[m] <= q[1]] > 1 / 512).mean()),
                                     frac_del_quartil_clar_tocat=float((np.abs(dT[m][uc[m] >= q[4]]) > 1 / 512).mean()),
                                     aixecament_mitja_decil_fosc=float(dT[m][uc[m] <= q[1]].mean()))
# energia per escales i contrast plomall/buit del ràster (dins del marc, fora del limbe)
def dog(a, s1, s2): return (a if s1 == 0 else cv2.GaussianBlur(a, (0, 0), s1)) - cv2.GaussianBlur(a, (0, 0), s2)
x0, y0, x1, y1 = MARC; sl = (slice(y0, y1), slice(x0, x1))
en = {}
for nom, (s1, s2) in {'1-2': (0.7, 2), '2-8': (2, 8), '8-32': (8, 32), '32-128': (32, 128), 'pa_2-64': (2, 64)}.items():
    D = {k: dog(np.ascontiguousarray(v[sl]), s1, s2) for k, v in (('V107', u0), ('CEL_Q', uc), ('CEL_TER_Q', u1))}
    rr = r[sl]; mm = alfa[sl] & (dlimb[sl] >= 60); e = {}
    for a, b in BANDES[1:5]:
        k = mm & (rr >= a) & (rr < b); e0 = float(np.sqrt(np.mean(D['V107'][k] ** 2)))
        d = dict(CEL_Q=float(np.sqrt(np.mean(D['CEL_Q'][k] ** 2)) / e0), CEL_TER_Q=float(np.sqrt(np.mean(D['CEL_TER_Q'][k] ** 2)) / e0),
                 corr_CTQ_V107=float(np.corrcoef(D['CEL_TER_Q'][k], D['V107'][k])[0, 1]))
        if nom == 'pa_2-64':
            for kk in ('V107', 'CEL_Q', 'CEL_TER_Q'):
                v = D[kk][k]; d[f'{kk}_p90-p10'] = float(np.percentile(v, 90) - np.percentile(v, 10))
                d[f'{kk}_mitj_pos'] = float(v[v > 0].mean()); d[f'{kk}_mitj_neg'] = float(v[v < 0].mean())
            v0 = D['V107'][k]; v1 = D['CEL_TER_Q'][k]
            pos, neg = v0 > np.percentile(v0, 80), v0 < np.percentile(v0, 20)
            d['pendent_plomalls(p80+)'] = float(np.polyfit(v0[pos], v1[pos], 1)[0]); d['pendent_buits(p20-)'] = float(np.polyfit(v0[neg], v1[neg], 1)[0])
        e[f'{a:g}-{b:g}'] = d
    en[nom] = e; del D
res['energia_i_contrast_raster_41'] = en
# anells: mitjana per anell d'1 px de Δ, pas alt radial (treu la tendència de > 8 px) → rms
ri = np.floor(r * RSOL).astype(np.int32); mk = alfa & (dlimb >= 40)
for nom, d_ in (('dA', dA), ('dC', dC), ('dT', dT), ('u0', u0), ('u1', u1)):
    c = np.bincount(ri[mk], minlength=ri.max() + 1); s = np.bincount(ri[mk], d_[mk], minlength=ri.max() + 1); mu = s / np.maximum(c, 1)
    hp = mu - gaussian_filter1d(mu, 8); res.setdefault('anells_rms_pas_alt_radial', {})[nom] = {f'{a:g}-{b:g}': float(np.sqrt(np.mean(hp[int(a * RSOL):int(b * RSOL)] ** 2))) for a, b in ((1.3, 3), (3, 4.5), (4.5, 7))}
# perfil azimutal de Δ_T a 3 i 4 R☉ (costures de sector?): potència per sobre de 3° vs total
for rr_ in (2.5, 3.0, 3.5, 4.0):
    n = 3600; t = np.radians(np.arange(n) / 10); X = (SOL[0] + rr_ * RSOL * np.cos(t)).astype(np.float32); Y = (SOL[1] - rr_ * RSOL * np.sin(t)).astype(np.float32)
    for nom, d_ in (('dT', dT), ('dC', dC)):
        p = cv2.remap(d_, X[None], Y[None], cv2.INTER_LINEAR)[0]
        hp = p - gaussian_filter1d(p, 30, mode='wrap')      # < 3°
        res.setdefault('azimutal', {}).setdefault(nom, {})[f'{rr_:g}'] = {'rms_total': float(p.std()), 'rms_menys_de_3graus': float(hp.std())}
# vistes del llenç sencer (1/4): Δ_CEL i Δ_TER
for nom, d_ in (('dCEL', dC), ('dTER', dT), ('dTOTAL', dA)):
    s = cv2.resize(d_, (W // 4, H // 4), interpolation=cv2.INTER_AREA); v = np.clip(128 + s * 1200, 0, 255).astype(np.uint8)
    cv2.imwrite(str(VIS / f'VN2_{nom}_llenc_sencer_x1200.png'), v)
(OUT / 'VN2.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n'); print(json.dumps(res, ensure_ascii=False, indent=1))
