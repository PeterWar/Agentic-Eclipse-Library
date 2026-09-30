import sys, numpy as np
fs = sys.argv[1:]
Zs = [np.load(f) for f in fs]
dg = Zs[0]['dgrid']; nth = int(Zs[0]['nth']); dth = np.degrees(np.linspace(0, 2*np.pi, nth, endpoint=False))
print('cobertura (fracció de l\'arc amb dada) | ' + ' | '.join(f.split('/')[-2][:14] for f in fs))
for lo, hi in [(60,140),(200,240),(240,280),(280,320),(0,360)]:
    s = (dth>=lo)&(dth<hi)
    for d in [0.5,1.0,1.5,2.0,3.0,4.0]:
        i = int(np.argmin(np.abs(dg-d)))
        print(f'{lo:3d}-{hi:<3d} d {d:3.1f} | ' + ' | '.join(f'{(Z["pes"][i][s]>0).mean():.2f} (A {(Z["pA"][i][s]>0).mean():.2f} B {(Z["pB"][i][s]>0).mean():.2f})' for Z in Zs))
