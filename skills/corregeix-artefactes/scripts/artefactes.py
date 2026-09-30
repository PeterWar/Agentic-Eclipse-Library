#!/usr/bin/env python3
"""Detectors i correccions d'artefactes del postprocessat de la corona.

S'executa ABANS de qualsevol filtre nou i DESPRÉS de cada muntatge (norma de
Pere, 04-09-2026). Tot al rectangle sencer; cap operació circular llevat de
les declarades (pedaç d'un ghost, esvaïment del detall on només hi ha cel).

Famílies que cobreix (vegeu ../SKILL.md):
  G  ghosts (reflex del Sol a la lent de la Sony: rodons, ~100-500 px, febles)
  R  ratllat del patró fix del sensor (família espectral a un angle fix)
  V  vores rectes: seams de cobertura, extensions, rectangles de capes
  L  limbe: franja fosca o clara entre les perles i la corona
  M  monotonia del perfil radial (anells clars o foscos)
  H  H1: nivell per anell de les capes de detall (0,5-neutres)
  P  marques pintades per Pere sobre un TIF: ingestió i finestres
"""
import numpy as np, cv2, json, os
from scipy.ndimage import gaussian_filter, label, find_objects


# ------------------------------------------------------------------ utilitats
def polars(H, W, cx, cy):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    return np.hypot(yy - cy, xx - cx), np.degrees(np.arctan2(yy - cy, xx - cx))


def suau_masc(a, m, s):
    mf = m.astype(np.float32)
    return gaussian_filter(np.where(m, a, 0.0).astype(np.float32), s) / np.maximum(gaussian_filter(mf, s), 1e-6)


def smoothstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------ G · ghosts
def blobs_rodons(img, m, rad, RS, r_min=2.0, s_lo=40.0, s_hi=140.0, k=3.5, area_min=2500, rodonesa_min=0.55,
                 mida_max=700, omplert_min=0.45):
    """Taques rodones febles: DoG (s_lo − s_hi) sobre `img` dins de `m`, llindar k·σ robust,
    components COMPACTES: rodonesa (costat curt/llarg) ≥ rodonesa_min, costat llarg ≤ mida_max i
    àrea/caixa ≥ omplert_min. ⛔ Sense el sostre de mida i l'ompliment, una component en forma
    d'anell que abraça el Sol té el centroide al Sol i una caixa de 5000 px: a la V26 (04-09) un
    "blob" així va fer tapar la corona sencera. Torna dicts (x, y, w, h, area, r, amp, rodonesa)."""
    mm = m & (rad > r_min * RS)
    dog = np.where(mm, suau_masc(img, mm, s_lo) - suau_masc(img, mm, s_hi), 0.0)
    v = dog[mm]; med = np.median(v); sig = 1.4826 * np.median(np.abs(v - med))
    lab, n = label((dog - med) > k * sig); out = []
    for i, sl in enumerate(find_objects(lab), 1):
        c = lab[sl] == i; area = int(c.sum())
        if area < area_min: continue
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        rod = min(w, h) / max(w, h)
        if rod < rodonesa_min or max(w, h) > mida_max or area / float(w * h) < omplert_min: continue
        ys, xs = np.nonzero(c); yc = sl[0].start + ys.mean(); xc = sl[1].start + xs.mean()
        out.append(dict(x=int(xc), y=int(yc), w=int(w), h=int(h), area=area, r=float(rad[int(yc), int(xc)] / RS),
                        amp=float((dog[sl][c].max() - med) / max(sig, 1e-9)), rodonesa=round(rod, 2)))
    out.sort(key=lambda d: -d["amp"]); return out


