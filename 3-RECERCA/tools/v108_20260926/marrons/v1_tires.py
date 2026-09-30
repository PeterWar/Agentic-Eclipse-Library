"""v1 · Tires «redreçades» de cada traç: la imatge remostrejada al sistema del traç (s al llarg, t perpendicular, ±tmax), amb el DoG
(σa − σb) estirat a ±lim. Ús: v1_tires.py <sortida.png> <font1> [<font2> …] [tmax=400] [sa=4] [sb=40] [lim=auto] [geo=m3|269] [ext=0]
font = npy[:canal] | psb:V107 (compost). ext = píxels d'allargament del traç a cada punta (per veure on comença i acaba)."""
import sys, json, struct
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_marrons import *
args = [a for a in sys.argv[1:] if '=' not in a]; kw = dict(a.split('=', 1) for a in sys.argv[1:] if '=' in a)
dst, fonts = args[0], args[1:]; tmax = float(kw.get('tmax', 400)); sa = float(kw.get('sa', 4)); sb = float(kw.get('sb', 40)); ext = float(kw.get('ext', 0))
geo = kw.get('geo', 'm3')
if geo == 'm3':
    g = json.loads((OUT / 'M3_GEOMETRIA.json').read_text())
    for tr in TRACOS:
        z = g[str(tr['k'])]; tr['centre'] = np.array(z['centre']); tr['d'] = np.array(z['direccio']); tr['n'] = np.array([-tr['d'][1], tr['d'][0]])
def carrega(f, box):
    x0, y0, x1, y1 = box
    if f.startswith('psb:'):
        psb = ARREL / f'1-PHOTOSHOP/{f[4:]}.psb'
        with open(psb, 'rb') as fh:
            hdr = fh.read(26); nch = struct.unpack('>H', hdr[12:14])[0]
            n = struct.unpack('>I', fh.read(4))[0]; fh.seek(n, 1); n = struct.unpack('>I', fh.read(4))[0]; fh.seek(n, 1); n = struct.unpack('>Q', fh.read(8))[0]; fh.seek(n, 1); pos = fh.tell()
        mm = np.memmap(psb, dtype='>u2', mode='r', offset=pos + 2, shape=(nch, H, W)); return sum(np.asarray(mm[c, y0:y1, x0:x1], np.float32) for c in range(3)) / 3
    p, _, ch = f.partition(':'); a = np.load(p, mmap_mode='r')
    if a.ndim == 3 and a.shape[0] < 100:      # (n, H/4, W/4): no suportat aquí
        raise ValueError(f)
    a = a[..., int(ch)] if (ch and a.ndim == 3) else a
    return np.asarray(a[y0:y1, x0:x1], np.float32)
files = []
for f in fonts:
    rows = []
    for tr in TRACOS:
        L = tr['llarg'] + 2 * ext; tr2 = dict(tr, llarg=L); box = caixa(tr2, tmax + 60); x0, y0, x1, y1 = box
        img = carrega(f, box); m = np.isfinite(img) & (img != 0); w = m.astype(np.float32); img = np.where(m, img, 0)
        ng = lambda x, s: cv2.GaussianBlur(x * w, (0, 0), s) / np.maximum(cv2.GaussianBlur(w, (0, 0), s), 1e-6)
        rel = np.where(m, ng(img, sa) / np.maximum(ng(img, sb), 1e-12) - 1, np.nan).astype(np.float32)
        s, t, X, Y = graella(tr2, tmax=tmax, dt=2, ds=4); P = mostreja(rel, X, Y, (x0, y0))      # (ns, nt)
        lim = float(kw['lim']) if 'lim' in kw else 3 * np.nanstd(P)
        u = np.clip(128 + 127 * np.nan_to_num(P.T, nan=0) / lim, 0, 255).astype(np.uint8)   # files = t, columnes = s
        u = cv2.cvtColor(u, cv2.COLOR_GRAY2BGR); u[len(t) // 2, ::6] = (0, 0, 255)
        if ext: 
            for sx in (ext / 4, (L - ext) / 4): u[::6, int(sx)] = (0, 200, 0)
        cv2.putText(u, f"T{tr['k']} {Path(f).name if not f.startswith('psb') else f} lim {lim:.4f}", (5, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 220, 255), 1)
        rows.append(u)
    wmax = max(r.shape[1] for r in rows); rows = [np.pad(r, ((0, 6), (0, wmax - r.shape[1]), (0, 0)), constant_values=60) for r in rows]
    files.append(np.vstack(rows))
wmax = max(f.shape[1] for f in files); out = np.hstack([np.pad(f, ((0, max(x.shape[0] for x in files) - f.shape[0]), (0, 10), (0, 0)), constant_values=60) for f in files])
cv2.imwrite(dst, out); print(dst, out.shape)
