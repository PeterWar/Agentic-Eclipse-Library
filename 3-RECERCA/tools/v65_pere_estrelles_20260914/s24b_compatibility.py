from pathlib import Path
import sys,numpy as np
from psd_tools import PSDImage
from psd_tools.constants import Compression
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';sys.path.insert(0,str(R/'research/tools/encaix_sony'));from psb_utils import set_merged
p=PSDImage.open(O/'S24_estrelles_capes.psb');set_merged(p,np.load(O/'arrays/S24_stars_RGB16.npy'),Compression.RAW);q=O/'S24b_estrelles_capes.psb';assert not q.exists();p.save(q);print(q.stat().st_size)
