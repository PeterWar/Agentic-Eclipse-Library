"""Les vistes de l'auditoria. LLENÇ SENCER, mai un retall, i a 2-OUTPUT.

Brno es remapa al NOSTRE llenç (Sol al centre, nord amunt, mateixa escala), o
sigui que els tres panells són el mateix marc i es poden mirar l'un damunt de
l'altre. L'estructura es normalitza per anell als dos costats perquè la corba
de to i el guany desapareguin i quedi només la FORMA.
"""
from __future__ import annotations
import json, os
import numpy as np
import cv2
from PIL import Image

import nucli as N

K = 4                                   # reducció de la vista (llenç SENCER)
SORTIDA = os.path.expanduser("~/Desktop/Eclipse determinista/2-OUTPUT/AUDITORIA_ESTRUCTURA")
REF = "TSE2026_Trigaza_800mm.png"


def perfil_radial(a, rad, m, nb=900, rmax=10.0):
    idx = np.clip((rad / rmax * nb).astype(np.int32), 0, nb - 1)
    k = m & np.isfinite(a)
    c = np.bincount(idx[k], None, nb); s = np.bincount(idx[k], a[k], nb)
    mu = np.where(c > 200, s / np.maximum(c, 1), np.nan)
    s2 = np.bincount(idx[k], np.abs(a[k] - mu[idx[k]]), nb)
    sd = np.where(c > 200, s2 / np.maximum(c, 1), np.nan) * 1.4826
    for v in (mu, sd):                                  # omple els forats
        bo = np.isfinite(v)
        v[:] = np.interp(np.arange(nb), np.arange(nb)[bo], v[bo])
    return mu[idx], np.maximum(sd[idx], 1e-12)


def a_gris(a, m, lo=-2.2, hi=2.2):
    v = np.clip((np.nan_to_num(a) - lo) / (hi - lo), 0, 1)
    g = np.repeat((v * 255).astype(np.uint8)[..., None], 3, axis=2)
    g[~m] = np.array([110, 35, 130], np.uint8)
    return g


if __name__ == "__main__":
    os.makedirs(SORTIDA, exist_ok=True)
    lum, pes, LL, S = N.carrega_nostre()
    H, W, RS = LL["H"], LL["W"], LL["R_sol_px"]
    reg = json.load(open(os.path.join(N.AQUI, N.REGISTRE)))[REF]
    br, _, _, _ = N.carrega_brno(REF)

    h, w = H // K, W // K
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    X = (xx + 0.5) * K - W / 2.0; Y = (yy + 0.5) * K - H / 2.0
    rad = np.hypot(X, Y) / RS

    small = lambda a: cv2.resize(a, (w, h), interpolation=cv2.INTER_AREA)
    nos = small(lum.astype(np.float32)); wp = small(pes.astype(np.float32))
    del lum, pes

    # Brno al NOSTRE llenç
    g = np.deg2rad(reg["gir_deg"]); ca, sa = np.cos(g), np.sin(g)
    sx = reg["cx"] + (ca * X + sa * Y) * (reg["R_sol_px"] / RS)
    sy = reg["cy"] + (-sa * X + ca * Y) * (reg["R_sol_px"] / RS)
    sxc = np.ascontiguousarray(sx, np.float32); syc = np.ascontiguousarray(sy, np.float32)
    viu = np.isfinite(br).astype(np.float32)     # fora el peu de foto
    bro = cv2.remap(np.nan_to_num(br).astype(np.float32), sxc, syc,
                    cv2.INTER_LINEAR, borderValue=0.0)
    dins = cv2.remap(viu, sxc, syc, cv2.INTER_LINEAR, borderValue=0.0) > 0.999
    geo = json.load(open(N.GEO_BRNO))[REF]
    dm = np.hypot(sx - geo["cx"], sy - geo["cy"]) > geo["R_lluna_px"] + 0.012 * reg["R_sol_px"]
    mb = dins & dm & (rad > 1.0) & (rad < 9.0)

    ref = np.nanpercentile(wp[rad < 6.0], 90)
    mn = np.isfinite(nos) & (wp > 0.02 * ref) & (rad > 1.0) & (rad < 9.0)

    en = np.full_like(nos, np.nan); eb = np.full_like(nos, np.nan)
    for a, m, out in ((nos, mn, en), (bro, mb, eb)):
        mu, sd = perfil_radial(a.astype(np.float64), rad, m)
        out[...] = (a - mu) / sd

    tots = mn & mb
    dif = np.where(tots, en - eb, np.nan)
    panells = [("NOSALTRES", a_gris(en, mn)), ("BRNO 800 mm", a_gris(eb, mb)),
               ("DIFERÈNCIA", a_gris(dif, tots, -3, 3))]
    tela = np.full((h, w * 3 + 24, 3), 20, np.uint8)
    for i, (_, im) in enumerate(panells):
        tela[:, i * (w + 12):i * (w + 12) + w] = im
    p = os.path.join(SORTIDA, f"ESTRUCTURA_nosaltres_Brno_diferencia_x{K}.png")
    Image.fromarray(tela).save(p)
    print(f"{p}  ({tela.shape[1]}×{tela.shape[0]})")
    print(f"  llenç sencer {W}×{H} reduït ×{K}; lila = sense dada")
    print(f"  panells: nosaltres · Brno remapat al nostre llenç · diferència")
