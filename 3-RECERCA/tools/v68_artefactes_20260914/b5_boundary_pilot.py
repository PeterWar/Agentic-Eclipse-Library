from pathlib import Path
import numpy as np,json,cv2,ast
from scipy.ndimage import map_coordinates,gaussian_filter1d
R=Path.cwd();O=R/'output/v68_artefactes_20260914';A=O/'arrays';F=R/'output/v58_correccions_20260913/filters';S=R/'output/v58_correccions_20260913/sources';CAUF=R/'research/tools/v29/cau_final';sl=np.s_[2777:4777,4377:6377];CX=5361.768111973117;CY=3775.747534140857;RS=440.60304883027544;N=2000;cv2.setNumThreads(2)
y,x=np.mgrid[2777:4777,4377:6377];r=np.hypot(y-CY,x-CX).astype('float32');t=np.arctan2(y-CY,x-CX)%(2*np.pi);total=np.array(np.load(S/'fusion_starless.npy',mmap_mode='r')[sl]);m=np.array(np.load(S/'support.npy',mmap_mode='r')[sl]);mfull=np.load(S/'support.npy',mmap_mode='r');totalfull=np.load(S/'fusion_starless.npy',mmap_mode='r')
# Only the initial radial profile needs whole-canvas reductions. No full-canvas floating grids.
nmax=13000;counts=[np.zeros(nmax) for _ in range(3)];sums=[np.zeros(nmax) for _ in range(3)]
for yy in range(0,7506,128):
 rr=np.rint(np.hypot(np.arange(yy,min(yy+128,7506))[:,None]-CY,np.arange(10551)[None,:]-CX)).astype(int);q=totalfull[yy:yy+128];mm=mfull[yy:yy+128]
 for ch in range(3):
  good=mm&(q[...,ch]>0);ids=rr[good];counts[ch]+=np.bincount(ids,minlength=nmax);sums[ch]+=np.bincount(ids,weights=np.log(np.maximum(q[...,ch][good],1e-8)),minlength=nmax)
print('PROFILES',flush=True)
profiles=json.loads((CAUF/'refined_detail_receipt.json').read_text())['profiles'];oldrep=json.loads((F.parent/'E3_isotropic_filters.json').read_text());sigma=np.array(np.load(CAUF/'resolution_sigma.npy',mmap_mode='r')[sl])
def gauss(a,s):return cv2.GaussianBlur(np.asarray(a,np.float32),(0,0),s,borderType=cv2.BORDER_REFLECT_101)
def normgauss(a,w,s):return gauss(np.where(w>0,a,0)*w,s)/np.maximum(gauss(w,s),1e-8)
tree=ast.parse((R/'research/tools/v29/fuse_and_filter.py').read_text());exec(compile(ast.Module(body=[a for a in tree.body if isinstance(a,ast.FunctionDef) and a.name=='sn_smooth'],type_ignores=[]),'pure','exec'))
layers={'01':([2,4,8,16,32],3.),'04':([1,2,4,8,16],1.5),'05':([2,4,8,16,32,48],3.),'06':([4,8,16,32,64],3.)};sigmas=sorted(set(s for ss,_ in layers.values() for s in ss));raw={key:[[],[]] for key in layers};nt=2880;theta=np.arange(nt)*2*np.pi/nt;radial=np.arange(350,510,.5);co=[CY-2777+radial[:,None]*np.sin(theta),CX-4377+radial[:,None]*np.cos(theta)];pos=np.arange(nmax);reproduction=[]
for ch in range(3):
 good=m&(total[...,ch]>0);ln=np.log(np.maximum(total[...,ch],1e-8));nn=counts[ch];pr=np.divide(sums[ch],nn,out=np.full(nmax,np.nan),where=nn>0);full=np.flatnonzero(nn>=.999*2*np.pi*np.maximum(pos,1));first=int(full[full>.9*RS][0]);slope=np.polyfit(np.arange(first,first+20),pr[first:first+20],1)[0];pr[:first]=pr[first]+slope*(np.arange(first)-first);pr=np.interp(pos,pos[np.isfinite(pr)],pr[np.isfinite(pr)]);oldfill=np.interp(r,pos,pr).astype('float32');oldx=np.where(good,ln,oldfill)
 v=map_coordinates(good.astype(float),co,order=1,mode='nearest');p=map_coordinates(np.where(good,ln,0),co,order=1,mode='nearest')/np.maximum(v,1e-12);valid=v>.999;idx=np.argmax(valid,axis=0);offsets=[]
 for di in [0,1,2]:
  ix=np.minimum(idx+di,len(radial)-1);offsets.append(p[ix,np.arange(nt)]-np.interp(radial[ix],pos,pr))
 off=gaussian_filter1d(np.median(offsets,axis=0),3/(2*np.pi*450/nt),mode='wrap');delta=np.interp(t,theta,off,period=2*np.pi);newx=np.where(good,ln,oldfill+delta).astype('float32');scale=np.interp(np.log(np.maximum(r/RS,1e-5)),profiles[str(ch)]['lnr_centres'],profiles[str(ch)]['robust_contrast']).astype('float32');acc=[{k:np.zeros_like(ln) for k in layers} for _ in range(2)]
 for ss in sigmas:
  for j,z in enumerate([oldx,newx]):
   band=z-gauss(z,ss)
   for k,(sig,_se) in layers.items():
    if ss in sig:acc[j][k]+=band/len(sig)
 for k in layers:
  for j in range(2):raw[k][j].append(np.where(good,acc[j][k]/scale,np.nan).astype('float32'))
 np.savez_compressed(A/f'B5_boundary_ch{ch}.npz',old=oldx,new=newx,good=good,offset=off)
 print('channel',ch,'first',first,'offset',np.percentile(off,[0,50,100]),flush=True)
for key,(sig,se) in layers.items():
 b0=np.nan_to_num(np.nanmedian(raw[key][0],axis=0));b1=np.nan_to_num(np.nanmedian(raw[key][1],axis=0));expected=np.array(np.load(F/f'{key}_float.npy',mmap_mode='r')[sl]);err=abs(b0-expected);good=m&(r<750);rep=dict(key=key,max_error=float(err[good].max()),p99_error=float(np.percentile(err[good],99)));reproduction.append(rep);print(rep,flush=True)
 sc=oldrep[key]['scale_tanh'];d=.5*np.tanh(b1/sc)-.5*np.tanh(b0/sc);d,_=sn_smooth(d,m,sigma=sigma);d=normgauss(d,m.astype(float),se);d[~m]=0;old=np.array(np.load(F/f'{key}_u16.npy',mmap_mode='r')[sl]).astype(float)/65535;new=old+d;np.savez_compressed(A/f'B5_{key}_candidate.npz',old=old,new=new,delta=d,raw_old=b0,raw_new=b1);print(key,'range',new.min(),new.max(),'dmax',abs(d).max(),flush=True)
(O/'B5_reproduction.json').write_text(json.dumps(reproduction,indent=2)+'\n')
