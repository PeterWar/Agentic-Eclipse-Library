"""Corba de creixement per fotograma i correccio d'obertura."""
import numpy as np, pandas as pd

for tag, rap in (('sony', 9), ('r6', 10)):
    z = np.load(f'phot_{tag}.npz', allow_pickle=True)
    F = z['F']            # (nframes, nstars, RMAX)
    tab = pd.read_csv(f'final_match_{tag}.csv')
    R = np.arange(1, F.shape[2]+1)
    # combina fotogrames amb pes = temps d'exposicio (senyal/soroll ~ sqrt(t))
    exp = z['exp']
    W = exp[:, None, None]
    Fc = np.nansum(F*W, axis=0)/np.nansum(np.where(np.isfinite(F), W, 0), axis=0)
    br = np.argsort(-tab.flux.values)[:10]
    ref = np.nanmedian(Fc[br]/Fc[br, rap-1][:, None], axis=0)
    print(f'=== {tag} === corba de creixement mediana (10 mes brillants), '
          f'normalitzada a r={rap} px')
    print('  r     :', ' '.join(f'{r:6d}' for r in R))
    print('  f/fap :', ' '.join(f'{v:6.3f}' for v in ref))
    # correccio d'obertura: extrapolacio al plateau
    plateau = np.nanmedian(ref[13:18])
    print(f'  plateau r=14..18 : {plateau:.4f}  -> correccio {1/plateau:.4f} '
          f'({-2.5*np.log10(plateau):+.4f} mag)')
    np.savez(f'cogf_{tag}.npz', R=R, Fc=Fc, ref=ref, rap=rap, plateau=plateau)
    print()
