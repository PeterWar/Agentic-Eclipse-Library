"""A7: perfils radials per sector (mediana en azimut, pas 0,25 px) del compost i de cada capa, als sectors de les marques."""
import sys, numpy as np, json
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
from compo import *
from scipy.ndimage import map_coordinates
Rr=np.load(SP+'/roi_recomp.npz'); Cr=Rr['C'].astype(np.float32)/65535; ar=Rr['a'].astype(np.float32)/65535
CX,CY=5377-4377-1.6,3777-2777-0.9
RR=np.arange(420,500,0.25)
def perfil(img,az0,az1):
    th=np.deg2rad(np.arange(az0,az1,0.25)); xs=CX+RR[None,:]*np.cos(th[:,None]); ys=CY-RR[None,:]*np.sin(th[:,None])
    P=map_coordinates(img,[ys.ravel(),xs.ravel()],order=1,mode='nearest').reshape(len(th),len(RR)); return np.median(P,0)
sectors={'marca1 dalt (az 76–100)':(76,100),'marca2 NW (az 148–158)':(148,158),'marca3-4 W (az 163–173)':(163,173),'marca5 W eq (az 177–181)':(177,181),'marca6 WSW (az 189–199)':(189,199),'marca8 SSW (az 240–254)':(240,254),'control E (az 350–10)':(-10,10),'control S (az 260–280)':(260,280)}
seq=[l for l in IDX['layers'] if l['visible'] and l['id']!=218]
caps={l['id']:carrega(l['id']) for l in seq}
out={}
for nom,(a0,a1) in sectors.items():
    d={'r':RR.tolist(),'compost_L':perfil(Cr.mean(-1),a0,a1).tolist(),'compost_alfa':perfil(ar,a0,a1).tolist()}
    for lid in (3,30,76,96,204,206,41,42,45,46,51,53,55,56):
        rgb,a=caps[lid]; d[f'L{lid}_L']=perfil(rgb.mean(-1),a0,a1).tolist(); d[f'L{lid}_a']=perfil(a,a0,a1).tolist()
    out[nom]=d
json.dump(out,open(SP+'/a7_perfils.json','w'))
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
fig,axs=plt.subplots(len(sectors),2,figsize=(16,4*len(sectors)))
for i,(nom,d) in enumerate(out.items()):
    ax=axs[i,0]; ax.plot(RR,d['compost_L'],'k',lw=2,label='compost (lluminància)')
    for lid,c in [(3,'tab:orange'),(30,'tab:gray'),(76,'tab:red'),(96,'tab:purple'),(204,'tab:pink'),(206,'tab:brown')]:
        ax.plot(RR,d[f'L{lid}_L'],c,lw=1,label=f'L{lid} RGB')
    ax.set_title(nom+' · nivells'); ax.set_ylim(0,0.6); ax.axvline(453.5,color='c',ls=':'); ax.legend(fontsize=7,ncol=2); ax.grid(alpha=.3)
    ax=axs[i,1]; ax.plot(RR,d['compost_alfa'],'k',lw=2,label='alfa compost')
    for lid,c in [(3,'tab:orange'),(30,'tab:gray'),(76,'tab:red'),(96,'tab:purple'),(204,'tab:pink'),(206,'tab:brown'),(41,'tab:green'),(56,'tab:olive')]:
        ax.plot(RR,d[f'L{lid}_a'],c,lw=1,label=f'L{lid} alfa·màsc·op')
    ax.set_title(nom+' · alfes efectives'); ax.set_ylim(-0.02,1.02); ax.axvline(453.5,color='c',ls=':'); ax.legend(fontsize=7,ncol=2); ax.grid(alpha=.3)
plt.tight_layout(); plt.savefig(SP+'/v_A7_perfils.png',dpi=80); print('fet')
