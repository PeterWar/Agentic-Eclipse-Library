"""b1 (V116, 29-09-2026) · FILTRE DE DETALL RADIAL COHERENT ENTRE ELS DOS APUNTAMENTS DE LA SONY («l'accident fortuït» de Pere).
La Sony 300 mm va relliscar a mitja totalitat: la mateixa corona es va fotografiar des de dues posicions del sensor separades ~750 px (A abans, B
després). La corona real és al mateix lloc del cel a totes dues; el que és del sensor (restes de flat, pols, patró fix, arcs interns de l'òptica
d'A, soroll) no hi coincideix. Aquest filtre només deixa passar el detall que les dues veuen igual.
Matemàtica (sobre la lluminància de cada apuntament, calibrada: A = sony_A_corr / pesos, B = sony_B_total / pesos, amb el flat 2D v5, sense estrelles):
  1. pla LOG-POLAR centrat al Sol: ρ = ln r (pas uniforme), θ (NT mostres). Una σ constant en ρ és una σ ∝ r (els raigs s'eixamplen amb r).
  2. a cada apuntament X: x = ln X; suavitzat radial σ_ρ (1,5 % de r) i detall azimutal D_X = G_θ(σ1)·x − G_θ(σ2)·x (0,15°–1,5°): els raigs.
  3. coherència local (finestra σ_ρ 5 % de r × σ_θ 1°): w = max(0, ⟨D_A·D_B⟩) / (½(⟨D_A²⟩ + ⟨D_B²⟩)) ∈ [0, 1]
     (1 = el mateix detall amb la mateixa amplitud; 0 = res en comú: soroll o artefacte d'un sol apuntament). És el guany de Wiener de dues vistes.
  4. detall coherent D = w · (D_A + D_B)/2; tornada al llenç; ploma a la vora del camp comú (només on hi ha totes dues) i zero a les estrelles.
Ús: b1_filtre_coherent_AB.py <carpeta_sortida>  → D_coherent_f32.npy (llenç sencer, ln), W_coherencia_f16.npy, B1_REBUT.json i vistes"""
import sys, json, time, hashlib, numpy as np, cv2
from pathlib import Path
from scipy import ndimage as ndi
R = Path(__file__).resolve().parents[3]; OUT = Path(sys.argv[1]).resolve(); OUT.mkdir(parents=True, exist_ok=True); t0 = time.time()
F = dict(A=R / '4-RESULTATS/v114_estrelles_20260928/fonts_c/fusio/b3/cau/sony_A_corr_v42.npy', Aw=R / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/sources_v29/sony_A_weights.npy',
         B=R / '4-RESULTATS/v108_20260926/flat2d_v5/apilats/cau/sony_B_total_v42.npy', Bw=R / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/b2_sony_B/cau/sony_B_weights_v42.npy',
         estrelles=R / '4-RESULTATS/v114_estrelles_20260928/fonts_c/fusio/d4/products/sources/star_footprints.npy')
H, W = 7506, 10551; SOL = (5361.768, 3775.748); RS = 440.603
def llum(ft, fw):
    t = np.load(ft, mmap_mode='r'); w = np.load(fw, mmap_mode='r'); L = np.zeros((H, W), np.float32); Wm = np.zeros((H, W), np.float32)
    for c, k in ((0, 1), (1, 2), (2, 1)):
        for y0 in range(0, H, 1024):
            wc = np.asarray(w[y0:y0 + 1024, :, c], np.float32); L[y0:y0 + 1024] += k * np.asarray(t[y0:y0 + 1024, :, c], np.float32) / np.maximum(wc, 1e-6)
            if c == 1: Wm[y0:y0 + 1024] = wc
    return L / 4, Wm
