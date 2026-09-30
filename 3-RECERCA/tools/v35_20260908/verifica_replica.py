"""Verifica una RÈPLICA de la cadena V34(a1–b2)+V35(b3–c4) contra els artefactes canònics: per a cada matriu clau,
diferència màxima, fracció d'elements diferents i SHA; per al PSB, SHA. Escriu un JSON i diu PASS/FAIL amb toleràncies
DECLARADES (quasi-determinisme: BLAS amb fils pot moure l'últim bit dels float32; les capes u16 poden diferir ±1 DN16 en
una fracció petita de píxels). Ús: verifica_replica.py <dir_v34_replica> <dir_v35_replica> [--json sortida]."""
import sys, json, hashlib, argparse
from pathlib import Path
import numpy as np
ROOT = Path('/Users/USUARI/Downloads/Eclipse 2026'); T = ROOT / 'research/tools'
ap = argparse.ArgumentParser(); ap.add_argument('v34'); ap.add_argument('v35'); ap.add_argument('--json', default=None); A = ap.parse_args()
R34, R35 = Path(A.v34), Path(A.v35); C34, C35 = T / 'v34_20260907', T / 'v35_20260908'
TOL = {'float_rel_max': 1e-4, 'float_frac_diff': 0.05, 'u16_max_dn': 2, 'u16_frac_diff': 0.02}


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(16 << 20), b''):
            h.update(b)
    return h.hexdigest()


def cmp_float(a, b):
    a = np.load(a, mmap_mode='r'); b = np.load(b, mmap_mode='r'); assert a.shape == b.shape and a.dtype == b.dtype, (a.shape, b.shape)
    mx = 0.0; nd = 0; n = 0; relmax = 0.0
    for y in range(0, a.shape[0], 512):
        x = np.asarray(a[y:y + 512]); z = np.asarray(b[y:y + 512]); fa = np.isfinite(x); fb = np.isfinite(z)
        if not np.array_equal(fa, fb):
            nd += int((fa != fb).sum())
        k = fa & fb; d = np.abs(x[k] - z[k]); mx = max(mx, float(d.max()) if d.size else 0); nd += int((d > 0).sum()); n += int(k.sum())
        s = np.maximum(np.abs(x[k]), 1e-12); relmax = max(relmax, float((d / s).max()) if d.size else 0)
    return {'max_abs': mx, 'max_rel': relmax, 'frac_diff': nd / max(n, 1), 'identical': nd == 0}


def cmp_u16(a, b):
    a = np.load(a, mmap_mode='r'); b = np.load(b, mmap_mode='r'); assert a.shape == b.shape
    mx = 0; nd = 0
    for y in range(0, a.shape[0], 512):
        d = np.abs(np.asarray(a[y:y + 512]).astype(np.int32) - np.asarray(b[y:y + 512]).astype(np.int32)); mx = max(mx, int(d.max())); nd += int((d > 0).sum())
    return {'max_dn16': mx, 'frac_diff': nd / a.size, 'identical': nd == 0}


rep = {'tolerancies': TOL, 'float': {}, 'u16': {}, 'psb': {}}; ok = True
for name in ('vixen_total_v34.npy', 'sony_A_total_v34.npy', 'sony_B_total_v34.npy'):
    if (R34 / 'cau' / name).exists():
        r = cmp_float(C34 / 'cau' / name, R34 / 'cau' / name); rep['float'][name] = r; ok &= r['max_rel'] <= TOL['float_rel_max'] and r['frac_diff'] <= TOL['float_frac_diff']; print(f"{name}: max_abs {r['max_abs']:.3g} max_rel {r['max_rel']:.2e} frac_diff {r['frac_diff']:.2e} {'IDÈNTIC' if r['identical'] else ''}", flush=True)
for name in ('sony_corrected_total_v35.npy', 'fusion_total_v35.npy', 'base_G_v35.npy', 'weight_vixen_v35.npy', 'rho_v35.npy', 'delta_v35.npy'):
    if (R35 / 'cau' / name).exists():
        r = cmp_float(C35 / 'cau' / name, R35 / 'cau' / name); rep['float'][name] = r; ok &= r['max_rel'] <= TOL['float_rel_max'] and r['frac_diff'] <= TOL['float_frac_diff']; print(f"{name}: max_abs {r['max_abs']:.3g} max_rel {r['max_rel']:.2e} frac_diff {r['frac_diff']:.2e} {'IDÈNTIC' if r['identical'] else ''}", flush=True)
for k in ('01', '02', '04', '05', '06'):
    p = f'{k}_v35_u16.npy'
    if (R35 / 'cau' / p).exists():
        r = cmp_u16(C35 / 'cau' / p, R35 / 'cau' / p); rep['u16'][p] = r; ok &= r['max_dn16'] <= TOL['u16_max_dn'] and r['frac_diff'] <= TOL['u16_frac_diff']; print(f"{p}: max {r['max_dn16']} DN16, frac_diff {r['frac_diff']:.2e} {'IDÈNTIC' if r['identical'] else ''}", flush=True)
for k in ('P01_NRGF', 'P02_RHEF', 'P03_MGN', 'P04_WOW', 'P05_WOW_bilateral'):
    p = f'{k}_u16.npy'
    if (R35 / 'purs/cau' / p).exists():
        r = cmp_u16(C35 / 'purs/cau' / p, R35 / 'purs/cau' / p); rep['u16'][p] = r; ok &= r['max_dn16'] <= TOL['u16_max_dn'] and r['frac_diff'] <= TOL['u16_frac_diff']; print(f"{p}: max {r['max_dn16']} DN16, frac_diff {r['frac_diff']:.2e} {'IDÈNTIC' if r['identical'] else ''}", flush=True)
psb = R35 / 'staging/V35.psb'
if psb.exists():
    h = sha(psb); rep['psb'] = {'replica_sha256': h, 'canonic_sha256': '50c8e1cfb7144794db67c227324238fb33b9ccaf91502ff33fb6f954692aa6d4', 'identical': h == '50c8e1cfb7144794db67c227324238fb33b9ccaf91502ff33fb6f954692aa6d4', 'bytes': psb.stat().st_size}; print('PSB rèplica', h, 'IDÈNTIC' if rep['psb']['identical'] else 'DIFERENT (mira les capes: si les u16 passen, el PSB és equivalent)')
rep['PASS'] = bool(ok); print('VERIFICACIÓ:', 'PASS' if ok else 'FAIL')
if A.json:
    Path(A.json).write_text(json.dumps(rep, indent=1) + '\n')
