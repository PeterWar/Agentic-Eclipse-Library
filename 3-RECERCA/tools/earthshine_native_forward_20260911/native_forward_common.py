from pathlib import Path
import json,hashlib,numpy as np
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'output/earthshine_native_forward_20260911';SRC=ROOT/'output/earthshine_native_psf_20260911'
CLAIM='CODEX_EARTHSHINE_NATIVE_FORWARD_20260911'
assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']==CLAIM
CX=699.568111973117;CY=699.6475341408573
PLAN=json.loads((OUT/'PLAN.json').read_text())
def save(name,a):(OUT/name).write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
