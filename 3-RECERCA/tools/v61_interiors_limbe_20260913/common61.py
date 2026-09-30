from pathlib import Path
import sys,json,hashlib
import numpy as np
R=Path('/Users/USUARI/Downloads/Eclipse 2026');O=R/'output/v61_interiors_limbe_20260913';T=R/'research/tools/v61_interiors_limbe_20260913'
sys.path.insert(0,str(R/'research/tools/v60_marques_v59_20260913'))
from common60 import chan,box,sha,ROI,CX,CY,RS
SRC=Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V60.psb')
REF=Path('/Users/USUARI/Downloads/Vista_V57_correcte.psb')
V57=R/'output/v58_correccions_20260913/V57_Pere_input.psb'
def claim():assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_V61_V60_INNER_LIMB_20260913'
def save(n,d):
 p=O/n;assert not p.exists(),p;p.write_text(json.dumps(d,indent=2,ensure_ascii=False,default=lambda v:v.item() if isinstance(v,np.generic) else v.tolist())+'\n')
