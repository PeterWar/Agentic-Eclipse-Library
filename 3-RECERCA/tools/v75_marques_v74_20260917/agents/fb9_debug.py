"""fb9: per què la variant B no treu la taca? Mesura consistent (mitjana i mediana, σ12) de cada camp intermedi, i mapes."""
import sys, numpy as np, json
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/e4f0fbff-bfdf-4da5-a1d0-1bbdf0423383/scratchpad')
from fb6_candidata import *
from scipy.ndimage import gaussian_filter
V=np.load(S4+'/fb6b_variants.npz'); candB=V['candB']; Vlin=V['Vlin']; c0=float(V['c0'])
f,finv,xc,yi=ajusta_f(RAWs,P); lin=finv(P); linp=lin-(Vlin-c0); fl=f(linp); kap=kappa()
fR=f(RAWs); rho=P-fR
disc=(rr<430)
def s12(A): 
    m=disc.astype(float); return gaussian_filter(np.nan_to_num(A)*m,12)/np.maximum(gaussian_filter(m,12),1e-9)
def mesures(nom,A,rel=True):
    a=s12(A); md=float(np.median(a[m6])); me=float(np.median(a[e6])); mn_d=float(a[m6].mean()); mn_e=float(a[e6].mean())
    if rel: print(f'{nom:28s} σ12: mediana dins {md:9.2f} entorn {me:9.2f} → ln {np.log(md/me):+.4f} | mitjana dins {mn_d:9.2f} entorn {mn_e:9.2f} → ln {np.log(mn_d/mn_e):+.4f}')
    else: print(f'{nom:28s} σ12: mediana dins {md:9.2f} entorn {me:9.2f} → dif {md-me:+.1f} | mitjana dif {mn_d-mn_e:+.1f}')
mesures('RAWs (lineal)',RAWs); mesures('f⁻¹(P) (lineal)',lin); mesures('Vlin−c0 (lineal, additiu)',Vlin-c0,rel=False); mesures('RAWs−(Vlin−c0)',RAWs-(Vlin-c0)); mesures("f⁻¹(P)−(Vlin−c0)",linp)
mesures('f(RAWs)',fR); mesures('P',P); mesures('ρ = P − f(RAWs) (additiu)',rho,rel=False); mesures('f(lin′)',fl); mesures('candB (amb κ)',candB); mesures('capa69',G69); mesures('capa74',G74); mesures('κ',kap,rel=False)
# on és el mínim de la taca dins de la marca? radi mitjà de la marca i de l'entorn
print('r mitjà marca %.0f, entorn %.0f ; fracció de la marca amb κ<0,5: %.2f'%(rr[m6].mean(),rr[e6].mean(),(kap[m6]<0.5).mean()))
# mapa σ12 en ln relatiu a la mediana del disc, retall 700 al voltant de la marca: RAWs | f⁻¹(P) | lin′ | f(lin′) | capa74
from PIL import Image
y0,x0=1157-230,828-230; sl=(slice(y0,y0+700),slice(x0,x0+700))
def tile(A,scale):
    a=s12(A); a=np.log(np.maximum(a,1))-np.log(np.median(a[disc])); return np.clip(0.5+a/(2*scale),0,1)[sl]*disc[sl]
pan=np.concatenate([tile(RAWs,0.01),tile(lin,0.01),tile(linp,0.01),tile(fl,0.1),tile(candB,0.1),tile(G74,0.1)],1)
Image.fromarray(np.uint8(pan*255)).save(S4+'/v_fb9_debug_s12.png'); print('fet')
