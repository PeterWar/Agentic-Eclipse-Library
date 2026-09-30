"""g2 (V106, «LOLA fi») · Mapes D_fina de tots els fotogrames a la caixa lunar (67 × 1400 × 1400, float32, px): distància al limbe real de cada
fotograma (geom_fina, variant «lola», relleu LOLA-64 suavitzat σ 1,25 px = nucli de la PSF). Positiu = fora de la Lluna. Fotogrames no mesurables
(mesurat = False a GEOMETRIA_FINA.npz): geometria del model + comuns + LOLA, sense correcció pròpia."""
import numpy as np, json
from pathlib import Path
from geom_fina import G
from vora_lib import by0, by1, bx0, bx1, nF
H = Path(__file__).parent
yy, xx = np.mgrid[by0:by1, bx0:bx1].astype(np.float64)
out = np.lib.format.open_memmap(H / 'D_FINA_nucli.npy', mode='w+', dtype=np.float32, shape=(nF, by1 - by0, bx1 - bx0))
for j in range(nF):
    out[j] = G.dfina(j, xx, yy, 1.25, 'lola').astype(np.float32)
out.flush()
(H / 'D_FINA_nucli.json').write_text(json.dumps(dict(forma=[nF, by1 - by0, bx1 - bx0], caixa_y0y1x0x1=[by0, by1, bx0, bx1], unitat='px', signe='positiu = fora de la Lluna',
    geometria='GEOMETRIA_FINA.npz (variant lola, sigma relleu 1,25 px)', mesurats=[int(j) for j in np.nonzero(G.mesurat)[0]]), indent=1))
print('fet', out.shape)
