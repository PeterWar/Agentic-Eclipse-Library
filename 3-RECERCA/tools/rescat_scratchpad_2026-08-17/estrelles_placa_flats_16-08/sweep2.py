import os, json, numpy as np, rawpy
from concurrent.futures import ProcessPoolExecutor
D="/Users/USUARI/Desktop/Eclipse 2026/Darks Canon R6III Eclipse"
OUT="/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/sweep2.json"

def one(fn):
    try:
        with rawpy.imread(os.path.join(D,fn)) as raw:
            a=raw.raw_image.astype(np.float32)
            v=raw.raw_image_visible.astype(np.float64)
            c=raw.raw_colors_visible
            d={'file':fn}
            d['std_stride4']=float(a[::4,::4].std())
            d['std_full']=float(a.std())
            d['top6_mean']=float(a[:6].mean())
            d['top_ob_mean']=float(a[:108].mean())
            d['top_ob_std']=float(a[:108].std())
            d['ob_left_mean']=float(a[108:,:172].mean())
            d['vis_med']=float(np.median(v)); d['vis_mean']=float(v.mean()); d['vis_std']=float(v.std())
            d['vis_p99']=float(np.percentile(v,99)); d['vis_p999']=float(np.percentile(v,99.9))
            d['vis_max']=float(v.max()); d['n_gt1000']=int((v>1000).sum()); d['n_gt600']=int((v>600).sum())
            d['ped']=[float(np.median(v[c==i])) for i in range(4)]
            d['mean_ch']=[float(v[c==i].mean()) for i in range(4)]
            h,w=v.shape
            d['tiles']=[[round(float(v[i*h//3:(i+1)*h//3,j*w//3:(j+1)*w//3].mean()),4) for j in range(3)] for i in range(3)]
            return d
    except Exception as e:
        return {'file':fn,'error':repr(e)}

if __name__=='__main__':
    fns=sorted(f for f in os.listdir(D) if f.upper().endswith('.CR3'))
    with ProcessPoolExecutor(max_workers=8) as ex:
        res=list(ex.map(one,fns,chunksize=4))
    json.dump(res,open(OUT,'w'))
    print("fet",len(res))
