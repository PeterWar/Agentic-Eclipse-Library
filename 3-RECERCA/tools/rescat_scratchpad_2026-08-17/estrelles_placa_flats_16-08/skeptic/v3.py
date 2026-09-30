import numpy as np
M="/Users/USUARI/Desktop/Eclipse 2026/Vixen Unfiltered/Calibrated_Claude/_masters/"
for name in ["master_10.npy","master_0.5.npy","master_0.25.npy","master_1.npy","master_2.npy"]:
    a=np.load(M+name, mmap_mode='r')
    a=np.asarray(a,dtype=np.float64)
    vis=a[108:108+4639,172:172+6959]
    print(name,"shape",a.shape)
    print("   FULL   median %.6f mean %.6f std %.4f"%(np.median(a),a.mean(),a.std()))
    print("   VIS    median %.6f mean %.6f std %.4f min %.1f max %.1f"%(np.median(vis),vis.mean(),vis.std(),vis.min(),vis.max()))
    rp=a.mean(axis=1); print("   rows0-9",np.round(rp[:10],1))
    del a,vis