def tapa_blob(B, capes_detall, x, y, radi, ploma=14, radi_max=400):
    """Pedaç DECLARAT: la base rep la mediana anular (radi+15 … radi+55) per canal amb ploma;
    les capes de detall (0,5-neutres) hi van a 0,5. Modifica in situ. ⛔ Refusa radis > radi_max:
    un pedaç més gran que un ghost no és un pedaç, és tapar la imatge."""
    if radi > radi_max:
        raise ValueError(f"pedaç de radi {radi} px > {radi_max}: no és un ghost")
    H, W = B.shape[:2]; R = int(radi + 60)
    y0, y1, x0, x1 = max(y - R, 0), min(y + R, H), max(x - R, 0), min(x + R, W)
    yy, xx = np.mgrid[y0:y1, x0:x1]; rr = np.hypot(yy - y, xx - x)
    anell = (rr >= radi + 15) & (rr < radi + 55); pes = (1 - np.clip((rr - (radi - ploma)) / (2 * ploma), 0, 1)).astype(np.float32)
    sub = B[y0:y1, x0:x1]
    for i in range(B.shape[2] if B.ndim == 3 else 1):
        ch = sub[..., i] if B.ndim == 3 else sub
        med = float(np.median(ch[anell])); ch[...] = ch * (1 - pes) + med * pes
    for D in capes_detall:
        d = D[y0:y1, x0:x1]; d[...] = d * (1 - pes) + 0.5 * pes


def tapa_inpaint(B, x, y, radi, ploma=10):
    """Pedaç per INPAINTING (Telea) d'un disc de `radi` px: el forat s'omple des de la vora amb
    continuïtat, sense cap graó de nivell (la mediana anular deixava una «moneda» plana amb halo,
    V26). Modifica in situ; val per a (H,W) i (H,W,3). Radi = el nucli real del ghost (25 px a
    3 R☉ el 2026), no el seu halo: el que es tapa és llum del ghost, res més."""
    H, W = B.shape[:2]; R = int(radi + ploma + 40)
    y0, y1, x0, x1 = max(y - R, 0), min(y + R, H), max(x - R, 0), min(x + R, W)
    yy, xx = np.mgrid[y0:y1, x0:x1]; rr = np.hypot(yy - y, xx - x)
    forat = (rr <= radi).astype(np.uint8); pes = (1 - np.clip((rr - (radi - ploma)) / (2 * ploma), 0, 1)).astype(np.float32)
    sub = B[y0:y1, x0:x1]; chans = range(B.shape[2]) if B.ndim == 3 else [None]
    for i in chans:
        ch = sub[..., i] if i is not None else sub
        lo, hi = float(np.nanmin(ch)), float(np.nanmax(ch)); esc = max(hi - lo, 1e-9)
        u8 = np.clip((ch - lo) / esc * 255.0, 0, 255).astype(np.uint8)          # Telea vol 8 bits: es fa a 16 nivells
        u16 = np.clip((ch - lo) / esc * 65535.0, 0, 65535).astype(np.uint16)
        fill8 = cv2.inpaint(u8, forat, 3, cv2.INPAINT_TELEA).astype(np.float32) / 255.0 * esc + lo
        fill16 = cv2.inpaint(u16, forat, 3, cv2.INPAINT_TELEA).astype(np.float32) / 65535.0 * esc + lo if u16.dtype == np.uint16 else fill8
        fill16 = gaussian_filter(fill16, 3.0)      # Telea deixa una costura al centre del disc (un puntet a la V27 ronda 4): es fon
        ch[...] = ch * (1 - pes) + fill16 * pes


def clona_textura(B, x, y, radi, dx, dy, sigma=8.0, ploma=10):
    """Després d'un inpaint (llis), el disc es veu com una MONEDA dins d'un camp amb textura (V27
    ronda 2). Com el tampó de clonar de Photoshop: s'hi afegeix la textura d'alta freqüència
    (B − G(B; σ)) d'un veí desplaçat (dx, dy) — al MATEIX radi (tangencial), perquè l'estadística del
    gra sigui la mateixa — amb ploma. DECLARAT al rebut. Modifica in situ (H,W) o (H,W,3)."""
    H, W = B.shape[:2]; R = int(radi + ploma + 4)
    y0, y1, x0, x1 = y - R, y + R, x - R, x + R; sy0, sy1, sx0, sx1 = y0 + dy, y1 + dy, x0 + dx, x1 + dx
    if min(y0, x0, sy0, sx0) < 0 or y1 > H or sy1 > H or x1 > W or sx1 > W: raise ValueError("finestra fora del llenç")
    yy, xx = np.mgrid[y0:y1, x0:x1]; rr = np.hypot(yy - y, xx - x); pes = (1 - np.clip((rr - (radi - ploma)) / (2 * ploma), 0, 1)).astype(np.float32)
    dst = B[y0:y1, x0:x1]; src = B[sy0:sy1, sx0:sx1]
    chans = range(B.shape[2]) if B.ndim == 3 else [None]
    for i in chans:
        d = dst[..., i] if i is not None else dst; s_ = src[..., i] if i is not None else src
        tex = s_ - gaussian_filter(s_, sigma); d[...] = d + tex * pes


