"""V34 · la composició curada a l'ORIGEN (research/149). Tres canvis, cap suavitzat:
  1. finestra de pes amb entrada GRADUAL (sostre: smoothstep del 35 al 85 % de la saturació) als dos trens;
  2. Sony: correcció de linealitat amb la corba mesurada (R33_linealitat_sensor.json), al pla abans del flat;
  3. fusió per variància (b3): Vixen sola fins a 2,0 R☉; de 2,0 enfora pesos ∝ 1/σ² mesurats; A i B per variància amb porta.
La resta (registre F1.3, flats, k, offsets c03, camps B1, flat Sony suavitzat, ρ, filtres) és la de la V32."""
import os, sys, json, time
from pathlib import Path
ROOT = Path('/Users/USUARI/Downloads/Eclipse 2026')
sys.path.insert(0, str(ROOT / 'research/tools/v32_arcs_20260907'))
import comu32
from comu32 import *          # H, W, CX, CY, RS, RUNS, COMMON_TO_FINAL, coords, smooth, gauss, normgauss, comu, f2, CAUF, FIX, V31P, Q, HC, WC, sha, log, savejson, coarse_coords, frame_groups, load_offsets, flat_ripple_correction
HERE34 = Path(__file__).resolve().parent
CAU34 = HERE34 / 'cau'; OUT34 = ROOT / 'output/v34_20260907'; VIS34 = OUT34 / 'lliurables/vistes'; REB34 = OUT34 / '4-rebuts'
IAOUT34 = Path('/Users/USUARI/Desktop/Eclipse 2026/IA/output/v34_20260907')
for p in (CAU34, VIS34, REB34, IAOUT34):
    p.mkdir(parents=True, exist_ok=True)
# ---- 1. finestra d'entrada gradual (declarada): terra igual (12→48 DN); sostre smoothstep 0,35·sat → 0,85·sat
RAMPA_INICI = 0.35 / 0.85      # fracció d'alt on comença la rampa (alt = 0,85·(sat−ped))
def finestra_v34(f, t, sat, ped):
    alt = f2.SOSTRE * (sat - ped)
    w = np.clip((f - f2.TERRA_DN) / (3.0 * f2.TERRA_DN), 0.0, 1.0)
    w *= 1.0 - smooth(f, RAMPA_INICI * alt, alt)
    return (w * t).astype(np.float32)
f2.finestra = finestra_v34
# ---- 2. linealitat de la Sony (corba mesurada, mediana de parelles i sectors; 0 fins a x 0,425)
_LIN = json.loads((ROOT / 'output/revisio_marques_v33_20260907/4-rebuts/R33_linealitat_sensor.json').read_text())
def _lut(tag):
    d = _LIN[tag]; xs = np.array(d['x_centres']); ys = np.array([0.0 if v is None else v / 100.0 for v in d['mediana_pct']])
    ys = np.where(xs <= 0.425, 0.0, ys)
    return xs, ys
LIN_X, LIN_LN = _lut('sony')
def lin_corr_sony(raw_sub, ped, sat):
    """Factor 1/L(x) a aplicar a (raw − dark): x = (raw − ped)/(sat − ped); ln L interpolat, extrapolat lineal per damunt de 0,975."""
    x = (raw_sub - ped) / (sat - ped)
    lnL = np.interp(x, LIN_X, LIN_LN, left=0.0, right=LIN_LN[-1] + (LIN_LN[-1] - LIN_LN[-2]) / (LIN_X[-1] - LIN_X[-2]) * 0.0)
    over = x > LIN_X[-1]
    if over.any():
        slope = (LIN_LN[-1] - LIN_LN[-2]) / (LIN_X[-1] - LIN_X[-2]); lnL = np.where(over, LIN_LN[-1] + slope * (x - LIN_X[-1]), lnL)
    return np.exp(-lnL).astype(np.float32)
_orig_plans = f2.Ctx.plans
def plans_v34(s, nom, e):
    """Com f2.Ctx.plans, amb la correcció de linealitat de la Sony sobre (raw − dark) abans del flat."""
    import rawpy
    with rawpy.imread(s.ruta[nom]) as r:
        raw = r.raw_image.astype(np.float32)
    dk = s.dark(e); out = {}; ped = s.cfg['pedestal_dn']; sat = s.cfg['saturacio_dn']
    for i in range(4):
        oy, ox = s.orig[i]; rs = raw[oy::2, ox::2]; ds = dk[oy::2, ox::2]
        if s.run.tren == 'sony':
            rs = ds + (rs - ds) * lin_corr_sony(rs, ped, sat)
        pl = comu.calibra_pla(rs, ds, s.flat[oy::2, ox::2], e, s.wb, s.mc, i)
        w = f2.finestra(raw[oy::2, ox::2] - ped, e, sat, ped) * s.valid[oy::2, ox::2]
        out[i] = (pl, w)
    return out
f2.Ctx.plans = plans_v34
REP_CANVIS = {'finestra': 'terra 12→48 DN igual; sostre smoothstep 0,35·sat → 0,85·sat (V32: lineal 0,70 → 0,85)', 'linealitat_sony': {'x': LIN_X.tolist(), 'ln_L': LIN_LN.tolist(), 'aplicacio': '(raw − dark)/L(x) abans del flat; x = (raw − ped)/(sat − ped)'}, 'vixen_linealitat': 'sense correcció (±0,13 % fins al sostre)'}
