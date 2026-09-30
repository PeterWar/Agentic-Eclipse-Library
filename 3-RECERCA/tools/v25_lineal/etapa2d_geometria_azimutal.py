#!/usr/bin/env python3
"""V27 · geometria llenç comú → V23 refeta amb una prova que NO s'enganya amb l'estructura radial.

⛔ Lliçó (05-09-2026): la V25/V26 va anar amb una rotació de −91,97° «validada» per correlació de
fase en finestres i per un escaquer; Pere va dir dues vegades que les capes anaven girades i tenia
raó: la correlació AZIMUTAL (perfil polar en ln, mitjana per anell fora) entre la meva base i les
seves capes 10/09 dona un pic a −138,5°, no a 0°. Les finestres i l'escaquer es van enganxar a
l'estructura RADIAL (els raigs són radials a qualsevol angle) i al gradient. Regla: tota geometria
entre llenços porta la prova azimutal (pic a 0 ± 0,5°) a més de les finestres.

Mètode: (1) angle gros = pic de la correlació circular en azimut entre la meva base (llenç comú,
Sol al centre) i la capa 10+09 de Pere (V23, centre del disc C2); (2) M inicial = rotació al
voltant del centre del llenç + translació centre→disc; (3) afinat de translació i angle per
correlació de fase en finestres (band-pass 4-40 px) contra les capes 10, 09 i 13 dins de la seva
dada, dues iteracions; (4) validació: prova azimutal a 0 ± 0,5° i residu de finestres.
"""
import os, sys, json, numpy as np, cv2
from psd_tools import PSDImage
from scipy.ndimage import gaussian_filter
AQUI = os.path.dirname(os.path.abspath(__file__)); CAU = os.path.join(AQUI, "cau_v25")
sys.path.insert(0, "/Users/USUARI/Downloads/Eclipse 2026/research/tools/encaix_sony")
V24 = "/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/CapesTotalsV24.psb"
CX, CY, RM = 5361.877, 3774.741, 453.45          # disc C2 de Pere (Lluna); R☉ = 440,603 px a la mateixa escala
RS = 440.603
BASE = os.path.join(CAU, "v26_final", "base_B_rgb16.npy") if os.path.exists(os.path.join(CAU, "v26_final", "base_B_rgb16.npy")) else os.path.join(CAU, "base_B_rgb16.npy")


def full_layer(c, W, H):
    x0, y0, x1, y1 = c.bbox; a = c.numpy("color")[..., :3]; F = np.zeros((H, W, 3), np.float32)
    X0, Y0, X1, Y1 = max(x0, 0), max(y0, 0), min(x1, W), min(y1, H); F[Y0:Y1, X0:X1] = a[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
    m = np.zeros((H, W), bool); m[Y0:Y1, X0:X1] = True
    return F, m


def lum(a): return (a[..., 0] + 2 * a[..., 1] + a[..., 2]) / 4.0


def polar(img, cx, cy, r_px0, r_px1, nr=80, nt=1440):
    rr = np.linspace(r_px0, r_px1, nr); th = np.linspace(0, 2 * np.pi, nt, endpoint=False)
    xs = cx + rr[:, None] * np.cos(th)[None, :]; ys = cy + rr[:, None] * np.sin(th)[None, :]
    return cv2.remap(img.astype(np.float32), xs.astype(np.float32), ys.astype(np.float32), cv2.INTER_LINEAR)


def azim(img, cx, cy, r0, r1):
    p = polar(img, cx, cy, r0 * RS, r1 * RS); p = np.log(np.maximum(p, 1e-4)); return p - p.mean(axis=1, keepdims=True)


def lag_azimutal(a, b):
    """angle (°) que cal girar `a` perquè coincideixi amb `b` (convenció θ = atan2(y, x), y avall)."""
    Fa = np.fft.fft(a - a.mean(axis=1, keepdims=True), axis=1); Fb = np.fft.fft(b - b.mean(axis=1, keepdims=True), axis=1)
    c = np.real(np.fft.ifft(Fa * np.conj(Fb), axis=1)).mean(axis=0); c = c / c.max(); nt = a.shape[1]
    k = int(np.argmax(c)); ang = k * 360.0 / nt; ang = ang if ang <= 180 else ang - 360
    # afinat parabòlic
    y0, y1, y2 = c[(k - 1) % nt], c[k], c[(k + 1) % nt]; d = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2 + 1e-12)
    return -(ang + d * 360.0 / nt), c


