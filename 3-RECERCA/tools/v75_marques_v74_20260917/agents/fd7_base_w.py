"""fd7: la base 3 de V74 dins la silueta: és fosca a tots els sectors? (a fd1 'després de 56' a az 150–172 surt L* 92 a r 450–452)."""
import numpy as np, json
import fd_lib as F
c74=F.compo74(); c71=F.compo71()
rgb3,al3=c74.carrega(3); L3=F.Lstar(rgb3); rgb3_71,al3_71=c71.carrega(3); L3_71=F.Lstar(rgb3_71)
res={}
print('sector | L* base3 V74 a r 300-400 / 440-450 / 450-453 / 453-455 / 455-457 | alfa3 440-450 | V71 base3 440-450 / 450-453')
for a in range(0,360,10):
    s=F.sector(a,a+10); q={}
    for nom,(r0,r1) in {'r300_400':(300,400),'r440_450':(440,450),'r450_453':(450,453),'r453_455':(453,455),'r455_457':(455,457)}.items(): q[nom]=round(float(np.median(L3[s&F.anell(r0,r1)])),1)
    q['alfa3_440_450']=round(float(al3[s&F.anell(440,450)].mean()),3); q['V71_440_450']=round(float(np.median(L3_71[s&F.anell(440,450)])),1); q['V71_450_453']=round(float(np.median(L3_71[s&F.anell(450,453)])),1)
    res[a]=q; print('%3d | %5.1f %5.1f %5.1f %5.1f %5.1f | %.3f | %5.1f %5.1f'%(a,q['r300_400'],q['r440_450'],q['r450_453'],q['r453_455'],q['r455_457'],q['alfa3_440_450'],q['V71_440_450'],q['V71_450_453']))
# mapa: on és clara la base dins r<452?
clar=(L3>30)&(F.RR<452); res['frac_base_clara_dins_452']=float(clar.mean()/((F.RR<452).mean()))
ys,xs=np.nonzero(clar); res['base_clara_bbox_roi']=[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())] if len(xs) else None
res['base_clara_az_hist']={int(a):int((clar&F.sector(a,a+30)).sum()) for a in range(0,360,30)}
res['base_clara_r_min']=float(F.RR[clar].min()) if clar.any() else None
print('base clara (L*>30) dins r<452: fracció %.3f, bbox %s, r_min %s'%(res['frac_base_clara_dins_452'],res['base_clara_bbox_roi'],res['base_clara_r_min']))
print('per sector 30°:',res['base_clara_az_hist'])
F.dump('fd7_base_w',res)
from PIL import Image
im=np.clip(rgb3[400:1600,400:1600],0,1); Image.fromarray((im*255).astype(np.uint8)).resize((600,600),Image.BILINEAR).save(F.S4+'/v_fd_base3_v74_lluna.png')
im=np.clip(rgb3_71[400:1600,400:1600],0,1); Image.fromarray((im*255).astype(np.uint8)).resize((600,600),Image.BILINEAR).save(F.S4+'/v_fd_base3_v71_lluna.png')
print('fd7 fet')
