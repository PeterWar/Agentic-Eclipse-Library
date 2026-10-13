"""c2 · La corona de la final contra K-Cor (llum blanca polaritzada, 1,07–2,0 R☉) i SOHO/LASCO C2 (2,3–6 R☉) i C3 (4–20 R☉).
Tot es porta a coordenades solars (r en R☉ de cada observador, PA des del nord solar cap a l'est).
1. Desplegats polars, r logarítmic 1,05–20 R☉, PA a 0,5°: final (lluminància), K-Cor NRGF, C2 i C3 amb NRGF calculat a la
   mateixa imatge (el fons de corona F i la llum difusa són radials i el NRGF els treu igual a totes).
2. Perfils d'angle a radis fixos: correlació de Pearson i gir que la maximitza (correlació circular), amb els dos perfils
   suavitzats a la mateixa resolució angular. Zones sense dada de cada instrument (ocultador, pilar, rètols) excloses.
Escriu C2_PERFILS.json i C2_desplegats.npz."""
import json, sys
import numpy as np
from scipy import ndimage as nd
from astropy.io import fits
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from comu_comp import *

BIN = 4
fin = carrega_final(); gF = geo_final('efemeride')
H, W = fin.shape[:2]; Hb, Wb = H // BIN, W // BIN
L = np.zeros((Hb, Wb), np.float32)
for i in range(0, Hb):          # lluminància i binat 4×4 per franges (memòria)
    blk = np.asarray(fin[i * BIN:(i + 1) * BIN, :Wb * BIN]).astype(np.float32) / 65535.0
    l = 0.2974 * blk[..., 0] + 0.6273 * blk[..., 1] + 0.0753 * blk[..., 2]
    L[i] = l.reshape(BIN, Wb, BIN).mean(axis=(0, 2))
gB = Geo('final/4', (gF.cx + 0.5) / BIN - 0.5, (gF.cy + 0.5) / BIN - 0.5, gF.R / BIN, gF.n, gF.e, gF.data, gF.obs)
lluna = np.array(GEO['lluna_px']); RL = GEO['R_lluna_px']
yy, xx = np.mgrid[0:Hb, 0:Wb]
mL = np.hypot((xx + 0.5) * BIN - 0.5 - lluna[0], (yy + 0.5) * BIN - 0.5 - lluna[1]) < RL + 6
Lv = np.where(mL, np.nan, L)
np.save(RES / 'C2_final_L_bin4.npy', L)
print(f"final binada {Wb}×{Hb}; R☉ {gB.R:.2f} px; abast r: {gB.polar(np.array([0, Wb-1, 0, Wb-1]), np.array([0, 0, Hb-1, Hb-1]))[0].round(2)} (cantonades)")

# ---------------- K-Cor NRGF (GIF): valor 0–255 = NRGF −2…+4
kc, gK = carrega_kcor('20260812_182932_kcor_l2_nrgf_avg_cropped.gif')
kc1, _ = carrega_kcor('20260812_182846_kcor_l2_nrgf_cropped.gif')
ky, kx = np.mgrid[0:512, 0:512]
rK, paK = gK.polar(kx, ky)
mK = (rK > 1.10) & (rK < 2.00)
for (a, b, c, d) in [(0, 150, 0, 48), (395, 512, 0, 40), (0, 265, 462, 512), (340, 512, 462, 512)]:   # rètols
    mK[c:d, a:b] = False
kc_v = np.where(mK, -2 + 6 * kc / 255.0, np.nan).astype(np.float32)
kc1_v = np.where(mK, -2 + 6 * kc1 / 255.0, np.nan).astype(np.float32)

# ---------------- LASCO C2 i C3 (nivell 0,5, DN/s), màscara d'ocultador, pilar i vora
def prep_lasco(fitxer, rmin, rmax):
    d, g, hd = carrega_lasco(fitxer)
    yy2, xx2 = np.mgrid[0:d.shape[0], 0:d.shape[1]]
    r, pa = g.polar(xx2, yy2)
    m = (r > rmin) & (r < rmax) & (d > 0)
    if hd['detector'] == 'C3':
        mk = fits.open(DADES / 'lasco_calib/c3clearmask2.fts')[0].data
        m &= (mk[:d.shape[0], :d.shape[1]] > 0) if mk.shape == d.shape else m
    # pilar: sector on el perfil d'angle cau > 25 % sota la mitjana local, a radis intermedis
    ann = (r > rmin + 0.3) & (r < rmin + 1.5 if hd['detector'] == 'C2' else r < rmin + 4)
    bins = np.arange(0, 361, 2.0); k = np.digitize(pa[ann], bins) - 1
    prof = np.array([np.nanmedian(d[ann][k == i]) for i in range(180)])
    ref = nd.median_filter(prof, size=31, mode='wrap')
    dolent = prof < 0.75 * ref
    dolent = nd.binary_dilation(dolent, iterations=2)
    for i in np.nonzero(dolent)[0]:
        m &= ~((pa >= bins[i]) & (pa < bins[i + 1]))
    return np.where(m, d, np.nan).astype(np.float32), g, hd, [float(bins[i]) for i in np.nonzero(dolent)[0]]

