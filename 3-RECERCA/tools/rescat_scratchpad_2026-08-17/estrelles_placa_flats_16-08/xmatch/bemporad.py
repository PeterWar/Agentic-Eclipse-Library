"""Prova de coherencia a la Bemporad (2020): la DIFERENCIA de magnituds
observada entre parells d'estrelles ha de coincidir amb la del cataleg."""
import numpy as np, pandas as pd, json, itertools

zp2 = json.load(open('zp2.json'))
for tag in ('sony', 'r6'):
    d = pd.read_csv(f'zp2_{tag}.csv')
    d = d[np.isfinite(d.minst)].reset_index(drop=True)
    z = zp2[tag]
    # magnitud observada corregida d'extincio i color, comparable amb el cataleg
    BV = np.where(np.isfinite(d.BV), d.BV, 0.0)
    d['Vobs'] = d.minst + z['ZPsun'] - z['k']*(d.X - z['Xsun']) - z['c']*BV
    d['dV'] = d.Vobs - d.V
    print(f'================ {tag} ================')
    for lab, m in (('totes', np.ones(len(d), bool)),
                   ('SNR>15', d.snr > 15),
                   ('SNR>30', d.snr > 30),
                   ('V d\'Hipparcos', d.HIP.notna()),
                   ('Hipparcos i SNR>15', d.HIP.notna() & (d.snr > 15))):
        if m.sum() < 3:
            continue
        r = d.dV[m]
        print(f'  {lab:20s} n={m.sum():2d}  mediana={r.median():+.3f}  '
              f'sd={r.std(ddof=1):.3f}  MAD*1.48={1.4826*np.median(np.abs(r-r.median())):.3f} mag')
    # parells: diferencia observada contra diferencia de cataleg
    sub = d[(d.snr > 15)].reset_index(drop=True)
    if len(sub) >= 2:
        dd = []
        for i, j in itertools.combinations(range(len(sub)), 2):
            dobs = sub.Vobs[i]-sub.Vobs[j]
            dcat = sub.V[i]-sub.V[j]
            dd.append((sub.det[i], sub.det[j], dcat, dobs, dobs-dcat))
        dd = pd.DataFrame(dd, columns=['a', 'b', 'dV_cat', 'dV_obs', 'error'])
        e = dd.error.abs()
        print(f'  PARELLS (SNR>15): n={len(dd)}  |error| mediana={e.median():.3f}  '
              f'p68={e.quantile(0.68):.3f}  p90={e.quantile(0.90):.3f} mag')
        print(f'    dins de 0,10 mag: {100*(e<0.10).mean():.0f} %   '
              f'dins de 0,20: {100*(e<0.20).mean():.0f} %')
        dd.sort_values('error', key=abs).to_csv(f'pairs_{tag}.csv', index=False)
        # els cinc parells mes brillants
        b = sub.sort_values('snr', ascending=False).head(5)
        print('    parells de les 5 mes brillants:')
        for i, j in itertools.combinations(b.index, 2):
            print(f'      {sub.det[i]:>4s}-{sub.det[j]:<4s} cat={sub.V[i]-sub.V[j]:+.3f}  '
                  f'obs={sub.Vobs[i]-sub.Vobs[j]:+.3f}  error={sub.Vobs[i]-sub.Vobs[j]-(sub.V[i]-sub.V[j]):+.3f}')
    print()
    d.to_csv(f'bemp_{tag}.csv', index=False)
