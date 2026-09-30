#!/usr/bin/env python3
"""V26 · muntatge amb les correccions d'artefactes de la skill `corregeix-artefactes`,
sobre la base, la geometria i les capes de detall de la V25 (etapes 1, 2b, 2c).

Canvis respecte de la V25 (04-09-2026, marques de Pere a ~/Downloads/Artefactes.tif):
  V  el camp exterior fora de la cobertura del llenç comú ja NO s'inventa (l'extensió per
     raig deixava vores rectes): hi va la DADA de les capes 12+13 de Pere (Sony V17 amb el
     seu Camera Raw i el fons per raig), copiada a la meva base i IGUALADA en to a la
     meva base (ρ radial × azimutal k≤2 a 6,0-8,5 R☉), amb ploma de 120 px a la vora;
  G  ghosts del Sol a la lent de la Sony: pedaç DECLARAT (mediana anular a la base,
     0,5 a les capes de detall) a les SIS marques grogues de Pere (~8 R☉), al ghost de
     3,0 R☉ (research/116) i als blobs rodons detectats a la capa ACHF (>3,5σ);
  R  ratllat del patró fix de la Sony (−45° a la V23, períodes 28-181 px): tall
     direccional a l'espectre de les capes de detall, aplicat amb rampa 2,65→3,5 R☉
     (zona Sony) — DECLARAT;
  E  esvaïment del detall on només hi ha cel: 5→7 R☉ (DECLARAT; la corona és cosmètica
     de 3,25 R☉ enfora, research/123);
  A  prova de superposició: finestres en escaquer entre la base i les capes 10 i 09.
Ronda 3 (04-09, nit):
  L  la ploma del camp exterior es mesura a la vora EXTERIOR de la cobertura (forat lunar
     omplert abans de la distància): la ronda 2 barrejava la base amb les capes de Pere (zero
     dins de 2,6 R☉) fins a 120 px del limbe → franja fosca 1,0-1,27 R☉;
  E  el detall FI (ACHF 2-32 px, passa-alt σ24) s'esvaeix 3,5→5 R☉ (a 4-5 R☉ és gra pur:
     la "recta" de 45° i els 5 "blobs" de la ronda 2 eren la vora i l'interior d'aquest gra);
  +  capa nova `03 DETALL ACHF 32-256 px` (etapa 1b: streamers), esvaïda 5→6,5 R☉, Superposar 50 %;
  +  capa OCULTA `00b BASE sense cel` (corona + 0,25·cel, etapa 1b) amb la mateixa màscara.
"""
import os, sys, json, time, shutil, subprocess, importlib.util
import numpy as np, cv2
from scipy.ndimage import gaussian_filter, distance_transform_edt, binary_fill_holes
from psd_tools import PSDImage
from psd_tools.constants import Compression, BlendMode
from psd_tools.psd.image_data import ImageData
from PIL import Image, ImageDraw, ImageFont
AQUI = os.path.dirname(os.path.abspath(__file__)); CAU = os.path.join(AQUI, "cau_v25")
sys.path.insert(0, "/Users/USUARI/Downloads/Eclipse 2026/research/tools/encaix_sony")
sys.path.insert(0, "/Users/USUARI/Downloads/Eclipse 2026/.claude/skills/corregeix-artefactes/scripts")
from psb_utils import add_pixel_layer, add_mask16, finalize_lr16
import artefactes as art
spec = importlib.util.spec_from_file_location("e3", os.path.join(AQUI, "etapa3_munta_v25.py")); e3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(e3)
raw_capa, a_canvas, sobre, omple_mitja_lluna, rho_display = e3.raw_capa, e3.a_canvas, e3.sobre, e3.omple_mitja_lluna, e3.rho_display

CT = e3.CT; V24 = e3.V24; V26 = os.path.join(CT, "CapesTotalsV26_lineal_B.psb")
OUT = "/Users/USUARI/Desktop/Eclipse 2026/IA/output/v26_lineal_20260904"; os.makedirs(OUT, exist_ok=True)
PORTA = e3.PORTA; RS, CX, CY = e3.RS, e3.CX, e3.CY
OPACITAT_ACHF, OPACITAT_PASSALT, OPACITAT_GRAN = 70, 40, 50
MARQUES_PERE = os.path.join(CAU, "marques_pere_artefactes.json")
T0 = time.time(); REB = {"versio": "V26", "base": "etapa 1 V25", "geometria": "etapa 2b/2c V25"}
def marca(t): print(f"[{time.time()-T0:7.1f} s] {t}", flush=True)


