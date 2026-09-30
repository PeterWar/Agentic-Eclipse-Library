from pathlib import Path
import numpy as np,json
from scipy.ndimage import map_coordinates
from scipy.optimize import nnls
from PIL import Image,ImageDraw
R=Path.cwd();O=R/'output/v68_artefactes_20260914';A=O/'arrays';N=1400;CX=699.568111973117;CY=699.6475341408573;nt=2880;rr=np.arange(.5,458,.5);th=np.arange(nt)*2*np.pi/nt;co=[CY+rr[:,None]*np.sin(th),CX+rr[:,None]*np.cos(th)];f=np.fft.rfftfreq(nt)[None,:]*nt/(2*np.pi*rr[:,None]);u=np.clip((f-1/16)/(1/12-1/16),0,1);v=np.clip((f-1/4)/(1/3-1/4),0,1);H=(.5-.5*np.cos(np.pi*u))*(.5+.5*np.cos(np.pi*v))
def pol(a):return map_coordinates(a,co,order=1,mode='nearest')
def band(a):return np.fft.irfft(np.fft.rfft(a,axis=1)*H,n=nt,axis=1)
z=np.load(A/'B9_fine_detector.npz');P=np.stack([np.load(A/f'L30_C{c}.npy')[300:1700,301:1701] for c in range(3)],-1).astype('int32');Q=band(pol(P.mean(-1)));S=band(pol(z['source']));D=band(pol(z['correction']));domain=458.;u=(rr[:,None]/domain)**2;basis=np.broadcast_to(np.stack([(1-u)**2,2*u*(1-u),u*u],-1),(*Q.shape,3));train=np.broadcast_to((rr[:,None]>=60)&(rr[:,None]<420),Q.shape)&((np.arange(nt)[None,:]//240)%2==0);hold=np.broadcast_to((rr[:,None]>=60)&(rr[:,None]<420),Q.shape)&~train;X=np.concatenate([S[...,None]*basis,D[...,None]*basis],-1);cf,_=nnls(X[train],Q[train]);pred=X@cf
Y,Xx=np.mgrid[:N,:N];r=np.hypot(Xx-CX,Y-CY);u=(r/domain)**2;bg=np.stack([(1-u)**2,2*u*(1-u),u*u],-1);gamma=bg@cf[3:];mask=np.load(A/'L30_C-2.npy')[300:1700,301:1701];alpha=np.load(A/'L30_C-1.npy')[300:1700,301:1701];visible=(mask>0)&(alpha>0);delta=-np.rint(gamma*z['correction']).astype('int32');delta[~visible]=0;new=P+delta[...,None];np.savez_compressed(A/'B10_photo_pilot.npz',candidate=new,delta=delta,gamma=gamma,old=P);good=visible&(r<420)
rep=dict(coefficients=cf.tolist(),heldout_correlation=float(np.corrcoef(pred[hold],Q[hold])[0,1]),predictor_D_photo_corr=float(np.corrcoef(D[hold],Q[hold])[0,1]),changed=int((delta!=0).sum()),delta_percentiles=np.percentile(delta[visible],[0,1,50,99,100]).tolist(),clipped=int(((new.min(-1)<0)|(new.max(-1)>65535)).sum()),rms_before=float(np.std(Q[hold])),rms_after=float(np.std(band(pol(new.mean(-1)))[hold])))
(O/'B10_photo_pilot.json').write_text(json.dumps(rep,indent=2)+'\n');print(rep)
s=np.s_[3910-3077:4170-3077,5170-4678:5470-4678];pan=Image.new('RGB',(1800,820),'#151515');dr=ImageDraw.Draw(pan)
for j,q in enumerate([P,new]):
 a=q[s].astype(float)*4/65535;im=Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5));pan.paste(im.resize((900,780),Image.Resampling.NEAREST),(j*900,40));dr.text((j*900+10,12),['V67 x4','Fine detector pilot x4'][j],fill='white')
pan.save(O/'vistes/B10_fine_photo.png')
