"""Dues regions 1:1: plomalls sobre el limbe, i cel a ~3,5 R☉."""
import sys, numpy as np, cv2, tifffile
sys.path.insert(0, "/Users/USUARI/Downloads/Eclipse 2026/research/tools")
import hdr_corona_vixen as M
cy = 4638/2.0 - M.RETALL[0]; cx = 6958/2.0 - M.RETALL[2]
R = M.R_SOL_PX
ZONES = [("plomalls", int(cx-450), int(cy-1.05*R-820), 900, 820),
         ("cel 3,5 R☉", int(cx+3.1*R), int(cy-1.2*R), 900, 820)]
tires = []
for nom in sys.argv[1:]:
    a = tifffile.imread(M.OUT / nom)
    a = a.astype(np.float32)/65535.0 if a.dtype == np.uint16 else a.astype(np.float32)
    col = []
    for et, x0, y0, w, h in ZONES:
        c = np.ascontiguousarray((np.clip(a[y0:y0+h, x0:x0+w],0,1)*255)
                                 .astype(np.uint8)[..., ::-1])
        cv2.putText(c, f"{nom.replace('corona_vixen_','').replace('.tif','')} · {et}",
                    (12, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
        col.append(c)
    tires.append(np.concatenate(col, axis=0)); del a
d = "/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/8222da38-0c6f-46a7-867a-f0224834d74e/scratchpad/retall2.png"
cv2.imwrite(d, np.concatenate(tires, axis=1)); print(d)
