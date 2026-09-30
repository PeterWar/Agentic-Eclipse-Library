"""Freeze V29 and Pere's marks; full-canvas previews and component inventory."""
import sys,json,subprocess
from pathlib import Path
import numpy as np,cv2
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;CAU=D/'cau';OUT=Path('/Users/USUARI/Desktop/Eclipse 2026/IA/output/v30_20260905')
sys.path.insert(0,str(ROOT/'research/tools/v29'))
from inspect_inputs import sha,channel,inventory
CT=Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals')

def main():
    rep={'sources':{},'marks':[]}
    for label,src in [('V29',CT/'V29.psb'),('marques',Path('/Users/USUARI/Downloads/minicerclesConcentrics.psb'))]:
        dest=CAU/f'input_{label}.psb';assert not dest.exists();subprocess.run(['/bin/cp','-c',str(src),str(dest)],check=True)
        h=sha(dest);assert h==sha(src);s,meta=inventory(dest);rep['sources'][label]={'source':str(src),'snapshot':str(dest),'sha256':h,'bytes':dest.stat().st_size,'inventory':meta}
        if label=='V29':del s;continue
        for i,l in enumerate(s):
            rgb=np.stack([channel(l,c) for c in (0,1,2)],axis=-1);r,g,b=[rgb[...,c].astype('int32') for c in (0,1,2)]
            blue=(b-r>4000)&(b-g>2000)&(b>18000)
            n,lab,stats,centres=cv2.connectedComponentsWithStats(blue.astype('uint8'),8)
            items=[]
            for k in range(1,n):
                x,y,w,h,area=map(int,stats[k])
                if area<20:continue
                item={'component':k,'bbox':[x,y,x+w,y+h],'pixels':area,'xy':centres[k].tolist()};items.append(item)
            np.save(CAU/f'marked_{i}_G16.npy',rgb[...,1]);np.save(CAU/f'marked_{i}_blue.npy',blue)
            im=Image.fromarray((rgb/257).round().astype('uint8'));im.thumbnail((1800,1800),Image.Resampling.LANCZOS);im.save(OUT/f'MARQUES_{i}_llenc_sencer.png')
            rep['marks'].append({'layer':l.name,'i':i,'components':items});print(l.name,len(items),flush=True)
            del rgb,r,g,b,blue,lab,im
        del s
    (CAU/'input_manifest.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
