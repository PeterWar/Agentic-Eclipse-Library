"""Verify originals and exact consumed inputs; snapshot authority before updating."""
from diffraction_common import *
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import ast
prior_path=ROOT/'research/tools/earthshine_intermediate_witness_20260911/delivery_manifest.json';prior=json.loads(prior_path.read_text());old=json.loads((NATIVE/'Z0_preservation.json').read_text());known={r['path']:r for r in prior['files']+prior['verified_arrays']+prior['additional_inputs']}
def rec(path):
    path=Path(path)
    with path.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
    return dict(path=str(path),bytes=path.stat().st_size,sha256=h)
def check(r):
    out=rec(r['path']);assert out['sha256']==r['sha256'],('CHANGED',r['path']);return out
names=[r['stem'] for r in json.loads((OUT/'A2_stack_plan.json').read_text())['frames']]
inputs=[NATIVE/f'D0_native_field_{s}.npz' for s in names]+[SRC/f'A0_native_samples_{s}.npz' for s in names]+[NATIVE/'D0_native_fields.json',NATIVE/'D1_inputs.json',NATIVE/'E0_physical_cascade.json',ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy']
with ThreadPoolExecutor(max_workers=3) as pool:
    consumed=list(pool.map(check,[known[str(p)] for p in inputs]));originals=list(pool.map(check,old['originals']));prefs=list(pool.map(check,old['camera_raw_preferences']));raws=list(pool.map(check,old['verified_RAWs']))
plan=json.loads((OUT/'PLAN.json').read_text());scale=check(dict(path=plan['plate_scale_receipt'],sha256=plan['plate_scale_sha256']));publication=check(prior['publication']);canonical=[check(r) for r in prior['canonical_after']];handoff=check(prior['handoff']);before=HERE/'docs_before';before.mkdir(exist_ok=False)
for i,r in enumerate(canonical):(before/f'{i}_{Path(r["path"]).name}').write_bytes(Path(r['path']).read_bytes())
for p in HERE.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
save('Z0_preservation.json',dict(PASS=True,created=datetime.now(timezone.utc).isoformat(),verified_inputs=consumed,verified_RAWs=raws,originals=originals,camera_raw_preferences=prefs,publication=publication,canonical_before=canonical,previous_handoff=handoff,prior_manifest=rec(prior_path),scale_receipt=scale,claude_status=rec(ROOT/'.coordination/CLAUDE_STATUS.md'),scope='Read-only raw/cache analysis; original PSBs/V49/three XMP verified unchanged; no Photoshop call, no live document operation; authority snapshot before update'))
print('PRESERVATION PASS',len(consumed),'inputs',len(raws),'RAWs, originals/V49/XMP, 9 authorities',flush=True)