def main():
    G = json.load(open(os.path.join(CAU, "geometria_v23.json"))); M1 = np.array(G["M_llenc_a_v23"], np.float64)
    REB["geometria_num"] = {k: G.get(k) for k in ("rotacio_total_deg", "escala_total", "mediana_offset_px", "p90_offset_px")}
    psd = PSDImage.open(V24); W, H = psd.width, psd.height; capes = list(psd); assert len(capes) == 20
    rad, theta_deg = art.polars(H, W, CX, CY); theta = np.radians(theta_deg)
    def warp(a, interp=cv2.INTER_LANCZOS4):
        return cv2.warpAffine(np.ascontiguousarray(a), M1, (W, H), flags=interp, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    base = np.load(os.path.join(CAU, "base_B_rgb16.npy")).astype(np.float32) / 65535.0
    B = np.dstack([warp(base[..., i]) for i in range(3)]); del base
    base = np.load(os.path.join(CAU, "base_B_k025_rgb16.npy")).astype(np.float32) / 65535.0
    Bk = np.dstack([warp(base[..., i]) for i in range(3)]); del base
    al = np.clip(warp(np.load(os.path.join(CAU, "mascara_fusio.npy")).astype(np.float32), cv2.INTER_LINEAR), 0, 1)
    cob = al > 0.999
    cob_ple = binary_fill_holes(cob) | (rad < 1.3 * RS)          # ⛔ la ploma es mesura a la vora EXTERIOR, no al forat lunar
    d_in = distance_transform_edt(cob_ple)
    ACHF = warp(np.load(os.path.join(CAU, "capa_achf_u16.npy")).astype(np.float32) / 65535.0)
    PAL = warp(np.load(os.path.join(CAU, "capa_passalt24_u16.npy")).astype(np.float32) / 65535.0)
    GRAN = warp(np.load(os.path.join(CAU, "capa_achf_gran_u16.npy")).astype(np.float32) / 65535.0)
    for a in (ACHF, PAL, GRAN): a[~cob] = 0.5
    marca(f"re-mostreig · cobertura {cob.mean():.3f}")
    # --- L · mitja lluna del limbe (V25) ---
    B = omple_mitja_lluna(B, al, rad, theta); Bk = omple_mitja_lluna(Bk, al, rad, theta)
    # --- V · camp exterior amb DADA: capes 12+13 de Pere igualades a la meva base ---
    # cada capa de Pere s'iguala PER SEPARAT a la meva base (ρ radial × k≤2 a 6-8,5 R☉), i a la vora
    # del rectangle de la 13 la 12 rep el guany local 13/12 (banda de 20-300 px dins de la 13, estès
    # cap enfora pel veí més proper) amb ploma de 200 px: la ronda 3 tenia un graó de 0,014-0,05
    # de display al límit del rectangle de la 13 (vora recta vertical a ~9,5 R☉, família V).
    EL, AL = {}, {}
    for k in (12, 13):
        rgb, msk, top, left = raw_capa(capes[k], W, H); A, a = a_canvas(rgb, msk, top, left, W, H)
        EL[k] = sobre(np.zeros((H, W, 3), np.float32), A, a, "normal"); AL[k] = a.astype(np.float32); del rgb, A, a
    ins13 = AL[13] > 0.5; d13 = distance_transform_edt(ins13); f13 = np.clip(d13 / 200.0, 0, 1).astype(np.float32)[..., None]
    band = ins13 & (d13 > 20) & (d13 < 300) & (AL[12] > 0.99)
    idx_nn = distance_transform_edt(~band, return_distances=False, return_indices=True)
    feather = np.clip(d_in / 120.0, 0, 1).astype(np.float32)[..., None]
    def exterior(Bx):
        rho13, rep13 = rho_display(Bx, EL[13], cob & (d_in > 60) & (AL[13] > 0.99), rad, theta, 6.0, 8.5)
        rho12, rep12 = rho_display(Bx, EL[12], cob & (d_in > 60) & (AL[12] > 0.99), rad, theta, 6.0, 8.5)
        E13 = np.clip(EL[13] * rho13, 0, 1); E12 = np.clip(EL[12] * rho12, 0, 1); del rho13, rho12
        g = np.ones((H, W, 3), np.float32)
        for c in range(3):
            R = np.where(band, E13[..., c] / np.maximum(E12[..., c], 1e-4), 1.0).astype(np.float32)
            R = art.suau_masc(R, band, 100.0); g[..., c] = R[idx_nn[0], idx_nn[1]]
        Ef = np.where(ins13[..., None], E13 * f13 + E12 * g * (1 - f13), E12 * g).astype(np.float32)
        rep_ = dict(rho13=rep13, rho12=rep12, guany_12_fora_mediana=[float(np.median(g[..., c][~ins13])) for c in range(3)],
                    salt_vora_13_abans=[float(np.median(E13[..., c][band]) - np.median(E12[..., c][band])) for c in range(3)])
        del E13, E12, g
        return Ef, rep_
    Efar, rep = exterior(B); B = np.where(cob_ple[..., None], B * feather + Efar * (1 - feather), Efar).astype(np.float32); del Efar
    Efar, rep_k = exterior(Bk); Bk = np.where(cob_ple[..., None], Bk * feather + Efar * (1 - feather), Efar).astype(np.float32); del Efar, feather, EL, AL, band, idx_nn, d13, f13
    REB["camp_exterior"] = {"font": "capes 12 i 13 de Pere igualades PER SEPARAT a la base; guany local 13/12 a la vora del rectangle de la 13 (ploma 200 px)", "rho_6-8.5Rsol": rep, "rho_base_k": rep_k, "ploma_px": 120, "ploma_mesurada_a": "vora exterior (forat lunar omplert)", "fraccio_llenc": float((~cob).mean())}
    marca(f"camp exterior amb dada de Pere igualada: {rep}")
    # --- R al camp exterior de la BASE (les capes de Pere porten el ratllat de la Sony): famílies a 8,5 R☉ ---
    FINS9 = [(int(CY + 8.5 * RS * np.sin(np.radians(a_))), int(CX + 8.5 * RS * np.cos(np.radians(a_)))) for a_ in (0, 30, 150, 180, 210, 330)]
    dins = np.ones((H, W), bool)
    fams_b, _ = art.families_ratllat(B[..., 1], dins, FINS9, pic_min=30.0, n_min=3, per_min=8, per_max=200)   # ratlles: ≤200 px
    pes_far = art.smoothstep(rad / RS, 7.5, 8.5).astype(np.float32)
    for f_ in fams_b[:3]:
        for c in range(3):
            B[..., c] = art.notch_direccional(B[..., c], f_["angle"], tol_deg=5.0, per_min=8, per_max=600, pes_espacial=pes_far)
            Bk[..., c] = art.notch_direccional(Bk[..., c], f_["angle"], tol_deg=5.0, per_min=8, per_max=600, pes_espacial=pes_far)
    fams_b2, _ = art.families_ratllat(B[..., 1], dins, FINS9, pic_min=30.0, n_min=3, per_min=8, per_max=200)
    REB["ratllat_camp_exterior_base"] = {"finestres": FINS9, "abans": fams_b, "despres": fams_b2, "notch": "famílies a ≥3 finestres, rampa 7,5→8,5 R☉"}
    marca(f"ratllat del camp exterior de la base: abans {fams_b} · després {fams_b2}")
    # --- R (mesura abans): famílies del sensor = mateix angle a finestres d'azimuts diferents ---
    fin_r = (int(CY - 8 * RS * 0.6), int(CX + 8 * RS * 0.8)); fin_r2 = (int(CY + 6 * RS * 0.7), int(CX - 6 * RS * 0.7))
    FINS = [(int(CY + 6.5 * RS * np.sin(np.radians(a_))), int(CX + 6.5 * RS * np.cos(np.radians(a_)))) for a_ in range(0, 360, 45)] + [fin_r, fin_r2]
    abans = [art.ratllat(PAL, cob, fin_r), art.ratllat(ACHF, cob, fin_r), art.ratllat(PAL, cob, fin_r2)]
    fams, per_fin = art.families_ratllat(PAL, cob, FINS, pic_min=30.0, n_min=3, per_min=8, per_max=400)
    marca(f"famílies de ratllat (≥3 finestres, pic ≥30): {fams}")
    # --- G · ghosts: marques grogues de Pere + 3 R☉ + detectats a l'ACHF (compactes, r > 4 R☉) ---
    pedacos = []
    grocs = [m_ for m_ in json.load(open(MARQUES_PERE)) if m_["color"] == "groc" and m_["area"] > 15000]
    for m_ in grocs: pedacos.append(dict(x=m_["x"], y=m_["y"], radi=int(0.55 * max(m_["w"], m_["h"])), font="marca de Pere (groc)"))
    pedacos.append(dict(x=4911, y=5014, radi=45, font="ghost 3,0 R☉ research/116"))
    det = art.blobs_rodons(ACHF, cob, rad, RS, r_min=4.0, s_lo=40, s_hi=140, k=3.5, area_min=2500, mida_max=700, omplert_min=0.45)
    for b in det[:12]:
        if all(np.hypot(b["x"] - p["x"], b["y"] - p["y"]) > 300 for p in pedacos) and 4.0 < b["r"] < 11.5 and b["amp"] > 3.5:
            pedacos.append(dict(x=b["x"], y=b["y"], radi=int(0.6 * max(b["w"], b["h"])), font=f"detectat ACHF {b['amp']:.1f}σ"))
    for p in pedacos:
        assert p["radi"] <= 400, p
        art.tapa_blob(B, (ACHF, PAL, GRAN), p["x"], p["y"], p["radi"]); art.tapa_blob(Bk, (), p["x"], p["y"], p["radi"])
    marca("pedaços: " + ", ".join(f"({p['x']},{p['y']}) r{p['radi']}" for p in pedacos))
    REB["ghosts_tapats"] = pedacos; REB["blobs_detectats_achf"] = det[:12]
    marca(f"ghosts tapats: {len(pedacos)} (Pere {len(grocs)}, detectats {len(pedacos) - len(grocs) - 1})")
    # --- R · ratllat: notch direccional a les capes de detall (zona Sony) ---
    pes_r = art.smoothstep(rad / RS, 2.65, 3.5).astype(np.float32)
    angles = [f["angle"] for f in fams[:3]] or [-45.0]                    # pics mesurats (espectrals)
    for ang_esp in angles:
        ACHF = art.notch_direccional(ACHF, ang_esp, tol_deg=5.0, per_min=8, per_max=600, pes_espacial=pes_r)
        PAL = art.notch_direccional(PAL, ang_esp, tol_deg=5.0, per_min=8, per_max=600, pes_espacial=pes_r)
        GRAN = art.notch_direccional(GRAN, ang_esp, tol_deg=5.0, per_min=8, per_max=600, pes_espacial=pes_r)
    despres = [art.ratllat(PAL, cob, fin_r), art.ratllat(ACHF, cob, fin_r), art.ratllat(PAL, cob, fin_r2)]
    fams_despres, _ = art.families_ratllat(PAL, cob, FINS, pic_min=30.0, n_min=3, per_min=8, per_max=400)
    REB["ratllat_families"] = {"finestres": FINS, "abans": fams, "per_finestra_abans": per_fin, "despres": fams_despres, "tallades": angles}
    marca(f"famílies després: {fams_despres}")
    REB["ratllat"] = {"abans_PAL_ACHF": abans, "despres_PAL_ACHF": despres, "notch": f"pics espectrals a {angles}° ±5°, 8-600 px, rampa 2,65→3,5 R☉"}
    marca(f"ratllat: abans {abans} · després {despres}")
    # --- E · esvaïment del detall on només hi ha cel ---
    fade = (1 - art.smoothstep(rad / RS, 3.5, 5.0)).astype(np.float32)
    ACHF = (0.5 + (ACHF - 0.5) * fade).astype(np.float32); PAL = (0.5 + (PAL - 0.5) * fade).astype(np.float32)
    # (l'esvaïment de la capa gran ja ve de l'etapa 1b: 32-64 px 3→4,5 R☉ · 128-256 px 5→6,5 R☉)
    # --- V · costures rectes dins de la dada (vora d'un apuntament de la Sony a ±45°, ~4,7 R☉):
    #     a la corona SOLA el residu de cel del segon apuntament hi fa un graó (~30 % a 4,7 R☉)
    #     que el detall gran dibuixa com a línia. Atenuació DECLARADA de les tres capes de detall
    #     al llarg de cada costura mesurada (Hough sobre la capa gran), σ 100 px, només r > 3,5 R☉.
    lin_abans = art.arestes_rectes(GRAN, cob & (rad > 2 * RS), centre=(CX, CY), dist_min=1.5 * RS)   # mai una recta radial (streamer)
    costures = art.agrupa_arestes(lin_abans, tol_ang=3.0, tol_dist=60.0)[:3]
    for c_ in costures:
        wl = art.pes_costura(H, W, c_, sigma=100.0, marge=400.0) * art.smoothstep(rad / RS, 3.0, 3.5)
        for cap in (GRAN, ACHF, PAL): cap[...] = 0.5 + (cap - 0.5) * (1 - wl)
    REB["costures_atenuades"] = {"linies_hough_abans": len(lin_abans), "costures": costures, "sigma_px": 100, "nomes_r_gt": "3,5 R☉", "excloses": "rectes a < 1,5 R☉ del centre (streamers)"}
    marca(f"costures rectes atenuades: {costures}")
    REB["esvaiment_detall"] = {"fi (ACHF 2-32, passa-alt 24)": "3,5→5 R☉ (declarat: a 4-5 R☉ el detall fi és gra)", "gran (ACHF 32-256)": "5→6,5 R☉ (declarat: de 5,5 R☉ enfora la corona sola és residu del model de cel)"}
    # --- portes a les capes de detall ---
    REB["H1"] = {"ACHF": art.h1_nivell(ACHF, rad, cob & (rad > 1.05 * RS), RS), "PAL": art.h1_nivell(PAL, rad, cob & (rad > 1.05 * RS), RS), "GRAN": art.h1_nivell(GRAN, rad, cob & (rad > 1.05 * RS), RS)}
    REB["blobs_despres"] = {"ACHF_fi_on_queda": art.blobs_rodons(ACHF, cob & (fade > 0.5), rad, RS, r_min=2.2, s_lo=40, s_hi=140, k=3.5, area_min=2500)[:5],
                            "GRAN": art.blobs_rodons(GRAN, cob & (rad < 5.5 * RS), rad, RS, r_min=2.2, s_lo=40, s_hi=140, k=3.5, area_min=2500)[:5]}; del fade
    marca(f"H1 {REB['H1']} · blobs després {REB['blobs_despres']}")
    # --- composició ---
    t2 = np.clip((rad / RS - 1.005) / 0.007, 0, 1); ploma = (t2 * t2 * (3 - 2 * t2)).astype(np.float32); del t2
    E01 = np.zeros((H, W, 3), np.float32)
    for k in (0, 1):
        rgb, msk, top, left = raw_capa(capes[k], W, H); A, a = a_canvas(rgb, msk, top, left, W, H); E01 = sobre(E01, A, a, "normal"); del rgb, A, a
    guarda = {}
    for k in (17, 18, 19):
        rgb, msk, top, left = raw_capa(capes[k], W, H)
        guarda[k] = dict(rgb=rgb, msk=msk, top=top, left=left, name=capes[k].name, blend=capes[k].blend_mode, op=capes[k].opacity, vis=capes[k].visible)
    g18 = guarda[18]; A18, a18 = a_canvas(g18["rgb"], g18["msk"], g18["top"], g18["left"], W, H); E01 = sobre(E01, A18, a18, "normal", g18["op"] / 255.0); del A18, a18
    comp = sobre(E01, B, ploma, "normal"); comp_base = comp.copy()
    uns = np.ones((H, W), np.float32)
    comp = sobre(comp, np.dstack([GRAN] * 3), uns, "overlay", OPACITAT_GRAN / 100)
    comp = sobre(comp, np.dstack([ACHF] * 3), uns, "overlay", OPACITAT_ACHF / 100)
    Lc = (comp[..., 0] + 2 * comp[..., 1] + comp[..., 2]) / 4.0
    REB["perfil_radial"] = art.monotonia(art.perfil_radial(Lc, rad, RS)); REB["limbe"] = art.limbe(Lc, rad, RS)
    REB["arestes_rectes_ACHF"] = art.arestes_rectes(ACHF, cob & (rad > 2 * RS), centre=(CX, CY), dist_min=1.5 * RS)[:10]; REB["arestes_rectes_GRAN"] = art.arestes_rectes(GRAN, cob & (rad > 2 * RS), centre=(CX, CY), dist_min=1.5 * RS)[:10]
    marca(f"monotonia {REB['perfil_radial']} · limbe {REB['limbe']['passa']} {REB['limbe'].get('franja_fosca')} · arestes rectes ACHF {len(REB['arestes_rectes_ACHF'])} GRAN {len(REB['arestes_rectes_GRAN'])}")
    del Lc
    # --- vista de l'alternativa (base k) amb les mateixes capes de detall, només per mirar ---
    comp_k = sobre(E01, Bk, ploma, "normal")
    for cap, op in ((GRAN, OPACITAT_GRAN), (ACHF, OPACITAT_ACHF), (PAL, OPACITAT_PASSALT)):
        comp_k = sobre(comp_k, np.dstack([cap] * 3), uns, "overlay", op / 100)
    # --- PSB ---
    shutil.copy2(V24, V26); psd = PSDImage.open(V26); capes = list(psd); hdr = psd._record.header
    for k in (19, 18, 17): capes[k].delete_layer()
    for k in list(range(2, 12)) + [12, 13]: capes[k].visible = False
    tb = psd._record.layer_and_mask_information.tagged_blocks
    for kk in list(tb.keys()):
        kb = kk.value if hasattr(kk, "value") else kk
        if kb not in (b"Lr16", b"Mt16"): del tb[kk]
    def reposa(k):
        g = guarda[k]; c = add_pixel_layer(psd, g["rgb"], g["name"], top=g["top"], left=g["left"], blend=g["blend"], opacity=g["op"], visible=g["vis"], compression=Compression.ZIP)
        if g["msk"] is not None:
            m16, mt, ml = g["msk"]; add_mask16(c, np.ascontiguousarray(m16), top=mt, left=ml)
    reposa(18)
    cb = add_pixel_layer(psd, (np.clip(B, 0, 1) * 65535 + 0.5).astype(np.uint16), "00 BASE LINEAL B · LDIC Vixen 019 + Sony 016 (ρ per canal), fons per raig, corba 0,22/0,74/0,045 · camp exterior = Sony V17 de Pere igualada · ghosts tapats · V26", blend=BlendMode.NORMAL, compression=Compression.ZIP)
    add_mask16(cb, (ploma * 65535 + 0.5).astype(np.uint16), top=0, left=0)
    cbk = add_pixel_layer(psd, (np.clip(Bk, 0, 1) * 65535 + 0.5).astype(np.uint16), "00b BASE SENSE CEL · corona + 0,25·cel (k DECLARAT, etapa 1b) · mateixa corba B i àncora · mateix exterior i pedaços · OCULTA: alternativa a la 00 · V26", visible=False, compression=Compression.ZIP)
    add_mask16(cbk, (ploma * 65535 + 0.5).astype(np.uint16), top=0, left=0); del Bk
    add_pixel_layer(psd, (np.dstack([GRAN] * 3) * 65535 + 0.5).astype(np.uint16), f"03 DETALL ACHF 32-256 px · streamers · NRGF davant · H1 · notch ratllat · esvaïment 5-6,5 R☉ · Superposar {OPACITAT_GRAN} % · V26", blend=BlendMode.OVERLAY, opacity=int(255 * OPACITAT_GRAN / 100 + 0.5), compression=Compression.ZIP)
    add_pixel_layer(psd, (np.dstack([ACHF] * 3) * 65535 + 0.5).astype(np.uint16), f"01 DETALL ACHF 2-32 px · NRGF davant · mediana de canals · S/N i H1 · notch ratllat · esvaïment 3,5-5 R☉ · Superposar {OPACITAT_ACHF} % · V26", blend=BlendMode.OVERLAY, opacity=int(255 * OPACITAT_ACHF / 100), compression=Compression.ZIP)
    add_pixel_layer(psd, (np.dstack([PAL] * 3) * 65535 + 0.5).astype(np.uint16), f"02 DETALL passa-alt σ24 px · notch ratllat · esvaïment 3,5-5 R☉ · Superposar {OPACITAT_PASSALT} % · V26", blend=BlendMode.OVERLAY, opacity=int(255 * OPACITAT_PASSALT / 100), visible=True, compression=Compression.ZIP)
    reposa(17); reposa(19); finalize_lr16(psd)
    comp = sobre(comp, np.dstack([PAL] * 3), np.ones((H, W), np.float32), "overlay", OPACITAT_PASSALT / 100)
    for k in (17, 19):
        g = guarda[k]; A, a = a_canvas(g["rgb"], g["msk"], g["top"], g["left"], W, H)
        comp = sobre(comp, A, a, "dodge" if g["blend"] == BlendMode.LINEAR_DODGE else "normal", g["op"] / 255.0); del A, a
    plans_v24 = psd._record.image_data.get_data(hdr)
    dades = [np.ascontiguousarray((np.clip(comp[..., c], 0, 1) * 65535 + 0.5).astype(np.uint16)).astype(">u2").tobytes() for c in range(3)] + list(plans_v24[3:])
    idata = ImageData(compression=Compression.RAW); idata.set_data(dades, hdr); psd._record.image_data = idata; psd._updated = False
    marca("desant…"); psd.save(V26); marca(f"desat {os.path.getsize(V26)/1e9:.2f} GB")
    # --- vistes ---
    def png(a, nom, scale=4):
        im = Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8), "RGB")
        if scale > 1: im = im.resize((W // scale, H // scale), Image.LANCZOS)
        im.save(os.path.join(OUT, nom))
    png(comp, "V26_PROPOSTA_llenc_sencer_x4.png"); png(comp_base, "V26_nomes_BASE_llenc_sencer_x4.png"); png(comp_k, "V26_ALTERNATIVA_base_sense_cel_llenc_sencer_x4.png")
    try: f = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 30)
    except Exception: f = ImageFont.load_default()
    fin = [("centre", CY, CX), ("NE_1.5Rsol", CY - 1.5 * RS * 0.7, CX + 1.5 * RS * 0.7), ("W_2.5Rsol", CY, CX - 2.5 * RS), ("NE_8Rsol_ghost", grocs[0]["y"], grocs[0]["x"]), ("N_vora_cobertura", 520, 4200), ("SW_4.7Rsol_recta_r2", 5300, 3885)]
    pan = Image.new("RGB", (len(fin) * 1034 + 10, 1024 + 60), (18, 18, 20)); dr = ImageDraw.Draw(pan)
    for j, (nom, yc, xc) in enumerate(fin):
        y0 = int(np.clip(yc - 512, 0, H - 1024)); x0 = int(np.clip(xc - 512, 0, W - 1024)); crop = comp[y0:y0 + 1024, x0:x0 + 1024]
        pan.paste(Image.fromarray((np.clip(crop, 0, 1) * 255 + 0.5).astype(np.uint8), "RGB"), (10 + j * 1034, 50)); dr.text((10 + j * 1034, 12), f"1:1 · {nom}", fill=(235, 235, 230), font=f)
    pan.save(os.path.join(OUT, "V26_PROPOSTA_finestres_1a1_inspeccio.png"))
    pan = Image.new("RGB", (len(fin) * 1034 + 10, 1024 + 60), (18, 18, 20)); dr = ImageDraw.Draw(pan)
    for j, (nom, yc, xc) in enumerate(fin):
        y0 = int(np.clip(yc - 512, 0, H - 1024)); x0 = int(np.clip(xc - 512, 0, W - 1024)); crop = comp_k[y0:y0 + 1024, x0:x0 + 1024]
        pan.paste(Image.fromarray((np.clip(crop, 0, 1) * 255 + 0.5).astype(np.uint8), "RGB"), (10 + j * 1034, 50)); dr.text((10 + j * 1034, 12), f"1:1 · {nom} · base SENSE CEL (k=0,25)", fill=(235, 235, 230), font=f)
    pan.save(os.path.join(OUT, "V26_ALTERNATIVA_base_sense_cel_finestres_1a1.png")); del comp_k
    # prova de superposició: escaquer base ↔ capa 10 i capa 09 a 1:1
    p24 = PSDImage.open(V24); L24 = list(p24)
    pan = Image.new("RGB", (3 * 1034 + 10, 1024 + 60), (18, 18, 20)); dr = ImageDraw.Draw(pan)
    for j, (idx, r_, az) in enumerate([(2, 1.27, 45), (3, 1.45, 200), (12, 3.0, 300)]):
        l = L24[idx]; x0l, y0l, x1l, y1l = l.bbox; arr = l.numpy("color")
        Lp = np.zeros((H, W, 3), np.float32); X0, Y0, X1, Y1 = max(x0l, 0), max(y0l, 0), min(x1l, W), min(y1l, H)
        Lp[Y0:Y1, X0:X1] = arr[Y0 - y0l:Y1 - y0l, X0 - x0l:X1 - x0l, :3]; del arr
        yc = int(CY + r_ * RS * np.sin(np.radians(az))); xc = int(CX + r_ * RS * np.cos(np.radians(az))); y0 = yc - 512; x0 = xc - 512
        a = comp_base[y0:y0 + 1024, x0:x0 + 1024]; b = Lp[y0:y0 + 1024, x0:x0 + 1024]
        yy, xx = np.mgrid[0:1024, 0:1024]; esc = ((yy // 128 + xx // 128) % 2 == 0)[..., None]
        def norm(v):
            lo, hi = np.percentile(v, 1), np.percentile(v, 99.5); return np.clip((v - lo) / (hi - lo + 1e-6), 0, 1)
        crop = np.where(esc, norm(a), norm(b))
        pan.paste(Image.fromarray((crop * 255 + 0.5).astype(np.uint8), "RGB"), (10 + j * 1034, 50)); dr.text((10 + j * 1034, 12), f"escaquer 128 px · base V26 ↔ {l.name[:22]} · r={r_} R☉", fill=(235, 235, 230), font=f)
    pan.save(os.path.join(OUT, "V26_PROVA_SUPERPOSICIO_escaquer.png"))
    # --- fidelitat i porta ---
    p2 = PSDImage.open(V26); c2 = list(p2); noms = [c.name for c in c2]; REB["capes_v26"] = noms; igual = 0
    for k in (17, 18, 19):
        idx = noms.index(guarda[k]["name"]); rgb2, msk2, t2_, l2 = raw_capa(c2[idx], W, H)
        ok = np.array_equal(rgb2, guarda[k]["rgb"]) and (t2_, l2) == (guarda[k]["top"], guarda[k]["left"])
        if guarda[k]["msk"] is not None: ok = ok and msk2 is not None and np.array_equal(msk2[0], guarda[k]["msk"][0]) and msk2[1:] == guarda[k]["msk"][1:]
        igual += int(ok)
    REB["fidelitat"] = f"{igual}/3"
    r = subprocess.run([PORTA, V26], capture_output=True, text=True, timeout=5400); REB["porta_photoshop"] = (r.stdout + r.stderr).strip()
    REB["fitxer"] = {"psb": V26, "bytes": os.path.getsize(V26)}
    json.dump(REB, open(os.path.join(CAU, "rebut_v26.json"), "w"), indent=1, ensure_ascii=False, default=float)
    marca(f"fidelitat {REB['fidelitat']} · Photoshop: {REB['porta_photoshop']} · FET V26")


if __name__ == "__main__":
    main()
