"""dentat_2: mecanisme: la màscara de la capa 30 v70 = farcit a 1 dins del cercle booleà rr<453 (sense antialiàs) → graó 1→M30(r) a r=453 allà on la màscara de Pere ja era <1."""
import sys, json, numpy as np
SP='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'
from scipy.ndimage import map_coordinates
CX,CY,RS=998.88,998.41,456.0
yy,xx=np.mgrid[0:2000,0:2000]; rr=np.hypot(xx-CX,yy-CY); az=np.rad2deg(np.arctan2(-(yy-CY),xx-CX))%360
d69=np.load(SP+'/roi_L30.npz'); d70=np.load(SP+'/roi_L30_v70.npz')
A=d69['c-1'].astype(np.float32)/65535; M69=d69['c-2'].astype(np.float32)/65535; M70=d70['c-2'].astype(np.float32)/65535
E69=A*M69; E70=A*M70
print('alfa 30 (c-1) ≥0,999 fins a r =',round(float(rr[A>=0.999].max()),2),'; píxels canviats a la màscara:',int((np.abs(M70-M69)>1/65535).sum()))
# perfil radial de la màscara (mediana per sector) a r 449..458 pas 0,5
R=np.arange(449,458.01,0.5); TH=np.deg2rad(np.arange(0,360,0.25)); THD=np.rad2deg(TH)
def pol(img):
    xs=CX+R[None,:]*np.cos(TH[:,None]); ys=CY-R[None,:]*np.sin(TH[:,None]); return map_coordinates(img,[ys.ravel(),xs.ravel()],order=1).reshape(len(TH),len(R))
P69=pol(E69); P70=pol(E70)
print('\nalfa efectiva de la capa 30 (mediana per sector) a r = '+' '.join(f'{r:5.1f}' for r in R[::2]))
print('           V69 → V70 ; salt màxim |ΔE70| entre píxels veïns radials a r 452–454 (V69 | V70)')
# salt entre veïns: gradient radial discret al voltant de 453
from scipy.ndimage import sobel
g69=np.hypot(sobel(E69,0),sobel(E69,1))/8; g70=np.hypot(sobel(E70,0),sobel(E70,1))/8
tab=[]
for s in range(0,360,10):
    k=(THD>=s)&(THD<s+10); kp=(az>=s)&(az<s+10)&(rr>452)&(rr<454.5)
    m69=np.median(P69[k],0); m70=np.median(P70[k],0)
    row=dict(sector=s,E69=[round(float(x),3) for x in m69[::2]],E70=[round(float(x),3) for x in m70[::2]],grad_max_69=round(float(g69[kp].max()),3),grad_max_70=round(float(g70[kp].max()),3),grad_p95_69=round(float(np.percentile(g69[kp],95)),3),grad_p95_70=round(float(np.percentile(g70[kp],95)),3),M69_a_453=round(float(np.median(P69[k][:,R==453])),3))
    tab.append(row)
    print(f'{s:3d}–{s+10:3d} V69 '+' '.join(f'{x:5.3f}' for x in m69[::2])+f'   grad p95 {row["grad_p95_69"]:.3f} màx {row["grad_max_69"]:.3f}')
    print(f'        V70 '+' '.join(f'{x:5.3f}' for x in m70[::2])+f'   grad p95 {row["grad_p95_70"]:.3f} màx {row["grad_max_70"]:.3f}')
# el graó: diferència entre el píxel just dins (rr<453) i just fora (453≤rr<454) de la màscara v70, per sector
print('\ngraó a r=453 (mitjana E dins [452,453) − mitjana E fora [453,454)), per sector: V69 | V70')
res=[]
for s in range(0,360,10):
    ki=(az>=s)&(az<s+10)&(rr>=452)&(rr<453); ko=(az>=s)&(az<s+10)&(rr>=453)&(rr<454)
    res.append((s,round(float(E69[ki].mean()-E69[ko].mean()),3),round(float(E70[ki].mean()-E70[ko].mean()),3)))
print(' '.join(f'{s}:{a:+.2f}|{b:+.2f}' for s,a,b in res))
json.dump(dict(perfil=tab,grao=res),open(SP+'/dentat_mascara30.json','w'),indent=0)
