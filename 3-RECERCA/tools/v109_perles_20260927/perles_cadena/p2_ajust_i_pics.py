"""p2 (V109 · perles a la cadena) · D'on ve el canvi que SÍ hi ha a les perles al compost fusionat, i si la «pèrdua» de la mètrica de pics és real.

A · Les capes d'ajust (239–244). On el compost de sota (PLE, la pila ràster sense ajust, emulada amb els modes i màscares de la V107) és
    IDÈNTIC entre V107 i V108, qualsevol canvi al fusionat l'han fet les capes d'ajust, que no són operacions píxel a píxel (Claredat,
    Boira, Llum). Es mesura: (1) a les perles (d 0–6 px, PA 155–190°), (2) dins del disc lunar (d < −10 px, la llum cendrosa, que la cadena
    no toca), (3) a tot el llenç on ΔPLE = 0. I si el canvi és local o global: correlació del Δ fusionat (on ΔPLE = 0) amb ΔPLE suavitzat
    a σ = 3 … 300 px.
B · La mètrica de pics (m1 FP de la V108: 300 màxims de DoG σ1−σ4 del ln a 0–60 px del limbe; V108/V107 = 0,970 de mediana, p5 0,842).
    Nul de selecció: la mateixa mètrica amb els papers girats (pics triats a la V108, quocient V107/V108). Si només fos regressió a la
    mitjana, tots dos quocients sortirien < 1 igual; k = √(directe/invers) és l'atenuació real. Sobre C1, PLE i fusionat; amb la PA dels
    pics que més perden.
Sortida: 4-RESULTATS/v109_perles_20260927/perles_cadena/P2_AJUST_I_PICS.json. Només lectura de tota la resta."""
import sys, json, time
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent))
from comu_perles import OUT, V8, PSB7, PSB8, LLUNA, RLLUNA, W, H, fusionat, lum  # noqa: E402
cv2.setNumThreads(6)
T0 = time.time(); CO = V8 / 'v108_final/composts'
R = {}
# ------------------------------------------------------------------ A · capes d'ajust, a pas 1 a la caixa lunar ampliada i a pas 2 a tot el llenç
BX = (4477, 2877, 6277, 4677); x0, y0, x1, y1 = BX
yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32); D = np.hypot(xx - LLUNA[0], yy - LLUNA[1]) - RLLUNA
PA = np.degrees(np.arctan2(-(yy - LLUNA[1]), xx - LLUNA[0])) % 360; del yy, xx
F7 = lum(fusionat(PSB7, BX)); F8 = lum(fusionat(PSB8, BX))
P7 = np.asarray(np.load(CO / 'L_V107.npy', mmap_mode='r')[y0:y1, x0:x1], np.float32); P8 = np.asarray(np.load(CO / 'L_V108.npy', mmap_mode='r')[y0:y1, x0:x1], np.float32)
lf7, lf8 = np.log(np.maximum(F7, 1e-4)), np.log(np.maximum(F8, 1e-4)); dF = lf8 - lf7
dP = np.log(np.maximum(P8, 1e-6)) - np.log(np.maximum(P7, 1e-6)); igual = P7 == P8


def dog(a, s1, s2): return cv2.GaussianBlur(a, (0, 0), s1) - cv2.GaussianBlur(a, (0, 0), s2)


def zona(k, nom):
    o = dict(n=int(k.sum()), n_PLE_igual=int((k & igual).sum()), dF_mitjana=round(float(dF[k].mean()), 5), dF_rms=round(float(np.sqrt(np.mean(dF[k] ** 2))), 5),
             dPLE_rms=round(float(np.sqrt(np.mean(dP[k] ** 2))), 6))
    for s1, s2 in ((0.7, 2), (1, 4), (2, 8), (4, 16)):
        a = dog(lf7, s1, s2)[k].astype(np.float64); b = dog(lf8, s1, s2)[k].astype(np.float64)
        o[f'beta_{s1:g}-{s2:g}'] = round(float(((b - a) * a).sum() / (a * a).sum()), 4); o[f'quocient_E_{s1:g}-{s2:g}'] = round(float(np.sqrt((b * b).sum() / (a * a).sum())), 4)
    print('A', nom, o, flush=True); return o


