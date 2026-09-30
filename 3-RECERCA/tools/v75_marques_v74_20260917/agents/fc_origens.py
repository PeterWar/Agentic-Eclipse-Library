"""fc: perfils de les capes d'ORIGEN al voltant del limbe de dalt, i limbe fotografiat (RAW Vixen, fotos de Pere)."""
import json, importlib.util, numpy as np, os
S4='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/e4f0fbff-bfdf-4da5-a1d0-1bbdf0423383/scratchpad'
NEW='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/6346f583-afd0-49da-9c17-95128c31820e/scratchpad'
OLD='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'
Y,X=np.mgrid[0:2000,0:2000]; rr=np.hypot(X-998.88,Y-998.41); az=(np.degrees(np.arctan2(-(Y-998.41),X-998.88)))%360
M=np.array([[0.5767,0.1856,0.1882],[0.2974,0.6273,0.0753],[0.0270,0.0707,0.9911]],np.float32); WN=np.array([0.9505,1,1.089],np.float32)
def Lstar(C):
    lin=np.clip(C,0,1)**2.2; y=(lin@M.T)[...,1]; f=np.where(y>0.008856,np.cbrt(y),7.787*y+16/116); return 116*f-16
RB=np.arange(440,471)
def perfil(img,a0,a1):
    s=(az>=a0)&(az<a1); return np.array([np.median(img[s&(rr>=r0)&(rr<r0+1)]) for r0 in RB[:-1]])
def creua(p,v,rb=RB[:-1]+0.5,desc=True):
    for i in range(len(p)-1):
        if (desc and p[i]>=v>p[i+1]) or ((not desc) and p[i]<v<=p[i+1]): return float(rb[i]+(v-p[i])/(p[i+1]-p[i]))
    return None
def capa(ruta):
    d=np.load(ruta); rgb=np.dstack([d['c0'],d['c1'],d['c2']]).astype(np.float32)/65535
    return rgb,d['c-1'].astype(np.float32)/65535,(d['c-2'].astype(np.float32)/65535 if 'c-2' in d else None)
SECT=[(60,65),(70,75),(85,90),(95,100),(100,105),(105,110),(115,120),(120,125),(0,5),(15,20),(300,305),(315,320)]
out={}
b3,a3,m3=capa(S4+'/roi74p_L3.npz'); b3_71,a3_71,m3_71=capa(NEW+'/roi71_L3.npz')
c30,a30,m30=capa(S4+'/roi74p_L30.npz'); c30_71,a30_71,m30_71=capa(NEW+'/roi71_L30.npz')
print('capa30 V74==V71 rgb:',np.array_equal(c30,c30_71),'alfa:',np.array_equal(a30,a30_71),'mask:',np.array_equal(m30,m30_71))
c57,a57,m57=capa(NEW+'/roi71_L57.npz')
fotos={k:capa(S4+f'/roi74p_L{k}.npz') for k in (76,96,204,206)}
raw=np.load(OLD+'/raw_disc_norm_2000.npy') if os.path.exists(OLD+'/raw_disc_norm_2000.npy') else None
print('raw',None if raw is None else (raw.shape,raw.dtype,float(np.nanmin(raw)),float(np.nanmax(raw))))
L3=Lstar(b3); L3_71=Lstar(b3_71); L30=Lstar(c30); L57=Lstar(c57); Lf={k:Lstar(v[0]) for k,v in fotos.items()}
for a0,a1 in SECT:
    k=f'{a0}-{a1}'; e={}
    e['base3_L']=perfil(L3,a0,a1).round(2).tolist(); e['base3_alfa']=perfil(a3*(m3 if m3 is not None else 1),a0,a1).round(3).tolist()
    e['base3_V71_L']=perfil(L3_71,a0,a1).round(2).tolist(); e['base3_V71_alfa']=perfil(a3_71*(m3_71 if m3_71 is not None else 1),a0,a1).round(3).tolist()
    e['capa30_L']=perfil(L30,a0,a1).round(2).tolist(); e['capa30_alfa_propia']=perfil(a30,a0,a1).round(3).tolist(); e['capa30_mask']=perfil(m30,a0,a1).round(3).tolist()
    e['capa30_alfa_ef']=perfil(a30*m30,a0,a1).round(3).tolist()
    e['powaaah57_L']=perfil(L57,a0,a1).round(2).tolist(); e['powaaah57_alfa']=perfil(a57*(m57 if m57 is not None else 1),a0,a1).round(3).tolist()
    for kk,(rgb,al,mk) in fotos.items():
        e[f'foto{kk}_L']=perfil(Lf[kk],a0,a1).round(2).tolist(); e[f'foto{kk}_alfa_ef']=perfil(al*(mk if mk is not None else 1),a0,a1).round(3).tolist()
        p=perfil(Lf[kk],a0,a1); lo=np.median(p[:6]); hi=np.median(p[-6:]); e[f'foto{kk}_limbe50']=creua(p,(lo+hi)/2,desc=False) if hi>lo+5 else None
    if raw is not None:
        p=perfil(raw,a0,a1); e['raw_disc_prof']=p.round(4).tolist(); lo=np.median(p[:6]); hi=np.median(p[-6:]); e['raw_limbe50']=creua(p,(lo+hi)/2,desc=False)
        e['raw_limbe10_90']=[creua(p,lo+0.1*(hi-lo),desc=False),creua(p,lo+0.9*(hi-lo),desc=False)]
    e['base3_alfa_50']=creua(np.array(e['base3_alfa']),0.5); e['capa30_mask_50']=creua(np.array(e['capa30_mask']),0.5); e['powaaah57_alfa_50']=creua(np.array(e['powaaah57_alfa']),0.5)
    out[k]=e
json.dump({'r_bins':RB[:-1].tolist(),'sectors':out},open(S4+'/fc_origens.json','w'),indent=1)
for k,e in out.items():
    print(f"\n== az {k}: base3 alfa50={e['base3_alfa_50']}  mask30 50={e['capa30_mask_50']}  57 alfa50={e['powaaah57_alfa_50']}  raw limbe50={e.get('raw_limbe50')} 10-90={e.get('raw_limbe10_90')}  fotos limbe50: "+', '.join(f'{kk}={e[f"foto{kk}_limbe50"]}' for kk in fotos))
    print(' r   base3L a3   |b3V71L a3V71| c30L a30 m30 | 57L a57 | 96L a96 | 206L a206 | raw')
    for i,rb in enumerate(RB[:-1]):
        if 444<=rb<=462: print(f"{rb} {e['base3_L'][i]:6.1f} {e['base3_alfa'][i]:.2f} |{e['base3_V71_L'][i]:6.1f} {e['base3_V71_alfa'][i]:.2f}| {e['capa30_L'][i]:5.1f} {e['capa30_alfa_propia'][i]:.2f} {e['capa30_mask'][i]:.2f} | {e['powaaah57_L'][i]:5.1f} {e['powaaah57_alfa'][i]:.2f} | {e['foto96_L'][i]:5.1f} {e['foto96_alfa_ef'][i]:.2f} | {e['foto206_L'][i]:5.1f} {e['foto206_alfa_ef'][i]:.2f} | {e['raw_disc_prof'][i] if raw is not None else ''}")
