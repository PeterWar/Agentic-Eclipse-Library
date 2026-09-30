"""Verify immutable inputs and snapshot authority before recording progress."""
from scatter_common import *
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import ast
prior_path=ROOT/'research/tools/earthshine_native_forward_20260911/delivery_manifest.json';prior=json.loads(prior_path.read_text());source_manifest=json.loads((ROOT/'research/tools/earthshine_native_psf_20260911/delivery_manifest.json').read_text());known={r['path']:r for r in source_manifest['files']+source_manifest['inputs']};oldpres=json.loads((SRC/'Z0_preservation.json').read_text());frames=json.loads((OUT/'D0_completion_sources.json').read_text())['frames'];native=json.loads((OUT/'PLAN.json').read_text());paths=[SRC/f'A0_quincunx_{r["stem"]}.npz' for r in frames]+[SRC/f'A0_native_samples_{s}.npz' for s in native['training_stems']+native['reserved_stems']]
def rec(p):
    p=Path(p)
    with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
    return dict(path=str(p),bytes=p.stat().st_size,sha256=h)
def check(r):
    actual=rec(r['path']);assert actual['sha256']==r['sha256'],('CHANGED',r['path']);return actual
assert len(set(paths))==87
with ThreadPoolExecutor(max_workers=3) as pool:consumed=list(pool.map(check,[known[str(p)] for p in paths]));originals=list(pool.map(check,oldpres['originals']));prefs=list(pool.map(check,oldpres['camera_raw_preferences_exact']))
publication=check(prior['publication']);canonical=[check(r) for r in prior['canonical_after']];previous_handoff=check(prior['handoff']);before=HERE/'docs_before';before.mkdir(exist_ok=False)
for i,r in enumerate(canonical):
    p=Path(r['path']);(before/f'{i}_{p.name}').write_bytes(p.read_bytes())
for p in HERE.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
save('Z0_preservation.json',dict(PASS=True,created=datetime.now(timezone.utc).isoformat(),consumed_inputs=consumed,originals=originals,camera_raw_preferences=prefs,publication=publication,canonical_before=canonical,previous_handoff=previous_handoff,prior_manifest=rec(prior_path),claude_status=rec(ROOT/'.coordination/CLAUDE_STATUS.md'),scope='87 frozen input arrays and original V46/V47/V48/V49 and XMP rehashed. No RAW stack or Photoshop operation this round; no live document query or alteration.'))
print('PRESERVATION PASS 87 inputs; originals3 and V49; XMP3; authority9',flush=True)
