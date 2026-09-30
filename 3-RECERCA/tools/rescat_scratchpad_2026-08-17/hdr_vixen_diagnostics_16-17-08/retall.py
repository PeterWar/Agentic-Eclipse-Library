"""Retall 1:1 comparable amb la captura de Pere: sobre la Lluna, cap enfora."""
import sys, numpy as np, cv2, tifffile
sys.path.insert(0, "/Users/USUARI/Downloads/Eclipse 2026/research/tools")
import hdr_corona_vixen as M

# el compost té el Sol al centre; el retall aplica RETALL[0], RETALL[2]
cy = 4638/2.0 - M.RETALL[0]
cx = 6958/2.0 - M.RETALL[2]
AMPL, ALT = 1100, 1180
x0 = int(cx - AMPL/2)
y0 = int(cy - 1.05*M.R_SOL_PX - ALT)     # just per damunt del limbe, cap amunt
tires = []
for nom in sys.argv[1:]:
    a = tifffile.imread(M.OUT / nom)
    a = a.astype(np.float32)/65535.0 if a.dtype == np.uint16 else a.astype(np.float32)
    c = a[y0:y0+ALT, x0:x0+AMPL]
    c = np.ascontiguousarray((np.clip(c,0,1)*255).astype(np.uint8)[..., ::-1])
    cv2.putText(c, nom.replace("corona_vixen_","").replace(".tif",""),
                (14, 34), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255,255,255), 2)
    tires.append(c)
    del a
out = np.concatenate(tires, axis=1)
d = "/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/8222da38-0c6f-46a7-867a-f0224834d74e/scratchpad/retall_1a1.png"
cv2.imwrite(d, out)
print(d, out.shape)
