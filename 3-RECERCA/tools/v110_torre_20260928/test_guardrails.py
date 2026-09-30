"""Adversarial in-memory checks of the exact predicates used by the PSB gate."""
from pathlib import Path
import sys, json, copy
import numpy as np
from psd_tools.constants import Tag
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'3-RECERCA/tools/guardrails_postprocessat'))
from porta_torre_pisa import PSB, record_bytes, same_array, inventory, q_blocs, llegeix_registres, rid, sha
O = ROOT/'4-RESULTATS/v110_torre_20260928'
c = json.loads((O/'CONTRACTE_TORRE.json').read_text())
base = PSB(c['base']['path'])
manual = PSB(c['manual']['path'])
stage = PSB(str(O/'noCEL_stage.psb'))
results = {}
sample=np.array([[0, 1, 32768, 65535]], dtype=np.uint16)
results['uint16_big_endian_values_accepted']=same_array(sample,sample.astype('>u2'))
results['signed_int16_rejected']=not same_array(sample,sample.astype(np.int16))
changed=sample.astype('>u2');changed[0,2]+=1
results['big_endian_one_pixel_change_rejected']=not same_array(sample,changed)
expected = q_blocs(np.load(c['replacement']['41']['path'], mmap_mode='r'))
original = base.channel(41, 0)[0]
results['original_41_rejected'] = not same_array(original, expected)
results['original_41_different_pixels'] = int(np.count_nonzero(original != expected))
del original
results['corrected_41_accepted'] = same_array(stage.channel(41, 0)[0], expected)
del expected
mask, (left, top) = manual.channel(308, -2)
mutated = mask.copy()
y, x = 3300-top, 5300-left
mutated[y, x] += 2
results['single_manual_mask_pixel_rejected'] = not same_array(mask, mutated)
results['mask_mutation'] = dict(x=5300, y=3300, before=int(mask[y,x]), after=int(mutated[y,x]))
del mask, mutated
records = {rid(r): r for r, _ in llegeix_registres(Path(base.path))['recs']}
r = records[239]
altered = copy.deepcopy(r)
altered.tagged_blocks[Tag.CONTENT_GENERATOR_EXTRA_DATA].data[b'brightnessBlacks'].value = 14
results['adjustment_payload_rejected'] = record_bytes(r) != record_bytes(altered)
admin = copy.deepcopy(r)
for ch in admin.channel_info:
    ch.length += 10
for item in admin.tagged_blocks[Tag.METADATA_SETTING].data:
    if item.key == b'cust' and b'layerTime' in item.data:
        item.data[b'layerTime'].value += 10
results['native_admin_changes_accepted'] = record_bytes(r) == record_bytes(admin)
baseids = [l['id'] for l in base.layers]
good = [l['id'] for l in stage.layers]
bad = [9400 if l['id']==400 else 9401 if l['id']==401 else l['id']
       for l in PSB(str(ROOT/'1-PHOTOSHOP/V109.psb')).layers]
results['renumbered_V109_rejected'] = bool(inventory(bad, baseids))
results['innocuous_extra_hidden_layer_rejected'] = bool(inventory(good+[9123], baseids))
assert all(v for k,v in results.items() if k.endswith(('_rejected','_accepted')))
report = dict(status='PASS', scope='actual predicate tests in memory, not full gate runs on mutated PSB files',
              gate_sha256=sha(ROOT/'3-RECERCA/tools/guardrails_postprocessat/porta_torre_pisa.py'), tests=results)
(O/'TESTS_ADVERSARIALS.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
