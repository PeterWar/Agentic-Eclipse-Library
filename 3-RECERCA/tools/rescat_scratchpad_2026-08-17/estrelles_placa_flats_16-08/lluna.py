import tifffile, numpy as np, sys, json, os
cfg=json.loads(sys.argv[1]); out=[]
for c in cfg:
    a=tifffile.imread(c["path"]); ds=2
    R=c["R"]; cx=c["cx"]; cy=c["cy"]
    g=a[...,1].astype(np.float32)[::ds,::ds]; rgb=a[::ds,::ds]
    H,W=g.shape; yy,xx=np.mgrid[0:H,0:W]
    r=np.hypot(yy*ds-cy,xx*ds-cx)/R
    rows=[]
    for rr in [0.15,0.3,0.45,0.6,0.75,0.85,0.92]:
        s=(r>=rr-0.075)&(r<rr+0.075)
        if s.sum()<200: continue
        v=g[s]
        rows.append([rr,round(float(np.median(v)),1),round(float(np.percentile(v,16)),1),round(float(np.percentile(v,84)),1),
                     round(float((rgb[s]>=64000).any(-1).mean()),4),
                     round(float(np.median(rgb[s][...,0])),1),round(float(np.median(rgb[s][...,2])),1)])
    out.append({"file":os.path.basename(c["path"]),"exp":c["exp"],"intra":rows})
print(json.dumps(out))
