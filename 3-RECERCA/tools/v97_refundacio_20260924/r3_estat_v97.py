"""r3 (V97) · Munta l'«estat V97» per al jutge i per al PSB: la base nova (f2b) i els 16 filtres nous (f3) amb el format de v96_ref
(L{id}_G/RGB.npy, L{id}_alfa.npy, L{id}_mascara.npy + CAPES.json); la resta de capes, clons APFS de v96_ref (idèntiques a la V96).
Propietats (mode, opacitat, visibilitat) i màscares de Pere: les de la V96, sense tocar. Alfa: la base, plena (com la V96); les capes en
Multiplicar, plena (nivell al buit); les altres, la del domini de dada. Ús: r3_estat_v97.py <filtres_dir> <base_u16.npy> <sortida>"""
import sys, json, subprocess, shutil
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; RES = ARREL / '4-RESULTATS/v97_refundacio_20260924'; REF = RES / 'v96_ref'
FIL, BASE, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]); OUT.mkdir(parents=True, exist_ok=True)
TAG = {41: 'P01_NRGF', 42: 'P01_NRGF_extrap', 43: 'P02_RHEF', 44: 'P02b_RHEF_ups0.35', 45: 'P02c_RHEF_local60_native', 46: 'P02d_RHEF_local30_native',
       47: '03', 48: '03v30', 49: '07', 50: '01', 51: '04', 52: '05', 53: '06', 54: 'P03_MGN', 55: 'P04_WOW', 56: 'P05_WOW_bilateral'}
meta = json.loads((REF / 'CAPES_V96.json').read_text()); nous = {}
def clona(src, dst):
    if dst.exists(): dst.unlink()
    subprocess.run(['cp', '-c', str(src), str(dst)], check=True)
for f in REF.glob('L*.npy'):
    lid = int(f.name[1:].split('_')[0])
    if lid == 3 or lid in TAG: continue
    clona(f, OUT / f.name)
# base
if (OUT / 'L3_RGB.npy').resolve() != BASE.resolve(): clona(BASE, OUT / 'L3_RGB.npy')
clona(REF / 'L3_alfa.npy', OUT / 'L3_alfa.npy'); clona(REF / 'L3_mascara.npy', OUT / 'L3_mascara.npy'); nous[3] = str(BASE)
for lid, tag in TAG.items():
    u = FIL / f'{tag}_u16.npy'
    if not u.exists(): print('FALTA', lid, tag); continue
    clona(u, OUT / f'L{lid}_G.npy'); clona(FIL / f'{tag}_alfa_u16.npy', OUT / f'L{lid}_alfa.npy'); clona(REF / f'L{lid}_mascara.npy', OUT / f'L{lid}_mascara.npy'); nous[lid] = str(u)
meta['font'] = 'estat V97 (r3): base i filtres nous; la resta, V96'; meta['nous'] = {str(k): v for k, v in nous.items()}
(OUT / 'CAPES_V97.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1) + '\n'); print('FET', len(nous), 'capes noves')
