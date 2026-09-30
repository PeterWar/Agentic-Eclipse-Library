"""Promoció no-clobber de CapesTotalsV3c: (1) directori net de màscares (4,5,7,8); (2) build amb build_capes_totals_v3c;
(3) verificació reoberta; (4) carpeta QA, manifest propi i LLEGEIX-ME a la documentació de V3c. No toca cap fitxer existent."""
import shutil, subprocess, hashlib
from pathlib import Path
from v3c_lib import *
P = '/Users/USUARI/.venvs/eines-ia-py312/bin/python'
DEST = Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals')
DOC = DEST / 'Documentacio i QA/V3c'
V3B_PSB = DEST / 'CapesTotalsV3b.psb'
cand = DEST / 'CapesTotalsV3c.psb'; man_b = DOC / 'CapesTotalsV3c.manifest.json'; readme = DOC / 'LLEGEIX-ME_CapesTotalsV3c.md'; qa_dir = DOC / 'CapesTotalsV3c_QA'
DOC.mkdir(parents=True, exist_ok=True)
ONLY_VERIFY = os.environ.get('ONLY_VERIFY') == '1'   # el PSB ja és construït: només verificar i copiar la QA
for p in ((readme, qa_dir) if ONLY_VERIFY else (cand, man_b, readme, qa_dir)):
    if p.exists(): raise SystemExit(f'ja existeix, no es toca: {p}')
mask_build = Path(SCR) / 'masks_build'; mask_build.mkdir(exist_ok=True)
for f in mask_build.glob('*'): f.unlink()
for i in (4, 5, 7, 8): shutil.copy(Path(SCR) / 'masks' / f'mask_{i}.npy', mask_build / f'mask_{i}.npy')
work = Path(SCR) / 'work' / 'build'; work.mkdir(exist_ok=True)
cmd = [P, f'{HERE}/build_capes_totals_v3c.py', '--final-config', f'{HERE}/final_config_v3c.json', '--mask-dir', str(mask_build), '--offsets', f'{HERE}/offsets_v3c.json',
       '--work-dir', str(work), '--candidate', str(cand), '--manifest', str(man_b)]
if not ONLY_VERIFY:
    print(' '.join(cmd), flush=True); subprocess.run(cmd, check=True)
# verificació
ver = Path(SCR) / 'QA' / 'verify_v3c.json'
subprocess.run([P, f'{HERE}/verify_capes_totals_v3c.py', str(cand), str(V3B_PSB), str(DEST / 'CapesTotalsV2b.psb'), str(mask_build), '3,4,5,7,8', f'{SCR}/states/S8.npy', str(ver)], check=True)
rep = json.load(open(ver))
if not rep['ok']: raise SystemExit('VERIFICACIÓ KO: no es promou res més')
# QA
qa_dir.mkdir()
for sub in ('', 'fonament', 'cadena', 'final', 'cerca'):
    src = Path(SCR) / 'QA' / sub
    for f in sorted(src.glob('*')):
        if f.is_file() and (f.suffix in ('.png', '.json', '.md')):
            shutil.copy(f, qa_dir / (f'{sub}_{f.name}' if sub else f.name))
shutil.copy(ver, qa_dir / 'verify_v3c.json')
for i in (4, 5, 7, 8): shutil.copy(mask_build / f'mask_{i}.npy', qa_dir / f'mask_{i}.npy')
for n in ('P3.npy', 'P4.npy'): shutil.copy(Path(SCR) / 'masks' / n, qa_dir / n)
shutil.copy(Path(SCR) / 'lluna_ellipse_llenc.json', qa_dir / 'lluna_ellipse_llenc.json'); shutil.copy(Path(SCR) / 'rang.json', qa_dir / 'rang_3_4_5_7.json')
print('QA copiada a', qa_dir, 'SHA candidat', rep['sha256_v3c'], rep['size_v3c'])
