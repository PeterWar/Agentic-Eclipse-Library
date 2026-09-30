from filters58 import *
from rhef_native58 import rhef_native_cdf
claim();C=O/'filters';S=O/'sources';a=np.load(S/'base_G.npy');m=np.load(S/'support.npy')&np.isfinite(a)&(a>0);r,t=coords();rep={}
for deg,tag in [(60.,'P02c_RHEF_local60_native'),(30.,'P02d_RHEF_local30_native')]:
 q=rhef_native_cdf(a,m,r,t,deg,deg/4);ok=m&np.isfinite(q);u=np.round(np.clip(np.nan_to_num(q,nan=.5),0,1)*65535).astype('uint16');np.save(C/f'{tag}_u16.npy',u);np.save(C/f'{tag}_float.npy',q);np.save(C/f'{tag}_support.npy',ok);rep[tag]=dict(sha256=sha(C/f'{tag}_u16.npy'),undefined_at_physical_support=int((m&~ok).sum()),operator='CDF at fixed radius, polar spacing0.5px and16384periodic angles, native source interpolation and native rectangular output; no smoothing or annular source blending',source_sha256=sha(S/'base_G.npy'))
 from PIL import Image
 Image.fromarray((u[::4,::4]//257).astype('uint8')).save(O/'vistes'/f'E6_{tag}_full.png');log(tag+' DONE')
save('E6_fixed_radius_filters.json',rep)
