"""Fins on arriben de veritat les ales estel.lars: error real (dispersio entre
estrelles) i prova d'integral. I on treballa el model de halo."""
import numpy as np, json
from wings import halo_model, BINS

P = 2048
ky, kx = np.mgrid[0:P, 0:P]
kd = np.hypot(np.minimum(kx, P-kx), np.minimum(ky, P-ky))
p = json.load(open('/Users/USUARI/Desktop/Eclipse 2026/Earthshine_FINAL/'
                   'earthshine_FINAL_halo_params.json'))['G']
norms = {}
for lab, (s, b) in (('k1', p['k1']), ('k2', p['k2'])):
    norms[lab] = float((1.0/(1.0+(kd/s)**2)**b).sum())
print('=== model de halo, canal G ===')
print(f"  nucli proper k1: s={p['k1'][0]} beta={p['k1'][1]}  A1={p['A1']:.5f}  "
      f"norma={norms['k1']:.4g}")
print(f"  nucli ample  k2: s={p['k2'][0]} beta={p['k2'][1]}  A2={p['A2']:.5f}  "
      f"norma={norms['k2']:.4g}")
print(f"  fraccio de llum dispersada total A1+A2 = {p['A1']+p['A2']:.4f} "
      f"({100*(p['A1']+p['A2']):.2f} %)")


def comp(r):
    a = p['A1']*(1.0/(1.0+(r/p['k1'][0])**2)**p['k1'][1])/norms['k1']
    b = p['A2']*(1.0/(1.0+(r/p['k2'][0])**2)**p['k2'][1])/norms['k2']
    return a, b


print('\n  qui domina el halo a cada radi (fraccio del flux total per pixel):')
print(f'  {"r px":>7s} {"proper":>11s} {"ample":>11s} {"total":>11s} {"% ample":>8s}')
for r in (5, 10, 20, 50, 100, 200, 300, 500, 800):
    a, b = comp(float(r))
    print(f'  {r:7d} {a:11.3e} {b:11.3e} {a+b:11.3e} {100*b/(a+b):8.1f}')

# fraccio de llum dispersada mes enlla de r
print('\n  fraccio del flux dispersat mes enlla de r (integral 2*pi*r dr):')
rr = np.arange(0.5, 1024, 0.5)
a, b = comp(rr)
tot = np.cumsum((a+b)*2*np.pi*rr*0.5)
for r in (10, 20, 50, 100, 200, 400, 800):
    i = np.searchsorted(rr, r)
    print(f'    r>{r:4d} px : {tot[-1]-tot[i]:.5f}  '
          f'(r<{r:4d}: {tot[i]:.5f})')

print('\n=== mesura estel.lar: prova d\'integral ===')
for tag, sc in (('sony', 3.1923), ('r6', 2.1478)):
    z = np.load(f'wings_{tag}.npz')
    r, pr, er = z['r'], z['prof'], z['err']
    b = BINS
    area = np.pi*(b[1:]**2 - b[:-1]**2)
    cum = np.cumsum(pr*area)
    hm = np.array([np.mean(np.sum(comp(np.linspace(max(b[i], .3), b[i+1], 40)),
                                  axis=0)) for i in range(len(r))])
    cumh = np.cumsum(hm*area)
    print(f'  --- {tag} ---')
    print(f'  {"r px":>7s} {"flux acum.":>12s} {"model acum.":>12s}')
    for i in range(len(r)):
        print(f'  {b[i+1]:7.1f} {cum[i]:12.4f} {cumh[i]:12.5f}')
    j = np.searchsorted(b, 20)
    print(f'  >>> el flux acumulat hauria de tendir a 1,0. A r=130 px val '
          f'{cum[-2]:.1f}: {"IMPOSSIBLE, es fons residual" if cum[-2]>1.5 else "coherent"}')
