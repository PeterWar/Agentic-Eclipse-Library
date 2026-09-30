"""textura AL LLARG de l'anell (residu d'una mitjana mòbil azimutal) per radi, V74 vs V71 i contingut de la capa 30."""
import numpy as np, json
from scipy.ndimage import map_coordinates, uniform_filter1d
S4='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/e4f0fbff-bfdf-4da5-a1d0-1bbdf0423383/scratchpad'
M=np.array([[0.5767,0.1856,0.1882],[0.2974,0.6273,0.0753],[0.0270,0.0707,0.9911]],np.float32)
def Lstar(C):
    lin=np.clip(C,0,1)**2.2; y=(lin@M.T)[...,1]; f=np.where(y>0.008856,np.cbrt(y),7.787*y+16/116); return 116*f-16
L74=Lstar(np.load(S4+'/fc_V74_C.npy')); L71=Lstar(np.load(S4+'/fc_V71_C.npy'))
d30=np.load(S4+'/roi74p_L30.npz'); L30=Lstar(np.dstack([d30['c0'],d30['c1'],d30['c2']]).astype(np.float32)/65535)
ra=np.arange(438,458,1.0); aa=np.arange(63,123,0.25)
R,A=np.meshgrid(ra,aa,indexing='ij'); xx=998.88+R*np.cos(np.radians(A)); yy=998.41-R*np.sin(np.radians(A))
out={}
for nom,L in [('V74',L74),('V71',L71),('capa30_contingut',L30)]:
    P=map_coordinates(L,[yy,xx],order=1); res=P-uniform_filter1d(P,size=12,axis=1,mode='nearest')  # residu sobre 3°
    out[nom]={f'r{int(r)}':float(np.std(res[i])) for i,r in enumerate(ra)}
print('r    V74    V71   capa30')
for r in ra: k=f'r{int(r)}'; print(f"{int(r)}  {out['V74'][k]:5.2f}  {out['V71'][k]:5.2f}  {out['capa30_contingut'][k]:5.2f}")
json.dump(out,open(S4+'/fc_textura_azimutal.json','w'),indent=1)
