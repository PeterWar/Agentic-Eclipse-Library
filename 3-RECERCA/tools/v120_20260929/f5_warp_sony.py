"""f5 (V120, 29-09-2026) · DEFORMA LA SONY (A i B) A LA GEOMETRIA DE LA VIXEN amb el model del f4 (opció 3 de Pere: «moure la Sony cap a la Vixen»).
X'(q) = X(q − u_X(q − u_X(q)))   (u_X = posició a V − posició a X; dues iteracions del punt fix; el camp és suau: salt màxim 0,01 px/px)
Què es deforma (tot el que la fusió i els testimonis llegeixen en geometria Sony; els fitxers originals no es toquen):
  · dades (interpolació CÚBICA; la validesa es remostreja bilineal i s'erosiona 2 px, el peu del cúbic; fora de la validesa, NaN):
      A de la fusió  4-RESULTATS/v112_claude_20260928/fonts_v113_vora/apilats/sony_A_total.npy        → sony_A_total_v113vora.npy
      A original     4-RESULTATS/v108_20260926/flat2d_v5/apilats/sony_A_total.npy                      → sony_A_total_flat2d_v5.npy (testimonis)
      B              4-RESULTATS/v108_20260926/flat2d_v5/apilats/cau/sony_B_total_v42.npy              → sony_B_total_v42.npy
  · pesos (BILINEAL, 0 fora): sources_v29/sony_A_weights.npy, b2_sony_B/cau/sony_B_weights_v42.npy, sources_v29/sony_B_weights.npy
  · sony_weight_G = wA_G + wB_G deformats (als originals és exacte); sony_support = l'ORIGINAL deformat (segona tirada; la reconstrucció (wA > 0) | (wB > 0)
    només coincideix amb l'original al 99,98 %: hi sobren 16.219 píxels a la vora de la B)
  · la fusió congelada de la V98 (congela): la fracció d'A sony_fA_v42.npy es deforma amb el camp d'A (les seves vores són les d'A, amb esvaïment
    llarg; a la vora de B la fracció ja és ~1); ρ, δ i el pes de la Vixen són de la Vixen o de baixa freqüència i es clonen tal qual.
Ús: f5_warp_sony.py <carpeta_f1 amb F4_MODEL.json> <carpeta_sortida>"""
import sys, json, time, shutil, hashlib, importlib.util, numpy as np, cv2
from pathlib import Path
from scipy import ndimage as ndi
F1, OUT = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(); OUT.mkdir(parents=True, exist_ok=True)
R = Path(__file__).resolve().parents[3]; t0 = time.time(); H, W = 7506, 10551
def log(*a): print(f'[{time.time() - t0:5.0f}s]', *a, flush=True)
spec = importlib.util.spec_from_file_location('camp_v120', Path(__file__).with_name('camp_v120.py')); f4 = importlib.util.module_from_spec(spec); spec.loader.exec_module(f4)   # el camp definitiu (autosuficient)
import os; MODEL_NOM = os.environ.get('V120_MODEL', 'CAMP_V120.json'); MODEL = json.load(open(F1 / MODEL_NOM))
def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 24), b''): h.update(b)
    return h.hexdigest()
MAPS = {}
def mapes(X):
    """mapx, mapy (float32) tals que X'(q) = X(mapx(q), mapy(q))."""
    if X in MAPS: return MAPS[X]
    mx = np.empty((H, W), np.float32); my = np.empty((H, W), np.float32); xs = np.arange(W, dtype=np.float64)
    for y0 in range(0, H, 256):
        yy = np.arange(y0, min(H, y0 + 256), dtype=np.float64)[:, None] * np.ones((1, W)); xx = np.ones((len(yy), 1)) * xs[None, :]
        ux, uy = f4.camp(MODEL, X, xx, yy); px, py = xx - ux, yy - uy          # 1a iteració
        ux, uy = f4.camp(MODEL, X, px, py); mx[y0:y0 + len(yy)] = xx - ux; my[y0:y0 + len(yy)] = yy - uy   # 2a: q − u(q − u(q))
    MAPS[X] = (mx, my); return MAPS[X]
