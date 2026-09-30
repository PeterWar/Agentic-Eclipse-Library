#!/usr/bin/env python3
"""V25 LINEAL · etapa 3: muntatge a la graella de la V23/V24 de Pere.

- Un sol re-mostreig (Lanczos) del llenç comú → V23 amb la transformació
  MESURADA a l'etapa 2, per a la base i les capes de detall.
- El camp llunyà que el llenç comú no cobreix el continuen posant les capes
  de Pere 12 (Sony, Camera Raw seu = format canònic) i 13 (fons per raig), que
  queden VISIBLES a sota; la meva base porta una màscara de cobertura amb ploma
  i s'iguala en baixa freqüència al seu exterior (finestra declarada 4,5-8 R☉,
  aplicat només de 3,5 R☉ enfora) perquè el traspàs no tingui esglaó.
- PSB NOU al costat de la V24 (mai a sobre): totes les capes de Pere es
  conserven; les 01-10 (ACR de la Vixen) i les comparacions 14-16 queden
  apagades; perles, limbe, estrelles, earthshine i reflex es tornen a posar A
  SOBRE de la base nova amb els mateixos píxels i màscares (fidelitat
  comprovada). Porta Photoshop al final.
"""
import os, sys, json, time, shutil, subprocess
import numpy as np, cv2
from scipy.ndimage import gaussian_filter, gaussian_filter1d, distance_transform_edt
from psd_tools import PSDImage
from psd_tools.constants import Compression, BlendMode
from psd_tools.psd.image_data import ImageData
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, "/Users/USUARI/Downloads/Eclipse 2026/research/tools/encaix_sony")
from psb_utils import add_pixel_layer, add_mask16, finalize_lr16

AQUI = os.path.dirname(os.path.abspath(__file__)); CAU = os.path.join(AQUI, "cau_v25")
CT = "/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals"
V24 = os.path.join(CT, "CapesTotalsV24.psb")
V25 = os.path.join(CT, "CapesTotalsV25_lineal_B.psb")
OUT = "/Users/USUARI/Desktop/Eclipse 2026/IA/output/v25_lineal_20260902"; os.makedirs(OUT, exist_ok=True)
PORTA = "/Users/USUARI/Downloads/Eclipse 2026/research/tools/capes_totals_v14/porta_photoshop.sh"
RS = 440.603; CX, CY = 5361.877, 3774.741          # R☉ i disc de C2 a la V23
OPACITAT_ACHF, OPACITAT_PASSALT = 70, 40
T0 = time.time(); REB = {}
def marca(t): print(f"[{time.time()-T0:7.1f} s] {t}", flush=True)


def raw_capa(layer, W_doc, H_doc):
    """Píxels RGB uint16 i màscara uint16 (amb el seu rectangle) tal com són al fitxer."""
    rec = layer._record; top, left = rec.top, rec.left; H, W = rec.bottom - rec.top, rec.right - rec.left
    ver = layer._psd._record.header.version
    chans = {ci.id: cd for ci, cd in zip(rec.channel_info, layer._channels)}
    rgb = np.zeros((H, W, 3), np.uint16)
    for i, cid in enumerate((0, 1, 2)):
        rgb[..., i] = np.frombuffer(chans[cid].get_data(W, H, 16, ver), ">u2").reshape(H, W)
    mask = None
    if rec.mask_data is not None and -2 in chans:
        md = rec.mask_data; mh, mw = md.bottom - md.top, md.right - md.left
        mask = (np.frombuffer(chans[-2].get_data(mw, mh, 16, ver), ">u2").reshape(mh, mw), md.top, md.left)
    return rgb, mask, top, left


