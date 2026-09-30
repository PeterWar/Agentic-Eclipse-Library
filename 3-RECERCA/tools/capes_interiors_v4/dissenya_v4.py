"""Disseny de les màscares radials de V4 (espai polar). v2: abast recursiu, assignació per pressupost (capa més llarga vàlida + resta),
limbe tractat fora de la Lluna. Escriu v4/disseny.npz (perfils m_k(r), W_k(r), T) i el diagnòstic."""
import numpy as np, json, os, sys
from scipy import ndimage as ndi
os.makedirs('v4', exist_ok=True)
P95_MAX = float(os.environ.get('P95_MAX', 0.66)); P50_MAX = float(os.environ.get('P50_MAX', 0.46))
RAMP_LO, RAMP_W = 0.02, float(os.environ.get('RAMP_W', 0.12))
SIG_T = 0.04; SIG_W = float(os.environ.get('SIG_W', 0.025))
R_PEAK = 1.00                      # des d'aquí el perfil objectiu és monòton no creixent
MOON_C = (4036.5, 2737.8); MOON_R = 451.5   # centre i radi del disc lunar (ajust del limbe de Capa 5 / 09), píxels de document
d = np.load('v3/polar.npz'); c = np.load('v3/polar_compost.npz'); e = np.load('v3/perfils_ext.npz')
meta = json.load(open('v3/meta.json')); nL = len(meta['layers'])
rr_in = d['rr']; th_deg = d['th']; th = np.deg2rad(th_deg); rr_ex = e['rr']; sel_ex = rr_ex > rr_in[-1] + 1e-9
rr = np.concatenate([rr_in, rr_ex[sel_ex]]); nin = len(rr_in)
SUN = (4021.89, 2738.66); RS = 446.15
lum = lambda C: 0.2126 * C[0] + 0.7152 * C[1] + 0.0722 * C[2]
# màscara de la Lluna i de la protuberància a la reixa polar interior
R, T = np.meshgrid(rr_in, th, indexing='ij'); X = SUN[0] + R * RS * np.cos(T); Y = SUN[1] - R * RS * np.sin(T)
r_moon = np.hypot(X - MOON_C[0], Y - MOON_C[1]) / MOON_R
fora_lluna = r_moon > 1.02
no_prot = ~((th_deg > 160) & (th_deg < 178))[None, :] | (R > 1.12)
okmask = fora_lluna & no_prot
def med_masked(A):           # mediana per anell només on okmask
    A = np.where(okmask, A, np.nan); return np.nanmedian(A, axis=1)
def pct_masked(A, p):
    A = np.where(okmask, A, np.nan); return np.nanpercentile(A, p, axis=1)
def fillnan(a):
    a = a.copy(); ok = np.isfinite(a)
    if not ok.all(): a[~ok] = np.interp(np.flatnonzero(~ok), np.flatnonzero(ok), a[ok])
    return a
Lbar, P50, P95 = {}, {}, {}
for i in range(nL):
    Li = d[f'L{i}']; mx = np.max(Li, axis=0)
    Lbar[i] = fillnan(np.concatenate([med_masked(lum(Li)), e[f'p50_{i}'][sel_ex]]))
    P50[i] = fillnan(np.concatenate([med_masked(mx), e[f'p50_{i}'][sel_ex]]))
    P95[i] = fillnan(np.concatenate([pct_masked(mx, 95), e[f'p95max_{i}'][sel_ex]]))
# suavitzat lleu dels perfils (σ = 2 mostres = 0,01 R☉ a la reixa interior) perquè el soroll de les medianes no entri als pesos
for Dd in (Lbar, P50, P95):
    for k in Dd:
        a_ = Dd[k].copy(); a_[:nin] = ndi.gaussian_filter1d(a_[:nin], 2.0, mode='nearest'); Dd[k] = a_
