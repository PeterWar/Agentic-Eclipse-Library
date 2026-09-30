"""m17 · AVALUACIÓ DEL PILOT (flat 2D) a cada etapa: per a cada parell (abans = cadena, després = pilot) i cada traç rellevant,
el solc fi (σ 4/40) a la geometria de la MARCA de Pere amb la tolerància del pinzell (±60 px, ±1,5°), i la seva significació contra
120 segments nuls a l'atzar (mateixa distància al Sol, qualsevol angle, mateixa cerca) mesurats a la imatge d'ABANS (el mateix nul per a
totes dues: si la cura treu el traç, el p puja cap a 0,5). A més, el patró fix: correlació del residu del flat (banda σ 2–30) amb
l'apilat abans i després (ha de caure a ~0), i la textura fina (MAD del contrast fi al camp exterior). Sortida: M17_<nom>.json.
Ús: m17_avalua_pilot.py <nom> <abans.npy[:canal]> <després.npy[:canal]> <traços, p. ex. 1,2,6>"""
import sys, json
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_marrons import *
nom, fa, fd, trs = sys.argv[1], sys.argv[2], sys.argv[3], [int(x) for x in sys.argv[4].split(',')]
def obre(f):
    p, _, ch = f.partition(':'); a = np.load(p, mmap_mode='r'); return (a, int(ch)) if ch else (a, None)
A, ca = obre(fa); D, cd = obre(fd)
def mapa_r(src, ch, box):
    x0, y0, x1, y1 = box; img = np.asarray(src[y0:y1, x0:x1] if ch is None else src[y0:y1, x0:x1, ch], np.float32)
    m = np.isfinite(img) & (img > 0); w = m.astype(np.float32); img = np.where(m, img, 0)
    ng = lambda x, s: cv2.GaussianBlur(x * w, (0, 0), s) / np.maximum(cv2.GaussianBlur(w, (0, 0), s), 1e-6)
    ok = cv2.erode(w, np.ones((81, 81), np.uint8)) > 0
    return np.where(ok, ng(img, 4) / np.maximum(ng(img, 40), 1e-12) - 1, np.nan).astype(np.float32)
TH = np.arange(-1.5, 1.501, 0.25); TT = np.arange(-60, 61, 2.0)
def cerca(r, org, c, d, L):
    best = np.inf
    for dth in TH:
        a = np.radians(dth); dd = np.array([d[0] * np.cos(a) - d[1] * np.sin(a), d[0] * np.sin(a) + d[1] * np.cos(a)]); nn = np.array([-dd[1], dd[0]])
        s = np.arange(-L / 2, L / 2 + 1e-6, 3.0)
        X = (c[0] + s[:, None] * dd[0] + TT[None, :] * nn[0]).astype(np.float32); Y = (c[1] + s[:, None] * dd[1] + TT[None, :] * nn[1]).astype(np.float32)
        P = mostreja(r, X, Y, org); cov = np.isfinite(P).mean(0)
        with np.errstate(all='ignore'): v = np.where(cov > 0.8, np.nanmean(P, 0), np.inf)
        best = min(best, float(np.min(v)))
    return best
def val(src, ch, c, d, L):
    p = np.array([c + d * (L / 2 + 150), c - d * (L / 2 + 150)])
    box = (int(max(0, p[:, 0].min() - 150)), int(max(0, p[:, 1].min() - 150)), int(min(W, p[:, 0].max() + 150)), int(min(H, p[:, 1].max() + 150)))
    return cerca(mapa_r(src, ch, box), box[:2], c, d, L)