def corregeix_bol(B, x, y, r_in=25.0, r_out=130.0, r_ref=(130.0, 180.0), nb=30):
    """Al voltant d'un ghost, el compost pot portar un BOL radialment simètric (a 3 R☉ el 2026: −1 a
    −1,8 % de 30 a 105 px) que un passa-alt gran ensenya com una taca fosca. Es mesura la corba
    radial (mediana per anell de la luminància, normalitzada al nivell de r_ref) i es divideix
    per ella entre r_in i r_out (ploma a la vora): es conserva la textura, no s'inventa res.
    Modifica in situ (H,W,3) o (H,W). Torna la corba mesurada (r, guany)."""
    H, W = B.shape[:2]; R = int(r_ref[1] + 5); y0, y1, x0, x1 = max(y - R, 0), min(y + R, H), max(x - R, 0), min(x + R, W)
    yy, xx = np.mgrid[y0:y1, x0:x1]; rr = np.hypot(yy - y, xx - x); sub = B[y0:y1, x0:x1]
    L = (sub[..., 0] + 2 * sub[..., 1] + sub[..., 2]) / 4.0 if B.ndim == 3 else sub
    ref = float(np.median(L[(rr >= r_ref[0]) & (rr < r_ref[1])]))
    edges = np.linspace(r_in, r_out, nb + 1); cen = 0.5 * (edges[1:] + edges[:-1]); prof = np.ones(nb)
    for k in range(nb):
        sel = (rr >= edges[k]) & (rr < edges[k + 1])
        if sel.sum() > 20: prof[k] = float(np.median(L[sel])) / max(ref, 1e-9)
    prof = gaussian_filter(prof, 1.5, mode="nearest"); guany = 1.0 / np.maximum(prof, 0.5)
    g = np.interp(rr, cen, guany, left=guany[0], right=1.0).astype(np.float32)
    pes = (1 - smoothstep(rr, r_out - 20, r_out)).astype(np.float32) * (rr >= 0)
    g = 1.0 + (g - 1.0) * pes
    if B.ndim == 3:
        for i in range(3): sub[..., i] *= g
    else: sub *= g
    return list(zip([round(float(c), 1) for c in cen], [round(float(v), 4) for v in guany]))


# ------------------------------------------------------------------ R · ratllat
def _sense_pla(w):
    """Resta el pla ajustat (a + b·x + c·y): el gradient d'una imatge NO neutra (la base, el
    cel) fuita a les freqüències més baixes al llarg dels eixos i es disfressa de família."""
    n = w.shape[0]; yy, xx = np.mgrid[0:n, 0:n].astype(np.float32); A = np.column_stack([np.ones(n * n), xx.ravel(), yy.ravel()])
    coef, *_ = np.linalg.lstsq(A, w.ravel().astype(np.float64), rcond=None)
    return (w - (coef[0] + coef[1] * xx + coef[2] * yy)).astype(np.float32)


def _hann2(n):
    h = np.hanning(n).astype(np.float32); return h[:, None] * h[None, :]


def ratllat(det, m, centre, mida=1024, per_min=8.0, per_max=400.0):
    """Espectre 2D d'una finestra d'una capa de detall (0,5-neutra) i el pic
    direccional dominant: (període px, orientació °, potència pic / mediana de l'anell)."""
    yc, xc = centre; h = mida // 2
    win = det[yc - h:yc + h, xc - h:xc + h] - 0.5
    if win.shape != (mida, mida) or not m[yc - h:yc + h, xc - h:xc + h].all():
        return None
    win = _sense_pla(win) * _hann2(mida)
    F = np.abs(np.fft.fftshift(np.fft.fft2(win))) ** 2
    yy, xx = np.mgrid[0:mida, 0:mida]; rr = np.hypot(yy - h, xx - h)
    ok = (rr >= mida / per_max) & (rr <= mida / per_min); F2 = np.where(ok, F, 0)
    ky, kx = np.unravel_index(np.argmax(F2), F2.shape)
    per = mida / max(np.hypot(ky - h, kx - h), 1e-6); ang = float(np.degrees(np.arctan2(ky - h, kx - h)))
    an = np.abs(rr - np.hypot(ky - h, kx - h)) < 2
    return dict(periode_px=round(float(per), 1), orientacio_deg=round(ang, 1), pic_sobre_anell=round(float(F2.max() / max(np.median(F[an]), 1e-9)), 1), rms=float(win.std()))


