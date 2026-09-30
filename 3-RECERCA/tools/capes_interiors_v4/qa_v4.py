"""QA del compost V4 (des dels npy finals, = el PSB): perfils, test d'anells (residu del perfil respecte d'una versió suau),
correlació de l'estructura azimutal amb les capes soles, i figures."""
import numpy as np, json
from scipy import ndimage as ndi
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
SUN3 = (4021.89, 2738.66); RS = 446.15
D = np.load('v4/disseny.npz'); rr = D['rr']; meta = json.load(open('v3/meta.json')); ladder = [int(i) for i in D['ladder']]
mer = np.load('v3/merged_rgb.npy', mmap_mode='r'); V4 = np.load('v4/compost_rgb16.npy', mmap_mode='r'); V4g = np.load('v4/compost_gain_rgb16.npy', mmap_mode='r')
Lay = {i: np.load(f, mmap_mode='r') for i, f in enumerate(sorted(__import__('glob').glob('v3/*_rgb.npy'))) if 'merged' not in f}
MOON = (4035.8, 2737.3); MR = 451.5
# reixa polar fina: r 0,98–3,0 cada 0,002 (0,9 px), θ cada 0,5°
rf = np.arange(0.98, 3.0, 0.002); th = np.deg2rad(np.arange(0, 360, 0.5)); R, T = np.meshgrid(rf, th, indexing='ij')
def pol(arr, sun, off):
    X = sun[0] + R * RS * np.cos(T) - off[0]; Y = sun[1] - R * RS * np.sin(T) - off[1]
    return np.stack([ndi.map_coordinates(np.asarray(arr[..., c], np.float32) / 65535., [Y, X], order=1) for c in range(3)])
lum = lambda C: 0.2126 * C[0] + 0.7152 * C[1] + 0.0722 * C[2]
X3 = SUN3[0] + R * RS * np.cos(T); Y3 = SUN3[1] - R * RS * np.sin(T)
fora = np.hypot(X3 - MOON[0], Y3 - MOON[1]) / MR > 1.03
noprot = ~((np.rad2deg(T) > 160) & (np.rad2deg(T) < 178)) | (R > 1.12)
ok = fora & noprot
P3 = pol(mer, SUN3, (0, 0)); P4 = pol(V4, (SUN3[0] - 1, SUN3[1] - 1), (457, 463)); P4g = pol(V4g, (SUN3[0] - 1, SUN3[1] - 1), (457, 463))
def medprof(P):
    L = np.where(ok, lum(P), np.nan); return np.nanmedian(L, axis=1)
def fillnan(a):
    a = a.copy(); okk = np.isfinite(a); a[~okk] = np.interp(np.flatnonzero(~okk), np.flatnonzero(okk), a[okk]); return a
m3, m4, m4g = fillnan(medprof(P3)), fillnan(medprof(P4)), fillnan(medprof(P4g))
# --- test d'anells: residu del perfil mitjà (en ln) respecte d'una versió suavitzada (σ = 0,02 en ln r ≈ 9 px a 1 R☉)
lnr = np.log(rf); g = np.linspace(lnr[0], lnr[-1], 6000)
def ring_test(m, lab):
    y = np.log(np.maximum(m, 1e-5)); yi = np.interp(g, lnr, y); ys = ndi.gaussian_filter1d(yi, 0.02 / (g[1] - g[0]), mode='nearest')
    res = yi - ys; sel = (np.exp(g) > 1.09) & (np.exp(g) < 2.9)
    print(f'test d\'anells {lab}: residu del perfil (ln) respecte de la versió suau: rms {res[sel].std()*100:.2f} %, màx |{np.abs(res[sel]).max()*100:.2f}| % a r={np.exp(g[sel][np.argmax(np.abs(res[sel]))]):.3f}')
    for rq in (1.1, 1.15, 1.2, 1.3, 1.5, 1.7, 1.8, 2.0, 2.5): print(f'      residu a r={rq}: {res[np.argmin(np.abs(np.exp(g)-rq))]*100:+.2f} %')
    return np.exp(g), res
