"""Posa totes les imatges de «Projecte photoshop/2-Filtres» al llenç E de 7648×5353 (el de CapesInteriors,
CapesExteriors i Aplicant_Filtres), on cadascuna cau de veritat, i les lliura de dues maneres:

  1. un PSB de capes, `Filtres_alineats_7648x5353.psb`, amb la fusionada d'Aplicant_Filtres a baix i cada imatge
     com a capa al seu lloc (rectangle propi, transparent fora), amagada, amb el mode de fusió que tenia al fitxer
     de Pere (Overlay als filtres radials; Linear Light al PASSALT del pipeline, que és com es fa servir);
  2. un TIFF pla de 7648×5353 per imatge a `alineades_7648x5353/`, per «Enganxa al lloc» (fora de la font: gris
     de la vora per a filtres i renders, negre per a les capes base).

Col·locacions (mesurades per correlació creuada del passa-alt contra la fusionada d'Aplicant_Filtres, vegeu
mesura_alineacio3.py):
  - filtres_Tangencials.tif (6961×4641, coordenades de CapesInteriors abans de redimensionar): E = font + (456, 462), exacte;
  - filtres_radials.tif (6748×4553, el llenç antic de Pere): E = font + (599, 549), exacte;
  - reixa del pipeline Corona_HDR_Vixen (6958×4638, Sol a (3479, 2319)): E = P + (542,6, 418,5) ± 0,1 px → es
    remostreja (cúbic) el subpíxel; el PASSALT_FORT és el retall RETALL de P (comença a (40, 85)) → E = retall + (582,6, 503,5).
    (Coherent amb la cadena documentada: P → reixa DNG (84,89, −44,34) mesurat aquí (85,50, −44,02), i DNG → E (457, 462,7).)
Només lectura sobre les fonts. RGB 16 bits amb el perfil Display P3 d'Aplicant_Filtres (els números no canvien).
"""
import os, sys, json, time, struct, numpy as np, tifffile, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.expanduser("~/Downloads/Eclipse 2026/research/tools/encaix_sony"))
from capes_tiff import TiffCapes
from psd_tools.constants import BlendMode, Compression, Resource
from psd_tools.psd.image_resources import ImageResource
from psb_utils import new_psb, add_pixel_layer, set_merged, finalize_lr16

D = os.path.expanduser("~/Desktop/Eclipse 2026/Projecte photoshop/2-Filtres/")
BASE = os.path.join(D, "Recursos", "Base", "Aplicant_Filtres.tif")
CHV = os.path.expanduser("~/Desktop/Eclipse 2026/Derivats/Vixen/Corona_HDR_Vixen/")
OUT_TIF = os.path.join(D, "Recursos", "Alineats", "alineades_7648x5353"); os.makedirs(OUT_TIF, exist_ok=True)
OUT_PSB = os.path.join(D, "Filtres_alineats_7648x5353.psb")
SP = os.path.dirname(os.path.abspath(__file__))
W, H = 7648, 5353
P2E = (542.6, 418.5)          # reixa P del pipeline → E (mesurat: detall/radial/PASSALT contra E i via el DNG 03_1s; ±0,1 px)
RETALL_XY = (40, 85)          # el PASSALT és P[85:4596, 40:6831]
NOMES = sys.argv[1:]          # opcional: 'tif' o 'psb' per fer-ne només un
t0 = time.time()
def log(*a): print(f"[{time.time()-t0:5.0f} s]", *a, flush=True)

with tifffile.TiffFile(BASE) as t:
    ICC = bytes(t.pages[0].tags[34675].value)
log("perfil ICC d'Aplicant_Filtres:", len(ICC), "bytes")

def u16(a): return np.clip(np.rint(a * 65535.0), 0, 65535).astype(np.uint16)

def resample(src, ox, oy, interp=cv2.INTER_CUBIC):
    """src float32 (h, w[, 3]) a la reixa P; el posa a E amb el desplaçament (ox, oy) subpíxel.
    Retorna (img, left, top): img cobreix E[top:top+h+1, left:left+w+1] i s'ha mostrejat a (X−ox, Y−oy)."""
    h, w = src.shape[:2]
    left, top = int(np.floor(ox)), int(np.floor(oy))
    fx, fy = ox - left, oy - top                     # 0 ≤ f < 1: E(left+i) ↔ src(i − fx)
    W2, H2 = w + 1, h + 1
    M = np.array([[1, 0, fx], [0, 1, fy]], np.float32)   # dst(x) = src(x − fx)
    out = cv2.warpAffine(src, M, (W2, H2), flags=interp, borderMode=cv2.BORDER_REPLICATE)
    return out, left, top