LA, WA = llum(F['A'], F['Aw']); LB, WB = llum(F['B'], F['Bw'])
mA = WA > 0.2 * np.median(WA[WA > 0]); mB = WB > 0.2 * np.median(WB[WB > 0])
st = np.load(F['estrelles'], mmap_mode='r'); st = ndi.binary_dilation(np.asarray(st) > 0, iterations=3)
m = mA & mB & (LA > 0) & (LB > 0) & ~st
print(f'llegit {time.time() - t0:.0f}s · camp comú {m.mean():.3f}', flush=True)
# log-polar
r0, r1 = 1.12 * RS, 10.5 * RS; NR = 4096; NT = 24576
rho = np.linspace(np.log(r0), np.log(r1), NR).astype(np.float32); th = (np.arange(NT) * 2 * np.pi / NT).astype(np.float32)
rr = np.exp(rho)[:, None]; MX = (SOL[0] + rr * np.cos(th)[None, :]).astype(np.float32); MY = (SOL[1] - rr * np.sin(th)[None, :]).astype(np.float32)
def polar(x, interp=cv2.INTER_LINEAR): return cv2.remap(x.astype(np.float32), MX, MY, interp, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
PM = polar(m.astype(np.float32)) > 0.999
xA = np.where(PM, np.log(np.maximum(polar(LA), 1e-9)), 0).astype(np.float32); xB = np.where(PM, np.log(np.maximum(polar(LB), 1e-9)), 0).astype(np.float32)
del LA, LB
dr = float(rho[1] - rho[0]); dth = 2 * np.pi / NT
cv2.setNumThreads(8)
def gcv(x, sr, st_):
    """gaussiana (σ_ρ, σ_θ en mostres) amb θ periòdic: farciment circular manual (cv2 no fa BORDER_WRAP) i cv2.GaussianBlur (multifil)."""
    p = int(4 * st_) + 2; xp = np.concatenate([x[:, -p:], x, x[:, :p]], 1)
    return cv2.GaussianBlur(xp, (0, 0), sigmaX=float(st_), sigmaY=float(sr), borderType=cv2.BORDER_REFLECT)[:, p:-p]
_DEN = {}
def gn(x, sr, st_):
    """suavitzat gaussià normalitzat al domini PM."""
    if (sr, st_) not in _DEN: _DEN[(sr, st_)] = gcv(PM.astype(np.float32), sr, st_)
    den = _DEN[(sr, st_)]; num = gcv(np.where(PM, x, 0).astype(np.float32), sr, st_)
    return num / np.maximum(den, 1e-6), den
SR = 0.015 / dr                                    # suavitzat radial: 1,5 % de r
S1, S2 = np.radians(0.15) / dth, np.radians(1.5) / dth
def detall(x):
    a, _ = gn(x, SR, S1); b, _ = gn(x, SR, S2); return np.where(PM, a - b, 0).astype(np.float32)
DA, DB = detall(xA), detall(xB); del xA, xB
print(f'detall {time.time() - t0:.0f}s', flush=True)
WR, WT = 0.05 / dr, np.radians(1.0) / dth
cov, den = gn(DA * DB, WR, WT); vA, _ = gn(DA * DA, WR, WT); vB, _ = gn(DB * DB, WR, WT)
w = np.clip(cov / np.maximum(0.5 * (vA + vB), 1e-12), 0, 1).astype(np.float32); w[~PM] = 0
D = (w * 0.5 * (DA + DB)).astype(np.float32)
# vora del camp comú: ploma (la coherència necessita la finestra sencera)
feather = np.clip((den - 0.6) / 0.4, 0, 1).astype(np.float32); D *= feather; w *= feather
print(f'coherència {time.time() - t0:.0f}s', flush=True)
# tornada al llenç
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); rc = np.hypot(xx - SOL[0], yy - SOL[1]); tc = np.mod(np.arctan2(-(yy - SOL[1]), xx - SOL[0]), 2 * np.pi)
IX = (tc / (2 * np.pi) * NT).astype(np.float32); IY = ((np.log(np.maximum(rc, 1)) - rho[0]) / dr).astype(np.float32); del yy, xx, rc, tc
fora = (IY < 0) | (IY > NR - 1)
def cart(P):
    Pw = np.concatenate([P, P[:, :2]], 1)
    out = cv2.remap(Pw, IX, IY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0); out[fora] = 0; return out
Dc = cart(D); Wc = cart(w); Dc[~m & ~ndi.binary_dilation(m, iterations=2)] = 0
np.save(OUT / 'D_coherent_f32.npy', Dc.astype(np.float32)); np.save(OUT / 'W_coherencia_f16.npy', Wc.astype(np.float16))
# diagnòstic: el mateix detall de cada apuntament per separat, al llenç (per a la prova d'artefactes)
np.save(OUT / 'DA_f16.npy', cart(DA).astype(np.float16)); np.save(OUT / 'DB_f16.npy', cart(DB).astype(np.float16))
def sha(p):
    with open(p, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
rep = dict(guio=str(Path(__file__).relative_to(R)), entrades={k: str(v.relative_to(R)) for k, v in F.items()}, sha256_entrades={k: sha(v) for k, v in F.items() if k in ('A', 'B')},
           log_polar=dict(r0_Rsol=1.12, r1_Rsol=10.5, NR=NR, NT=NT), suavitzat_radial_frac_r=0.015, detall_azimutal_graus=[0.15, 1.5], finestra_coherencia=dict(frac_r=0.05, graus=1.0),
           camp_comu=float(m.mean()), segons=round(time.time() - t0, 1))
for a, b in ((1.3, 2), (2, 3.5), (3.5, 5.5), (5.5, 9.5)):
    rq = np.hypot(np.arange(W)[None, ::4] - SOL[0], np.arange(H)[::4, None] - SOL[1]) / RS; k = (rq >= a) & (rq < b) & m[::4, ::4]
    rep[f'banda_{a}-{b}'] = dict(w_mediana=float(np.median(Wc[::4, ::4][k])), sd_D_pct=float(np.std(Dc[::4, ::4][k]) * 100))
(OUT / 'B1_REBUT.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1)); print(json.dumps(rep, ensure_ascii=False)[:1500])
