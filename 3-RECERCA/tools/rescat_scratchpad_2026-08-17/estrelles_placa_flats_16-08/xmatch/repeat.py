"""Repetibilitat interna: dispersio del flux entre fotogrames independents.
Separa el soroll fotometric de l'error del model (extincio/vinyetatge/cataleg)."""
import numpy as np, pandas as pd

RAP = {'sony': 6, 'r6': 7}
for tag in ('sony', 'r6'):
    z = np.load(f'phot_{tag}.npz', allow_pickle=True)
    F = z['F'][:, :, RAP[tag]-1]        # (nframes, nstars) ADU/s
    names = z['names']; exp = z['exp']
    tab = pd.read_csv(f'final_match_{tag}.csv')
    print(f'================ {tag} ================')
    print('  fotogrames:', ', '.join(f'{n}({e:g}s)' for n, e in zip(names, exp)))
    W = exp[:, None]
    mean = np.nansum(F*W, 0)/np.nansum(np.where(np.isfinite(F), W, 0), 0)
    # dispersio ponderada entre fotogrames, en magnituds
    rows = []
    for i in range(F.shape[1]):
        f = F[:, i]
        ok = np.isfinite(f) & (f > 0)
        if ok.sum() < 3:
            continue
        m = -2.5*np.log10(f[ok])
        w = exp[ok]
        mu = np.sum(w*m)/np.sum(w)
        sd = np.sqrt(np.sum(w*(m-mu)**2)/np.sum(w)*ok.sum()/(ok.sum()-1))
        rows.append(dict(det=tab.det[i], V=tab.V[i], snr=tab.snr[i], n=ok.sum(),
                         flux=mean[i], sd_frame=sd, sem=sd/np.sqrt(ok.sum())))
    r = pd.DataFrame(rows)
    for lab, m in (('SNR>30', r.snr > 30), ('SNR 15-30', (r.snr > 15) & (r.snr <= 30)),
                   ('SNR<15', r.snr <= 15)):
        if m.sum():
            print(f'  {lab:10s} n={m.sum():2d}  dispersio entre fotogrames mediana='
                  f'{r['sd_frame'][m].median():.3f} mag  -> error del flux combinat '
                  f'{r['sem'][m].median():.3f} mag')
    r.to_csv(f'repeat_{tag}.csv', index=False)
    print()
