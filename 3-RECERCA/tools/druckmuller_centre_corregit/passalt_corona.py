#!/usr/bin/env python3
"""Filtre de pas alt de la corona, en escala de grisos, sense costures de camp.

Ordre de Pere, 23-08-2026: un pas alt de la corona fet **amb totes les imatges
apilades** dels dos trens, **sense la Lluna ni les protuberàncies**, **en
escala de grisos**, i «espero no veure-hi cap artefacte de canvi de camp
Canon/Sony (com els bordes de la imatge)».

COM S'EVITEN LES COSTURES
-------------------------
Un pas alt és una resta de desenfocaments. Un desenfocament corrent, en trobar
la vora d'un camp, hi barreja el buit i **fabrica** un esglaó que abans no hi
era: és exactament l'artefacte que Pere veu. Aquí hi ha tres proteccions, i
totes tres calen:

1. **Convolució normalitzada.** Cada desenfocament es fa
   `G(x·m)/G(m)` amb la màscara de validesa `m`. La vora del camp no aporta
   res en lloc d'aportar zeros, o sigui que no hi ha esglaó per construcció.
2. **Finestra per distància a la vora, banda per banda.** Encara amb (1), una
   banda ampla a tocar de la vora veu el fons per un sol costat i queda
   esbiaixada. Cada banda s'apaga suau dins de **2,5 σ de la seva pròpia
   escala**, mesurat en mostres polars. És la mateixa protecció que
   `hdr_corona_vixen.py` va haver d'afegir el 17-08 quan la capa nua va
   destapar dos arcs a ~5 R☉ (`Corona_HDR_Vixen/LLEGEIX-ME.md`).
3. **Bandes en graus, no en píxels.** En log-polars les escales creixen amb el
   radi, o sigui que no hi ha cap escala privilegiada que dibuixi un anell. El
   fons azimutal de cada columna es treu amb una sèrie de Fourier de m ≤ 4
   sobre les files vàlides: la corona en surt sense el seu perfil radial i
   sense l'asimetria de gran escala.

A més, el compost d'entrada ja porta les sis correccions de `research/93`:
registre per les dues solucions de placa, calibratge absolut a B/B☉, pedestal
per zona de cobertura, igualació entre trens per canal, màscara de limbe al
disc lunar mesurat i apodització sobre el marc del sensor.

LLUNA I PROTUBERÀNCIES
----------------------
Mesurat al compost: l'excés de vermell (Hα) arriba fins a **1,06–1,08 R_lluna**
i per damunt no queda cap píxel amb `R/G > 1,25`. El pas alt s'apaga amb una
rampa suau entre **1,08 i 1,16 R_lluna** i és exactament neutre per dins. Cap
protuberància ni cap tros de disc no entra al filtre.

SOROLL
------
El pes de Wiener de cada banda necessita el soroll per píxel, i es mesura de
les dades: **les dues meitats independents de l'apilat Sony** (A i B) donen
σ per píxel amb `σ = σ(A−B)·√(w_A·w_B)/(w_A+w_B)`, i la **variància propagada
de l'HDR Vixen** dona la seva. Es combinen amb els mateixos pesos de fusió que
el compost.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import math
import os
import sys

import numpy as np

try:
    import cv2
    import tifffile as tiff
    from scipy import ndimage as ndi
except ImportError as exc:  # pragma: no cover
    sys.exit(f"Falta {exc.name}; mira detecta_python.py --check")

HOME = os.path.expanduser("~")
DESKTOP = os.path.join(HOME, "Desktop", "Eclipse 2026")
WORKTREE = os.path.join(HOME, "Downloads", "Eclipse 2026")

NA = 4096          # mostres d'angle
NR = 1536          # mostres de log-radi
BANDES_DEG = [0.10, 0.17, 0.27, 0.44, 0.71, 1.16, 1.86, 3.0, 4.9, 7.9, 12.8, 20.8]
# ⛔ Les bandes amples (≥4,9°) s'apaguen. En aquest compost el cel NO està
# restat —el flat òptic Sony no s'ha aplicat (research/93 §C)— i una banda
# ampla no distingeix el vinyetatge del senyal: amplifica el fons i, a tocar de
# les vores del camp, el biaix d'un sol costat. Provat: amb elles enceses
# surten anells concèntrics de mig llenç i les vores brillen. Un pas alt és un
# pas ALT; el fons és feina del flat, no d'aquesta capa.
GUANYS = [0.0, 2.0, 4.0, 6.0, 6.0, 5.5, 4.0, 2.0, 0.0, 0.0, 0.0]
# ⛔⛔ EL FILTRE HA DE COBRIR TOT EL RECTANGLE. Norma de Pere, 23-08-2026, i
# diu que és un error MEU RECURRENT. Un filtre de pas alt que s'apaga dins de
# la zona que encara té dades deixa una regió plana a gris neutre, i quan la
# capa es munta a Photoshop aquella frontera ÉS UN HALO: dins hi ha realçat i
# fora no. No importa que la transició sigui suau ni que l'amplitud hi sigui
# petita — el que es veu és el canvi de règim. Per això `R_EXT` va a ZERO per
# defecte: el filtre es calcula i es lliura a tot el llenç, i l'única cosa que
# el pot aturar és que no hi hagi dada.
# Si l'exterior surt lleig, la reparació és aigües amunt (flat òptic, cel,
# estrelles), MAI retallar un cercle.
R_EXT_LO, R_EXT_HI = 0.0, 0.0     # desactivat: cap tall radial
# ⛔ CAP porta de cobertura azimutal. Era redundant i, com tota porta radial,
# dibuixava una frontera —un quadrat arrodonit a ~8 R☉ on el gra s'aturava—.
# La cobertura parcial ja la tracten bé les dues proteccions que hi ha: la
# convolució normalitzada `G(x·m)/G(m)`, que no compta els azimuts que no hi
# són, i la finestra `dist_vora` per banda. I l'ajust de Fourier azimutal ja
# cau a la mitjana ponderada quan una columna té menys del 5 % d'azimut.
COBERTURA_MIN = 0.0               # 0 = sense porta
SIG_MIN_IMG_PX = 1.6
FLOOR_FRAC = 0.15   # terra de luminància, com a fracció del perfil llis local
M_FOURIER = 4
PROM_LO, PROM_HI = 1.08, 1.16       # rampa en radis lunars
# ⛔ El màster Vixen `hdr_vixen_countss.npy` porta els esglaons de la seva
# fusió HDR entre 1,05 i ~1,6 R☉: estries concèntriques i una vora dentada que
# segueix un contorn de saturació (artefacte F de research/93, verificat
# renderitzant NOMÉS aquella matriu). Un pas alt els ressalta com una anella
# dura. No es pinten a sobre: el filtre s'apaga on l'entrada té el defecte, i
# la reparació és refer la fusió HDR aigües amunt. Amb `--r-corona 0,0` es pot
# desactivar aquesta protecció per veure'l.
R_CORONA_LO, R_CORONA_HI = 1.70, 1.90    # R☉
VORA_SIGMES = 3.0
ESTRELLA_SIGMES = 4.0             # excés sobre la mediana local per dir-ne font compacta
ESTRELLA_R_MIN = 2.2              # R☉: per dins no s'hi toca (la corona hi és fina i brillant)


def envolupant_decreixent(v, w=None):
    """Regressió isotònica DECREIXENT (pool adjacent violators), pesada.

    L'amplitud d'un pas alt honest de la corona baixa amb el radi: la corona
    és més feble i més llisa cada vegada. Aquesta funció dona la corba
    decreixent més propera al perfil mesurat; el que en sobresurt és el que
    el perfil ha hagut de pujar, o sigui un anell. No hi ha cap finestra
    triada a mà, que és el defecte de comparar amb una mediana mòbil: una
    finestra curta segueix l'anell i el fa invisible, i una de llarga
    confon una pujada llarga i legítima amb un defecte.
    """
    v = np.asarray(v, float)
    w = np.ones_like(v) if w is None else np.asarray(w, float)
    val, pes, n = [], [], []
    for x, p in zip(v, w):
        val.append(x); pes.append(p); n.append(1)
        while len(val) > 1 and val[-2] < val[-1]:          # violació de decreixent
            x2 = val.pop(); p2 = pes.pop(); n2 = n.pop()
            x1 = val.pop(); p1 = pes.pop(); n1 = n.pop()
            val.append((x1 * p1 + x2 * p2) / (p1 + p2)); pes.append(p1 + p2); n.append(n1 + n2)
    return np.repeat(np.array(val), np.array(n))


def suau(x):
    """smoothstep: 0 i 1 amb DERIVADA ZERO als extrems.

    ⛔ Cap finestra, rampa ni porta d'aquest fitxer no pot ser un `clip`
    lineal. Un `clip` és continu però no derivable, i l'ull veu les
    discontinuïtats de derivada com una ratlla (bandes de Mach). La marca ocre
    que Pere va posar a 6,28 R☉ era exactament això: la rampa exterior era
    lineal i s'acabava amb cantonada a 6,5 R☉, on a més el gra de soroll
    s'aturava en sec. Una vora de textura es veu encara que la mitjana no
    canviï gens.
    """
    x = np.clip(x, 0.0, 1.0)
    return (x * x * (3.0 - 2.0 * x)).astype(np.float32)


def sha256(p, buf=1 << 22):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(buf), b""):
            h.update(c)
    return h.hexdigest()


def log(m):
    print(f"[{_dt.datetime.now():%H:%M:%S}] {m}", flush=True)


def mapes_polars(h, w, cy, cx, r_min, r_max):
    """Reixa log-polar: files = angle (periòdic), columnes = ln r."""
    rho = np.linspace(math.log(r_min), math.log(r_max), NR).astype(np.float32)
    r_of = np.exp(rho).astype(np.float32)
    th = (np.arange(NA, dtype=np.float32) * (2 * math.pi / NA))
    mx = (cx + r_of[None, :] * np.cos(th)[:, None]).astype(np.float32)
    my = (cy + r_of[None, :] * np.sin(th)[:, None]).astype(np.float32)
    # mapa invers: per a cada píxel d'imatge, quina mostra polar li toca
    Y, X = np.mgrid[0:h, 0:w].astype(np.float32)
    dx, dy = X - cx, Y - cy
    rr = np.maximum(np.hypot(dx, dy), 1e-3)
    ang = np.mod(np.arctan2(dy, dx), 2 * math.pi)
    ix = ((np.log(rr) - rho[0]) / (rho[1] - rho[0])).astype(np.float32)
    iy = (ang * (NA / (2 * math.pi))).astype(np.float32)
    K = (NR - 1) / (rho[-1] - rho[0])          # mostres per unitat de ln r
    return mx, my, ix, iy, r_of, K


def a_polar(img, mx, my):
    return cv2.remap(img.astype(np.float32), mx, my, cv2.INTER_LINEAR,
                     borderMode=cv2.BORDER_CONSTANT, borderValue=0.0)


def a_imatge(pol, ix, iy):
    """Polars -> imatge. L'ANGLE ES EMBOLCALLA.

    ⛔ Amb `BORDER_CONSTANT` la fila θ = 0 es barreja amb el buit i deixa una
    ratlla d'un píxel que surt del Sol cap a la dreta i travessa tota la
    corona. L'angle és periòdic: la fila de sota de la primera és l'última.
    """
    a = np.ascontiguousarray(pol, np.float32)
    a = np.vstack([a[-1:], a, a[:1]])
    return cv2.remap(a, ix, iy + np.float32(1.0), cv2.INTER_LINEAR,
                     borderMode=cv2.BORDER_REPLICATE)


def blur_polar(x, s_rho, s_ang):
    """Gaussiana sobre la reixa polar; l'angle s'embolcalla (no hi ha costura a 0°)."""
    a = np.ascontiguousarray(x, np.float32)
    p = int(max(4, math.ceil(3 * s_ang)))
    p = min(p, NA - 1)
    a = np.vstack([a[-p:], a, a[:p]])
    a = cv2.GaussianBlur(a, (0, 0), sigmaX=max(s_rho, 1e-3), sigmaY=max(s_ang, 1e-3),
                         borderType=cv2.BORDER_REPLICATE)
    return a[p:p + x.shape[0]]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", required=True, help="carpeta del stack calibrat")
    ap.add_argument("--sony-halves", default=None, help="carpeta amb sony_half_{A,B}_{rgb,wt}.npy")
    ap.add_argument("--vixen-var", default=os.path.join(DESKTOP, "Derivats/Vixen/Corona_HDR_Vixen/hdr_vixen_var.npy"))
    ap.add_argument("--out-root", default=os.path.join(WORKTREE, "output", "passalt_corona_20260823"))
    ap.add_argument("--preview-root", default=os.path.join(DESKTOP, "IA", "output", "passalt_corona_20260823"))
    ap.add_argument("--build-id", default=None)
    ap.add_argument("--amplitud", default="auto",
                    help=("D que es mapeja a blanc/negre. `auto` = percentil 99,99 de |D|, o sigui "
                          "que el lliurable de 16 bits NO retalla: un pas alt retallat ha perdut "
                          "justament els filaments més brillants, que és el que s'hi anava a buscar. "
                          "El contrast es posa amb una corba a Photoshop, no retallant."))
    ap.add_argument("--capa", default="06b_Compost_LINEAL_sense_cel_BBsol_float32.tif",
                    help=("quin compost s'hi filtra. Per defecte el SENSE CEL. ⛔ Amb el 06 "
                          "el pedestal de cel (~9,5e-9 B/B☉) esclafa el contrast logarítmic de "
                          "la corona (2,1e-9 a 5 R☉) i el filtre es mor més enllà de 3 R☉."))
    ap.add_argument("--r-ext", default=f"{R_EXT_LO},{R_EXT_HI}",
                    help=("rampa exterior en R☉. ⚠️ És un tall a un radi TRIAT A MÀ i no mesura "
                          "res de les dades: on s'acaba hi ha una vora de textura que l'ull veu "
                          "encara que la mitjana no canviï. Qui ha de decidir on s'acaba el "
                          "realçat és el pes de Wiener, que sí que mesura el senyal contra el "
                          "soroll. Amb `0,0` es desactiva."))
    ap.add_argument("--r-corona", default=f"{R_CORONA_LO},{R_CORONA_HI}",
                    help="rampa interior en R☉ per esquivar els esglaons de fusió del màster Vixen")
    args = ap.parse_args()

    bid = args.build_id or _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = os.path.join(args.out_root, bid)
    prev = os.path.join(args.preview_root, bid)
    if os.path.exists(out) or os.path.exists(prev):
        sys.exit(f"NO-CLOBBER: {bid} ja existeix")
    os.makedirs(out); os.makedirs(prev)

    man = {"build_id": bid, "created_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
           "purpose": "filtre de pas alt de la corona, escala de grisos, sense Lluna ni protuberancies ni costures de camp",
           "authority": "ordre de Pere 23-08-2026; metode a research/93 i research/94",
           "status": "EXPERIMENTAL_NOT_CANONICAL", "inputs": {}, "geometry": {}, "masks": {},
           "bands": [], "checks": {}, "outputs": {}}

    src = json.load(open(os.path.join(args.build, "MANIFEST.json")))
    sx, sy = src["geometry"]["sun_sony_astrometric"]
    rsol = src["geometry"]["r_sol_sony_px"]
    dcx, dcy = src["geometry"]["lunar_disc_center_px"]
    dR = src["geometry"]["lunar_disc_radius_px"]

    p_comp = os.path.join(args.build, args.capa)
    p_val = os.path.join(args.build, "07_Mascara_validesa_float32.tif")
    p_msk = os.path.join(args.build, "03_Mascara_fusio_float32.tif")
    for n, p in (("compost", p_comp), ("validesa", p_val), ("mascara_fusio", p_msk)):
        man["inputs"][n] = {"path": p, "bytes": os.path.getsize(p), "sha256": sha256(p)}
    man["inputs"]["stack_calibrat_manifest"] = {"build_id": src["build_id"]}
    man["inputs"]["capa_filtrada"] = args.capa

    log("carregant el compost…")
    C = tiff.imread(p_comp)
    V = tiff.imread(p_val)
    Wv = tiff.imread(p_msk)
    h, w = C.shape[:2]
    L = np.nan_to_num(C[:, :, 1].astype(np.float32), nan=0.0, posinf=0.0, neginf=0.0)
    del C

    # ---- fonts compactes ---------------------------------------------------
    # Les estrelles NO són corona i no es poden deixar passar: un pas alt les
    # converteix en taques negres. Es treuen aquí, que és on toca, en lloc de
    # tapar mig llenç amb un tall radial. Criteri: excés per damunt de la
    # mediana local de 5 px, mesurat en unitats del gra local, i només fora de
    # la corona interior, on l'estructura real sí que és fina i brillant.
    log("fonts compactes…")
    L5 = cv2.medianBlur(L, 5)
    dif = L - L5
    sfin = cv2.GaussianBlur(np.abs(dif), (0, 0), 48) * np.float32(1.4826)
    Yq, Xq = np.mgrid[0:h, 0:w].astype(np.float32)
    Rq = (np.hypot(Xq - sx, Yq - sy) / rsol).astype(np.float32)
    punts = (dif > np.float32(ESTRELLA_SIGMES) * np.maximum(sfin, 1e-30)) & (Rq > ESTRELLA_R_MIN)
    punts = cv2.dilate(punts.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))) > 0
    L = np.where(punts, L5, L).astype(np.float32)
    man["masks"]["fonts_compactes_llevades_px"] = int(punts.sum())
    man["masks"]["fonts_compactes_criteri"] = f"> {ESTRELLA_SIGMES} sigma sobre la mediana de 5 px, a r > {ESTRELLA_R_MIN} R☉"
    log(f"  {int(punts.sum())} px de fonts compactes substituïts per la mediana local "
        f"({100*punts.mean():.3f} % del llenç)")
    del L5, dif, sfin, punts, Rq, Xq, Yq

    Y, X = np.mgrid[0:h, 0:w].astype(np.float32)
    Rl = np.hypot(X - dcx, Y - dcy).astype(np.float32)
    Rs = (np.hypot(X - sx, Y - sy) / rsol).astype(np.float32)
    del X, Y

    # ---- màscara: dades + fora de Lluna i protuberàncies -------------------
    t = np.clip((Rl / dR - PROM_LO) / (PROM_HI - PROM_LO), 0.0, 1.0)
    m_prom = (t * t * (3.0 - 2.0 * t)).astype(np.float32)       # smoothstep
    rlo, rhi = [float(v) for v in args.r_corona.split(",")]
    if rhi > rlo > 0:
        u = np.clip((Rs - rlo) / (rhi - rlo), 0.0, 1.0)
        m_hdr = (u * u * (3.0 - 2.0 * u)).astype(np.float32)
    else:
        m_hdr = np.ones_like(Rs, np.float32)
    # ⚠️ La màscara ha de ser un ANELL NET. Si s'hi obren forats —perquè el
    # compost té píxels ≤ 0 als forats de saturació que la Vixen deixa a la
    # corona interior— la convolució normalitzada els tracta com a vores i el
    # pas alt dibuixa un contorn dentat al seu voltant. Es tanquen els forats
    # per morfologia i el zero es tracta com a TERRA de luminància, no com a
    # absència de dada: només és invàlid on de debò no hi ha camp (V = 0).
    # ⛔ La Lluna NO passa per la morfologia. `distanceTransform` sobre una
    # màscara amb el forat lunar el converteix en vora, i l'element
    # estructurant de 61 px hi deixa les seves CARES: el disc sortia amb una
    # dotzena de facetes rectes, just al lloc més delicat de la imatge. El
    # forat es tapa analíticament abans de la morfologia —així la vora del
    # camp queda neta— i la Lluna s'exclou després amb un cercle exacte, que
    # no té facetes perquè no és cap píxel: és una funció del radi.
    base = (np.clip(V, 0, 1) > 0.02).astype(np.uint8)
    base[Rl <= dR * 1.25] = 1                       # tapa el forat lunar
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (61, 61))
    base = cv2.morphologyEx(base, cv2.MORPH_CLOSE, k)
    base = cv2.erode(base, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    d_in = cv2.distanceTransform(base, cv2.DIST_L2, 5)
    m_camp = suau(d_in / 60.0)
    # i la Lluna, exacta i circular. El càlcul no hi pot mirar: allà no hi ha
    # corona, hi ha llum d'instrument i earthshine, i la convolució
    # normalitzada l'escamparia cap a la corona interior.
    # La MATEIXA geometria que feia la morfologia —9 px d'erosió i 60 px de
    # rampa—, però analítica i circular. ⚠️ No s'hi pot acostar més: entre
    # 1,03 i 1,23 radis lunars hi ha la cromosfera i les protuberàncies, i si
    # entren al càlcul el pas alt les converteix en taques ovalades (provat).
    m_lluna = suau((Rl - dR - 9.0) / 60.0)
    m_camp = (m_camp * m_lluna).astype(np.float32)
    # ⛔ DUES màscares, i no és el mateix. `suport` és el que veu el CÀLCUL:
    # només la vora real del camp. `valid` és el que es MOSTRA. Si el retall
    # interior entra al càlcul, la convolució normalitzada el tracta com una
    # vora, les bandes amples hi queden esbiaixades per un sol costat i, just
    # on la finestra de vora les torna a encendre, hi dibuixa una anella. El
    # retall interior s'aplica al final, multiplicant un camp que ja és suau:
    # així no pot fabricar cap vora.
    suport = m_camp.astype(np.float32)
    valid = (m_camp * m_prom * m_hdr).astype(np.float32)
    # ⛔ Cap terra global de luminància. Amb el cel restat, la corona a 6 R☉
    # és més feble que el soroll del cel i molts píxels són NEGATIUS: un terra
    # constant els aplana tots al mateix valor i el logaritme hi fabrica una
    # taca. El terra es posa més avall, en polars i RELATIU al perfil llis
    # local, que és l'única referència que té sentit a cada radi.
    man["masks"] = {"holes_closed_px": 61,
                    "prominence_ramp_lunar_radii": [PROM_LO, PROM_HI],
                    "prominence_ramp_rsol": [PROM_LO * dR / rsol, PROM_HI * dR / rsol],
                    "lunar_disc_radius_px": dR, "lunar_disc_center_px": [dcx, dcy],
                    "hdr_merge_ramp_rsol": [float(args.r_corona.split(",")[0]), float(args.r_corona.split(",")[1])],
                    "hdr_merge_ramp_motiu": "esglaons de fusio HDR del master Vixen (artefacte F, research/93)",
                    "valid_fraction": float((valid > 0.5).mean()),
                    "nota": "l'exces de vermell Halfa mesurat s'acaba a 1,06-1,08 R_lluna"}
    log(f"  màscara: {100*man['masks']['valid_fraction']:.1f} % del llenç; "
        f"rampa {PROM_LO}–{PROM_HI} R_lluna = {PROM_LO*dR/rsol:.3f}–{PROM_HI*dR/rsol:.3f} R☉")

    # ---- soroll per píxel ---------------------------------------------------
    log("soroll per píxel…")
    sig = np.zeros((h, w), np.float32)
    if args.sony_halves and os.path.isdir(args.sony_halves):
        A = np.load(os.path.join(args.sony_halves, "sony_half_A_rgb.npy"), mmap_mode="r")
        Bh = np.load(os.path.join(args.sony_halves, "sony_half_B_rgb.npy"), mmap_mode="r")
        wA = np.load(os.path.join(args.sony_halves, "sony_half_A_wt.npy"), mmap_mode="r")
        wB = np.load(os.path.join(args.sony_halves, "sony_half_B_wt.npy"), mmap_mode="r")
        d = (np.asarray(A[:, :, 1], np.float32) - np.asarray(Bh[:, :, 1], np.float32))
        pa = np.asarray(wA[:, :, 1], np.float32); pb = np.asarray(wB[:, :, 1], np.float32)
        # ⛔ σ del pes ponderat: σ(A−B)·√(wA·wB)/(wA+wB). El codi feia
        # √(wA·wB/(wA+wB)), que és la mateixa expressió amb l'arrel mal
        # col·locada i surt **√(wA+wB) = 4,975 vegades massa gran** amb el pes
        # típic de 24,75 s. A més era dimensionalment incoherent (ADU/s·√s).
        # Conseqüència: els pesos de Wiener de les bandes fines quedaven a
        # 0,07–0,20 i el detall fi no arribava mai a la sortida.
        # Comprovació: amb wA = wB = w ha de donar σ(A−B)/2, i ho fa.
        s_sony = (np.abs(d) * np.sqrt(np.maximum(pa * pb, 0)) /
                  np.maximum(pa + pb, 1e-6) * 1.2533)                     # |N(0,σ)| -> σ
        # ⛔ I el desenfoc ha de ser NORMALITZAT. `A−B` té un 4,9 % de NaN
        # —els forats de saturació dels fotogrames de 8 s— i una gaussiana
        # corrent de 24 px els escampa fins al **23 %** del llenç. Cada NaN
        # acabava a `sig_log = 1,0` per `nan_to_num`, o sigui senyal/soroll = 1,
        # que apaga el filtre: un anell mort de vora dentada a la corona
        # interior, perquè el patró segueix les isofotes de saturació. Un NaN
        # és manca de MESURA, no soroll infinit: s'omple amb el veïnat.
        bo = np.isfinite(s_sony).astype(np.float32)
        s_sony = np.nan_to_num(s_sony, nan=0.0, posinf=0.0, neginf=0.0)
        num = cv2.GaussianBlur(s_sony * bo, (0, 0), 24)
        den = cv2.GaussianBlur(bo, (0, 0), 24)
        s_sony = (num / np.maximum(den, 1e-3)).astype(np.float32)
        man["checks"]["soroll_sony_px_sense_mesura"] = round(float(1.0 - bo.mean()), 5)
        man["checks"]["soroll_sony_formula"] = "sigma(A-B)*sqrt(wA*wB)/(wA+wB)*1.2533"
        log(f"  soroll Sony: {100*(1-bo.mean()):.2f} % de píxels sense mesura, omplerts pel veïnat")
        del pa, pb, bo, num, den
        # ⛔ A unitats del compost amb la CONSTANT FÍSICA, no amb un quocient
        # de medianes. El quocient de medianes només val si el compost i les
        # meitats tenen el mateix zero, i el compost que filtrem té el cel
        # restat mentre que les meitats no: a 3–6 R☉ el quocient sortiria unes
        # cinc vegades massa petit, el soroll quedaria infravalorat i els
        # pesos de Wiener deixarien passar gra com si fos corona. El pas de
        # la Sony a B/B☉ és una constant mesurada (research/75 §5.2) i el
        # canal verd no porta cap altre factor.
        esc = float(src["photometry"]["factor_B_sony_per_ADUs"])   # del manifest del compost
        s_sony *= esc
        # comprovació independent: el pendent de L contra A on el pedestal no
        # pesa (1,5–3 R☉). Ha de coincidir amb la constant.
        _s = (Rs > 1.5) & (Rs < 3.0) & (valid > 0.9)
        _a = np.asarray(A[:, :, 1], np.float32)[_s].astype(np.float64)
        _l = L[_s].astype(np.float64)
        _f = np.isfinite(_a) & np.isfinite(_l)
        if _f.sum() > 10000:
            _pend = float(np.polyfit(_a[_f], _l[_f], 1)[0])
            man["checks"]["escala_soroll_constant"] = esc
            man["checks"]["escala_soroll_pendent_mesurat"] = _pend
            man["checks"]["escala_soroll_desviacio_pct"] = round(100 * (_pend / esc - 1), 2)
            log(f"  escala ADU/s -> B/B☉: constant {esc:.4e}, pendent mesurat "
                f"{_pend:.4e} ({100*(_pend/esc-1):+.1f} %)")
        del _s, _a, _l, _f
        man["inputs"]["sony_halves"] = args.sony_halves
        del A, Bh, wA, wB, d
    else:
        s_sony = None
    if s_sony is None:
        s_sony = np.full((h, w), float(np.std(L[(Rs > 9) & (valid > 0.9)])), np.float32)
    # ⛔ El soroll de la Vixen NO és un factor inventat. Fins ara aquí hi havia
    # `sig = s_sony * (1 - 0,75·Wv)`: el fitxer de variància s'obria i es
    # llençava, i el model de soroll acabava essent **la màscara de fusió**.
    # Això lliga la porta de Wiener a la sigmoide de 2,8 R☉ i hi pinta una
    # rampa de guany centrada exactament allà — dins de la banda que Pere va
    # marcar en vermell. Ara es fa servir la variància mesurada, warpada amb
    # la mateixa M que la capa, i es combinen amb els pesos de fusió reals:
    #     σ² = (wv·σ_vixen)² + ((1−wv)·σ_sony)²
    s_vix = None
    if os.path.exists(args.vixen_var):
        Vv = np.asarray(np.load(args.vixen_var, mmap_mode="r")[:, :, 1], np.float32)
        Mw = np.array(src["geometry"]["M"], np.float32)
        s_vix = np.sqrt(np.maximum(cv2.warpAffine(Vv, Mw, (w, h), flags=cv2.INTER_LINEAR,
                                                  borderMode=cv2.BORDER_CONSTANT,
                                                  borderValue=0.0), 0.0)).astype(np.float32)
        del Vv
        ph = src["photometry"]
        k_vix = (float(ph["factor_B_vixen_per_ADUs"]) * float(ph["gain_per_canal"][1])
                 * float(ph["neutralitzacio_RGB"][1]))
        s_vix *= np.float32(k_vix)
        man["checks"]["soroll_vixen_escala"] = k_vix
        man["checks"]["soroll_vixen_nota"] = ("variancia mesurada warpada amb la M de la capa; el "
                                              "remostreig correla el soroll, o sigui que a escala de "
                                              "pixel es una cota superior")
        log(f"  soroll Vixen: de la variància mesurada, escala {k_vix:.4e}")
    wvc = np.clip(Wv, 0, 1).astype(np.float32)
    if s_vix is not None:
        sig = np.sqrt((wvc * s_vix) ** 2 + ((1.0 - wvc) * s_sony) ** 2).astype(np.float32)
        del s_vix
    else:
        log("  ⚠️ sense fitxer de variància de la Vixen: només el soroll de la Sony")
        sig = ((1.0 - wvc) * s_sony).astype(np.float32)
    del wvc
    piso = float(np.median(L[(Rs > 3) & (Rs < 6) & (valid > 0.9)]))
    # ⚠️ Un NaN residual NO pot valer 1,0: això és senyal/soroll = 1 i apaga el
    # filtre en silenci. S'omple amb la mediana del que sí que s'ha mesurat.
    sig_log = (sig / np.maximum(L, 1e-30)).astype(np.float32)
    fin = np.isfinite(sig_log) & (m_camp > 0.5)
    reserva = float(np.median(sig_log[fin])) if fin.any() else 0.1
    sig_log = np.where(np.isfinite(sig_log), sig_log, reserva).astype(np.float32)
    man["checks"]["sigma_log_reserva"] = reserva
    sig_log = np.clip(sig_log, 0.0, 3.0)
    man["checks"]["sigma_log_median_3_6_Rsol"] = float(np.median(sig_log[(Rs > 3) & (Rs < 6) & (valid > 0.9)]))
    log(f"  σ/L mediana a 3–6 R☉: {man['checks']['sigma_log_median_3_6_Rsol']:.4f}")

    # ---- a log-polars -------------------------------------------------------
    r_min = max(min(PROM_LO * dR, rlo * rsol * 0.92) * 0.95, 120.0)
    r_max = math.hypot(max(sy, h - sy), max(sx, w - sx)) + 4.0
    mx, my, ix, iy, r_of, K = mapes_polars(h, w, sy, sx, r_min, r_max)
    log(f"log-polars {NA}×{NR}, r de {r_min:.0f} a {r_max:.0f} px "
        f"({r_min/rsol:.2f}–{r_max/rsol:.2f} R☉)")
    ok = a_polar(suport, mx, my)
    sp = a_polar(sig_log, mx, my)
    Lp = a_polar(L, mx, my)
    ok0 = np.nan_to_num(np.clip(ok, 0, 1), nan=0.0).astype(np.float32)
    iso0 = 2 * math.pi * K / NA
    s_ample = BANDES_DEG[-1] * (NA / 360.0)
    c_abs = float(src.get("artifact_checks", {}).get("A_sigma_cel_BBsol", 0.0) or 0.0)
    man["masks"]["terra_absolut_BBsol"] = c_abs
    Lsm = (blur_polar(np.nan_to_num(Lp) * ok0, s_ample * iso0, s_ample) /
           np.maximum(blur_polar(ok0, s_ample * iso0, s_ample), 1e-3))
    # ⚠️ El terra RELATIU només té sentit si no n'hi ha d'absolut. Amb tots dos
    # posats, el relatiu aplana el 11 % dels píxels a un valor constant i les
    # bandes hi donen zero exacte: altiplans plans de vora dentada, que és una
    # frontera interna com qualsevol altra (norma del rectangle).
    frac = 0.0 if c_abs > 0 else FLOOR_FRAC
    sostre = np.maximum(Lsm, 0.0) * np.float32(frac)
    tocat = float(np.mean((np.nan_to_num(Lp) < sostre)[ok0 > 0.5]))
    # ⛔ I un terra ABSOLUT al nivell del soroll del cel. El compost sense cel
    # es torna NEGATIU a partir d'uns 7,5 R☉ —la quàdrica es va ajustar a
    # r > 8,5 R☉, on la corona F encara hi és, i per tant la sobreresta— i el
    # logaritme hi explota. Amb `ln(L + c)` i `c` = σ del cel, el contrast de
    # la corona interior es conserva gairebé sencer (compressió ×1,2 a 3 R☉
    # contra ×2,5 si es filtra el compost amb el cel a dins) i l'exterior es
    # comporta. NO és un tall radial: és una constant, i per tant no pot
    # dibuixar cap frontera.
    # ⛔ I el terra ha de ser POSITIU i proporcionat. Retallar a 1e−30 fa que
    # `ln` hi salti a −69: allà on `L + c` es torna negatiu —a 8 R☉ ja ho és
    # per a una cinquena part dels píxels— sortia un arc dur. Es limita a un
    # quart de `c`, o sigui que l'excursió del logaritme queda acotada a
    # ln(0,25) = −1,39 respecte del nivell de referència. Continua sense ser
    # cap tall radial: és una constant.
    Lp2 = np.nan_to_num(Lp, nan=0.0) + np.float32(c_abs)
    terra_dur = np.float32(max(0.25 * c_abs, 1e-30))
    tocat_dur = float(np.mean((Lp2 < terra_dur)[ok0 > 0.5]))
    man["masks"]["terra_dur_BBsol"] = float(terra_dur)
    man["masks"]["terra_dur_px_tocats"] = round(tocat_dur, 5)
    P = np.log(np.maximum(Lp2, np.maximum(sostre, terra_dur)))
    log(f"  terra dur = {float(terra_dur):.3e} (25 % de c): el toca el {100*tocat_dur:.2f} %")
    log(f"  terra absolut (σ del cel) = {c_abs:.3e} B/B☉")
    del Lp2
    man["masks"]["terra_relatiu_fraccio_del_perfil_llis"] = frac
    man["masks"]["terra_relatiu_px_tocats"] = round(tocat, 5)
    _tr = "desactivat (n'hi ha d'absolut)" if frac == 0 else f"{100*frac:.0f} % del perfil llis"
    log(f"  terra relatiu: {_tr}; píxels negatius a l'entrada: {100*tocat:.2f} %")
    del Lp, Lsm, sostre

    # ---- fons azimutal per columna: Fourier m ≤ 4 sobre les files vàlides ----
    log(f"fons azimutal de Fourier m ≤ {M_FOURIER}…")
    th = (np.arange(NA, dtype=np.float64) * (2 * math.pi / NA))
    base = [np.ones(NA)]
    for mm in range(1, M_FOURIER + 1):
        base += [np.cos(mm * th), np.sin(mm * th)]
    Bm = np.stack(base, axis=1).astype(np.float64)          # NA × (2m+1)
    Wp = np.clip(ok, 0, 1).astype(np.float64)
    Pd = np.nan_to_num(P.astype(np.float64))
    G = np.einsum("ai,aj,ac->cij", Bm, Bm, Wp, optimize=True)
    rhs = np.einsum("ai,ac->ci", Bm, Wp * Pd, optimize=True)
    F = np.zeros_like(Pd)
    nb = Bm.shape[1]
    for c in range(NR):
        if Wp[:, c].sum() < 0.05 * NA:
            F[:, c] = np.average(Pd[:, c], weights=np.maximum(Wp[:, c], 1e-9)) if Wp[:, c].sum() > 0 else 0.0
            continue
        try:
            coef = np.linalg.solve(G[c] + 1e-9 * np.eye(nb), rhs[c])
        except np.linalg.LinAlgError:
            coef = np.zeros(nb)
        F[:, c] = Bm @ coef
    # ⛔ SENSE multiplicar per la màscara. `bn()` ja fa la convolució
    # normalitzada `G(x·m)/G(m)`; si a més s'entra `R` ja emmascarat, la
    # màscara s'aplica DUES vegades —`G(x·m²)/G(m)`— i el resultat torna a
    # tenir una vora dura justament al rim de la màscara. És l'artefacte
    # dentat que perseguíem: es movia amb la màscara, no amb les dades.
    R = np.nan_to_num((Pd - F).astype(np.float32), nan=0.0, posinf=0.0, neginf=0.0)
    del Pd, F, G, rhs
    log("  fet")

    # ---- bandes -------------------------------------------------------------
    iso = 2 * math.pi * K / NA
    px_deg = NA / 360.0
    esc = [d * px_deg for d in BANDES_DEG]
    okf = np.nan_to_num(np.clip(ok, 0, 1), nan=0.0).astype(np.float32)
    sp = np.nan_to_num(sp, nan=1.0, posinf=1.0, neginf=1.0)

    def bn(a, s):
        return blur_polar(a * okf, s * iso, s) / np.maximum(blur_polar(okf, s * iso, s), 1e-3)

    # ⚠️ FRACCIÓ d'azimut vàlid, no mitjana del pes. `okf` és un pes suau —a la
    # corona interior val 0,85–0,97 perquè la validesa hi ve del pes de fusió de
    # la Vixen— i fer-ne la mitjana el confon amb cobertura parcial: el gate
    # apagava tot el realçat d'1,2 a 2,7 R☉, que és justament la corona.
    cob = (okf > 0.5).mean(axis=0).astype(np.float32)
    # ⚠️ Rampa LLARGA. Amb el llindar a 0,98 i una finestra de 0,02, aquesta
    # porta era un esglaó de 4,4 px de radi disfressat de rampa suau, i deixava
    # un cercle perfecte a 8,2 R☉ on el gra s'aturava en sec.
    if COBERTURA_MIN > 0:
        r_ok = suau((cob - COBERTURA_MIN) / (1.0 - COBERTURA_MIN))
    else:
        r_ok = np.ones_like(cob, np.float32)
    man["cobertura_gate"] = bool(COBERTURA_MIN > 0)
    # ⛔ L'esvaïment exterior és GAUSSIÀ i no té final. Una rampa que arriba a
    # zero a un radi concret deixa una vora de TEXTURA: dins hi ha gra i fora
    # no, i l'ull la veu encara que la mitjana no canviï gens. Amb `clip`
    # lineal (fins a la v12) hi havia a més una cantonada de derivada, i és
    # el cercle que Pere va marcar en ocre a 6,28 R☉. La gaussiana decau sense
    # aturar-se mai: `e_hi` només diu on val 0,1, no on s'acaba.
    e_lo, e_hi = [float(v) for v in args.r_ext.split(",")]
    if e_hi > e_lo > 0:
        S = (e_hi - e_lo) / math.sqrt(2.0 * math.log(10.0))
        u = np.maximum(r_of / rsol - e_lo, 0.0) / S
        r_ext = np.exp(-0.5 * u * u).astype(np.float32)
    else:
        r_ext = np.ones_like(r_of, np.float32)
    man["r_ext_Rsol"] = ({"plena_fins_a": e_lo, "val_0.1_a": e_hi, "forma": "gaussiana, sense zero dur"}
                         if e_hi > e_lo > 0 else None)
    r_gate = (r_ext * r_ok).astype(np.float32)
    man["checks"]["radi_on_la_rampa_arriba_a_zero_Rsol"] = float(
        r_of[int(np.argmax(r_gate <= 0.001))] / rsol) if (r_gate <= 0.001).any() else None
    log("  esvaïment exterior: " + (f"gaussià, ple fins a {e_lo} R☉ i 0,1 a {e_hi}"
        if man["r_ext_Rsol"] else "DESACTIVAT (mana el pes de Wiener)") +
        f"; cobertura azimutal mínima {COBERTURA_MIN}")
    rng = np.random.default_rng(20260823)
    z = rng.standard_normal(R.shape).astype(np.float32)
    dist_vora = cv2.distanceTransform((okf > 0.5).astype(np.uint8), cv2.DIST_L2, 5)
    cel = (a_polar(((Rs > 4) & (Rs < 6)).astype(np.float32), mx, my) > 0.5) & (okf > 0.9)
    prevR, prevZ = bn(R, esc[0]), bn(z, esc[0])
    D = np.zeros_like(R)
    env2 = np.zeros(NR, np.float64)      # envolupant radial DECLARADA del filtre
    f_sist = 1.0
    log("  banda (°)      k soroll   S/N cel   pes mitjà   aportació   σ img @2 R☉")
    i2 = int(np.searchsorted(r_of, 2 * rsol))
    for j, (d0, d1) in enumerate(zip(BANDES_DEG[:-1], BANDES_DEG[1:])):
        segR, segZ = bn(R, esc[j + 1]), bn(z, esc[j + 1])
        b, bz = prevR - segR, prevZ - segZ
        prevR, prevZ = segR, segZ
        k_r = np.sqrt(np.maximum(np.sum(bz.astype(np.float64) ** 2 * okf, axis=0), 0) /
                      np.maximum(okf.sum(axis=0), 1.0)).astype(np.float32)
        n_col = k_r[None, :] * sp
        rms_cel = float(np.sqrt(np.mean(b[cel].astype(np.float64) ** 2))) if cel.any() else 0.0
        n_cel = max(float(np.median(n_col[cel])) if cel.any() else 1e-12, 1e-12)
        if j == 0:
            brut = rms_cel / n_cel
            f_sist = max(1.0, brut)
            # ⚠️ El `max()` és d'un sol costat i per això no pot dir mai que el
            # model de soroll SOBREESTIMA: amb la fórmula equivocada, el
            # quocient sortia molt per sota d'1 i quedava tapat com a 1,00.
            # El quocient cru s'anota sempre.
            man["checks"]["f_sistematic_cru"] = round(float(brut), 3)
            man["checks"]["model_soroll_sobreestima"] = bool(brut < 0.5)
            log(f"  sistemàtic d'escala fina: quocient cru {brut:.2f} -> f = ×{f_sist:.2f}"
                + ("   ⚠️ el model de soroll SOBREESTIMA" if brut < 0.5 else ""))
        sig_img = np.deg2rad(d0) * r_of
        if GUANYS[j] == 0.0:
            log(f"  {d0:5.2f}–{d1:5.2f}   {k_r[i2]:9.5f}   {rms_cel/(n_cel*f_sist):6.1f}   guany 0, descartada")
            man["bands"].append({"deg": [d0, d1], "gain": 0.0})
            continue
        n2 = (f_sist * n_col) ** 2
        v = bn(b * b, 4.0 * esc[j + 1])
        wj = np.clip(1.0 - n2 / np.maximum(v, 1e-14), 0.0, 1.0).astype(np.float32)
        g_r = (GUANYS[j] * suau(sig_img / SIG_MIN_IMG_PX - 1.0) * r_gate).astype(np.float32)
        wv = np.clip(dist_vora / (VORA_SIGMES * esc[j + 1]), 0.0, 1.0)
        wv = (wv * wv * (3.0 - 2.0 * wv)).astype(np.float32)
        cont = g_r[None, :] * wj * wv * b
        D += cont
        env2 += g_r.astype(np.float64) ** 2
        man["bands"].append({"deg": [d0, d1], "gain": GUANYS[j], "k_at_2Rsol": float(k_r[i2]),
                             "snr_sky": float(rms_cel / (n_cel * f_sist)),
                             "mean_wiener_weight": float(wj[okf > 0.5].mean()),
                             "contribution_rms": float(np.std(cont[okf > 0.5]))})
        log(f"  {d0:5.2f}–{d1:5.2f}   {k_r[i2]:9.5f}   {rms_cel/(n_cel*f_sist):6.1f}   "
            f"{float(wj[okf>0.5].mean()):7.3f}   {float(np.std(cont[okf>0.5])):9.6f}   {sig_img[i2]:6.1f}")
    man["checks"]["f_sistematic"] = f_sist
    man["gains"] = GUANYS
    man["cobertura_azimutal_minima"] = COBERTURA_MIN
    del z, prevR, prevZ, R, sp

    # ---- de tornada a la imatge --------------------------------------------
    log("de tornada a la reixa d'imatge…")
    Di = a_imatge(D, ix, iy) * valid
    Di[~np.isfinite(Di)] = 0.0
    del D

    # l'envolupant radial DECLARADA: la fan servir tant les comprovacions de
    # costura com la G, i totes dues només valen on el filtre lliura.
    env = np.sqrt(np.maximum(env2, 0.0)).astype(np.float32)
    env_of_r = np.interp(Rs.ravel() * rsol, r_of, env, left=env[0],
                         right=env[-1]).reshape(Rs.shape).astype(np.float32)
    env_ref = float(np.percentile(env, 95)) or 1.0

    # ---- comprovacions de costura ------------------------------------------
    log("comprovacions de costura…")
    def salt(mask_a, mask_b, nom):
        """Salt a banda i banda d'una vora, en unitats del gra LOCAL.

        ⛔ Aquest control informava «0,000 σ» a totes les versions i era fals:
        agafava dues franges senceres al voltant de la caixa, que passen sobre
        tot pels cantons del llenç on l'esvaïment exterior ha deixat D
        exactament a zero. El 85 % dels píxels de cada franja eren zeros
        exactes, les dues medianes valien 0 i el salt sortia 0 per
        construcció. Un control que no pot fallar no és un control. Ara:
        només on el filtre lliura de debò, es refusa la mostra si és
        degenerada, i el gra es mesura A LA VORA, no a tot el camp.
        """
        a = Di[mask_a]; b = Di[mask_b]
        if a.size < 5000 or b.size < 5000:
            man["checks"][nom] = {"estat": "MOSTRA_INSUFICIENT", "n": [int(a.size), int(b.size)]}
            log(f"  {nom}: mostra insuficient ({a.size}, {b.size})")
            return
        z = max(float(np.mean(a == 0.0)), float(np.mean(b == 0.0)))
        if z > 0.20:
            man["checks"][nom] = {"estat": "MOSTRA_DEGENERADA", "fraccio_zeros": round(z, 4)}
            log(f"  {nom}: MOSTRA DEGENERADA ({100*z:.0f} % de zeros exactes) — no es pot mesurar")
            return
        s = float(np.std(np.concatenate([a, b])))
        d = float(np.median(a) - np.median(b))
        man["checks"][nom] = {"delta": d, "sigma_local": s, "sigmes": float(abs(d) / max(s, 1e-12)),
                              "n": [int(a.size), int(b.size)], "fraccio_zeros": round(z, 4),
                              "llindar_sigmes": 0.30, "PASSA": bool(abs(d) / max(s, 1e-12) < 0.30)}
        log(f"  {nom}: {man['checks'][nom]['sigmes']:.3f} σ sobre {a.size + b.size} px "
            f"-> {'PASSA' if man['checks'][nom]['PASSA'] else 'FALLA'}")
    Mw = np.array(src["geometry"]["M"], float)
    hv, wv_ = 4638, 6958
    poly = (Mw @ np.array([[0, 0, 1], [wv_, 0, 1], [wv_, hv, 1], [0, hv, 1]], float).T).T
    frame = np.zeros((h, w), np.uint8)
    cv2.fillPoly(frame, [poly.astype(np.int32)], 1)
    dfr = cv2.distanceTransform(frame, cv2.DIST_L2, 5)
    dfo = cv2.distanceTransform(1 - frame, cv2.DIST_L2, 5)
    # ⚠️ I on el filtre ha produït un valor. La caixa de cobertura de la Sony
    # arriba a x = 7926 i el llenç només té 7648 px d'ample: una part del seu
    # perímetre NO EXISTEIX, i mostrejar-la omplia la mostra de zeros exactes.
    lliura = (valid > 0.99) & (env_of_r > 0.5 * float(env.max())) & (Di != 0.0)
    man["checks"]["vores_avaluades_on"] = "valid>0.99 i envolupant declarada >= 50 % del maxim"
    salt((dfr > 5) & (dfr < 90) & lliura, (dfo > 5) & (dfo < 90) & lliura, "vora_marc_Vixen")
    bx = src["masks"]["sony_full_coverage_box"]
    inb = np.zeros((h, w), np.uint8); inb[bx[1]:bx[3], bx[0]:bx[2]] = 1
    din = cv2.distanceTransform(inb, cv2.DIST_L2, 5); dout = cv2.distanceTransform(1 - inb, cv2.DIST_L2, 5)
    salt((din > 5) & (din < 90) & lliura, (dout > 5) & (dout < 90) & lliura, "vora_cobertura_Sony")
    salt((Rs > 2.6) & (Rs < 2.8) & (valid > 0.99), (Rs > 2.8) & (Rs < 3.0) & (valid > 0.99), "sigmoide_fusio_2.8Rsol")

    # ---- lliurables ---------------------------------------------------------
    # ---- G: EL RMS RADIAL NO POT PUJAR ------------------------------------
    # És la comprovació que hauria cantat l'anell que Pere va marcar en
    # vermell, i cap de les que hi havia no ho va fer: les de costura miren
    # VORES concretes (el marc Vixen, la caixa Sony, la sigmoide) i aquell
    # artefacte era un anell radial enmig del camp. La corona és llisa i
    # decreixent: l'amplitud d'un pas alt honest baixa monòtonament amb el
    # radi. Si puja, hi ha un graó fabricat. A la v12 pujava ×2,30 entre
    # 2,25 i 2,35 R☉.
    log("perfil radial del pas alt…")
    # ⚠️ G només mira on el filtre va a ple. Si hi entren les rampes
    # declarades —la de protuberàncies, la dels esglaons HDR o l'esvaïment
    # exterior— la comprovació es jutja a si mateixa: la pujada que veuria
    # seria la rampa encenent-se, no un defecte.
    # ⚠️ Es divideix per l'ENVOLUPANT RADIAL DECLARADA del filtre —la porta de
    # resolució, l'esvaïment exterior i les portes de cobertura—, que és el que
    # el filtre fa a propòsit amb el radi. Sense això la comprovació es jutjaria
    # a si mateixa: de 1,5 a 1,8 R☉ el rms puja ×1,7 només perquè les bandes
    # fines s'encenen en creuar el límit de mostreig, i això no és cap defecte.
    Dn = np.where(env_of_r > 0.05 * env_ref, Di / np.maximum(env_of_r, 1e-6), np.nan).astype(np.float32)
    g_lo = max(rhi if rhi > rlo > 0 else 0.0, PROM_HI * dR / rsol) + 0.05
    g_hi = 7.0
    man["checks"]["G_rang_Rsol"] = [round(g_lo, 2), round(g_hi, 2)]
    man["checks"]["G_nota"] = "rms de D dividit per l'envolupant radial declarada del filtre"
    rb = np.arange(g_lo, g_hi, 0.1)
    prof = []
    for t in rb:
        mm = (valid > 0.99) & (Rs >= t) & (Rs < t + 0.1) & np.isfinite(Dn)
        if mm.sum() < 3000:
            prof.append(None); continue
        prof.append(float(np.sqrt(np.mean(Dn[mm].astype(np.float64) ** 2))))
    pr = [(float(t), v) for t, v in zip(rb, prof) if v is not None and v > 1e-9]
    man["checks"]["G_rms_radial"] = [[round(t, 2), float(f"{v:.5g}")] for t, v in pr]
    if len(pr) > 12:
        # ⚠️ El que delata un anell és un EXCÉS LOCAL, no una pujada. El filtre
        # encén bandes fines a mesura que el radi creix —cada banda té el seu
        # llindar de mostreig— i això fa pujades legítimes i llargues. Un anell,
        # en canvi, és estret: es veu comparant cada radi amb la mediana mòbil
        # del seu entorn. A la v12 aquest quocient valia 3,2 a 2,5 R☉.
        rr = np.array([t for t, _ in pr]); vv = np.array([v for _, v in pr])
        # la porta només val on el filtre lliura: envolupant >= 50 % del màxim
        env_r = np.interp(rr * rsol, r_of, env, left=env[0], right=env[-1])
        dins = env_r >= 0.5 * float(env.max())
        sm = np.full_like(vv, np.nan)
        if dins.sum() > 6:
            sm[dins] = envolupant_decreixent(vv[dins])
        q = np.where(dins, vv / np.maximum(sm, 1e-12), 0.0)
        man["checks"]["G_porta_Rsol"] = [round(float(rr[dins].min()), 2),
                                         round(float(rr[dins].max()), 2)] if dins.any() else None
        if dins.sum() > 6:
            i = int(np.argmax(q))
            man["checks"]["G_exces_local_max"] = round(float(q[i]), 3)
            man["checks"]["G_exces_local_max_Rsol"] = round(float(rr[i]), 2)
            man["checks"]["G_llindar"] = 1.30
            man["checks"]["G_PASSA"] = bool(q[i] < 1.30)
            log(f"  G · excés sobre l'envolupant decreixent ×{q[i]:.3f} a {rr[i]:.2f} R☉ "
                f"(llindar 1,30; porta {man['checks']['G_porta_Rsol']}) -> "
                f"{'PASSA' if man['checks']['G_PASSA'] else 'FALLA'}")

    if str(args.amplitud).strip().lower() == "auto":
        A = float(np.percentile(np.abs(Di[valid > 0.5]), 99.99))
        log(f"  amplitud automàtica: |D| p99,99 = {A:.4f}")
    else:
        A = float(args.amplitud)
    man["amplitud_mode"] = "auto" if str(args.amplitud).strip().lower() == "auto" else "fixa"
    g = np.clip(0.5 + Di / (2.0 * A), 0.0, 1.0)
    g = np.where(valid > 0, g, 0.5)
    u16 = (g * 65535.0 + 0.5).astype(np.uint16)
    p_gris = os.path.join(out, "PASSALT_corona_gris_uint16.tif")
    tiff.imwrite(p_gris, u16, photometric="minisblack")
    p_f32 = os.path.join(out, "PASSALT_corona_D_float32.tif")
    tiff.imwrite(p_f32, Di.astype(np.float32))
    p_msk_out = os.path.join(out, "PASSALT_mascara_valid_float32.tif")
    tiff.imwrite(p_msk_out, valid.astype(np.float32))
    man["outputs"] = {"passalt_gris_uint16": p_gris, "D_float32": p_f32, "mascara": p_msk_out}
    man["checks"]["D_rms_valid"] = float(np.std(Di[valid > 0.5]))
    man["checks"]["D_p001_p999"] = [float(np.percentile(Di[valid > 0.5], 0.1)),
                                    float(np.percentile(Di[valid > 0.5], 99.9))]
    man["checks"]["fraccio_saturada"] = float(np.mean((g[valid > 0.5] <= 0.001) | (g[valid > 0.5] >= 0.999)))
    man["amplitud"] = A
    log(f"  D rms {man['checks']['D_rms_valid']:.4f}; p0,1–p99,9 "
        f"{man['checks']['D_p001_p999'][0]:+.3f}…{man['checks']['D_p001_p999'][1]:+.3f}; "
        f"saturat {100*man['checks']['fraccio_saturada']:.3f} %")

    prv = cv2.resize((g * 255).astype(np.uint8), (3840, 2560), interpolation=cv2.INTER_AREA)
    p_prev = os.path.join(prev, "00_PASSALT_4K.jpg")
    cv2.imwrite(p_prev, prv, [int(cv2.IMWRITE_JPEG_QUALITY), 93])
    man["outputs"]["preview"] = p_prev

    for k, v in list(man["outputs"].items()):
        if isinstance(v, str) and os.path.exists(v):
            man["outputs"][k] = {"path": v, "bytes": os.path.getsize(v), "sha256": sha256(v)}
    with open(os.path.join(out, "MANIFEST.json"), "x", encoding="utf-8") as fh:
        json.dump(man, fh, indent=2, ensure_ascii=False)
    log(f"manifest: {os.path.join(out, 'MANIFEST.json')}")
    log("FET")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
