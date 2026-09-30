"""B9: igualació de to i color en baixa freqüència de les fotos d'interiors (76) i perles (96/204) al compost de sota, fora del disc: guany per canal g_c = suau(sota_c/foto_c) mesurat als píxels sense protuberància (R/G de la foto ≤ R/G de sota + 0,15) de la ploma (alfa 0,03–0,9), σ 24 px, estès per convolució normalitzada; aplicat a tot el suport de la foto fora de r < R−2. Màscares i alfa intactes."""
import sys, json, numpy as np
NEW='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/6346f583-afd0-49da-9c17-95128c31820e/scratchpad'
sys.path.insert(0,NEW)
import compo71; from compo71 import *
from scipy.ndimage import gaussian_filter
CX,CY,RS=998.88,998.41,456.0; Y,X=np.mgrid[0:2000,0:2000]; rr=np.hypot(X-CX,Y-CY)
compo71.OVERRIDE.clear(); compo71.OVERRIDE[3]=NEW+'/roi72_L3.npz'; compo71.OVERRIDE[30]=NEW+'/roi72_L30.npz'; compo71.OVERRIDE[56]=NEW+'/roi72_L56.npz'; compo71.OVERRIDE[55]=NEW+'/roi72_L55.npz'
Cs,as_=recompon(exclou=(219,220,76,96,204,206,202))   # el que hi ha SOTA les fotos
rep={}
for lid in (76,96,204):
    rgb,a=carrega(lid); d=np.load(NEW+f'/roi71_L{lid}.npz'); op=LAYERS[lid]['opacity']/255.0; aeff=a/op
    rg_f=gaussian_filter(rgb[...,0],2)/np.maximum(gaussian_filter(rgb[...,1],2),1e-4); rg_s=gaussian_filter(Cs[...,0],2)/np.maximum(gaussian_filter(Cs[...,1],2),1e-4)
    L_f=gaussian_filter(rgb.mean(-1),2); L_s=gaussian_filter(Cs.mean(-1),2)
    mesura=(aeff>0.03)&(aeff<0.9)&(rr>RS+3)&(rr<RS+90)&(rg_f<=rg_s+0.15)&(L_f<L_s*1.05)&(as_>0.99)   # ploma sense protuberància ni perles
    print(f'capa {lid}: píxels de mesura {int(mesura.sum())}')
    gains=[]
    for c in range(3):
        ratio=np.where(mesura,np.log(np.maximum(Cs[...,c],1e-4)/np.maximum(rgb[...,c],1e-4)),0.0); w=mesura.astype(float)
        num=gaussian_filter(ratio,24); den=gaussian_filter(w,24); g=np.where(den>0.02,num/np.maximum(den,1e-6),np.nan)
        # estén on no hi ha mesura (protuberàncies): convolució normalitzada més ampla
        num2=gaussian_filter(np.nan_to_num(g)*(den>0.02),60); den2=gaussian_filter((den>0.02).astype(float),60); g2=np.where(den>0.02,g,num2/np.maximum(den2,1e-6)); g2=np.clip(np.exp(np.nan_to_num(g2)),0.7,1.7)
        gains.append(g2)
    G=np.dstack(gains); zona=(aeff>0.005)&(rr>RS-2); fade=np.clip((rr-(RS-2))/6,0,1)[...,None]   # dins del disc intacte
    new=np.clip(rgb*(1+(G-1)*fade)*zona[...,None]+rgb*(~zona)[...,None],0,1)
    q_ab=np.median((rgb.mean(-1)/np.maximum(Cs.mean(-1),1e-4))[mesura]); q_de=np.median((new.mean(-1)/np.maximum(Cs.mean(-1),1e-4))[mesura])
    rep[lid]=dict(pixels_mesura=int(mesura.sum()),quocient_L_abans=float(q_ab),quocient_L_despres=float(q_de),guany_mediana_RGB=[float(np.median(G[...,c][mesura])) for c in range(3)],guany_max=float(G[zona].max()),guany_min=float(G[zona].min()),pixels_canviats=int((np.abs(new-rgb).max(-1)>1/65535).sum()))
    print(' ',rep[lid])
    o={k:d[k] for k in d.files}
    for c,key in enumerate(('c0','c1','c2')): o[key]=(new[...,c]*65535+.5).astype(np.uint16)
    np.savez_compressed(NEW+f'/roi72_L{lid}.npz',**o)
json.dump(rep,open(NEW+'/b9_fotos.json','w'),indent=1); print('fet')
