from pathlib import Path
import json,hashlib,numpy as np
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'output/earthshine_joint_20260911';SRC=ROOT/'output/earthshine_detail_20260911';OPT=ROOT/'output/earthshine_optics_20260911'
CLAIM='CODEX_EARTHSHINE_JOINT_20260911'
assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']==CLAIM
N=1400;CX=699.568111973117;CY=699.6475341408573
def save(name,value):(OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
