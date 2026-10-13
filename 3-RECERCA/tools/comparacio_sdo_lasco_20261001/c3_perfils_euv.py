"""c3 · Corona baixa (1,10–1,28 R☉): la final, el K-Cor i l'SDO/AIA (171, 193, 211 Å), amb el mateix mètode i la mateixa màscara.
Pregunta: la final porta la mateixa informació d'estructura que un coronògraf professional de llum blanca?
Referència: K-Cor ↔ AIA (dos instruments professionals independents). Si final ↔ AIA ≈ K-Cor ↔ AIA, la final es comporta com el K-Cor.
Perfils d'angle per bandes de radi (NRGF per radi a cada imatge, suavitzat σ 1,5°), Pearson i Spearman, i control nul de girs.
La màscara de la Lluna (instant C2) s'aplica a totes les imatges perquè es comparin els mateixos punts. Escriu C3_PERFILS_EUV.json."""
import json, sys
import numpy as np
from scipy import ndimage as nd
from scipy.stats import spearmanr
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from comu_comp import *

fin = carrega_final(); gF = geo_final('efemeride')
lluna = np.array(GEO['lluna_px']); RL = GEO['R_lluna_px']
M = int(round(1.40 * gF.R)); x0, y0 = int(round(gF.cx)) - M, int(round(gF.cy)) - M
crop = np.asarray(fin[y0:y0 + 2 * M + 1, x0:x0 + 2 * M + 1]).astype(np.float32) / 65535.0
Lf = 0.2974 * crop[..., 0] + 0.6273 * crop[..., 1] + 0.0753 * crop[..., 2]
g0 = Geo('retall', gF.cx - x0, gF.cy - y0, gF.R, gF.n, gF.e, gF.data, gF.obs)

DPA = 0.25
pa = np.arange(0, 360, DPA); rr = np.arange(1.06, 1.30001, 0.004)
RR, PP = np.meshgrid(rr, pa, indexing='ij')
xL, yL = g0.px(RR, PP)
dins = np.hypot(xL + x0 - lluna[0], yL + y0 - lluna[1]) < RL + 3.0       # Lluna (instant C2) + 3 px
P = {'final': mostreja(Lf, g0, RR, PP)}
kc, gK = carrega_kcor('20260812_182932_kcor_l2_nrgf_avg_cropped.gif')
kv = -2 + 6 * kc / 255.0
rK, _ = gK.polar(*np.meshgrid(np.arange(512), np.arange(512)))
kv[(rK < 1.09)] = np.nan
for (a, b, c, d) in [(0, 150, 0, 48), (395, 512, 0, 40), (0, 265, 462, 512), (340, 512, 462, 512)]:
    kv[c:d, a:b] = np.nan
P['kcor'] = mostreja(kv, gK, RR, PP)
for ona in ['0171', '0193', '0211']:
    d, g = carrega_aia('1828', ona)
    P[f'aia{ona}'] = mostreja(np.log10(np.clip(d, 0.05, None)), g, RR, PP)
comuna = ~dins
for v in P.values(): comuna &= np.isfinite(v)
print(f"punts comuns: {comuna.mean() * 100:.1f} % de la graella (Lluna i rètols fora)")

def nrgf_p(A):
    A = np.where(comuna, A, np.nan)
    mu = np.nanmedian(A, axis=1, keepdims=True); sd = 1.4826 * np.nanmedian(np.abs(A - mu), axis=1, keepdims=True)
    return (A - mu) / sd
N = {k: nrgf_p(v) for k, v in P.items()}
def perfil(A, r1, r2, sig=1.5):
    sel = (rr >= r1) & (rr <= r2); p = np.nanmean(A[sel], axis=0)
    ok = np.isfinite(p).astype(float); pz = np.where(ok > 0, p, 0.0); s = sig / DPA
    den = nd.gaussian_filter1d(ok, s, mode='wrap')
    return np.where(den > 0.6, nd.gaussian_filter1d(pz, s, mode='wrap') / np.maximum(den, 1e-6), np.nan)
def pas_alt(p, sig=12.0):
    ok = np.isfinite(p).astype(float); pz = np.where(ok > 0, p, 0.0); s = sig / DPA
    return p - nd.gaussian_filter1d(pz, s, mode='wrap') / np.maximum(nd.gaussian_filter1d(ok, s, mode='wrap'), 1e-6)
def rho(p, q, gir=0.0):
    q = np.roll(q, int(round(gir / DPA))); m = np.isfinite(p) & np.isfinite(q)
    a, b = p[m] - p[m].mean(), q[m] - q[m].mean()
    return float((a * b).sum() / np.sqrt((a * a).sum() * (b * b).sum())), float(spearmanr(p[m], q[m]).statistic), int(m.sum())
def gir_optim(p, q):
    girs = np.arange(-5, 5.001, DPA); cs = [rho(p, q, g)[0] for g in girs]; i = int(np.argmax(cs))
    if 0 < i < len(girs) - 1:                                 # paràbola pels tres punts del màxim
        y1, y2, y3 = cs[i - 1], cs[i], cs[i + 1]; den = (y1 - 2 * y2 + y3)
        off = 0.5 * (y1 - y3) / den if den != 0 else 0.0
        return float(girs[i] + off * DPA), float(cs[i])
    return float(girs[i]), float(cs[i])
def nul(p, q):
    v = np.array([rho(p, q, g)[0] for g in np.arange(30, 331, 2)]); return float(v.mean()), float(v.std()), float(v.max())

res = {}
parells = [('final', 'kcor'), ('final', 'aia0171'), ('kcor', 'aia0171'), ('final', 'aia0193'), ('kcor', 'aia0193'),
           ('final', 'aia0211'), ('kcor', 'aia0211')]
for r1, r2 in [(1.10, 1.16), (1.16, 1.22), (1.22, 1.28)]:
    for a, b in parells:
        pa_, pb_ = perfil(N[a], r1, r2), perfil(N[b], r1, r2)
        r0, s0, n = rho(pa_, pb_); g, rg = gir_optim(pa_, pb_); nm, ns, nx = nul(pa_, pb_)
        ha, hb = pas_alt(pa_), pas_alt(pb_); rh, sh, _ = rho(ha, hb); nhm, nhs, nhx = nul(ha, hb)
        res[f'{a}~{b}_{r1:.2f}-{r2:.2f}'] = dict(pearson=r0, spearman=s0, gir_optim_deg=g, rho_gir=rg, nul=[nm, ns, nx], n_angles=n,
                                                 detall_12=dict(pearson=rh, spearman=sh, nul=[nhm, nhs, nhx]))
        print(f"r {r1:.2f}–{r2:.2f}  {a:6s} ↔ {b:8s}: Pearson {r0:+.3f}  Spearman {s0:+.3f}  gir òptim {g:+.2f}°  "
              f"(nul {nm:+.2f}±{ns:.2f})  | detall <12°: {rh:+.3f} (nul {nhm:+.2f}±{nhs:.2f})")
json.dump(dict(resultats=res, punts_comuns_frac=float(comuna.mean()), suavitzat_sigma_deg=1.5, pas_alt_sigma_deg=12.0,
               aia_instant='18:28:00–18:28:10 UTC', kcor='mitjana de 2 min a 18:29:32 UTC'), open(RES / 'C3_PERFILS_EUV.json', 'w'), indent=1)
np.savez_compressed(RES / 'C3_desplegats.npz', pa=pa, r=rr, comuna=comuna, **{f'nrgf_{k}': v for k, v in N.items()})
print('fet')