# perfil V3 (compost reproduït amb les màscares radialitzades de V3) fora de la Lluna + exterior del merged
mer = np.load('v3/merged_rgb.npy', mmap_mode='r')
thE = np.deg2rad(np.arange(0, 360, 1.0)); Rm, Tm = np.meshgrid(rr_ex[sel_ex], thE, indexing='ij')
Xm = SUN[0] + Rm * RS * np.cos(Tm); Ym = SUN[1] - Rm * RS * np.sin(Tm); inside = (Xm >= 460) & (Xm < 7416) & (Ym >= 466) & (Ym < 5102)
mv = np.stack([ndi.map_coordinates(np.asarray(mer[..., ch], np.float32) / 65535., [Ym, Xm], order=1, mode='constant', cval=np.nan) for ch in range(3)]); mv[:, ~inside] = np.nan
T3_ex = fillnan(np.nanmedian(lum(mv), axis=1))
T3 = fillnan(np.concatenate([med_masked(lum(c['C3'])), T3_ex])); T3r = fillnan(np.concatenate([med_masked(lum(c['Cr'])), T3_ex]))
# ---- validesa
vis = [meta['layers'][i]['visible'] for i in range(nL)]
ladder = [i for i in range(1, nL)]            # V4: totes les capes (04 i 03 incloses, visibles)
u, r_on = {}, {}
for i in ladder:
    ok = (P95[i] <= P95_MAX) & (P50[i] <= P50_MAX)
    bad = np.flatnonzero(~ok & (rr >= 1.0)); r_on[i] = rr[bad[-1] + 1] if len(bad) else 1.0
    if i in (1, 2): r_on[i] = 0.9                     # Capa 4 i Capa 5: sempre (al limbe no hi ha res millor)
    x = np.clip((rr - (r_on[i] - RAMP_LO)) / RAMP_W, 0, 1); u[i] = x * x * (3 - 2 * x)
    if i in (1, 2): u[i] = np.ones_like(rr)
print('radi d\'entrada (validesa) per capa:', {meta['layers'][i]['name'][:8]: round(float(r_on[i]), 3) for i in ladder})
# ---- abast: composició estàndard de dalt a baix amb màscares u_k (forma producte)
Wraw = {}
prod = np.ones_like(rr)
for i in reversed(ladder[1:]):
    Wraw[i] = u[i] * prod; prod = prod * (1 - u[i])
L0 = Lbar[ladder[0]]
B_reach = sum(Wraw[i] * Lbar[i] for i in ladder[1:]) + (1 - sum(Wraw[i] for i in ladder[1:])) * L0
lnr = np.log(rr)
def smooth_lnr(y, sig):
    g = np.linspace(lnr[0], lnr[-1], 4000); yi = np.interp(g, lnr, y)
    return np.interp(lnr, g, ndi.gaussian_filter1d(yi, sig / (g[1] - g[0]), mode='nearest'))
jp = np.searchsorted(rr, R_PEAK)
T3r_ext = T3r.copy(); T3r_ext[:jp] = T3r[jp]                      # cap a dins del pic: constant (no contamina)
T_des = smooth_lnr(T3r_ext, SIG_T)
T = np.minimum(T_des, B_reach)
T[jp:] = np.minimum.accumulate(T[jp:]); T[:jp] = B_reach[:jp]     # dins del pic: tot el que es pugui (Capa 5)
# perfil objectiu: (a) corba rim→genoll→altiplà = mínim acumulat de B_reach des del limbe, arrodonida PER SOTA amb filtre de mínim
# + gaussiana (queda sota B_reach); (b) unió suau amb el perfil V3 a fora per mínim suau en ln.
W_KNEE = float(os.environ.get('W_KNEE', 0.04)); SIG_KNEE = float(os.environ.get('SIG_KNEE', 0.03)); K_SOFT = float(os.environ.get('K_SOFT', 0.15))
P_hard = np.minimum.accumulate(np.where(rr >= R_PEAK, B_reach, B_reach[jp]))
g_u = np.linspace(lnr[0], lnr[-1], 4000); dg = g_u[1] - g_u[0]
Pu = np.interp(g_u, lnr, P_hard)
Pu = ndi.minimum_filter1d(Pu, size=int(round(2 * W_KNEE / dg)) | 1, mode='nearest')
Pu = ndi.gaussian_filter1d(Pu, SIG_KNEE / dg, mode='nearest')
P_soft = np.minimum(np.interp(lnr, g_u, Pu), B_reach)
def softmin_ln(*curves):
    L = np.stack([np.log(np.maximum(c_, 1e-6)) for c_ in curves]); m0 = L.min(0)
    return np.exp(m0 - K_SOFT * np.log(np.sum(np.exp(-(L - m0) / K_SOFT), axis=0)))
