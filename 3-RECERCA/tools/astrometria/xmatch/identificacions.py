#!/usr/bin/env python3
"""Taula d'identificacions publicada: IDENTIFICACIONS_sony.csv i IDENTIFICACIONS_r6.csv.

NOU a la promocio (17-08-2026): el generador d'aquests dos fitxers no era al
rescat. El format s'ha deduit dels rescatats
(estrelles_placa_flats_16-08/xmatch/IDENTIFICACIONS_*.csv) i es reprodueix
exactament (diferencia maxima 4e-15 a R_Rsol, la resta byte a byte):

    det, HIP, TYC, HD, Sp, V, BV, R_Rsol, resid, flux_tot, snr, Vobs, dV

- det … BV, resid, snr : de final_match_<tag>.csv (final_solve.py), ordenat per V;
- R_Rsol               : hypot(x - sun_x, y - sun_y) * escala / 947,07, amb el
                         centre del Sol i l'escala de la solucio LINEAL
                         (final_solution.json[tag], no la '_radial'), com fa
                         corona2.py;
- flux_tot, Vobs, dV   : de bemp_<tag>.csv (bemporad.py). Les deteccions sense
                         fotometria valida (obertura fora del sensor) no hi
                         surten, com al rescat (R6: 21 de 22).

Si bemp_<tag>.csv encara no existeix (etapa xmatch abans de la fotometria),
escriu la taula amb flux_tot/Vobs/dV buits i ho diu; torna'l a executar despres
de bemporad.py per tenir-la sencera. Copia el resultat a comu.out()."""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import comu
os.chdir(comu.work("xmatch"))

import json, shutil
import numpy as np, pandas as pd

RSUN_AS = 947.07
COLS = ['det', 'HIP', 'TYC', 'HD', 'Sp', 'V', 'BV', 'R_Rsol', 'resid',
        'flux_tot', 'snr', 'Vobs', 'dV']

sol = json.load(open('final_solution.json'))
for tag in ('sony', 'r6'):
    fm = pd.read_csv(f'final_match_{tag}.csv')
    S = sol[tag]                       # solucio lineal (com corona2.py)
    fm['R_Rsol'] = np.hypot(fm.x - S['sun_x'], fm.y - S['sun_y'])*S['scale']/RSUN_AS
    bemp = Path(f'bemp_{tag}.csv')
    if bemp.exists():
        b = pd.read_csv(bemp)[['det', 'flux_tot', 'Vobs', 'dV']]
        d = fm.merge(b, on='det', how='inner')       # nomes les que tenen fotometria
        estat = f'{len(d)}/{len(fm)} amb fotometria (bemp_{tag}.csv)'
    else:
        d = fm.copy()
        for c in ('flux_tot', 'Vobs', 'dV'):
            d[c] = np.nan
        estat = (f'{len(d)} identificades, SENSE fotometria: falta bemp_{tag}.csv '
                 f'(executa bemporad.py i torna-hi)')
    d = d[COLS]                        # ordre de final_match (ja ordenat per V)
    d.to_csv(f'IDENTIFICACIONS_{tag}.csv', index=False)
    shutil.copy2(f'IDENTIFICACIONS_{tag}.csv', comu.out()/f'IDENTIFICACIONS_{tag}.csv')
    print(f'IDENTIFICACIONS_{tag}.csv: {estat}')
