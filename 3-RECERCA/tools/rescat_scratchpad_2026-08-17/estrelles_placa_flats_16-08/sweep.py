import os, json, numpy as np, rawpy
from concurrent.futures import ProcessPoolExecutor
D="/Users/USUARI/Desktop/Eclipse 2026/Darks Canon R6III Eclipse"

def one(fn):
    p=os.path.join(D,fn)
    try:
        with rawpy.imread(p) as raw:
            v=raw.raw_image_visible.astype(np.float64)
            c=raw.raw_colors_visible
            med=float(np.median(v))
            d={'file':fn,'median':med,'mean':float(v.mean()),'std':float(v.std()),
               'p99':float(np.percentile(v,99)),'p999':float(np.percentile(v,99.9)),
               'max':float(v.max()),'n_gt1000':int((v>1000).sum()),
               'n_gt600':int((v>600).sum()),
               'ped':[float(np.median(v[c==i])) for i in range(4)],
               'std_ch':[float(v[c==i].std()) for i in range(4)]}
            h,w=v.shape
            d['tiles']=[[round(float(v[i*h//4:(i+1)*h//4,j*w//4:(j+1)*w//4].mean()),3) for j in range(4)] for i in range(4)]
            return d
    except Exception as e:
        return {'file':fn,'error':str(e)}

if __name__=='__main__':
    fns=sorted(f for f in os.listdir(D) if f.upper().endswith('.CR3'))
    print(len(fns),"fitxers")
    with ProcessPoolExecutor(max_workers=8) as ex:
        res=list(ex.map(one,fns,chunksize=4))
    json.dump(res,open('/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/sweep_all.json','w'))
    print("fet")
