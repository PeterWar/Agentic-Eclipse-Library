"""Pas 0: factor fi del sensor (PRNU) de la Vixen des dels 125 flats del 22-08 (recepta de la recerca 90,
refeta perquè el mapa es va retirar el 16-09).  Sortida: 4-RESULTATS/ael_20260930/moviment/PRNU_VIXEN_FINE_mosaic_visible.npy"""
import json, time, numpy as np
from comu import *
from ael import calibrate as cal, io as aio
t0 = time.time()
FL = sorted((ARREL / '0-RAW/Vixen R6III/Flats R6III').glob('572A7*.CR3'))
assert len(FL) == 125, len(FL)
master, info = cal.master_flat(FL, black=511.5, saturation=13995.0, visible=True, progress=True)
fine = cal.fine_sensor_factor(master, 2.0)
mos = cal.merge_cfa(fine)
RM = RES / 'moviment'; RM.mkdir(exist_ok=True)
np.save(RM / 'PRNU_VIXEN_FINE_mosaic_visible.npy', mos)
np.save(RM / 'FLAT_VIXEN_MASTER_cfa4.npy', master)
st = [dict(pla=n, rms_pct=float(100 * np.std(f)), p1=float(np.percentile(f, 1)), p99=float(np.percentile(f, 99))) for n, f in zip(info['planes'], fine)]
info.update(fine_stats=st, temps_s=time.time() - t0, forma_mosaic=list(mos.shape))
json.dump(info, open(RM / 'PRNU_VIXEN_REBUT.json', 'w'), indent=1)
print(json.dumps(st, indent=1), f'{time.time() - t0:.0f} s')
