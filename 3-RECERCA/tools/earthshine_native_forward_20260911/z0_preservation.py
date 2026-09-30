"""Verify consumed frozen inputs and preserve current authority before a handoff."""
from native_forward_common import *
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import ast
HERE=Path(__file__).resolve().parent
oldmanifest=ROOT/'research/tools/earthshine_native_psf_20260911/delivery_manifest.json';old=json.loads(oldmanifest.read_text());pres=json.loads((SRC/'Z0_preservation.json').read_text());known={r['path']:r for r in old['files']+old['inputs']}
native_stems=set(json.loads((OUT/'PLAN.json').read_text())['train_stems']+json.loads((OUT/'PLAN.json').read_text())['reserved_stems']+['572A2968','572A2969','572A2970'])
texture_stems=json.loads((OUT/'D0_texture_plan.json').read_text())['vixen_stems']
paths=[SRC/f'A0_native_samples_{s}.npz' for s in sorted(native_stems)]+[SRC/f'A0_quincunx_{s}.npz' for s in texture_stems]+[ROOT/'output/earthshine_detail_20260911/native'/f'sony_{s}.npz' for s in ['DSC06987','DSC06984','DSC06985']]
def rec(p):
    p=Path(p)
    with p.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
    return dict(path=str(p),bytes=p.stat().st_size,sha256=sha)
def check(r):
    actual=rec(r['path']);assert actual['sha256']==r['sha256'],('INPUT_CHANGED',r['path']);return actual
for p in paths:assert str(p) in known,('NO_FROZEN_HASH',p)
with ThreadPoolExecutor(max_workers=3) as pool:consumed=list(pool.map(check,[known[str(p)] for p in paths]));originals=list(pool.map(check,pres['originals']));prefs=list(pool.map(check,pres['camera_raw_preferences_exact']))
publication=check(old['publication']);canonical=[check(r) for r in old['canonical_after']];previous_handoff=check(old['handoff'])
before=HERE/'docs_before';before.mkdir(exist_ok=False)
for i,r in enumerate(canonical):
    p=Path(r['path']);(before/f'{i}_{p.name}').write_bytes(p.read_bytes())
for p in HERE.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
save('Z0_preservation.json',dict(PASS=True,created=datetime.now(timezone.utc).isoformat(),consumed_inputs=consumed,originals=originals,camera_raw_preferences=prefs,publication=publication,canonical_before=canonical,previous_handoff=previous_handoff,prior_manifest=rec(oldmanifest),claude_status=rec(ROOT/'.coordination/CLAUDE_STATUS.md'),scope='34 consumed native/sample files and original products rehashed against frozen earlier receipts. No RAW re-stack or Photoshop interaction in this round. Live document state not queried or altered by this round.'))
print('PRESERVATION PASS',len(consumed),'inputs;',len(originals),'originals;',len(prefs),'XMP; V49 exact',flush=True)
