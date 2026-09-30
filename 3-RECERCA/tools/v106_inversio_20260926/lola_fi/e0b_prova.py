import numpy as np, time, json
from vora_lib import *
B1 = {r['j']: r for r in json.loads((R0/'4-RESULTATS/v106_inversio_20260926/b1/B1_PSF_LOLA_canal1.json').read_text())['fotogrames']}
for j in [5, 55]:
    t0=time.time(); V, W, th, r = polar(j, 1); Pb = bins(V).T   # (nb, ns)
    psf = (B1[j]['s1'], B1[j]['f'], B1[j]['s2'])
    p, err, s2, n = ajusta(Pb, S, psf)
    print(j, 'temps', round(time.time()-t0,2), 'psf', np.round(psf,2))
    u0 = p[:,4]
    print(' u0 percentils', np.round(np.nanpercentile(u0,[1,5,25,50,75,95,99]),3), ' err med', np.round(np.nanmedian(err),4), 'b med', np.round(np.median(p[:,1]),4), 'B0/A med', np.round(np.median(p[:,2]/np.exp(p[:,0])),4))
    for k in range(0,1440,90): 
        print(f'  θ {k*0.25:6.2f}: u0 {u0[k]:+.3f} ± {err[k]:.3f}  b {p[k,1]:+.3f}  A {np.exp(p[k,0]):9.0f} B0 {p[k,2]:8.0f} B1 {p[k,3]:+7.0f} chi {np.sqrt(s2[k]):.4f} n {n[k]:.0f}')
    np.save(f'/private/tmp/claude_v106/lola_fi/_prova_u0_{j}.npy', np.stack([u0, err]))
