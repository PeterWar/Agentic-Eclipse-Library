"""Comú per a la V93 (Claude, 24-09-2026, nit desatesa). Rutes relatives a l'arrel del projecte."""
from pathlib import Path
import json, hashlib, sys, time
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v93_20260924'; H, W = 7506, 10551
CX, CY, RS = 5361.768111973117, 3775.747534140857, 440.60304883027544
for p_ in ('v73_marques_v71_20260917', 'v86_neta_20260923', 'v90_marques_pere_20260923'): sys.path.insert(0, str(ARREL / '3-RECERCA/tools' / p_))
PSB_PERE = ARREL / '1-PHOTOSHOP/V92.psb'
GEO = json.loads((ARREL / '4-RESULTATS/v92_20260924/A2_GEOMETRIA.json').read_text())['lluna_presentacio']
FILTRES = {48: '03v30', 50: '01', 52: '05', 53: '06', 54: 'P03_MGN', 43: 'P02_RHEF', 44: 'P02b_RHEF_ups0.35', 41: 'P01_NRGF', 42: 'P01_NRGF_extrap',
           47: '03', 49: '07', 51: '04', 45: 'P02c_RHEF_local60_native', 46: 'P02d_RHEF_local30_native', 55: 'P04_WOW', 56: 'P05_WOW_bilateral'}
def log(s): print(time.strftime('%H:%M:%S'), s, flush=True)
def sha(p):
    with open(p, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def desa_json(nom, d):
    p = SORT / nom; p.write_text(json.dumps(d, ensure_ascii=False, indent=2, default=lambda v: v.item() if isinstance(v, np.generic) else v.tolist()) + '\n'); return p
def claim():
    o = json.loads((ARREL / '.coordination/claim.lock/owner.json').read_text()); assert o.get('serial_writes') == 'HELD', o
