"""V21 (cinquena ronda): la capa EARTHSHINE monocroma, disc sencer.

Itera sobre la quarta per ordre de Pere (disc massa petit; línies verticals
de color): estructura MONOCROMA del canal G (lliçó d'Earthshine_FINAL: el
residu del canal R és 3× pitjor i el color amplificat és soroll), disc fins
al limbe, ratlles del re-mostreig Bayer restades. Canònic: research/126.
"""
from __future__ import annotations
import json, os, subprocess, sys, time
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v21")
CAU18 = os.path.join(AQUI, "cau_v18")
CAU19 = os.path.join(AQUI, "cau_v19")
CAUF = os.path.join(CAU19, "fons")
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "encaix_sony"))
B = "/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/"
SRC, DST = B + "CapesTotalsV19.psb", B + "CapesTotalsV21.psb"
T0 = time.time()


def marca(t):
    print(f"[{time.time()-T0:7.1f}s] {t}", flush=True)


def main():
    from psd_tools import PSDImage
    from psd_tools.constants import Compression, BlendMode
    from psd_tools.psd.image_data import ImageData
    from psb_utils import add_pixel_layer, add_mask16, finalize_lr16
    from v21_munta import canal_cru

    psd = PSDImage.open(SRC)
    d_, v_ = psd.depth, psd.version
    capes = list(psd)
    assert len(capes) == 14
    W, H = psd.width, psd.height
    m_sony = canal_cru(capes[12], -2, d_, v_).astype(np.float32) / 65535.0
    m_fons = canal_cru(capes[13], -2, d_, v_).astype(np.float32) / 65535.0
    marca("màscares vives decodificades")

    Ep = np.load(f"{CAU}/capa_es3_px.npy"); Em = np.load(f"{CAU}/capa_es3_msk.npy")
    emd = json.load(open(f"{CAU}/capa_es3_meta.json"))
    ey, ex = emd["pos"]
    Sp = np.load(f"{CAU}/capa_est_px.npy"); Sm = np.load(f"{CAU}/capa_est_msk.npy")
    reb = json.load(open(f"{CAU}/earthshine2_rebut.json"))
    pur = json.load(open(f"{CAU}/purga_rebut.json"))
    rL = {"r": reb["r_lroc"], "z": reb["z"]}
    marca("capes carregades")

    tb = psd._record.layer_and_mask_information.tagged_blocks
    for kk in list(tb.keys()):
        kb = kk.value if hasattr(kk, "value") else kk
        if kb not in (b"Lr16", b"Mt16"):
            del tb[kk]
    nom_e = (f"EARTHSHINE · DOS TRENS · monocroma (G) · Vixen 3×10 s + Sony "
             f">1 s a la LLUNA · vel restat · r={rL['r']:.3f} amb LROC NASA "
             f"({rL['z']:.1f}σ) · contrast real {reb['amplitud_pct']:.2f} % "
             f"amplificat ×{emd['amplificacio_contrast']:.0f} DECLARAT (V21)")
    ce = add_pixel_layer(psd, Ep, nom_e, top=int(ey), left=int(ex),
                         blend=BlendMode.NORMAL, compression=Compression.ZIP)
    add_mask16(ce, Em, top=int(ey), left=int(ex))
    nom_s = (f"ESTRELLES · {pur['n']} del catàleg (puresa {pur['puresa_pct']:.0f} % "
             "mesurada) · llum REAL de l'apilat, cap disc dibuixat · "
             "Linear Dodge (V21)")
    cs = add_pixel_layer(psd, Sp, nom_s, top=0, left=0,
                         blend=BlendMode.LINEAR_DODGE, compression=Compression.ZIP)
    add_mask16(cs, Sm, top=0, left=0)
    finalize_lr16(psd)
    marca("capes inserides i Lr16 reconstruït")

    S12r = np.load(os.path.join(CAU19, "sony_v18_rgb16.npy"), mmap_mode="r")
    V16r = np.load(os.path.join(CAU18, "vixen_sota_rgb16.npy"), mmap_mode="r")
    A8r = np.load(os.path.join(CAU18, "vixen_sota_alfa8.npy"), mmap_mode="r")
    Bf = np.load(os.path.join(CAUF, "B_v19_rgb16.npy"), mmap_mode="r")
    a_v = np.asarray(A8r, np.float32) / 255.0
    alfaT = m_sony + a_v * (1 - m_sony)
    alfaT = alfaT + m_fons * (1 - alfaT)
    Smf = Sm.astype(np.float32) / 65535.0
    mef = np.zeros((H, W), np.float32)
    he, we = Em.shape
    mef[ey:ey + he, ex:ex + we] = Em.astype(np.float32) / 65535.0
    plans = []
    for ch in range(3):
        C = (np.asarray(S12r[..., ch], np.float32) * m_sony
             + np.asarray(V16r[..., ch], np.float32) * a_v * (1 - m_sony))
        F = C * (1 - m_fons) + np.asarray(Bf[..., ch], np.float32) * m_fons
        del C
        Ef = np.zeros((H, W), np.float32)
        Ef[ey:ey + he, ex:ex + we] = Ep[..., ch]
        F = F * (1 - mef) + Ef * mef
        del Ef
        F = F + Sp[..., ch].astype(np.float32) * Smf
        F = F + (1.0 - alfaT) * 65535.0
        plans.append(np.clip(F + 0.5, 0, 65535).astype(">u2").tobytes())
        del F
        marca(f"fusionada: canal {ch}")
    if psd._record.header.channels == 4:
        plans.append(np.clip(np.rint(alfaT * 65535.0), 0, 65535)
                     .astype(">u2").tobytes())
    idata = ImageData(compression=Compression.RAW)
    idata.set_data(plans, psd._record.header)
    psd._record.image_data = idata
    if getattr(psd, "_updated", False):
        psd._updated = False
    del plans
    marca("desant…")
    psd.save(DST)
    marca(f"{DST} · {os.path.getsize(DST)/1e9:.2f} GB")

    p2 = PSDImage.open(DST)
    c2 = list(p2)
    assert (p2.width, p2.height) == (W, H) and len(c2) == 16
    src2 = PSDImage.open(SRC)
    assert list(src2)[0]._channels[1].data == c2[0]._channels[1].data
    print("    fidelitat: capa 0 byte a byte ✓", flush=True)
    r = subprocess.run([os.path.join(AQUI, "porta_photoshop.sh"), DST],
                       capture_output=True, text=True, timeout=5400)
    print("    Photoshop diu:", (r.stdout + r.stderr).strip(), flush=True)
    json.dump({"capes": [ly.name for ly in c2], "bytes": os.path.getsize(DST),
               "earthshine": {"r_lroc": rL["r"], "z": rL["z"],
                              "contrast_pct": reb["amplitud_pct"],
                              "amplificacio": emd["amplificacio_contrast"],
                              "monocroma": True, "pesos": reb["pesos"]},
               "estrelles": {"n": pur["n"], "puresa": pur["puresa_pct"]}},
              open(f"{CAU}/rebut_v21e.json", "w"), indent=1, ensure_ascii=False)
    marca("fet")


if __name__ == "__main__":
    main()