def warp_dades(src_path, X, dst_name):
    a = np.load(src_path, mmap_mode='r'); mx, my = mapes(X); out = np.lib.format.open_memmap(OUT / dst_name, mode='w+', dtype=np.float32, shape=a.shape)
    nch = a.shape[2] if a.ndim == 3 else 1; st = {}
    for c in range(nch):
        ch = np.asarray(a[..., c] if a.ndim == 3 else a, np.float32); val = np.isfinite(ch) & (ch > 0)
        d = cv2.remap(np.where(val, ch, 0).astype(np.float32), mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        v = cv2.remap(val.astype(np.float32), mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0) > 0.999
        v = ndi.binary_erosion(v, iterations=2)
        # (V120, segona tirada) on el peu del cúbic tocaria la vora de la dada, bilineal NORMALITZAT (només amb dada, sense barrejar-hi zeros):
        # amb el camp esvaït (f10), a la vora del marc el desplaçament és de mil·lèsimes de píxel i el marc es conserva sencer
        vl = cv2.remap(val.astype(np.float32), mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        dl = cv2.remap(np.where(val, ch, 0).astype(np.float32), mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0) / np.maximum(vl, 1e-6)
        r = np.where(v & (d > 0), d, np.where((vl > 0.5) & (dl > 0), dl, np.nan)).astype(np.float32); del vl, dl
        if a.ndim == 3: out[..., c] = r
        else: out[:] = r
        st[str(c)] = dict(valids_abans=int(val.sum()), valids_despres=int(np.isfinite(r).sum()))
    out.flush(); del out; log('dades', dst_name, st); return st
def warp_pes(src_path, X, dst_name=None, torna=False):
    a = np.load(src_path, mmap_mode='r'); mx, my = mapes(X); res = np.empty(a.shape, np.float32)
    for c in range(a.shape[2] if a.ndim == 3 else 1):
        ch = np.nan_to_num(np.asarray(a[..., c] if a.ndim == 3 else a, np.float32))
        r = cv2.remap(ch, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        if a.ndim == 3: res[..., c] = r
        else: res[:] = r
    if dst_name: np.save(OUT / dst_name, res); log('pes', dst_name)
    return res
AP = R / '4-RESULTATS/v108_20260926/flat2d_v5/apilats'; S29 = R / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/sources_v29'; B2 = R / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/b2_sony_B/cau'
ENT = {'sony_A_total_v113vora.npy': (R / '4-RESULTATS/v112_claude_20260928/fonts_v113_vora/apilats/sony_A_total.npy', 'A'),
       'sony_A_total_flat2d_v5.npy': (AP / 'sony_A_total.npy', 'A'),
       'sony_B_total_v42.npy': (AP / 'cau/sony_B_total_v42.npy', 'B')}
rep = dict(guio=str(Path(__file__).relative_to(R)), model=str((F1 / MODEL_NOM).relative_to(R)), sha_model=sha(F1 / MODEL_NOM), fitxers={})
for dst, (src, X) in ENT.items():
    rep['fitxers'][dst] = dict(font=str(src.relative_to(R)), camp=X, sha_font=sha(src), validesa=warp_dades(src, X, dst))
wA = warp_pes(S29 / 'sony_A_weights.npy', 'A', 'sony_A_weights.npy'); rep['fitxers']['sony_A_weights.npy'] = dict(font=str((S29 / 'sony_A_weights.npy').relative_to(R)), camp='A')
warp_pes(B2 / 'sony_B_weights_v42.npy', 'B', 'sony_B_weights_v42.npy'); rep['fitxers']['sony_B_weights_v42.npy'] = dict(font=str((B2 / 'sony_B_weights_v42.npy').relative_to(R)), camp='B')
wB0 = warp_pes(S29 / 'sony_B_weights.npy', 'B', 'sony_B_weights.npy'); rep['fitxers']['sony_B_weights.npy'] = dict(font=str((S29 / 'sony_B_weights.npy').relative_to(R)), camp='B')
np.save(OUT / 'sony_weight_G.npy', (wA[..., 1] + wB0[..., 1]).astype(np.float32))
# (V120, segona tirada) el suport: l'ORIGINAL deformat (amb el camp d'A i amb el de B, unió), dins d'on hi ha pes. La reconstrucció (wA > 0) | (wB > 0)
# inclou 16.219 píxels que l'original exclou a la vora del marc de la B, i la 56 hi agafava dada que a la V119 no hi era. Amb el camp esvaït, a la
# vora del marc el suport surt IDÈNTIC a l'original; només es mou la vora de la Lluna.
so = np.load(S29 / 'sony_support.npy').astype(np.float32); sup = np.zeros(so.shape, bool)
for X in ('A', 'B'):
    mx, my = mapes(X); sup |= cv2.remap(so, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0) > 0.5
sup &= (wA[..., 1] > 0) | (wB0[..., 1] > 0); np.save(OUT / 'sony_support.npy', sup)
so = so > 0.5; rr_ = np.hypot(*np.meshgrid(np.arange(W) - 5361.768, np.arange(H) - 3775.748)) / 440.603; dif = so != sup
rep['fitxers']['sony_weight_G.npy'] = 'wA_G + wB_G (deformats)'
rep['fitxers']['sony_support.npy'] = dict(font=str((S29 / 'sony_support.npy').relative_to(R)), regla="l'original deformat amb els camps d'A i de B (unió), dins de (wA_G > 0) | (wB_G > 0)",
                                          diferents_de_l_original=int(dif.sum()), diferents_a_r_mes_de_1_2_Rsol=int((dif & (rr_ > 1.2)).sum()))
log('suport', rep['fitxers']['sony_support.npy']); del wA, wB0, so, sup, rr_, dif
# la fusió congelada: una còpia del control de la V98 amb la fracció d'A deformada
CG = R / '4-RESULTATS/v98_20260925/cadena_v98/b3'; CO = OUT / 'congela_b3'; (CO / 'cau').mkdir(parents=True, exist_ok=True); (CO / 'receipts').mkdir(exist_ok=True)
for nom in ('rho_v42.npy', 'delta_v42.npy', 'weight_vixen_v42.npy'):
    if not (CO / 'cau' / nom).exists(): import subprocess; subprocess.run(['cp', '-c', str(CG / 'cau' / nom), str(CO / 'cau' / nom)], check=True)
shutil.copy(CG / 'receipts/B3_fusio.json', CO / 'receipts/B3_fusio.json')
fa = warp_pes(CG / 'cau/sony_fA_v42.npy', 'A'); np.save(CO / 'cau/sony_fA_v42.npy', np.clip(fa, 0, 1).astype(np.float32))
rep['congela'] = dict(font=str(CG.relative_to(R)), sony_fA_v42='deformada amb el camp d\'A', clonats=['rho_v42.npy', 'delta_v42.npy', 'weight_vixen_v42.npy', 'receipts/B3_fusio.json'])
# mapes de desplaçament (a 1/4) per al rebut i les vistes
for X in ('A', 'B'):
    mx, my = mapes(X); yy, xx = np.mgrid[0:H, 0:W]
    np.save(OUT / f'camp_{X}_u_quart.npy', np.stack([(xx - mx)[::4, ::4], (yy - my)[::4, ::4]], 0).astype(np.float16))
rep['segons'] = round(time.time() - t0, 1); json.dump(rep, open(OUT / 'F5_REBUT.json', 'w'), ensure_ascii=False, indent=1); log('fet')
