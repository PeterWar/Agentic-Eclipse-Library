"""Comú per a la V88 (Claude, 23-09-2026). Rutes relatives a l'arrel del projecte (la carpeta de CLAUDE.md).
Els scripts de filtres de la V86 es copien aquí amb aquest mòdul en lloc de v86_comu: escriuen a 4-RESULTATS/v88_20260923."""
from pathlib import Path
import json, hashlib, sys, time
import numpy as np
ARREL = Path(__file__).resolve().parents[3]
EINES = ARREL / '3-RECERCA/tools/v88_20260923'
SORT = ARREL / '4-RESULTATS/v88_20260923'
SORT86 = ARREL / '4-RESULTATS/v86_neta_20260923'
V85D = ARREL / '4-RESULTATS/v85_regeneracio_20260922'
FONTS = V85D / 'd4_baseline/products/sources'          # suma lineal reproduïda des dels RAW (rèplica exacta de V58/D4)
H, W = 7506, 10551
CX, CY, RS = 5361.768111973117, 3775.747534140857, 440.60304883027544   # centre del Sol per efemèride i radi solar en px (common58)
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917')); sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v86_neta_20260923'))
def log(s): print(time.strftime('%H:%M:%S'), s, flush=True)
def sha(p):
    with open(p, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def desa_json(nom, d):
    p = SORT / nom; p.write_text(json.dumps(d, ensure_ascii=False, indent=2, default=lambda v: v.item() if isinstance(v, np.generic) else v.tolist()) + '\n'); return p
def claim():
    # SERIAL_WRITES: cap pas no escriu sense un claim viu a .coordination/claim.lock (la V88 va amb CLAUDE_V88_20260923)
    p = ARREL / '.coordination/claim.lock/owner.json'
    assert p.exists(), 'cal un claim viu (.coordination/claim.lock) abans de córrer els passos de la V88'
    o = json.loads(p.read_text()); assert 'HELD' in (o.get('serial_writes'), o.get('status')), o
def coords():
    y, x = np.ogrid[:H, :W]; return np.hypot(y - CY, x - CX).astype('float32'), np.arctan2(y - CY, x - CX).astype('float32')
