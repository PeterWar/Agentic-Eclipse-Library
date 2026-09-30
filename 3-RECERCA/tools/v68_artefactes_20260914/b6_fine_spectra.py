from pathlib import Path
import numpy as np,json
from scipy.ndimage import gaussian_filter,maximum_filter
from PIL import Image,ImageDraw
R=Path.cwd();O=R/'output/v68_artefactes_20260914';A=O/'arrays';P=R/'output/earthshine_max_detail_20260913';s=np.s_[700:1100,420:820];N=400;y,x=np.mgrid[:N,:N];win=np.hanning(N)[:,None]*np.hanning(N)[None,:];fy=np.fft.fftshift(np.fft.fftfreq(N))[:,None];fx=np.fft.fftshift(np.fft.fftfreq(N))[None,:];rr=np.hypot(fy,fx);radbin=np.rint(rr*N).astype(int)
z=np.load(R/'output/earthshine_v56_three_routes_20260913/arrays/R5_sources.npz');a=np.load(A/'L30_C1.npy')[300:1700,301:1701];srcs={'V67':a,'Gclean':z['Gclean'],'Rclean':z['red_repeatable'],'Sony':np.load(R/'output/earthshine_detail_20260911/B2_sony_reference.npz')['reference']}
for stem in ['572A2978','572A2979','572A2980','572A2981','572A2982','572A2983','572A2984']:
 z=np.load(P/'native'/('vixen_'+stem+'.npz'));srcs[stem]=(z['G1']+z['G2'])/2
results=[];panel=Image.new('RGB',(1600,440*((len(srcs)+3)//4)),'#151515');dr=ImageDraw.Draw(panel)
for j,(name,a) in enumerate(srcs.items()):
 q=np.nan_to_num(a[s]);q=(q-gaussian_filter(q,12))*win;F=np.fft.fftshift(np.fft.fft2(q));power=abs(F)**2;mean=np.bincount(radbin.ravel(),weights=power.ravel())/np.maximum(np.bincount(radbin.ravel()),1);wh=power/mean[radbin];valid=(rr>1/12)&(rr<1/3)&(fx>0);peaks=valid&(wh==maximum_filter(wh,7));iy,ix=np.where(peaks);sort=np.argsort(wh[iy,ix])[-12:][::-1];peakslist=[dict(fx=float(fx[0,ix[i]]),fy=float(fy[iy[i],0]),ratio=float(wh[iy[i],ix[i]]),wavelength=float(1/rr[iy[i],ix[i]])) for i in sort];results.append(dict(source=name,peaks=peakslist));im=Image.fromarray(np.uint8(np.clip(np.log1p(wh)/np.log(100),0,1)*255));panel.paste(im,((j%4)*400,(j//4)*440+40));dr.text(((j%4)*400+8,(j//4)*440+10),name,fill='white');print(name,peakslist[:3],flush=True)
panel.save(O/'vistes/B6_fine_spectra.png');(O/'B6_spectra.json').write_text(json.dumps(results,indent=2)+'\n')
