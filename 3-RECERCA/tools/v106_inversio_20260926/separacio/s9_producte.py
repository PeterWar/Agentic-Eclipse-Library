"""s9 (V106 · Separació, Claude, 26-09-2026) · PRODUCTE: el detall de corona net de relleu, Ĉ, de la inversió conjunta sobre la dada real,
al format de DELTA_sigc32.npz (c1 de la V105) perquè m1_fraccio_lunar.py i c2_capa_detall.py (c2b) el llegeixin:
  delta  = Ĉ (tots els fotogrames útils; 0 on cap fotograma no veu el píxel)      pes = Σ pesos (0 = sense observació)
  h125/p125   = Ĉ(S1)  i  hcurts/pcurts = Ĉ(S2): dues inversions INDEPENDENTS (conjunts de fotogrames disjunts) → la ρ de la c2
  hA/pA = grup A (0–10) netejat amb la Λ de S1;  hB/pB = grup B (13–18) netejat amb la Λ de S2 (cap soroll compartit) → la prova m1
  centres = centre lunar de cada fotograma;  dgrid, nth, centre: els de la c1 (d −4…40, pas 0,25; θ a 0,5 px d'arc).
També: lam (Λ̂ a la graella lunar), la Λ̂ avaluada a la Lluna de presentació (per veure què s'ha tret) i la mitjana ingènua (c1 sense rampa)."""
import numpy as np, sys, json, time, subprocess
from scipy.ndimage import gaussian_filter1d
from pipeline import Pipeline
cfg = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
TAG = sys.argv[2] if len(sys.argv) > 2 else 'final'
P = Pipeline(cfg); t0 = time.time()
R = P.proves(verbose=True); IT, I1, I2 = R['IT'], R['I1'], R['I2']; S = IT.S; i4 = S.i4; nd, nth = len(S.dg), S.nth
WT = IT.Wt.reshape(nd, nth); W1 = I1.Wt.reshape(nd, nth); W2 = I2.Wt.reshape(nd, nth)
# mitjana ingènua (mateixos pesos, sense Λ) i Λ̂ a la Lluna de presentació
lam = IT.lam.copy(); IT.lam[:] = 0; Cn, _ = IT.grup(P.fr); IT.lam[:] = lam
e_pres = np.interp(S.dth, S.SPA, S.SE, period=360); Dpres = S.dg[:, None] - e_pres[None, :]
apres = np.broadcast_to(S.dth[None, :], Dpres.shape)
Lpres = np.where(Dpres >= P.cfg['LO'], IT.avalua_lam(apres, Dpres), 0.0)
arcm = gaussian_filter1d(np.where(WT > 0, IT.C, 0), 64, axis=1, mode='wrap') / np.maximum(gaussian_filter1d((WT > 0).astype(float), 64, axis=1, mode='wrap'), 1e-6)
print('mitjana al llarg de l\'arc de Ĉ (σ 32 px), rms a d 0–6:', float(np.sqrt(np.mean(arcm[(S.dg >= 0) & (S.dg <= 6)][WT[(S.dg >= 0) & (S.dg <= 6)] > 0] ** 2))))
out = f'DELTA_sep_{TAG}.npz'
f32 = lambda x: np.asarray(x, np.float32)
np.savez_compressed(out, delta=f32(np.where(WT > 0, IT.C, 0)[i4:]), pes=f32(WT[i4:]), dgrid=f32(S.dg[i4:]), nth=nth, centre=np.array([S.cx, S.cy, S.R]),
    h125=f32(np.where(W1 > 0, I1.C, np.nan)[i4:]), p125=f32(W1[i4:]), hcurts=f32(np.where(W2 > 0, I2.C, np.nan)[i4:]), pcurts=f32(W2[i4:]),
    hA=f32(np.where(R['pA'] > 0, R['hA'], np.nan)[i4:]), pA=f32(R['pA'][i4:]), hB=f32(np.where(R['pB'] > 0, R['hB'], np.nan)[i4:]), pB=f32(R['pB'][i4:]),
    centres=np.array([[j, *S.C0[j]] for j in P.fr]), ingenu=f32(np.where(WT > 0, Cn, 0)[i4:]), lluna_pres=f32(Lpres[i4:]),
    lam=f32(IT.Lam()), lam_obs=IT.lam_obs, lam_D=IT.D0 + IT.dD * np.arange(IT.nD), lam_dphi=IT.dphi,
    rampa=np.array([P.cfg['LO'], P.cfg['LO']]), rampa_pa=np.array([]), cfg=json.dumps(P.cfg), S1=np.array(P.S1), S2=np.array(P.S2))
print('desat', out, round(time.time() - t0), 's', flush=True)
PY = '/Users/USUARI/.venvs/eines-ia-py312/bin/python'; M1 = '/Users/USUARI/Desktop/Eclipse 2026/3-RECERCA/tools/v105_limbe_20260926/m1_fraccio_lunar.py'
subprocess.run([PY, '-B', M1, out, f'M1_FRACCIO_LUNAR_{TAG}.json'], check=True)
