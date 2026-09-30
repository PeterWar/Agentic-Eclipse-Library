import numpy as np
from e4_ajust import *
A4 = np.load(H/'E4_AJUST_LDEM64.npz'); hl = hlola(float(A4['thN']), float(A4['sig_arc']))
_, _, pc, pf, res, _ = solve(hl, return_all=True)
Bs = {}
for i in range(nJ):
    w = (Wt[i]>0).astype(float); Bs[i] = bandes(np.where(w>0,res[i],0), w)
def cc(i,k,b): m=(Wt[i]>0)&(Wt[k]>0); return corr(Bs[i][b], Bs[k][b], m)
idx = {j:i for i,j in enumerate(J)}
for b in ('gran','mitjana'):
    print('banda', b)
    for pairs in [[(0,1),(1,2),(4,5),(6,7)],[(9,10),(10,11),(15,16),(16,17)],[(27,28),(28,29),(33,34),(40,41),(46,47)],[(50,51),(55,56),(60,61)],[(10,28),(16,46),(11,29),(17,41)],[(0,50),(5,55),(7,60)]]:
        print('   ', ' '.join(f'{j}-{k}:{cc(idx[j],idx[k],b):+.2f}' for j,k in pairs))
    print('   rms per fotograma:', ' '.join(f'{j}:{np.std(Bs[idx[j]][b][Wt[idx[j]]>0]):.2f}' for j in J))
# perfil del residu (gran) de la mitjana de grups
for nom, gr in {'A':range(0,9),'A2':range(9,18),'C':range(26,49),'B':range(50,67)}.items():
    S=np.zeros(nb); W=np.zeros(nb)
    for j in gr:
        if j in idx: i=idx[j]; S+=Wt[i]*res[i]; W+=Wt[i]
    g = np.where(W>0,S/np.maximum(W,1e-30),np.nan)
    sm = gsm(np.nan_to_num(g),(W>0).astype(float),2.0)
    print(nom, 'residu suavitzat 2° cada 15°:', ' '.join(f'{sm[k]:+.2f}' for k in range(0,1440,60)))
