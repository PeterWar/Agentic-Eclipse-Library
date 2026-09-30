"""Lector C (fc): marca lila m1 al limbe de dalt — perfils, atribució capa a capa, nitidesa, vora de màscares, V71 vs V74."""
import sys, json, importlib.util, numpy as np
S4='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/e4f0fbff-bfdf-4da5-a1d0-1bbdf0423383/scratchpad'
NEW='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/6346f583-afd0-49da-9c17-95128c31820e/scratchpad'
def modul(nom,ruta):
    sp=importlib.util.spec_from_file_location(nom,ruta); m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
c74=modul('compo74',S4+'/compo74.py'); c71=modul('compo71',NEW+'/compo71.py')
Y,X=np.mgrid[0:2000,0:2000]; rr=np.hypot(X-998.88,Y-998.41); az=(np.degrees(np.arctan2(-(Y-998.41),X-998.88)))%360
M=np.array([[0.5767,0.1856,0.1882],[0.2974,0.6273,0.0753],[0.0270,0.0707,0.9911]],np.float32); WN=np.array([0.9505,1,1.089],np.float32)
def lab(C):
    lin=np.clip(C,0,1)**2.2; xyz=lin@M.T; t=xyz/WN
    f=np.where(t>0.008856,np.cbrt(t),7.787*t+16/116)
    return np.stack([116*f[...,1]-16,500*(f[...,0]-f[...,1]),200*(f[...,1]-f[...,2])],-1)
RB=np.arange(436,477); SECT=[(a,a+5) for a in range(60,125,5)]; REF=[(0,30),(300,330),(0,5),(15,20),(300,305),(315,320)]
def perfil(img,a0,a1,rb=RB,stat=np.median):
    """perfil radial d'1 px (mediana per corona) d'un mapa 2D o 3D dins del sector."""
    s=(az>=a0)&(az<a1); out=[]
    for r0 in rb[:-1]:
        m=s&(rr>=r0)&(rr<r0+1); out.append(stat(img[m],axis=0) if m.any() else np.nan*np.ones(img.shape[-1] if img.ndim==3 else 1))
    return np.array(out)
def vora(a_prof,rb=RB,llindar=0.5):
    """primer radi (interpolat) on el perfil creua el llindar cap avall"""
    a=np.asarray(a_prof).ravel()
    for i in range(len(a)-1):
        if a[i]>=llindar>a[i+1]: return float(rb[i]+ (a[i]-llindar)/(a[i]-a[i+1]))
    return None
def amplada(Lp,rb=RB):
    """amplada 10–90 % del trànsit disc→corona sobre el perfil L*; nivell disc = mediana r 438–446, corona = mediana r 464–472"""
    L=np.asarray(Lp).ravel(); rmid=rb[:-1]+0.5
    d=np.nanmedian(L[(rmid>=438)&(rmid<446)]); c=np.nanmedian(L[(rmid>=464)&(rmid<472)])
    if not np.isfinite(d) or not np.isfinite(c) or c<=d: return None
    l10=d+0.1*(c-d); l90=d+0.9*(c-d)
    def creua(v):
        for i in range(len(L)-1):
            if L[i]<v<=L[i+1]: return rmid[i]+(v-L[i])/(L[i+1]-L[i])
        return None
    r10,r90=creua(l10),creua(l90)
    return dict(L_disc=float(d),L_corona=float(c),r10=r10,r90=r90,amplada=(None if r10 is None or r90 is None else float(r90-r10)),r50=creua(d+0.5*(c-d)))