def a_canvas(rgb, mask, top, left, W, H):
    """Capa i alfa (0-1) sobre el llenç sencer, en float32 0-1."""
    A = np.zeros((H, W, 3), np.float32); al = np.zeros((H, W), np.float32)
    h, w = rgb.shape[:2]; y0, x0 = max(top, 0), max(left, 0); y1, x1 = min(top + h, H), min(left + w, W)
    A[y0:y1, x0:x1] = rgb[y0 - top:y1 - top, x0 - left:x1 - left].astype(np.float32) / 65535.0
    al[y0:y1, x0:x1] = 1.0
    if mask is not None:
        m16, mt, ml = mask; mh, mw = m16.shape
        M = np.zeros((H, W), np.float32)   # fora del rectangle de la màscara: 0 (color de fons de la màscara = 0, com Photoshop per defecte)
        yy0, xx0 = max(mt, 0), max(ml, 0); yy1, xx1 = min(mt + mh, H), min(ml + mw, W)
        M[yy0:yy1, xx0:xx1] = m16[yy0 - mt:yy1 - mt, xx0 - ml:xx1 - ml].astype(np.float32) / 65535.0
        al *= M
    return A, al


def sobre(comp, A, al, mode, op=1.0):
    a = (al * op)[..., None]
    if mode == "normal":
        return comp * (1 - a) + A * a
    if mode == "dodge":                       # Linear Dodge (Add)
        return np.clip(comp + A * a, 0, 1)
    if mode == "overlay":
        ov = np.where(comp <= 0.5, 2 * comp * A, 1 - 2 * (1 - comp) * (1 - A))
        return comp * (1 - a) + ov * a
    raise ValueError(mode)


def rho_display(E, B, m, rad, theta, lo, hi):
    """ρ per canal = radial(ln r) × azimutal k≤2 de E/B a la finestra [lo,hi] R☉."""
    out = np.ones_like(B); rep = {}
    lnr = np.log(np.maximum(rad, 1.0) / RS)
    for i in range(3):
        a = m & (rad > lo * RS) & (rad < hi * RS) & (B[..., i] > 0.02) & (E[..., i] > 0.02)
        q = np.where(a, E[..., i] / np.maximum(B[..., i], 1e-6), np.nan)
        nb = 30; ed = np.linspace(np.log(lo), np.log(hi), nb + 1); ce = 0.5 * (ed[1:] + ed[:-1])
        idx = np.clip(((lnr - ed[0]) / (ed[-1] - ed[0]) * nb).astype(np.int32), 0, nb - 1)
        prof = np.array([np.nanmedian(q[a & (idx == k)]) if (a & (idx == k)).sum() > 1000 else np.nan for k in range(nb)])
        ok = np.isfinite(prof); prof = gaussian_filter1d(np.interp(ce, ce[ok], prof[ok]), 2.0, mode="nearest")
        rr = np.interp(lnr, ce, prof, left=prof[0], right=prof[-1]).astype(np.float32)
        res = np.where(a, q / rr, np.nan); nt = 72
        tb = np.clip(((theta + np.pi) / (2 * np.pi) * nt).astype(np.int32), 0, nt - 1)
        az = np.array([np.nanmedian(res[a & (tb == k)]) if (a & (tb == k)).sum() > 300 else np.nan for k in range(nt)])
        okt = np.isfinite(az); th = (np.arange(nt) + 0.5) / nt * 2 * np.pi - np.pi
        X = np.column_stack([np.ones(okt.sum()), np.cos(th[okt]), np.sin(th[okt]), np.cos(2 * th[okt]), np.sin(2 * th[okt])])
        c = np.linalg.lstsq(X, az[okt], rcond=None)[0]
        out[..., i] = rr * (c[0] + c[1] * np.cos(theta) + c[2] * np.sin(theta) + c[3] * np.cos(2 * theta) + c[4] * np.sin(2 * theta))
        rep["RGB"[i]] = {"radial": [float(prof.min()), float(prof.max())], "az": [float(v) for v in c],
                          "residu_abans": float(np.nanmedian(np.abs(q - 1))), "residu_despres": float(np.nanmedian(np.abs(np.where(a, E[..., i] / np.maximum(B[..., i] * out[..., i], 1e-6), np.nan) - 1)))}
    return out, rep


