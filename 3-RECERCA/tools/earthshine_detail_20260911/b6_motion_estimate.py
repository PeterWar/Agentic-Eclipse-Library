"""Document finite-exposure lunar displacement; NOT a measured per-frame PSF.
Solar positions of long Vixen frames were modelled after failed correlation;
therefore this is a nominal motion hypothesis with an explicit uncertainty.
No deconvolution is applied from these estimated trajectories.
"""
from detail_common import *
import sys
sys.path.insert(0,str(ROOT/'research/tools/v45_earthshine_20260910'))
from comu45 import RUNS,COMMON_TO_FINAL,f2,comu
rows=[]
source_frames=json.loads((ROOT/'output/v45_earthshine_20260910/4-rebuts/B1_inputs.json').read_text())['frames'];groups={m['nom']:m['grup'] for m in source_frames}
for tag in ['vixen','sony']:
 ctx=f2.Ctx(comu.Run.obre(str(RUNS[tag])));p=json.loads((RUNS[tag]/'4-rebuts/F1.3_registre.json').read_text())['fotogrames'];fr=[(n,v) for n,v in p.items() if v.get('coronal') and v['exp']>=1];fr.sort(key=lambda nv:nv[1]['t'])
 # Local secants of observed/modelled frame centres, not instantaneous guiding.
 for i,(name,v) in enumerate(fr):
  if i==0 or i==len(fr)-1:continue
  same=[(n,w) for n,w in fr if groups.get(n)==groups.get(name)];j=next(j for j,(n,w) in enumerate(same) if n==name)
  if len(same)<2:continue
  a,b=same[max(j-1,0)][1],same[min(j+1,len(same)-1)][1];dt=b['t']-a['t'];vel=np.array([(b['sol_x']+b['lluna_dx']-a['sol_x']-a['lluna_dx'])/dt,(b['sol_y']+b['lluna_dy']-a['sol_y']-a['lluna_dy'])/dt]);common=np.array([ctx.ca*vel[0]-ctx.sa*vel[1],ctx.sa*vel[0]+ctx.ca*vel[1]])/ctx.k;vv=COMMON_TO_FINAL[:,:2]@common;rows.append(dict(tren=tag,frame=name,exp=v['exp'],nominal_motion_final_xy=(vv*v['exp']).tolist(),length_px=float(np.linalg.norm(vv)*v['exp']),solar_position_origin=v['font'],pointing_group=groups.get(name),limit='secant using same-pointing exposures only, includes modelled solar centres; not independent PSF measurement'))
save('B6_motion_estimate.json',dict(method=__doc__,frames=rows,decision='Do not deconvolve before measuring or bounding intra-exposure tracking/PSF from actual data.'))
print([(r['tren'],r['frame'],round(r['length_px'],3),r['solar_position_origin']) for r in rows if r['exp']>=5],flush=True)
