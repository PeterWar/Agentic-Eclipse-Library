"""w7 (verificador adversari 2) · Els discos rodons de la vista W5_1 (base després/abans, σ6): són ombres de pols que la cura TREU (hi eren
abans com a clot i després el lloc queda pla) o que la cura POSA (abans pla, després disc)? Perfil radial del ln al voltant de cada disc, abans i
després, a la base i als tres apilats, relatiu a l'anell 90–140 px. Nul: el mateix a 8 posicions a 300 px.
Sortida: W7_DISCOS_POLS.json"""
import json, sys
from pathlib import Path
import numpy as np
A = Path(__file__).resolve().parents[4]; OUT = A / '4-RESULTATS/v108_20260926/verifica2_marrons'
F2 = A / '4-RESULTATS/v108_20260926/flat2d_v2'; CAD = A / '4-RESULTATS/v108_20260926/cadena'; CR = A / '4-RESULTATS/v97_refundacio_20260924'
P = {'base_G': (CAD / 'control/lineal/base_G.npy', CAD / 'flat2d_v2/lineal/base_G.npy', None),
     'vixen_G': (CR / 'proves_apilat/vixen_comuna_taula_original/vixen_total.npy', F2 / 'apilats/vixen_total.npy', 1),
     'sonyA_G': (CR / 'cadena_raw/b2_sony_A/cau/sony_A_total_v36.npy', F2 / 'apilats/sony_A_total.npy', 1),
     'sonyB_G': (CR / 'cadena_raw/b2_sony_B/cau/sony_B_total_v42.npy', F2 / 'apilats/cau/sony_B_total_v42.npy', 1)}
CENTRES = [tuple(map(int, c.split(','))) for c in sys.argv[1:]] or [(5862, 5316), (6153, 4376)]
M = 460
R = {}
def tall(p, ch, x, y):
    a = np.load(p, mmap_mode='r'); t = np.asarray(a[y - M:y + M, x - M:x + M] if ch is None else a[y - M:y + M, x - M:x + M, ch], np.float64); return t
yy, xx = np.mgrid[-M:M, -M:M]
for (x0, y0) in CENTRES:
    # recentra al màxim local del canvi a la base (σ6) dins de ±40 px
    a = tall(P['base_G'][0], None, x0, y0); b = tall(P['base_G'][1], None, x0, y0)
    from scipy.ndimage import gaussian_filter
    d = gaussian_filter(np.log(b / a), 6); w = d[M - 40:M + 40, M - 40:M + 40]; iy, ix = np.unravel_index(np.nanargmax(np.abs(w)), w.shape); cx, cy = x0 + ix - 40, y0 + iy - 40
    res = dict(centre=[int(cx), int(cy)])
    for nom, (pa, pd, ch) in P.items():
        a = tall(pa, ch, cx, cy); b = tall(pd, ch, cx, cy)
        def prof(img, ox=0, oy=0):
            rr = np.hypot(yy - oy, xx - ox); l = np.log(np.where(img > 0, img, np.nan)); ref = np.nanmedian(l[(rr >= 90) & (rr < 140)])
            return [round(1e4 * (float(np.nanmedian(l[(rr >= r0) & (rr < r0 + 10)])) - ref), 1) for r0 in range(0, 90, 10)]
        o = dict(abans=prof(a), despres=prof(b))
        nul = []
        for k in range(8):
            ang = np.radians(45 * k); ox, oy = int(300 * np.cos(ang)), int(300 * np.sin(ang)); pa_ = prof(a, ox, oy); nul.append(pa_[0])
        o['nul_disc0_abans_ppm'] = nul
        res[nom] = o; print((cx, cy), nom, o, flush=True)
    R[f'{cx},{cy}'] = res
(OUT / 'W7_DISCOS_POLS.json').write_text(json.dumps(R, ensure_ascii=False, indent=1))
