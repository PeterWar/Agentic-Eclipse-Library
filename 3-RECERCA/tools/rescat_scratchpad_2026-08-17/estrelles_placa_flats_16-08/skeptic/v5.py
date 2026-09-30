import numpy as np
M="/Users/USUARI/Desktop/Eclipse 2026/Vixen Unfiltered/Calibrated_Claude/_masters/"
a=np.load(M+"master_10.npy").astype(np.float64)
vis=a[108:108+4639,172:172+6959]
print("master_10 vis: mean %.6f median %.4f"%(vis.mean(),np.median(vis)))
# integer? (n=25 odd -> median is one of the samples -> integer)
frac_int=np.mean(vis==np.round(vis)); print("fraction integer:",frac_int)
v=vis.ravel()
for val in [508,509,510,511,512,513,514,515,516]:
    print("  value %d : %.4f %%"%(val, 100*np.mean(v==val)))
print("  <=511 : %.4f%%   >=512: %.4f%%"%(100*np.mean(v<=511),100*np.mean(v>=512)))
del a,vis,v
b=np.load(M+"master_0.5.npy").astype(np.float64)
vb=b[108:108+4639,172:172+6959]
print("master_0.5 vis: mean %.6f median %.4f frac int %.4f"%(vb.mean(),np.median(vb),np.mean(vb==np.round(vb))))
vv=vb.ravel()
for val in [510.5,511,511.5,512,512.5,513]:
    print("  value %s : %.4f %%"%(val, 100*np.mean(vv==val)))
print("  <512: %.4f%%  ==512: %.4f%%  >512: %.4f%%"%(100*np.mean(vv<512),100*np.mean(vv==512),100*np.mean(vv>512)))