def vora_mediana(a):
    """valor de farciment: mediana del marc exterior de 5 px"""
    m = np.concatenate([a[:5].reshape(-1, a.shape[-1]) if a.ndim == 3 else a[:5].ravel(),
                        a[-5:].reshape(-1, a.shape[-1]) if a.ndim == 3 else a[-5:].ravel(),
                        a[:, :5].reshape(-1, a.shape[-1]) if a.ndim == 3 else a[:, :5].ravel(),
                        a[:, -5:].reshape(-1, a.shape[-1]) if a.ndim == 3 else a[:, -5:].ravel()])
    return np.median(m, axis=0)

def desa_tif(nom, img16, left, top, fill):
    """img16 uint16 (h, w, 3) posat a E[top:, left:] sobre un llenç ple de `fill` (uint16 per canal)"""
    llenc = np.empty((H, W, 3), np.uint16); llenc[...] = np.asarray(fill, np.uint16)
    h, w = img16.shape[:2]
    y0, x0 = max(top, 0), max(left, 0); y1, x1 = min(top + h, H), min(left + w, W)
    llenc[y0:y1, x0:x1] = img16[y0 - top:y1 - top, x0 - left:x1 - left]
    p = os.path.join(OUT_TIF, nom + ".tif")
    tifffile.imwrite(p, llenc, photometric="rgb", compression="adobe_deflate", predictor=True,
                     resolution=(300, 300), resolutionunit="INCH",
                     extratags=[(34675, 7, len(ICC), ICC, False)],
                     description=f"{nom}: al llenc 7648x5353 de CapesInteriors/CapesExteriors (E); font a E[{top}:{top+h}, {left}:{left+w}]; "
                                 f"fora de la font: farciment constant. Perfil Display P3 (els valors no s'han convertit).")
    log(f"  → {p}  ({os.path.getsize(p)/1e6:.0f} MB)")
    return p

# ------------------------------------------------------------------ fonts
capes = []      # (nom_capa, img16 (h,w,3), left, top, blend, fill16, nom_tif, nota)
log("llegeixo la fusionada d'Aplicant_Filtres (base, E)")
base = tifffile.imread(BASE)
assert base.shape == (H, W, 3) and base.dtype == np.uint16

T = TiffCapes(D + "filtres_Tangencials.tif")
noms_T = {0: "3", 1: "2", 2: "1", 3: "b", 4: "a"}
log("filtres_Tangencials.tif → capes 0 (=1=2), 3 (b), 4 (a) a E + (456, 462)")
c3 = T.rgb(0)
capes.append(("Tangencials · 1 = 2 = 3 (base, disc farcit; les tres capes són byte a byte iguals) · E+(456,462)",
              c3, 456, 462, BlendMode.NORMAL, (0, 0, 0), "filtres_Tangencials_1-2-3_base_E7648", "base"))
for k, nm in ((3, "b"), (4, "a")):
    a = T.rgb(k)
    capes.append((f"Tangencials · {nm} (pas alt tangencial, signe INVERTIT: blur − base) · E+(456,462)",
                  a, 456, 462, BlendMode.NORMAL, tuple(int(v) for v in vora_mediana(a)), f"filtres_Tangencials_{nm}_E7648", "filtre"))
del T

R = TiffCapes(D + "filtres_radials.tif")
log("filtres_radials.tif → Background, filtre radial B, filtre radial A a E + (599, 549)")
bg = R.rgb(0)
capes.append(("Radials · Background (base) · E+(599,549)", bg, 599, 549, BlendMode.NORMAL, (0, 0, 0),
              "filtres_radials_Background_E7648", "base"))
b_ = R.rgb(1)
capes.append(("Radials · filtre radial B (Overlay al fitxer de Pere; signe normal) · E+(599,549)", b_, 599, 549,
              BlendMode.OVERLAY, tuple(int(v) for v in vora_mediana(b_)), "filtres_radials_filtre_radial_B_E7648", "filtre"))
a_ = R.rgb(2)
capes.append(("Radials · filtre radial A (Overlay al fitxer de Pere; signe INVERTIT) · E+(599,549)", a_, 599, 549,
              BlendMode.OVERLAY, tuple(int(v) for v in vora_mediana(a_)), "filtres_radials_filtre_radial_A_E7648", "filtre"))
del R

log("corona_vixen_PASSALT_FORT.tif (retall P a (40,85)) → remostreig a E + (582,6, 503,5)")
pas = tifffile.imread(D + "corona_vixen_PASSALT_FORT.tif").astype(np.float32) / 65535.0
img, left, top = resample(pas, P2E[0] + RETALL_XY[0], P2E[1] + RETALL_XY[1])
capes.append(("corona_vixen_PASSALT_FORT (pipeline, gris 50 % + D; Linear Light) · reixa P → E+(582,6, 503,5) remostrejat",
              u16(img), left, top, BlendMode.LINEAR_LIGHT, tuple(int(v) for v in u16(vora_mediana(pas))),
              "corona_vixen_PASSALT_FORT_E7648", "filtre"))
