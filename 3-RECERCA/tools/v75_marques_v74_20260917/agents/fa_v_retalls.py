import numpy as np, json
from PIL import Image, ImageDraw
import fa_lib as F
C74=np.load(F.S4+'/roi74p_C_sensemarques.npy'); C71=np.load(F.S4+'/roi71_C_sensemarques.npy')
Cps=np.load(F.S4+'/roi74p_compost.npz')['C']  # compost Photoshop amb la capa de marques
print('compost PS', Cps.shape, Cps.dtype, Cps.max())
L74=F.Lstar(C74); L71=F.Lstar(C71)
def to8(C): return (np.clip(C,0,1)**(1/1.0)*255).astype(np.uint8)
def contorn(m):
    from scipy import ndimage as ndi
    return m & ~ndi.binary_erosion(m)
for k in F.MARKS:
    m=F.mask(k); y0,y1,x0,x1=F.bbox(m,pad=40)
    Z=4
    panels=[]
    for nom,C in (('V74',C74),('V71',C71)):
        im=Image.fromarray(to8(C[y0:y1,x0:x1])).resize(((x1-x0)*Z,(y1-y0)*Z),Image.NEAREST)
        d=ImageDraw.Draw(im); ys,xs=np.nonzero(contorn(m)[y0:y1,x0:x1])
        for y,x in zip(ys,xs): d.rectangle([x*Z,y*Z,x*Z+Z-1,y*Z+Z-1],outline=(255,0,255))
        # cercle R=456
        d.ellipse([(F.CX-F.R-x0)*Z,(F.CY-F.R-y0)*Z,(F.CX+F.R-x0)*Z,(F.CY+F.R-y0)*Z],outline=(0,255,255))
        d.text((4,4),nom+' '+k,fill=(255,255,0)); panels.append(im)
    # compost de Photoshop (amb el traç de Pere), sense contorn
    ps=Cps[y0:y1,x0:x1]
    if ps.dtype!=np.uint8: ps=(ps.astype(np.float32)/ps.max()*255).astype(np.uint8)
    im=Image.fromarray(ps[...,:3]).resize(((x1-x0)*Z,(y1-y0)*Z),Image.NEAREST); ImageDraw.Draw(im).text((4,4),'PS amb marca',fill=(255,255,0)); panels.append(im)
    # L* estirat: (L−mediana local 41)+50 → mostra l'estructura fina
    from scipy import ndimage as ndi
    for nom,L in (('dL74',L74),('dL71',L71)):
        Lc=L[y0:y1,x0:x1]; dl=Lc-ndi.median_filter(Lc,41); g=np.clip(128+dl*12,0,255).astype(np.uint8)
        im=Image.fromarray(np.dstack([g,g,g])).resize(((x1-x0)*Z,(y1-y0)*Z),Image.NEAREST); d=ImageDraw.Draw(im); ys,xs=np.nonzero(contorn(m)[y0:y1,x0:x1])
        for y,x in zip(ys,xs): d.rectangle([x*Z,y*Z,x*Z+Z-1,y*Z+Z-1],outline=(255,0,255))
        d.text((4,4),nom+' (x12, gris=0)',fill=(255,255,0)); panels.append(im)
    W=sum(p.width for p in panels)+10*(len(panels)-1); H=max(p.height for p in panels)
    out=Image.new('RGB',(W,H),(40,40,40)); x=0
    for p in panels: out.paste(p,(x,0)); x+=p.width+10
    out.save(F.S4+f'/v_fa_retall_{k}.png'); print(k,out.size)
