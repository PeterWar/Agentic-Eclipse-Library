"""f1 · V113 (Claude, 28-09-2026): la Sony A, corregida contra la Sony B al pis de la fusió (torre de Pisa: primer pis on neix el defecte).

Diagnosi (vistes/apilats_dalt.png, cercles_AB.png): els arcs 2, 3 i 5 de «V111 artefactes» són a l'apilat de la Sony A i NO a la Sony B, que
veu el mateix cel; són concèntrics (radis 1.908, 2.366 i 2.832 px) amb un punt a ~200 px del centre del sensor de l'apuntament A: estructura
instrumental de l'apuntament A. La marca 8 és a la franja de la vora d'A on el pes fA passa de 0 a 0,44 (TAPER_A_PX = 480): la fusió hi
converteix el desajust A/B en una línia (diagnosi del Codex, DIAGNOSI_FONTS).

Cura: al solapament, la A pren de la B l'estructura que la B hi veu, sense tocar el gra fi de la A (< 25 px) ni el nivell del cel de gran
escala (> 600 px) lluny de la vora d'A:
    δ_c = ln A_c + pred_c − ln B_c                (pred = guany A→B congelat de la fusió de control, V98)
    C_c = [ (LP25 − LP600)[δ_c] + T_A · LP600[δ_c] ] · T_B · T_sol,     A'_c = A_c · exp(−C_c)
  LP_s = gaussiana normalitzada de σ s px sobre el solapament vàlid (sense estrelles, sense la taca de l'eix d'A, r_sol > 2,5 R);
  T_B: 0 a la vora de la B → 1 a 800 px dins (on s'acaba la B, la A es queda com era);
  T_A: 1 fins a 700 px de la vora d'A → 0 a 2.200 px (el nivell de gran escala només on fA varia);
  T_sol: 0 a r_sol 3 R → 1 a 4 R (la corona interior i el limbe no es toquen).
Cap píxel inventat: tot el que entra ve de l'apilat de la Sony B, que ha observat el mateix cel. La fusió (fA, guany, Vixen) no es toca.
Sortida: 4-RESULTATS/v112_claude_20260928/fonts_v113/apilats/sony_A_total.npy (substitueix l'entrada «sony_A_total_v36.npy» de la fusió),
C_bin4.npy i F1_REBUT.json. Ús: f1_correccio_sonyA.py"""
from pathlib import Path
import json, time, hashlib
import numpy as np, cv2
from scipy import ndimage as ndi
R = Path(__file__).resolve().parents[3]
F = R / '4-RESULTATS/v108_20260926/flat2d_v5/apilats'
V97 = R / '4-RESULTATS/v97_refundacio_20260924/cadena_raw'
import sys
LOCAL = '--local' in sys.argv          # cura només al domini de les marques 2, 3, 5 (escales mitjanes) i 8 (+ nivell de la vora d'A)
VORA8 = '--vora8' in sys.argv         # v3: com la v2, però la franja de la vora d'A només al tram de la marca 8, esvaint-se AL LLARG de la vora
                                       # (1.500 px més enllà dels extrems del traç); a través de la vora, T_A (700 → 2.200 px), sense domini dibuixat
VORA = '--vora-A' in sys.argv or VORA8          # v2: arcs al domini de 2, 3, 5 (escales mitjanes); la vora d'A SENCERA (totes les escales > 25 px) amb T_A,
                                       # sense cap domini dibuixat a la 8 (la v1 hi deixava una ondulació nova on s'esvaïa el domini)
OUT = R / ('4-RESULTATS/v112_claude_20260928/fonts_v113' + ('_vora8' if VORA8 else '_vora' if VORA else ('_local' if LOCAL else '')) + '/apilats'); OUT.mkdir(parents=True, exist_ok=True)
DIL_PX, FEATHER_PX = 300.0, 400.0
H, W = 7506, 10551; B4 = 4; h4, w4 = H // B4, W // B4
CX, CY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736
LP_FI, LP_GRAN = 25.0, 600.0; TB_PX = 800.0; TA0, TA1 = 700.0, 2200.0; TS0, TS1 = 3.0, 4.0; RSOL_MIN = 2.5
t0 = time.time()
assert json.loads((R / '.coordination/claim.lock/owner.json').read_text())['serial_writes'] == 'HELD'

def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 24), b''): h.update(b)
    return h.hexdigest()

