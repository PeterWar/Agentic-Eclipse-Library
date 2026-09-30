import numpy as np
from PIL import Image, ImageDraw
import fa_lib as F
Cps=np.load(F.S4+'/roi74p_compost.npz')['C'][...,:3].astype(np.float32)/65535
C71=np.load(F.S4+'/roi71_C_tot.npy')
def to8(C): return Image.fromarray((np.clip(C,0,1)*255).astype(np.uint8))
for nom,C in (('v74ps',Cps),('v71',C71)):
    im=to8(C)
    for z in (0.33,0.5):
        im.resize((int(2000*z),int(2000*z)),Image.LANCZOS).save(F.S4+f'/v_fa_zoom{int(z*100)}_{nom}.png')
# quadrant N (m2,m3) i W (m4,m5) i SW (m7) al 50 %
for nom,C in (('v74ps',Cps),('v71',C71)):
    im=to8(C)
    for g,(y0,y1,x0,x1) in {'N':(300,900,500,1500),'W':(500,1300,300,900),'SW':(1100,1700,400,1100)}.items():
        im.crop((x0,y0,x1,y1)).resize((int((x1-x0)*0.5),int((y1-y0)*0.5)),Image.LANCZOS).save(F.S4+f'/v_fa_zoom50_{g}_{nom}.png')
print('ok')