T = softmin_ln(P_soft, T_des)
T = np.minimum(T, B_reach); T[jp:] = np.minimum.accumulate(T[jp:]); T[:jp] = T[jp]
j_join = int(np.flatnonzero(np.isclose(P_hard, P_hard[np.searchsorted(rr, 1.6)]))[0])
print(f'nivell de l\'altiplà (coll d\'ampolla) {P_hard[j_join]:.4f} a r={rr[j_join]:.3f}')
# ---- pesos per PARELLES ADJACENTS de l'escala de brillantor (Capa 4 < Capa 5 < 09 < … < 05): a cada r, T cau entre
# dues capes consecutives (en mediana) i es reparteix entre elles; la més clara mai no passa del seu cap de validesa u_k.
W = {i: np.zeros_like(rr) for i in ladder}
viol = np.zeros_like(rr)
for jr in range(len(rr)):
    Ls = [Lbar[i][jr] for i in ladder]; t = T[jr]
    if t <= Ls[0]:
        W[ladder[0]][jr] = 1.0; continue
    placed = False
    for n in range(len(ladder) - 1):
        if Ls[n] <= t <= Ls[n + 1]:
            wb = (t - Ls[n]) / max(Ls[n + 1] - Ls[n], 1e-9)
            cap = u[ladder[n + 1]][jr]
            if wb > cap: viol[jr] = wb - cap; wb = cap
            W[ladder[n + 1]][jr] = wb; W[ladder[n]][jr] = 1 - wb; placed = True; break
    if not placed:      # T per sobre de la capa més clara: tot a la més clara (limitada pel cap) i la resta a la següent
        top = ladder[-1]; W[top][jr] = u[top][jr]; W[ladder[-2]][jr] = 1 - u[top][jr]
# camp llunyà (r > 2,0→2,6): la capa més llarga vàlida (05) atenuada amb Capa 4 (negre), que és la millor relació S/N;
# es barreja suaument amb les parelles adjacents perquè a l'interior el que mana és la suavitat del mescla
# camp llunyà: el senyal el posen les capes llargues vàlides (03, 04, 05) amb quotes ∝ nombre de fotogrames apilats
# (S/N òptim si domina el soroll fotònic del cel), i la resta va a Capa 4 (la capa fosca real) per deixar el perfil a T
NFR = {7: 2, 8: 4, 9: 2}                                    # 05 apilat2, 04 apilat4, 03 apilat2
Wb = {i: np.zeros_like(rr) for i in ladder}
share = {i: NFR[i] * u[i] for i in NFR}
ssum = sum(share.values())
for i in share: share[i] = np.where(ssum > 1e-9, share[i] / np.maximum(ssum, 1e-9), 0.0)
B_S = sum(share[i] * Lbar[i] for i in share)
L0_ = Lbar[ladder[0]]
c_ff = np.where(ssum > 1e-9, np.clip((T - L0_) / np.maximum(B_S - L0_, 1e-9), 0, 1), 0.0)
for i in share: Wb[i] = share[i] * c_ff
Wb[ladder[0]] = 1 - sum(Wb[i] for i in share)
# on encara no hi ha cap capa llarga vàlida (ssum≈0) el camp llunyà no s'aplica (s_ff hi és 0 de tota manera)
s_ff = np.clip((rr - 2.0) / 0.6, 0, 1); s_ff = s_ff * s_ff * (3 - 2 * s_ff)
for i in ladder: W[i] = (1 - s_ff) * W[i] + s_ff * Wb[i]
# suavitzat lleu dels pesos (σ = 0,01 R☉) i renormalització
for i in ladder:
    a_ = W[i].copy(); a_[:nin] = ndi.gaussian_filter1d(a_[:nin], 2.0, mode='nearest'); W[i] = np.clip(a_, 0, None)
