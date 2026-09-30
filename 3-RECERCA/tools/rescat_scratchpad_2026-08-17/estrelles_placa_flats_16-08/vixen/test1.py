import numpy as np, lib, time
from scipy import ndimage as ndi
t0=time.time()
hm=lib.hotmask('dark_med_10.npy')
print('hot px', hm.sum(), '%.4f%%'%(100*hm.mean()))
im=lib.load_raw('572A2982')
dk=np.load('dark_med_10.npy')[:lib.H,:lib.W]
sat=(im>=lib.SAT)
print('sat frac %.4f'%sat.mean())
im=im-dk
bad=sat|hm
bad=ndi.binary_dilation(bad,np.ones((3,3)))
g=lib.green_full(im,bad)
print('green_full done',time.time()-t0)
mask=~np.isfinite(g)
bg,sig,res=lib.bg_and_sigma(np.nan_to_num(g,nan=np.nan),bs=24,mask=mask)
print('bg done',time.time()-t0)
snr=np.where(mask,0,res/sig)
print('snr stats', np.percentile(snr[~mask],[1,50,99,99.9,99.99]), snr[~mask].max())
print('sigma map median', np.median(sig[~mask]))
print('bg median', np.median(bg))
# count pixels above thresholds
for T in [4,5,6,8,10]:
    print('  >%d sigma: %d px'%(T,(snr>T).sum()))
np.save('t_snr.npy',snr.astype(np.float32)); np.save('t_res.npy',res); np.save('t_sig.npy',sig); np.save('t_mask.npy',mask)
print(time.time()-t0)
