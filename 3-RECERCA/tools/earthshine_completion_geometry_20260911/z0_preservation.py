"""Verify frozen scientific inputs and snapshot live authority before updating it."""
from geometry_common import *
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import ast
prior_path=ROOT/'research/tools/earthshine_scatter_witness_20260911/delivery_manifest.json';prior=json.loads(prior_path.read_text());source_manifest=json.loads((ROOT/'research/tools/earthshine_native_psf_20260911/delivery_manifest.json').read_text());known={r['path']:r for r in source_manifest['files']+source_manifest['inputs']};previous_known={r['path']:r for r in prior['files']};oldpres=json.loads((SRC/'Z0_preservation.json').read_text());frames=json.loads((PREV/'D2_training_sources.json').read_text())['frames'];paths=[SRC/f'A0_quincunx_{r["stem"]}.npz' for r in frames]+[SRC/f'A0_native_samples_{s}.npz' for s in CAL+TEST]
previous_names=['PLAN.json','B1_physical_mixture.json','D2_training_sources.json','D2_training_sources.npz','D2_auxiliary_corona.npz','E1_completion_map_572A2967.npz','E1_completion_map_572A3003.npz']
def rec(p):
    p=Path(p)
    with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
    return dict(path=str(p),bytes=p.stat().st_size,sha256=h)
def check(r):
    actual=rec(r['path']);assert actual['sha256']==r['sha256'],('CHANGED',r['path']);return actual
assert len(set(paths))==83
with ThreadPoolExecutor(max_workers=3) as pool:
    checked_arrays=list(pool.map(check,[known[str(p)] for p in paths]));previous_data=list(pool.map(check,[previous_known[str(PREV/n)] for n in previous_names]));originals=list(pool.map(check,oldpres['originals']));prefs=list(pool.map(check,oldpres['camera_raw_preferences_exact']))
publication=check(prior['publication']);canonical=[check(r) for r in prior['canonical_after']];previous_handoff=check(prior['handoff']);before=HERE/'docs_before';before.mkdir(exist_ok=False)
for i,r in enumerate(canonical):
    p=Path(r['path']);(before/f'{i}_{p.name}').write_bytes(p.read_bytes())
for p in HERE.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
extra=[ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy',ROOT/'output/v45_earthshine_20260910/4-rebuts/B1_inputs.json']
save('Z0_preservation.json',dict(PASS=True,created=datetime.now(timezone.utc).isoformat(),verified_arrays=checked_arrays,previous_data=previous_data,additional_inputs=[rec(p) for p in extra],originals=originals,camera_raw_preferences=prefs,publication=publication,canonical_before=canonical,previous_handoff=previous_handoff,prior_manifest=rec(prior_path),claude_status=rec(ROOT/'.coordination/CLAUDE_STATUS.md'),scope='83 frozen arrays verified conservatively (67 quincunx and16 native).7 prior diagnostic inputs, original PSBs, V49 and3 XMP rehashed. No source image or Photoshop call/alteration this round. Additional inherited contour/metadata hashes recorded; their calibration is shared.'))
print('PRESERVATION PASS:83 arrays,7 prior inputs,original PSBs,V49,XMP,9authority files',flush=True)
