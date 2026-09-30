"""TANCAMENT HDR PÍXEL A PÍXEL, no per anell.

La porta `tancament_hdr` compara el compost amb un fotograma solt als MATEIXOS
ANELLS, i una mediana d'anell no pot veure un error que viu on el joc
d'exposicions canvia —que és justament on la corona és més brillant, perquè
allà les llargues saturen i les curtes no—. Aquí el quocient compost/fotograma
es mesura píxel a píxel i s'ordena per BRILLANTOR: si puja amb la brillantor,
el compost amplifica els trets brillants i la porta no ho podia veure.
"""
from __future__ import annotations
import json, math, os, sys
import numpy as np
import rawpy, cv2

sys.path.insert(0, os.path.expanduser(
    (__import__("glob").glob(os.path.expanduser("~/Desktop/Eclipse determinista/1-RUNS/*20260827T012038Z*")) + [""])[0] + "/codi"))
import comu  # noqa: E402
import nucli as N  # noqa: E402


def frame_al_llenc(nom, v, LL, ped, W, H):
    """Pla VERD del fotograma, remapat al llenç (nord amunt, Sol al centre)."""
    with rawpy.imread(os.path.join(comu.TRENS["VIXEN"]["dir"], "totalitat", nom)) as r:
        raw = r.raw_image.astype(np.float32)
        mc = comu.mapa_colors(r)
    y, x = np.nonzero(mc == 1)
    y0, x0 = y.min(), x.min()
    pl = raw[y0::2, x0::2] - ped
    sat = (raw[y0::2, x0::2] >= 16000)
    a = math.radians(LL["pa_north_deg"]); ca, sa = math.cos(a), math.sin(a)
    RS = LL["R_sol_px"]
    # graella del llenç, retallada a l'interior (aquí només mirem r < 1,6 R☉)
    n = int(1.65 * RS)
    yy, xx = np.mgrid[-n:n, -n:n].astype(np.float32)
    sx = (v["sol_x"] + ca * xx - sa * yy - x0) / 2.0
    sy = (v["sol_y"] + sa * xx + ca * yy - y0) / 2.0
    sx = np.ascontiguousarray(sx, np.float32); sy = np.ascontiguousarray(sy, np.float32)
    im = cv2.remap(np.ascontiguousarray(pl, np.float32), sx, sy,
                   cv2.INTER_LINEAR, borderValue=0.0)
    dins = cv2.remap(np.ones_like(pl, np.float32), sx, sy, cv2.INTER_LINEAR,
                     borderValue=0.0)
    sm = cv2.remap(np.ascontiguousarray(sat, np.float32), sx, sy,
                   cv2.INTER_LINEAR, borderValue=1.0)
    im = np.where(dins > 0.999, im, np.nan)
    return im, sm, n, np.hypot(xx, yy) / RS


if __name__ == "__main__":
    lum, pes, LL, S = N.carrega_nostre(quin="CORONA")
    from astropy.io import fits
    G = fits.getdata(os.path.join(N.RUN, "2-ldic", "CORONA_G.fits")).astype(np.float32)
    cy, cx = int(LL["H"] // 2), int(LL["W"] // 2)
    ped = comu.TRENS["VIXEN"]["pedestal_dn"]
    fr = {k: v for k, v in S["fotogrames"].items() if v.get("coronal")}

    for nom in ("572A2969.CR3", "572A2975.CR3", "572A2988.CR3"):
        v = fr[nom]
        im, sm, n, rad = frame_al_llenc(nom, v, LL, ped, LL["W"], LL["H"])
        sub = G[cy - n:cy + n, cx - n:cx + n]
        k = (np.isfinite(im) & np.isfinite(sub) & (sm < 0.01) & (im > 40)
             & (sub > 0) & (rad > 1.05) & (rad < 1.55))
        q = sub[k] / im[k]
        b = im[k]
        print(f"\n{nom}  exp {v['exp']:g} s   {k.sum():,} px  (1,05–1,55 R☉, "
              f"sense saturar)")
        print(f"{'decil de brillantor':>20s} {'DN del fotograma':>18s}"
              f" {'compost/fotograma':>19s}  {'desviació':>10s}")
        ta = np.percentile(b, np.arange(0, 101, 10))
        ref = np.median(q)
        for i in range(10):
            m = (b >= ta[i]) & (b < ta[i + 1])
            if m.sum() < 100:
                continue
            print(f"{i*10:>15d}-{(i+1)*10:<3d} {np.median(b[m]):18.0f}"
                  f" {np.median(q[m]):19.4g}  {np.median(q[m])/ref*100-100:+9.1f}%")
