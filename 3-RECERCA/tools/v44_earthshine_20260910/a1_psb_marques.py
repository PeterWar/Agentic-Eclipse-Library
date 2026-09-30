"""Read original + marked PSB; preserve annotations and measure exact channels."""
import sys, json, gc
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import label
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'research/tools/v39_20260909'))
import c4_projecte_v39 as C
from psd_tools import PSDImage
OUT = ROOT/'output/v44_earthshine_20260910'
CAU = Path(__file__).parent/'cau'; CAU.mkdir(exist_ok=True)
CI = Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors')
X0,Y0,N=4677,3077,1400
def tile(l,c):
    if c == -2 and l._record.mask_data is None: return None
    a=C.channel(l,c)
    if a is None:return None
    md=l._record.mask_data
    x,y=(md.left,md.top) if c==-2 else (l.left,l.top)
    out=np.zeros((N,N),np.uint16)
    xa,ya=max(X0,x),max(Y0,y); xb,yb=min(X0+N,x+a.shape[1]),min(Y0+N,y+a.shape[0])
    if xb>xa and yb>ya:out[ya-Y0:yb-Y0,xa-X0:xb-X0]=a[ya-y:yb-y,xa-x:xb-x]
    return out
def main():
    a=PSDImage.open(CI/'Earthshine_V43.psb'); b=PSDImage.open(CI/'Earthshine_V43_detall.psb'); old={l.name:l for l in a}; rep=[]
    logpath=OUT/'4-rebuts/A1.log'
    if logpath.exists():
        for line in logpath.read_text().splitlines():
            if line.startswith('{'): rep.append(json.loads(line))
    done={row['name'] for row in rep}
    yy,xx=np.mgrid[:N,:N]; rr=np.hypot(xx-699.568111973117,yy-699.6475341408573)
    order=[l for l in b if l.name.startswith('09 ') or l.name.endswith('limbe net') and 'fosc' in l.name]+[l for l in b if not (l.name.startswith('09 ') or l.name.endswith('limbe net') and 'fosc' in l.name)]
    for l in order:
        if l.name in done: continue
        o=old[l.name]; rgb=np.stack([tile(l,c) for c in range(3)],-1); ref=np.stack([tile(o,c) for c in range(3)],-1)
        dif=np.max(np.abs(rgb.astype(int)-ref.astype(int)),axis=-1)>2
        m=tile(l,-2); om=tile(o,-2)
        rec=dict(name=l.name,changed_rgb_pixels=int(dif.sum()),mask_equal=(m is None and om is None) or bool(np.array_equal(m,om)))
        if dif.any():
            Image.fromarray((rgb>>8).astype('uint8')).save(OUT/'lliurables/vistes'/f'A1_capa_{len(rep):02d}_anotada.png')
            Image.fromarray((ref>>8).astype('uint8')).save(OUT/'lliurables/vistes'/f'A1_capa_{len(rep):02d}_font.png')
            g=(rgb[...,1].astype(float)>rgb[...,0]*1.2)&(rgb[...,1].astype(float)>rgb[...,2]*1.2)&dif
            cy=(rgb[...,2].astype(float)>rgb[...,0]*1.3)&(rgb[...,1].astype(float)>rgb[...,0]*1.3)&dif
            for name,z in [('verd',g),('cian',cy)]:
                lab,n=label(z); rows=[]
                for j in range(1,n+1):
                    msk=lab==j
                    if msk.sum()<5:continue
                    y,x=np.where(msk); rows.append(dict(n=int(msk.sum()),bbox=[int(x.min()+X0),int(y.min()+Y0),int(x.max()+X0+1),int(y.max()+Y0+1)],r_percentiles=np.percentile(rr[msk],[0,10,50,90,100]).tolist()))
                rec[name]=rows; np.save(CAU/f'marques_{name}.npy',z)
        if l.name.startswith('09 ') or l.name.endswith('limbe net') and 'fosc' in l.name:
            stem='pere09' if l.name.startswith('09 ') else 'v43'
            np.save(CAU/f'{stem}_rgb.npy',ref)
            if om is not None:np.save(CAU/f'{stem}_mask.npy',om)
        rep.append(rec); print(json.dumps(rec,ensure_ascii=False),flush=True); gc.collect()
        (OUT/'4-rebuts/A1_marques.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2)+'\n')
    (OUT/'4-rebuts/A1_marques.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
