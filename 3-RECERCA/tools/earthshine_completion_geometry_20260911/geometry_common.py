from pathlib import Path
import json,hashlib,numpy as np
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent;OUT=ROOT/'output/earthshine_completion_geometry_20260911';SRC=ROOT/'output/earthshine_native_psf_20260911';PREV=ROOT/'output/earthshine_scatter_witness_20260911';CLAIM='CODEX_EARTHSHINE_COMPLETION_GEOMETRY_20260911'
assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']==CLAIM
CX=699.568111973117;CY=699.6475341408573;N=1400;P_WIDE=json.loads((PREV/'B1_physical_mixture.json').read_text())['p']
CAL=json.loads((PREV/'PLAN.json').read_text())['reserved_stems'];TEST=['572A2967','572A2985','572A2997','572A3003'];LONG=['572A2978','572A2980','572A2983']
def save(name,value):(OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
