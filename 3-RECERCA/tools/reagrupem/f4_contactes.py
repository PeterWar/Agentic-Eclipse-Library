#!/usr/bin/env python3
"""FASE 4 ter — les PERLES i els ANELLS DE DIAMANT, al mateix llenç.

És l'**objectiu científic número dos** del projecte, i fins ara els seus
fotogrames només tenien la nota «van a capes de contacte, no al sumatori
coronal». Aquí es fan aquelles capes.

Contactes calculats per **efemèride**, no suposats: la totalitat surt de
**105,20 s** (C2 a t=13,97 s, C3 a t=119,16 s) contra els **103,7 s** mesurats
de les imatges. La diferència d'1,5 s és el **relleu lunar**, que `research/11`
xifra en 1-3 s per contacte.

⛔ **Norma del rectangle**: cap capa retallada. Van al llenç sencer, amb el
mateix registre que la corona, o sigui que se superposen exactament.

⚠️ Corba de to: el mateix pendent declarat de 0,17/dècada, però amb el sostre
al **màxim de cada capa** i no a l'anell coronal — a un anell de diamant
l'àncora de 1,05-1,15 R☉ no vol dir res.
"""

from __future__ import annotations

import glob, json, math, os, sys, time
import numpy as np, cv2, rawpy
from astropy.io import fits

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/Users/USUARI/Downloads/Eclipse 2026/research/tools/encaix_sony")
import comu  # noqa: E402

PEND, TERRA = 0.17, 0.045


def to(v, m):
    x = np.where(m & (v > 0), v, np.nan)
    mx = float(np.nanpercentile(x, 99.995))
    y = 1.0 + PEND*np.log10(np.maximum(x, mx*1e-9)/mx)
    return np.clip(np.where(np.isfinite(y), y, TERRA), TERRA, 1.0).astype(np.float32)