def pics_espectrals(det, m, centre, mida=1024, per_min=8.0, per_max=400.0, n=3, sep_deg=6.0):
    """Els `n` pics direccionals més forts d'una finestra (cadascun amb la seva família ±sep_deg
    exclosa abans de buscar el següent). Torna llista de dicts com `ratllat` o None."""
    yc, xc = centre; h = mida // 2
    win = det[yc - h:yc + h, xc - h:xc + h] - 0.5
    if win.shape != (mida, mida) or not m[yc - h:yc + h, xc - h:xc + h].all():
        return None
    win = _sense_pla(win) * _hann2(mida)          # ⛔ sense això el gradient de la imatge fuita als eixos (V26 ronda 6)
    F = np.abs(np.fft.fftshift(np.fft.fft2(win))) ** 2
    yy, xx = np.mgrid[0:mida, 0:mida]; rr = np.hypot(yy - h, xx - h); ang = np.degrees(np.arctan2(yy - h, xx - h))
    ok = (rr >= mida / per_max) & (rr <= mida / per_min); out = []
    for _ in range(n):
        F2 = np.where(ok, F, 0); ky, kx = np.unravel_index(np.argmax(F2), F2.shape)
        if F2.max() <= 0: break
        a = float(np.degrees(np.arctan2(ky - h, kx - h))); an = np.abs(rr - np.hypot(ky - h, kx - h)) < 2
        out.append(dict(periode_px=round(float(mida / max(np.hypot(ky - h, kx - h), 1e-6)), 1), orientacio_deg=round(a, 1),
                        pic_sobre_anell=round(float(F2.max() / max(np.median(F[an]), 1e-9)), 1)))
        d = np.abs(((ang - a + 90.0) % 180.0) - 90.0); ok = ok & (d > sep_deg)
    return out


def families_ratllat(det, m, finestres, pic_min=30.0, n_min=2, sep_deg=6.0, **kw):
    """Famílies de ratlles DEL SENSOR: un pic espectral que surt al MATEIX angle (±sep_deg) a
    ≥ n_min finestres d'azimuts diferents amb pic/anell ≥ pic_min. Una estructura real (streamer,
    arc) canvia d'angle amb l'azimut; un patró fix del sensor, no. Torna [(angle, n_finestres,
    pic_mitjà, període_mitjà)] ordenat per força, i el detall per finestra."""
    per_fin = {f: pics_espectrals(det, m, f, **kw) for f in finestres}
    cands = [dict(fin=f, **p) for f, ps in per_fin.items() if ps for p in ps if p["pic_sobre_anell"] >= pic_min]
    fams = []
    for c in sorted(cands, key=lambda d: -d["pic_sobre_anell"]):
        for fam in fams:
            if abs(((c["orientacio_deg"] - fam["angle"] + 90.0) % 180.0) - 90.0) <= sep_deg:
                if c["fin"] not in fam["fins"]: fam["fins"].append(c["fin"]); fam["pics"].append(c["pic_sobre_anell"]); fam["pers"].append(c["periode_px"])
                break
        else:
            fams.append(dict(angle=c["orientacio_deg"], fins=[c["fin"]], pics=[c["pic_sobre_anell"]], pers=[c["periode_px"]]))
    out = [dict(angle=f["angle"], n_finestres=len(f["fins"]), pic_mitja=round(float(np.mean(f["pics"])), 1), periode_mitja=round(float(np.mean(f["pers"])), 1))
           for f in fams if len(f["fins"]) >= n_min]
    return sorted(out, key=lambda d: -d["pic_mitja"]), {str(k): v for k, v in per_fin.items()}


