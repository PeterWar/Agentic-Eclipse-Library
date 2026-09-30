"""Same eight signed broad injections; refit response and both S8 stages.

Injected source and photograph share the predeclared A4 local derivative.
This is conditional transfer, not independent validation of the derivative.
Every location must remain in the previous 0.90-1.10 band. No new threshold.
"""
from pathlib import Path
import ast,json,numpy as np
from scipy.ndimage import map_coordinates
from scipy.optimize import nnls
R=Path.cwd();O=R/'output/earthshine_spectral_broad_20260914';T=Path(__file__).parent;INJECTION_METHOD=__doc__
# Read only function construction, no old campaign outputs or candidate calls.
tree=ast.parse((T/'a6_separate_limb_operator.py').read_text());body=[]
for node in tree.body:
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='P' for t in node.targets):break
 body.append(node)
exec(compile(ast.Module(body=body,type_ignores=[]),str(T/'a6_separate_limb_operator.py'),'exec'))
N=1400;CX=699.568111973117;CY=699.6475341408573;y,x=np.mgrid[:N,:N];rad=np.hypot(x-CX,y-CY);ang=np.arctan2(y-CY,x-CX)%(2*np.pi)
P=np.load(R/'research/tools/earthshine_v50_temporal_20260912/cau/lun_ch1_roi.npy').astype(float);src=np.load(R/'output/earthshine_v56_three_routes_20260913/arrays/R5_sources.npz')['Gclean'].astype(float);edge=np.load(R/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy');physical=rad<np.interp(ang,np.arange(len(edge))*2*np.pi/len(edge),edge,period=2*np.pi)
rr=np.arange(.5,460.,.5);th=np.arange(1440)*2*np.pi/1440;co=[CY+rr[:,None]*np.sin(th),CX+rr[:,None]*np.cos(th)];freq=np.fft.rfftfreq(1440)[None,:]*1440/(2*np.pi*rr[:,None]);u=(rr[:,None]/460)**2;basis=np.broadcast_to(np.stack([(1-u)**2,2*u*(1-u),u*u],-1),(len(rr),1440,3))
guard=(co[1]>=500)&(co[1]<773)&(co[0]>=852)&(co[0]<1098);fit=(rr[:,None]>60)&(rr[:,None]<410)&((np.arange(1440)[None,:]//120)%2==0)&~guard
def filt(a,lo,hi):
 a0=np.clip((freq-1/(hi*1.25))/(1/hi-1/(hi*1.25)),0,1);b=np.clip((freq-1/lo)/(1/(lo*.8)-1/lo),0,1);h=(.5-.5*np.cos(np.pi*a0))*(.5+.5*np.cos(np.pi*b))
 return np.fft.irfft(np.fft.rfft(a,axis=1)*h,n=1440,axis=1)
def template(p,s):
 ps=map_coordinates(s,co,order=1,mode='nearest');pp=map_coordinates(p,co,order=1,mode='nearest');S=filt(ps,32,64);T=filt(pp,32,64);A=S[...,None]*basis;cf,_=nnls(A[fit],T[fit]);beta=basis@cf;lp=filt(ps,24,256)*beta
 L=map_coordinates(np.c_[lp,lp[:,:1]],[(rad-.5)/.5,ang*1440/(2*np.pi)],order=1,mode='nearest');L[~physical]=0
 return L,cf
L,cf=template(P,src);base,_=evaluate(P,edge,L);a4=np.array(json.loads((O/'A4_protected_source.json').read_text())['coefficients']);assert np.max(abs(cf-a4))<1e-6
u=(rad/460)**2;beta=cf[0]*(1-u)**2+cf[1]*2*u*(1-u)+cf[2]*u*u
protocol=dict(method=INJECTION_METHOD,positions=[[636,975,50],[636,975,90],[1000,680,50],[500,440,50]],amplitudes=[-200,200],required_gain=[.9,1.1],operator='A6, with A4 template response fully refitted for each injected observation',status='FROZEN_BEFORE_INJECTIONS')
(O/'A7_protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
for cx,cy,sig in protocol['positions']:
 e=np.exp(-((x-cx)**2+(y-cy)**2)/(2*sig**2));use=(e>.05)&(rad<435)
 for amp in [-200,200]:
  pp=P+amp*e;ss=src+amp*e/np.maximum(beta,1e-3);ll,cc=template(pp,ss);test,_=evaluate(pp,edge,ll);response=(test-base)/amp;gain=float(np.sum(response[use]*e[use])/np.sum(e[use]**2));row=dict(center=[cx,cy],sigma=sig,amplitude=amp,refit_gain=gain,pass_090_110=bool(.9<=gain<=1.1),coefficients=cc.tolist());rows.append(row);print(row,flush=True)
out=dict(protocol=protocol,injections=rows,status='PASS_CONDITIONAL_ONLY_OTHER_GATES_PENDING' if all(q['pass_090_110'] for q in rows) else 'REJECTED_BROAD_TRANSFER')
(O/'A7_full_refit_injections.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'],flush=True)