ZP = (PA >= 155) & (PA < 190)
R['A_zones'] = {'perles_d0-6_PLE_igual': zona(ZP & (D >= 0) & (D < 6) & igual, 'perles 0-6'),
                'perles_d6-20': zona(ZP & (D >= 6) & (D < 20), 'perles 6-20'),
                'disc_lunar_d<-10 (cendrosa)': zona((D < -10) & igual, 'disc'),
                'limbe_resta_d0-6_PLE_igual': zona(~ZP & (D >= 0) & (D < 6) & igual, 'resta 0-6')}
# local o global: Δ fusionat on ΔPLE = 0 (a la caixa, fora del disc: d ≥ 0) contra ΔPLE suavitzat
k = igual & (D >= -10) & (D < 12)
cor = {}
for s in (3, 10, 30, 100, 300):
    g = cv2.GaussianBlur(dP.astype(np.float32), (0, 0), s)
    cor[str(s)] = round(float(np.corrcoef(dF[k], g[k])[0, 1]), 3)
R['A_local_o_global'] = dict(n=int(k.sum()), corr_dF_amb_dPLE_suavitzat=cor, dF_mitjana_disc=round(float(dF[(D < -10)].mean()), 5))
print('A local/global', R['A_local_o_global'], flush=True)
# a qui s'assembla la part local: al canvi del flat 2D sol (compost F de v108_final) o al del genoll sol (compost N), suavitzats
lF = np.log(np.maximum(np.asarray(np.load(CO / 'L_F.npy', mmap_mode='r')[y0:y1, x0:x1], np.float32), 1e-6)) - np.log(np.maximum(P7, 1e-6))
lN = np.log(np.maximum(np.asarray(np.load(CO / 'L_N.npy', mmap_mode='r')[y0:y1, x0:x1], np.float32), 1e-6)) - np.log(np.maximum(P7, 1e-6))
qui = {}
for s in (30, 100, 200):
    gF = cv2.GaussianBlur(lF.astype(np.float32), (0, 0), s)[k]; gN = cv2.GaussianBlur(lN.astype(np.float32), (0, 0), s)[k]
    A_ = np.stack([np.ones(k.sum()), gF, gN], 1); c_, *_ = np.linalg.lstsq(A_, dF[k], rcond=None); pr = A_ @ c_
    qui[str(s)] = dict(corr_flat2d=round(float(np.corrcoef(dF[k], gF)[0, 1]), 3), corr_genoll=round(float(np.corrcoef(dF[k], gN)[0, 1]), 3),
                       R2_tots_dos=round(float(1 - ((dF[k] - pr) ** 2).sum() / ((dF[k] - dF[k].mean()) ** 2).sum()), 3), terme_constant=round(float(c_[0]), 5))
R['A_flat2d_o_genoll'] = qui; print('A qui', qui, flush=True); del lF, lN
del F7, F8, P7, P8
# tot el llenç a pas 2: dF on ΔPLE = 0, per veure si és un canvi global (paràmetre de la capa d'ajust) o localitzat
PAS = 2


def fus2(p):
    import struct
    from comu_perles import _pos_image_data
    pos, nch, h, w = _pos_image_data(p); mm = np.memmap(p, dtype='>u2', mode='r', offset=pos, shape=(nch, h, w))
    C = np.stack([np.asarray(mm[c, ::PAS, ::PAS], np.float32) / 65535 for c in range(3)], -1); return lum(C)