def notch_direccional(det, orientacio_espectral_deg, tol_deg=4.0, per_min=8.0, per_max=600.0, pes_espacial=None):
    """Treu del detall la família de ratlles el PIC ESPECTRAL de la qual és a
    `orientacio_espectral_deg` (el número que torna `ratllat`; ⛔ no és l'orientació de les
    ratlles a la imatge, que és a 90°: a la V26 el primer tall va caure a 90° del pic i no va
    treure res, 240 → 254). Falca ±tol a l'espectre, només entre per_min i per_max.
    `pes_espacial` (0-1) diu on s'aplica (1 = notch sencer, 0 = original): rampa radial DECLARADA."""
    H, W = det.shape; x = (det - 0.5).astype(np.float32)
    F = np.fft.fft2(x); fy = np.fft.fftfreq(H)[:, None]; fx = np.fft.fftfreq(W)[None, :]
    k = np.hypot(fx, fy); ang = np.degrees(np.arctan2(fy, fx))
    a0 = orientacio_espectral_deg % 180.0
    d = np.abs(((ang - a0 + 90.0) % 180.0) - 90.0)             # distància angular mòdul 180
    falca = np.exp(-(d / tol_deg) ** 2) * ((k >= 1.0 / per_max) & (k <= 1.0 / per_min))
    Fn = F * (1.0 - falca)
    xn = np.real(np.fft.ifft2(Fn)).astype(np.float32)
    if pes_espacial is not None:
        xn = x * (1 - pes_espacial) + xn * pes_espacial
    return (xn + 0.5).astype(np.float32)


# ------------------------------------------------------------------ V · vores rectes
def dist_linia_centre(l, centre):
    """Distància (px) del centre (cx, cy) a la recta que passa pel segment l."""
    cx, cy = centre; ux, uy = l["x2"] - l["x1"], l["y2"] - l["y1"]; L = max(np.hypot(ux, uy), 1e-6)
    return float(abs((cx - l["x1"]) * uy - (cy - l["y1"]) * ux) / L)


def arestes_rectes(det, m, llindar_rel=6.0, long_min=400, centre=None, dist_min=0.0):
    """Línies rectes llargues en una capa de detall: gradient fort i coherent al llarg de
    ≥ long_min px (seams de cobertura, extensions, rectangles). Torna segments (x1,y1,x2,y2,long).
    ⛔ Amb `centre` i `dist_min`: es descarten les rectes que passen a < dist_min px del Sol —
    un streamer recte ÉS una recta radial (a la V26 ronda 4 l'atenuador va caçar un streamer de
    900 px a 57 px del centre); una costura de fotograma és a ~4,7 R☉ del centre."""
    x = ((det - 0.5) * 255).astype(np.float32); x = np.where(m, x, 0)
    g = cv2.GaussianBlur(x, (0, 0), 3.0); e = cv2.Canny(np.clip(g * 8 + 128, 0, 255).astype(np.uint8), 40, 120)
    lin = cv2.HoughLinesP(e, 1, np.pi / 720, threshold=int(long_min * 0.6), minLineLength=long_min, maxLineGap=40)
    out = []
    if lin is not None:
        for (x1, y1, x2, y2) in np.asarray(lin).reshape(-1, 4):
            l = dict(x1=int(x1), y1=int(y1), x2=int(x2), y2=int(y2), long=float(np.hypot(x2 - x1, y2 - y1)))
            if centre is not None:
                l["dist_centre"] = round(dist_linia_centre(l, centre), 1)
                if l["dist_centre"] < dist_min: continue
            out.append(l)
    out.sort(key=lambda d: -d["long"]); return out


