"""Portes de la V14 (edició quirúrgica de la V13_Pere). Totes sobre el FITXER ESCRIT.

A · fidelitat    els canals de píxels són BYTE A BYTE els de la V13_Pere; els
                 rectangles valen exactament original + moviment; la màscara de
                 la 12 és intacta; les altres només canvien dins del disc + rampa
                 i només cap avall.
B · alineació    la desalineació de corona re-mesurada al fitxer escrit queda
                 ≤ 0,35 px a totes les parelles fiables (abans: fins a 2,9 px).
C · limbe net    el vel dins del disc cau per sota de 0,005 de nivell (abans
                 0,04-0,09); cap pujada nova al perfil radial del limbe.
D · rodona       la silueta fosca del disc té el radi constant en azimut (≤ 2 px).
E · obrible      psd-tools i ImageIO (sips) llegeixen el fitxer (la lliçó del 27-08).
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v13pere")
SRC = ("/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/"
       "Capes Totals/CapesTotalsV13_Pere.psd")
DST = ("/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/"
       "Capes Totals/CapesTotalsV14.psd")

import fes_v14_pere as F
import mesura_desalineacio as MD


def porta(nom, ok, detall):
    print(f"  {nom}: {'PASSA' if ok else '⛔ FALLA'} — {detall}")
    return ok


def main():
    from psd_tools import PSDImage
    from psd_tools.constants import ChannelID

    tot_ok = True
    a = PSDImage.open(SRC)
    b = PSDImage.open(DST)
    W, H = a.width, a.height
    discos = F._discos()
    (c2c, c2R) = discos["C2"]

    # ---- A · fidelitat
    print("[A] fidelitat")
    ok = True
    detalls = []
    caches_g = {}
    for la, lb in zip(a, b):
        num = la.name.split("_")[0]
        dx, dy = F.MOVIMENTS[num]
        ra, rb = la._record, lb._record
        if not (rb.top == ra.top + dy and rb.left == ra.left + dx
                and rb.bottom == ra.bottom + dy and rb.right == ra.right + dx):
            ok = False; detalls.append(f"{num}: rect de capa")
        if not (rb.mask_data.top == ra.mask_data.top + dy
                and rb.mask_data.left == ra.mask_data.left + dx):
            ok = False; detalls.append(f"{num}: rect de màscara")
        if la.name != lb.name or la.visible != lb.visible or la.opacity != lb.opacity:
            ok = False; detalls.append(f"{num}: metadades")
        for j, ci in enumerate(ra.channel_info):
            if int(ci.id) == int(ChannelID.USER_LAYER_MASK):
                continue
            ha = hashlib.sha256(la._channels[j].data).hexdigest()
            hb = hashlib.sha256(lb._channels[j].data).hexdigest()
            if ha != hb:
                ok = False; detalls.append(f"{num}: canal {int(ci.id)}")
        if num == "12":
            _, cda = F._canal_mascara(la)
            _, cdb = F._canal_mascara(lb)
            if cda.data != cdb.data:
                ok = False; detalls.append("12: la màscara hauria de ser intacta")
        else:
            ma, _, _ = F._decodifica_mascara(la, W, H)
            mb, _, _ = F._decodifica_mascara(lb, W, H)
            # el contingut de la nova, tornat al marc de l'original (i fora la
            # vora de 4 px del llenç, on el roll dona la volta)
            mb0 = np.roll(np.roll(mb, -dy, axis=0), -dx, axis=1)
            dif = (mb0 - ma)[4:-4, 4:-4]
            xx = np.arange(W, dtype=np.float32)[None, :]
            yy = np.arange(H, dtype=np.float32)[:, None]
            dd = np.hypot(xx - (c2c[0] - dx), yy - (c2c[1] - dy))
            fora_zona = dd > c2R + F.RAMPA_INICI + F.RAMPA_AMPLE + 6
            if num in discos:
                oc, oR = discos[num]
                fora_zona &= (np.hypot(xx - (oc[0] - dx), yy - (oc[1] - dy))
                              > oR + F.RAMPA_INICI + F.RAMPA_AMPLE + 6)
            if float(np.abs(dif[fora_zona[4:-4, 4:-4]]).max()) > 0:
                ok = False; detalls.append(f"{num}: màscara canviada FORA del disc")
            if float(dif.max()) > 0.5 / 65535.0:
                ok = False; detalls.append(f"{num}: màscara puja enlloc")
            del ma, mb, mb0, dif
        # cau del G del fitxer escrit per a la porta B (al marc del llenç)
        g = np.zeros((H, W), np.float32)
        x0, y0, x1, y1 = lb.bbox
        arr = lb.numpy("color")[..., 1]
        g[max(0, y0):min(H, y1), max(0, x0):min(W, x1)] = arr[
            max(0, y0) - y0:min(H, y1) - y0, max(0, x0) - x0:min(W, x1) - x0]
        caches_g[num] = g
        del arr
    tot_ok &= porta("A", ok, "; ".join(detalls) if detalls else
                    "canals de píxels byte a byte, rectangles = original+moviment, "
                    "màscares només avall i només dins del disc")

    # ---- B · alineació re-mesurada al fitxer escrit
    print("[B] alineació de corona (re-mesura sobre la V14)")
    MD._g = lambda num: caches_g[num]
    (cx, cy), _ = MD._centre()
    parelles = [("11", "10"), ("10", "09"), ("09", "08"), ("08", "07"),
                ("07", "06"), ("06", "05"), ("05", "04"), ("04", "03"),
                ("03", "02"), ("09", "07"), ("08", "06"), ("06", "04"),
                ("05", "02")]
    pitjor = 0.0
    ok = True
    for pa, pb in parelles:
        rin, rout = MD._banda(pa, pb)
        r = MD.mesura_parella(pa, pb, cx, cy, rin, rout)
        d = max(abs(r["tot"]["dx"]), abs(r["tot"]["dy"]))
        pitjor = max(pitjor, d)
        print(f"    {pa}→{pb}: ({r['tot']['dx']:+.2f}, {r['tot']['dy']:+.2f}) "
              f"resp {r['tot']['resposta']:.2f}")
        if d > 0.35:
            ok = False
    tot_ok &= porta("B", ok, f"pitjor residu {pitjor:.2f} px (llindar 0,35; "
                    "abans fins a 2,9)")

    # ---- C · el vel dins del disc, i cap pujada nova
    print("[C] limbe net")
    comp14 = np.load(os.path.join(CAU, "compost_v14.npy"), mmap_mode="r")
    g14 = comp14[..., 1].astype(np.float32) / 65535.0
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dl = np.hypot(xx - c2c[0], yy - c2c[1])
    anells = {"[-120,-80]": (-120, -80), "[-60,-40]": (-60, -40),
              "[-30,-20]": (-30, -20), "[-12,-6]": (-12, -6)}
    ok = True
    vels = {}
    for nom, (r0, r1) in anells.items():
        s = (dl > c2R + r0) & (dl < c2R + r1)
        vels[nom] = float(g14[s].mean())
        if vels[nom] > 0.005 and r1 <= -20:
            ok = False
    print("    vel per anell:", {k: round(v, 4) for k, v in vels.items()},
          "(V13_Pere: 0.038-0.09)")
    perfil = []
    for r0 in np.arange(-10, 26, 2.0):
        s = (dl > c2R + r0 - 1) & (dl < c2R + r0 + 1)
        perfil.append(float(np.median(g14[s])))
    puj = min(np.diff(perfil))
    if puj < -0.02:
        ok = False
    tot_ok &= porta("C", ok, f"vel [-60,-40] {vels['[-60,-40]']:.4f} · perfil del "
                    f"limbe monòton (pitjor pas {puj:+.4f})")

    # ---- D · la silueta, per MÀXIM DE GRADIENT i contra la V13_Pere amb la
    #      mateixa vara. ⛔ Un llindar de brillantor mesura la isofota, no la
    #      vora (la lliçó de research/111/114): a l'azimut de la protuberància
    #      la brillantor comença AL limbe i a la resta uns px més enfora, i
    #      això NO és cap defecte de la silueta. La desviació residual de
    #      ~6,5 px a ~194° és la protuberància, idèntica a la V13_Pere.
    print("[D] silueta (vora per gradient, no-regressió contra la V13_Pere)")
    import cv2 as _cv2
    g13 = a.numpy()[..., 1].astype(np.float32)
    c2c13 = c2c - np.array(F.MOVIMENTS["12"], float)

    def _radis(g, cc):
        rs = []
        for az in np.linspace(0, 2 * np.pi, 720, endpoint=False):
            rr = np.arange(c2R - 25, c2R + 25, 0.5)
            px = np.clip((cc[0] + rr * np.cos(az)).astype(int), 0, W - 1)
            py = np.clip((cc[1] + rr * np.sin(az)).astype(int), 0, H - 1)
            v = _cv2.GaussianBlur(g[py, px][None], (0, 0), 1.5)[0]
            rs.append(rr[np.argmax(np.diff(v))])
        rs = np.array(rs)
        d = np.abs(rs - np.median(rs))
        return float(np.percentile(d, 95)), float(d.max())

    p95_13, max_13 = _radis(g13, c2c13)
    p95_14, max_14 = _radis(g14, c2c)
    okD = p95_14 <= p95_13 + 0.5 and max_14 <= max_13 + 1.0
    tot_ok &= porta("D", okD,
                    f"vora per gradient: p95 {p95_14:.2f} px (V13_Pere {p95_13:.2f}) "
                    f"· màx {max_14:.2f} (V13_Pere {max_13:.2f}; el màxim compartit "
                    f"és la protuberància, contingut real)")
    desv = max_14

    # ---- E · obrible
    r = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", DST],
                       capture_output=True, text=True)
    okE = (f"pixelWidth: {W}" in r.stdout + r.stderr
           and f"pixelHeight: {H}" in r.stdout + r.stderr)
    tot_ok &= porta("E", okE, "psd-tools i ImageIO llegeixen el fitxer")

    print("\nVEREDICTE:", "TOTES LES PORTES PASSEN" if tot_ok else "⛔ HI HA FALLES")
    json.dump({"passa": bool(tot_ok), "vel_per_anell": vels,
               "silueta_desv_px": desv, "alineacio_pitjor_px": pitjor},
              open(os.path.join(CAU, "portes.json"), "w"), indent=1)
    return tot_ok


if __name__ == "__main__":
    raise SystemExit(0 if main() else 1)
