"""Continue the same joint solver: B2 had not reached a stable objective."""
from common50 import *
from scipy.fft import rfft2,irfft2
import time
z=np.load(OUT/'B2_joint_inputs.npz');D=z['g']-z['background'];B=z['background'];W=z['weight'];M=z['mask'];O=1-M
old=np.load(OUT/'B2_joint_result.npz');L=old['lunar'].copy();S=old['solar'].copy();T=old['transfer'];YL=L.copy();YS=S.copy();t=1.;history=[]
step_s=.45;step_l=.45/sum(float(w.max()) for w in W)
def blur(a):return irfft2(rfft2(a,workers=2)*T,s=(N,N),workers=2)
start=time.time()
for iteration in range(800):
    pred=blur(M*YL+O*YS);res=pred-D;back=blur(W*res)
    Ln=YL-step_l*M*back.sum(axis=0);Sn=np.maximum(YS-step_s*O*back,0)
    tn=(1+np.sqrt(1+4*t*t))/2;YL=Ln+(t-1)/tn*(Ln-L);YS=Sn+(t-1)/tn*(Sn-S);L=Ln;S=Sn;t=tn
    if iteration%100==0 or iteration==799:
        spill=blur(O*S);corrected=D+B-spill
        np.savez_compressed(OUT/f'B3_checkpoint_{iteration:03d}.npz',lunar=L,mean_spill=(W*spill).sum(0)/W.sum(0),mean_corrected=(W*corrected).sum(0)/W.sum(0))
        row=dict(iteration=iteration,objective=float(np.sum(W*res*res)/W.sum()),seconds=time.time()-start);history.append(row);save('B3_convergence.json',dict(method=__doc__,history=history,publication='NONE; source/independence/photographic validation pending'));print('CONTINUE',row,flush=True)
spill=blur(O*S);np.savez_compressed(OUT/'B3_joint_result.npz',lunar=L,solar=S,spill=spill,corrected=D+B-spill,mask=M,transfer=T)
print('CONTINUATION COMPLETE',flush=True)
