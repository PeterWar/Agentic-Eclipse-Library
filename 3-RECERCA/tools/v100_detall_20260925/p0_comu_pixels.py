"""p0 (V100 detall · PÍXELS) · comú: fonts de lectura (NOMÉS LECTURA), geometria de presentació, lluminància lineal i ln.
Totes les fonts es porten a coordenades del LLENÇ natiu 10551×7506 (x cap a la dreta, y cap avall).
- V80.tif (Pere, 17-09, enquadrament final 8023×5121): hipòtesi llenç = fitxer + (1325, 1142); p1 ho verifica.
- V98_lluna.tif / V99_lluna.tif (vistes natives, retall [4600,3000,6150,4550] del llenç).
- V69/V71/V78.tif i V75_Corretgit.tif (~/Downloads, llenç sencer, època de la V75): opcionals, mateix llenç.
Cau de retalls al scratchpad (variable PIX_CAU) per no rellegir TIFs d'1 GB; mai s'escriu al projecte fora de les carpetes v100."""
import os
from pathlib import Path
import numpy as np
import tifffile

ARREL = Path(__file__).resolve().parents[3]
EINES = ARREL / '3-RECERCA/tools/v100_detall_20260925'
SORT = ARREL / '4-RESULTATS/v100_detall_20260925/pixels'
CAU = Path(os.environ.get('PIX_CAU', '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/cfee1433-3fe6-4216-bf6a-d5e08d6f606b/scratchpad/pix_cau'))
HOME = Path.home()

LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736  # Lluna de presentació
SX, SY, RS = 5361.768, 3775.748, 440.603                            # Sol
D29 = ARREL / '4-RESULTATS/v100_detall_20260925/D29_candidat_banda.npz'
SIL = ARREL / '4-RESULTATS/v99_banda_20260925/D21_silueta_o2.npz'

# nom: (ruta, (ox, oy) amb llenç = fitxer + (ox, oy))
FONTS = {
    'V80': (ARREL / '1-PHOTOSHOP/V80.tif', (1325, 1142)),
    'V98': (ARREL / '4-RESULTATS/v98_20260925/vistes/V98_lluna.tif', (4600, 3000)),
    'V99': (ARREL / '4-RESULTATS/v99_banda_20260925/B/vistes/V99_lluna.tif', (4600, 3000)),
    'V69': (HOME / 'Downloads/V69.tif', (0, 0)),
    'V71': (HOME / 'Downloads/V71.tif', (0, 0)),
    'V75C': (HOME / 'Downloads/V75_Corretgit.tif', (0, 0)),
    'V78': (HOME / 'Downloads/V78.tif', (0, 0)),
}
# finestra de treball comuna al llenç (y0, y1, x0, x1): la de les vistes natives V98/V99
FIN = (3000, 4550, 4600, 6150)


def llegeix_finestra(nom, fin=FIN, marge=0):
    """RGB uint16 de la font `nom` a la finestra del llenç `fin` (+ marge), amb la hipòtesi d'offset de FONTS.
    Fora del fitxer, zeros. Desa una còpia al scratchpad (CAU)."""
    ruta, (ox, oy) = FONTS[nom]
    y0, y1, x0, x1 = fin[0] - marge, fin[1] + marge, fin[2] - marge, fin[3] + marge
    CAU.mkdir(parents=True, exist_ok=True)
    c = CAU / f'{nom}_{y0}_{y1}_{x0}_{x1}.npy'
    if c.exists():
        return np.load(c)
    im = tifffile.imread(ruta)
    if im.ndim == 3 and im.shape[2] > 3:
        im = im[..., :3]
    H, W = im.shape[:2]
    out = np.zeros((y1 - y0, x1 - x0, 3), np.uint16)
    fy0, fy1, fx0, fx1 = y0 - oy, y1 - oy, x0 - ox, x1 - ox
    sy0, sy1, sx0, sx1 = max(fy0, 0), min(fy1, H), max(fx0, 0), min(fx1, W)
    if sy1 > sy0 and sx1 > sx0:
        out[sy0 - fy0:sy1 - fy0, sx0 - fx0:sx1 - fx0] = im[sy0:sy1, sx0:sx1, :3]
    del im
    np.save(c, out)
    return out


def lin_adobe(rgb16):
    """Adobe RGB (1998) codificat → lineal [0,1] (gamma 563/256)."""
    return (rgb16.astype(np.float64) / 65535.0) ** 2.19921875


def lluminancia(rgb16):
    L = lin_adobe(rgb16)
    return 0.2973769 * L[..., 0] + 0.6273491 * L[..., 1] + 0.0752741 * L[..., 2]


def ln_lum(rgb16, eps=1e-6):
    return np.log(lluminancia(rgb16) + eps)


def geometria(fin=FIN):
    """d (distància al cercle de presentació, px) i PA (graus, 90 = dalt, 180 = esquerra) a la finestra."""
    y0, y1, x0, x1 = fin
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float64)
    d = np.hypot(xx - LX, yy - LY) - RL
    pa = (np.degrees(np.arctan2(-(yy - LY), xx - LX)) + 360) % 360
    return d, pa


def d29_a_finestra(clau, fin=FIN):
    """Una clau de D29 (caixa [3077,4477,4677,6077]) posada a la finestra FIN; fora de la caixa, NaN."""
    z = np.load(D29)
    by0, by1, bx0, bx1 = z['box']
    a = z[clau]
    y0, y1, x0, x1 = fin
    out = np.full((y1 - y0, x1 - x0) + a.shape[2:], np.nan, np.float64)
    out[by0 - y0:by1 - y0, bx0 - x0:bx1 - x0] = a
    return out
