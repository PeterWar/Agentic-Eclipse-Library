"""Uncertainty-limited burst, after B0 overweights noisy short captures.
Response preference is enabled only if repeated across six training sectors.
Jackknife uncertainty shrinks the excess over unity; p=2 stays frozen. This is
a distinct Vixen-only estimator; Sony never selects the shrinkage or exponent.
"""
from common import *
from scipy.fft import rfft2,irfft2
claim();meta=json.loads((OUT/'A1_clean_frames.json').read_text())['frames'];ids=[i for i,m in enumerate(meta) if m['exp']>=.5];n=384;x0=y0=508;sl=np.s_[y0:y0+n,x0:x0+n];gg=np.load(OUT/'arrays/G_frames.npy',mmap_mode='r');ww=np.load(OUT/'arrays/W_frames.npy',mmap_mode='r');gs=np.array([gg[i][sl] for i in ids],float);ws=np.array([ww[i][sl] for i in ids],float);base=np.load(OLD/'arrays/B11_repeatable_all.npz')['source'][sl];y,x=np.mgrid[:n,:n];Q=np.stack([np.ones_like(x),x/n,y/n],-1);win=np.hanning(n)[:,None]*np.hanning(n)[None,:];sec=((np.arctan2(y+y0-CY,x+x0-CX)%(2*np.pi))//(np.pi/6)).astype(int);fit=(win>.25)&(sec%2==0);hold=(win>.25)&(sec%2==1);bands=[[16,24],[24,40],[40,64],[64,96]]
save('B1_protocol.json',dict(method=__doc__,bands=bands,directions=8,exponent=2,training='Six even30degree spatial sectors, frame excluded from two reference halves. Jackknife across six sectors; if positive response excess does not exceed2*SE, use ordinary precision. Otherwise excess reduced by2*SE, response may decrease below1 only if same evidence.',limits='Conditional cross-sector Fourier support, not six independent tests. Central pilot support unchanged. No full-disc product.'))
def transform(a):
 co=np.linalg.lstsq(Q.reshape(-1,3)*win.ravel()[:,None],a.ravel()*win.ravel(),rcond=None)[0];return rfft2((a-Q@co)*win)
F=np.array([transform(a) for a in gs]);FB=transform(base);prec=np.array([np.median(w[fit]) for w in ws]);prec/=prec.sum();fy=np.fft.fftfreq(n)[:,None];fx=np.fft.rfftfreq(n)[None,:];fr=np.hypot(fx,fy);ang=np.arctan2(fy,fx)%np.pi;out=FB.copy();rows=[]
for lo,hi in bands:
 for d in range(8):
  m=(fr>=1/hi)&(fr<1/lo)&(ang>=d*np.pi/8)&(ang<(d+1)*np.pi/8);imgs=np.array([irfft2(f*m,s=(n,n)) for f in F]);response=[];unc=[]
  for i in range(len(ids)):
   ia=[j for j in range(len(ids)) if j!=i and j%2==0];ib=[j for j in range(len(ids)) if j!=i and j%2==1];a=np.average(imgs[ia],axis=0,weights=prec[ia]);b=np.average(imgs[ib],axis=0,weights=prec[ib]);num=[];den=[]
   for s in range(0,12,2):
    sel=fit&(sec==s);num.append(min(float(np.sum(imgs[i][sel]*a[sel])),float(np.sum(imgs[i][sel]*b[sel]))));den.append(float(np.sum(a[sel]*b[sel])))
   num=np.array(num);den=np.array(den);ratio=num.sum()/den.sum() if den.sum()>0 else 1.;jack=np.divide(num.sum()-num,den.sum()-den,out=np.ones(6),where=(den.sum()-den)>0);se=float(np.sqrt(5/6*np.sum((jack-jack.mean())**2)));excess=np.sign(ratio-1)*max(abs(ratio-1)-2*se,0);response.append(max(1+excess,0));unc.append(dict(ratio=ratio,jackknife_se=se))
  w=prec*np.array(response)**2;w=w/w.sum() if w.sum()>0 else prec;out[m]=np.einsum('i,ijk->jk',w,F)[m];rows.append(dict(band=[lo,hi],direction=d,response=response,uncertainty=unc,weights=w))
candidate=base+np.divide(irfft2(out-FB,s=(n,n)),win,out=np.zeros((n,n)),where=win>.001);np.savez_compressed(OUT/'arrays/B1_burst_pilot.npz',baseline=base,candidate=candidate,valid=win>.25)
sony=np.load(ROOT/'output/earthshine_detail_20260911/B2_sony_reference.npz')['reference'][sl];lc=np.load(ROOT/'research/tools/v42_20260910/cau/lroc_capa_v39_rgba.npy');bb=json.loads((ROOT/'output/v42_20260910/4-rebuts/P2b_rotacio.json').read_text())['lroc_bbox'];lr=np.zeros((N,N));oy,ox=bb[1]-Y0,bb[0]-X0;lr[oy:oy+lc.shape[0],ox:ox+lc.shape[1]]=lc[...,:3].mean(-1);FT={k:transform(a) for k,a in dict(V55source=base,burst=candidate,Sony=sony,LROC=lr[sl]).items()};judge=[]
for lo,hi in [[8,16]]+bands:
 sel=(fr>=1/hi)&(fr<1/lo);B={k:irfft2(f*sel,s=(n,n)) for k,f in FT.items()}
 for k in ['V55source','burst']:
  row=dict(band=[lo,hi],candidate=k,Sony=corr(B[k],B['Sony'],hold),LROC=corr(B[k],B['LROC'],hold));judge.append(row);print('BURST REG',row,flush=True)
save('B1_burst_pilot.json',dict(rows=rows,judge=judge,limits=['No full-disc product; no independent optical sharpness identification','Same central support and external bands as B0, repeated-use exploratory']))