for m, lab in ((m3, 'V3'), (m4, 'V4 nu'), (m4g, 'V4 + guany')): ring_test(m, lab)
# --- pendent local del perfil (d ln L / d ln r) suau: bony = canvi de signe
def slope(m):
    y = np.log(np.maximum(m, 1e-5)); yi = np.interp(g, lnr, y); ys = ndi.gaussian_filter1d(yi, 0.03 / (g[1] - g[0]), mode='nearest'); return np.gradient(ys, g)
s3, s4, s4g = slope(m3), slope(m4), slope(m4g)
sel = (np.exp(g) > 1.03) & (np.exp(g) < 2.9)
print('pendent màxim (positiu = s\'aclareix cap enfora): V3', float(s3[sel].max()), ' V4 nu', float(s4[sel].max()), ' V4+guany', float(s4g[sel].max()))
# --- estructura azimutal: correlació del log-ratio a la mediana d'anell amb la capa 07 i la capa 08 (a la seva zona vàlida)
def struct(P):
    L = lum(P); med = np.nanmedian(np.where(ok, L, np.nan), axis=1, keepdims=True); return np.log(np.maximum(L, 1e-5)) - np.log(np.maximum(med, 1e-5))
S3, S4 = struct(P3), struct(P4)
for i, lab, r0, r1 in ((5, '07 (1/15 s)', 1.4, 1.9), (4, '08 (1/30 s)', 1.25, 1.6), (2, 'Capa 5 (1/125)', 1.0, 1.2), (6, '06 (1/8 s)', 1.55, 2.2)):
    Pi = pol(Lay[i], SUN3, tuple(meta['layers'][i]['bbox'][:2])); Si = struct(Pi)
    sel2 = ok & (R > r0) & (R < r1) & np.isfinite(Si) & np.isfinite(S3) & np.isfinite(S4)
    c3 = np.corrcoef(S3[sel2], Si[sel2])[0, 1]; c4 = np.corrcoef(S4[sel2], Si[sel2])[0, 1]
    a3 = np.polyfit(Si[sel2], S3[sel2], 1)[0]; a4 = np.polyfit(Si[sel2], S4[sel2], 1)[0]
    print(f'estructura vs capa {lab} a {r0}–{r1} R☉: correlació V3 {c3:.3f} / V4 {c4:.3f}; pendent (contrast relatiu) V3 {a3:.2f} / V4 {a4:.2f}')
# --- figures
fig, ax = plt.subplots(2, 1, figsize=(9, 10), sharex=True)
ax[0].semilogy(rr, D['T3'], 'k-', lw=2, label='V3 (mitjana az.)'); ax[0].semilogy(rf, m4, 'b-', lw=2, label='V4 fusió nua'); ax[0].semilogy(rf, m4g, 'r-', lw=1.5, label='V4 + guany radial')
ax[0].semilogy(rr, D['B_reach'], 'g--', lw=1, label='sostre vàlid (capa més llarga no comprimida)')
for i in ladder: ax[0].semilogy(rr, D[f'L{i}'], ':', lw=0.8, label=meta['layers'][i]['name'][:8])
ax[0].set_ylabel('luminància codificada (mediana azimutal)'); ax[0].set_xlim(0.98, 3.0); ax[0].set_ylim(0.01, 1.2); ax[0].legend(fontsize=7, ncol=3); ax[0].grid(alpha=0.3); ax[0].set_title('CapesInteriorsV4: perfil radial del compost i de cada capa')
for i in ladder: ax[1].plot(rr, D[f'W{i}'], label=meta['layers'][i]['name'][:8])
ax[1].set_ylabel('pes efectiu de cada capa'); ax[1].set_xlabel('r (R☉)'); ax[1].legend(fontsize=7, ncol=4); ax[1].grid(alpha=0.3); ax[1].set_ylim(0, 1.02)
fig.tight_layout(); fig.savefig('v4/qa_perfils.png', dpi=110)
fig, ax = plt.subplots(figsize=(9, 4))
for i in ladder: ax.plot(rr, D[f'm{i}'], label=meta['layers'][i]['name'][:8])
ax.set_xlim(0.95, 3.0); ax.set_xlabel('r (R☉)'); ax.set_ylabel('valor de la màscara'); ax.set_title('Màscares radials de V4 (fora del disc lunar)'); ax.legend(fontsize=7, ncol=4); ax.grid(alpha=0.3)
fig.tight_layout(); fig.savefig('v4/qa_mascares.png', dpi=110)
print('figures fetes')
