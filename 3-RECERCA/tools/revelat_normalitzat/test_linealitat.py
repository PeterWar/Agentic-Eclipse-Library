"""Test de linealitat del slider ACR (§5.1 de la proposta V4, fail-closed).

La mateixa capa 07 revelada a +0,00 i +1,00 EV: decodificats Display P3 -> lineal
(TRC sRGB), la rao dels dos rasters ha de ser 2,000 constant (±1 %) entre
e = 0,01 i 0,8 (e = nivell lineal del revelat a +0). Si falla -> Opcio B.
"""
import json, sys
from pathlib import Path
import numpy as np
import tifffile

BASE = Path.home() / 'Desktop/Eclipse 2026/Derivats/Vixen/HDR4/revelat_v4'
P0, P1 = BASE / 'out/probe_07_p0.tif', BASE / 'out/probe_07_p1.tif'
LO, HI, TARGET, TOL = 0.01, 0.8, 2.0, 0.01

def srgb_to_linear(c):
    c = np.asarray(c, np.float64)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)

def main():
    a = tifffile.imread(P0).astype(np.float64) / 65535.0
    b = tifffile.imread(P1).astype(np.float64) / 65535.0
    assert a.shape == b.shape == (4640, 6960, 3), a.shape
    la, lb = srgb_to_linear(a), srgb_to_linear(b)
    report = {'files': [str(P0), str(P1)], 'range_e': [LO, HI], 'target': TARGET, 'tol': TOL}
    ok_all = True
    for k, name in enumerate('RGB'):
        x, y = la[..., k], lb[..., k]
        m = (x >= LO) & (x <= HI)
        q = y[m] / x[m]
        med, p1, p99 = np.percentile(q, [50, 1, 99])
        # constancia per decil d'e: la rao no pot derivar amb el nivell
        edges = np.linspace(LO, HI, 11)
        per_bin = []
        for e0, e1 in zip(edges[:-1], edges[1:]):
            mb = (x >= e0) & (x < e1)
            per_bin.append(float(np.median(y[mb] / x[mb])) if mb.any() else None)
        spread = max(per_bin) - min(per_bin)
        ok = abs(med - TARGET) <= TOL * TARGET and abs(p1 - TARGET) <= TOL * TARGET \
            and abs(p99 - TARGET) <= TOL * TARGET and spread <= 2 * TOL * TARGET
        report[name] = {'n': int(m.sum()), 'median': float(med), 'p1': float(p1), 'p99': float(p99),
                        'per_decile': per_bin, 'spread': float(spread), 'ok': bool(ok)}
        ok_all &= ok
        print(f'{name}: n={m.sum():>9,}  mediana={med:.4f}  p1={p1:.4f}  p99={p99:.4f}  '
              f'spread_decils={spread:.4f}  {"OK" if ok else "FALLA"}')
    report['verdict'] = 'PASS' if ok_all else 'FAIL'
    out = BASE / 'receipts/test_linealitat_5.1.json'
    out.write_text(json.dumps(report, indent=1))
    print(f"VEREDICTE §5.1: {report['verdict']}  -> {out}")
    sys.exit(0 if ok_all else 1)

if __name__ == '__main__':
    main()