rng = np.random.default_rng(20260926); res = {'abans': fa, 'despres': fd, 'tracos': {}}
for tr in [t for t in TRACOS if t['k'] in trs]:
    c0, d0, L = tr['centre'], tr['d'], tr['llarg']; rs = np.hypot(c0[0] - SOL[0], c0[1] - SOL[1]); nuls = []
    while len(nuls) < 120:
        rr = rs * rng.uniform(0.75, 1.25); ph = rng.uniform(0, 2 * np.pi); c = np.array([SOL[0] + rr * np.cos(ph), SOL[1] + rr * np.sin(ph)]); an = rng.uniform(0, np.pi); d = np.array([np.cos(an), np.sin(an)])
        e1 = c + d * (L / 2 + 80); e2 = c - d * (L / 2 + 80)
        if min(e1[0], e2[0]) < 100 or min(e1[1], e2[1]) < 100 or max(e1[0], e2[0]) > W - 100 or max(e1[1], e2[1]) > H - 100 or np.hypot(*(c - c0)) < 300 + L / 2: continue
        nuls.append((c, d))
    va = val(A, ca, c0, d0, L); vd = val(D, cd, c0, d0, L)
    if not (np.isfinite(va) and np.isfinite(vd)): continue
    vn = np.array([val(A, ca, c, d, L) for c, d in nuls]); vn = vn[np.isfinite(vn)]; med = float(np.median(vn)); mad = float(1.4826 * np.median(np.abs(vn - med)))
    pa = float((np.sum(vn <= va) + 1) / (len(vn) + 1)); pd = float((np.sum(vn <= vd) + 1) / (len(vn) + 1))
    res['tracos'][tr['k']] = dict(solc_abans=va, solc_despres=vd, nul_mediana=med, nul_mad=mad, z_abans=(va - med) / mad, z_despres=(vd - med) / mad, p_abans=pa, p_despres=pd, n_nul=int(len(vn)))
    print(f"{nom} T{tr['k']}: abans {va*1e4:+.1f}‱ (z {(va-med)/mad:+.1f}, p {pa:.3f}) → després {vd*1e4:+.1f}‱ (z {(vd-med)/mad:+.1f}, p {pd:.3f}) · nul {med*1e4:+.1f}±{mad*1e4:.1f}‱", flush=True)
# textura fina al camp exterior (r > 4 R☉) i diferència de nivell a gran escala
boxes = [(x, y, min(W, x + 2000), min(H, y + 2000)) for y in range(0, H, 2000) for x in range(0, W, 2000)]
ta, td, dl = [], [], []
for b in boxes:
    ra = mapa_r(A, ca, b); rd = mapa_r(D, cd, b); x0, y0, x1, y1 = b; yy, xx = np.mgrid[y0:y1, x0:x1]; k = np.isfinite(ra) & np.isfinite(rd) & (np.hypot(xx - SOL[0], yy - SOL[1]) > 4 * RSOL)
    if k.sum() > 1e5: ta.append(np.abs(ra[k] - np.median(ra[k]))); td.append(np.abs(rd[k] - np.median(rd[k])))
    ia = np.asarray(A[y0:y1, x0:x1] if ca is None else A[y0:y1, x0:x1, ca], np.float32); idd = np.asarray(D[y0:y1, x0:x1] if cd is None else D[y0:y1, x0:x1, cd], np.float32)
    kk = np.isfinite(ia) & np.isfinite(idd) & (ia > 0) & (idd > 0)
    if kk.sum() > 1e5:
        q = np.where(kk, idd / np.where(kk, ia, 1) - 1, 0).astype(np.float32); w = kk.astype(np.float32)
        qs = cv2.GaussianBlur(q, (0, 0), 100) / np.maximum(cv2.GaussianBlur(w, (0, 0), 100), 1e-6); dl.append(np.abs(qs[cv2.erode(w, np.ones((301, 301), np.uint8)) > 0]))
if ta:
    res['textura_fina_MAD_camp_exterior'] = dict(abans=float(1.4826 * np.median(np.concatenate(ta))), despres=float(1.4826 * np.median(np.concatenate(td))))
    print(f"{nom} textura fina (MAD, r > 4 R☉): abans {res['textura_fina_MAD_camp_exterior']['abans']*1e4:.2f}‱ → després {res['textura_fina_MAD_camp_exterior']['despres']*1e4:.2f}‱", flush=True)
if dl:
    z = np.concatenate(dl); res['nivell_gran_escala_despres_sobre_abans_menys_1'] = dict(p50=float(np.median(z)), p99=float(np.percentile(z, 99)), max=float(z.max()))
    print(f"{nom} nivell a gran escala (σ 100 px) |després/abans − 1|: p50 {np.median(z)*1e4:.2f}‱ p99 {np.percentile(z, 99)*1e4:.2f}‱ màx {z.max()*1e4:.2f}‱", flush=True)
desa(OUT / f'M17_{nom}.json', res)
