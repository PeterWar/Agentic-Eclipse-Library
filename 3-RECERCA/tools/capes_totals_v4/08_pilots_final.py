"""08 — Pilots de baix a dalt amb tots els estats acceptats de la V4, vistes generals a 1/4,
i verificació final dels nuclis P3/P4 contra les fonts (byte-idèntic dins P3 a la 1/3200,
dins P4 al compost 12+11). G7.07: PNG al rebut."""
import numpy as np
from v4_tests import *
from v4_tests import _P3, _P4

ids = [int(s) for s in sys.argv[1:]] or None
QA = V4W / 'QA/final'
os.makedirs(QA, exist_ok=True)
cad = json.load(open(V4W / 'QA/cadena/cadena.json'))
accepted = [3, 4, 5, 7] + [i for i in (8, 9, 10, 11, 12, 13, 16, 17)
                           if cad.get(str(i), {}).get('veredicte') == 'ACCEPTADA']
if ids:
    accepted = ids
S = [np.load(V4W / f'states/S{k}.npy', mmap_mode='r') for k in accepted]
names = {3: '12 1/3200', 4: '+11 1/500', 5: '+10 1/125', 7: '+09 1/60', 8: '+08 1/30', 9: '+07 1/15',
         10: '+06 1/8', 11: '+05 1/4', 12: '+04 1/2', 13: '+03 1s', 16: '+02 2s', 17: '+01 10,3s'}
pil = pilots(S, [names[k] for k in accepted], f'{QA}/pilot_baix_a_dalt')
overview(S[accepted.index(7)], f'{QA}/compost_fonament_S7_1de4.png')
overview(S[-1], f'{QA}/compost_final_S{accepted[-1]}_1de4.png')
# nuclis finals: dins P3 el final ha de ser ID3; dins P4, el compost 12+11
final = np.asarray(S[-1], np.float32) / 65535.0
s3 = np.asarray(S[0], np.float32) / 65535.0
S4 = np.asarray(np.load(V4W / 'states/S4.npy', mmap_mode='r'), np.float32) / 65535.0
P3c = np.asarray(_P3) >= 1
P4c = np.asarray(_P4) >= 1
nuc = dict(
    P3_px=int(P3c.sum()),
    P3_dif_max_DN=int(np.abs(quantize(final)[P3c].astype(np.int32) - quantize(s3)[P3c].astype(np.int32)).max()),
    P4_px=int(P4c.sum()),
    P4_dif_max_DN=int(np.abs(quantize(final)[P4c].astype(np.int32) - quantize(S4)[P4c].astype(np.int32)).max()),
)
jdump(nuc, f'{QA}/nuclis_P3_P4_final.json')
jdump(pil, f'{QA}/pilots.json')
print(json.dumps(nuc, indent=1))
print('acceptades:', accepted, flush=True)