G7, G8 = fus2(PSB7), fus2(PSB8)
Q7 = np.asarray(np.load(CO / 'L_V107.npy', mmap_mode='r')[::PAS, ::PAS], np.float32); Q8 = np.asarray(np.load(CO / 'L_V108.npy', mmap_mode='r')[::PAS, ::PAS], np.float32)
ig = (Q7 == Q8) & (Q7 > 1e-4); dG = np.log(np.maximum(G8, 1e-4)) - np.log(np.maximum(G7, 1e-4))
R['A_llenc_pas2'] = dict(frac_PLE_igual=round(float(ig.mean()), 4), dF_on_PLE_igual=dict(mitjana=round(float(dG[ig].mean()), 5), rms=round(float(np.sqrt(np.mean(dG[ig] ** 2))), 5),
                                                                                              p1_p99=np.percentile(dG[ig], [1, 99]).round(5).tolist()),
                         dF_on_PLE_canvia=dict(mitjana=round(float(dG[~ig].mean()), 5), rms=round(float(np.sqrt(np.mean(dG[~ig] ** 2))), 5)))
print('A llenç', R['A_llenc_pas2'], flush=True)
del G7, G8, Q7, Q8, dG, ig

# ------------------------------------------------------------------ B · la mètrica de pics, directa i girada
yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)


def lnm(img):
    m = (np.isfinite(img) & (img > 0)).astype(np.float32); return np.where(m > 0, np.log(np.maximum(img, 1e-12)), 0).astype(np.float32), m


def ng(l, m, s): return cv2.GaussianBlur(l * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)


def pics(A, B, nom):
    la, ma = lnm(A); lb, mb = lnm(B); m = ma * mb
    da = ng(la, m, 1) - ng(la, m, 4); db = ng(lb, m, 1) - ng(lb, m, 4); fr = (D >= 0) & (D < 60) & (m > 0)
    out = {}
    for sent, (x, y) in (('directe_V108_sobre_V107', (da, db)), ('invers_V107_sobre_V108', (db, da))):
        mx = cv2.dilate(x, np.ones((9, 9), np.uint8)); pk = fr & (x == mx) & (x > 0); ys, xs = np.nonzero(pk); o = np.argsort(-x[ys, xs])[:300]; ys, xs = ys[o], xs[o]
        rat = y[ys, xs] / x[ys, xs]; q = np.percentile(rat, [5, 50, 95])
        per = {}
        for a in range(0, 360, 45):
            s = (PA[ys, xs] >= a) & (PA[ys, xs] < a + 45)
            if s.sum(): per[f'{a}-{a + 45}'] = dict(n=int(s.sum()), mediana=round(float(np.median(rat[s])), 4))
        zp = ZP[ys, xs]
        out[sent] = dict(p5_p50_p95=q.round(4).tolist(), perles_PA155_190=dict(n=int(zp.sum()), mediana=round(float(np.median(rat[zp])), 4) if zp.any() else None),
                         per_sector_45=per, pitjors_10=[dict(x=int(xs[i] + x0), y=int(ys[i] + y0), PA=round(float(PA[ys[i], xs[i]]), 1), d=round(float(D[ys[i], xs[i]]), 1),
                                                                  q=round(float(rat[i]), 3)) for i in np.argsort(rat)[:10]])
    k = np.sqrt(out['directe_V108_sobre_V107']['p5_p50_p95'][1] / out['invers_V107_sobre_V108']['p5_p50_p95'][1]); out['atenuacio_real_k_mediana'] = round(float(k), 4)
    print('B', nom, json.dumps(out)[:900], flush=True); return out


R['B_pics'] = {}
R['B_pics']['C1'] = pics(np.asarray(np.load(CO / 'C1_V107.npy', mmap_mode='r')[y0:y1, x0:x1], np.float32), np.asarray(np.load(CO / 'C1_V108.npy', mmap_mode='r')[y0:y1, x0:x1], np.float32), 'C1')
R['B_pics']['PLE'] = pics(np.asarray(np.load(CO / 'L_V107.npy', mmap_mode='r')[y0:y1, x0:x1], np.float32), np.asarray(np.load(CO / 'L_V108.npy', mmap_mode='r')[y0:y1, x0:x1], np.float32), 'PLE')
R['B_pics']['FUSIONAT'] = pics(lum(fusionat(PSB7, BX)), lum(fusionat(PSB8, BX)), 'FUSIONAT')
(OUT / 'P2_AJUST_I_PICS.json').write_text(json.dumps(R, ensure_ascii=False, indent=1) + '\n')
print('fet', round(time.time() - T0), 's')
