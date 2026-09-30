"""c6a · PROVA (no va a cap PSB): la lent que queda és textura ESTIRADA AL LLARG DEL RADI per les dues continuacions de la vora de la Lluna:
 (1) a4 (V88): als ~4–6 px sense dada plena, cada filtre es continua COPIANT radialment el valor de r_ref = R + DMIN + 4 px (vora fina de lent);
 (2) continua_ln (entrada de WOW, WOW bilateral, MGN i ACHF isòtrops): dins la Lluna, perfil radial + residu continuat per pull-push + Laplace,
     llis i estirat radialment; la WOW (blanqueig per escales) l'hereta i l'amplifica a 5–14 px del limbe.
Cura que es prova: MIRALL de la textura a través de la vora (conserva la isotropia; el nivell llis es continua com ara).
Variants del ràster de la P05 WOW bilateral (la capa que porta la lent, c5): actual (validació: ha de ser el de la V91), A (a4 amb mirall),
B (WOW amb l'entrada continuada amb mirall), C (A + B). Totes acaben amb el suavitzat radial a5c (104–228°) com la V91.
WOW en una caixa de 2600 px al voltant de la Lluna, dues vegades (entrada actual i amb mirall); s'aplica NOMÉS la diferència, fins a 150 px
del limbe i fosa fins a 300 px (els efectes de la caixa són els mateixos a les dues i es cancel·len). Sortida: prova_mirall/<variant>_u16.npy."""
from pathlib import Path
import json, sys, time, gc
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v91_lent_residual_20260923'; OUT = SORT / 'prova_mirall'; OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v86_neta_20260923'))
from v86_operadors import wow, pull_push, relaxa, perfil_ln, ng, smoothstep
o = json.loads((ARREL / '.coordination/claim.lock/owner.json').read_text()); assert o.get('serial_writes') == 'HELD'
def log(s): print(time.strftime('%H:%M:%S'), s, flush=True)
H, W = 7506, 10551; CX, CY = 5361.768111973117, 3775.747534140857
V88 = ARREL / '4-RESULTATS/v88_20260923'; FONTS = ARREL / '4-RESULTATS/v85_regeneracio_20260922/d4_baseline/products/sources'
Q = np.load(V88 / 'A3A_franja_un_instant.npz'); qy0, qy1, qx0, qx1 = [int(v) for v in Q['box']]; DMIN = Q['DMIN']; NBZ = len(DMIN)
cx, cy, R = [float(v) for v in Q['centre']]
disp = json.loads((ARREL / '2-ARXIU/reconstruccio_compactacio_20260915/raw_replay/filters_v58_dependencies/display/P05_WOW_bilateral.json').read_text())['display']; LO, HI = float(disp['black']), float(disp['white'])
# ---- entrada de la WOW com a a3_filtres E2 (V88)
a = np.load(FONTS / 'base_G.npy').astype(np.float32); m = np.load(FONTS / 'support.npy') & np.isfinite(a) & (a > 0)
a[qy0:qy1, qx0:qx1] = Q['G']; m[qy0:qy1, qx0:qx1] = Q['domini'] & (a[qy0:qy1, qx0:qx1] > 0)
yy, xx = np.ogrid[:H, :W]; r = np.hypot(yy - CY, xx - CX).astype(np.float32)
L = np.where(m, np.log(np.maximum(a, 1e-9)), 0).astype(np.float32); nodes, p, info = perfil_ln(L, m, r); P = np.interp(r, nodes, p).astype(np.float32); del r; gc.collect()
e0 = relaxa(pull_push(np.where(m, L - P, 0).astype(np.float32), m), m); log('continuació actual feta')
# ---- continuació amb mirall a la caixa de la Lluna: dins, residu = el del punt reflectit a través de la vora del domini (R + DMIN(θ)), fins a 40 px
#      de fondària i fos amb la continuació actual fins a 80 px
B = 1300; bx0, bx1, by0, by1 = int(cx) - B, int(cx) + B, int(cy) - B, int(cy) + B
Y, X = np.mgrid[by0:by1, bx0:bx1]; rho = np.hypot(X - cx, Y - cy).astype(np.float32); th = (np.degrees(np.arctan2(-(Y - cy), X - cx)) + 360) % 360
Rb = (R + DMIN[(th / 360 * NBZ).astype(int) % NBZ]).astype(np.float32); prof = Rb - rho                       # fondària sota la vora del domini
rho_m = np.where(prof > 0, 2 * Rb - rho + 1.0, rho); ang = np.radians(th)
MXm = (cx + rho_m * np.cos(ang) - bx0).astype(np.float32); MYm = (cy - rho_m * np.sin(ang) - by0).astype(np.float32)
Eb = np.where(m[by0:by1, bx0:bx1], (L - P)[by0:by1, bx0:bx1], 0).astype(np.float32); Mb = m[by0:by1, bx0:bx1].astype(np.float32)
emir = cv2.remap(Eb, MXm, MYm, cv2.INTER_LINEAR); wv = cv2.remap(Mb, MXm, MYm, cv2.INTER_LINEAR); emir = np.where(wv > 0.5, emir / np.maximum(wv, 1e-6), 0)
wm = ((1 - smoothstep(prof, 40, 80)) * (prof > 0) * (wv > 0.5)).astype(np.float32)
e0b = e0[by0:by1, bx0:bx1]; evb = np.where(m[by0:by1, bx0:bx1], e0b, wm * emir + (1 - wm) * e0b).astype(np.float32)
ent0 = np.where(m[by0:by1, bx0:bx1], a[by0:by1, bx0:bx1], np.exp(P[by0:by1, bx0:bx1] + e0b)).astype(np.float32)
ent1 = np.where(m[by0:by1, bx0:bx1], a[by0:by1, bx0:bx1], np.exp(P[by0:by1, bx0:bx1] + evb)).astype(np.float32)
del L, e0, a; gc.collect(); full = np.ones(ent0.shape, bool)
q0 = wow(ent0, full, 11, True); log('WOW bilateral actual (caixa) feta'); q1 = wow(ent1, full, 11, True); log('WOW bilateral amb mirall (caixa) feta')
u = lambda q: np.clip((q - LO) / (HI - LO), 0, 1).astype(np.float32)
D = u(q1) - u(q0); dL = rho - R; wD = (1 - smoothstep(dL, 150, 300)).astype(np.float32); dom_b = m[by0:by1, bx0:bx1]
rep = dict(caixa=[bx0, by0, bx1, by1], dif_per_distancia={f'{a_}-{b_}': round(float(np.abs(D[dom_b & (dL >= a_) & (dL < b_)]).mean()), 5) for a_, b_ in ((0, 5), (5, 15), (15, 40), (40, 150), (150, 300), (300, 800))})
log('|dif| mitjana per distància: ' + json.dumps(rep['dif_per_distancia']))
raw0 = np.load(V88 / 'filtres/P05_WOW_bilateral_u16.npy').astype(np.float32) / 65535; raw1 = raw0.copy(); raw1[by0:by1, bx0:bx1] = np.clip(raw0[by0:by1, bx0:bx1] + wD * D, 0, 1)
# ---- a4 (V88: còpia radial) i a4 amb mirall de la textura
by0q, by1q, bx0q, bx1q = qy0, qy1, qx0, qx1; dom = Q['domini']; yq, xq = np.mgrid[by0q:by1q, bx0q:bx1q]; rL = np.hypot(xq - cx, yq - cy).astype('float32')
thq = (np.degrees(np.arctan2(-(yq - cy), xq - cx)) + 360) % 360; dmin_q = DMIN[(thq / 360 * NBZ).astype(int) % NBZ]; dist = (rL - R) - dmin_q; VORA = 2.0
pes = (smoothstep(dist, VORA - 1, VORA + 2) * dom).astype('float32'); zona = (pes < 0.999) & (rL < R + 60); r_ref = R + dmin_q + VORA + 2.0; aq = np.radians(thq)
MXr = (cx + r_ref * np.cos(aq) - bx0q).astype('float32'); MYr = (cy - r_ref * np.sin(aq) - by0q).astype('float32')
rhm = np.maximum(2 * r_ref - rL, r_ref); MXx = (cx + rhm * np.cos(aq) - bx0q).astype('float32'); MYx = (cy - rhm * np.sin(aq) - by0q).astype('float32')
def a4(raw, mirall):
    box = raw[by0q:by1q, bx0q:bx1q].astype('float32')
    if not mirall: new = cv2.remap(box, MXr, MYr, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    else:
        nivell = ng(box, dom, 3.0).astype('float32'); tex = np.where(dom, box - nivell, 0).astype('float32')
        new = cv2.remap(nivell, MXr, MYr, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE) + cv2.remap(tex, MXx, MYx, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    out = raw.copy(); out[by0q:by1q, bx0q:bx1q] = np.where(zona, pes * box + (1 - pes) * new, box); return np.clip(out, 0, 1)
# ---- a5c (V91): suavitzat radial prop del limbe NOMÉS a 104–228°
S0, D1, D2 = 4.0, 4.0, 14.0; DS = np.arange(-30.0, 30.0 + 1e-6, 0.25); NT = 7200; TS = np.radians((np.arange(NT) + 0.5) * 360 / NT); TSg = np.degrees(TS)
S = S0 * smoothstep(TSg, 99.0, 104.0) * (1 - smoothstep(TSg, 228.0, 232.0)); SIG = (S[None, :] * (1 - smoothstep(DS, D1, D2))[:, None]).astype(np.float32)
GEO = json.loads((ARREL / '4-RESULTATS/v91_20260923/A2_GEOMETRIA.json').read_text())['lluna_presentacio']; gcx, gcy, gR = GEO['cx'], GEO['cy'], GEO['R']
mm = int(gR + 30.0 + 4); cb0, cb1, rb0, rb1 = int(gcx) - mm, int(gcx) + mm + 1, int(gcy) - mm, int(gcy) + mm + 1
TT, DD = np.meshgrid(TS, DS); PX = (gcx + (gR + DD) * np.cos(TT) - cb0).astype(np.float32); PY = (gcy - (gR + DD) * np.sin(TT) - rb0).astype(np.float32)
y2, x2 = np.mgrid[rb0:rb1, cb0:cb1]; d2 = np.hypot(x2 - gcx, y2 - gcy) - gR; t2 = (np.arctan2(-(y2 - gcy), x2 - gcx) + 2 * np.pi) % (2 * np.pi)
IX = (t2 / (2 * np.pi) * NT - 0.5).astype(np.float32); IY = ((d2 - DS[0]) / 0.25).astype(np.float32); dins = (d2 > -30) & (d2 < 30)
K = np.clip(np.floor(SIG).astype(int), 0, 3); FR = (SIG - K).astype(np.float32)
def a5c(full):
    Xb = full[rb0:rb1, cb0:cb1].astype(np.float32); Pp = cv2.remap(Xb, PX, PY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    St = np.stack([Pp] + [cv2.GaussianBlur(Pp, (1, 0), sigmaX=1e-3, sigmaY=s / 0.25) for s in (1.0, 2.0, 3.0, 4.0)])
    A_ = np.take_along_axis(St, K[None], 0)[0]; B_ = np.take_along_axis(St, (K + 1)[None], 0)[0]; Q_ = np.where(SIG > 0, (1 - FR) * A_ + FR * B_, Pp)
    back = lambda Z: cv2.remap(Z, np.mod(IX, NT), IY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    out = full.copy(); out[rb0:rb1, cb0:cb1] = np.where(dins, Xb + (back(Q_) - back(Pp)), Xb); return np.clip(out, 0, 1)
ref = np.load(ARREL / '4-RESULTATS/v91_20260923/filtres_radial_c/P05_WOW_bilateral_u16.npy')
for nom, raw, mir in (('actual', raw0, False), ('A_a4_mirall', raw0, True), ('B_wow_mirall', raw1, False), ('C_tots_dos', raw1, True)):
    v = np.round(a5c(a4(raw, mir)) * 65535).astype(np.uint16); np.save(OUT / f'{nom}_u16.npy', v)
    if nom == 'actual': rep['validacio_actual_vs_V91_max_DN16'] = int(np.abs(v.astype(np.int32) - ref.astype(np.int32)).max()); log(f"validació: actual contra el ràster de la V91, màx {rep['validacio_actual_vs_V91_max_DN16']} DN16")
    log(nom + ' fet')
(SORT / 'C6A_PROVA_MIRALL.json').write_text(json.dumps(rep, ensure_ascii=False, indent=2) + '\n'); log('fet')
