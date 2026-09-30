from pathlib import Path
import json
from psb_munta import ROOT,sha,assemble
O=ROOT/'4-RESULTATS/v112_20260928';old=O/'sensor_mass_raw';S=O/'sensor_mass301';S.mkdir(exist_ok=False)
r=json.loads((old/'TARGETS.json').read_text());c=json.loads((old/'CONFIG.json').read_text());corner=old/'corner301'
c['destination']=str(S/'V112_mass301_stage.psb');c['corner_receipt']=str(corner/'RECEIPT.json');c['replace']['301']={str(cid):str(corner/f'L301_c{cid}.npy') for cid in (0,1,2)}
r['replacement']['301']=dict(channels={str(cid):dict(path=str(corner/f'L301_c{cid}.npy'),sha256=sha(corner/f'L301_c{cid}.npy')) for cid in (0,1,2)},receipt=str(corner/'RECEIPT.json'),receipt_sha256=sha(corner/'RECEIPT.json'))
r['method']+=' Existing301 RGB regenerated with original presentation-only recipe from native corrected stack below; same alpha exact and no metadata change.'
(S/'TARGETS.json').write_text(json.dumps(r,indent=2)+'\n');(S/'CONFIG.json').write_text(json.dumps(c,indent=2)+'\n');assemble(c)
