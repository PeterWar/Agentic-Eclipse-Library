import rawpy, numpy as np, tifffile, os
V="/Users/USUARI/Desktop/Eclipse 2026/Vixen Unfiltered/"
C=V+"Calibrated_Claude/"
M=C+"_masters/"
t=tifffile.imread(C+"572A2982_cal.tif")
print("cal tif:",t.shape,t.dtype,"min %.3f max %.3f mean %.4f"%(t.min(),t.max(),t.mean()))
with rawpy.imread(V+"572A2982.CR3") as r:
    full=r.raw_image.astype(np.float64); vis=full[108:108+4639,172:172+6959]
m=np.load(M+"master_10.npy").astype(np.float64); mvis=m[108:108+4639,172:172+6959]
print("light vis mean %.4f ; master vis mean %.4f"%(vis.mean(),mvis.mean()))
if t.ndim==2 and t.shape==vis.shape:
    a=vis-mvis; b=vis-511.0
    print("resid(light-master) mean %.5f ; resid(light-511) mean %.5f ; tif mean %.5f"%(a.mean(),b.mean(),t.mean()))
    for lab,x in [("light-master",a),("light-511",b)]:
        d=t.astype(np.float64)-x
        print("  tif - %s : mean %.5f std %.5f max|.| %.5f"%(lab,d.mean(),d.std(),np.abs(d).max()))
else:
    print("shape mismatch, tif shape",t.shape)
    # try scaling / flat
    print("tif sample corner:",t[:2,:4])
