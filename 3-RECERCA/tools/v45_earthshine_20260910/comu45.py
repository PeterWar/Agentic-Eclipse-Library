"""V45: recover measured limb texture across time; never overwrite V44."""
import sys
from pathlib import Path
HERE45=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE45.parent/'v44_earthshine_20260910'))
from comu44 import *
CAU45=HERE45/'cau'
OUT45=ROOT/'output/v45_earthshine_20260910'
REB45=OUT45/'4-rebuts'
VIS45=OUT45/'lliurables/vistes'
CLAIM45='CODEX_EARTHSHINE_V45_20260910'

def claim45():
    d=json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())
    assert d['claim_id']==CLAIM45 and d['owner']=='Codex /root'

def png45(name,a):
    from PIL import Image
    Image.fromarray(np.round(np.clip(a,0,1)*255).astype(np.uint8)).save(VIS45/name)