res={'sectors':{},'referencia':{},'sub_marques':{}}
for nom,c,excl in [('V74',c74,(222,)),('V71',c71,(218,219,220))]:
    C,a,passos=c.recompon(exclou=excl,retorna_passos=True); L=lab(C)
    np.save(S4+f'/fc_{nom}_C.npy',C)
    ordre=[l['id'] for l in c.IDX['layers'] if l['visible'] and l['id'] not in excl]
    # alfes efectives i màscares d'usuari
    a30=c.carrega(30)[1]; d30=np.load((S4+'/roi74p_L30.npz') if nom=='V74' else (NEW+'/roi71_L30.npz')); m30=d30['c-2'].astype(np.float32)/65535; al30=d30['c-1'].astype(np.float32)/65535
    a76=c.carrega(76)[1]; a96=c.carrega(96)[1]; a204=c.carrega(204)[1]; a206=c.carrega(206)[1]
    a57=c.carrega(57)[1] if 57 in c.LAYERS and c.LAYERS[57]['visible'] else None
    for (a0,a1) in SECT+REF:
        k=f'{a0}-{a1}'
        pL=perfil(L,a0,a1); pC=perfil(C,a0,a1)
        ent={'L':pL[:,0].round(2).tolist(),'a':pL[:,1].round(2).tolist(),'b':pL[:,2].round(2).tolist(),
             'R':(pC[:,0]*255).round(1).tolist(),'G':(pC[:,1]*255).round(1).tolist(),'B':(pC[:,2]*255).round(1).tolist()}
        ent['vora_mask30_c2_0.5']=vora(perfil(m30,a0,a1)); ent['vora_alfa30_efectiva_0.5']=vora(perfil(a30,a0,a1)); ent['vora_alfa30_propia_0.5']=vora(perfil(al30,a0,a1))
        p76=perfil(a76,a0,a1).ravel(); ent['alfa76_per_r']=p76.round(3).tolist(); ent['alfa76_max_r440_456']=float(np.nanmax(p76[(RB[:-1]>=440)&(RB[:-1]<456)]))
        ent['alfa76_mitjana_r440_456']=float(np.nanmean(p76[(RB[:-1]>=440)&(RB[:-1]<456)]))
        ent['alfa206_per_r']=perfil(a206,a0,a1).ravel().round(3).tolist(); ent['alfa96_r450']=float(perfil(a96,a0,a1).ravel()[14]); ent['alfa204_r450']=float(perfil(a204,a0,a1).ravel()[14])
        if a57 is not None: ent['alfa57_per_r']=perfil(a57,a0,a1).ravel().round(3).tolist()
        ent['transit']=amplada(pL[:,0])
        # atribució capa a capa: ΔL* per banda
        bands={'448-456':(448,456),'456-462':(456,462),'440-448':(440,448),'462-470':(462,470)}
        s=(az>=a0)&(az<a1); atr={}
        prevL=None; prev_id=None
        for lid in ordre:
            Ci,ai=passos[lid]; Li=lab(Ci)[...,0]
            if prevL is None: base=Li; prevL=np.zeros_like(Li)
            row={}
            for bn,(r0,r1) in bands.items():
                m=s&(rr>=r0)&(rr<r1); row[bn]=float(np.median(Li[m]-prevL[m]))
            atr[str(lid)]=row; prevL=Li
        ent['atribucio_dL_per_capa']=atr
        ent['L_final_bandes']={bn:float(np.median(L[...,0][s&(rr>=r0)&(rr<r1)])) for bn,(r0,r1) in bands.items()}
        (res['sectors'] if (a0,a1) in SECT else res['referencia']).setdefault(nom,{})[k]=ent
    del passos
# sub-marques: mesura marca contra entorn a V74 i V71
mk=np.load(S4+'/marques74_masks.npz'); m1=mk['m1']; ent1=mk['ent_m1']
llarg=m1&(rr<456); curt=m1&(rr>=456)
C74=np.load(S4+'/fc_V74_C.npy'); C71=np.load(S4+'/fc_V71_C.npy'); L74=lab(C74); L71=lab(C71)
for nomsub,ms in [('trac_llarg_r449-453',llarg),('trac_curt_r458-465',curt)]:
    d={}
    for nom,Lx in [('V74',L74),('V71',L71)]:
        # entorn a la mateixa banda radial ±3 px però fora la marca, dins ent_m1 o el sector 60–125
        rlo,rhi=rr[ms].min(),rr[ms].max(); e=(~m1)&(rr>=rlo-1)&(rr<=rhi+1)&(az>=60)&(az<125)
        d[nom]={'marca_Lab':[float(np.median(Lx[...,i][ms])) for i in range(3)],'entorn_mateix_r_Lab':[float(np.median(Lx[...,i][e])) for i in range(3)],
                'entorn_ent_m1_Lab':[float(np.median(Lx[...,i][ent1])) for i in range(3)],'n':int(ms.sum()),'r':[float(rlo),float(rhi)],
                'az':[float(az[ms].min()),float(az[ms].max())]}
    res['sub_marques'][nomsub]=d
json.dump(res,open(S4+'/fc_m1_limbe.json','w'),indent=1,ensure_ascii=False)
print('fet')
