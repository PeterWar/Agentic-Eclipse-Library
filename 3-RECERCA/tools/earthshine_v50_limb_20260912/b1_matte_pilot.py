"""Two epoch solar-spill pilots; same saved appearance, no published version."""
from common50 import *
from optical_matte import estimate,coordinates
from scipy.ndimage import map_coordinates
from PIL import Image
import time
p=np.array(json.loads((OUT/'A1_fit.json').read_text())['p'])
core=json.loads((OUT/'B0_native_star_psf.json').read_text())['core_sigma_native_percentiles'][1]
yy,xx=np.mgrid[:N,:N];world=np.stack([xx,yy],-1)
rows=[]
for stem in ['572A2974','572A2992']:
    start=time.time();z=dict(np.load(NATIVE/f'D0_native_field_{stem}.npz'));assert np.all(z['valid'])
    spill,receipt=estimate(z['g'],z,p,core)
    native=(world-z['world_origin'])@np.linalg.inv(z['native_to_world']).T
    u=(native[...,0]+native[...,1]-1)/2-int(z['u0']);v=(native[...,0]-native[...,1]-1)/2-int(z['v0'])
    sampled=map_coordinates(spill,[v,u],order=1,mode='nearest',prefilter=False)
    observed=map_coordinates(z['g'],[v,u],order=1,mode='nearest',prefilter=False)
    np.savez_compressed(OUT/f'B1_matte_{stem}.npz',spill=sampled,observed=observed,corrected=observed-sampled,native_spill=spill)
    rr=np.hypot(xx-CX,yy-CY);report=[]
    angle=np.arctan2(yy-CY,xx-CX)%(2*np.pi);edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy');d=rr-np.interp(angle,np.arange(len(edge))*2*np.pi/len(edge),edge,period=2*np.pi)
    for lo,hi in [(-100,-40),(-40,-6),(-6,-.5),(-.5,3)]:
        use=(d>=lo)&(d<hi);report.append(dict(distance=[lo,hi],old=np.percentile(observed[use],[5,50,95]).tolist(),new=np.percentile((observed-sampled)[use],[5,50,95]).tolist()))
    rows.append(dict(stem=stem,parameters=receipt,regions=report,seconds=time.time()-start));save('B1_matte_pilot.json',dict(method=__doc__,p=p.tolist(),core=core,frames=rows,scope='Solar component separation pilot using observed Vixen boundary. Support and core uncertainty, injection and independent-telescope checks are not yet passed. No new photographic image.'))
    print(stem,report,'seconds',round(time.time()-start,1),flush=True)
