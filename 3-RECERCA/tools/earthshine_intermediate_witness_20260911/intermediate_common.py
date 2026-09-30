from pathlib import Path
import json,hashlib,numpy as np
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent;OUT=ROOT/'output/earthshine_intermediate_witness_20260911';SRC=ROOT/'output/earthshine_native_psf_20260911';PREV=ROOT/'output/earthshine_scatter_witness_20260911';CLAIM='CODEX_EARTHSHINE_INTERMEDIATE_WITNESS_20260911'
assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']==CLAIM
CX=699.568111973117;CY=699.6475341408573;N=1400;P12=json.loads((PREV/'B1_physical_mixture.json').read_text())['p'];ALPHA=14.826313721285086
TRAIN=json.loads((PREV/'PLAN.json').read_text())['training_stems'];RETRO=json.loads((PREV/'PLAN.json').read_text())['reserved_stems'];FRESH=[f'572A{x}' for x in [2960,2962,2964,2966,3012,3016,3020,3024]]
def save(name,value):(OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
