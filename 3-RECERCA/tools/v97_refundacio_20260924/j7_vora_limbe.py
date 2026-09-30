"""j7 (V97) · A7, la vora clara de la fusió arran del limbe: fusió (G) contra la suma dels fotogrames primerencs de la caixa lunar
(limb_frames: numerador i pes per fotograma, calibrats i registrats, SENSE la taula de vora de la V38), per distància al limbe de presentació.
Primerencs = t ≤ 22,3 s (els d'A3A de la V86). A cada píxel, el quocient fusió/primerencs; mediana per calaix d'1 px de d (0,5–40) i per
sector de 30°, i mediana entre sectors. L'excés A7 = mediana(d 1–3) − mediana(d 15–40) (el nivell lluny del limbe, on no hi ha efecte de vora).
Llindar de Codex: excés ≤ 2 %. Ús: j7_vora_limbe.py <sortida.json> etiqueta=fusio.npy[:canal] …"""
import sys, json
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from jutge_comu import LLUNA, RLLUNA, desa, ARREL
LF = ARREL / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/limb_frames'
meta = json.loads((LF / 'METADATA.json').read_text()); y0, y1, x0, x1 = meta['box_y0y1x0x1']
Nn = np.load(LF / 'numerator.npy', mmap_mode='r'); Wg = np.load(LF / 'weight.npy', mmap_mode='r')
early = [i for i, f in enumerate(meta['frames']) if f['time'] <= 22.3]
num = np.zeros((y1 - y0, x1 - x0), np.float64); den = np.zeros_like(num)
for i in early: num += Nn[i, ..., 1]; den += Wg[i, ..., 1]
E = np.where(den > 0, num / np.maximum(den, 1e-20), np.nan).astype(np.float32)
yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32); d = np.hypot(xx - LLUNA[0], yy - LLUNA[1]) - RLLUNA
th = (np.degrees(np.arctan2(-(yy - LLUNA[1]), xx - LLUNA[0])) + 360) % 360
out = dict(definicio=__doc__.split('\n')[1], primerencs=[meta['frames'][i]['name'] for i in early], resultats={})
for arg in sys.argv[2:]:
    et, ruta = arg.split('=', 1); c = 1
    if ':' in ruta.split('/')[-1]: ruta, c = ruta.rsplit(':', 1); c = int(c)
    F = np.load(ruta, mmap_mode='r'); F = np.asarray(F[y0:y1, x0:x1, c] if F.ndim == 3 else F[y0:y1, x0:x1], np.float32)
    q = F / E; ok = np.isfinite(q) & (q > 0) & (E > 0) & (F > 0)
    edges = np.arange(0.5, 40.5, 1.0); prof_s = {}
    for s0 in range(0, 360, 30):
        ms = ok & (th >= s0) & (th < s0 + 30); P = []
        for a in edges:
            m = ms & (d >= a) & (d < a + 1); P.append(float(np.median(q[m])) if m.sum() > 30 else np.nan)
        prof_s[s0] = P
    A = np.array(list(prof_s.values())); med = np.nanmedian(A, 0)
    exces = float(np.nanmedian(med[0:3]) / np.nanmedian(med[14:40]) - 1)
    per_sector = {k: (float(np.nanmedian(np.array(v)[0:3]) / np.nanmedian(np.array(v)[14:40]) - 1) if np.isfinite(np.array(v)[0:3]).any() else None) for k, v in prof_s.items()}
    out['resultats'][et] = dict(exces_d1_3=exces, per_sector=per_sector, perfil_mediana_d0p5_40=[round(float(x), 4) for x in med])
    print(et, 'excés', round(exces * 100, 1), '%', {k: (None if v is None else round(v * 100, 1)) for k, v in per_sector.items()}, flush=True)
desa(sys.argv[1], out)