def agrupa_arestes(linies, tol_ang=3.0, tol_dist=60.0):
    """Agrupa segments de Hough col·lineals (mateix angle ±tol_ang i mateixa distància a l'origen
    ±tol_dist) en UNA costura: (x1,y1,x2,y2) = l'extensió màxima del grup, amb `n` i `long`."""
    grups = []
    for l in linies:
        ang = np.degrees(np.arctan2(l["y2"] - l["y1"], l["x2"] - l["x1"])) % 180.0
        nx, ny = -np.sin(np.radians(ang)), np.cos(np.radians(ang)); dist = nx * l["x1"] + ny * l["y1"]
        for g in grups:
            da = abs(((ang - g["ang"] + 90.0) % 180.0) - 90.0)
            if da <= tol_ang and abs(dist - g["dist"]) <= tol_dist:
                g["seg"].append(l); break
        else:
            grups.append(dict(ang=ang, dist=dist, seg=[l]))
    out = []
    for g in grups:
        ux, uy = np.cos(np.radians(g["ang"])), np.sin(np.radians(g["ang"]))
        pts = [(l["x1"], l["y1"]) for l in g["seg"]] + [(l["x2"], l["y2"]) for l in g["seg"]]
        t = [ux * x + uy * y for x, y in pts]; i0, i1 = int(np.argmin(t)), int(np.argmax(t))
        out.append(dict(x1=int(pts[i0][0]), y1=int(pts[i0][1]), x2=int(pts[i1][0]), y2=int(pts[i1][1]), ang=round(float(g["ang"]), 1), n=len(g["seg"]), long=float(max(t) - min(t))))
    out.sort(key=lambda d: -d["long"]); return out


