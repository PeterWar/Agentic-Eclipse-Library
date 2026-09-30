"""Refà el PSB a partir dels TIFF lineals ja escrits, amb una corba que serveixi.

⚠️ Per què la primera no servia: amb exposicions de 8 i 10,3 s, el rang útil d'un
fotograma sol va del CEL (~9e-9 B/B☉) a la SATURACIÓ (4,27e-8 a la Vixen, 2,25e-8 a la
Sony) — un factor de només 4,7. Una corba ancorada al p99,5 hi aplana tot. Ara:
  · s'hi resta el CEL de cada capa (el seu propi p1) i s'escala a la seva saturació;
  · el color es neutralitza amb el quocient R/G i B/G mesurat a 1,5–2,5 R☉ de cada capa
    (la corona és dispersió Thomson, o sigui acromàtica: no és una tria estètica);
  · corba log declarada al MANIFEST, i els TIFF lineals de al costat no es toquen.
La saturació és REAL i no s'hi pot fer res amb aquests fotogrames: el limbe hi és cremat.
"""
import os, sys, json, math, time, numpy as np, cv2, tifffile
sys.path.insert(0, os.path.expanduser("~/Downloads/Eclipse 2026/research/tools/encaix_sony"))
from psd_tools.constants import BlendMode, Compression
from psb_utils import new_psb, add_pixel_layer, set_merged, finalize_lr16

OUT = os.path.expanduser("~/Downloads/Eclipse 2026/output/llenc_prova_dos_trens_20260823")
m = json.load(open(os.path.join(OUT, "MANIFEST.json")))
W, H = m["llenc"]; ESC = m["escala_arcsec_px"]; RS = m["rsol_arcsec_del_dia"]; cx, cy = m["sol"]
K = 300.0                                     # duresa de la corba log
t0 = time.time()
def log(*a): print(f"[{time.time()-t0:6.1f}s]", *a, flush=True)

capes, det = [], []
for c in m["capes"]:
    log(c["fitxer"], "…")
    a = tifffile.imread(os.path.join(OUT, f"{c['fitxer']}_llencComu_BBsol_float32.tif")).astype(np.float32)
    x0, y0, x1, y1 = c["bbox"]
    Y, X = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    R = np.hypot(X - cx, Y - cy) * ESC / RS
    del X, Y
    ok = (a.sum(2) > 0) & np.isfinite(a[:, :, 1])
    an = ok & (R > 1.5) & (R < 2.5)
    # ⚠️ L'ORDRE IMPORTA. El cel i la corona NO tenen el mateix color: la corona és
    # dispersió Thomson i per tant acromàtica, i el cel és blau. Si es resta un sol
    # `cel` mesurat al verd als tres canals, queda una dominant (ho vaig fer i sortia
    # cian). Primer es resta el cel PER CANAL —així el cel va a negre— i només llavors
    # es neutralitza la corona.
    cel = [float(np.percentile(a[:, :, i][ok], 1.0)) for i in range(3)]
    for i in range(3):
        a[:, :, i] -= np.float32(cel[i])
    g = a[:, :, 1]
    rg = float(np.median(a[:, :, 0][an] / np.maximum(g[an], 1e-30)))
    bg = float(np.median(a[:, :, 2][an] / np.maximum(g[an], 1e-30)))
    a[:, :, 0] /= np.float32(rg); a[:, :, 2] /= np.float32(bg)          # corona neutra
    top = float(np.percentile(g[ok], 99.99))
    u = np.clip(a / max(top, 1e-30), 0.0, 1.0)
    v = np.log1p(u * K) / math.log1p(K)
    u16 = (v * 65535.0 + 0.5).astype(np.uint16)
    mask8 = (ok * 255).astype(np.uint8)
    nom = next(x["nom"] for x in m["capes"] if x["fitxer"] == c["fitxer"])
    capes.append((nom, u16, mask8, x0, y0))
    det.append(dict(fitxer=c["fitxer"], neutralitzacio_RG=round(rg, 4), neutralitzacio_BG=round(bg, 4),
                    cel_BBsol_RGB=[float(f"{v:.5g}") for v in cel], blanc_BBsol=top,
                    frac_al_blanc=round(float((g[ok] >= top * 0.999).mean()), 5)))
    log(f"  cel RGB {cel[0]:.2e}/{cel[1]:.2e}/{cel[2]:.2e}  blanc {top:.3e}  R/G {rg:.3f} B/G {bg:.3f}  "
        f"al blanc {100*det[-1]['frac_al_blanc']:.2f} %")
    del a, g, R, ok, an, u, v

log("PSB…")
psd = new_psb(W, H)
base = np.zeros((H, W, 3), np.uint16)
add_pixel_layer(psd, base, "Fons · llenc comu, nord amunt, Sol al centre", top=0, left=0,
                blend=BlendMode.NORMAL, visible=True, compression=Compression.ZIP_WITH_PREDICTION)
for nom, u16, mask8, x0, y0 in capes:
    add_pixel_layer(psd, u16, nom, top=y0, left=x0, mask8=mask8, blend=BlendMode.NORMAL,
                    visible=True, compression=Compression.ZIP_WITH_PREDICTION)
    log("  capa", nom[:66])
finalize_lr16(psd)
set_merged(psd, base, compression=Compression.ZIP_WITH_PREDICTION)
p = os.path.join(OUT, "Prova_Vixen10s_sobre_Sony8s.psb")
psd.save(p)
log(f"  → {p}  ({os.path.getsize(p)/1e9:.2f} GB)")
m["corba"] = {"formula": "per canal: log1p(clip((B/Bsol - cel_c)/k_c / blanc, 0, 1) * %g) / log1p(%g), amb k_R=R/G i k_B=B/G a 1,5-2,5 Rsol" % (K, K),
              "per_capa": det, "nota": "cel i sat son PER CAPA; els TIFF lineals de al costat no porten corba"}
json.dump(m, open(os.path.join(OUT, "MANIFEST.json"), "w"), indent=1, ensure_ascii=False)
log("fet")
