"""s7 · Variants del model sobre la dada real: prova Lluna/corona (inversions independents) i ρ, resumides a 200–280° i d 1–4."""
import numpy as np, json, sys, time
from pipeline import Pipeline
B1 = {r['j']: r for r in json.load(open('/Users/USUARI/Desktop/Eclipse 2026/4-RESULTATS/v106_inversio_20260926/b1/B1_PSF_LOLA_canal1.json'))['fotogrames']}
variants = json.loads(sys.argv[1])
def resum(R):
    out = []
    for sec in [(200, 240), (240, 280), (60, 100), (280, 320)]:
        f = [f"d{d:g}:{R['m1'][(sec[0], sec[1], d)]['f']:+.2f}/{R['rho'].get((sec[0], sec[1], d), (np.nan,))[0]:.2f}" for d in [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0] if (sec[0], sec[1], d) in R['m1']]
        out.append(f'  {sec[0]}-{sec[1]} (fracció/ρ): ' + ' '.join(f))
    return '\n'.join(out)
S = None
for nom, cfg in variants.items():
    t0 = time.time(); b1 = cfg.pop('b1', False)
    P = Pipeline(cfg, S=S)
    if b1:
        orig = P.nova
        def nova(orig=orig):
            I = orig()
            for j in P.fr:
                if j in B1: I.dxy[j] = (B1[j]['dx'], B1[j]['dy'])
            return I
        P.nova = nova
    R = P.proves(verbose=False); S = R['IT'].S
    print(f'=== {nom} {P.cfg} b1={b1} ({time.time()-t0:.0f} s)'); print(resum(R), flush=True)
    json.dump(dict(cfg=P.cfg, b1=b1, m1={f'{k[0]}-{k[1]} d{k[2]}': v for k, v in R['m1'].items()}, rho={f'{k[0]}-{k[1]} d{k[2]}': v for k, v in R['rho'].items()}), open(f'VARIANT_{nom}.json', 'w'), indent=1)
    del R