def pes_costura(H, W, c, sigma=100.0, marge=400.0):
    """Pes 0-1 d'atenuació al voltant d'una costura recta: gaussiana de la distància a la línia
    (σ px), limitada al tram del segment allargat `marge` px per cada extrem (amb rampa suau)."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    ux, uy = c["x2"] - c["x1"], c["y2"] - c["y1"]; L = max(np.hypot(ux, uy), 1e-6); ux, uy = ux / L, uy / L
    dx, dy = xx - c["x1"], yy - c["y1"]; t = dx * ux + dy * uy; d = np.abs(dx * uy - dy * ux)
    along = smoothstep(t, -marge, -marge + 200) * (1 - smoothstep(t, L + marge - 200, L + marge))
    return (np.exp(-0.5 * (d / sigma) ** 2) * along).astype(np.float32)


# ------------------------------------------------------------------ A · alineació (prova azimutal)
def prova_azimutal(img, ref, cx, cy, RS, r0=1.15, r1=2.0, nr=80, nt=1440, tol_deg=0.5):
    """⛔ L'ÚNICA prova d'alineació entre llenços que no s'enganya amb l'estructura radial (V25/V26
    anaven girades 138,5° amb 48 finestres de fase a «1,5 px» i un escaquer «continu»). Perfil polar
    en ln (r0-r1 R☉ × azimut) amb la mitjana per anell restada, correlació circular en azimut entre
    `img` i `ref` (mateix centre (cx, cy) al llenç): torna (angle residual °, correlació a 0°, PASSA,
    correlació amb el CONTROL NUL = ref girada 180°)."""
    rr = np.linspace(r0, r1, nr) * RS; th = np.linspace(0, 2 * np.pi, nt, endpoint=False)
    xs = (cx + rr[:, None] * np.cos(th)[None, :]).astype(np.float32); ys = (cy + rr[:, None] * np.sin(th)[None, :]).astype(np.float32)
    def pol(a):
        q = cv2.remap(a.astype(np.float32), xs, ys, cv2.INTER_LINEAR); q = np.log(np.maximum(q, 1e-4)); return q - q.mean(axis=1, keepdims=True)
    pa, pb = pol(img), pol(ref)
    def corr(a, b):
        Fa = np.fft.fft(a, axis=1); Fb = np.fft.fft(b, axis=1); c = np.real(np.fft.ifft(Fa * np.conj(Fb), axis=1)).mean(axis=0); return c / max(c.max(), 1e-12)
    c = corr(pa, pb); k = int(np.argmax(c)); ang = k * 360.0 / nt; ang = ang if ang <= 180 else ang - 360
    c_nul = corr(pa, np.roll(pb, nt // 2, axis=1))
    return dict(angle_residual_deg=round(float(ang), 2), corr_a_0=round(float(c[0]), 3), PASSA=bool(abs(ang) <= tol_deg and c[0] > 0.8),
                control_nul_corr_a_0=round(float(c_nul[0]), 3))


# ------------------------------------------------------------------ M · monotonia · L · limbe · H · H1
def perfil_radial(L, rad, RS, r0=1.2, r1=12.0, pas=0.1, n_min=500):
    prof = []
    for a in np.arange(r0, r1, pas):
        s = (rad > a * RS) & (rad < (a + pas) * RS)
        if s.sum() > n_min: prof.append((round(float(a), 2), float(np.median(L[s]))))
    return prof


def monotonia(prof, tol=0.005):
    pujades = [(a[0], round(b[1] - a[1], 4)) for a, b in zip(prof, prof[1:]) if b[1] - a[1] > tol]
    return dict(passa=len(pujades) == 0, pujades=pujades)


def limbe(L, rad, RS, r0=0.98, r1=1.16):
    prof = [(round(float(a), 3), float(np.median(L[(rad > a * RS) & (rad < (a + 0.01) * RS)]))) for a in np.arange(r0, r1, 0.01)]
    v = [p[1] for p in prof]; i_max = int(np.argmax(v))
    dip = max(0.0, max(v[:i_max + 1]) - min(v[i_max:])) if i_max < len(v) - 1 else 0.0
    # franja fosca = una caiguda seguida d'una pujada entre 1,00 i 1,12
    caig = [(prof[i][0], round(v[i + 1] - v[i], 3)) for i in range(len(v) - 1) if v[i + 1] < v[i] - 0.03 and prof[i][0] < 1.12 and any(v[j] > v[i + 1] + 0.03 for j in range(i + 2, len(v)))]
    return dict(perfil=prof, franja_fosca=caig, passa=len(caig) == 0)


def h1_nivell(det, rad, m, RS, nb=200):
    """Porta H1 de la cadena: desviació màxima de la mediana per anell respecte de 0,5."""
    rmax = float(rad[m].max()); lo = np.log10(20.0 / rmax)
    idx = np.clip(((np.log10(np.maximum(rad, 1.0) / rmax) - lo) / (0.0 - lo) * nb).astype(np.int32), 0, nb - 1)
    pit = 0.0; rr = float("nan")
    for k in range(nb):
        s = m & (idx == k)
        if s.sum() < 400: continue
        v = det[s]; me = float(np.median(v)); di = 1.4826 * float(np.median(np.abs(v - me)))
        if di <= 0.02: continue
        if abs(me - 0.5) > pit: pit, rr = abs(me - 0.5), float(10 ** (lo + (k + 0.5) / nb * (0 - lo)) * rmax / RS)
    return dict(max_abs=pit, r_pitjor=rr, passa=pit <= 0.05)


# ------------------------------------------------------------------ P · marques de Pere
def marques_tif(path_tif, cx, cy, RS, r_min=1.03, s_min=0.55, v_min=0.35, area_min=300):
    """Llegeix un TIF pintat per Pere (traços saturats) i torna les marques com a components."""
    import tifffile
    A = tifffile.imread(path_tif)[..., :3]; A8 = (A >> 8).astype(np.uint8) if A.dtype == np.uint16 else A.astype(np.uint8)
    H, W = A8.shape[:2]; hsv = cv2.cvtColor(A8, cv2.COLOR_RGB2HSV)
    S = hsv[..., 1] / 255.0; V = hsv[..., 2] / 255.0; rad, th = polars(H, W, cx, cy)
    marca = (S > s_min) & (V > v_min) & (rad > r_min * RS)
    from scipy.ndimage import binary_dilation
    lab, n = label(binary_dilation(marca, iterations=3)); rows = []
    for i, sl in enumerate(find_objects(lab), 1):
        c = lab[sl] == i; area = int(c.sum())
        if area < area_min: continue
        ys, xs = np.nonzero(c); yc = sl[0].start + ys.mean(); xc = sl[1].start + xs.mean()
        hue = int(np.median(hsv[..., 0][sl][c])); col = {0: "vermell", 30: "groc", 60: "verd", 90: "cian", 120: "blau", 150: "magenta"}.get(int(round(hue / 30) * 30) % 180, "?")
        rows.append(dict(id=len(rows) + 1, x=int(xc), y=int(yc), w=sl[1].stop - sl[1].start, h=sl[0].stop - sl[0].start, area=area,
                         r_Rsol=round(float(np.hypot(xc - cx, yc - cy) / RS), 2), az=round(float(np.degrees(np.arctan2(yc - cy, xc - cx))), 0), color=col))
    rows.sort(key=lambda d: -d["area"]); return rows, marca, A8
