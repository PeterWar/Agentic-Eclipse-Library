"""V97 (24-09 nit): còpia literal de la V88 (Vixen al marc de la Lluna) amb el mòdul v97_comu (sortida per V97_SORT; limb_frames regenerats).
e1 · Earthshine V88 des de zero: apilat lineal de la Lluna al seu propi marc (Claude, 23-09-2026).
Per què: a la capa de la Lluna de la V87 (225, «Earthshine V86») la vora exterior del disc (1–11 px dins del limbe) porta arcs paral·lels al
limbe i textura (marques liles de Pere). Arran del limbe, els fotogrames llargs hi són saturats a pedaços (els de 10 s només tenen el 54–57 %
dels píxels vàlids a −12..−2 px, i els que sobreviuen són els foscos: una selecció), i la Lluna s'hi mou 2,8 px durant una exposició de 10 s.
Fonts: els 67 fotogrames Vixen calibrats de la caixa de la Lluna (4-RESULTATS/v85…/limb_frames: numerador i pes per canal, CFA natiu
equilibrat, al llenç del Sol; pes 0 on el píxel satura), amb la distància de cada píxel al limbe del model de cada fotograma.
Regles:
  fotogrames: exposició ≥ 0,25 s (14: 2×0,25, 4×0,5, 2×1, 3×2, 3×10 s);
  registre: cada fotograma es desplaça perquè la seva Lluna (centre del cercle del model) caigui on la trajectòria mesurada la posa a t = 18,43 s,
      l'instant de la Lluna de Pere (el centre de la seva Lluna és a 0,36 px d'aquesta trajectòria);
  pes = pes de la cadena × erosió de 4 px de la validesa (cap píxel al costat d'un de saturat)
        × rampa de saturació: per a cada azimut (1°), el primer radi (des de dins) on el fotograma deixa de tenir el 99,5 % dels píxels vàlids;
          pes ple fins a 7 px abans i zero a 3 px abans (cap barreja de píxels supervivents d'una zona saturada)
        × guarda del moviment: zero a menys de (arrossegament/2 + 1) px del limbe observat del fotograma, rampa de 2 px;
  per canal: E_c = Σ desplaçat(v·p) / Σ desplaçat(p) (interpolació bilineal normalitzada); després, guanys i matriu de color de la cadena.
Sortida: 4-RESULTATS/v88_20260923/E1_earthshine_lineal.npz (caixa de limb_frames) i E1_EARTHSHINE.json."""
from v97_comu import *
import os
import cv2
from scipy.ndimage import binary_erosion, minimum_filter1d, gaussian_filter1d
claim()
LF = V85D / 'limb_frames'; meta = json.loads((LF / 'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']
num = np.load(LF / 'numerator.npy', mmap_mode='r'); wt = np.load(LF / 'weight.npy', mmap_mode='r'); Dm = np.load(LF / 'distance_model.npy', mmap_mode='r')
geo = json.loads((SORT / 'A2_GEOMETRIA.json').read_text())['lluna_presentacio']; R = geo['R']; T_LLUNA = geo['instant_s']
RL = float(meta['radius_model']); DR = RL - R
EXP_MIN, EROSIO, MARGE_SAT, RAMPA_SAT = 0.25, 4, 3.0, 4.0
yy, xx = np.mgrid[by0:by1, bx0:bx1].astype(np.float64)
def centre(i):
    D = np.asarray(Dm[i]); s = (D > -8) & (D < 8); x = xx[s]; y = yy[s]
    A = np.c_[2 * x, 2 * y, np.ones_like(x)]; b = x ** 2 + y ** 2; sol, *_ = np.linalg.lstsq(A, b, rcond=None); return sol[0], sol[1]
C = np.array([centre(i) for i in range(len(fr))]); T = np.array([f['time'] for f in fr])
px_, py_ = np.polyfit(T, C[:, 0], 2), np.polyfit(T, C[:, 1], 2)
ct = np.array([np.polyval(px_, T_LLUNA), np.polyval(py_, T_LLUNA)]); vel = np.hypot(np.polyval(np.polyder(px_), T), np.polyval(np.polyder(py_), T))
res_traj = float(np.sqrt(np.mean((C[:, 0] - np.polyval(px_, T)) ** 2 + (C[:, 1] - np.polyval(py_, T)) ** 2)))
log(f'trajectòria: residu rms {res_traj:.3f} px; Lluna a t={T_LLUNA:.2f} s a ({ct[0]:.2f}, {ct[1]:.2f}); presentació ({geo["cx"]:.2f}, {geo["cy"]:.2f})')
EXP_MAX = float(os.environ.get('E1_EXP_MAX', '1e9')); SEL = [i for i, f in enumerate(fr) if EXP_MIN <= f['exposure'] <= EXP_MAX]   # V97: E1_EXP_MAX per provar sense els 10 s (arrossegament de 2,7 px)
def ss(x, a, b): t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
disc = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * EROSIO + 1, 2 * EROSIO + 1)).astype(bool)
Hb, Wb = by1 - by0, bx1 - bx0
N = np.zeros((Hb, Wb, 3)); Wt = np.zeros((Hb, Wb, 3)); rep = dict(fotogrames=[], trajectoria_residu_rms_px=res_traj, lluna_t=T_LLUNA, centre_desti=ct.tolist())
for i in SEL:
    f = fr[i]; Do = np.asarray(Dm[i]) + DR; thf = (np.degrees(np.arctan2(-(yy - C[i, 1]), xx - C[i, 0])) + 360) % 360; ib = thf.astype(int) % 360
    w3 = np.stack([np.asarray(wt[i, :, :, c], np.float64) for c in range(3)], -1); val = (w3 > 0).all(-1)
    val_e = binary_erosion(val, structure=disc, border_value=1)
    # radi de saturació per azimut (comú als tres canals): primer calaix de 0,5 px (des de −80 px cap enfora) amb menys del 99,5 % de píxels vàlids
    zona = (Do > -80) & (Do <= -0.5); Dsat = np.full(360, 10.0)
    kb = np.clip(((Do + 80) / 0.5).astype(int), 0, 159)
    for a in range(360):
        q = zona & (ib == a)
        if not q.any(): continue
        tot = np.bincount(kb[q], minlength=160); ok = np.bincount(kb[q], weights=val[q].astype(float), minlength=160)
        frac = np.where(tot > 0, ok / np.maximum(tot, 1), 1.0); dol = np.flatnonzero((frac < 0.995) & (tot > 3))
        Dsat[a] = (dol[0] * 0.5 - 80) if dol.size else 10.0     # cap calaix saturat fins al limbe: cap límit (només la guarda del moviment)
    Dsat = gaussian_filter1d(minimum_filter1d(Dsat, 3, mode='wrap'), 1, mode='wrap')
    f_sat = 1 - ss(Do, Dsat[ib] - MARGE_SAT - RAMPA_SAT, Dsat[ib] - MARGE_SAT)
    guarda = vel[i] * f['exposure'] / 2 + 1.0; f_mot = 1 - ss(Do, -guarda - 2.0, -guarda)
    fac = val_e * f_sat * f_mot
    dx, dy = ct[0] - C[i, 0], ct[1] - C[i, 1]; M = np.float32([[1, 0, dx], [0, 1, dy]])
    for c in range(3):
        v = np.where(w3[..., c] > 0, np.asarray(num[i, :, :, c], np.float64) / np.maximum(w3[..., c], 1e-30), 0); p = w3[..., c] * fac
        N[..., c] += cv2.warpAffine((v * p).astype(np.float32), M, (Wb, Hb), flags=cv2.INTER_LINEAR, borderValue=0)
        Wt[..., c] += cv2.warpAffine(p.astype(np.float32), M, (Wb, Hb), flags=cv2.INTER_LINEAR, borderValue=0)
    rep['fotogrames'].append(dict(nom=f['name'], t=f['time'], exposicio=f['exposure'], desplacament_px=[round(dx, 3), round(dy, 3)], guarda_px=round(guarda, 2),
                                  radi_saturacio_p5_p50_p95=np.percentile(Dsat, [5, 50, 95]).round(1).tolist(), pes_util_disc=float(fac[Do < -150].mean())))
    log(f"{f['name']} t {f['time']:.1f} exp {f['exposure']}: desplaçament ({dx:.2f}, {dy:.2f}), guarda {guarda:.1f} px, saturació p50 {np.median(Dsat):.1f} px")
