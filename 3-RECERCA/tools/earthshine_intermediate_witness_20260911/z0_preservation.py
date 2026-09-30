"""Verify frozen inputs, RAW identity and original projects before status update."""
from intermediate_common import *
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import ast
prior_path=ROOT/'research/tools/earthshine_completion_geometry_20260911/delivery_manifest.json';prior=json.loads(prior_path.read_text());original=json.loads((ROOT/'research/tools/earthshine_native_psf_20260911/delivery_manifest.json').read_text());known={r['path']:r for r in original['files']+original['inputs']};oldpres=json.loads((SRC/'Z0_preservation.json').read_text());names=TRAIN+RETRO+FRESH;paths=[SRC/f'A0_{kind}_{s}.npz' for kind in ['quincunx','native_samples'] for s in names]
def rec(p):
    p=Path(p)
    with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
    return dict(path=str(p),bytes=p.stat().st_size,sha256=h)
def check(r):
    a=rec(r['path']);assert a['sha256']==r['sha256'],('CHANGED',r['path']);return a
raws={r['stem']:r for r in json.loads((SRC/'A2_all_native.json').read_text())['frames']};raw_expected=[dict(path=raws[s]['raw_path'],sha256=raws[s]['raw_sha256']) for s in names];auxprior=json.loads((ROOT/'research/tools/earthshine_scatter_witness_20260911/delivery_manifest.json').read_text());auxknown={r['path']:r for r in auxprior['files']};auxpaths=[PREV/'PLAN.json',PREV/'B1_physical_mixture.json'];additional=[ROOT/'output/v45_earthshine_20260910/4-rebuts/F2_temporal.json',ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy',ROOT/'output/v45_earthshine_20260910/4-rebuts/B1_inputs.json'];assert len(paths)==56
with ThreadPoolExecutor(max_workers=3) as pool:
    consumed=list(pool.map(check,[known[str(p)] for p in paths]));raw_checked=list(pool.map(check,raw_expected));originals=list(pool.map(check,oldpres['originals']));prefs=list(pool.map(check,oldpres['camera_raw_preferences_exact']));previous_data=list(pool.map(check,[auxknown[str(p)] for p in auxpaths]))
publication=check(prior['publication']);canonical=[check(r) for r in prior['canonical_after']];previous_handoff=check(prior['handoff']);before=HERE/'docs_before';before.mkdir(exist_ok=False)
for i,r in enumerate(canonical):
    p=Path(r['path']);(before/f'{i}_{p.name}').write_bytes(p.read_bytes())
for p in HERE.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
native=json.loads((OUT/'D0_native_fields.json').read_text());assert len(native['frames'])==28 and all(all(r['exact_identity'].values()) for r in native['frames'])
save('Z0_preservation.json',dict(PASS=True,created=datetime.now(timezone.utc).isoformat(),verified_arrays=consumed,verified_RAWs=raw_checked,previous_data=previous_data,additional_inputs=[rec(p) for p in additional],originals=originals,camera_raw_preferences=prefs,publication=publication,canonical_before=canonical,previous_handoff=previous_handoff,prior_manifest=rec(prior_path),claude_status=rec(ROOT/'.coordination/CLAUDE_STATUS.md'),scope='56 frozen arrays and28 RAWs checked against V49 records;28 native fields reproduce all frozen annular samples exactly. Original PSBs,V49 and3XMP unchanged. No Photoshop call or live-document mutation.'))
print('PRESERVATION PASS:56 arrays,28 RAWs,28 exact native fields,original PSBs,V49,XMP,9authorities',flush=True)
