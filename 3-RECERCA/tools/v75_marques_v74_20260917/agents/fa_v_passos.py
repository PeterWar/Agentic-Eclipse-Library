import numpy as np, sys
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
import fa_lib as F
sys.path.insert(0,F.S4); import compo74 as c
C,a,P=c.recompon(exclou=(222,),retorna_passos=True)
grups=[(3,'base'),(42,'+NRGF 41/42'),(53,'+ACHF 47-53'),(46,'+RHEF 45/46'),(55,'+WOW 55'),(56,'+WOW bil 56'),(30,'+30 earthshine'),(76,'+76 interiors'),(202,'final')]
def contorn(m): return m & ~ndi.binary_erosion(m)
for k in F.MARKS:
    m=F.mask(k); y0,y1,x0,x1=F.bbox(m,pad=60); Z=2
    panels=[]
    for lid,nom in grups:
        Cb=P[lid][0][y0:y1,x0:x1]; L=F.Lstar(Cb)
        for mode in ('rgb','dL'):
            if mode=='rgb': im=Image.fromarray((np.clip(Cb,0,1)*255).astype(np.uint8))
            else:
                dl=L-ndi.median_filter(L,41); g=np.clip(128+dl*10,0,255).astype(np.uint8); im=Image.fromarray(np.dstack([g,g,g]))
            im=im.resize(((x1-x0)*Z,(y1-y0)*Z),Image.NEAREST); d=ImageDraw.Draw(im); ys,xs=np.nonzero(contorn(m)[y0:y1,x0:x1])
            for y,x in zip(ys,xs): d.rectangle([x*Z,y*Z,x*Z+Z-1,y*Z+Z-1],outline=(255,0,255))
            d.text((3,3),nom+' '+mode,fill=(255,255,0)); panels.append(im)
    n=len(grups); w=panels[0].width; h=panels[0].height
    out=Image.new('RGB',(w*n+6*(n-1),h*2+6),(40,40,40))
    for i in range(n):
        out.paste(panels[2*i],(i*(w+6),0)); out.paste(panels[2*i+1],(i*(w+6),h+6))
    out.save(F.S4+f'/v_fa_passos_{k}.png'); print(k,out.size)
