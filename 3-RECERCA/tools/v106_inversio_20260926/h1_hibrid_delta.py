"""h1 (V106, Claude, 26-09-2026) · Detall tangencial HÍBRID per a la capa de la V106: el de la geometria fina (c1f «LOLA fi»: nord 45,25°, LOLA-64, vora
mesurada de cada fotograma, cada fotograma dividit per la seva transmissió T i admès des de T ≥ 0,7) a 100–290°, on la prova «Lluna o corona» millora,
i el de la V105 (t2/DELTA_sigc32_pa) a la resta (dalt-dreta i dreta: allà la V105 ja era neta i la c1f no hi millora; a 300–320° hi empitjora).
Barreja amb pes w(θ) (smoothstep 95→105° i 285→295°), ponderada pel pes de cada font: X = (w·P_f·X_f + (1−w)·P_t·X_t) / (w·P_f + (1−w)·P_t).
Res no s'inventa: on cap font no té observació, pes 0. Ús: h1_hibrid_delta.py <DELTA_c1f.npz> <DELTA_V105.npz> <sortida.npz>"""
import sys, numpy as np
F = np.load(sys.argv[1]); T = np.load(sys.argv[2]); OUT = sys.argv[3]
assert np.array_equal(F['dgrid'], T['dgrid']) and int(F['nth']) == int(T['nth']) and np.allclose(F['centre'], T['centre'])
nth = int(F['nth']); th = np.degrees(np.linspace(0, 2 * np.pi, nth, endpoint=False))
def ss(x, a, b): q = np.clip((x - a) / (b - a), 0, 1); return q * q * (3 - 2 * q)
w = (ss(th, 95, 105) * (1 - ss(th, 285, 295)))[None, :]
out = {k: T[k] for k in ('dgrid', 'nth', 'centre', 'rampa')}
out['centres'] = F['centres']; out['w_c1f'] = w[0].astype(np.float32)
for x, p in (('delta', 'pes'), ('h125', 'p125'), ('hcurts', 'pcurts'), ('hA', 'pA'), ('hB', 'pB')):
    Pf = np.nan_to_num(F[p]).astype(np.float64); Pt = np.nan_to_num(T[p]).astype(np.float64)
    a = w * Pf; b = (1 - w) * Pt; P = a + b
    X = np.where(P > 0, (a * np.nan_to_num(F[x]) + b * np.nan_to_num(T[x])) / np.maximum(P, 1e-30), 0)
    out[x] = X.astype(np.float32); out[p] = P.astype(np.float32)
np.savez_compressed(OUT, **out)
print('escrit', OUT, '· w=1 a', round(float((w[0] > 0.999).mean() * 360)), '°')
