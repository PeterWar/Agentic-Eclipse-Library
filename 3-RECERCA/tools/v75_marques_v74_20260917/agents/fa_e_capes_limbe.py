import numpy as np, json, sys
import fa_lib as F
sys.path.insert(0,F.S4); sys.path.insert(0,F.NEW); import compo74 as c74, compo71 as c71
rb=np.arange(444,470); ri=np.floor(F.RR).astype(int)
sectors={'N(m2)':(104,113),'S':(240,300),'E':(330,30),'W(m5)':(163,171),'m7':(220,249)}
def perfil(arr,sel): return [float(np.median(arr[sel&(ri==r)])) for r in rb]
out={}
for nomv,c in (('V74',c74),('V71',c71)):
    out[nomv]={}
    for lid in (3,30,76,96,204,206):
        rgb,al=c.carrega(lid); L=F.Lstar(rgb)
        out[nomv][lid]={}
        for k,(a0,a1) in sectors.items():
            sel=((F.AZ>=a0)&(F.AZ<a1)) if a0<a1 else ((F.AZ>=a0)|(F.AZ<a1))
            out[nomv][lid][k]=dict(alfa=perfil(al,sel),L=perfil(L,sel))
    if nomv=='V71':
        rgb,al=c.carrega(57); L=F.Lstar(rgb); out[nomv][57]={k:dict(alfa=perfil(al,((F.AZ>=a0)&(F.AZ<a1)) if a0<a1 else ((F.AZ>=a0)|(F.AZ<a1))),L=perfil(L,((F.AZ>=a0)&(F.AZ<a1)) if a0<a1 else ((F.AZ>=a0)|(F.AZ<a1)))) for k,(a0,a1) in sectors.items()}
json.dump(dict(r=rb.tolist(),perfils=out),open(F.S4+'/fa_e_capes_limbe.json','w'),indent=1)
for k in sectors:
    print('=====',k); print('      r    : '+' '.join('%5d'%r for r in rb))
    for nomv in ('V71','V74'):
        for lid in out[nomv]:
            d=out[nomv][lid][k]
            print('%s L%-3d alfa: '%(nomv,lid)+' '.join('%5.2f'%v for v in d['alfa']))
            print('%s L%-3d L*  : '%(nomv,lid)+' '.join('%5.1f'%v for v in d['L']))
