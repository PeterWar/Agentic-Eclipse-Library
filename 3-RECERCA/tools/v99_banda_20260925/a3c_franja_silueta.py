"""a3c (V99 banda) · La selecció física per fotograma de l'a3b (V98), però amb la distància al limbe REAL de cada fotograma.
Per què (d16–d19, 25-09 vespre): el dèficit de vora «per sector» de la V98 era sobretot geometria. La Lluna observada no és el cercle del model:
el·lipse ~0,8 % (refracció diferencial amb el Sol baix) i centre desplaçat ~1,4 px, comuns a tots els fotogrames i estables en el temps
(D19_SILUETA_I_COLLAPSE.json). Amb D_real = D_obs − e(PA_j) les corbes de transmissió de tots els sectors i èpoques col·lapsen
(curts: −5…−16 % a 2 px, −1…−8 % a 3, 0…−4 % a 4). Les rampes 6→9 de la V98 cobrien l'error de geometria i a dalt hi perdien ~3,5 px de dada neta.
Què canvia respecte de l'a3b:
  · D_real = D_model + DR − e(PA_j), amb e(PA) la silueta comuna (D19_silueta.npz; A3C_SILUETA) i PA_j l'angle de posició respecte del centre
    del model d'aquell fotograma (cercle exacte: centre = p − (D+R_model)·∇D).
  · Rampes sobre D_real (A3C_RAMPES, JSON {classe: [lo, hi]}).
  · Opcional (A3C_TCORR = JSON {classe: {"D": [...], "lnT": [...]}}): cada fotograma es divideix per la seva transmissió de vora mesurada
    T_classe(D_real) (calibració comuna a tots els sectors, com un camp pla) i pesa pes·T² (variància inversa de V/T).
La resta (validesa, vora del domini, unió amb la fusió a 60–90 px, sortida) és la de l'a3b.
Ús: A3B_LF=<limb_frames_comuna> V97_SORT=<sortida> V97_FONTS=<d4 sources> A3C_SILUETA=<D19_silueta.npz> A3C_RAMPES='{"curts":[3,5.5],...}' [A3C_TCORR=<json>] a3c_franja_silueta.py"""
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'v97_refundacio_20260924'))
from v97_comu import *
from v86_operadors import smoothstep
import cv2
from scipy.ndimage import maximum_filter1d, gaussian_filter1d
claim()
LF = Path(os.environ['A3B_LF']); LF = LF if LF.is_absolute() else ARREL / LF
meta = json.loads((LF / 'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']
num = np.load(LF / 'numerator.npy', mmap_mode='r'); wt = np.load(LF / 'weight.npy', mmap_mode='r'); Dm = np.load(LF / 'distance_model.npy', mmap_mode='r')
geo = json.loads((RES / 'lineal_v97_franja/A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = geo['cx'], geo['cy'], geo['R']
DR = float(meta['radius_model']) - R
RAMPES = {k: tuple(v) for k, v in json.loads(os.environ.get('A3C_RAMPES', '{"curts": [3.0, 5.5], "mitjans": [3.0, 5.0], "llargs": [3.0, 5.5]}')).items()}
_sil = np.load(os.environ['A3C_SILUETA']); SIL_PA = np.asarray(_sil['pa'], np.float64); SIL_E = np.asarray(_sil['e'], np.float64)
TCORR = json.loads(Path(os.environ['A3C_TCORR']).read_text()) if os.environ.get('A3C_TCORR') else None
def lnT(c_, D):
    if TCORR is None: return np.zeros_like(D)
    t_ = TCORR[c_]; return np.interp(D, t_['D'], t_['lnT'], left=t_['lnT'][0], right=0.0)
def classe(e): return 'curts' if e <= 1 / 800 else ('mitjans' if e <= 1 / 50 else 'llargs')
yy, xx = np.mgrid[by0:by1, bx0:bx1]; rL = np.hypot(xx - cx, yy - cy); dL = (rL - R).astype(np.float32)
th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
hb, wb = by1 - by0, bx1 - bx0; nF = len(fr); Rm_ = float(meta['radius_model'])
Ns = np.zeros((hb, wb, 3), np.float64); Ws = np.zeros((hb, wb, 3), np.float64); NF = np.zeros((hb, wb), np.int16); Wraw = np.zeros((hb, wb), np.float64)
S_classe = {k: np.zeros((hb, wb), np.float32) for k in RAMPES}; DREAL_MAX = np.full((hb, wb), -99.0, np.float32)
for j in range(nF):
    Dj = np.asarray(Dm[j], np.float64); gy_, gx_ = np.gradient(Dj); iy_, ix_ = hb // 2, wb - 100
    cxj = ix_ + bx0 - (Dj[iy_, ix_] + Rm_) * gx_[iy_, ix_]; cyj = iy_ + by0 - (Dj[iy_, ix_] + Rm_) * gy_[iy_, ix_]
    PAj = (np.degrees(np.arctan2(-(yy - cyj), xx - cxj)) + 360) % 360
    Dr = (Dj + DR - np.interp(PAj.ravel(), SIL_PA, SIL_E, period=360).reshape(hb, wb)).astype(np.float32)
    c_ = classe(fr[j]['exposure']); lo, hi = RAMPES[c_]; s = smoothstep(Dr, lo, hi).astype(np.float32)
    T_ = np.exp(lnT(c_, Dr)).astype(np.float64); T_ = np.where(s > 0, T_, 1.0)
    for c in range(3):
        w = np.asarray(wt[j, :, :, c], np.float64) * s * T_ ** 2; Ns[..., c] += np.asarray(num[j, :, :, c], np.float64) * s * T_; Ws[..., c] += w
        if c == 1:
            NF += ((w > 0)).astype(np.int16); S_classe[c_] += w.astype(np.float32); Wraw += np.asarray(wt[j, :, :, 1], np.float64)
            DREAL_MAX = np.where(np.asarray(wt[j, :, :, 1]) > 0, np.maximum(DREAL_MAX, Dr), DREAL_MAX)
    if j % 10 == 0: log(f'fotograma {j + 1}/{nF}')
E = np.where(Ws > 0, Ns / np.maximum(Ws, 1e-30), 0).astype(np.float32)
omplerts = {}; te_canal = [Ws[..., c] > 0 for c in range(3)]
for c in (0, 2):     # desmosaic: només els píxels on aquest canal no té cap pes i el verd sí
    buit = (Ws[..., c] <= 0) & (Ws[..., 1] > 0); omplerts[c] = int(buit.sum())
    if buit.any():
        Nc = cv2.GaussianBlur(Ns[..., c].astype(np.float32), (0, 0), 0.8); Wc = cv2.GaussianBlur(Ws[..., c].astype(np.float32), (0, 0), 0.8)
        E[..., c] = np.where(buit & (Wc > 0), Nc / np.maximum(Wc, 1e-30), E[..., c]); te_canal[c] = te_canal[c] | (buit & (Wc > 0))
Mx = np.array(meta['matrix'], np.float32); gn = np.array(meta['gain'], np.float32); E = np.einsum('ij,...j->...i', Mx, E * gn).astype(np.float32)
curts = [i for i, f in enumerate(fr) if classe(f['exposure']) == 'curts']; _wc = np.asarray(wt[curts[0], ::7, ::7, 1]); W_CURT = float(np.median(_wc[_wc > 0]))
valid = (Ws[..., 1] >= 1.5 * W_CURT) & (NF >= 3) & (E[..., 1] > 0) & te_canal[0] & te_canal[2]
# vora del domini: per azimut, la distància a partir de la qual TOTS els píxels són vàlids (zona −40…+20 px); mai cap endins
NBZ = 1440; ibz = (th / 360 * NBZ).astype(int) % NBZ; zona = (dL > -40) & (dL < 20)
ordre = np.argsort(ibz[zona]); ib_s = ibz[zona][ordre]; d_s = dL[zona][ordre]; v_s = valid[zona][ordre]; talls = np.searchsorted(ib_s, np.arange(NBZ + 1)); dmin = np.full(NBZ, np.nan)
for k in range(NBZ):
    dd_, vv_ = d_s[talls[k]:talls[k + 1]], v_s[talls[k]:talls[k + 1]]; dolents = dd_[~vv_]
    dmin[k] = (dolents.max() + 0.25) if dolents.size else (dd_.min() if dd_.size else np.nan)
ok_ = np.isfinite(dmin); dmin[~ok_] = np.interp(np.flatnonzero(~ok_), np.flatnonzero(ok_), dmin[ok_], period=NBZ)
DMIN = gaussian_filter1d(maximum_filter1d(dmin, 5, mode='wrap'), 4, mode='wrap'); DMIN = np.maximum(DMIN, maximum_filter1d(dmin, 3, mode='wrap')).astype(np.float32)
llisa = dL >= DMIN[ibz]
forats = int((llisa & ~valid & (dL < 20)).sum())
domini_E = llisa & valid & (dL >= 0)   # dins del disc de presentació, a la dreta, hi ha dada neta de final de totalitat (la Lluna ja no hi era): és la
# cromosfera i la corona de prop de C3, que a l'instant de la Lluna mostrada és darrere la Lluna; fora del domini perquè no entri als operadors
# nivell i unió amb la fusió: el mateix apilat lluny del limbe → un factor constant per canal (mediana a 60–120 px) i β 1 → 0 a 60–90 px
fonts = dict(G=np.load(FONTS / 'base_G.npy', mmap_mode='r'), F=np.load(FONTS / 'fusion_starless.npy', mmap_mode='r'), V=np.load(FONTS / 'vixen_starless.npy', mmap_mode='r'))
sup = np.load(FONTS / 'support.npy')[by0:by1, bx0:bx1]
D1_, D2_ = 60.0, 90.0
beta = ((1 - smoothstep(dL, D1_, D2_)) * domini_E).astype(np.float32)
anell = domini_E & sup & (dL >= D1_) & (dL <= 120)
def cte(font, e):
    ok = anell & (font > 0) & (e > 0); q = font[ok] / e[ok]; return float(np.median(q)), float(np.percentile(q, 16)), float(np.percentile(q, 84))
out = {}; esc = {}
Gb = np.asarray(fonts['G'][by0:by1, bx0:bx1]).astype(np.float32); cG = cte(Gb, E[..., 1]); esc['c_G'] = cG
out['G'] = np.where(beta > 0, (1 - beta) * Gb + beta * cG[0] * E[..., 1], Gb).astype(np.float32)
Fb = np.asarray(fonts['F'][by0:by1, bx0:bx1]).astype(np.float32); Fn = Fb.copy()
for c in range(3):
    cc = cte(Fb[..., c], E[..., c]); esc[f'c_F{c}'] = cc; Fn[..., c] = np.where(beta > 0, (1 - beta) * Fb[..., c] + beta * cc[0] * E[..., c], Fb[..., c])
out['F'] = Fn
Vb = np.asarray(fonts['V'][by0:by1, bx0:bx1, 1]).astype(np.float32); cV = cte(Vb, E[..., 1]); esc['c_V'] = cV
out['V'] = np.where(beta > 0, (1 - beta) * Vb + beta * cV[0] * E[..., 1], Vb).astype(np.float32)
# domini nou de la caixa: on hi ha dada neta (E) a menys de 90 px del limbe; més enllà, el suport de la d4 (tal com era)
domini = np.where(dL < D2_, domini_E, sup & (rL > R))
dins_franja = beta > 0          # on la dada és la nova (la Sony no hi entra: a la caixa el pes de la Vixen ja és 1)
# comprovacions: fusió/nova a 60–120 px (ha de ser plana) i perfil del dèficit residual per distància (mediana ln(E/E_ref) no es pot sense referència:
# es dona el nombre de fotogrames i el pes per distància i azimut, que diuen on la dada és prima)
chk = {}
for d0, d1 in [(-10, 0), (0, 3), (3, 6), (6, 10), (10, 20), (20, 40), (40, 60), (60, 90), (90, 120)]:
    s_ = domini_E & (dL >= d0) & (dL < d1)
    chk[f'{d0}..{d1}'] = dict(px=int(s_.sum()), fotogrames_p50=float(np.median(NF[s_])) if s_.any() else None,
                               ln_fusio_sobre_nova_p16_50_84=(np.percentile(np.log(Gb[s_ & (Gb > 0)] / (cG[0] * E[..., 1][s_ & (Gb > 0)])), [16, 50, 84]).round(4).tolist() if (s_ & (Gb > 0)).sum() > 100 else None))
dmin_az = {f'{a}': round(float(DMIN[int(a / 360 * NBZ)]), 2) for a in range(0, 360, 15)}
np.savez_compressed(SORT / 'A3C_franja_silueta.npz', DREAL_MAX=DREAL_MAX, box=np.array([by0, by1, bx0, bx1]), G=out['G'], F=out['F'], V=out['V'], domini=domini, dins_franja=dins_franja,
                    beta=beta, E=E, NF=NF, DMIN=DMIN, centre=np.array([cx, cy, R]), domini_E=domini_E)
rep = dict(silueta=os.environ['A3C_SILUETA'], tcorr=os.environ.get('A3C_TCORR'), limb_frames=str(LF.relative_to(ARREL)), fonts=str(FONTS.relative_to(ARREL)) if str(FONTS).startswith(str(ARREL)) else str(FONTS), rampes_D_obs_px=RAMPES,
           DR_px=DR, W_CURT=W_CURT, desmosaic_px_omplerts={'R': omplerts[0], 'B': omplerts[2]}, unio_fusio_px=[D1_, D2_], escales=esc,
           vora_domini=dict(azimuts=NBZ, DMIN_per_azimut=dmin_az, p5_p50_p95=np.percentile(DMIN, [5, 50, 95]).round(2).tolist(), forats_dins_la_corba=forats),
           per_distancia=chk, domini_caixa=int(domini.sum()))
desa_json('A3C_FRANJA_SILUETA.json', rep); log('A3C fet · DMIN ' + json.dumps(dmin_az) + ' · c_G ' + json.dumps(cG))
