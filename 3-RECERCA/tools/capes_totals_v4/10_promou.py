"""10 — Promoció no-clobber de CapesTotalsV4: (1) directori net de màscares; (2) build amb
build_capes_totals_v4 (ràsters nous + offsets + màscares); (3) verificació reoberta;
(4) carpeta QA, manifests i LLEGEIX-ME a la documentació de la variant. No toca cap fitxer existent."""
import shutil, subprocess, os, sys, json
from pathlib import Path
from v4_lib import V4W, ORDER
from g5_11_gate import (CHAIN_IDS, FOUNDATION_LAYER_IDS, FOUNDATION_STATES,
                        artifact_record_matches, promotion_gate)

P = sys.executable
HERE = Path(__file__).resolve().parent
DEST = Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals')
TAG = os.environ.get('V4TAG', 'V4b')   # V4b: autoritat del clip de la 1/500 corregida a la 1/3200
DOC = DEST / 'Documentacio i QA' / TAG
cand = DEST / f'CapesTotals{TAG}.psb'
man_b = DOC / f'CapesTotals{TAG}.manifest.json'
qa_dir = DOC / f'CapesTotals{TAG}_QA'
V2B_PSB = DEST / 'CapesTotalsV2b.psb'
ONLY_VERIFY = os.environ.get('ONLY_VERIFY') == '1'
def _occupied(path):
    return path.exists() or path.is_symlink()

cfg = json.load(open(HERE / 'final_config_v4.json'))
visible = [int(k) for k, v in cfg['visibility'].items() if v]
mask_ids = sorted(int(k) for k in cfg['masks'])
if tuple(visible) != ORDER:
    raise SystemExit(f'PROMOCIÓ BLOQUEJADA: visibilitat no canònica {visible}; cal {list(ORDER)}')
if tuple(mask_ids) != tuple(layer_id for layer_id in ORDER if layer_id != 3):
    raise SystemExit(f'PROMOCIÓ BLOQUEJADA: conjunt de màscares no canònic {mask_ids}')
foundation_path = V4W / 'QA/fonament/resum.json'
chain_path = V4W / 'QA/cadena/cadena.json'
with open(foundation_path) as fh:
    foundation_receipt = json.load(fh)
with open(chain_path) as fh:
    chain_receipt = json.load(fh)
promotion_receipt = promotion_gate(foundation_receipt, chain_receipt, ORDER)
if not promotion_receipt['ok']:
    raise SystemExit(f'PROMOCIÓ BLOQUEJADA: {promotion_receipt["failures"]}')

artifact_failures = []
foundation_artifacts = foundation_receipt['artifacts']
for state in FOUNDATION_STATES:
    path = V4W / f'states/{state}.npy'
    if not artifact_record_matches(foundation_artifacts['states'][state], path):
        artifact_failures.append(str(path))
for layer_id in FOUNDATION_LAYER_IDS:
    path = V4W / f'masks/mask_{layer_id}.npy'
    if not artifact_record_matches(foundation_artifacts['masks'][str(layer_id)], path):
        artifact_failures.append(str(path))
for layer_id in CHAIN_IDS:
    entry = chain_receipt[str(layer_id)]
    for record_name, path in (
        ('mask_artifact', V4W / f'masks/mask_{layer_id}.npy'),
        ('state_artifact', V4W / f'states/S{layer_id}.npy'),
    ):
        if not artifact_record_matches(entry[record_name], path):
            artifact_failures.append(str(path))
if artifact_failures:
    raise SystemExit(f'PROMOCIÓ BLOQUEJADA: artefactes stale, substituïts o absents: {artifact_failures}')

ver = V4W / f'QA/verify_v4_{TAG}.json'
verify_work = ver.parent / f'verify_work_{ver.stem}'
if DOC.is_symlink() or (V4W / 'QA').is_symlink() or (V4W / 'work').is_symlink():
    raise SystemExit('PROMOCIÓ BLOQUEJADA: directori pare simbòlic no autoritzat')
for p in ((qa_dir,) if ONLY_VERIFY else (cand, man_b, qa_dir)):
    if _occupied(p):
        raise SystemExit(f'ja existeix, no es toca: {p}')
mask_build = V4W / f'masks_build_{TAG}'
if _occupied(mask_build):
    raise SystemExit(f'ja existeix, no es toca: {mask_build}')
if _occupied(ver):
    raise SystemExit(f'ja existeix, no es toca: {ver}')
if _occupied(verify_work):
    raise SystemExit(f'ja existeix, no es toca: {verify_work}')
work = V4W / f'work/build_{TAG}'
if not ONLY_VERIFY and _occupied(work):
    raise SystemExit(f'ja existeix, no es toca: {work}')
DOC.mkdir(parents=True, exist_ok=True)
mask_build.mkdir(parents=True)
for i in mask_ids:
    shutil.copy(V4W / 'masks' / f'mask_{i}.npy', mask_build / f'mask_{i}.npy')
top = max(visible)
if not ONLY_VERIFY:
    work.mkdir(parents=True)
    cmd = [P, str(HERE / 'build_capes_totals_v4.py'), '--final-config', str(HERE / 'final_config_v4.json'),
           '--mask-dir', str(mask_build), '--offsets', str(HERE / 'offsets_v4.json'),
           '--work-dir', str(work), '--candidate', str(cand), '--manifest', str(man_b)]
    print(' '.join(cmd), flush=True)
    subprocess.run(cmd, check=True)
subprocess.run([P, str(HERE / 'verify_capes_totals_v4.py'), str(cand), str(V2B_PSB), str(mask_build),
                ','.join(map(str, visible)), str(V4W / f'states/S{top}.npy'), str(ver)], check=True)
rep = json.load(open(ver))
if not rep['ok']:
    raise SystemExit('VERIFICACIÓ KO: no es promou res més')
qa_dir.mkdir()
with open(qa_dir / 'G5_10_G5_11_PROMOTION_GATE.json', 'x') as fh:
    json.dump(promotion_receipt, fh, indent=1, ensure_ascii=False)
for sub in ('', 'fonament', 'cadena', 'final', 'cerca'):
    src = V4W / 'QA' / sub
    if not src.is_dir():
        continue
    for f in sorted(src.glob('*')):
        if f.is_file() and f.suffix in ('.png', '.json', '.md'):
            shutil.copy(f, qa_dir / (f'{sub}_{f.name}' if sub else f.name))
shutil.copy(ver, qa_dir / 'verify_v4.json')
for i in mask_ids:
    shutil.copy(mask_build / f'mask_{i}.npy', qa_dir / f'mask_{i}.npy')
for n in ('P3.npy', 'P4.npy'):
    shutil.copy(V4W / 'masks' / n, qa_dir / n)
shutil.copy(V4W / 'lluna_ellipse_v4.json', qa_dir / 'lluna_ellipse_v4.json')
shutil.copy(V4W / 'rang.json', qa_dir / 'rang_v4.json')
print('QA copiada a', qa_dir, '| SHA candidat', rep['sha256_v4'], rep['size_v4'])
