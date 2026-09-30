"""Coherent Fourier burst pilot, central native-size384 patch (not a product).
Fixed eight directions/four bands. Capture preference derives only from Vixen
cross-prediction against two reference halves excluding that frame. Fourier
magnitude alone never chooses a frame. Same existing G/geometry/FPN as V55.
"""
from common import *
from scipy.fft import rfft2,irfft2
from PIL import Image,ImageDraw
claim();meta=json.loads((OUT/'A1_clean_frames.json').read_text())['frames'];ids=[i for i,m in enumerate(meta) if m['exp']>=.5];n=384;x0=y0=508;sl=np.s_[y0:y0+n,x0:x0+n];allG=np.load(OUT/'arrays/G_frames.npy',mmap_mode='r');allW=np.load(OUT/'arrays/W_frames.npy',mmap_mode='r');gs=np.array([allG[i][sl] for i in ids],float);ws=np.array([allW[i][sl] for i in ids],float);assert np.isfinite(gs).all() and (ws>0).all()
base=np.load(OLD/'arrays/B11_repeatable_all.npz')['source'][sl];y,x=np.mgrid[:n,:n];basis=np.stack([np.ones_like(x),x/n,y/n],-1);win=np.hanning(n)[:,None]*np.hanning(n)[None,:];fit=(win>.25)&(((np.arctan2(y+y0-CY,x+x0-CX)%(2*np.pi))//(np.pi/6)).astype(int)%2==0);hold=(win>.25)&~fit
bands=[[16,24],[24,40],[40,64],[64,96]];p=2;dirs=8
save('B0_protocol.json',dict(method=__doc__,patch=dict(x0=x0,y0=y0,size=n),bands=bands,directions=dirs,exponent=p,fit='Even30degree sectors in central384 patch after fixed Fourier filtering, win>0.25; reference halves shared calibration, Fourier support crosses sectors. No claim of untouched spatial test.',candidate='Baseline plus Fourier difference to coherence-weighted burst on four bands; inverse Hann valid only for pilot win>0.25. Not a full-disc product or new PSB.',weights='precision_i * min(positive cross-response to two independent frame subsets)^2, response normalized to their own mutual power; exclude i from both reference subsets. No Sony/LROC to fit.',gate='Source Sony/LROC and actual-space injections; if promising, full support-aware perfect-reconstruction assembly with unchanged whole-disc judge required'))
def transform(a):
 co=np.linalg.lstsq(basis.reshape(-1,3)*win.ravel()[:,None],a.ravel()*win.ravel(),rcond=None)[0];return rfft2((a-basis@co)*win)
F=np.array([transform(a) for a in gs]);FB=transform(base);fy=np.fft.fftfreq(n)[:,None];fx=np.fft.rfftfreq(n)[None,:];freq=np.hypot(fx,fy);angle=np.arctan2(fy,fx)%np.pi;prec=np.array([np.median(w[fit]) for w in ws]);prec/=prec.sum();out=FB.copy();ordinary=FB.copy();rows=[];gainmaps=[]
for lo,hi in bands:
 for d in range(dirs):
  m=(freq>=1/hi)&(freq<1/lo)&(angle>=d*np.pi/dirs)&(angle<(d+1)*np.pi/dirs);imgs=np.array([irfft2(f*m,s=(n,n)) for f in F]);ratios=[]
  for i in range(len(ids)):
   ia=[j for j in range(len(ids)) if j!=i and j%2==0];ib=[j for j in range(len(ids)) if j!=i and j%2==1];a=np.average(imgs[ia],axis=0,weights=prec[ia]);b=np.average(imgs[ib],axis=0,weights=prec[ib]);ab=np.sum(a[fit]*b[fit]);ca=np.sum(imgs[i][fit]*a[fit]);cb=np.sum(imgs[i][fit]*b[fit]);ratios.append(max(min(ca,cb),0)/max(ab,1e-30) if ab>0 else 0)
  weights=prec*np.array(ratios)**p
  if weights.sum()<=0:weights=prec.copy()
  weights/=weights.sum();mixed=np.einsum('i,ijk->jk',weights,F);std=np.einsum('i,ijk->jk',prec,F);out[m]=mixed[m];ordinary[m]=std[m];rows.append(dict(band=[lo,hi],direction=d,relative_response=ratios,weights=weights));gainmaps.append((m,weights))
candidate=base+np.divide(irfft2(out-FB,s=(n,n)),win,out=np.zeros((n,n)),where=win>.001);simple=base+np.divide(irfft2(ordinary-FB,s=(n,n)),win,out=np.zeros((n,n)),where=win>.001)
# External references are loaded only after the candidate and weights are fixed.
np.savez_compressed(OUT/'arrays/B0_burst_pilot.npz',baseline=base,candidate=candidate,simple=simple,valid=win>.25)
sony=np.load(ROOT/'output/earthshine_detail_20260911/B2_sony_reference.npz')['reference'][sl];lc=np.load(ROOT/'research/tools/v42_20260910/cau/lroc_capa_v39_rgba.npy');bb=json.loads((ROOT/'output/v42_20260910/4-rebuts/P2b_rotacio.json').read_text())['lroc_bbox'];lr=np.zeros((N,N));oy,ox=bb[1]-Y0,bb[0]-X0;lr[oy:oy+lc.shape[0],ox:ox+lc.shape[1]]=lc[...,:3].mean(-1);lroc=lr[sl];arr={'V55source':base,'plain12':simple,'burst':candidate,'Sony':sony,'LROC':lroc};FT={k:transform(a) for k,a in arr.items()};judge=[]
for lo,hi in [[8,16]]+bands:
 sel=(freq>=1/hi)&(freq<1/lo);filtered={k:irfft2(f*sel,s=(n,n)) for k,f in FT.items()}
 for k in ['V55source','plain12','burst']:
  q=dict(band=[lo,hi],candidate=k,Sony=corr(filtered[k],filtered['Sony'],hold),LROC=corr(filtered[k],filtered['LROC'],hold));judge.append(q);print('BURST',q,flush=True)
save('B0_burst_pilot.json',dict(rows=rows,frames=[meta[i] for i in ids],base_precision=prec,judge=judge,limits=['Pilot central support only, not full-disc qualification','Frame reference halves share calibrations and inherited FPN model','Source producer excludes Sony/LROC; previous use of geometry acknowledged','No product before a full-image operator, injection and photographic retention']))
# Context always accompanies a local diagnostic; product source is never edited.
full=Image.open(OLD/'vistes/E3_Photoshop_V55_full.png').convert('RGB');full.thumbnail((1056,751));panel=Image.new('RGB',(1200,1200),'#172021');panel.paste(full,(72,0));dr=ImageDraw.Draw(panel);lo,hi=np.percentile(base[win>.25],[1,99])
for j,(name,a) in enumerate([('Font V55',base),('Pilot fusio',candidate),('Diferencia x4',base+4*(candidate-base))]):
 v=np.clip((a-lo)/(hi-lo)*220+15,0,255).astype('uint8');im=Image.fromarray(v).convert('RGB');panel.paste(im,(j*400,795));dr.text((j*400+12,765),name,fill='white')
panel.save(OUT/'vistes/B0_burst_diagnostic.png')
