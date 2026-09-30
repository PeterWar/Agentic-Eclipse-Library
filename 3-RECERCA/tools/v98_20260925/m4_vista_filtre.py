"""m4 (V98) · Retall ampliat d'un ràster de filtre (npy u16 + alfa) de dues carpetes, costat a costat, amb el mateix estirament:
m4_vista_filtre.py <carpetaA> <carpetaB> <tag> x0 y0 x1 y1 <factor> <sortida.png> [--hp s]  (--hp: pas alt σ s abans d'estirar)"""
import sys
from pathlib import Path
import numpy as np, cv2
A, B, tag = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]; x0, y0, x1, y1, f = map(int, sys.argv[4:9]); out = sys.argv[9]
def carrega(c):
    u = np.load(c / f'{tag}_u16.npy', mmap_mode='r')[y0:y1, x0:x1].astype(np.float32) / 65535; a = np.load(c / f'{tag}_alfa_u16.npy', mmap_mode='r')[y0:y1, x0:x1].astype(np.float32) / 65535
    if '--hp' in sys.argv:
        s = float(sys.argv[sys.argv.index('--hp') + 1]); w = (a > 0.5).astype(np.float32); u = u - cv2.GaussianBlur(u * w, (0, 0), s) / np.maximum(cv2.GaussianBlur(w, (0, 0), s), 1e-6)
    return u, a
ua, aa = carrega(A); ub, ab = carrega(B)
lo, hi = np.percentile(np.concatenate([ua[aa > 0.99], ub[ab > 0.99]]), [1, 99])
def im(u, a):
    v = np.clip((u - lo) / (hi - lo), 0, 1); v = v * a + 0.12 * (1 - a); return cv2.resize((v * 255).astype(np.uint8), None, fx=f, fy=f, interpolation=cv2.INTER_NEAREST)
ia, ib = im(ua, aa), im(ub, ab); sep = np.full((ia.shape[0], 10), 255, np.uint8); cv2.imwrite(out, np.hstack([ia, sep, ib])); print(out)