def esten_per_raig(B, cob, rad, theta, nt=2880, nr=1400):
    """Fora de la cobertura, cada raig continua amb el valor (en ln) del seu final."""
    H, W = cob.shape; out = B.copy()
    r0, r1 = 0.98 * RS, float(np.hypot(max(CX, W - CX), max(CY, H - CY))) * 1.02
    lr = np.linspace(np.log(r0), np.log(r1), nr, dtype=np.float32); th = np.linspace(-np.pi, np.pi, nt, endpoint=False, dtype=np.float32)
    rr = np.exp(lr)[None, :]; xx = CX + rr * np.cos(th)[:, None]; yy = CY + rr * np.sin(th)[:, None]
    from scipy.ndimage import map_coordinates
    pv = map_coordinates(cob.astype(np.float32), [yy, xx], order=1, mode="constant", cval=0.0) > 0.5
    ok_ray = pv.any(axis=1)
    last = np.where(ok_ray, nr - 1 - np.argmax(pv[:, ::-1], axis=1), 0)      # últim índex cobert de cada raig
    dlr = (np.log(r1) - np.log(r0)) / (nr - 1)
    ri = (np.log(np.maximum(rad, 1.0)) - np.log(r0)) / dlr; ti = (theta + np.pi) / (2 * np.pi) * nt
    fora = ~cob
    for i in range(3):
        pol = map_coordinates(np.where(cob, B[..., i], 0.0).astype(np.float32), [yy, xx], order=1, mode="constant", cval=0.0)
        lp = np.log(np.maximum(pol, 1e-4)).astype(np.float32)
        val = np.zeros(nt, np.float32)
        for k in range(nt):
            if not ok_ray[k]: continue
            a, b = max(last[k] - 24, 0), last[k] + 1                     # mitjana dels últims ~24 mostres cobertes
            val[k] = float(np.mean(lp[k, a:b][pv[k, a:b]])) if pv[k, a:b].any() else lp[k, last[k]]
        # raigs sense cobertura: interpola circularment
        if (~ok_ray).any():
            idx = np.arange(nt); val = np.interp(idx, idx[ok_ray], val[ok_ray], period=nt)
        val_s = np.concatenate([val[-30:], val, val[:30]]); from scipy.ndimage import gaussian_filter1d
        val = gaussian_filter1d(val_s, 6.0)[30:-30]                        # suau en azimut
        ext = np.exp(np.interp(ti, np.arange(nt), val, period=nt)).astype(np.float32)
        out[..., i] = np.where(fora, ext, B[..., i])
    return out


def omple_mitja_lluna(B, al, rad, theta, nt=2880):
    """Per raig, on la base no té dada entre 0,99 i 1,08 R☉ (forat de la cadena més gran
    que el disc de Pere), extrapolació LINEAL cap endins dels primers 16 px vàlids."""
    out = B.copy(); r0, r1 = 0.99 * RS, 1.10 * RS; nr = int(r1 - r0) + 1
    rr = np.linspace(r0, r1, nr, dtype=np.float32); th = np.linspace(-np.pi, np.pi, nt, endpoint=False, dtype=np.float32)
    xx = CX + rr[None, :] * np.cos(th)[:, None]; yy = CY + rr[None, :] * np.sin(th)[:, None]
    from scipy.ndimage import map_coordinates
    pv = map_coordinates(al, [yy, xx], order=1, mode="constant", cval=0.0) > 0.98
    first = np.argmax(pv, axis=1); okr = pv.any(axis=1)
    zona = (rad >= r0) & (rad <= 1.08 * RS) & (al < 0.98)
    ri = (rad - r0); ti = (theta + np.pi) / (2 * np.pi) * nt
    for i in range(3):
        pol = map_coordinates(B[..., i], [yy, xx], order=1, mode="nearest")
        val = np.zeros((nt, nr), np.float32)
        for k in range(nt):
            if not okr[k]: continue
            f0 = first[k]; f1 = min(f0 + 16, nr - 1)
            x = rr[f0:f1 + 1]; y = pol[k, f0:f1 + 1]
            a, b = np.polyfit(x, y, 1) if f1 > f0 + 3 else (0.0, float(y[0]))
            val[k] = np.clip(a * rr + b, 0.0, 1.0); val[k, f0:] = pol[k, f0:]
        ext = map_coordinates(val, [ti, np.clip(ri, 0, nr - 1)], order=1, mode="wrap").astype(np.float32)
        out[..., i] = np.where(zona, ext, B[..., i])
    return out


