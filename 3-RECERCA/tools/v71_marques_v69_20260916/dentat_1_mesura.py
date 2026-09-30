"""dentat_1: índex de dentat de la vora lunar (radi 50 % del trànsit Lluna→corona en lluminància, 1440 azimuts) a V69, V70 i variants acumulatives/aïllades; alfa efectiva de la capa 76 v70 al limbe."""
import sys, json, numpy as np
SP='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'
sys.path.insert(0,SP)
import compo; from compo import recompon, LAYERS
from scipy.ndimage import map_coordinates, gaussian_filter1d, minimum_filter, maximum_filter
CX,CY,RS=998.88,998.41,456.0
TH=np.deg2rad(np.arange(0,360,0.25)); THD=np.rad2deg(TH); RR=np.arange(430,480.001,0.25)
SECT=list(range(0,360,10))
def perfils(img):
    xs=CX+RR[None,:]*np.cos(TH[:,None]); ys=CY-RR[None,:]*np.sin(TH[:,None])
    return map_coordinates(img,[ys.ravel(),xs.ravel()],order=1,mode='nearest').reshape(len(TH),len(RR))
def vora50(P):
    lo=np.median(P[:,RR<=440],1); hi=np.median(P[:,RR>=470],1); mid=(lo+hi)/2; out=np.full(len(TH),np.nan)
    for i in range(len(TH)):
        p=P[i]; j=np.nonzero((p[:-1]<mid[i])&(p[1:]>=mid[i]))[0]
        if len(j): k=j[0]; out[i]=RR[k]+(mid[i]-p[k])/(p[k+1]-p[k]+1e-12)*0.25
    ok=np.isfinite(out)
    if (~ok).any(): out[~ok]=np.interp(np.nonzero(~ok)[0],np.nonzero(ok)[0],out[ok],period=len(TH))
    return out,int((~ok).sum())
def index_dentat(v):
    hp=v-gaussian_filter1d(v,4,mode='wrap')   # σ 1° = 4 mostres
    sd=[]; sc=[]
    for s in SECT:
        k=(THD>=s)&(THD<s+10); d=np.diff(v[k]); sg=np.sign(d); sg=sg[sg!=0]
        sd.append(float(hp[k].std())); sc.append(int((np.diff(sg)!=0).sum()))
    return dict(hp_std_global=float(hp.std()),hp_p95=float(np.percentile(np.abs(hp),95)),std_sector=sd,canvis_signe_sector=sc,r_mediana=float(np.median(v)),hp=hp)
def mesura(C,a):
    L=(C*a[...,None]).mean(-1); v,nan=vora50(perfils(L)); r=index_dentat(v); r['vora']=v; r['sense_creuament']=nan; return r
res={}; vores={}
# 1) compost V69 (recomposició) i V70 (compost desat)
R69=np.load(SP+'/roi_recomp.npz'); C69=R69['C'].astype(np.float32)/65535; a69=R69['a'].astype(np.float32)/65535
R70=np.load(SP+'/roi_compost_v70.npz'); C70=R70['C'].astype(np.float32)/65535; a70=R70['a'].astype(np.float32)/65535
res['V69']=mesura(C69,a69); res['V70']=mesura(C70,a70)
# 2) variants
FIL=(47,49,51,53,55,56); NRGF=(41,42,45,46)
variants={'a_filtres':FIL,'b_+nrgf':FIL+NRGF,'c_+30':FIL+NRGF+(30,),'d_+3':FIL+NRGF+(30,3),'e_+76(=V70)':FIL+NRGF+(30,3,76),
          'nomes_30':(30,),'nomes_3':(3,),'nomes_76':(76,),'nomes_30+3':(30,3),'nomes_nrgf':NRGF}
comps={}
for nom,ids in variants.items():
    compo.OVERRIDE.clear()
    for lid in ids: compo.OVERRIDE[lid]=SP+f'/roi_L{lid}_v70.npz'
    C,a=recompon(); res[nom]=mesura(C,a); comps[nom]=(C,a)
    print(nom,'fet; hp std global %.3f'%res[nom]['hp_std_global'],flush=True)
