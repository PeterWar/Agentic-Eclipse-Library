import numpy as np, pandas as pd, json
XD='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/xmatch/'
sol=json.load(open(XD+'final_solution.json'))
for tag in ('sony','r6'):
    S=sol[tag+'_radial']; px=np.array(S['px']); py=np.array(S['py'])
    cat=pd.read_csv(XD+f'cat2_{tag}.csv'); m=pd.read_csv(XD+f'final_match_{tag}.csv')
    c=cat[(cat.sep_deg<5.0)&(cat.Vuse<=12.5)].reset_index(drop=True)
    xi,eta=c.xh_as.values,c.yh_as.values; r2=xi*xi+eta*eta
    A=np.column_stack([np.ones_like(xi),xi,eta,xi*r2,eta*r2])
    CX,CY=A@px,A@py
    print(f'--- {tag}: deteccions amb MES D\'UNA candidata dins 20 px ---')
    n=0
    for _,q in m.iterrows():
        d=np.hypot(q.x-CX,q.y-CY); k=np.argsort(d)[:3]
        if d[k[1]]<20:
            n+=1
            print(f'  {q.det:5s} V={q.V:5.2f} -> 1a: {c.TYC[k[0]]:14s} V={c.Vuse[k[0]]:5.2f} d={d[k[0]]:5.2f}px | '
                  f'2a: {c.TYC[k[1]]:14s} V={c.Vuse[k[1]]:5.2f} d={d[k[1]]:5.2f}px  (mateix HIP? {c.HIP[k[0]]==c.HIP[k[1]]})')
    if n==0: print('  cap')