def main():
    G = json.load(open(os.path.join(CAU, "geometria_v23.json"))); M1 = np.array(G["M_llenc_a_v23"], np.float64)
    REB["geometria"] = {k: G.get(k) for k in ("rotacio_total_deg", "escala_total", "rms_offset_px", "mediana_offset_px", "p90_offset_px", "dist_sol_disc_px", "nota")}
    psd = PSDImage.open(V24); W, H = psd.width, psd.height; capes = list(psd); assert len(capes) == 20
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); rad = np.hypot(yy - CY, xx - CX); theta = np.arctan2(yy - CY, xx - CX); del yy, xx
    # 1. un sol re-mostreig llenç → V23
    def warp(a, interp=cv2.INTER_LANCZOS4):
        return cv2.warpAffine(a, M1, (W, H), flags=interp, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    base = np.load(os.path.join(CAU, "base_B_rgb16.npy")).astype(np.float32) / 65535.0
    B = np.dstack([warp(base[..., i]) for i in range(3)]); del base
    mf = np.load(os.path.join(CAU, "mascara_fusio.npy")).astype(np.float32)
    al = np.clip(warp(mf, cv2.INTER_LINEAR), 0, 1); del mf
    cob = al > 0.999
    d = distance_transform_edt(cob); ploma = np.clip(d / 80.0, 0, 1).astype(np.float32)   # ploma de 80 px a la vora de la cobertura
    # ⛔ Les capes de perles (0) i limbe (1) de Pere són les de MÉS AVALL de la pila i
    #    tenen màscares gairebé opaques: el que les deixa veure són les màscares de les
    #    capes de sobre. La base, doncs, s'obre al limbe amb una rampa radial (1,02→1,09 R☉),
    #    com les seves capes 09/10, i les capes 0 i 1 es queden on són.
    t_ = np.clip((rad / RS - 1.010) / 0.008, 0, 1); ploma_limbe = (t_ * t_ * (3 - 2 * t_)).astype(np.float32); del t_   # la base té dada des d'1,013 R☉
    ACHF = warp(np.load(os.path.join(CAU, "capa_achf_u16.npy")).astype(np.float32) / 65535.0)
    PAL = warp(np.load(os.path.join(CAU, "capa_passalt24_u16.npy")).astype(np.float32) / 65535.0)
    for a in (ACHF, PAL):
        a[~cob] = 0.5
    marca(f"re-mostreig fet · cobertura de la base {cob.mean():.3f} del llenç de Pere")
    # ⛔ GHOST DE L'EIX ÒPTIC DE LA SONY (research/116: reflex intern a ~3,0 R☉, només al
    #    primer apuntament). Tapat amb la mediana anular, base i capes de detall; DECLARAT.
    gx0, gy0 = 4912, 5016
    win = gaussian_filter(ACHF[gy0 - 60:gy0 + 60, gx0 - 60:gx0 + 60] - 0.5, 12.0)   # ⛔ al passa-alt: la base té gradient radial i el màxim tira cap al Sol
    ky, kx = np.unravel_index(np.argmax(win), win.shape); gy, gx = gy0 - 60 + int(ky), gx0 - 60 + int(kx)
    yy_, xx_ = np.mgrid[gy - 120:gy + 120, gx - 120:gx + 120]; rr_ = np.hypot(yy_ - gy, xx_ - gx)
    anell = (rr_ >= 60) & (rr_ < 100); pes_g = (1 - np.clip((rr_ - 38) / 14.0, 0, 1)).astype(np.float32)
    sub = B[gy - 120:gy + 120, gx - 120:gx + 120]
    for i in range(3):
        med = float(np.median(sub[..., i][anell])); sub[..., i] = sub[..., i] * (1 - pes_g) + med * pes_g
    for a in (ACHF, PAL):
        sa = a[gy - 120:gy + 120, gx - 120:gx + 120]; sa[...] = sa * (1 - pes_g) + 0.5 * pes_g
    REB["ghost_sony_tapat"] = {"centre_v23_xy": [gx, gy], "r_Rsol": float(np.hypot(gx - CX, gy - CY) / RS), "radi_px": 45, "metode": "mediana anular 60-100 px, base i capes de detall"}
    marca(f"ghost de la Sony tapat a ({gx},{gy}) · r={np.hypot(gx - CX, gy - CY) / RS:.2f} R☉")
    # 2. l'exterior de Pere (capes 12 i 13 amb màscares) com a camp llunyà i referència d'igualació
    guarda = {}
    for k in (17, 18, 19):
        rgb, msk, top, left = raw_capa(capes[k], W, H)
        guarda[k] = dict(rgb=rgb, msk=msk, top=top, left=left, name=capes[k].name, blend=capes[k].blend_mode, op=capes[k].opacity, vis=capes[k].visible)
    E = np.zeros((H, W, 3), np.float32)
    for k in (0, 1):
        rgb, msk, top, left = raw_capa(capes[k], W, H); A, a = a_canvas(rgb, msk, top, left, W, H); E = sobre(E, A, a, "normal"); del rgb, A, a
    # ⛔ El camp exterior de Pere (capes 12+13, Camera Raw seu) és més clar que la base i
    #    igualar-hi la base des de 3,5 R☉ deixava un ANELL FOSC a 2,5-4 R☉ (vist a la vista
    #    del 02-09). La base no depèn de cap referència externa: fora de la cobertura del
    #    llenç comú s'ESTÉN PER RAIG (el valor del final de cada raig, en ln, constant cap
    #    enfora: és cel, cosmètica DECLARADA com a la V19), i les capes 12 i 13 s'apaguen.
    B = esten_per_raig(B, cob, rad, theta)
    feather = np.clip(d / 40.0, 0, 1).astype(np.float32)            # 40 px de ploma a la vora de la cobertura
    REB["extensio_per_raig"] = {"fraccio_llenc_estesa": float((~cob).mean()), "ploma_px": 40}
    # ⛔ El forat lunar de la cadena és més gran que el disc de C2 de Pere (vora de la
    #    base a 1,010-1,050 R☉ segons l'azimut, fins a 22 px): allà on la base no té dada
    #    ha de deixar veure la capa 11 de Pere (limbe, 1/500 s). Alfa = rampa del limbe × validesa.
    # ⛔ 02-09, 5a ronda: la capa EARTHSHINE V24e de Pere porta una BANDA exterior fins a
    #    ~1,08 R☉ amb la còpia del seu compost V23 (nivell 0,51). Sobre la base nova (0,76
    #    a 1,03) quedava com una franja FOSCA de 35 px. La base va ARA per sobre de la capa
    #    18 des d'1,012 R☉, i els 4-22 px on la cadena no té dada s'omplen per raig
    #    (extrapolació lineal cap endins, DECLARADA). El disc i el perímetre interior
    #    continuen sent de la capa 18; les perles (capa 0) surten per la banda d'1,00-1,012.
    B = omple_mitja_lluna(B, al, rad, theta)
    t2 = np.clip((rad / RS - 1.005) / 0.007, 0, 1); ploma = (t2 * t2 * (3 - 2 * t2)).astype(np.float32); del t2
    REB["mitja_lluna_omplerta"] = {"metode": "extrapolació lineal cap endins per raig, 0,99-1,08 R☉ on la base no té dada", "declarat": True}
    g18 = guarda[18]; A18, a18 = a_canvas(g18["rgb"], g18["msk"], g18["top"], g18["left"], W, H)
    E = sobre(E, A18, a18, "normal", g18["op"] / 255.0); del A18, a18
    comp = sobre(E, B, ploma, "normal")
    comp_base = comp.copy()
    # gate: el perfil radial de la base composta ha de ser MONÒTON cap enfora d'1,2 R☉
    Lc = (comp[..., 0] + 2 * comp[..., 1] + comp[..., 2]) / 4.0
    rr = rad / RS; prof = []
    for r0 in np.arange(1.2, 12.0, 0.1):
        s_ = (rr > r0) & (rr < r0 + 0.1)
        if s_.sum() > 500: prof.append((round(float(r0), 1), float(np.median(Lc[s_]))))
    pujades = [(a[0], round(b[1] - a[1], 4)) for a, b in zip(prof, prof[1:]) if b[1] - a[1] > 0.005]
    REB["perfil_radial_monoton"] = {"pujades_mes_de_0.005": pujades, "PASSA": len(pujades) == 0, "perfil": prof[::5]}
    marca(f"perfil radial monòton: {'PASSA' if not pujades else pujades}")
    # perfil fi al limbe (banda fosca?)
    prof_limbe = [(round(float(r0), 3), float(np.median(Lc[(rr > r0) & (rr < r0 + 0.01)]))) for r0 in np.arange(0.99, 1.16, 0.01)]
    REB["perfil_limbe"] = prof_limbe; del Lc
    comp = sobre(comp, np.dstack([ACHF] * 3), np.ones((H, W), np.float32), "overlay", OPACITAT_ACHF / 100)
    marca("composició base+detall feta")
    # 3. PSB nou
    shutil.copy2(V24, V25); psd = PSDImage.open(V25); capes = list(psd); hdr = psd._record.header
    for k in (19, 18, 17):
        capes[k].delete_layer()
    for k in list(range(2, 12)) + [12, 13]:   # les ACR de la Vixen, la Sony amb Camera Raw i el fons per raig queden apagades
        capes[k].visible = False
    tb = psd._record.layer_and_mask_information.tagged_blocks
    for kk in list(tb.keys()):
        kb = kk.value if hasattr(kk, "value") else kk
        if kb not in (b"Lr16", b"Mt16"):
            del tb[kk]
    reposa_18 = True
    g18 = guarda[18]
    c18 = add_pixel_layer(psd, g18["rgb"], g18["name"], top=g18["top"], left=g18["left"], blend=g18["blend"], opacity=g18["op"], visible=g18["vis"], compression=Compression.ZIP)
    if g18["msk"] is not None:
        m16, mt, ml = g18["msk"]; add_mask16(c18, np.ascontiguousarray(m16), top=mt, left=ml)
    b16 = (np.clip(B, 0, 1) * 65535 + 0.5).astype(np.uint16)
    cb = add_pixel_layer(psd, b16, "00 BASE LINEAL B · LDIC Vixen 019 + Sony 016 fusionats (ρ per canal), fons per raig 2,45-3,25, corba 0,22/0,74/0,045 sobre lluminància · V25", blend=BlendMode.NORMAL, compression=Compression.ZIP)
    add_mask16(cb, (ploma * 65535 + 0.5).astype(np.uint16), top=0, left=0)   # s'obre només dins d'1,025 R☉ (perles i limbe de Pere a sota)
    ca = add_pixel_layer(psd, (np.dstack([ACHF] * 3) * 65535 + 0.5).astype(np.uint16), f"01 DETALL ACHF 2-32 px · NRGF davant · mediana de canals · S/N i H1 · Superposar {OPACITAT_ACHF} % (el dial de Claridad/Textura sense halos) · V25", blend=BlendMode.OVERLAY, opacity=int(255 * OPACITAT_ACHF / 100), compression=Compression.ZIP)
    cp = add_pixel_layer(psd, (np.dstack([PAL] * 3) * 65535 + 0.5).astype(np.uint16), f"02 DETALL passa-alt σ24 px · Superposar {OPACITAT_PASSALT} % · apagada: dosa-la tu · V25", blend=BlendMode.OVERLAY, opacity=int(255 * OPACITAT_PASSALT / 100), visible=False, compression=Compression.ZIP)
    del b16
    def reposa(k):
        g = guarda[k]
        c = add_pixel_layer(psd, g["rgb"], g["name"], top=g["top"], left=g["left"], blend=g["blend"], opacity=g["op"], visible=g["vis"], compression=Compression.ZIP)
        if g["msk"] is not None:
            m16, mt, ml = g["msk"]; add_mask16(c, np.ascontiguousarray(m16), top=mt, left=ml)
    for k in (17, 19):
        reposa(k)
    finalize_lr16(psd)
    marca("capes inserides")
    # composició sencera per a la fusionada i les vistes
    for k in (17, 19):
        g = guarda[k]; A, a = a_canvas(g["rgb"], g["msk"], g["top"], g["left"], W, H)
        mode = "dodge" if g["blend"] == BlendMode.LINEAR_DODGE else "normal"
        if g["vis"]:
            comp = sobre(comp, A, a, mode, g["op"] / 255.0)
        del A, a
    # ⛔ la capçalera diu 4 canals (RGB + transparència fusionada, bloc Mt16): la
    #    fusionada s'escriu amb els QUATRE plans, el quart copiat de la V24 tal qual.
    #    Amb només tres, Photoshop refusa amb «les opcions d'obertura no són correctes».
    plans_v24 = psd._record.image_data.get_data(hdr)
    dades = [np.ascontiguousarray((np.clip(comp[..., c], 0, 1) * 65535 + 0.5).astype(np.uint16)).astype(">u2").tobytes() for c in range(3)]
    dades += list(plans_v24[3:])
    REB["fusionada_canals"] = len(dades)
    idata = ImageData(compression=Compression.RAW); idata.set_data(dades, hdr); psd._record.image_data = idata; psd._updated = False
    marca("desant el PSB…"); psd.save(V25); marca(f"desat {os.path.getsize(V25)/1e9:.2f} GB")
    # 4. vistes (llenç sencer ×4, i finestres 1:1 declarades d'inspecció)
    def png(a, nom, scale=4):
        im = Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8), "RGB")
        if scale > 1:
            im = im.resize((W // scale, H // scale), Image.LANCZOS)
        im.save(os.path.join(OUT, nom))
    png(comp, "V25_PROPOSTA_llenc_sencer_x4.png"); png(comp_base, "V25_nomes_BASE_llenc_sencer_x4.png")
    fin = [("centre_perles_earthshine", CY, CX), ("NE_1.5Rsol", CY - 1.5 * RS * 0.7, CX + 1.5 * RS * 0.7), ("W_2.5Rsol", CY, CX - 2.5 * RS), ("SW_4Rsol", CY + 4 * RS * 0.7, CX - 4 * RS * 0.7)]
    try: f = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 30)
    except Exception: f = ImageFont.load_default()
    pan = Image.new("RGB", (4 * 1024 + 50, 1024 + 60), (18, 18, 20)); dr = ImageDraw.Draw(pan)
    for j, (nom, yc, xc) in enumerate(fin):
        y0, x0 = int(yc) - 512, int(xc) - 512; crop = comp[y0:y0 + 1024, x0:x0 + 1024]
        pan.paste(Image.fromarray((np.clip(crop, 0, 1) * 255 + 0.5).astype(np.uint8), "RGB"), (10 + j * 1034, 50)); dr.text((10 + j * 1034, 12), f"1:1 · {nom}", fill=(235, 235, 230), font=f)
    pan.save(os.path.join(OUT, "V25_PROPOSTA_finestres_1a1_inspeccio.png"))
    # 5. fidelitat i porta Photoshop
    p2 = PSDImage.open(V25); c2 = list(p2)
    noms = [c.name for c in c2]; REB["capes_v25"] = noms
    igual = 0
    for k in (17, 18, 19):
        idx = noms.index(guarda[k]["name"]); rgb2, msk2, t2, l2 = raw_capa(c2[idx], W, H)
        ok = np.array_equal(rgb2, guarda[k]["rgb"]) and (t2, l2) == (guarda[k]["top"], guarda[k]["left"])
        if guarda[k]["msk"] is not None:
            ok = ok and msk2 is not None and np.array_equal(msk2[0], guarda[k]["msk"][0]) and msk2[1:] == guarda[k]["msk"][1:]
        igual += int(ok)
    REB["fidelitat_capes_reposades"] = f"{igual}/3"; marca(f"fidelitat de les capes reposades: {igual}/3")
    r = subprocess.run([PORTA, V25], capture_output=True, text=True, timeout=5400)
    REB["porta_photoshop"] = (r.stdout + r.stderr).strip(); marca(f"Photoshop diu: {REB['porta_photoshop']}")
    REB["fitxer"] = {"psb": V25, "bytes": os.path.getsize(V25)}; REB["opacitats"] = {"achf": OPACITAT_ACHF, "passalt": OPACITAT_PASSALT}
    json.dump(REB, open(os.path.join(CAU, "rebut_etapa3.json"), "w"), indent=1, ensure_ascii=False, default=float)
    marca("FET etapa 3")


if __name__ == "__main__":
    main()