compo.OVERRIDE.clear()
# comprovació: la variant e reprodueix el compost V70 desat?
Ce,ae=comps['e_+76(=V70)']; print('variant e vs roi_compost_v70: max |dif| DN16 = %.1f'%(np.abs(Ce-C70).max()*65535))
np.savez_compressed(SP+'/dentat_comps.npz',C69=(np.clip(C69,0,1)*65535+.5).astype(np.uint16),a69=(a69*65535+.5).astype(np.uint16),
    Cc=(np.clip(comps['c_+30'][0],0,1)*65535+.5).astype(np.uint16),ac=(comps['c_+30'][1]*65535+.5).astype(np.uint16),
    C30=(np.clip(comps['nomes_30'][0],0,1)*65535+.5).astype(np.uint16),a30=(comps['nomes_30'][1]*65535+.5).astype(np.uint16),
    C76=(np.clip(comps['nomes_76'][0],0,1)*65535+.5).astype(np.uint16),a76=(comps['nomes_76'][1]*65535+.5).astype(np.uint16))
# taules
ordre=['V69','V70','a_filtres','b_+nrgf','c_+30','d_+3','e_+76(=V70)','nomes_30','nomes_3','nomes_76','nomes_30+3','nomes_nrgf']
print('\nGLOBAL: hp std (px) · p95 |hp| · r mediana · canvis de signe totals · azimuts sense creuament')
for k in ordre:
    r=res[k]; print(f'{k:14s} {r["hp_std_global"]:.3f}  {r["hp_p95"]:.3f}  {r["r_mediana"]:.2f}  {sum(r["canvis_signe_sector"]):4d}  {r["sense_creuament"]}')
print('\nÍNDEX DE DENTAT (std del passa-alt, px) per sector de 10°:')
print('sector  '+''.join(f'{k[:11]:>12s}' for k in ordre))
for i,s in enumerate(SECT):
    print(f'{s:3d}–{s+10:3d} '+''.join(f'{res[k]["std_sector"][i]:12.3f}' for k in ordre))
print('\nCANVIS DE SIGNE DEL PENDENT per sector (40 mostres/sector):')
print('sector  '+''.join(f'{k[:11]:>12s}' for k in ordre))
for i,s in enumerate(SECT):
    print(f'{s:3d}–{s+10:3d} '+''.join(f'{res[k]["canvis_signe_sector"][i]:12d}' for k in ordre))
print('\nRADI MEDIÀ de la vora per sector:')
print('sector  '+''.join(f'{k[:11]:>12s}' for k in ordre))
for i,s in enumerate(SECT):
    k=(THD>=s)&(THD<s+10); print(f'{s:3d}–{s+10:3d} '+''.join(f'{np.median(res[q]["vora"][k]):12.2f}' for q in ordre))
# 4) alfa efectiva de la capa 76 v70 al limbe
d76=np.load(SP+'/roi_L76_v70.npz'); d69=np.load(SP+'/roi_L76.npz'); op=LAYERS[76]['opacity']
print('\ncapa 76: opacitat a l\'índex =',op,'(la tasca diu 227/255; calculo amb 227/255 i amb la de l\'índex)')
yy,xx=np.mgrid[0:2000,0:2000]; rr=np.hypot(xx-CX,yy-CY); az=np.rad2deg(np.arctan2(-(yy-CY),xx-CX))%360
alfa={}
for nom,dd in (('v70',d76),('v69',d69)):
    alfa[nom]=dd['c-1'].astype(np.float32)/65535*dd['c-2'].astype(np.float32)/65535
band=(rr>=RS)&(rr<RS+6)
mn=minimum_filter(alfa['v70']*227/255,3); mx=maximum_filter(alfa['v70']*227/255,3); brusc=(mn<0.1)&(mx>0.5)
mn2=minimum_filter(alfa['v70']*op/255,3); mx2=maximum_filter(alfa['v70']*op/255,3); brusc2=(mn2<0.1)&(mx2>0.5)
mn9=minimum_filter(alfa['v69']*227/255,3); mx9=maximum_filter(alfa['v69']*227/255,3); brusc9=(mn9<0.1)&(mx9>0.5)
print('fracció de la corona a d 0–6 px on l\'alfa 76 passa de <0,1 a >0,5 en <3 px (finestra 3×3), per sector:')
print('sector   v70(227)  v70(idx)  v69(227)   alfa76 mitjana v70 | v69   fracció alfa>0,5 v70 | v69')
tab4=[]
for s in SECT:
    k=band&(az>=s)&(az<s+10); n=k.sum()
    row=(s,float(brusc[k].mean()),float(brusc2[k].mean()),float(brusc9[k].mean()),float((alfa['v70']*227/255)[k].mean()),float((alfa['v69']*227/255)[k].mean()),float(((alfa['v70']*227/255)[k]>0.5).mean()),float(((alfa['v69']*227/255)[k]>0.5).mean()))
    tab4.append(row); print(f'{s:3d}–{s+10:3d}  {row[1]:8.3f}  {row[2]:8.3f}  {row[3]:8.3f}     {row[4]:6.3f} | {row[5]:6.3f}        {row[6]:6.3f} | {row[7]:6.3f}')
