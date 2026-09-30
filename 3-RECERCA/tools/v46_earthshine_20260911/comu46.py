"""V46 explicitly requested photographic edge grading; unchanged source grid."""
import sys
from pathlib import Path
HERE46=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE46.parent/'v45_earthshine_20260910'))
from comu45 import *
CAU46=HERE46/'cau';OUT46=ROOT/'output/v46_earthshine_20260911'
REB46=OUT46/'4-rebuts';VIS46=OUT46/'lliurables/vistes'
CLAIM46='CODEX_EARTHSHINE_V46_20260911'

def claim46():
    a=json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())
    assert a['claim_id']==CLAIM46 and a['owner']=='Codex /root'

def png46(name,a):
    from PIL import Image
    icc=CAU46/'source_icc.bin'
    kw={'icc_profile':icc.read_bytes()} if icc.exists() else {}
    Image.fromarray(np.rint(np.clip(a,0,1)*255).astype(np.uint8)).save(VIS46/name,**kw)