def fase(a, b):
    """desplaçament (dy, dx) de b respecte d'a per correlació de fase amb subpíxel (finestra Hann)."""
    n = a.shape[0]; h = np.hanning(n); w = h[:, None] * h[None, :]
    A = np.fft.fft2((a - a.mean()) * w); B = np.fft.fft2((b - b.mean()) * w)
    R = A * np.conj(B); R /= np.abs(R) + 1e-9; c = np.real(np.fft.ifft2(R)); k = np.unravel_index(np.argmax(c), c.shape)
    pk = float(c.max()); out = []
    for ax, kk in enumerate(k):
        y0, y1, y2 = c.take((kk - 1) % n, axis=ax).max(), c.take(kk, axis=ax).max(), c.take((kk + 1) % n, axis=ax).max()
        d = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2 + 1e-12); v = kk + d; out.append(v - n if v > n / 2 else v)
    return out[0], out[1], pk


def bandpass(a, s_lo=4.0, s_hi=40.0): return gaussian_filter(a, s_lo) - gaussian_filter(a, s_hi)


def sense_perfil(Limg, m, cx, cy, nb=600):
    """⛔ Resta la mediana per anell (ln r) ABANS de correlar finestres: el gradient radial fa que la
    correlació de fase doni «0,1 px» encara que la imatge vagi girada 93° (mesurat el 05-09-2026)."""
    H, W = Limg.shape; yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); rad = np.hypot(yy - cy, xx - cx)
    lnr = np.log(np.maximum(rad, 1.0)); a = m & np.isfinite(Limg); lo, hi = float(lnr[a].min()), float(lnr[a].max())
    idx = np.clip(((lnr - lo) / (hi - lo) * nb).astype(np.int32), 0, nb - 1); cen = lo + (np.arange(nb) + 0.5) / nb * (hi - lo)
    prof = np.full(nb, np.nan)
    for k in range(nb):
        sel = a & (idx == k)
        if sel.sum() > 200: prof[k] = np.median(Limg[sel])
    ok = np.isfinite(prof); prof = np.interp(cen, cen[ok], prof[ok])
    return (Limg - np.interp(lnr, cen, prof)).astype(np.float32)


def retard_radial(Bw, ref, m, cx, cy, r0, r1, nsec=36, nr=400, nt=1440, esc_max=6):
    """Per a cada sector d'azimut, el retard RADIAL (px) entre la meva base i la referència en
    polar (r lineal): un desplaçament del centre (dx, dy) fa Δr(θ) = dx·cosθ + dy·sinθ; una
    escala errònia fa Δr ∝ r. Torna (dx, dy, escala, residu_px, n_sectors)."""
    rr = np.linspace(r0 * RS, r1 * RS, nr); th = np.linspace(0, 2 * np.pi, nt, endpoint=False)
    xs = cx + rr[:, None] * np.cos(th)[None, :]; ys = cy + rr[:, None] * np.sin(th)[None, :]
    pa = cv2.remap(Bw, xs.astype(np.float32), ys.astype(np.float32), cv2.INTER_LINEAR); pb = cv2.remap(ref, xs.astype(np.float32), ys.astype(np.float32), cv2.INTER_LINEAR)
    pm = cv2.remap(m.astype(np.float32), xs.astype(np.float32), ys.astype(np.float32), cv2.INTER_NEAREST) > 0.5
    dr = rr[1] - rr[0]; out = []
    for k in range(nsec):
        c0, c1 = k * nt // nsec, (k + 1) * nt // nsec
        if pm[:, c0:c1].mean() < 0.98: continue
        a = pa[:, c0:c1].mean(axis=1); b = pb[:, c0:c1].mean(axis=1)
        a = a - gaussian_filter(a, 40); b = b - gaussian_filter(b, 40)         # fora el perfil radial llis
        best = None
        for sh in range(-int(esc_max / dr * 4), int(esc_max / dr * 4) + 1):
            aa = a[max(sh, 0):nr + min(sh, 0)]; bb = b[max(-sh, 0):nr + min(-sh, 0)]
            c = float((aa * bb).sum() / np.sqrt((aa * aa).sum() * (bb * bb).sum() + 1e-12))
            if best is None or c > best[1]: best = (sh, c)
        thm = (th[c0] + th[c1 - 1]) / 2; out.append((thm, best[0] * dr, best[1], (rr[0] + rr[-1]) / 2))
    if len(out) < 6: return None
    T = np.array(out); A = np.column_stack([np.cos(T[:, 0]), np.sin(T[:, 0]), np.ones(len(T))])
    sol, *_ = np.linalg.lstsq(A, T[:, 1], rcond=None); res = T[:, 1] - A @ sol
    return dict(dx=float(sol[0]), dy=float(sol[1]), c=float(sol[2]), residu_px=float(np.sqrt((res ** 2).mean())), n=len(T), corr_mediana=float(np.median(T[:, 2])), r_mig=float(T[0, 3]))


