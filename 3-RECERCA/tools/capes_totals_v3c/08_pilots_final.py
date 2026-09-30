"""Pilots de baix a dalt amb tots els estats acceptats, vistes generals a 1/4, i la mesura DESPRÉS del defecte (sectors de 5°
al voltant de la protuberància: màscara de la 1/125 i compost 12+11+10)."""
import numpy as np
from tests_v3c import *
ids = [int(s) for s in sys.argv[1:]] or [3, 4, 5, 7, 8, 9]
QA = f'{SCR}/QA/final'; os.makedirs(QA, exist_ok=True)
S = [np.load(f'{SCR}/states/S{k}.npy', mmap_mode='r') for k in ids]
names = {3: 'ID3 sol (1/3200)', 4: '+ID4 1/500', 5: '+ID5 1/125', 7: '+ID7 1/60', 8: '+ID8 1/30', 9: '+ID9 1/15', 10: '+ID10 1/8'}
pil = pilots(S, [names[k] for k in ids], f'{QA}/pilot_baix_a_dalt')
overview(S[ids.index(7)], f'{QA}/compost_fonament_S7_1de4.png'); overview(S[-1], f'{QA}/compost_final_S{ids[-1]}_1de4.png')
# DESPRÉS del defecte
m5 = np.load(f'{SCR}/masks/mask_5.npy').astype(np.float32)/65535.
d, az, Rm = lunar_coords(5); sel = frame_sel(5)
out = {}
for (r0, r1) in ((452, 470), (470, 500), (500, 530)):
    out[f'mascara_ID5_{r0}-{r1}'] = {s0: round(float(m5[sel & (d >= r0) & (d < r1) & (az >= s0) & (az < s0+5)].mean()), 3) for s0 in range(0, 360, 5)}
L5 = lum(np.asarray(S[ids.index(5)], np.float32)/65535.); L4 = lum(np.asarray(S[ids.index(4)], np.float32)/65535.)
for (r0, r1) in ((455, 470), (470, 500)):
    out[f'compost_DN_[12+11+10,12+11]_{r0}-{r1}'] = {s0: [round(float(np.median(L5[z])*65535)), round(float(np.median(L4[z])*65535))] for s0 in range(0, 360, 5) for z in [sel & (d >= r0) & (d < r1) & (az >= s0) & (az < s0+5)]}
# sot azimutal de la màscara al voltant de la protuberància (165-210°) respecte de la resta, per anell
for k in ('mascara_ID5_452-470', 'mascara_ID5_470-500'):
    v = out[k]; dins = np.mean([v[s] for s in range(165, 215, 5)]); fora = np.median([v[s] for s in v if not (165 <= s < 215)])
    out[k+'_resum'] = dict(mitjana_165_210=round(float(dins), 3), mediana_resta=round(float(fora), 3))
jdump(out, f'{QA}/DESPRES_mascara_ID5_sectors.json'); jdump(pil, f'{QA}/pilots.json')
print(json.dumps({k: v for k, v in out.items() if k.endswith('_resum')}, indent=1))
print('mascara 452-470 per 15°:', {s: out['mascara_ID5_452-470'][s] for s in range(0, 360, 15)})
print('mascara 470-500 per 15°:', {s: out['mascara_ID5_470-500'][s] for s in range(0, 360, 15)})