def main():
    t0 = time.time()
    S = json.load(open(os.path.join(comu.REBUTS, "F1_sol_llenc.json")))
    G = json.load(open(os.path.join(comu.REBUTS, "F1_contactes.json")))
    LL = S["llenc"]; W, H = LL["vixen"]["W"], LL["vixen"]["H"]
    CXc, CYc = W/2.0, H/2.0
    PA = math.radians(-LL["pa_north_deg_origen"]); ca, sa = math.cos(PA), math.sin(PA)

    with rawpy.imread(comu.llista(comu.VIXEN, ".CR3")[0]) as r:
        g = comu.geometria(r); mc = comu.mapa_colors(r)
    FLAT = fits.getdata(os.path.join(comu.F0, "flat", "FLAT_RADIAL_R6III.fits")).astype(np.float32)
    darks = {round(float(p.split("_E")[1].rstrip("s.fits")), 8): p
             for p in glob.glob(os.path.join(comu.F0, "masters_dark", "*.fits"))}
    orig = {}
    for i in range(4):
        ys, xs = np.where(mc == i); orig[i] = (int(ys.min()), int(xs.min()))
    col = {0: 0, 1: 1, 2: 2, 3: 1}
    dk = {}

    def posa(n):
        """Un fotograma al llenç, en RGB, normalitzat per exposició."""
        v = S["fotogrames"][n]; e = v["exp"]
        if e not in dk:
            dk[e] = fits.getdata(darks[min(darks, key=lambda q: abs(q-e))]).astype(np.float32)
        with rawpy.imread(os.path.join(comu.VIXEN, n)) as r:
            raw = r.raw_image.astype(np.float32)
        cal = (raw - dk[e])/FLAT/e
        sx, sy = v["sol_x"], v["sol_y"]
        XX, YY = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
        dX = XX-CXc; dY = YY-CYc
        rawx = (ca*dX+sa*dY)+sx; rawy = (-sa*dX+ca*dY)+sy
        num = np.zeros((H, W, 3), np.float32); den = np.zeros((H, W, 3), np.float32)
        for i in range(4):
            oy, ox = orig[i]
            pl = cal[oy::2, ox::2]
            mx = ((rawx-ox)*0.5).astype(np.float32); my = ((rawy-oy)*0.5).astype(np.float32)
            ok = np.ones_like(pl, np.float32)
            num[..., col[i]] += cv2.remap(pl*ok, mx, my, cv2.INTER_LINEAR, borderValue=0.0)
            den[..., col[i]] += cv2.remap(ok, mx, my, cv2.INTER_LINEAR, borderValue=0.0)
        im = np.where(den > 0.5, num/np.maximum(den, 1e-9), np.nan).astype(np.float32)
        # ⚠️ cada fotograma porta el SEU cel: a la fase parcial el cel és
        # brillant i, si no es treu, el màxim de la finestra se l'emporta
        # arreu i les perles queden rentades. Es resta la mediana del camp
        # llunyà de CADA fotograma, per canal.
        yy2, xx2 = np.mgrid[0:H, 0:W].astype(np.float32)
        rr = np.hypot(yy2-CYc, xx2-CXc); del yy2, xx2
        fora = (rr > 6.0*440.60) & np.isfinite(im).all(axis=2)
        if fora.sum() > 50000:
            for i in range(3):
                im[..., i] -= float(np.median(im[fora, i]))
        return im

    wb = None
    with rawpy.imread(os.path.join(comu.VIXEN, comu.llista(comu.VIXEN, ".CR3")[0])) as r:
        w_ = list(r.daylight_whitebalance); wb = np.array([w_[0]/w_[1], 1.0, w_[2]/w_[1]], np.float32)

    plans = [
        ("C2 · perles i PRIMER ANELL DE DIAMANT", G["grups"]["C2_perles"], "max"),
        ("C3 · SEGON ANELL DE DIAMANT i perles", G["grups"]["C3_perles"], "max"),
        ("parcial abans de C2 (documental)", G["grups"]["parcial_pre"][::3], "mediana"),
        ("parcial després de C3 (documental)", G["grups"]["parcial_post"][::3], "mediana"),
    ]
    from psb_utils import new_psb, add_pixel_layer, set_merged, finalize_lr16
    from psd_tools.constants import BlendMode
    psd = new_psb(W, H)
    rebut = {"C2_t": G["C2_t"], "C3_t": G["C3_t"], "totalitat_s": G["totalitat_s"],
             "capes": {}}
    primera = None
    for nom, noms, mode in plans:
        acc = None
        for n in sorted(noms):
            im = posa(n)*wb
            if acc is None:
                acc = im[None, ...] if mode == "mediana" else im
            elif mode == "max":
                acc = np.fmax(acc, im)
            else:
                acc = np.concatenate([acc, im[None, ...]], axis=0)
        if mode == "mediana":
            acc = np.nanmedian(acc, axis=0)
        m = np.isfinite(acc).all(axis=2)
        rgb = np.dstack([to(acc[..., i], m) for i in range(3)])
        u16 = np.clip(np.rint(rgb*65535), 0, 65535).astype(np.uint16)
        add_pixel_layer(psd, u16, nom, mask8=(m.astype(np.uint8)*255),
                        blend=BlendMode.NORMAL, visible=(primera is None))
        if primera is None: primera = u16
        rebut["capes"][nom] = {"n": len(noms), "mode": mode,
                               "fotogrames": sorted(noms)}
        print(f"  {nom:44s} {mode:8s} n={len(noms):2d}  [{time.time()-t0:.0f}s]", flush=True)
    finalize_lr16(psd); set_merged(psd, primera)
    if getattr(psd, "_updated", False): psd._updated = False
    dst = comu.lliurable("Eclipsi_2026_VIXEN_contactes.psb")
    psd.save(dst)
    print(f"\nPSB: {dst}\n     {os.path.getsize(dst)/1e9:.2f} GB · {len(plans)} capes "
          f"({time.time()-t0:.0f}s)")
    rebut["fitxer"] = dst
    json.dump(rebut, open(os.path.join(comu.REBUTS, "F4_contactes.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