def main():
    psd = PSDImage.open(V24); L = list(psd); W, H = psd.width, psd.height
    caps = {}
    for k, r0, r1 in ((2, 1.12, 1.55), (3, 1.25, 2.1), (12, 2.2, 5.5)):
        F, m = full_layer(L[k], W, H); Lk = np.log(np.maximum(lum(F), 1e-4)); caps[k] = dict(L=Lk, Ld=sense_perfil(Lk, m, CX, CY), m=m, r0=r0, r1=r1, nom=L[k].name[:28]); del F
    base = np.load(BASE).astype(np.float32) / 65535.0; Hl, Wl = base.shape[:2]; cxl, cyl = Wl / 2.0 - 0.5, Hl / 2.0 - 0.5
    Lb = np.log(np.maximum(lum(base), 1e-4)); del base
    # (1) angle gros: correlació azimutal, la meva base (llenç, Sol al centre) vs capa 10+09 (V23, centre del disc)
    ref = np.where(caps[3]["m"], caps[3]["L"], caps[2]["L"])
    pb = azim(np.exp(Lb), cxl, cyl, 1.15, 2.0); pr = azim(np.exp(ref), CX, CY, 1.15, 2.0)
    ang0, c = lag_azimutal(pb, pr)
    print(f"angle gros (azimutal, 1,15-2,0 R☉): {ang0:+.2f}° · pic {c.max():.2f} · a 0°: {c[0]:+.2f}")
    # (2) M inicial: gira al voltant del centre del llenç i porta'l al centre del disc (el Sol és a ~1′ del disc: la translació ho afina)
    def M_de(ang, tx, ty, esc=1.0):
        M = cv2.getRotationMatrix2D((cxl, cyl), -ang, esc)         # signe comprovat amb l'escombrada: lag +46,58 → OpenCV −46,58 dona residu 0
        M[0, 2] += tx; M[1, 2] += ty; return M
    ang, tx, ty, esc = ang0, CX - cxl, CY - cyl, 1.0
    # --- afinat polar: retard radial per sector → (dx, dy); dues bandes de radi → escala; iterat ---
    ref09 = np.where(caps[3]["m"], caps[3]["L"], caps[2]["L"]); m09 = caps[3]["m"] | caps[2]["m"]
    for it in range(4):
        M = M_de(ang, tx, ty, esc); Bw = cv2.warpAffine(Lb, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=np.log(1e-4))
        r_in = retard_radial(Bw, ref09, m09, CX, CY, 1.15, 1.55); r_out = retard_radial(Bw, ref09, m09, CX, CY, 1.55, 2.05)
        if r_in is None or r_out is None: print("  afinat polar: sectors insuficients", r_in, r_out); break
        dx = (r_in["dx"] + r_out["dx"]) / 2; dy = (r_in["dy"] + r_out["dy"]) / 2
        d_esc = 1.0 + (r_out["c"] - r_in["c"]) / (r_out["r_mig"] - r_in["r_mig"])       # Δr ∝ r → escala
        print(f"  polar it {it}: centre (dx,dy)=({dx:+.2f},{dy:+.2f}) px · c_in {r_in['c']:+.2f} c_out {r_out['c']:+.2f} → escala ×{d_esc:.5f} · residu {r_in['residu_px']:.2f}/{r_out['residu_px']:.2f} px · corr {r_in['corr_mediana']:.2f}/{r_out['corr_mediana']:.2f} · sectors {r_in['n']}/{r_out['n']}")
        tx -= dx; ty -= dy                                          # escala fixa 1,0 (mateixa escala de píxel; el retard radial es deixa enganyar pels anells comuns)
        a_ = azim(np.exp(Bw), CX, CY, 1.15, 2.0); b_ = azim(np.exp(ref09), CX, CY, 1.15, 2.0); da, _ = lag_azimutal(a_, b_); ang += da
        if abs(dx) < 0.3 and abs(dy) < 0.3 and abs(d_esc - 1) < 5e-4 and abs(da) < 0.05: break
    for it in range(1):
        M = M_de(ang, tx, ty, esc); Bw = cv2.warpAffine(Lb, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=np.log(1e-4))
        Bd = sense_perfil(Bw, Bw > np.log(2e-4), CX, CY)
        Bctrl = cv2.warpAffine(Bd, cv2.getRotationMatrix2D((CX, CY), 180, 1.0), (W, H))     # control nul: girada 180°
        # finestres: 512 px, dins de la dada de cada capa, band-pass 4-40, sobre les imatges SENSE perfil radial
        pts = []; ctrl = []
        for k, cp in caps.items():
            for az in range(0, 360, 20):
                for r_ in np.linspace(cp["r0"] + 0.15, cp["r1"] - 0.15, 3):
                    x = int(CX + r_ * RS * np.cos(np.radians(az))); y = int(CY + r_ * RS * np.sin(np.radians(az))); n = 512
                    if x - n // 2 < 0 or y - n // 2 < 0 or x + n // 2 > W or y + n // 2 > H: continue
                    if not cp["m"][y - n // 2:y + n // 2, x - n // 2:x + n // 2].all(): continue
                    a = bandpass(cp["Ld"][y - n // 2:y + n // 2, x - n // 2:x + n // 2]); b = bandpass(Bd[y - n // 2:y + n // 2, x - n // 2:x + n // 2])
                    dy, dx, pk = fase(a, b); dyc, dxc, pkc = fase(a, bandpass(Bctrl[y - n // 2:y + n // 2, x - n // 2:x + n // 2]))
                    ctrl.append((pkc, np.hypot(dxc, dyc)))
                    if pk > 0.05 and np.hypot(dx, dy) < 60: pts.append((x, y, dx, dy, pk, k))
        P = np.array([(p[0], p[1]) for p in pts], np.float64); D = np.array([(p[2], p[3]) for p in pts], np.float64)
        # ajust de similitud: la base desplaçada (x+dx, y+dy) ha d'anar a (x, y) → afegim la correcció a M
        src = P + D; dst = P
        A = np.column_stack([src[:, 0], -src[:, 1], np.ones(len(src)), np.zeros(len(src))]); A2 = np.column_stack([src[:, 1], src[:, 0], np.zeros(len(src)), np.ones(len(src))])
        AA = np.vstack([A, A2]); bb = np.concatenate([dst[:, 0], dst[:, 1]]); sol, *_ = np.linalg.lstsq(AA, bb, rcond=None)
        a_, b_, c_, d_ = sol; corr = np.array([[a_, -b_, c_], [b_, a_, d_]])
        M_new = np.vstack([M, [0, 0, 1]])[:2]                       # ⛔ les finestres NO corregeixen: només s'informen (pics 0,05-0,06)
        d_ang = np.degrees(np.arctan2(b_, a_)); d_esc = np.hypot(a_, b_)
        res = np.hypot(D[:, 0], D[:, 1]); C = np.array(ctrl); pk_ok = np.array([p[4] for p in pts])
        print(f"  it {it}: {len(pts)} finestres · desplaçament mediana {np.median(res):.2f} px p90 {np.percentile(res, 90):.2f} · pic mediana {np.median(pk_ok):.2f} · CONTROL NUL (ref 180°): pic mediana {np.median(C[:, 0]):.2f}, p90 {np.percentile(C[:, 0], 90):.2f} · correcció angle {d_ang:+.3f}° escala {d_esc:.5f}")
        # extreu (ang, esc, tx, ty) de M_new respecte del centre del llenç
        esc = float(np.hypot(M_new[0, 0], M_new[1, 0])); ang = float(np.degrees(np.arctan2(M_new[1, 0], M_new[0, 0])))   # coherent amb M_de(−ang)
        c0 = M_new @ np.array([cxl, cyl, 1.0]); tx, ty = float(c0[0] - cxl), float(c0[1] - cyl)
    M = M_de(ang, tx, ty, esc); Bw = cv2.warpAffine(Lb, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=np.log(1e-4))
    # (4) validació: azimutal per capa, retard radial final i control nul (referència girada 180°)
    val = {}
    rf = retard_radial(Bw, ref09, m09, CX, CY, 1.15, 2.05); refc = cv2.warpAffine(ref09, cv2.getRotationMatrix2D((CX, CY), 180, 1.0), (W, H))
    rc = retard_radial(Bw, refc, cv2.warpAffine(m09.astype(np.uint8), cv2.getRotationMatrix2D((CX, CY), 180, 1.0), (W, H)) > 0, CX, CY, 1.15, 2.05)
    print(f"  retard radial final: (dx,dy)=({rf['dx']:+.2f},{rf['dy']:+.2f}) residu {rf['residu_px']:.2f} px corr {rf['corr_mediana']:.2f} · CONTROL NUL: corr {rc['corr_mediana'] if rc else None} residu {rc['residu_px'] if rc else None}")
    val["retard_radial_final"] = rf; val["control_nul_retard"] = rc
    for k, cp in caps.items():
        a = azim(np.exp(Bw), CX, CY, cp["r0"], cp["r1"]); b = azim(np.exp(cp["L"]), CX, CY, cp["r0"], cp["r1"]); a_ang, cc = lag_azimutal(a, b)
        val[cp["nom"]] = dict(angle_residual_deg=round(float(a_ang), 3), pic=round(float(cc.max()), 3), a_0=round(float(cc[0]), 3))
        print(f"  validació azimutal vs {cp['nom']}: residu {a_ang:+.2f}° (a 0°: {cc[0]:.2f})")
    ang_total = float(np.degrees(np.arctan2(M[1, 0], M[0, 0]))); esc_total = float(np.hypot(M[0, 0], M[1, 0]))
    out = dict(M_llenc_a_v23=M.tolist(), rotacio_total_deg=ang_total, escala_total=esc_total, centre_llenc=[cxl, cyl], centre_disc_v23=[CX, CY],
               sol_v23=[float((M @ np.array([cxl, cyl, 1.0]))[0]), float((M @ np.array([cxl, cyl, 1.0]))[1])], angle_gros_azimutal=float(ang0),
               finestres=len(pts), mediana_offset_px=float(np.median(res)), p90_offset_px=float(np.percentile(res, 90)), pic_mediana=float(np.median(pk_ok)),
               control_nul_pic_mediana=float(np.median(C[:, 0])), control_nul_pic_p90=float(np.percentile(C[:, 0], 90)), validacio_azimutal=val,
               nota="rotació en la convenció d'OpenCV (positiu = antihorari a pantalla); la V25/V26 duien −91,969° i estaven girades 138,5°")
    json.dump(out, open(os.path.join(CAU, "geometria_v27.json"), "w"), indent=1)
    print("geometria V27:", {k: v for k, v in out.items() if k in ("rotacio_total_deg", "escala_total", "sol_v23", "mediana_offset_px", "p90_offset_px")})


if __name__ == "__main__":
    main()
