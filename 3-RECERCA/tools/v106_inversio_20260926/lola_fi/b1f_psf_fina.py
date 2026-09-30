"""b1f (V106, «LOLA fi», Claude, 26-09-2026) · Còpia de la b1 amb la GEOMETRIA FINA (geom_fina.py): D per component de la PSF (relleu LOLA-64
suavitzat a 1,25 px per al nucli i 2,5 px per a l'ala), centre i radi mesurats a la vora de cada fotograma; δ es manté lliure com a control
(ha de sortir ≈ 0). Sortida a lola_fi/b1f{B1F_TAG}/.
(Origen b1) · Transmissió de vora de cada fotograma amb la vora REAL de LOLA, i calibratge de la PSF.
Per a cada fotograma j: la distància al seu limbe real, D_j(x) = D_model_j(x) + DR − e_o2(PA_j) − r_lola(PA_j), on e_o2 és la silueta
d'ordre 2 de la V99 (centre, el·lipse per refracció) i r_lola el relleu de LOLA sense el seu propi ordre 2 (angle celeste = angle del llenç − θN).
Veritat: la corona del règim net (fotogrames que veuen el píxel a D ≥ 6 px, pes smoothstep 6→9), SENSE el fotograma j (deixa'n un fora).
T_obs = V_j / (g_j · veritat) als píxels a −2…8 px del limbe del fotograma; g_j de 10–20 px. Model: T = Φ_PSF(D − δ·n̂) amb PSF = (1−f)·G(σ) + f·G(σ_a),
δ = desplaçament del centre del fotograma (2 paràmetres), per fotograma. Ajust en sectors d'entrenament i prova en sectors i fotogrames reservats.
Canal: G de càmera (abans de la matriu). Sortides a 4-RESULTATS/v106_inversio_20260926/b1/."""
import os, sys, json, time, numpy as np
from pathlib import Path
from scipy.ndimage import gaussian_filter1d
from scipy.optimize import least_squares
from scipy.special import erf
R0 = Path.home() / 'Desktop/Eclipse 2026'
HF = Path(__file__).resolve().parent
import sys as _s; _s.path.insert(0, str(HF)); from geom_fina import G
LF = Path(os.environ.get('V105_LF', str(R0 / '4-RESULTATS/v106_inversio_20260926/limb_frames_sense_llindar')))
O = HF / ('b1f' + os.environ.get('B1F_TAG', '')); O.mkdir(parents=True, exist_ok=True)
VARIANT = os.environ.get('B1F_VARIANT', 'lola'); SIG_CORE = 1.25; SIG_ALA = 2.5; DELTA_LLIURE = os.environ.get('B1F_DELTA', '1') == '1'
TH_N = G.thN                                                            # angle del nord celeste al llenç: ajust LOLA-64 ↔ vora observada (e4)
CANAL = int(os.environ.get('V106_CANAL', '1'))
meta = json.loads((LF / 'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']
num = np.load(LF / 'numerator.npy', mmap_mode='r'); wt = np.load(LF / 'weight.npy', mmap_mode='r'); Dm = np.load(LF / 'distance_model.npy', mmap_mode='r')
geo = json.loads((R0 / '4-RESULTATS/v97_refundacio_20260924/lineal_v97_franja/A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = geo['cx'], geo['cy'], geo['R']
Rm = float(meta['radius_model']); DR = Rm - R
sil = np.load(R0 / '4-RESULTATS/v99_banda_20260925/D21_silueta_o2.npz'); SPA = np.asarray(sil['pa'], float); SE = np.asarray(sil['e'], float)
def e_o2(a): return np.interp(np.asarray(a) % 360, SPA, SE, period=360)
hb, wb = by1 - by0, bx1 - bx0; yy, xx = np.mgrid[by0:by1, bx0:bx1]; nF = len(fr)
def centre(j):
    D = np.asarray(Dm[j], np.float64); gy, gx = np.gradient(D); iy, ix = hb // 2, wb - 100
    return ix + bx0 - (D[iy, ix] + Rm) * gx[iy, ix], iy + by0 - (D[iy, ix] + Rm) * gy[iy, ix]
C = np.array([centre(j) for j in range(nF)])
d_pres = np.hypot(xx - cx, yy - cy) - R; banda = (d_pres > -45) & (d_pres < 45)             # anell de treball al voltant del limbe
iy, ix = np.nonzero(banda); X = xx[iy, ix].astype(np.float64); Y = yy[iy, ix].astype(np.float64); npx = X.size
def Dfina(j, dxy=(0.0, 0.0)):
    cxj, cyj = C[j, 0], C[j, 1]; a = np.degrees(np.arctan2(-(Y - cyj), X - cxj)) % 360
    return G.dfina(j, X, Y, SIG_CORE, VARIANT), a
def Dala(j): return G.dfina(j, X, Y, SIG_ALA, VARIANT)
t0 = time.time(); V = np.zeros((nF, npx), np.float32); Wg = np.zeros((nF, npx), np.float32); DF = np.zeros((nF, npx), np.float32); AN = np.zeros((nF, npx), np.float32); DA = np.zeros((nF, npx), np.float32)
for j in range(nF):
    w = np.asarray(wt[j, :, :, CANAL])[iy, ix]; n = np.asarray(num[j, :, :, CANAL])[iy, ix]
    Wg[j] = w; V[j] = np.where(w > 0, n / np.maximum(w, 1e-30), 0); DF[j], AN[j] = Dfina(j); DA[j] = Dala(j)
print('dades', round(time.time() - t0, 1), 's', flush=True)
def ss(x, a, b): q = np.clip((x - a) / (b - a), 0, 1); return q * q * (3 - 2 * q)
S_net = np.zeros(npx); N_net = np.zeros(npx); NF = np.zeros(npx)
for j in range(nF):
    s = ss(DF[j], 6, 9) * Wg[j]; S_net += s; N_net += s * V[j]; NF += (s > 0)
exp_ = np.array([f['exposure'] for f in fr]); t_ = np.array([f['time'] for f in fr])
def classe(e): return 'curts' if e <= 1 / 800 else ('mitjans' if e <= 1 / 50 else 'llargs')
cls = np.array([classe(e) for e in exp_])
def psf_T(D, s1, f, s2):
    return (1 - f) * 0.5 * (1 + erf(D / (np.sqrt(2) * s1))) + f * 0.5 * (1 + erf(D / (np.sqrt(2) * s2)))
res = []; MOD = {}
for j in range(nF):
    s = ss(DF[j], 6, 9) * Wg[j]; Sm = S_net - s; Nm = N_net - s * V[j]; nf = NF - (s > 0)
    ver = np.where((Sm > 0) & (nf >= 3), Nm / np.maximum(Sm, 1e-30), np.nan)
    ok = (Wg[j] > 0) & np.isfinite(ver) & (ver > 0)
    far = ok & (DF[j] >= 10) & (DF[j] < 20)
    if far.sum() < 2000: continue
    g = np.median(V[j][far] / ver[far])
    zona = ok & (DF[j] > -2.5) & (DF[j] < 8)
    if zona.sum() < 3000: continue
    To = V[j][zona] / (g * ver[zona]); a = AN[j][zona]; Xz = X[zona]; Yz = Y[zona]
    sat = np.median(To[DF[j][zona] > 4]) < 0.9                                        # saturat arran del limbe
    par = np.floor(a / 15).astype(int) % 2 == 0                                        # entrenament: sectors de 15° parells; prova: senars
    cxj, cyj = C[j]
    D1z = DF[j][zona].astype(np.float64); D2z = DA[j][zona].astype(np.float64); ca = np.cos(np.radians(a)); sa = np.sin(np.radians(a))
    def model(p, sel):
        dx, dy, s1, f, s2 = p; sh = dx * ca[sel] - dy * sa[sel]                   # desplaçament del centre (dx, dy; y avall) → la vora avança sh
        D1 = D1z[sel] - sh; D2 = D2z[sel] - sh
        return (1 - f) * 0.5 * (1 + erf(D1 / (np.sqrt(2) * s1))) + f * 0.5 * (1 + erf(D2 / (np.sqrt(2) * s2)))
    def resid(p): r = model(p, par) - To[par]; return np.clip(r, -1, 1)
    try:
        lb = [-3, -3, 0.3, 0.0, 1.5] if DELTA_LLIURE else [-1e-6, -1e-6, 0.3, 0.0, 1.5]; ub = [3, 3, 4.0, 0.8, 20.0] if DELTA_LLIURE else [1e-6, 1e-6, 4.0, 0.8, 20.0]
        sol = least_squares(resid, [0, 0, 1.2, 0.3, 2.5], bounds=(lb, ub), loss='soft_l1', f_scale=0.05)
    except Exception as ex:
        print('falla', j, ex); continue
    p = sol.x; Tm = model(p, np.ones(To.size, bool)); Dz = DF[j][zona] - (p[0] * np.cos(np.radians(a)) - p[1] * np.sin(np.radians(a))) * 0
    D_aj = D1z - (p[0] * ca - p[1] * sa)
    row = dict(j=j, nom=fr[j]['name'], t=round(t_[j], 2), exp=exp_[j], classe=cls[j], saturat=bool(sat), g=float(g), dx=float(p[0]), dy=float(p[1]), s1=float(p[2]), f=float(p[3]), s2=float(p[4]), n=int(zona.sum()))
    for lo, hi in [(0.5, 1.0), (1.0, 1.5), (1.5, 2.0), (2.0, 3.0), (3.0, 4.0), (4.0, 6.0)]:
        for nom, sel in (('entr', par), ('prova', ~par)):
            m = sel & (D_aj >= lo) & (D_aj < hi)
            if m.sum() >= 200:
                row[f'{nom}_{lo}-{hi}'] = float(np.median(To[m]) / np.median(Tm[m]) - 1)          # biaix del model (mediana)
                row[f'{nom}_{lo}-{hi}_rms'] = float(np.std(To[m] / np.maximum(Tm[m], 1e-3) - 1))
    res.append(row); MOD[j] = p
    print(j, fr[j]['name'], cls[j], 't', round(t_[j], 1), 'sat' if sat else '', 'σ', round(p[2], 2), 'f', round(p[3], 2), 'σa', round(p[4], 1), 'δ', round(p[0], 2), round(p[1], 2),
          ' prova 1–1,5:', round(row.get('prova_1.0-1.5', np.nan) * 100, 1), '% 1,5–2:', round(row.get('prova_1.5-2.0', np.nan) * 100, 1), '% 2–3:', round(row.get('prova_2.0-3.0', np.nan) * 100, 1), '%', flush=True)
(O / f'B1_PSF_LOLA_canal{CANAL}.json').write_text(json.dumps(dict(nord=G.thN, canal=CANAL, geometria='lola_fi/GEOMETRIA_FINA.npz', variant=VARIANT, fotogrames=res), indent=1, default=float))
print('fet', round(time.time() - t0, 1), 's')
