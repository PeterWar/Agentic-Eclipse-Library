"""Llenç de prova: els tres 10,3 s de la Vixen damunt les dues 8 s vàlides de la Sony.

Ordre de Pere, 23-08-2026. Serveix per veure amb els ulls el que research/96 diu amb
números: que el camp de la Sony va caure 750 px a mig de la totalitat i que els dos
fotogrames de 8 s són a apuntaments diferents.

MARC COMÚ, i és el que research/96 §C.1 declara (rectificat el 23-08 a la tarda):
pla tangent NORD AMUNT centrat al Sol, a l'escala fina (la de la Vixen, 2,1495 "/px).
⚠️ Nord amunt vol dir que el llenç és VERTICAL: pa_north de la Sony val 90,27°, o sigui
que el nord cau a 0,27° de l'eix llarg del sensor i posar-lo amunt gira la Sony dreta.

REGISTRE. Cap fotograma no es registra aquí: es col·loca amb la geometria ja mesurada.
  Sony  · sol del fotograma = sol de la referència (final_solution.sony_radial) + (dx,dy)
          de registre_v3.json. DSC06993 ÉS la referència (desplaçament 0,06 px).
  Vixen · sol_x, sol_y de manifest.csv, un per fotograma (ajust del limbe lunar).

FOTOMETRIA. Tots dos trens passen a B/B☉ amb els factors de research/75 §5.2, o sigui
que les capes són comparables entre elles. El PSB porta una corba declarada i el JSON
la fórmula per desfer-la; els TIFF lineals van al costat.
"""
import os, sys, csv, json, math, time
import numpy as np, cv2, rawpy, tifffile
sys.path.insert(0, os.path.expanduser("~/Downloads/Eclipse 2026/research/tools/encaix_sony"))
from psd_tools.constants import BlendMode, Compression
from psb_utils import new_psb, add_pixel_layer, set_merged, finalize_lr16

HOME = os.path.expanduser("~")
DESK = os.path.join(HOME, "Desktop", "Eclipse 2026")
SOL = json.load(open(os.path.join(DESK, "Derivats/Astrometria/Estrelles/Resultats_acceptacio_2026-08-17/final_solution.json")))
MANI = os.path.join(DESK, "Derivats/Vixen/Corona_HDR_Vixen/manifest.csv")
REG = json.load(open(os.path.join(HOME, "Downloads/Eclipse 2026/output/salt_muntura_20260823/registre_v3_sony.json")))
DIR_SONY = os.path.join(DESK, "300mm A7RIIIA")
DIR_VIX = os.path.join(DESK, "Vixen R6III/Vixen Fase totalitat")
OUT = os.path.join(HOME, "Downloads/Eclipse 2026/output/llenc_prova_dos_trens_20260823")
PREV = os.path.join(DESK, "IA/output/llenc_prova_dos_trens_20260823")

ESC = 2.1495                      # "/px del llenç comú (la de la Vixen)
RSOL_DIA = 947.068                # radi solar aparent d'aquell dia (suns.json), no el mitjà
FB_SONY, FB_VIX = 1.134e-11, 2.772e-11     # research/75 §5.2, B/B☉ per ADU/s
NEGRE = 512.0                     # pedestal pla als dos cossos (research/71: el de metadata és fals)
MARGE = 60

t0 = time.time()
def log(*a): print(f"[{time.time()-t0:6.1f}s]", *a, flush=True)

def afi(sun_xy, pa_deg, esc_frame, centre):
    """frame px -> llenç px. Gira perquè el nord quedi amunt i escala a ESC."""
    pa = math.radians(pa_deg)
    # PA = atan2(vx, -vy): 0 = amunt, 90 = a la dreta. Per posar el nord amunt cal
    # portar la direcció que ara és a PA = pa_north fins a PA = 0.
    R = np.array([[math.cos(pa), math.sin(pa)],
                  [-math.sin(pa), math.cos(pa)]], float)
    A = (esc_frame / ESC) * R
    t = np.array(centre, float) - A @ np.array(sun_xy, float)
    return np.hstack([A, t[:, None]]).astype(np.float64)

