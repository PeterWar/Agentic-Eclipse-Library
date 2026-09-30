"""C2: on és el verd? Mapa de tint (a*, b* aproximats en sRGB) del compost SENSE filtres al voltant del limbe, a l'escala de visualització (1:2), i perfils de a*/b* respecte del limbe; també amb el limbe de la Lluna (grisa) al costat."""
import sys, numpy as np
NEW='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/6346f583-afd0-49da-9c17-95128c31820e/scratchpad'; S3='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/e4f0fbff-bfdf-4da5-a1d0-1bbdf0423383/scratchpad'
sys.path.insert(0,NEW)
from PIL import Image, ImageCms
from scipy.ndimage import map_coordinates, gaussian_filter
CX,CY,RS=998.88,998.41,456.0
S=np.load(NEW+'/roi71_recomp_sensefiltres.npz'); C=S['C'].astype(np.float32)/65535; a=S['a'].astype(np.float32)/65535; img=C*a[...,None]+(1-a[...,None])
src=ImageCms.ImageCmsProfile(NEW+'/AdobeRGB.icc'); lab=ImageCms.createProfile('LAB')
pil=Image.fromarray(np.uint8(np.clip(img,0,1)*255+.5)); labim=ImageCms.profileToProfile(pil,src,lab,outputMode='LAB'); L,A,B=[np.asarray(ch).astype(np.float32) for ch in labim.split()]; A-=128; B-=128
TH=np.deg2rad(np.arange(0,360,0.25)); RR=np.arange(440,560,1.0)
def perfil(im,a0,a1):
    th=np.deg2rad(np.arange(a0,a1,0.25)); xs=CX+RR[None,:]*np.cos(th[:,None]); ys=CY-RR[None,:]*np.sin(th[:,None]); return np.median(map_coordinates(im,[ys.ravel(),xs.ravel()],order=1,mode='nearest').reshape(len(th),len(RR)),0)
print('Lab (8 bits, sRGB→Lab): a* (+vermell/−verd) i b* (+groc/−blau) per r, sectors de 60°')
print('r:        '+' '.join(f'{int(r):4d}' for r in RR[::8]))
for s in range(0,360,60):
    pa=perfil(A,s,s+60); pbb=perfil(B,s,s+60); pl=perfil(L,s,s+60)
    print(f'{s:3d}–{s+60:3d} a*: '+' '.join(f'{x:4.0f}' for x in pa[::8])); print(f'        b*: '+' '.join(f'{x:4.0f}' for x in pbb[::8])); print(f'        L*: '+' '.join(f'{x:4.0f}' for x in pl[::8]))
# mapa de a* (verd = negatiu) al voltant de la Lluna, a 1:2, i el compost 1:2 tal qual
Am=gaussian_filter(A,2); vis=np.clip(0.5+(Am-np.median(Am[(np.hypot(*np.mgrid[0:2000,0:2000][::-1]-np.array([[[CX]],[[CY]]]))>480)]))/20,0,1)
Image.fromarray(np.uint8(vis*255)).resize((1000,1000)).save(S3+'/v_C2_astar_x2.png')
ImageCms.profileToProfile(pil,src,ImageCms.createProfile('sRGB'),outputMode='RGB').resize((1000,1000),Image.Resampling.LANCZOS).save(S3+'/v_C2_sensefiltres_x2.png'); print('fet')
