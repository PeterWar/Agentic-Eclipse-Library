"""Validacio del renderer offline (substitueix el test §5.1 del slider ACR, que ja no
aplica: la via ACR scriptada esta descartada; la proposta §5 permet l'Opcio B amb
"factor racional exacte, arrodoniment documentat").

1. Probe d'escala: 07 a x1 i x2 -> despres de decodificar el TRC, la rao ha de ser
   2,000 constant (la tolerancia ±1 % de §5.1 es compleix per construccio; aqui es
   verifica empiricament inclosa la quantitzacio u16).
2. Contracte amb el revelat ACR vell (el raster ID9 de la cadena V3b/V3c, extret al
   scratchpad): a la zona on ACR es lineal (e < ~0,1) la rao vell/nou ha de ser plana
   (documenta el BaselineExposure 0,26 EV que ACR aplicava i nosaltres no); a e alta
   el vell s'ha de comprimir (es la corba que la V4 elimina).
"""
import json, os, sys
from pathlib import Path
import numpy as np
import tifffile

BASE = Path.home() / 'Desktop/Eclipse 2026/Derivats/Vixen/HDR4/revelat_v4'
CAPESTOTALS_WORK = Path(os.environ.get(
    'CAPESTOTALS_WORK',
    Path.home() / 'Desktop/Eclipse 2026/Derivats/Vixen/CapesTotals_work',
)).expanduser()
V3B = Path(os.environ.get('V3B_SCR', CAPESTOTALS_WORK / 'v3b')).expanduser()
SUN = (3563.89, 2274.66)   # centre solar, coords locals del frame 6960x4640
R_SUN = 446.15

def srgb_to_linear(c):
    c = np.asarray(c, np.float64)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)

def lum(a):
    return a @ np.array([0.2126, 0.7152, 0.0722])

def main():
    rep = {}
    # 1) probe d'escala
    p0 = tifffile.imread(BASE / 'out/probe_07_p0.tif').astype(np.float64) / 65535
    p1 = tifffile.imread(BASE / 'out/probe_07_p1.tif').astype(np.float64) / 65535
    l0, l1 = srgb_to_linear(p0), srgb_to_linear(p1)
    x, y = lum(l0), lum(l1)
    m = (x >= 0.01) & (x <= 0.4)     # x2 ha de quedar <= 0,8: dins del rang §5.1
    q = y[m] / x[m]
    med, p_1, p_99 = np.percentile(q, [50, 1, 99])
    ok = abs(med - 2) <= 0.02 and abs(p_1 - 2) <= 0.02 and abs(p_99 - 2) <= 0.02
    rep['probe_escala'] = {'n': int(m.sum()), 'median': float(med), 'p1': float(p_1),
                           'p99': float(p_99), 'ok': bool(ok)}
    print(f'probe escala x2/x1: mediana={med:.4f} p1={p_1:.4f} p99={p_99:.4f} -> {"OK" if ok else "FALLA"}')

    # 2) contracte amb el revelat ACR vell (ID9 = 07); R i B al v3b, G al v2b
    #    (aixi ho declara v3c_lib._src_paths)
    V2B = V3B.parent / 'v2b'
    old = np.stack([np.asarray(np.load((V3B if c in 'RB' else V2B) / f'src_id9_{c}.npy',
                                     mmap_mode='r'), np.float64)
                    for c in 'RGB'], axis=2) / 65535
    lo = lum(srgb_to_linear(old))
    yy, xx = np.mgrid[0:4640, 0:6960].astype(np.float64)
    rr = np.hypot(xx - SUN[0], yy - SUN[1]) / R_SUN
    bands = []
    for r0, r1 in [(1.05, 1.2), (1.2, 1.5), (1.5, 2.0), (2.0, 2.6)]:
        s = (rr >= r0) & (rr < r1)
        e_new = np.median(x[s]); e_old = np.median(lo[s])
        bands.append({'r': [r0, r1], 'e_nou': float(e_new), 'e_vell': float(e_old),
                      'rao_vell_nou': float(e_old / e_new)})
        print(f'  anell {r0:4.2f}-{r1:4.2f} R☉: e_nou={e_new:.5f} e_vell={e_old:.5f} '
              f'rao vell/nou={e_old/e_new:.4f}')
    rep['contracte_acr_vell'] = bands
    out = BASE / 'receipts/valida_render.json'
    out.write_text(json.dumps(rep, indent=1))
    print(f'-> {out}')
    sys.exit(0 if ok else 1)

if __name__ == '__main__':
    main()
