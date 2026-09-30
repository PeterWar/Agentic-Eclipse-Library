import sys, math
import numpy as np
sys.path.insert(0, "/Users/USUARI/Downloads/Eclipse 2026/research/tools")
import hdr_corona_vixen as M
SP = "/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/8222da38-0c6f-46a7-867a-f0224834d74e/scratchpad/"
z = np.load(SP + "bandes.npz")
lnorm = z["lnorm"]; valid = z["valid"]
H, W = valid.shape
cy, cx = H / 2.0, W / 2.0
r = M.anells(H, W, cy, cx); rs = r / M.R_SOL_PX
yy = np.abs(np.arange(H) - cy)[:, None] * np.ones((1, W), np.float32)
print("files vàlides: primera/última fila amb algun vàlid:", int(np.argmax(valid.any(1))), int(H - 1 - np.argmax(valid.any(1)[::-1])))
print("columnes vàlides:", int(np.argmax(valid.any(0))), int(W - 1 - np.argmax(valid.any(0)[::-1])))
# perfil de ln(norm) per files a la vora superior (mitjana sobre x central), respecte de la fila 200 més endins
for y0 in range(0, 140, 10):
    rows = slice(y0, y0 + 10)
    m = valid[rows, 2500:4500]
    v = lnorm[rows, 2500:4500][m]
    print(f"files {y0}-{y0+9}: n={m.sum():6d} ln(norm) mitjà {100*float(v.mean()) if v.size else float('nan'):+.2f} %")
print("--- anell 5.08–5.12 Rsol: amb i sense la tangència (|y-cy|>2200)")
m = valid & (rs > 5.08) & (rs < 5.12)
tang = yy > 2200
print(f"tot: {100*float(lnorm[m].mean()):+.3f}  sense tangència: {100*float(lnorm[m & ~tang].mean()):+.3f}  només tangència: {100*float(lnorm[m & tang].mean()):+.3f} (n={int((m&tang).sum())} de {int(m.sum())})")
m = valid & (rs > 5.00) & (rs < 5.06)
print(f"5.00–5.06 tot: {100*float(lnorm[m].mean()):+.3f} sense tang: {100*float(lnorm[m & ~tang].mean()):+.3f}")
m = valid & (rs > 4.80) & (rs < 4.90)
print(f"4.80–4.90 tot: {100*float(lnorm[m].mean()):+.3f} sense tang: {100*float(lnorm[m & ~tang].mean()):+.3f}")
# vora esquerra/dreta
xx = np.abs(np.arange(W) - cx)[None, :] * np.ones((H, 1), np.float32)
for x0 in range(0, 140, 10):
    cols = slice(x0, x0 + 10)
    m = valid[1500:3100, cols]
    v = lnorm[1500:3100, cols][m]
    print(f"cols {x0}-{x0+9}: n={m.sum():6d} ln(norm) {100*float(v.mean()) if v.size else float('nan'):+.2f} %")
