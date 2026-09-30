exec(open('research/tools/v62_prominencies_20260913/a3_masks.py').read().split('rows=[]')[0])
from scipy.ndimage import binary_dilation,distance_transform_edt,gaussian_filter
mx=s.max(-1);dark=mx<.05;labs,n=label(dark);core=labs==labs[1000,1000];outer=distance_transform_edt(~core);innerdist=distance_transform_edt(core)
valid=~binary_dilation(core,iterations=5);den=gaussian_filter(valid.astype('float32'),8);bgG=gaussian_filter(s[...,1]*valid,8)/np.maximum(den,1e-8)
cover=np.clip(s[...,1]/np.maximum(bgG,1e-8),0,1);cover=np.maximum(cover,mx);cover[outer>5]=1;cover[(innerdist>3)&(mx<.005)]=0
dematted=np.divide(s,cover[...,None],out=np.zeros_like(s),where=cover[...,None]>0)
al=soalpha*cover;fg=dematted*al[...,None]+cor*(1-al[...,None]);new=moon*lm[...,None]+fg*(1-lm[...,None])
for nm,bb in [('top',(5250,3303,5305,3350)),('west',(4870,3750,4950,3880))]:
 x0,y0,x1,y1=bb;w=x1-x0;h=y1-y0;k=5;pan=Image.new('RGB',(w*k*4,h*k+25))
 for j,(title,im) in enumerate([('V61',native),('Dematte candidate',new),('Original source',s),('Coverage',np.repeat(cover[...,None],3,2))]):
  pan.paste(cv(im[y0-2777:y1-2777,x0-4377:x1-4377]).resize((w*k,h*k),Image.Resampling.NEAREST),(j*w*k,25));ImageDraw.Draw(pan).text((j*w*k+2,5),title,fill='white')
 pan.save(O/'vistes'/f'B3_{nm}.png')
np.save(A/'B3_dematte_rgb.npy',dematted);np.save(A/'B3_dematte_alpha.npy',cover);np.save(A/'B3_candidate.npy',new)
print('source reconstruction',abs(dematted*cover[...,None]-s).max(),'changed',np.count_nonzero(cover!=1))
