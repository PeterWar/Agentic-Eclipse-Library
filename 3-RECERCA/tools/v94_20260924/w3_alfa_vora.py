"""w3 (V94) · Alfa de les WOW noves: 0 on no hi ha dada (res inventat), 1 on n'hi ha, amb una fosa d'1,5 px a la VORA de la dada seguint la
corba contínua de la vora (d − DMIN(θ) a la Lluna; distància al suport a la resta), en comptes del graó píxel a píxel (fa una línia fina i
dentada on comença la textura, com el «cosit de cremallera» de la V87). Sortida: wow/<tag>_alfa_u16.npy (en guarda la de w1 com a _alfa_w1)."""
import sys, json, shutil
from pathlib import Path
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v94_20260924'; OUT = SORT / 'wow'
sys.path.insert(0, str(Path(__file__).parent)); from wow_domini import smoothstep
o = json.loads((ARREL / '.coordination/claim.lock/owner.json').read_text()); assert o.get('serial_writes') == 'HELD'
Q = np.load(ARREL / '4-RESULTATS/v88_20260923/A3A_franja_un_instant.npz'); qy0, qy1, qx0, qx1 = [int(v) for v in Q['box']]; cx, cy, R = [float(v) for v in Q['centre']]; DMIN = Q['DMIN']; NBZ = len(DMIN)
for tag in ('P05_WOW_bilateral', 'P04_WOW'):
    src = OUT / f'{tag}_alfa_w1.npy'
    if not src.exists(): shutil.copy2(OUT / f'{tag}_alfa_u16.npy', src)
    m = np.load(src) > 32767
    dist = cv2.distanceTransform(m.astype(np.uint8), cv2.DIST_L2, 5).astype(np.float32); al = smoothstep(dist, 0.0, 1.5) * m
    yy, xx = np.mgrid[qy0:qy1, qx0:qx1]; d = np.hypot(xx - cx, yy - cy) - R; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
    dv = d - DMIN[(th / 360 * NBZ).astype(int) % NBZ]; aprop = smoothstep(dv, 0.0, 1.5) * m[qy0:qy1, qx0:qx1]; lluna = d < 40
    al[qy0:qy1, qx0:qx1] = np.where(lluna, aprop, al[qy0:qy1, qx0:qx1])
    np.save(OUT / f'{tag}_alfa_u16.npy', np.round(al * 65535).astype(np.uint16)); print(tag, 'alfa: px parcials', int(((al > 0) & (al < 1)).sum()))
