"""r1 (V106 · passa-banda DoG 1,2–6 px sobre ln: només estructura), Claude, 26-09-2026) · Registre CORONAL de cada fotograma contra el règim net, lluny del limbe (el que el Codex va deixar NOT_RUN).
Per a cada fotograma j: V_j ≈ g·B(x − s) + b ≈ g·B − g·s·∇B + b, per mínims quadrats lineals (g, g·sx, g·sy, b) sobre els píxels de 20–150 px del limbe
de presentació amb pes del fotograma i veritat (B = mitjana dels ALTRES fotogrames que veuen el píxel a D ≥ 6 px), en ln per no dependre del nivell.
Es fa per quadrants per veure si el desplaçament és una translació. Si s ≈ δ (el desplaçament de la Lluna de b1), és un error de registre del
fotograma sencer; si s ≈ 0, és un error de la posició de la Lluna.
Sortida: 4-RESULTATS/v106_inversio_20260926/r1/R1_REGISTRE_CORONAL.json"""
import os, json, numpy as np, cv2
from pathlib import Path
R0 = Path(__file__).resolve().parents[3]
LF = Path(os.environ.get('V105_LF', str(R0 / '4-RESULTATS/v106_inversio_20260926/limb_frames_sense_llindar')))
O = R0 / '4-RESULTATS/v106_inversio_20260926/r1'; O.mkdir(parents=True, exist_ok=True)
meta = json.loads((LF / 'METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']
num = np.load(LF / 'numerator.npy', mmap_mode='r'); wt = np.load(LF / 'weight.npy', mmap_mode='r'); Dm = np.load(LF / 'distance_model.npy', mmap_mode='r')
geo = json.loads((R0 / '4-RESULTATS/v97_refundacio_20260924/lineal_v97_franja/A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = geo['cx'], geo['cy'], geo['R']
Rm = float(meta['radius_model']); DR = Rm - R; nF = len(fr); hb, wb = by1 - by0, bx1 - bx0
yy, xx = np.mgrid[by0:by1, bx0:bx1]; dP = np.hypot(xx - cx, yy - cy) - R; th = np.degrees(np.arctan2(-(yy - cy), xx - cx)) % 360
def ss(x, a, b): q = np.clip((x - a) / (b - a), 0, 1); return q * q * (3 - 2 * q)
C = 1
V = np.zeros((nF, hb, wb), np.float32); Wg = np.zeros((nF, hb, wb), np.float32); S = np.zeros((nF, hb, wb), np.float32)
for j in range(nF):
    w = np.asarray(wt[j, :, :, C]); n = np.asarray(num[j, :, :, C]); Wg[j] = w; V[j] = np.where(w > 0, n / np.maximum(w, 1e-30), 0)
    S[j] = ss(np.asarray(Dm[j]) + DR, 6, 9) * w
Stot = S.sum(0); Ntot = (S * V).sum(0)
zona = (dP > 20) & (dP < 150)
b1 = json.loads((R0 / '4-RESULTATS/v106_inversio_20260926/b1/B1_PSF_LOLA_canal1.json').read_text())['fotogrames']; D1 = {r['j']: r for r in b1}
out = []
for j in range(nF):
    Sm = Stot - S[j]; B = np.where(Sm > 0, (Ntot - S[j] * V[j]) / np.maximum(Sm, 1e-30), 0).astype(np.float32)
    ok = zona & (Wg[j] > 0) & (B > 0) & (V[j] > 0) & (Sm > 0)
    if ok.sum() < 5000: continue
    lB = np.log(np.maximum(B, 1e-6)).astype(np.float32); lV = np.log(np.maximum(V[j], 1e-6)).astype(np.float32)
    dog = lambda a: cv2.GaussianBlur(a, (0, 0), 1.2) - cv2.GaussianBlur(a, (0, 0), 6.0)      # només l'estructura (passa-banda): el perfil radial no hi entra
    lB = dog(lB); lV = dog(lV); gy, gx = np.gradient(lB)
    row = dict(j=j, nom=fr[j]['name'], t=round(fr[j]['time'], 2), exp=fr[j]['exposure'])
    for nom, q in (('tot', ok), ('dreta', ok & ((th < 45) | (th >= 315))), ('dalt', ok & (th >= 45) & (th < 135)), ('esquerra', ok & (th >= 135) & (th < 225)), ('baix', ok & (th >= 225) & (th < 315))):
        if q.sum() < 2000: continue
        A = np.stack([lB[q], -gx[q], -gy[q]], 1); y = lV[q]
        c, *_ = np.linalg.lstsq(A, y, rcond=None)
        # lV ≈ c0 + c1·lB − sx·∂x lB − sy·∂y lB  →  desplaçament del fotograma respecte de la veritat (px; y cap avall)
        row[nom] = dict(sx=float(c[1] / max(c[0], 1e-6)), sy=float(c[2] / max(c[0], 1e-6)), pendent=float(c[0]), n=int(q.sum()))
    if j in D1: row['lluna_b1'] = dict(dx=D1[j]['dx'], dy=D1[j]['dy'])
    out.append(row)
    t_ = row.get('tot', {}); print(j, fr[j]['name'], 't', row['t'], 'corona s =', round(t_.get('sx', np.nan), 2), round(t_.get('sy', np.nan), 2), '· quadrants', {k: (round(row[k]['sx'], 2), round(row[k]['sy'], 2)) for k in ('dreta', 'dalt', 'esquerra', 'baix') if k in row}, '· Lluna b1', (round(D1[j]['dx'], 2), round(D1[j]['dy'], 2)) if j in D1 else None, flush=True)
(O / 'R1_REGISTRE_CORONAL.json').write_text(json.dumps(out, indent=1))
