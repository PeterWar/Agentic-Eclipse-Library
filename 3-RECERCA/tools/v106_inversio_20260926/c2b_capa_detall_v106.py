"""c2b (V106, Claude, 26-09-2026) · Capa «Detall arran del limbe · V106»: el mateix mètode que la c2 de la V105 (vegeu-la: F = 0,5 + g·δ, guany per
dèficit d'energia respecte de just a fora del forat dels filtres, porta de fiabilitat absoluta ρ, mitjana zero per arc i ponderada pel compost), amb
ENTRADES I SORTIDES PARAMETRITZADES per a la V106:
  · V106_DELTA = el npz del detall tangencial (format DELTA_sigc32: delta, pes, dgrid, nth, centre, h125/p125, hcurts/pcurts);
  · V106_OUT = carpeta de sortida (dins de 4-RESULTATS/v106_inversio_20260926/);
  · V105_ESTAT = l'estat de sota (per defecte el de la V105: la 56 amb la cura de la filera);
  · argv[1] = JSON amb canvis de cfg (p. ex. GATE_PA).
Sortides: CAPA_F.npy, GUANY.npz, INFORME.json, COMP_V105_emul.npy (la V105 real, de referència), COMP_SENSE_CAPA_emul.npy, COMP_V106_emul.npy."""
import sys, os, json, numpy as np, cv2
from pathlib import Path
from scipy.ndimage import gaussian_filter1d, gaussian_filter
R0 = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(R0 / '3-RECERCA/tools/v97_refundacio_20260924'))
from jutge_comu import Estat, comp
SIGC = os.environ.get('SIGC', '32'); TAG = ''
z = np.load(R0 / os.environ['V106_DELTA']); D = z['delta']; P = z['pes']; dgrid = z['dgrid']; nth = int(z['nth']); cx, cy, R = z['centre']
th = np.linspace(0, 2 * np.pi, nth, endpoint=False)
box = (4677, 3077, 6077, 4477); bx0, by0 = box[:2]
X = (cx + np.cos(th)[None, :] * (R + dgrid[:, None]) - bx0).astype(np.float32); Y = (cy - np.sin(th)[None, :] * (R + dgrid[:, None]) - by0).astype(np.float32)
def pol(a): return cv2.remap(np.ascontiguousarray(a, np.float32), X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
def hp(Lp):
    l = np.log(np.maximum(Lp, 1e-4)); return gaussian_filter1d(l, 2.0, axis=1, mode='wrap') - gaussian_filter1d(l, 2 * float(SIGC), axis=1, mode='wrap')
O = R0 / os.environ['V106_OUT']; assert '4-RESULTATS/v106_inversio_20260926/' in str(O); O.mkdir(parents=True, exist_ok=True)
cfg=dict(SIG_TH=118.0, GMAX=2.0, CLIP=0.15, FOSA=1.5, ZM_SIG=128.0, DEF0=0.2, DEF1=0.4, TMAX=1.5, DMAX=12.0, RHO0=0.35, RHO1=0.80, LLUNA_K=1.0, GATE_PA=[[0,-10],[185,-10],[195,2.5],[295,2.5],[305,-10]])
if len(sys.argv)>1: cfg.update(json.loads(sys.argv[1]))
SIG_TH=cfg['SIG_TH']
z2=z; A=np.nan_to_num(z2['h125']); B=np.nan_to_num(z2['hcurts']); pa=z2['p125']; pb=z2['pcurts']
Dm=gaussian_filter1d(D,1.0,axis=1,mode='wrap')
ESTAT=os.environ.get('V105_ESTAT','4-RESULTATS/v105_limbe_20260926/claude/estat_v105')   # la V105: 4-RESULTATS/v105_limbe_20260926/claude/estat_v105 (56 amb la cura de la filera)
S=Estat(R0/ESTAT); Pl=S.pila(box=box,fins_a=258)
C0,_=comp([(m,F,a) for _,m,F,a in Pl],1400,1400); L0=(C0[...,0]+2*C0[...,1]+C0[...,2])/4; H0=hp(pol(L0))
def lm(x,w,s=SIG_TH): return gaussian_filter1d(x*w,s,axis=1,mode='wrap')/np.maximum(gaussian_filter1d(w,s,axis=1,mode='wrap'),1e-12)
w=(P>0).astype(np.float64)
mx=lm(Dm,w); my=lm(H0,w); vx=lm(Dm*Dm,w)-mx*mx; cxy=lm(Dm*H0,w)-mx*my
tau0=cxy/np.maximum(vx,1e-12); rms_d=np.sqrt(np.maximum(vx,0))
wab=((pa>0)&(pb>0)).astype(np.float64); ma=lm(A,wab); mb=lm(B,wab)
rho=(lm(A*B,wab)-ma*mb)/np.sqrt(np.maximum((lm(A*A,wab)-ma*ma)*(lm(B*B,wab)-mb*mb),1e-20)); rho=np.where(gaussian_filter1d(wab,SIG_TH,axis=1,mode='wrap')>0.3,rho,0)
sb=np.clip(2*rho/(1+np.maximum(rho,0)),0,1)
# d_ple(θ): on l'alfa de la 56 (sense opacitat) arriba al 95 %
a56=[a for l,m,F,a in Pl if l==56][0]/ (S.capes[56]['opacitat']/255.0)
A56=pol(a56); ok56=A56>=0.95
dple=np.array([dgrid[np.argmax(ok56[:,j])] if ok56[:,j].any() else 40.0 for j in range(nth)])
dple=gaussian_filter1d(dple,SIG_TH/4,mode='wrap')
Dg=dgrid[:,None]
ref=(Dg>=dple[None,:])&(Dg<=dple[None,:]+2)
def refmed(q):
    v=np.where(ref,q,np.nan); m=np.nanmedian(v,axis=0); return gaussian_filter1d(np.nan_to_num(m,nan=np.nanmedian(m)),SIG_TH,mode='wrap')
tau_ref=refmed(tau0); rms_ref=refmed(rms_d); sb_ref=refmed(sb)
# porta de fiabilitat ABSOLUTA (verificador, 26-09): ρ entre grups independents; el p95 dels nuls (grups girats o desplaçats) és 0,12–0,30
xr=np.clip((rho-cfg['RHO0'])/(cfg['RHO1']-cfg['RHO0']),0,1); rel=xr*xr*(3-2*xr)
tau_t=tau_ref[None,:]*rel*cfg['TMAX']   # t9: sense sostre d'amplitud per rms de δ; l'objectiu d'ENERGIA ja limita l'amplitud del compost
x=np.clip((dple[None,:]+cfg['FOSA']-Dg)/cfg['FOSA'],0,1); forat=x*x*(3-2*x)
xm=np.clip((cfg['DMAX']-Dg)/2.0,0,1); forat=forat*xm*xm*(3-2*xm)
# porta radial per sector (jutge Brno i prova Lluna/corona, 26-09): a 195–295° el detall de d < 2,5 px no és corona demostrada → la capa hi actua des de d_min + 0…1 px
_gp=np.array(cfg['GATE_PA'],np.float64); _o=np.argsort(_gp[:,0]); dmin_pa=np.interp(np.degrees(th)%360,_gp[_o,0],_gp[_o,1],period=360)[None,:]
xg=np.clip(Dg-dmin_pa,0,1); forat=forat*xg*xg*(3-2*xg)   # només arran del limbe: fosa de DMAX−2 a DMAX px (la protuberància gran no hi entra)          # 1 dins del forat, 0 a d ≥ d_ple+FOSA
vy0=np.maximum(lm(H0*H0,w)-my*my,0)                      # energia del detall del compost (per sota de la Lluna)
rmsc_ref=refmed(np.sqrt(vy0))
E_t=(rmsc_ref[None,:]*rel)**2                             # energia objectiu: la de just a fora del forat × fiabilitat
t0p=np.maximum(tau0,0); vxx=np.maximum(vx,1e-12)
tau_E=np.where(E_t>vy0,-t0p+np.sqrt(t0p**2+np.maximum(E_t-vy0,0)/vxx),0)   # τ afegida perquè l'energia arribi a l'objectiu
deficit=1-np.sqrt(vy0)/np.maximum(rmsc_ref[None,:],1e-6)      # dèficit d'energia de textura respecte de just a fora del forat
xd=np.clip((deficit-cfg['DEF0'])/(cfg['DEF1']-cfg['DEF0']),0,1); wdef=gaussian_filter(xd*xd*(3-2*xd),(1.0,SIG_TH/4),mode=('nearest','wrap'))
falta=np.minimum(tau_E,np.clip(tau_t-t0p,0,None))*forat*wdef
yy,xx=np.mgrid[box[1]:box[3],box[0]:box[2]]; rC=np.hypot(xx-cx,yy-cy)-R; tC=(np.arctan2(-(yy-cy),xx-cx))%(2*np.pi)
FI=((rC-dgrid[0])/(dgrid[1]-dgrid[0])).astype(np.float32); FJ=(tC/(2*np.pi)*nth).astype(np.float32)
def canvas(p): return cv2.remap(np.concatenate([p,p[:,:1]],1).astype(np.float32),FJ,FI,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=0)
idx=[i for i,(l,_,_,_) in enumerate(Pl) if l==56][0]
def compost_amb(Fl, fins_moon=True):
    lay=[(m,F,a) for _,m,F,a in Pl]; lay.insert(idx+1,('OVERLAY',Fl,np.ones(Fl.shape,np.float32))); C,_=comp(lay,1400,1400); return C
C1=compost_amb((0.5+canvas(np.where(P>0,Dm,0))).astype(np.float32)); L1=(C1[...,0]+2*C1[...,1]+C1[...,2])/4; H1=hp(pol(L1))
s1=(lm(Dm*(H1-H0),w)-mx*lm(H1-H0,w))/np.maximum(vx,1e-12); s1=np.clip(gaussian_filter(s1,(2,SIG_TH/4),mode=('nearest','wrap')),0.3,None)
g=np.clip(falta/s1,0,cfg['GMAX']); g=gaussian_filter(g,(1.0,SIG_TH/8),mode=('nearest','wrap')); g=np.where(P>0,g,0)
a258=pol(S.alfa_efectiva(258,box)); g=g*np.clip(1-a258,0,1)**cfg['LLUNA_K']   # sota la vora translúcida de la Lluna de Pere, menys guany (verificador: fuita a 210° i 270°)
Fp=np.clip(np.where(P>0,g*Dm,0),-cfg['CLIP'],cfg['CLIP'])
wz=(g>1e-4).astype(np.float64)
for _ in range(2):   # mitjana local zero imposada (al llarg de l'arc) on la capa actua
    Fp=np.where(wz>0,Fp-lm(Fp,wz,cfg['ZM_SIG']),0); Fp=np.clip(Fp,-cfg['CLIP'],cfg['CLIP'])
# t11: mitjana zero PONDERADA pel compost de sota (Superposar: ΔC ≈ 2·C·(F−0,5) als canals < 0,5): Σ C·(F−0,5) = 0 localment → nivell mitjà intacte
Lb=pol(L0)
for _ in range(3):
    Fp=np.where(wz>0,Fp-lm(Lb*Fp,wz,cfg['ZM_SIG'])/np.maximum(lm(Lb,wz,cfg['ZM_SIG']),1e-6),0); Fp=np.clip(Fp,-cfg['CLIP'],cfg['CLIP'])
Fl=(0.5+canvas(Fp)).astype(np.float32)
# mitjana zero també en PÍXELS DEL LLENÇ (el pas polar→llenç en deixava +0,1…+0,4 % a dalt, d 0–2; verificador)
act=np.abs(Fl-0.5)>1e-7
for _ in range(2):
    q=pol(np.where(act,Fl-0.5,0)); wq=pol(act.astype(np.float32))
    mq=gaussian_filter1d(q,cfg['ZM_SIG'],axis=1,mode='wrap')/np.maximum(gaussian_filter1d(wq,cfg['ZM_SIG'],axis=1,mode='wrap'),1e-6)
    Fl=np.where(act,Fl-canvas(np.where(wq>0.5,mq,0)),0.5).astype(np.float32)
np.save(O/'CAPA_F.npy',Fl); np.savez_compressed(O/'GUANY.npz',g=g.astype(np.float32),wdef=wdef.astype(np.float32),falta=falta.astype(np.float32),tau0=tau0.astype(np.float32),tau_t=tau_t.astype(np.float32),rho=rho.astype(np.float32),s1=s1.astype(np.float32),dple=dple,tau_ref=tau_ref,rms_ref=rms_ref,cfg=json.dumps(cfg))
C2=compost_amb(Fl); L2=(C2[...,0]+2*C2[...,1]+C2[...,2])/4; H2=hp(pol(L2))
# compost complet (amb la Lluna i les capes de Pere) per a les vistes
Pf=S.pila(box=box,fins_a=234); lay=[(m,F,a) for _,m,F,a in Pf]; i56=[i for i,(l,_,_,_) in enumerate(Pf) if l==56][0]
CF0,_=comp(lay,1400,1400); lay.insert(i56+1,('OVERLAY',Fl,np.ones(Fl.shape,np.float32))); CF1,_=comp(lay,1400,1400)
CF0r=np.load(R0/'4-RESULTATS/v105_limbe_20260926/claude/capa_pa/COMP_V105_emul.npy')   # la V105 lliurada (capa 305), emulada
np.save(O/'COMP_V105_emul.npy',CF0r); np.save(O/'COMP_SENSE_CAPA_emul.npy',CF0); np.save(O/'COMP_V106_emul.npy',CF1)
CF0=CF0r   # el nivell per arc de l'informe es compara amb la V105
dth=np.degrees(th); rep={'cfg':cfg,'sectors':{}}
Lc0=(CF0[...,0]+2*CF0[...,1]+CF0[...,2])/4; Lc1=(CF1[...,0]+2*CF1[...,1]+CF1[...,2])/4; M0=pol(Lc0); M1=pol(Lc1)
for nm,(lo,hi) in {'dalt':(70,110),'dalt-esq':(120,150),'esq':(150,210),'baix-esq':(210,240),'baix':(240,290),'dreta':(330,390)}.items():
    t=dth.copy()
    if hi>360: t[t<lo]+=360
    s=(t>=lo)&(t<hi); rows=[]
    print(f'## {nm} d_ple~{np.median(dple[s]):.2f} τref {np.median(tau_ref[s]):.2f} | d | ρ  τ_t τ0→τ | rms H sense capa→V106 | g | arcmean ΔL/L V106/V105')
    for i,dd in enumerate(dgrid):
        if dd<-2 or dd>10 or (dd*4)%2: continue
        ok=s&(P[i]>0)
        if ok.sum()<100: continue
        xx_=Dm[i][ok]
        def tau(Hh): c=np.cov(xx_,Hh[i][ok]); return c[0,1]/c[0,0]
        dl=np.mean(M1[i][s])/np.mean(M0[i][s])-1
        rows.append(dict(d=float(dd),rho=float(np.median(rho[i][ok])),tau_t=float(np.median(tau_t[i][ok])),tau_v104=float(tau(H0)),tau_v105=float(tau(H2)),rms_v104=float(np.std(H0[i][ok])),rms_v105=float(np.std(H2[i][ok])),g=float(np.median(g[i][ok])),arcmean_rel=float(dl)))
        print(f'  {dd:5.2f} | {rows[-1]["rho"]:.2f} {rows[-1]["tau_t"]:.2f} {rows[-1]["tau_v104"]:.2f}→{rows[-1]["tau_v105"]:.2f} | {rows[-1]["rms_v104"]:.4f}→{rows[-1]["rms_v105"]:.4f} | {rows[-1]["g"]:.2f} | {dl*100:+.2f} %')
    rep['sectors'][nm]=rows
(O/'INFORME.json').write_text(json.dumps(rep,indent=1))
