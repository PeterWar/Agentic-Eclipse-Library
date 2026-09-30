"""fc: diferència V74−V71 fora del limbe, i vistes (retalls 300 % az 80–110 i tires polars r 430–480 az 60–125)."""
import numpy as np, json
from PIL import Image, ImageDraw
S4='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/e4f0fbff-bfdf-4da5-a1d0-1bbdf0423383/scratchpad'
Y,X=np.mgrid[0:2000,0:2000]; rr=np.hypot(X-998.88,Y-998.41); az=(np.degrees(np.arctan2(-(Y-998.41),X-998.88)))%360
M=np.array([[0.5767,0.1856,0.1882],[0.2974,0.6273,0.0753],[0.0270,0.0707,0.9911]],np.float32)
def Lstar(C):
    lin=np.clip(C,0,1)**2.2; y=(lin@M.T)[...,1]; f=np.where(y>0.008856,np.cbrt(y),7.787*y+16/116); return 116*f-16
C74=np.load(S4+'/fc_V74_C.npy'); C71=np.load(S4+'/fc_V71_C.npy'); L74=Lstar(C74); L71=Lstar(C71)
mk=np.load(S4+'/marques74_masks.npz'); m1=mk['m1']
d=L74-L71; s=(az>=60)&(az<125)
res={}
for r0,r1 in [(456,458),(458,462),(462,470),(470,480),(440,448),(448,456)]:
    m=s&(rr>=r0)&(rr<r1); res[f'{r0}-{r1}']={'dL_mediana':float(np.median(d[m])),'dL_abs_max':float(np.abs(d[m]).max()),'dL_abs_p99':float(np.percentile(np.abs(d[m]),99))}
# textura: desviació local (std en finestra 5x5) marca vs entorn al traç curt
from scipy.ndimage import uniform_filter
def std_local(L,k=5):
    m=uniform_filter(L,k); return np.sqrt(np.maximum(uniform_filter(L*L,k)-m*m,0))
curt=m1&(rr>=456); llarg=m1&(rr<456)
for nom,L in [('V74',L74),('V71',L71)]:
    sl=std_local(L); rlo,rhi=rr[curt].min(),rr[curt].max()
    e=(~m1)&(rr>=rlo)&(rr<=rhi)&(az>=60)&(az<125)
    res[f'textura_trac_curt_{nom}']={'std5_marca':float(np.median(sl[curt])),'std5_entorn':float(np.median(sl[e]))}
    # perfil azimutal del traç curt: L* mitjana a r 458–465 per bin d'1° de az 60–125
    prof=[float(np.median(L[(rr>=458)&(rr<465)&(az>=a)&(az<a+1)])) for a in range(60,125)]
    res[f'az_prof_r458_465_{nom}']=[round(v,2) for v in prof]
    prof2=[float(np.median(L[(rr>=449)&(rr<453)&(az>=a)&(az<a+1)])) for a in range(60,125)]
    res[f'az_prof_r449_453_{nom}']=[round(v,2) for v in prof2]
json.dump(res,open(S4+'/fc_dif_v74_v71.json','w'),indent=1)
print(json.dumps({k:v for k,v in res.items() if not k.startswith('az_prof')},indent=1))
# ---- vistes ----
def to8(C,guany=1.0):
    return (np.clip(C*guany,0,1)**(1/1.0)*255).astype(np.uint8)
# retall az 80–110, r 430–480 → caixa en píxels de la ROI
sel=(az>=78)&(az<=112)&(rr>=425)&(rr<=485); ys,xs=np.where(sel); y0,y1,x0,x1=ys.min(),ys.max()+1,xs.min(),xs.max()+1
print('retall',x0,x1,y0,y1,'llenç',x0+4377,x1+4377,y0+2777,y1+2777)
def retall(C,g):
    im=Image.fromarray(to8(C[y0:y1,x0:x1],g)); return im.resize((im.width*3,im.height*3),Image.NEAREST)
for g,tag in [(1.0,'to_normal'),(3.0,'to_x3')]:
    a=retall(C71,g); b=retall(C74,g); W=a.width; im=Image.new('RGB',(W*2+12,a.height+24),(40,40,40)); im.paste(a,(0,24)); im.paste(b,(W+12,24))
    dr=ImageDraw.Draw(im); dr.text((4,4),f'V71 (Pere)  az 80-110, r 430-480, 300 %, {tag}',fill=(255,255,255)); dr.text((W+16,4),'V74 (re-desada per Pere, sense capa 222)',fill=(255,255,255))
    im.save(S4+f'/v_fc_retall300_az80-110_{tag}.png')
# mateix retall amb la marca m1 superposada (contorn) sobre V74
b=np.array(retall(C74,3.0)); mm=np.kron(m1[y0:y1,x0:x1],np.ones((3,3),bool)); 
from scipy.ndimage import binary_dilation
cont=binary_dilation(mm,iterations=1)&~mm; b[cont]=[255,0,255]; Image.fromarray(b).save(S4+'/v_fc_retall300_az80-110_V74_amb_m1.png')
# tira polar r 430–480 (files, 1 px) × az 60–125 (columnes, 0,25°)
def polar(C,g):
    ra=np.arange(430,480,1.0); aa=np.arange(60,125,0.25)
    R,A=np.meshgrid(ra,aa,indexing='ij'); xx=998.88+R*np.cos(np.radians(A)); yy=998.41-R*np.sin(np.radians(A))
    from scipy.ndimage import map_coordinates
    out=np.stack([map_coordinates(C[...,i],[yy,xx],order=1) for i in range(3)],-1); return to8(out,g)
for g,tag in [(1.0,'to_normal'),(3.0,'to_x3')]:
    p71=polar(C71,g); p74=polar(C74,g); pm=polar(m1.astype(np.float32)[...,None].repeat(3,-1),1.0)[...,0]>127
    H,W=p71.shape[:2]; k=3; im=Image.new('RGB',(W*k+8,H*k*3+60),(40,40,40)); dr=ImageDraw.Draw(im)
    for j,(p,t) in enumerate([(p71,'V71'),(p74,'V74'),(p74,'V74 + marca m1 (lila)')]):
        q=p.copy()
        if j==2: q[pm]=[255,0,255]
        im.paste(Image.fromarray(q).resize((W*k,H*k),Image.NEAREST),(4,20+j*(H*k+20))); dr.text((4,4+j*(H*k+20)),f'{t}  tira polar r 430-480 (amunt=430) x az 60-125 (esq=60), x3, {tag}',fill=(255,255,255))
    im.save(S4+f'/v_fc_polar_r430-480_az60-125_{tag}.png')
print('vistes fetes')
