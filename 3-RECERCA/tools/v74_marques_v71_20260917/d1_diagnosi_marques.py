"""D1 (V74) · Diagnosi de les marques de Pere a la seva V71 (capes 219 i 220) i del TIF «WOW_Bilateral.tif».
Entrades: retalls de la ROI lunar (4377,2777)–(6377,4777) de V71.psb de Pere al scratchpad NEW (roi71_L{id}.npz amb c0,c1,c2,c-1,c-2),
compo71.py (fórmula de composició de Photoshop, verificada contra el V71.tif de Pere: 0,0 DN16 al disc, 2,5 al limbe, 1,4 a la corona, fora de les marques),
raw_disc_norm_2000.npy (disc lunar als RAW Vixen 10 s normalitzat per anells; scratchpad OLD), marques_219/220.npz.
Sortides: taules a stdout. Resultats clau (17-09):
  · El TIF de Pere és exactament el ràster de la capa 56 (corr 0,9999) + les marques 219 pintades.
  · a* de les marques = a* del voltant (cap verd absolut); el «verd» és contrast: marques 1 i 8 = franja clara i groga entre la vora de la
    màscara de Pere (r 451–455, a mà) i la silueta fotografiada (R 456,0), on es veu la ploma clara de POWAAAH3 (57, L 0,9–0,99 a r 447–452,
    hard light) i el farcit agregat de la base (R 0,98 a r 447–456); marques 2–5 i 6 = ploma de les fotos 76/96/204 (ΔL* −2…−4, Δa* −5…−9);
    anell 220 = la mateixa franja.
  · Taca (marca 7): capa 30 −5,3 % contra l'entorn immediat (8–40 px); LROC −0,3 % (no és lunar); el RAW no pot jutjar (l'earthshine hi és
    el 0,36 % del senyal); cap model de vel (vel_G*, vel_Gaz*, vel_corr*) correlaciona amb la mitjana escala de la capa 30 (r ≈ 0); origen =
    envolupant del vel del revelat (estudi 14-09); NO es toca a V74 (cap pedaç cosmètic)."""
import sys, numpy as np
from scipy.ndimage import binary_dilation, gaussian_filter
NEW='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/6346f583-afd0-49da-9c17-95128c31820e/scratchpad'
OLD='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'
sys.path.insert(0,NEW); import os; os.chdir(NEW); import compo71 as c
CX,CY,RS=998.88,998.41,456.0; Y,X=np.mgrid[0:2000,0:2000]; rr=np.hypot(X-CX,Y-CY); az=(np.degrees(np.arctan2(-(Y-CY),X-CX)))%360
def marca(path):
    m=np.load(path); M=np.zeros((2000,2000),np.float32); mx,my=int(m['x0'])-4377,int(m['y0'])-2777; M[my:my+m['A'].shape[0],mx:mx+m['A'].shape[1]]=m['A']/65535; return M
Mk,Mk2=marca('marques_219.npz'),marca('marques_220.npz')
def caixa(x0,y0,x1,y1): m=np.zeros((2000,2000),bool); m[y0-2777:y1-2777,x0-4377:x1-4377]=True; return m&(Mk>0.03)
regs={'1 dalt':caixa(5317,3309,5542,3358),'2-5 oest':caixa(4877,3510,5077,3760),'6 WSW':caixa(4870,3850,5010,3990),'8 SSW':caixa(5060,4080,5180,4200),'7 taca':caixa(5187,3928,5418,4132),'anell 220':(Mk2>0.03)&(rr>456)}
ents={}
for k,m in regs.items():
    yb,xb=np.nonzero(m); rb=np.hypot(xb-CX,yb-CY); e=binary_dilation(m,iterations=40)&~binary_dilation(m,iterations=8)&(rr>=rb.min()-15)&(rr<=rb.max()+15)
    ents[k]=e&((rr>458) if rb.mean()>456 else (rr<454))
def lab(C):
    lin=np.clip(C,0,1)**2.2; M=np.array([[0.5767,0.1856,0.1882],[0.2974,0.6273,0.0753],[0.0270,0.0707,0.9911]]); XYZ=lin@M.T; wn=np.array([0.9505,1.0,1.089]); f=lambda t: np.where(t>0.008856,np.cbrt(t),7.787*t+16/116); fx,fy,fz=f(XYZ[...,0]/wn[0]),f(XYZ[...,1]/wn[1]),f(XYZ[...,2]/wn[2]); return 116*fy-16,500*(fx-fy),200*(fy-fz)
Cb,ab,passos=c.recompon(exclou=(218,219,220),retorna_passos=True)
print('A) marca − entorn immediat (ΔL*, Δa*, Δb*) després de cada capa (de baix a dalt)')
for lid,(C,a) in passos.items():
    Ls,As,Bs=lab(C); print('%-4s %-26s '%(lid,c.LAYERS[lid]['name'][:26])+' '.join('%5.1f %5.1f %5.1f '%(Ls[m].mean()-Ls[ents[k]].mean(),As[m].mean()-As[ents[k]].mean(),Bs[m].mean()-Bs[ents[k]].mean()) for k,m in regs.items()))
print('B) taca: regió contra entorn immediat (8–40 px, dins r<448)')
R7,ent=regs['7 taca'],ents['7 taca']
def L(path): d=np.load(path); return np.dstack([d['c0'],d['c1'],d['c2']]).astype(np.float64).mean(-1)/65535
for nom,A in (('capa 30 V69',L(OLD+'/roi_L30.npz')),('capa 30 V71 Pere',L('roi71_L30.npz')),('LROC (62)',L('roi71_L62.npz')),('RAW disc (normalitzat per anells)',np.load(OLD+'/raw_disc_norm_2000.npy').astype(np.float64))):
    print('  %-34s dins/entorn −1 = %+5.2f %%'%(nom,100*(np.nanmean(A[R7])/np.nanmean(A[ent])-1)))
print('C) capa 56 (WOW bilateral): mediana per anell menys nivell llunyà (biaix d\'anell) 456–620')
d=np.load('roi71_L56.npz'); g=d['c0'].astype(np.float64)/65535; far=np.median(g[(rr>=600)&(rr<900)]); ri=np.round(rr).astype(int)
print('  '+' '.join('%d:%+.3f'%(r,np.median(g[ri==r])-far) for r in range(456,620,16)))
print('D) limbe per sector: vora de la màscara de la capa 30 (r on cau a 0,5), L del contingut no blanc de 57 a 448–452, L* del compost a 452–456 contra 456–462')
d30=np.load('roi71_L30.npz'); m30=d30['c-2'].astype(float)/65535; d57=np.load('roi71_L57.npz'); r57=np.dstack([d57['c0'],d57['c1'],d57['c2']]).astype(np.float64)/65535; white=r57.min(-1)>=0.999
Ls,As,Bs=lab(Cb)
for a0 in range(0,360,30):
    s=(az>=a0)&(az<a0+30); prof=[m30[s&(ri==r)].mean() for r in range(444,462)]; edge=444+int(np.argmax(np.array(prof)<0.5)) if min(prof)<0.5 else 462
    nb=s&(rr>=448)&(rr<452)&~white; print('  az %3d: vora màscara 30 ≈ r %d · 57 no blanc a 448–452: L %.2f (frac %.2f) · compost L* 452–456 %.1f contra 456–462 %.1f'%(a0,edge,r57.mean(-1)[nb].mean() if nb.any() else 0,nb.sum()/max((s&(rr>=448)&(rr<452)).sum(),1),Ls[s&(rr>=452)&(rr<456)].mean(),Ls[s&(rr>=456)&(rr<462)].mean()))