c2a, gC2a, h2a, pil2 = prep_lasco('24038985.fts', 2.3, 6.3)
c2b, gC2b, h2b, _ = prep_lasco('24038986.fts', 2.3, 6.3)
c3a, gC3a, h3a, pil3 = prep_lasco('32869549.fts', 4.0, 20.0)
print(f"C2 18:24 sector exclòs (pilar) a PA ≈ {pil2[:1]}–{pil2[-1:]}; C3 18:30 a PA ≈ {pil3[:1]}–{pil3[-1:]}")

# ---------------- desplegats polars
pa = np.arange(0, 360, 0.5); lr = np.linspace(np.log10(1.05), np.log10(20.0), 600); rr = 10 ** lr
RR, PP = np.meshgrid(rr, pa, indexing='ij')
D = dict(final=mostreja(Lv, gB, RR, PP), kcor=mostreja(kc_v, gK, RR, PP), kcor_182846=mostreja(kc1_v, gK, RR, PP),
         c2_1824=mostreja(c2a, gC2a, RR, PP), c2_1836=mostreja(c2b, gC2b, RR, PP), c3_1830=mostreja(c3a, gC3a, RR, PP))
def nrgf_polar(A):
    mu = np.nanmedian(A, axis=1, keepdims=True); sd = 1.4826 * np.nanmedian(np.abs(A - mu), axis=1, keepdims=True)
    return (A - mu) / sd
N = {k: (nrgf_polar(v) if k != 'kcor' and k != 'kcor_182846' else v) for k, v in D.items()}
# pilar de l'ocultador del LASCO: el tram CONTIGU, al voltant de PA 320°, on la mediana radial del NRGF cau per sota de −0,3 σ
# (2,5–6 R☉ al C2, 5–18 al C3), eixamplat 4°. ⛔ No s'hi barregen forats coronals: només el tram del pilar. Es treuen de la dada i es refà el NRGF (el sector fosc esbiaixava la mediana de cada radi).
pilar = {}
for k, (r1, r2) in {'c2_1824': (2.5, 6.0), 'c2_1836': (2.5, 6.0), 'c3_1830': (5.0, 18.0)}.items():
    sel = (rr >= r1) & (rr <= r2); med = np.nanmedian(N[k][sel], axis=0)
    fosc = ~(med > -0.3)
    lab, _ = nd.label(np.r_[fosc, fosc]); k320 = lab[int(320 / 0.5)]      # tram fosc contigu que conté PA 320° (el pilar), amb volta
    tram = (lab == k320) if k320 > 0 else np.zeros(2 * len(pa), bool)
    dol = nd.binary_dilation(tram[:len(pa)] | tram[len(pa):], iterations=8)     # 8 × 0,5° = 4°
    d2 = D[k].copy(); d2[:, dol] = np.nan; D[k] = d2; N[k] = nrgf_polar(d2)
    pilar[k] = [float(pa[dol].min()), float(pa[dol].max()), int(dol.sum())]
    print(f"pilar {k}: PA {pilar[k][0]:.1f}–{pilar[k][1]:.1f}° ({pilar[k][2] * 0.5:.0f}° exclosos)")
np.savez_compressed(RES / 'C2_desplegats.npz', pa=pa, r=rr, **{f'brut_{k}': v for k, v in D.items()}, **{f'nrgf_{k}': v for k, v in N.items()})

# ---------------- perfils d'angle i correlació circular
def perfil(A, r1, r2, sig=1.5):
    sel = (rr >= r1) & (rr <= r2); p = np.nanmean(A[sel], axis=0)
    ok = np.isfinite(p).astype(float); pz = np.where(ok > 0, p, 0.0)
    s = sig / 0.5
    num = nd.gaussian_filter1d(pz, s, mode='wrap'); den = nd.gaussian_filter1d(ok, s, mode='wrap')
    out = np.where(den > 0.6, num / np.maximum(den, 1e-6), np.nan); return out
