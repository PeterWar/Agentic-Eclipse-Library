"""j10 (V97) · DIAGNOSI POSTERIOR (no és un criteri predeclarat): la regressió E del jutge, separada per zones. E (predeclarada) compara el detall
del compost V97 i V96 a tot arreu fora del limbe i de l'anell 1,5–2,3 R☉ i va sortir 0,971 < 0,99. Aquí es treuen, per separat, les zones on
la V97 canvia A PROPÒSIT o on la V96 portava píxels que no eren dada: (a) les vores del camp (300 px del límit del suport: la V96 hi tenia la
continuació de la V86 a les capes 41/42), (b) la zona del graó diagonal de la Sony curat (dA 250–650 px on només hi ha la Sony A),
(c) les petjades d'estrella (la V96, pegats amb gra copiat). Ús: j10_regressio_neta.py <sortida.json>"""
import sys, json
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent))
from jutge_comu import *
PAS = 2; rs = radi_sol(pas=PAS); dl = dist_limbe(pas=PAS)
C6, cob = Estat(RES / 'v96_ref').compost(pas=PAS); C7, _ = Estat(RES / 'estat_v97').compost(pas=PAS)
L = lambda C: np.log(np.maximum(0.25 * C[..., 0] + 0.5 * C[..., 1] + 0.25 * C[..., 2], 1e-4)).astype(np.float32); d6 = dog(L(C6), 1, 8); d7 = dog(L(C7), 1, 8)
sup = np.asarray(np.load(RES / 'lineal_v97/support.npy', mmap_mode='r')[::PAS, ::PAS])
# (correcció de Codex, 24-09 nit) la distància és a la vora EXTERIOR del camp: el forat de la Lluna s'omple abans (si no, s'exclou tota la corona interior)
ple = sup | (dl < 0) | (rs < 1.6); vora = cv2.distanceTransform(ple.astype(np.uint8), cv2.DIST_L2, 5) * PAS < 300
sf = cv2.dilate(np.asarray(np.load(RES / 'lineal_v97/star_footprints.npy', mmap_mode='r')[::PAS, ::PAS], np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
C_ = RES / 'cadena_raw/sources_v29'; wA = np.load(C_ / 'sony_A_weights.npy', mmap_mode='r')[::PAS, ::PAS, 1] > 0; wB = np.load(C_ / 'sony_B_weights.npy', mmap_mode='r')[::PAS, ::PAS, 1] > 0; wV = np.load(C_ / 'vixen_weights.npy', mmap_mode='r')[::PAS, ::PAS, 1] > 0
dA = cv2.distanceTransform(np.asarray(wA, np.uint8), cv2.DIST_L2, 5) * PAS; diag = np.asarray(wA & ~wB & ~wV) & (dA > 250) & (dA < 650)
base = ~((dl < 40) | ((rs > 1.5) & (rs < 2.3))) & (cob > 0.99)
out = dict(nota=__doc__.split('\n')[0], E_predeclarada=corr(d7, d6, base))
for nom, excl in (('sense_vores_camp', vora), ('sense_zona_grao', diag), ('sense_estrelles', sf), ('sense_les_tres', vora | diag | sf)):
    out[nom] = corr(d7, d6, base & ~excl)
out['per_anell_sense_les_tres'] = {f'{a}-{b}': corr(d7, d6, base & ~(vora | diag | sf) & (rs >= a) & (rs < b)) for a, b in ((1, 1.5), (2.3, 3), (3, 4.5), (4.5, 7), (7, 12))}
desa(sys.argv[1], out); print(json.dumps(out, indent=1))
