"""d1 (V97) · El graó diagonal (el «marró»): perfil perpendicular a la vora del camp de la Sony A, a cada pis de la torre.
Mesura: dA = distància cap endins des de la vora del suport de la Sony A (pesos G de la V29 > 0), només on NO hi ha ni la Vixen ni la Sony B.
Per a cada imatge X (ln G): X − perfil radial del Sol (mitjana per anell de 2 px a tota la zona) → mitjana per calaix d'1 px de dA
(d 100–1400), per sectors d'angle de la vora. El graó = mitjana[440,500] − mitjana[360,420] després de treure la recta ajustada a
[300,560] sense la finestra [400,460] (el gradient local). Nul: el mateix amb dA mesurada des d'una vora desplaçada 200 px.
Ús: d1_grao_sony.py <sortida.json> etiqueta=ruta.npy[:canal] …   (ruta.npy (H,W) o (H,W,3); canal 1 = G per defecte)"""
import sys, json
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent))
from jutge_comu import SOL, RSOL, desa, ARREL
C = ARREL / '4-RESULTATS/v97_refundacio_20260924/cadena_raw'
wA = np.load(C / 'sources_v29/sony_A_weights.npy', mmap_mode='r'); wB = np.load(C / 'sources_v29/sony_B_weights.npy', mmap_mode='r'); wV = np.load(C / 'sources_v29/vixen_weights.npy', mmap_mode='r')
def ch(a, c=1): return np.asarray(a[..., c] if a.ndim == 3 else a, np.float32)
SA = ch(wA) > 0; nomesA = SA & ~(ch(wB) > 0) & ~(ch(wV) > 0)
dA = cv2.distanceTransform(SA.astype(np.uint8), cv2.DIST_L2, 5)
Hh, Ww = SA.shape; yy, xx = np.mgrid[0:Hh, 0:Ww].astype(np.float32); r = np.hypot(xx - SOL[0], yy - SOL[1])
# angle de la normal a la vora (per separar trams rectes de la vora)
gx = cv2.Sobel(cv2.GaussianBlur(dA, (0, 0), 20), cv2.CV_32F, 1, 0); gy = cv2.Sobel(cv2.GaussianBlur(dA, (0, 0), 20), cv2.CV_32F, 0, 1); ang = (np.degrees(np.arctan2(gy, gx)) + 360) % 360
zona = nomesA & (dA > 80) & (dA < 1450) & (r > 2.2 * RSOL)
def perfil(X, dmap, m):
    lx = np.log(np.maximum(X, 1e-9)); ok = m & np.isfinite(lx) & (X > 0)
    rb = (r[ok] / 2).astype(int); med = np.zeros(rb.max() + 1);
    ss = np.bincount(rb, lx[ok]); nn = np.bincount(rb); med = np.where(nn > 20, ss / np.maximum(nn, 1), np.nan)
    res = lx[ok] - med[rb]; di = dmap[ok].astype(int); good = np.isfinite(res)
    s = np.bincount(di[good], res[good], 1500); n = np.bincount(di[good], None, 1500); return np.where(n > 50, s / np.maximum(n, 1), np.nan), ok
def grao(P):
    d = np.arange(P.size); fit = ((d >= 300) & (d <= 560) & ~((d >= 400) & (d <= 460))) & np.isfinite(P)
    if fit.sum() < 50: return None
    k = np.polyfit(d[fit], P[fit], 1); Q = P - np.polyval(k, d)
    return float(np.nanmean(Q[440:500]) - np.nanmean(Q[360:420]))
out = dict(definicio=__doc__.split('\n')[1], zona_px=int(zona.sum()), resultats={})
SA2 = np.zeros_like(SA); sh = 200; SA2[:, sh:] = SA[:, :-sh]; dN = cv2.distanceTransform((SA2 & SA).astype(np.uint8), cv2.DIST_L2, 5)
for arg in sys.argv[2:]:
    et, ruta = arg.split('=', 1); c = 1
    if ':' in ruta.split('/')[-1]: ruta, c = ruta.rsplit(':', 1); c = int(c)
    X = ch(np.load(ruta, mmap_mode='r'), c)
    if X.shape != SA.shape: X = cv2.resize(X, (Ww, Hh), interpolation=cv2.INTER_LINEAR)
    P, ok = perfil(X, dA, zona); PN, _ = perfil(X, dN, zona & (dN > 80))
    sect = {}
    for a0 in range(0, 360, 45):
        m = zona & (ang >= a0) & (ang < a0 + 45)
        if m.sum() > 200000: Ps, _ = perfil(X, dA, m); sect[a0] = grao(Ps)
    out['resultats'][et] = dict(grao_ln=grao(P), grao_nul=grao(PN), per_sector_normal=sect, perfil_100_1400=[None if not np.isfinite(v) else round(float(v), 6) for v in P[100:1400]])
    print(et, 'graó', out['resultats'][et]['grao_ln'], 'nul', out['resultats'][et]['grao_nul'], sect, flush=True)
desa(sys.argv[1], out)