def corr_circular(p, q, maxgir=10.0):
    gir = np.arange(-maxgir, maxgir + 0.01, 0.5); cs = []
    for gdeg in gir:
        qs = np.roll(q, int(round(gdeg / 0.5)))
        m = np.isfinite(p) & np.isfinite(qs)
        if m.sum() < 60: cs.append(np.nan); continue
        a, b = p[m] - p[m].mean(), qs[m] - qs[m].mean(); cs.append(float((a * b).sum() / np.sqrt((a * a).sum() * (b * b).sum())))
    cs = np.array(cs); i = int(np.nanargmax(cs))
    m0 = np.isfinite(p) & np.isfinite(q)
    return float(cs[i]), float(gir[i]), float(cs[len(gir) // 2]), int(m0.sum())
def passa_alt_angle(p, sig=12.0):
    ok = np.isfinite(p).astype(float); pz = np.where(ok > 0, p, 0.0); s_ = sig / 0.5
    m = nd.gaussian_filter1d(pz, s_, mode='wrap') / np.maximum(nd.gaussian_filter1d(ok, s_, mode='wrap'), 1e-6)
    return p - m
def nul_girs(pF, pR):
    vals = []
    for gg in np.arange(30, 331, 2):
        qs = np.roll(pR, int(gg / 0.5)); m = np.isfinite(pF) & np.isfinite(qs)
        a, b = pF[m] - pF[m].mean(), qs[m] - qs[m].mean(); vals.append(float((a * b).sum() / np.sqrt((a * a).sum() * (b * b).sum())))
    return np.array(vals)
res = {}
parells = [('kcor', 1.15, 1.30), ('kcor', 1.30, 1.50), ('kcor', 1.50, 1.75), ('kcor', 1.75, 1.98),
           ('c2_1824', 2.4, 2.8), ('c2_1824', 2.8, 3.3), ('c2_1824', 3.3, 4.0), ('c2_1824', 4.0, 5.0), ('c2_1824', 5.0, 6.0),
           ('c2_1836', 2.8, 3.3), ('c2_1836', 3.3, 4.0),
           ('c3_1830', 4.5, 5.5), ('c3_1830', 5.5, 7.0), ('c3_1830', 7.0, 9.0)]
for ref, r1, r2 in parells:
    pF = perfil(N['final'], r1, r2); pR = perfil(N[ref], r1, r2)
    c, g, c0, n = corr_circular(pF, pR)
    nz = nul_girs(pF, pR)
    hF, hR = passa_alt_angle(pF), passa_alt_angle(pR)
    ch, gh, ch0, _ = corr_circular(hF, hR); nzh = nul_girs(hF, hR)
    res[f'{ref}_{r1:.2f}-{r2:.2f}'] = dict(rho=c, gir_deg=g, rho_0=c0, n_angles=n, nul_mitjana=float(nz.mean()), nul_sd=float(nz.std()), nul_max=float(nz.max()),
                                         passa_alt=dict(rho_0=ch0, rho=ch, gir_deg=gh, nul_mitjana=float(nzh.mean()), nul_sd=float(nzh.std()), nul_max=float(nzh.max())))
    print(f"final ↔ {ref:8s} r {r1:.2f}–{r2:.2f} R☉: ρ(0) {c0:+.3f} (gir òptim {g:+.1f}°; nul {nz.mean():+.2f}±{nz.std():.2f}, màx {nz.max():+.2f}) | "
          f"detall <12°: ρ(0) {ch0:+.3f} (gir {gh:+.1f}°; nul {nzh.mean():+.2f}±{nzh.std():.2f}, màx {nzh.max():+.2f}); {n} angles")
# control nul: el mateix amb el perfil de referència girat 90° i 180°
nul = {}
for ref, r1, r2 in [('kcor', 1.30, 1.50), ('c2_1824', 2.8, 3.3), ('c2_1824', 3.3, 4.0)]:
    pF = perfil(N['final'], r1, r2); pR = perfil(N[ref], r1, r2)
    for gg in (90, 180, 270):
        c, g, c0, n = corr_circular(pF, np.roll(pR, int(gg / 0.5)))
        nul[f'{ref}_{r1:.2f}-{r2:.2f}_gir{gg}'] = dict(rho_0=c0, rho_max=c, gir=g)
        print(f"   control nul {ref} r {r1}–{r2} girat {gg}°: ρ(0) {c0:+.3f}")
# coherència entre els dos instants del C2 i entre K-Cor 18:28:46 i la mitjana de 18:29:32 (sostre de cada comparació)
for a, b, r1, r2 in [('c2_1824', 'c2_1836', 2.8, 3.3), ('c2_1824', 'c2_1836', 3.3, 4.0), ('kcor', 'kcor_182846', 1.30, 1.50)]:
    c, g, c0, n = corr_circular(perfil(N[a], r1, r2), perfil(N[b], r1, r2))
    res[f'sostre_{a}_vs_{b}_{r1}-{r2}'] = dict(rho_0=c0, rho=c, gir_deg=g)
    print(f"sostre {a} ↔ {b} r {r1}–{r2}: ρ(0) {c0:+.3f}")
json.dump(dict(resultats=res, control_nul=nul, pilar=pilar, suavitzat_angular_sigma_deg=1.5),
          open(RES / 'C2_PERFILS.json', 'w'), indent=1)
print('fet')
