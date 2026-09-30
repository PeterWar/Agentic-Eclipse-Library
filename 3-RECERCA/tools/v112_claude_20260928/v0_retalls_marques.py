"""V112 (Claude, 28-09-2026): retalls de cada marca de «V111 artefactes» (capa 412), V111 contra la candidata del Codex.
Només lectura de 4-RESULTATS/v112_20260928; escriu a 4-RESULTATS/v112_claude_20260928/vistes/.
Tres panells per marca: V111 (render natiu sense la 412) · candidata Codex (desat natiu) · passa-alt de totes dues (σ 60 px),
amb el contorn de la marca de Pere. Mateix estirament als dos panells de cada fila."""
from pathlib import Path
import json
import numpy as np
import tifffile
from scipy import ndimage as ndi
from PIL import Image, ImageDraw

R = Path(__file__).resolve().parents[3]
C = R / '4-RESULTATS/v112_20260928'
O = R / '4-RESULTATS/v112_claude_20260928/vistes'
O.mkdir(parents=True, exist_ok=True)

ctrl = tifffile.memmap(C / 'control_natiu/visible_complet.tif')
cand = tifffile.memmap(C / 'sensor_mass301/final_natiu/visible_complet.tif')
mq = np.load(C / 'marques412.npz')
alpha, org = mq['alpha'], mq['origin']
marques = json.loads((C / 'MARQUES.json').read_text())
H, W = ctrl.shape[:2]


def lum(a):
    a = a.astype(np.float32)
    return (a[..., 0] + 2 * a[..., 1] + a[..., 2]) / 4


def estira(x, lo, hi):
    return np.clip((x - lo) / max(hi - lo, 1e-6) * 255, 0, 255).astype(np.uint8)


for m in marques:
    x0, y0, x1, y1 = m['box']
    mx = max(250, (x1 - x0) // 3); my = max(250, (y1 - y0) // 3)
    X0, Y0, X1, Y1 = max(0, x0 - mx), max(0, y0 - my), min(W, x1 + mx), min(H, y1 + my)
    a = np.asarray(ctrl[Y0:Y1, X0:X1]); b = np.asarray(cand[Y0:Y1, X0:X1])
    La, Lb = lum(a), lum(b)
    val = La > 300
    lo, hi = (np.percentile(La[val], [0.5, 99.5]) if val.any() else (0, 65535))
    # passa-alt: log(L) − gaussiana σ 60, mateixa escala als dos
    ha = np.log(np.maximum(La, 50)) - ndi.gaussian_filter(np.log(np.maximum(La, 50)), 60)
    hb = np.log(np.maximum(Lb, 50)) - ndi.gaussian_filter(np.log(np.maximum(Lb, 50)), 60)
    s = np.percentile(np.abs(ha[val]), 99) if val.any() else 0.05
    pa = [estira(La, lo, hi), estira(Lb, lo, hi), estira(ha, -s, s), estira(hb, -s, s)]
    # contorn de la marca
    al = np.zeros((Y1 - Y0, X1 - X0), bool)
    ay0, ax0 = Y0 - org[1], X0 - org[0]
    sub = alpha[max(0, ay0):max(0, ay0) + (Y1 - Y0), max(0, ax0):max(0, ax0) + (X1 - X0)] > 0
    al[:sub.shape[0], :sub.shape[1]] = sub
    vora = al & ~ndi.binary_erosion(al, iterations=3)
    panells = []
    for k, p in enumerate(pa):
        rgb = np.stack([p] * 3, -1)
        if k in (0, 2):
            rgb[vora] = (255, 0, 255)
        panells.append(rgb)
    fila1 = np.concatenate([panells[0], panells[1]], 1)
    fila2 = np.concatenate([panells[2], panells[3]], 1)
    im = Image.fromarray(np.concatenate([fila1, fila2], 0))
    esc = min(1.0, 2000 / im.width, 2000 / im.height)
    if esc < 1:
        im = im.resize((int(im.width * esc), int(im.height * esc)), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    d.text((8, 8), f"marca {m['id']} · V111 (contorn lila) | candidata Codex · a baix: passa-alt sigma 60 · caixa {X0},{Y0}-{X1},{Y1}", fill=(255, 255, 0))
    im.save(O / f"marca_{m['id']:02d}.png")
    print(m['id'], (X0, Y0, X1, Y1), 'esc', round(esc, 3))
