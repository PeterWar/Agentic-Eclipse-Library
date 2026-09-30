from pathlib import Path
import sys,json,gc,hashlib
import numpy as np
from psd_tools import PSDImage
from psd_tools.constants import Tag
R=Path.cwd();O=R/'output/v68_artefactes_20260914';sys.path.insert(0,str(R/'research/tools/v60_marques_v59_20260913'));from common60 import chan,box
p=PSDImage.open(O/'V67_Pere_input.psb');rows=[]
for l in p:
 lid=int(l._record.tagged_blocks.get_data(Tag.LAYER_ID))
 if lid not in [3,30,41,42,43,44,45,46,47,49,51,52,53,56,76,96,204,206,211]:continue
 for c in l._record.channel_info:
  cc=int(c.id);np.save(O/'arrays'/f'L{lid}_C{cc}.npy',box(l,cc))
 print(lid,l.name,flush=True);gc.collect()
