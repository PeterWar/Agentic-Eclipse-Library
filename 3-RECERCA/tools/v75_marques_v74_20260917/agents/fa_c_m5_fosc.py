import numpy as np, json, sys
from scipy import ndimage as ndi
import fa_lib as F
sys.path.insert(0,F.S4); import compo74 as c
C,a,P=c.recompon(exclou=(222,),retorna_passos=True)
ordre=[l['id'] for l in c.IDX['layers'] if l['visible'] and l['id']!=222]
Lf=F.Lstar(C); med=ndi.median_filter(Lf,21); d=Lf-med
# píxels foscos del sector W ampli (az 140–185, r 457–486) amb dL<−6
sel=(F.RR>=457)&(F.RR<=486)&(F.AZ>=140)&(F.AZ<=185)&(d<-6)
lab,n=ndi.label(sel); print('components dL<-6 al sector W:',n)
comps=[]
for i in range(1,n+1):
    cc=lab==i; ys,xs=np.nonzero(cc)
    comps.append(dict(n=int(cc.sum()),y=float(ys.mean()),x=float(xs.mean()),r=[float(F.RR[cc].min()),float(F.RR[cc].max())],az=[float(F.AZ[cc].min()),float(F.AZ[cc].max())],min_dL=float(d[cc].min()),L=float(Lf[cc].mean())))
comps.sort(key=lambda q:-q['n']); [print(q) for q in comps[:10]]
# atribució: per a tots els píxels foscos del sector (sel), L* del píxel − mediana(21) després de cada capa; i valors de les fotos
print('capa   dL_mitjà_pixels_foscos   L_pixels   alfa_mitjana_capa  L_capa(rgb propi)')
rows={}
for lid in ordre:
    Cb=P[lid][0]; Lb=F.Lstar(Cb); db=Lb-ndi.median_filter(Lb,21)
    rgb,al=c.carrega(lid); Ll=F.Lstar(rgb)
    rows[lid]=dict(dL=float(db[sel].mean()),L=float(Lb[sel].mean()),alfa=float(al[sel].mean()),L_capa=float(Ll[sel].mean()))
    print('%4d %-26s %+6.2f %6.2f %5.3f %6.1f'%(lid,c.LAYERS[lid]['name'][:26],rows[lid]['dL'],rows[lid]['L'],rows[lid]['alfa'],rows[lid]['L_capa']))
# perfil radial al raig az 168–173 de: compost després de 56, després de 76, després de 96, final; i L* propi de 76 i 96 amb alfa
rb=np.arange(452,486); ri=np.floor(F.RR).astype(int); s=(F.AZ>=168)&(F.AZ<=173)
def prof(A): return [float(np.median(A[s&(ri==r)])) for r in rb]
pr={'r':rb.tolist()}
for lid in (56,30,76,96,204,206):
    pr['despres_%d'%lid]=prof(F.Lstar(P[lid][0]))
for lid in (76,96,204):
    rgb,al=c.carrega(lid); pr['L_capa_%d'%lid]=prof(F.Lstar(rgb)); pr['alfa_%d'%lid]=prof(al)
print('r      : '+' '.join('%5d'%r for r in rb))
for k in pr:
    if k!='r': print('%-12s: '%k+' '.join('%5.1f'%v for v in pr[k]))
json.dump(dict(components=comps,atribucio=rows,perfil_az168_173=pr),open(F.S4+'/fa_c_m5_fosc.json','w'),indent=1)
