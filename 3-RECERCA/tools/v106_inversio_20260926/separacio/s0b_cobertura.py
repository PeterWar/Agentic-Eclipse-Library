import numpy as np
D='dades/'; m=np.load(D+'META.npz'); dg=m['dgrid']; nth=int(m['nth']); t=m['t']; e=m['e']
OK=np.load(D+'OK.npy',mmap_mode='r'); DP=np.load(D+'DP.npy',mmap_mode='r'); WG=np.load(D+'WG.npy',mmap_mode='r')
dth=np.degrees(np.linspace(0,2*np.pi,nth,endpoint=False))
secs=[(60,100),(100,140),(140,180),(180,200),(200,220),(220,240),(240,260),(260,280),(280,320),(320,360),(0,60)]
for d in [1.0,2.0,3.0,4.0]:
    i=int(np.argmin(np.abs(dg-d))); print('=== d',d)
    for lo,hi in secs:
        s=(dth>=lo)&(dth<hi); rows=[]
        for j in range(67):
            ok=OK[j,i,s]&(DP[j,i,s]>=0.6)
            fr=ok.mean()
            if fr>0.5: rows.append((j,round(float(np.median(DP[j,i,s][ok])),1)))
        print(f'{lo}-{hi}: n={len(rows)} ', ' '.join(f'{j}:{D_}' for j,D_ in rows))
# pes típic per fotograma a d=6
i=int(np.argmin(np.abs(dg-6)))
print('pes WG mitjà a d=6 per fotograma:', ' '.join(f'{j}:{float(np.median(WG[j,i][OK[j,i]])) if OK[j,i].any() else 0:.3g}' for j in range(67)))
