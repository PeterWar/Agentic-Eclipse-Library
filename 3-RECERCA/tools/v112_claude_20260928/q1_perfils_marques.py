"""q1 · Mesura amb geometria FIXA (decidida abans de mirar la V113): perfils del compost desat (render natiu, L=(R+2G+B)/4, ln).
 · Arcs 2/3/5: perfil radial des del centre comú ajustat als traços de Pere (4859, 2747), dins del sector angular que cobreixen els traços;
   mediana per anells de 10 px; es treu una tendència polinòmica de grau 3 sobre 1.500–3.200 px; mètrica = rms del residu a 1.700–3.000 px.
 · Marca 8: perfil perpendicular a l'eix del traç (recta ajustada a l'esquelet), ±700 px, calaixos de 10 px, al llarg de tot el traç;
   es treu una recta; mètrica = profunditat de la vall (mitjana de ±40 px de l'eix menys la mitjana de 150–400 px a banda i banda).
Ús: q1_perfils_marques.py NOM1=TIF1 NOM2=TIF2 …   → vistes/perfils_marques.png i PERFILS_MARQUES.json"""
import sys, json
from pathlib import Path
import numpy as np, tifffile
from scipy import ndimage as ndi
from skimage.morphology import skeletonize
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
R = Path(__file__).resolve().parents[3]; O = R / '4-RESULTATS/v112_claude_20260928'
mq = np.load(R / '4-RESULTATS/v112_20260928/marques412.npz'); al = mq['alpha'] > 0; og = mq['origin']
lab, _ = ndi.label(al)
def esquelet(i):
    sl = ndi.find_objects(lab)[i - 1]; yy, xx = np.nonzero(skeletonize(lab[sl] == i)); return xx + sl[1].start + og[0], yy + sl[0].start + og[1]
CEN = (4859.0, 2747.0)
ang = []
for i in (2, 3, 5):
    x, y = esquelet(i); ang += list(np.degrees(np.arctan2(y - CEN[1], x - CEN[0])))
A0, A1 = np.percentile(ang, 2), np.percentile(ang, 98)
x8, y8 = esquelet(8); P = np.c_[x8, y8].astype(float); c8 = P.mean(0); u, s, vt = np.linalg.svd(P - c8, full_matrices=False); d8 = vt[0]; n8 = np.array([-d8[1], d8[0]])
t8 = (P - c8) @ d8; T0, T1 = t8.min(), t8.max()
res = dict(arcs=dict(centre=CEN, sector_graus=[float(A0), float(A1)]), marca8=dict(centre=c8.tolist(), direccio=d8.tolist(), llarg=[float(T0), float(T1)]), versions={})
fig, ax = plt.subplots(1, 2, figsize=(14, 4.2))
for arg in sys.argv[1:]:
    nom, f = arg.split('=', 1); im = tifffile.memmap(f)
    # arcs
    y0, y1, x0, x1 = 0, 3000, 3500, 8200
    a = np.asarray(im[y0:y1, x0:x1], np.float64); L = (a[..., 0] + 2 * a[..., 1] + a[..., 2]) / 4
    yy, xx = np.mgrid[y0:y1, x0:x1]; r = np.hypot(xx - CEN[0], yy - CEN[1]); th = np.degrees(np.arctan2(yy - CEN[1], xx - CEN[0]))
    m = (th >= A0) & (th <= A1) & (L > 300) & (r > 1500) & (r < 3200)
    rb = (r[m] // 10).astype(int); v = np.log(L[m]); k = np.unique(rb)
    prof = np.array([np.median(v[rb == q]) for q in k]); rr = k * 10 + 5
    cf = np.polyfit(rr, prof, 3); resid = prof - np.polyval(cf, rr); w = (rr > 1700) & (rr < 3000)
    rms_arcs = float(np.sqrt(np.mean(resid[w] ** 2)))
    ax[0].plot(rr, resid * 100, lw=1, label=f'{nom}: rms {rms_arcs*100:.3f} %')
    # marca 8
    bx0, by0 = int(min(x8) - 800), int(min(y8) - 800); bx1, by1 = int(max(x8) + 800), int(max(y8) + 800)
    bx0, by0 = max(bx0, 0), max(by0, 0); bx1, by1 = min(bx1, 10551), min(by1, 7506)
    a = np.asarray(im[by0:by1, bx0:bx1], np.float64); L = (a[..., 0] + 2 * a[..., 1] + a[..., 2]) / 4
    yy, xx = np.mgrid[by0:by1, bx0:bx1]; Q = np.stack([xx - c8[0], yy - c8[1]], -1); t = Q @ d8; sd = Q @ n8
    m = (t >= T0) & (t <= T1) & (np.abs(sd) < 700) & (L > 300)
    sb = np.floor(sd[m] / 10).astype(int); v = np.log(L[m]); k = np.unique(sb)
    pr = np.array([np.mean(v[sb == q]) for q in k]); ss = k * 10 + 5
    cf = np.polyfit(ss, pr, 1); r8 = pr - np.polyval(cf, ss)
    vall = float(np.mean(r8[np.abs(ss) < 40]) - np.mean(r8[(np.abs(ss) > 150) & (np.abs(ss) < 400)]))
    ax[1].plot(ss, r8 * 100, lw=1, label=f'{nom}: vall {vall*100:+.3f} %')
    res['versions'][nom] = dict(fitxer=f, rms_arcs_pct=rms_arcs * 100, vall_marca8_pct=vall * 100)
    print(nom, 'rms arcs %', round(rms_arcs * 100, 4), 'vall 8 %', round(vall * 100, 4), flush=True)
for r_ in (1908, 2366, 2832): ax[0].axvline(r_, color='m', lw=.6, ls='--')
ax[0].set_title('Arcs 2/3/5: perfil radial des de (4859, 2747), sector dels traços (sense tendència)'); ax[0].set_xlabel('radi (px)'); ax[0].set_ylabel('ln L (%)'); ax[0].legend(fontsize=8); ax[0].grid(alpha=.3)
ax[1].set_title('Marca 8: perfil perpendicular al traç (sense recta)'); ax[1].set_xlabel('distància a l\'eix del traç (px)'); ax[1].legend(fontsize=8); ax[1].grid(alpha=.3)
fig.tight_layout(); fig.savefig(O / 'vistes/perfils_marques.png', dpi=100)
(O / 'PERFILS_MARQUES.json').write_text(json.dumps(res, indent=1, ensure_ascii=False))
