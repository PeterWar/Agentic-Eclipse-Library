"""w1 (V94) · Les dues WOW (P04 WOW i P05 WOW bilateral) refetes sobre el domini de dada, sense farcit (wow_domini), neutres de nivell
(neutralitza) i amb les línies coherents de l'esquerra fora (a5d de la V93, 104–228°, arc de 6 px). Els píxels sense dada queden TRANSPARENTS
(alfa 0), no omplerts. Entrades: les mateixes que a3_filtres E2 de la V88 (base_G amb la franja d'un instant a la caixa de la Lluna; domini).
Escala de visualització: 0,5 + k·q, amb k tal que el detall fi (pas alt σ 8 px) a 100–600 px del limbe tingui la mateixa amplitud que a la V93.
Sortida: 4-RESULTATS/v94_20260924/wow/<tag>_u16.npy, <tag>_alfa_u16.npy i W1_WOW.json."""
import sys, json, time, hashlib
from pathlib import Path
import numpy as np, cv2
from scipy.ndimage import gaussian_filter1d
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v94_20260924'; OUT = SORT / 'wow'; OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(Path(__file__).parent)); from wow_domini import wow_domini, neutralitza, smoothstep
o = json.loads((ARREL / '.coordination/claim.lock/owner.json').read_text()); assert o.get('serial_writes') == 'HELD'
def log(s): print(time.strftime('%H:%M:%S'), s, flush=True)
def sha(p):
    with open(p, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
H, W = 7506, 10551; V85 = ARREL / '4-RESULTATS/v85_regeneracio_20260922'; FONTS = V85 / 'd4_baseline/products/sources'; V88 = ARREL / '4-RESULTATS/v88_20260923'
Q = np.load(V88 / 'A3A_franja_un_instant.npz'); qy0, qy1, qx0, qx1 = [int(v) for v in Q['box']]; cx, cy, R = [float(v) for v in Q['centre']]
a = np.load(FONTS / 'base_G.npy').astype(np.float32); m = np.load(FONTS / 'support.npy') & np.isfinite(a) & (a > 0)
a[qy0:qy1, qx0:qx1] = Q['G']; m[qy0:qy1, qx0:qx1] = Q['domini'] & (Q['G'] > 0); a = np.nan_to_num(a); log(f'domini: {m.sum()} px')
yy, xx = np.ogrid[:H, :W]; d = np.hypot(xx - cx, yy - cy) - R; ref = (d > 100) & (d < 600) & m
# a5d (V93): línies coherents fora, 104–228°, sobre el ràster de visualització
GEO = json.loads((ARREL / '4-RESULTATS/v92_20260924/A2_GEOMETRIA.json').read_text())['lluna_presentacio']; gcx, gcy, gR = GEO['cx'], GEO['cy'], GEO['R']
DMIN_P, DMAX_P, DRp, NTp = -30.0, 30.0, 0.25, 7200; mm = int(gR + DMAX_P + 4); bx0, bx1, by0, by1 = int(gcx) - mm, int(gcx) + mm + 1, int(gcy) - mm, int(gcy) + mm + 1
TS = np.radians((np.arange(NTp) + 0.5) * 360 / NTp); DS = np.arange(DMIN_P, DMAX_P + 1e-6, DRp); TT, DD = np.meshgrid(TS, DS); TSg = np.degrees(TS)
WGT = ((smoothstep(TSg, 99.0, 104.0) * (1 - smoothstep(TSg, 228.0, 232.0)))[None, :] * (1 - smoothstep(DS, 4.0, 14.0))[:, None]).astype(np.float32)
PMX = (gcx + (gR + DD) * np.cos(TT) - bx0).astype(np.float32); PMY = (gcy - (gR + DD) * np.sin(TT) - by0).astype(np.float32)
y2, x2 = np.mgrid[by0:by1, bx0:bx1]; d2 = np.hypot(x2 - gcx, y2 - gcy) - gR; t2 = (np.arctan2(-(y2 - gcy), x2 - gcx) + 2 * np.pi) % (2 * np.pi)
IX = (t2 / (2 * np.pi) * NTp - 0.5).astype(np.float32); IY = ((d2 - DS[0]) / DRp).astype(np.float32); dins = (d2 > DMIN_P) & (d2 < DMAX_P); sig_th = 6.0 / ((gR + DS) * np.radians(360 / NTp))
def a5d(X, Mb):
    P = cv2.remap(X, PMX, PMY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE); V = cv2.remap(Mb.astype(np.float32), PMX, PMY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    num = gaussian_filter1d(P * V, 4.0 / DRp, axis=0, mode='nearest'); den = gaussian_filter1d(V, 4.0 / DRp, axis=0, mode='nearest'); HP = np.where(V > 0.5, P - num / np.maximum(den, 1e-6), 0)
    COH = np.empty_like(HP); VC = np.empty_like(HP)
    for i in range(HP.shape[0]): COH[i] = gaussian_filter1d(HP[i] * V[i], sig_th[i], mode='wrap'); VC[i] = gaussian_filter1d(V[i], sig_th[i], mode='wrap')
    COH = np.where(VC > 0.05, COH / np.maximum(VC, 1e-6), 0)
    back = lambda Z: cv2.remap(Z, np.mod(IX, NTp), IY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return np.where(dins & Mb, X - back(WGT * COH), X)
rep = dict(domini_px=int(m.sum()), escales=8, capes={})
for tag, bil in (('P05_WOW_bilateral', True), ('P04_WOW', False)):
    t0 = time.time(); q = wow_domini(a, m, 8, bil, log=log); log(f'{tag}: WOW en {time.time() - t0:.0f} s')
    qn = neutralitza(q, m, cx, cy, R); del q
    old = np.load(ARREL / f'4-RESULTATS/v93_20260924/filtres_v93/{tag}_u16.npy', mmap_mode='r').astype(np.float32) / 65535
    hp = lambda X: X - cv2.GaussianBlur(X, (0, 0), 8); qz = np.nan_to_num(qn)
    k = float(np.std(hp(old)[ref]) / np.std(hp(qz)[ref])); disp = np.where(m, 0.5 + k * qz, 0.5).astype(np.float32); del old, qz
    Xb = disp[by0:by1, bx0:bx1].copy(); disp[by0:by1, bx0:bx1] = a5d(Xb, m[by0:by1, bx0:bx1])
    u = np.round(np.clip(disp, 0, 1) * 65535).astype(np.uint16); u[~m] = 32768; np.save(OUT / f'{tag}_u16.npy', u)
    al = np.where(m, 65535, 0).astype(np.uint16); np.save(OUT / f'{tag}_alfa_u16.npy', al)
    rep['capes'][tag] = dict(bilateral=bil, k=round(k, 5), sha256=sha(OUT / f'{tag}_u16.npy'), mitjana_domini=round(float(disp[m].mean()), 4), segons=round(time.time() - t0))
    log(f"{tag}: k {k:.4f}, mitjana {rep['capes'][tag]['mitjana_domini']}"); del disp, u
(SORT / 'W1_WOW.json').write_text(json.dumps(rep, ensure_ascii=False, indent=2) + '\n'); log('W1 fet')
