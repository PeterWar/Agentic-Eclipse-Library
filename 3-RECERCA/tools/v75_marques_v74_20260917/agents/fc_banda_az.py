import numpy as np, json
from scipy.ndimage import uniform_filter
S4='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/e4f0fbff-bfdf-4da5-a1d0-1bbdf0423383/scratchpad'
Y,X=np.mgrid[0:2000,0:2000]; rr=np.hypot(X-998.88,Y-998.41); az=(np.degrees(np.arctan2(-(Y-998.41),X-998.88)))%360
M=np.array([[0.5767,0.1856,0.1882],[0.2974,0.6273,0.0753],[0.0270,0.0707,0.9911]],np.float32)
def Lstar(C):
    lin=np.clip(C,0,1)**2.2; y=(lin@M.T)[...,1]; f=np.where(y>0.008856,np.cbrt(y),7.787*y+16/116); return 116*f-16
C74=np.load(S4+'/fc_V74_C.npy'); C71=np.load(S4+'/fc_V71_C.npy'); L74=Lstar(C74); L71=Lstar(C71)
d30=np.load(S4+'/roi74p_L30.npz'); m30=d30['c-2'].astype(np.float32)/65535; c30=np.dstack([d30['c0'],d30['c1'],d30['c2']]).astype(np.float32)/65535; L30=Lstar(c30)
m1=np.load(S4+'/marques74_masks.npz')['m1']
RB=np.arange(436,477); rmid=RB[:-1]+0.5
def perfil(img,a0,a1):
    s=(az>=a0)&(az<a1); return np.array([np.median(img[s&(rr>=r0)&(rr<r0+1)]) for r0 in RB[:-1]])
def creua(p,v,desc=True):
    for i in range(len(p)-1):
        if (desc and p[i]>=v>p[i+1]) or ((not desc) and p[i]<v<=p[i+1]): return float(rmid[i]+(v-p[i])/(p[i+1]-p[i]))
    return None
rows=[]
for a0 in range(0,360,3):
    a1=a0+3; pm=perfil(m30,a0,a1); pL=perfil(L74,a0,a1); pL71=perfil(L71,a0,a1)
    e30=creua(pm,0.5); dl=np.median(pL[(rmid>438)&(rmid<446)]); cl=np.median(pL[(rmid>464)&(rmid<472)]); r50=creua(pL,(dl+cl)/2,desc=False)
    # ressalt a la vora de la màscara: màxim de L* a [e30-1.5,e30+1.5] menys nivell del disc (440-448)
    if e30 is not None:
        w=(rmid>=e30-1.5)&(rmid<=e30+1.5); bump=float(np.max(pL[w])-dl)
        # nivell mig de la banda plana entre e30+1.5 i r50-1.5
        wb=(rmid>=e30+1.5)&(rmid<=r50-1.5) if r50 else np.zeros_like(rmid,bool)
        banda=float(np.median(pL[wb])-dl) if wb.any() else None
    else: bump=None; banda=None
    s=(az>=a0)&(az<a1)
    rows.append(dict(az=a0,vora_mask30=e30,r50_V74=r50,amplada_banda=(None if (e30 is None or r50 is None) else round(r50-e30,2)),ressalt_vora_mask30_dL=bump,banda_plana_dL=banda,m1_px=int((m1&s).sum()),L_disc=float(dl),L_corona=float(cl),
                     r50_V71=creua(pL71,(np.median(pL71[(rmid>438)&(rmid<446)])+np.median(pL71[(rmid>464)&(rmid<472)]))/2,desc=False)))
json.dump(rows,open(S4+'/fc_banda_per_az.json','w'),indent=1)
print(' az  vora30  r50_74  r50_71  ampl  ressalt  banda  m1px')
for r in rows: print(f"{r['az']:3d} {r['vora_mask30'] or 0:7.2f} {r['r50_V74'] or 0:7.2f} {r['r50_V71'] or 0:7.2f} {r['amplada_banda'] or 0:5.2f} {r['ressalt_vora_mask30_dL'] if r['ressalt_vora_mask30_dL'] is not None else 0:6.2f} {r['banda_plana_dL'] if r['banda_plana_dL'] is not None else 0:6.2f} {r['m1_px']:5d}")
# textura: std local 5x5 de L* a la banda plana (r 452-454.5) vs earthshine (r 441-448) per sector de 5° a 60-125 (V74) i el mateix a V71 a 441-448
def std_local(L,k=5):
    m=uniform_filter(L,k); return np.sqrt(np.maximum(uniform_filter(L*L,k)-m*m,0))
s74=std_local(L74); tex={}
for a0 in range(60,125,5):
    s=(az>=a0)&(az<a0+5); tex[f'{a0}-{a0+5}']={'std5_banda_r452-454.5_V74':float(np.median(s74[s&(rr>=452)&(rr<454.5)])),'std5_earthshine_r441-448_V74':float(np.median(s74[s&(rr>=441)&(rr<448)])),
        'std5_capa30_contingut_r452-455':float(np.median(std_local(L30)[s&(rr>=452)&(rr<455)]))}
print(json.dumps(tex,indent=0)[:1500])
# on són les diferències V74-V71 a r>458
d=L74-L71; for_=(rr>=458)&(rr<470)&(np.abs(d)>2)
ys,xs=np.where(for_); print('pixels |dL|>2 a r 458-470:',for_.sum(),'az range',az[for_].min() if for_.any() else None,az[for_].max() if for_.any() else None,'r range',rr[for_].min() if for_.any() else None,rr[for_].max() if for_.any() else None)
# perfils azimutals r458-465
j=json.load(open(S4+'/fc_dif_v74_v71.json'))
print('az: L*(458-465) V71 | V74 | L*(449-453) V71 | V74')
for i,a in enumerate(range(60,125)): print(a, j['az_prof_r458_465_V71'][i], j['az_prof_r458_465_V74'][i],'|', j['az_prof_r449_453_V71'][i], j['az_prof_r449_453_V74'][i])
json.dump(tex,open(S4+'/fc_textura_banda.json','w'),indent=1)
