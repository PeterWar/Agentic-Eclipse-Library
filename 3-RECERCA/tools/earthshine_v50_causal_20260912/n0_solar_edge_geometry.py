"""Measure apparent edges of the four recovered solar rasters against F4.
This measures photographed response, not the intrinsic lunar radius. Frozen
perles shift reproduces the current Earthshine09 source; no image edits.
"""
from common50 import *
from scipy.ndimage import map_coordinates,gaussian_filter1d
edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy');th=np.arange(1440)*2*np.pi/1440;rr=np.arange(440,473,.25);yy=CY+np.sin(th[:,None])*rr;xx=CX+np.cos(th[:,None])*rr;D=np.stack([np.ones_like(th),np.cos(th),np.sin(th)],-1);rows=[]
for key in ['12','11','10','09','current']:
 z=np.load(OUT/'L0_09_RGB16.npy') if key=='current' else np.load(OUT/f'L4_original_{key}.npz')['rgb']
 if key=='12':z=np.roll(z,-3,axis=1)
 for c in [0,1,2]:
  p=map_coordinates(z[...,c].astype(float),[yy,xx],order=1);p=gaussian_filter1d(p,2,axis=0,mode='wrap');g=gaussian_filter1d(p,3,order=1,axis=1);ids=np.argmax(g,axis=1);ed=rr[ids];amp=g[np.arange(len(th)),ids];valid=(ids>0)&(ids<len(rr)-1)&(amp>100)
  for it in range(4):
   fit=np.linalg.lstsq(D[valid],(ed-edge)[valid],rcond=None)[0];res=ed-edge-D@fit;valid&=abs(res)<max(1.,3*np.std(res[valid]))
  rows.append(dict(layer=key,channel=c,valid_fraction=float(valid.mean()),difference_to_F4_R_dx_dy=fit.tolist(),residual_rms=float(np.std(res[valid])),radius_percentiles=np.percentile(ed[valid],[5,50,95]).tolist()))
save('N0_solar_edge_geometry.json',dict(method=__doc__,rows=rows));print(json.dumps(rows,indent=2),flush=True)
