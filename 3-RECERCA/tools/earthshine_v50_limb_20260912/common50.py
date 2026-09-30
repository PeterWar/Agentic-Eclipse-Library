from pathlib import Path
import json,hashlib,numpy as np
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
OUT=ROOT/'output/earthshine_v50_limb_20260912';CLAIM='CODEX_EARTHSHINE_V50_LIMB_20260912'
assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']==CLAIM
N=1400;CX=699.568111973117;CY=699.6475341408573;X0=4677;Y0=3077
NATIVE=ROOT/'output/earthshine_intermediate_witness_20260911'
V49=ROOT/'output/earthshine_v49_pere_reveal_20260912'
SIGMA=np.array([2.,4.,8.,16.,32.]);STEP=5;NC=N//STEP
def save(name,v):(OUT/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