E = np.where(Wt > 0, N / np.maximum(Wt, 1e-30), 0)
gain = np.array(meta['gain']); Mx = np.array(meta['matrix']); Ec = np.einsum('ij,...j->...i', Mx, E * gain)
# on arriba la dada, en coordenades de la Lluna de destinació
dL = np.hypot(xx - ct[0], yy - ct[1]) - R; thL = (np.degrees(np.arctan2(-(yy - ct[1]), xx - ct[0])) + 360) % 360
cob = {}
for x in [-20, -12, -8, -5, -3, -2, -1, 0]:
    q = np.abs(dL - x) < 0.5; cob[f'{x:+d}'] = dict(pes_mitja_G=float(Wt[..., 1][q].mean()), sense_dada=float((Wt[..., 1][q] <= 0).mean()))
rep['cobertura_per_distancia'] = cob
np.savez_compressed(SORT / 'E1_earthshine_lineal.npz', box=np.array([by0, by1, bx0, bx1]), E=Ec.astype(np.float32), E_natiu=E.astype(np.float32), W=Wt.astype(np.float32), centre=ct)
desa_json('E1_EARTHSHINE.json', rep); log('E1 fet · cobertura ' + json.dumps({k: round(v['sense_dada'], 3) for k, v in cob.items()}))