Ssum = sum(W[i] for i in ladder)
for i in ladder: W[i] = W[i] / Ssum
C4prof = sum(W[i] * Lbar[i] for i in ladder)
print('violacions del cap de validesa (pes demanat − cap): màx', float(viol.max()), ' | |C4prof−T| màx', float(np.abs(C4prof - T)[rr > 1.0].max()))
# ---- màscares (de dalt a baix)
m = {}; rem = np.ones_like(rr)
for i in reversed(ladder):
    m[i] = np.where(rem > 1e-6, np.clip(W[i] / np.maximum(rem, 1e-6), 0, 1), 0.0)
    rem = rem * (1 - m[i])
m[ladder[0]] = np.ones_like(rr)
np.savez('v4/disseny.npz', rr=rr, T=T, T3=T3, T3r=T3r, B_reach=B_reach, C4prof=C4prof, ladder=np.array(ladder),
         **{f'W{i}': W[i] for i in ladder}, **{f'm{i}': m[i] for i in ladder}, **{f'u{i}': u[i] for i in ladder}, **{f'L{i}': Lbar[i] for i in range(nL)},
         MOON_C=np.array(MOON_C), MOON_R=MOON_R, SUN=np.array(SUN), RS=RS)
print('\n  r    T_V3   T_obj  C4prof B_reach |  pesos:', ' '.join(f'{meta["layers"][i]["name"][:6]:>7s}' for i in ladder), ' | màscares')
for r in [1.0, 1.02, 1.04, 1.06, 1.08, 1.1, 1.12, 1.14, 1.16, 1.18, 1.2, 1.24, 1.28, 1.32, 1.36, 1.4, 1.45, 1.5, 1.55, 1.6, 1.7, 1.8, 1.9, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0, 3.5, 4.0, 5, 6, 8, 9.5]:
    j = int(np.argmin(np.abs(rr - r)))
    print(f'{rr[j]:5.2f} {T3[j]:6.3f} {T[j]:6.3f} {C4prof[j]:6.3f} {B_reach[j]:6.3f}  | ' + ' '.join(f'{W[i][j]:7.3f}' for i in ladder) + '  | ' + ' '.join(f'{m[i][j]:5.2f}' for i in ladder))
# ---- compost polar V4 i diagnòstic
C4 = np.zeros_like(d['L0'])
for i in ladder: C4 += W[i][:nin, None][None] * d[f'L{i}']
C3, Cr = c['C3'], c['Cr']
gam = lambda e_: np.interp(e_, [0.004, 0.1, 0.2, 0.27, 0.31, 0.38, 0.45, 0.53, 0.61, 0.69, 0.76, 0.82, 0.92, 0.99], [1.05, 1.15, 1.06, 0.83, 0.68, 0.74, 0.67, 0.61, 0.53, 0.45, 0.35, 0.28, 0.17, 0.04])
print('\nestructura azimutal (desv. del log-lum per anell, fora de la Lluna): V3 | radial-V3 | V4;  γ-mix efectiu (pes·γ_local de la mediana)')
for r in [1.02, 1.05, 1.1, 1.15, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 2.0, 2.5, 3.0]:
    j = int(np.argmin(np.abs(rr_in - r)))
    sd = lambda C: np.nanstd(np.where(okmask[j], np.log(np.maximum(lum(C)[j], 1e-4)), np.nan))
    g3 = sum(c['W3'][i][j].mean() * gam(Lbar[i][j]) for i in range(nL)); g4 = sum(W[i][j] * gam(Lbar[i][j]) for i in ladder)
    print(f'{r:4.2f}  {sd(C3):.3f} | {sd(Cr):.3f} | {sd(C4):.3f}    γ: V3 {g3:.2f}  V4 {g4:.2f}')
np.save('v4/C4_polar.npy', C4)
