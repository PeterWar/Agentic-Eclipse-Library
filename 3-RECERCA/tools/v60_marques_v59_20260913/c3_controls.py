from composite60 import *
from scipy.ndimage import gaussian_filter,map_coordinates,distance_transform_edt
claim();wl=np.load(O/'arrays/C2_lunar_protection.npy');pm=np.load(O/'arrays/C2_prominence_protection.npy');base=read(9,-2);y,x=np.indices(wl.shape);d=distance_transform_edt(read(29,-2)==0);theta=np.mod(np.arctan2(y-(3776.6475-2777),x-(5376.5681-4377)),2*np.pi);sec=(theta/(np.pi/6)).astype(int);reserved=sec%2==1
rep={'claim':'Filter DC boundary and physical lunar opacity; not new measured coronal detail','constant_controls':{},'injections':[],'source_retention':{}}
for i in range(11,17):
 f=read(i,1);new=np.load(O/'arrays'/f'C2_L{i:02d}_gray.npy')/65535;m=read(i,-2);nm=np.load(O/'arrays'/f'C2_L{i:02d}_mask.npy')/65535;a=read(i,-1)*rows[i]['opacity']/255
 # Constant source controls isolate the mask-caused ring, before and after.
 good=(base>.999)&(pm==0)&(d<30)&(d>1)&reserved
 old=1-a*m*.5;correct=1-a*nm*.5;expected=1-a*base*.5
 near=good&(d<4);far=good&(d>15)
 rep['constant_controls'][str(i)]={'old_near_far_gain_difference':float(np.median(old[near])-np.median(old[far])),'new_max_gain_residual':float(abs(correct[good]-expected[good]).max()),'outside_lunar_protection_RGB_exact':bool(np.array_equal(np.rint(f[wl==1]*65535),np.rint(new[wl==1]*65535)))}
 assert rep['constant_controls'][str(i)]['new_max_gain_residual']<1e-12
 # Frozen boundary operator has identity response wherever detailed signal is enabled.
 support=(wl==1)&(pm==0)&(base>.999)&reserved&(d<100)
 for wave in [8,16,24,40]:
  signal=.01*np.sin(2*np.pi*x/wave+.731)*support
  den=gaussian_filter(((wl==1)&(pm==0)&(m>.999)&(read(i,-1)>.999)).astype(float),16)
  v=(wl==1)&(pm==0)&(m>.999)&(read(i,-1)>.999)
  transported=wl*signal+(1-wl)*gaussian_filter(signal*v,16)/np.maximum(den,1e-30)
  gain=float(np.sum(transported[support]*signal[support])/np.sum(signal[support]**2));assert .9<=gain<=1.1
  rep['injections'].append({'layer':i,'wavelength':wave,'gain_on_supported_reserved_detail':gain})
 # Separately transported fixed observed Vixen and Sony samples retain all supported detail.
for n in ['vixen','sony']:
 src=np.load(PREV/'sources'/f'{n}_starless.npy',mmap_mode='r')[2777:4777,4377:6377,1].astype(float);valid=np.isfinite(src)&(src>0)&(wl==1)&(pm==0)&reserved
 sig=np.where(valid,np.log(np.maximum(src,1e-20)),0);den=gaussian_filter(valid.astype(float),16);out=wl*sig+(1-wl)*gaussian_filter(sig,16)/np.maximum(den,1e-30)
 rep['source_retention'][n]={'supported_samples':int(valid.sum()),'max_difference':float(abs(out[valid]-sig[valid]).max()),'qualification':'Algebraic identity on valid unprotected source; no independence/new-detail claim'}
 assert rep['source_retention'][n]['max_difference']==0
rep['PASS']=True;save('C3_frozen_controls.json',rep);print('CONTROLS PASS',len(rep['injections']))
