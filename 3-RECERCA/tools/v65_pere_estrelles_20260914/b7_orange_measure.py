from pathlib import Path
import numpy as np,json
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';A=O/'arrays';P=R/'output/v61_interiors_limbe_20260913/arrays';bb=[5260,3300,5300,3338];sl=np.s_[bb[1]-2777:bb[3]-2777,bb[0]-4377:bb[2]-4377]
for id in [76,96]:
 rgb=np.stack([np.load(A/f'L{id}_C{c}.npy')[sl] for c in range(3)],-1)/65535;print('current',id)
 for x,y in [(5278,3308),(5280,3318),(5282,3328),(5282,3332),(5295,3318),(5263,3318)]:
  v=rgb[y-bb[1],x-bb[0]];print((x,y),v,v/(v[1]+1e-8))
for j in [1,2]:
 rgb=np.stack([np.load(P/f'V57_L{j:02d}_C{c}.npy')[sl] for c in range(3)],-1)/65535;print('original',12-j)
 for x,y in [(5278,3308),(5280,3318),(5282,3328),(5282,3332),(5295,3318),(5263,3318)]:
  v=rgb[y-bb[1],x-bb[0]];print((x,y),v,v/(v[1]+1e-8))