def smooth(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

A = np.load(F / 'sony_A_total.npy', mmap_mode='r')
B = np.load(F / 'cau/sony_B_total_v42.npy', mmap_mode='r')
pa = np.load(V97 / 'sources_v29/sony_A_weights.npy', mmap_mode='r'); pb = np.load(V97 / 'b2_sony_B/cau/sony_B_weights_v42.npy', mmap_mode='r')
stars = np.load(R / '4-RESULTATS/v108_20260926/flat2d_v5/fusio/d4/products/sources/star_footprints.npy', mmap_mode='r')
rec = json.loads((R / '4-RESULTATS/v98_20260925/cadena_v98/b3/receipts/B3_fusio.json').read_text())['pointings']['channels']
COEF = {c: np.asarray(rec[str(c)]['coefficients'], np.float64) for c in range(3)}
geo = json.loads((R / '2-ARXIU/reconstruccio_compactacio_20260915/raw_replay/v36_rgb_dependencies/geometry.json').read_text())
M = np.array(geo['M_llenc_a_v23']); GX, GY = (M @ np.array([2825, 3988, 1.0])).tolist()      # la taca de l'eix d'A (GHOST_XY del b3)
# 1 · suports (com el b3: tots els canals finits, > 0 i amb pes) i δ en blocs 4×4
ma = np.ones((H, W), bool); mb = np.ones((H, W), bool)
for y0 in range(0, H, 512):
    s = slice(y0, min(H, y0 + 512))
    a_ = np.asarray(A[s]); b_ = np.asarray(B[s])
    ma[s] = np.all(np.isfinite(a_) & (a_ > 0) & (np.asarray(pa[s]) > 0), axis=2)
    mb[s] = np.all(np.isfinite(b_) & (b_ > 0) & (np.asarray(pb[s]) > 0), axis=2)
yy, xx = np.ogrid[:H, :W]
rsol = np.hypot(xx - CX, yy - CY) / RL
use = ma & mb & (rsol > RSOL_MIN) & (np.hypot(xx - GX, yy - GY) > 320) & ~ndi.binary_dilation(np.asarray(stars) > 0, iterations=3)
gx = (xx - W / 2) / 4000; gy = (yy - H / 2) / 4000
def bin4(a): return a[:h4 * B4, :w4 * B4].reshape(h4, B4, w4, B4).sum((1, 3))
m4 = bin4(use.astype(np.float64))
d4 = np.zeros((3, h4, w4))
for c in range(3):
    pred = COEF[c][0] + COEF[c][1] * gx + COEF[c][2] * gy + COEF[c][3] * gx * gx + COEF[c][4] * gx * gy + COEF[c][5] * gy * gy
    dl = np.zeros((H, W))
    for y0 in range(0, H, 512):
        s = slice(y0, min(H, y0 + 512)); u = use[s]
        dl[s][u] = (np.log(np.asarray(A[s, :, c], np.float64)) + pred[s] - np.log(np.asarray(B[s, :, c], np.float64)))[u] if np.ndim(pred) == 2 else 0
    d4[c] = bin4(dl * use)
    del dl, pred
print(f'δ fet ({time.time()-t0:.0f}s)', flush=True)

def lp(num, den, sig_px):
    # σ ≤ 50 px: al graella de 4 px; si no, a la de 16 px i tornada (bilineal)
    if sig_px <= 50:
        return ndi.gaussian_filter(num, sig_px / B4) / np.maximum(ndi.gaussian_filter(den, sig_px / B4), 1e-9)
    f = 4; hh, ww = h4 // f, w4 // f
    n = num[:hh * f, :ww * f].reshape(hh, f, ww, f).sum((1, 3)); d = den[:hh * f, :ww * f].reshape(hh, f, ww, f).sum((1, 3))
    q = ndi.gaussian_filter(n, sig_px / (B4 * f)) / np.maximum(ndi.gaussian_filter(d, sig_px / (B4 * f)), 1e-9)
    return cv2.resize(q.astype(np.float32), (w4, h4), interpolation=cv2.INTER_LINEAR).astype(np.float64)

# 2 · afebliments (graella de 4 px)
ma4 = ma[:h4 * B4, :w4 * B4].reshape(h4, B4, w4, B4).all((1, 3)); mb4 = mb[:h4 * B4, :w4 * B4].reshape(h4, B4, w4, B4).all((1, 3))
Y4, X4 = np.mgrid[0:h4, 0:w4] * B4 + B4 / 2
rs4 = np.hypot(X4 - CX, Y4 - CY) / RL
TB = smooth(ndi.distance_transform_edt(mb4 | (rs4 < 1.2)) * B4, 0, TB_PX)
TA = 1 - smooth(ndi.distance_transform_edt(ma4 | (rs4 < 1.2)) * B4, TA0, TA1)
TS = smooth(rs4, TS0, TS1)
C4 = np.zeros((3, h4, w4), np.float32)
if LOCAL or VORA:
    # domini: les marques de Pere (capa 412 de la V111) on la diagnosi ha trobat el defecte a la Sony A, eixamplades DIL_PX i amb vora suau
    mq = np.load(R / '4-RESULTATS/v112_20260928/marques412.npz'); al = mq['alpha'] > 0; og = mq['origin']
    lab, _ = ndi.label(al); full = np.zeros((H, W), np.int32); full[og[1]:og[1] + al.shape[0], og[0]:og[0] + al.shape[1]] = lab
    def domini(ids):
        m = np.isin(full, ids)[:h4 * B4, :w4 * B4].reshape(h4, B4, w4, B4).any((1, 3))
        d = ndi.distance_transform_edt(~m) * B4
        return 1 - smooth(d, DIL_PX, DIL_PX + FEATHER_PX)
    M235 = domini([2, 3, 5]); M8 = domini([8])
    if VORA8:
        from skimage.morphology import skeletonize
        sl8 = ndi.find_objects(lab)[7]; yy8, xx8 = np.nonzero(skeletonize(lab[sl8] == 8)); P8 = np.c_[xx8 + sl8[1].start + og[0], yy8 + sl8[0].start + og[1]].astype(float)
        c8 = P8.mean(0); d8 = np.linalg.svd(P8 - c8, full_matrices=False)[2][0]; t8 = (P8 - c8) @ d8
        tt = (X4 - c8[0]) * d8[0] + (Y4 - c8[1]) * d8[1]; fora = np.maximum(tt - t8.max(), t8.min() - tt)   # distància més enllà dels extrems
        E8 = 1 - smooth(fora, 300.0, 1800.0)
        WMID = np.maximum(M235, TA * E8); WGRAN = TA * E8
    elif VORA: WMID = np.maximum(M235, TA); WGRAN = TA
    else: WMID = np.maximum(M235, M8); WGRAN = TA * M8
else:
    WMID = np.ones((h4, w4)); WGRAN = TA
for c in range(3):
    lf = lp(d4[c], m4, LP_FI); lg = lp(d4[c], m4, LP_GRAN)
    C4[c] = (((lf - lg) * WMID + WGRAN * lg) * TB * TS).astype(np.float32)
C4 = np.where(np.isfinite(C4), C4, 0).astype(np.float32)
np.save(OUT.parent / 'C_bin4.npy', C4)
# 3 · A' = A · exp(−C), a resolució completa (C bilineal des de la graella de 4 px)
Ap = np.lib.format.open_memmap(OUT / 'sony_A_total.npy', mode='w+', dtype=np.float32, shape=(H, W, 3))
for c in range(3):
    Cf = cv2.resize(np.pad(C4[c], ((0, 1), (0, 1)), mode='edge'), (w4 * B4 + B4, h4 * B4 + B4), interpolation=cv2.INTER_LINEAR)
    Cf = np.pad(Cf, ((0, max(0, H - Cf.shape[0])), (0, max(0, W - Cf.shape[1]))), mode='edge')[:H, :W]
    for y0 in range(0, H, 512):
        s = slice(y0, min(H, y0 + 512)); a_ = np.asarray(A[s, :, c])
        Ap[s, :, c] = np.where(np.isfinite(a_), a_ * np.exp(-Cf[s]), a_)
Ap.flush(); del Ap
st = {c: dict(zip(('p1', 'p50', 'p99', 'max_abs'), [float(v) for v in np.percentile(C4[c][TB > 0.5], [1, 50, 99])] + [float(np.abs(C4[c]).max())])) for c in range(3)}
rep = dict(guio=str(Path(__file__).relative_to(R)), guio_sha256=sha(__file__), entrades=dict(sony_A=str((F / 'sony_A_total.npy').relative_to(R)), sony_A_sha256=sha(F / 'sony_A_total.npy'),
           sony_B=str((F / 'cau/sony_B_total_v42.npy').relative_to(R)), sony_B_sha256=sha(F / 'cau/sony_B_total_v42.npy'), guany='V98 B3_fusio.json (congelat)'),
           parametres=dict(LOCAL=LOCAL, VORA=VORA, VORA8=VORA8, domini=('marques 2,3,5 (escales 25–600 px) i franja de la vora d\'A al tram de la 8 (totes les escales > 25 px; T_A a través, 300 → 1.800 px al llarg)' if VORA8 else 'marques 2,3,5 (escales 25–600 px) i franja de la vora d\'A sencera (totes les escales > 25 px, T_A)' if VORA else ('marques 2,3,5 (escales 25–600 px) i 8 (també el nivell de gran escala a la vora d\'A)' if LOCAL else 'tot el solapament')), DIL_PX=DIL_PX, FEATHER_PX=FEATHER_PX, LP_FI=LP_FI, LP_GRAN=LP_GRAN, TB_PX=TB_PX, TA=[TA0, TA1], TSOL_R=[TS0, TS1], RSOL_MIN=RSOL_MIN, graella_px=B4, taca_eix_A=[GX, GY, 320]),
           C_estadistica_on_TB_gt_05=st, sortida=str((OUT / 'sony_A_total.npy').relative_to(R)), sortida_sha256=sha(OUT / 'sony_A_total.npy'), segons=round(time.time() - t0, 1))
(OUT.parent / 'F1_REBUT.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False)); print(json.dumps(rep, indent=1, ensure_ascii=False))