def demosaic(path):
    with rawpy.imread(path) as r:
        a = r.raw_image_visible.astype(np.float32) - NEGRE
        pat = "".join("RGBG"[int(c)] for c in r.raw_pattern.ravel())
        wl = float(r.white_level)
        sat = (r.raw_image_visible >= wl * 0.985)
        a = np.clip(a, 0, None)
    codi = {"RGGB": cv2.COLOR_BayerBG2RGB, "BGGR": cv2.COLOR_BayerRG2RGB,
            "GRBG": cv2.COLOR_BayerGB2RGB, "GBRG": cv2.COLOR_BayerGR2RGB}[pat]
    m = float(a.max()) or 1.0
    rgb = cv2.cvtColor((a / m * 65535.0).astype(np.uint16), codi).astype(np.float32) * (m / 65535.0)
    satd = cv2.dilate(sat.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    return rgb, satd, pat, wl

# ---------------------------------------------------------------- fotogrames
vix = {r["nom"].replace(".CR3", ""): r for r in csv.DictReader(open(MANI))}
FR = []
for n in ("572A2982", "572A2983", "572A2984"):
    m = vix[n]
    FR.append(dict(tren="vixen", nom=n, fitxer=os.path.join(DIR_VIX, n + ".CR3"),
                   sun=(float(m["sol_x"]), float(m["sol_y"])), pa=SOL["r6_radial"]["pa_north"],
                   esc=SOL["r6_radial"]["scale"], exp=float(m["exp_s"]), fb=FB_VIX,
                   nota=f"t_rel_C2 {float(m['t_rel_c2']):+.1f} s"))
s_ref = SOL["sony_radial"]
for n, et in (("DSC06993", "apuntament NOMINAL"), ("DSC06987", "apuntament DESPLACAT")):
    d = REG["registre"][n]
    FR.append(dict(tren="sony", nom=n, fitxer=os.path.join(DIR_SONY, n + ".ARW"),
                   sun=(s_ref["sun_x"] + d["dx"], s_ref["sun_y"] + d["dy"]), pa=s_ref["pa_north"],
                   esc=s_ref["scale"], exp=8.0, fb=FB_SONY,
                   nota=f"{et}; desplacament ({d['dx']:+.1f},{d['dy']:+.1f}) px"))

# ---------------------------------------------------------------- mida del llenç
log("mida del llenç a partir del perímetre de tots els fotogrames…")
pts = []
for f in FR:
    with rawpy.imread(f["fitxer"]) as r: h, w = r.raw_image_visible.shape
    f["hw"] = (h, w)
    A = afi(f["sun"], f["pa"], f["esc"], (0.0, 0.0))
    c = np.array([[0, 0], [w, 0], [w, h], [0, h]], float)
    pts.append((A[:, :2] @ c.T).T + A[:, 2])
P = np.vstack(pts)
Wc = int(2 * math.ceil(np.abs(P[:, 0]).max() + MARGE))
Hc = int(2 * math.ceil(np.abs(P[:, 1]).max() + MARGE))
CEN = (Wc / 2.0, Hc / 2.0)
log(f"  llenç {Wc} x {Hc} px = {Wc*Hc/1e6:.1f} Mpx  "
    f"({Wc*ESC/RSOL_DIA:.2f} x {Hc*ESC/RSOL_DIA:.2f} R☉, Sol al centre)")

os.makedirs(OUT, exist_ok=True); os.makedirs(PREV, exist_ok=True)
man = dict(creat=time.strftime("%Y-%m-%dT%H:%M:%S"), llenc=[Wc, Hc], escala_arcsec_px=ESC,
           rsol_arcsec_del_dia=RSOL_DIA, nord="amunt", sol=[CEN[0], CEN[1]],
           unitats="B/Bsol (research/75 §5.2)", negre=NEGRE, capes=[])

# ---------------------------------------------------------------- capes
REF = None
capes = []
for f in FR:
    log(f"{f['nom']} ({f['tren']}, {f['exp']} s)…")
    rgb, sat, pat, wl = demosaic(f["fitxer"])
    h, w = rgb.shape[:2]
    rgb *= np.float32(f["fb"] / f["exp"])                     # -> B/B☉
    A = afi(f["sun"], f["pa"], f["esc"], CEN)
    c = np.array([[0, 0], [w, 0], [w, h], [0, h]], float)
    q = (A[:, :2] @ c.T).T + A[:, 2]
    x0, y0 = int(math.floor(q[:, 0].min())), int(math.floor(q[:, 1].min()))
    x1, y1 = int(math.ceil(q[:, 0].max())), int(math.ceil(q[:, 1].max()))
    x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(Wc, x1), min(Hc, y1)
    Al = A.copy(); Al[0, 2] -= x0; Al[1, 2] -= y0
    out = cv2.warpAffine(rgb, Al, (x1 - x0, y1 - y0), flags=cv2.INTER_LANCZOS4,
                         borderMode=cv2.BORDER_CONSTANT, borderValue=0.0)
    alfa = cv2.warpAffine(np.ones((h, w), np.float32), Al, (x1 - x0, y1 - y0),
                          flags=cv2.INTER_NEAREST, borderValue=0.0)
    satw = cv2.warpAffine(sat.astype(np.float32), Al, (x1 - x0, y1 - y0),
                          flags=cv2.INTER_NEAREST, borderValue=0.0) > 0.5
    del rgb, sat
    if REF is None:
        m = (alfa > 0.5) & np.isfinite(out[:, :, 1])
        REF = float(np.percentile(out[:, :, 1][m & (out[:, :, 1] > 0)], 99.5))
        man["corba"] = {"formula": "log1p(clip(B/Bsol / ref, 0, 1) * 40) / log1p(40)", "ref_BBsol": REF}
        log(f"  referència de to = {REF:.4e} B/B☉ (p99,5 del verd de {f['nom']})")
    g = np.log1p(np.clip(out / REF, 0, 1) * 40.0) / math.log1p(40.0)
    u16 = (np.clip(g, 0, 1) * 65535.0 + 0.5).astype(np.uint16)
    mask8 = (np.clip(alfa, 0, 1) * 255).astype(np.uint8)
    nom = f"{f['tren'].upper()} {f['nom']} · {f['exp']:g} s · {f['nota']}"
    capes.append((nom, u16, mask8, x0, y0))
    tifffile.imwrite(os.path.join(OUT, f"{f['nom']}_llencComu_BBsol_float32.tif"),
                     (out * (alfa > 0.5)[:, :, None]).astype(np.float32))
    man["capes"].append(dict(nom=nom, fitxer=f["nom"], tren=f["tren"], exposicio_s=f["exp"],
                             sol_al_fotograma=[round(v, 3) for v in f["sun"]], pa_north=f["pa"],
                             escala=f["esc"], bbox=[x0, y0, x1, y1], bayer=pat, white_level=wl,
                             px_saturats=int(satw.sum()), nota=f["nota"]))
    log(f"  bbox ({x0},{y0})–({x1},{y1})  {x1-x0}x{y1-y0}  saturats {int(satw.sum())}")
    del out, alfa, satw, g

# ---------------------------------------------------------------- PSB
log("PSB…")
psd = new_psb(Wc, Hc)
base = np.zeros((Hc, Wc, 3), np.uint16)
add_pixel_layer(psd, base, "Fons (llenc comu, nord amunt, Sol al centre)", top=0, left=0,
                blend=BlendMode.NORMAL, visible=True, compression=Compression.ZIP_WITH_PREDICTION)
for nom, u16, mask8, x0, y0 in capes:
    add_pixel_layer(psd, u16, nom, top=y0, left=x0, mask8=mask8, blend=BlendMode.NORMAL,
                    visible=True, compression=Compression.ZIP_WITH_PREDICTION)
    log("  capa", nom[:64])
finalize_lr16(psd)
set_merged(psd, base, compression=Compression.ZIP_WITH_PREDICTION)
p_psb = os.path.join(OUT, "Prova_Vixen10s_sobre_Sony8s.psb")
psd.save(p_psb)
log(f"  → {p_psb}  ({os.path.getsize(p_psb)/1e9:.2f} GB)")
man["psb"] = p_psb
json.dump(man, open(os.path.join(OUT, "MANIFEST.json"), "w"), indent=1, ensure_ascii=False)
log("fet")
