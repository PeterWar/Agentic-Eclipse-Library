"""v0 · Vista de diagnòstic del LLENÇ SENCER: contrast relatiu local (gauss σa / gauss σb − 1) d'una imatge 2D, estirat a ±lim.
Ús: v0_vista_relativa.py <entrada: psb:V107 | npy[:canal]> <sortida.png> [pas=4] [sa=6] [sb=120] [lim=0.02] [marques=1]
Les marques de Pere (capa 269) es dibuixen com a contorn fi si marques=1."""
import sys, struct
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_marrons import *
src, dst = sys.argv[1], sys.argv[2]; kw = dict(a.split('=') for a in sys.argv[3:])
pas = int(kw.get('pas', 4)); sa = float(kw.get('sa', 6)); sb = float(kw.get('sb', 120)); lim = float(kw.get('lim', 0.02)); marq = kw.get('marques', '1') == '1'
if src.startswith('psb:'):
    psb = ARREL / f'1-PHOTOSHOP/{src[4:]}.psb'
    with open(psb, 'rb') as f:
        hdr = f.read(26); nch = struct.unpack('>H', hdr[12:14])[0]
        n = struct.unpack('>I', f.read(4))[0]; f.seek(n, 1); n = struct.unpack('>I', f.read(4))[0]; f.seek(n, 1); n = struct.unpack('>Q', f.read(8))[0]; f.seek(n, 1)
        pos = f.tell(); assert struct.unpack('>H', f.read(2))[0] == 0
    mm = np.memmap(psb, dtype='>u2', mode='r', offset=pos + 2, shape=(nch, H, W))
    img = sum(np.asarray(mm[c], np.float32) for c in range(3)) / 3
    valid = img > 0
else:
    p, _, ch = src.partition(':'); a = np.load(p, mmap_mode='r')
    img = np.asarray(a[..., int(ch)] if ch else a, np.float32)
    valid = np.isfinite(img) & (img > 0); img = np.where(valid, img, 0)
wv = valid.astype(np.float32)
if kw.get('radial', '0') == '1':
    # divideix pel perfil radial (mediana azimutal per anells de 4 px al voltant del Sol): treu la corba del perfil, no les línies
    yy, xx = np.mgrid[0:H, 0:W]; rb = (np.hypot(xx - SOL[0], yy - SOL[1]) / 4).astype(np.int32); del yy, xx
    k = valid & (img > 0); nb = rb.max() + 1; med = np.zeros(nb, np.float32)
    ordre = np.argsort(rb[k], kind='stable'); vals = img[k][ordre]; bins = rb[k][ordre]; cuts = np.searchsorted(bins, np.arange(nb + 1))
    for b in range(nb):
        if cuts[b + 1] > cuts[b]: med[b] = np.median(vals[cuts[b]:cuts[b + 1]])
    med = np.where(med > 0, med, np.interp(np.arange(nb), np.nonzero(med > 0)[0], med[med > 0]))
    img = np.where(valid, img / med[rb], 0).astype(np.float32); del rb
def ng(x, s): return cv2.GaussianBlur(x * wv, (0, 0), s) / np.maximum(cv2.GaussianBlur(wv, (0, 0), s), 1e-6)
rel = np.where(valid, ng(img, sa) / np.maximum(ng(img, sb), 1e-12) - 1, 0)
small = cv2.resize(rel, (W // pas, H // pas), interpolation=cv2.INTER_AREA)
u8 = np.clip(128 + 127 * small / lim, 0, 255).astype(np.uint8); rgb = cv2.cvtColor(u8, cv2.COLOR_GRAY2BGR)
if marq:
    z = np.load(OUT / 'marques_269.npz'); a4 = z['alfa']; org = z['org']
    m = np.zeros((H // 4 + 2, W // 4 + 2), np.uint8); y0, x0 = org[1] // 4, org[0] // 4
    m[y0:y0 + a4.shape[0], x0:x0 + a4.shape[1]] = (a4 > 2000)[:m.shape[0] - y0, :m.shape[1] - x0]
    m = cv2.resize(m[:H // 4, :W // 4], (W // pas, H // pas), interpolation=cv2.INTER_NEAREST)
    cnt, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); cv2.drawContours(rgb, cnt, -1, (40, 90, 200), 1)
cv2.putText(rgb, f'{Path(src).name}  contrast relatiu g{sa:g}/g{sb:g}-1, +-{100*lim:g} %  (llenc sencer, pas {pas})', (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0 * 4 / pas, (0, 220, 255), 2)
cv2.imwrite(dst, rgb); print('vista', dst, rgb.shape)
