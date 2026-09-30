"""Comú per a la diagnosi de les marques de Pere a la V88 i de la cua de la protuberància esquerra (Claude, 23-09-2026, tarda).
Rutes relatives a l'arrel del projecte. Només lectura de 1-PHOTOSHOP/V90.psb (el de Pere, desat a les 21:43)."""
from pathlib import Path
import json, hashlib, sys, time
import numpy as np
ARREL = Path(__file__).resolve().parents[3]
EINES = ARREL / '3-RECERCA/tools/v88_marques_pere_20260923'
SORT = ARREL / '4-RESULTATS/v90_marques_pere_20260923'
V88D = ARREL / '4-RESULTATS/v88_20260923'
PSB_PERE = ARREL / '1-PHOTOSHOP/V90.psb'
PSB_MEU = V88D / 'V88_stage.psb'     # el meu muntatge abans del desament natiu (el V88.psb natiu de les 15:08 ja no hi és: Pere l'ha desat a sobre)
H, W = 7506, 10551
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917')); sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v86_neta_20260923'))
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v88_20260923'))
GEO = json.loads((V88D / 'A2_GEOMETRIA.json').read_text())['lluna_presentacio']
def log(s): print(time.strftime('%H:%M:%S'), s, flush=True)
def sha(p):
    with open(p, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def desa_json(nom, d):
    p = SORT / nom; p.write_text(json.dumps(d, ensure_ascii=False, indent=2, default=lambda v: v.item() if isinstance(v, np.generic) else v.tolist()) + '\n'); return p
def claim():
    p = ARREL / '.coordination/claim.lock/owner.json'
    assert p.exists(), 'cal un claim viu (.coordination/claim.lock)'
    o = json.loads(p.read_text()); assert 'HELD' in (o.get('serial_writes'), o.get('status')), o
