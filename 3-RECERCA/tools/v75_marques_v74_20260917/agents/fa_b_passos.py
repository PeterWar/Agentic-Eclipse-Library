import numpy as np, json, sys
from scipy import ndimage as ndi
import fa_lib as F
sys.path.insert(0,F.S4); import compo74 as c
C,a,P=c.recompon(exclou=(222,),retorna_passos=True)
ordre=[l['id'] for l in c.IDX['layers'] if l['visible'] and l['id']!=222]
out={k:{} for k in F.MARKS}
# també: alfa efectiva de cada capa dins de cada marca i entorn
alfa={}
for lid in ordre:
    rgb,al=c.carrega(lid); alfa[lid]={k:dict(a_marca=float(al[F.mask(k)].mean()),a_entorn=float(al[F.mask('ent_'+k)].mean()),a_marca_max=float(al[F.mask(k)].max())) for k in F.MARKS}
for lid in ordre:
    Cb,ab=P[lid]; L=F.Lstar(Cb)
    for k in F.MARKS:
        m=F.mask(k); e=F.mask('ent_'+k); y0,y1,x0,x1=F.bbox(m|e,pad=25)
        Lc=L[y0:y1,x0:x1]; mc=m[y0:y1,x0:x1]; ec=e[y0:y1,x0:x1]
        d21=Lc-ndi.median_filter(Lc,21); d9=Lc-ndi.median_filter(Lc,9)
        out[k][lid]=dict(nom=c.LAYERS[lid]['name'][:28],L_marca=float(L[m].mean()),L_entorn=float(L[e].mean()),dif=float(L[m].mean()-L[e].mean()),
            min21_marca=float(d21[mc].min()),min21_entorn=float(d21[ec].min()),std21_marca=float(d21[mc].std()),std21_entorn=float(d21[ec].std()),
            min9_marca=float(d9[mc].min()),std9_marca=float(d9[mc].std()),p5_21_marca=float(np.percentile(d21[mc],5)),
            alfa_marca=alfa[lid][k]['a_marca'],alfa_entorn=alfa[lid][k]['a_entorn'],alfa_max=alfa[lid][k]['a_marca_max'])
json.dump(dict(ordre=ordre,per_marca=out),open(F.S4+'/fa_b_passos.json','w'),indent=1)
for k in F.MARKS:
    print('==',k)
    print('  capa nom                         alfa_m  L_m    L_e   dif   min21m min21e std21m std21e min9m  p5_21m')
    for lid in ordre:
        d=out[k][lid]; print('  %4d %-28s %.3f %6.2f %6.2f %+5.2f %6.2f %6.2f %5.2f %5.2f %6.2f %6.2f'%(lid,d['nom'],d['alfa_marca'],d['L_marca'],d['L_entorn'],d['dif'],d['min21_marca'],d['min21_entorn'],d['std21_marca'],d['std21_entorn'],d['min9_marca'],d['p5_21_marca']))