print('global: brusc v70 %.3f · v69 %.3f'%(brusc[band].mean(),brusc9[band].mean()))
# continuïtat al llarg del limbe: alfa 76 a d=2 px vs azimut: trossos (runs) per sobre de 0,3
def runs(a2,llindar=0.3):
    on=a2>llindar; ch=np.nonzero(np.diff(on.astype(int)))[0]; return int(len(ch)), float(on.mean())
for dpx in (1,2,4):
    xs=CX+(RS+dpx)*np.cos(TH); ys=CY-(RS+dpx)*np.sin(TH)
    a2=map_coordinates(alfa['v70']*227/255,[ys,xs],order=1); a9=map_coordinates(alfa['v69']*227/255,[ys,xs],order=1)
    print(f'd={dpx} px: v70 → {runs(a2)[0]} transicions (fracció ON {runs(a2)[1]:.3f}); v69 → {runs(a9)[0]} transicions (fracció ON {runs(a9)[1]:.3f})')
# on és la silueta pròpia de la capa 76 (lluminància RGB) i la de la 30, on tenen alfa: la vora del compost salta entre les dues?
def vora_capa(dd):
    rgb=np.dstack([dd['c0'],dd['c1'],dd['c2']]).astype(np.float32)/65535; return vora50(perfils(rgb.mean(-1)))[0]
v76=vora_capa(d76); v30=vora_capa(np.load(SP+'/roi_L30_v70.npz')); v3=vora_capa(np.load(SP+'/roi_L3_v70.npz'))
xs=CX+(RS+2)*np.cos(TH); ys=CY-(RS+2)*np.sin(TH); a76_2=map_coordinates(alfa['v70']*227/255,[ys,xs],order=1)
print('\nsilueta pròpia (50 % lluminància) per sector: capa 76 | capa 30 | base 3 | compost V69 | compost V70 ; alfa76(d=2) mitjana')
for s in SECT:
    k=(THD>=s)&(THD<s+10); print(f'{s:3d}–{s+10:3d}  {np.median(v76[k]):7.2f} {np.median(v30[k]):7.2f} {np.median(v3[k]):7.2f}  {np.median(res["V69"]["vora"][k]):7.2f} {np.median(res["V70"]["vora"][k]):7.2f}   {a76_2[k].mean():.3f}')
# correlació: el dentat de V70 segueix l'alfa 76? (hp de V70 vs a76 a d=2)
hp70=res['V70']['hp']; hp69=res['V69']['hp']; print('\ncorr(|hp V70|, alfa76 d=2) = %.3f ; corr(hp V70, alfa76 d=2) = %.3f ; corr(hp V70, hp V69) = %.3f'%(np.corrcoef(np.abs(hp70),a76_2)[0,1],np.corrcoef(hp70,a76_2)[0,1],np.corrcoef(hp70,hp69)[0,1]))
hpe=res['nomes_76']['hp']; hpc=res['nomes_30']['hp']; print('corr(hp V70, hp nomes_76) = %.3f ; corr(hp V70, hp nomes_30) = %.3f ; corr(hp V70, hp c_+30) = %.3f'%(np.corrcoef(hp70,hpe)[0,1],np.corrcoef(hp70,hpc)[0,1],np.corrcoef(hp70,res['c_+30']['hp'])[0,1]))
out={k:{kk:(vv.tolist() if isinstance(vv,np.ndarray) else vv) for kk,vv in v.items()} for k,v in res.items()}
out['alfa76_sectors']=tab4; out['silueta']=dict(v76=v76.tolist(),v30=v30.tolist(),v3=v3.tolist())
json.dump(out,open(SP+'/dentat_resultats.json','w'))
print('desat dentat_resultats.json i dentat_comps.npz')
