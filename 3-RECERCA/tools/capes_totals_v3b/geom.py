"""Geometria comuna (coordenades LOCALS del ràster 6960x4640; llenç = local + (457,463))."""
import json, os, numpy as np
from pathlib import Path

CAPESTOTALS_WORK = Path(os.environ.get(
    'CAPESTOTALS_WORK',
    Path.home() / 'Desktop/Eclipse 2026/Derivats/Vixen/CapesTotals_work',
)).expanduser()
V2B = str(Path(os.environ.get('V2B_SCR', CAPESTOTALS_WORK / 'v2b')).expanduser())
V3B = str(Path(os.environ.get('V3B_SCR', CAPESTOTALS_WORK / 'v3b')).expanduser())
OFF = (457, 463)
W, H = 6960, 4640
SUN = (4020.89 - OFF[0], 2737.66 - OFF[1])   # (3563.89, 2274.66)
R_SUN = 446.15
V_MOON = (-0.2492, -0.1317)   # px/s, Lluna respecte del Sol
R_APILAT, MARGE_APILAT, TRANS_APILAT = 460.0, 4.0, 14.0   # apila_hdr4_vixen.py
QA = '/Users/USUARI/Desktop/Eclipse 2026/Derivats/Vixen/HDR4/qa'
APILATS = {7: '09_1-60s_572A2975_apilat2.json', 8: '08_1-30s_572A2970_apilat4.json',
           9: '07_1-15s_572A2976_apilat2.json', 10: '06_1-8s_572A2971_apilat4.json'}
ELL = json.load(open(f'{V3B}/lluna3_ellipse.json'))
def apilat(i):
    return json.load(open(f'{QA}/{APILATS[i]}'))
def grid(y0=0, y1=H, x0=0, x1=W):
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    return xx, yy
def r_sun(xx, yy):
    return np.hypot(xx - SUN[0], yy - SUN[1]) / R_SUN
def d_ell(i, xx, yy, centre=None):
    """'Distància' al centre lunar en píxels equivalents: r * (b_mitjana / r_el·lipse(angle)), o sigui
    el radi d'un cercle de radi Rm = sqrt(a*b) que tingués el limbe al mateix lloc relatiu."""
    e = ELL[str(i)]
    cx, cy = centre if centre is not None else (e['cx'], e['cy'])
    a, b, th = e['a'], e['b'], np.radians(e['theta_deg'])
    dx, dy = xx - cx, yy - cy
    c, s = np.cos(th), np.sin(th)
    u = dx*c + dy*s; v = -dx*s + dy*c
    rho = np.sqrt((u/a)**2 + (v/b)**2)
    return rho * np.sqrt(a*b)
def R_moon(i):
    e = ELL[str(i)]; return float(np.sqrt(e['a']*e['b']))
def member_centres(i):
    """Centres del disc de cada membre en coords de sortida: ref + v*(t_f - t_ref)."""
    ap = apilat(i); e = ELL[str(i)]
    t = ap['t_rel_c2_s']; ref = ap['referencia']; t0 = t[ref]
    out = {}
    for f in ap['membres']:
        dt = t[f] - t0
        out[f] = (e['cx'] + V_MOON[0]*dt, e['cy'] + V_MOON[1]*dt, dt)
    return ref, out
def ref_fraction(i, xx, yy):
    """Fracció de pes de la referència a l'apilat (1/N fora de la banda, 1 on només hi és la referència)."""
    ref, cs = member_centres(i)
    d_ref = np.hypot(xx - cs[ref][0], yy - cs[ref][1])
    zona_ref = np.clip((d_ref - (R_APILAT + MARGE_APILAT)) / TRANS_APILAT, 0, 1)
    tot = np.ones_like(xx)
    for f, (cx, cy, dt) in cs.items():
        if f == ref: continue
        d_f = np.hypot(xx - cx, yy - cy)
        tot += np.clip((d_f - (R_APILAT + MARGE_APILAT)) / TRANS_APILAT, 0, 1) * zona_ref
    return 1.0 / tot, len(cs)
def smootherstep(x):
    x = np.clip(x, 0, 1); return x*x*x*(x*(x*6 - 15) + 10)