del pas, img

log("corona_vixen_detall a 16 bits (vis_luminancia.npy + disc 0,10 = detall.png a l'arrodoniment) → E + (542,6, 418,5)")
mix = np.load(CHV + "vis_luminancia.npy")
hdr = np.load(CHV + "hdr_vixen_countss.npy", mmap_mode="r")
valid = np.isfinite(hdr[..., 1]) | np.isfinite(hdr[..., 0])
det = np.where(~valid, 0.10, mix).astype(np.float32); del mix, valid, hdr
img, left, top = resample(det, *P2E)
img3 = np.repeat(u16(img)[..., None], 3, -1)
capes.append(("corona_vixen_detall (pipeline, 16 bits des de vis_luminancia.npy) · reixa P → E+(542,6, 418,5) remostrejat",
              img3, left, top, BlendMode.NORMAL, tuple([int(u16(vora_mediana(det)))] * 3), "corona_vixen_detall_16b_E7648", "render"))
del det, img, img3

log("corona_vixen_radial.png (8 bits) → E + (542,6, 418,5)")
rad = cv2.imread(D + "corona_vixen_radial.png", cv2.IMREAD_UNCHANGED)
if rad.ndim == 3: rad = rad[..., ::-1].mean(-1)
rad = rad.astype(np.float32) / 255.0
img, left, top = resample(rad, *P2E)
img3 = np.repeat(u16(img)[..., None], 3, -1)
capes.append(("corona_vixen_radial (pipeline, 8 bits) · reixa P → E+(542,6, 418,5) remostrejat",
              img3, left, top, BlendMode.NORMAL, tuple([int(u16(vora_mediana(rad)))] * 3), "corona_vixen_radial_E7648", "render"))
del rad, img, img3

# ------------------------------------------------------------------ TIFF plans
registre = []
if not NOMES or "tif" in NOMES:
    log("TIFF plans a", OUT_TIF)
    for nom_capa, img16, left, top, blend, fill, nom_tif, tipus in capes:
        p = desa_tif(nom_tif, img16, left, top, fill)
        registre.append(dict(capa=nom_capa, tif=os.path.basename(p), left=left, top=top, mida=[int(img16.shape[1]), int(img16.shape[0])],
                             blend=str(blend), farciment=[int(v) for v in fill], tipus=tipus))

# ------------------------------------------------------------------ PSB
if not NOMES or "psb" in NOMES:
    log("PSB", OUT_PSB)
    psd = new_psb(W, H, icc_bytes=ICC)
    # resolució 300 ppi (recurs 1005: hRes fixed 16.16, unitat 1 = px/polzada, amplada 1 = polzades; el mateix en vertical)
    psd._record.image_resources[Resource.RESOLUTION_INFO] = ImageResource(
        signature=b"8BIM", key=Resource.RESOLUTION_INFO, name="", data=struct.pack(">IHHIHH", 300 << 16, 1, 1, 300 << 16, 1, 1))
    add_pixel_layer(psd, base, "Base · Aplicant_Filtres.tif (fusionada; és el llenç E)", top=0, left=0,
                    blend=BlendMode.NORMAL, visible=True, compression=Compression.ZIP_WITH_PREDICTION)
    log("  capa base")
    for nom_capa, img16, left, top, blend, fill, nom_tif, tipus in capes:
        add_pixel_layer(psd, img16, nom_capa, top=top, left=left, blend=blend, visible=False,
                        compression=Compression.ZIP_WITH_PREDICTION)
        log("  capa", nom_capa[:60], "…", "bbox", (left, top, left + img16.shape[1], top + img16.shape[0]))
    finalize_lr16(psd)
    set_merged(psd, base, compression=Compression.RAW)
    psd.save(OUT_PSB)
    log(f"  → {OUT_PSB}  ({os.path.getsize(OUT_PSB)/1e9:.2f} GB)")

json.dump(dict(llenc=[W, H], P2E=list(P2E), retall_passalt=list(RETALL_XY), capes=registre or
               [dict(capa=c[0], left=c[2], top=c[3], mida=[int(c[1].shape[1]), int(c[1].shape[0])], blend=str(c[4]), tipus=c[7]) for c in capes]),
          open(os.path.join(SP, "col_locacions.json"), "w"), indent=1, ensure_ascii=False)
log("fet")
