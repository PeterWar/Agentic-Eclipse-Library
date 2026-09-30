from pathlib import Path
import json,hashlib,numpy as np
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'output/earthshine_detail_20260911'
PREV=ROOT/'output/earthshine_validation_20260911'
CAU45=ROOT/'research/tools/v45_earthshine_20260910/cau'
assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_EARTHSHINE_DETAIL_20260911'
CX=699.568111973117;CY=699.6475341408573;N=1400
def save(name,obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
