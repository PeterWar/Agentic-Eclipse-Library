"""Comú dels passos de la V97 que parteixen de les eines de la V86/V88 (franja d'un instant i filtres). Rutes relatives a l'arrel.
Les fonts lineals i la carpeta de sortida es trien amb variables d'entorn (per poder córrer el control i la V97 amb el mateix codi):
  V97_FONTS  carpeta amb base_G.npy, fusion_starless.npy, vixen_starless.npy, sony_starless.npy, support.npy (per defecte, el d4 del control regenerat)
  V97_SORT   carpeta de sortida (per defecte 4-RESULTATS/v97_refundacio_20260924/lineal_v97)
La caixa lunar per fotograma (limb_frames) és la regenerada des dels RAW (idèntica a la de la V85)."""
from pathlib import Path
import json, hashlib, sys, time, os
import numpy as np
ARREL = Path(__file__).resolve().parents[3]
RES = ARREL / '4-RESULTATS/v97_refundacio_20260924'
SORT = Path(os.environ.get('V97_SORT', RES / 'lineal_v97')); SORT = SORT if SORT.is_absolute() else ARREL / SORT; SORT.mkdir(parents=True, exist_ok=True)
V85D = RES / 'cadena_raw'                                  # substitueix 4-RESULTATS/v85_regeneracio_20260922 (regenerat bit a bit)
FONTS = Path(os.environ.get('V97_FONTS', V85D / 'd4_baseline/products/sources')); FONTS = FONTS if FONTS.is_absolute() else ARREL / FONTS
H, W = 7506, 10551
CX, CY, RS = 5361.768111973117, 3775.747534140857, 440.60304883027544
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917')); sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v86_neta_20260923'))
def log(s): print(time.strftime('%H:%M:%S'), s, flush=True)
def sha(p):
    with open(p, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def desa_json(nom, d):
    p = SORT / nom; p.write_text(json.dumps(d, ensure_ascii=False, indent=2, default=lambda v: v.item() if isinstance(v, np.generic) else v.tolist()) + '\n'); return p
def claim():
    return None  # 30-09-2026: regla de l'escriptor únic retirada per Pere
    p = ARREL / '.coordination/claim.lock/owner.json'
    assert p.exists(), 'cal un claim viu (.coordination/claim.lock)'
    o = json.loads(p.read_text()); assert 'HELD' in (o.get('serial_writes'), o.get('status')), o
def coords():
    y, x = np.ogrid[:H, :W]; return np.hypot(y - CY, x - CX).astype('float32'), np.arctan2(y - CY, x - CX).astype('float32')
