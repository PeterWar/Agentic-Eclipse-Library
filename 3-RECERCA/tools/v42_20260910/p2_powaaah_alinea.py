"""P2 (V42) · Alineació de `~/Desktop/POWAAAH3.tif` (HDR de Pere del 16-08, 15904×10608 RGB16, Photoshop) al llenç del projecte, per fer-ne capa (l'earthshine).
Mesures: (1) disc lunar al POWAAAH3: cercle ajustat a la vora del disc (gradient radial màxim en 360 raigs des d'un centre inicial); l'escala surt de R_disc / R_lluna del
projecte (455,5 px: mateix objecte, mateix dia); (2) rotació: correlació circular en AZIMUT dels perfils polars de ln(G) de la corona (1,15–1,9 R☉) entre el POWAAAH3
(centrat al SOL: el Sol és al centre del disc lunar més el desplaçament Lluna–Sol del seu instant, desconegut → s'ajusta la rotació amb el centre del disc i després
es refina el centre del Sol amb la correlació de fase de la corona) i la fusió V38; (3) control nul: la correlació azimutal amb la imatge girada 180°.
Sortida: cau/powaaah3_rgb_u16.npy (llenç sencer, mateixa escala i orientació, disc lunar del POWAAAH3 sobre el forat de la V38 (+14,8, +0,9) px del Sol),
cau/powaaah3_mascara_disc_u16.npy (disc + ploma), rebut REB42/P2_powaaah.json i vistes."""
from comu42 import *
import tifffile
from scipy.ndimage import map_coordinates, gaussian_filter
SRC = Path('/Users/USUARI/Desktop/POWAAAH3.tif'); RL_V38 = 455.5; MOON_V38 = (CX + 14.8, CY + 0.9)
GEO = ROOT / 'research/tools/v25_lineal/cau_v25/geometria_v27.json'


def polar_prof(img, cx, cy, r0, r1, nr=64, nth=1440):
    th = np.linspace(0, 2 * np.pi, nth, endpoint=False); rs = np.linspace(r0, r1, nr)
    R, T = np.meshgrid(rs, th, indexing='ij'); xs = cx + R * np.cos(T); ys = cy + R * np.sin(T)
    v = map_coordinates(img, [ys, xs], order=1, mode='nearest'); v = v - v.mean(axis=1, keepdims=True); return v


def corr_azimutal(a, b):
    """correlació circular en azimut (files = radis) → angle (°) del pic i valor"""
    Fa = np.fft.rfft(a, axis=1); Fb = np.fft.rfft(b, axis=1); cc = np.fft.irfft(Fa * np.conj(Fb), n=a.shape[1], axis=1).sum(axis=0)
    cc /= (np.sqrt((a * a).sum()) * np.sqrt((b * b).sum()) + 1e-12); k = int(np.argmax(cc)); return (k * 360.0 / a.shape[1] + 180) % 360 - 180, float(cc[k]), cc


def fit_disc(g, cx0, cy0, r0, dr=120, nth=720):
    """vora del disc: per a cada raig, el radi del gradient radial màxim (de fosc a clar) dins de r0±dr; ajust de cercle per mínims quadrats (3 iteracions)"""
    cx, cy = cx0, cy0
    for it in range(3):
        th = np.linspace(0, 2 * np.pi, nth, endpoint=False); rs = np.arange(r0 - dr, r0 + dr, 0.5)
        R, T = np.meshgrid(rs, th, indexing='ij'); prof = map_coordinates(g, [cy + R * np.sin(T), cx + R * np.cos(T)], order=1, mode='nearest')
        grad = np.gradient(gaussian_filter(prof, (2, 0)), axis=0); i = np.argmax(grad, axis=0); redge = rs[i]; ok = grad[i, np.arange(nth)] > 0.3 * np.median(grad[i, np.arange(nth)])
        x = cx + redge * np.cos(th); y = cy + redge * np.sin(th); A = np.c_[2 * x, 2 * y, np.ones_like(x)]; b = x * x + y * y; sol = np.linalg.lstsq(A[ok], b[ok], rcond=None)[0]
        cx, cy = sol[0], sol[1]; r0 = float(np.sqrt(sol[2] + cx * cx + cy * cy)); res = np.hypot(x - cx, y - cy) - r0
    return float(cx), float(cy), r0, float(np.std(res[ok])), int(ok.sum())


def main():
    with tifffile.TiffFile(SRC) as t: img = t.pages[0].asarray()
    Hp, Wp = img.shape[:2]; g = img[..., 1].astype(np.float32); log(f'POWAAAH3 {Wp}×{Hp}')
    # 1) disc: centre inicial = centroide de la regió fosca dins del cercle brillant (la corona interior satura a 65535)
    g4 = g[::4, ::4]; bright = g4 > 60000; yy, xx = np.nonzero(bright); cxb, cyb = xx.mean() * 4, yy.mean() * 4   # centre del blanc saturat ≈ Sol
    win = 800; sub = g[int(cyb - win):int(cyb + win), int(cxb - win):int(cxb + win)]; dark = sub < np.percentile(sub, 20); yy, xx = np.nonzero(dark); cx0, cy0 = xx.mean() + cxb - win, yy.mean() + cyb - win
    area = dark.sum(); r_est = float(np.sqrt(area / np.pi)); log(f'centre del blanc saturat ({cxb:.0f}, {cyb:.0f}); disc fosc inicial ({cx0:.0f}, {cy0:.0f}) r≈{r_est:.0f}')
    cxm, cym, Rm, res, nok = fit_disc(g, cx0, cy0, r_est); esc = Rm / RL_V38; log(f'disc lunar: centre ({cxm:.1f}, {cym:.1f}) R {Rm:.1f} px (residu {res:.2f} px, {nok} raigs) → escala pel disc {esc:.4f} (R_V38 {RL_V38})')
    args = dict(a.split('=', 1) for a in sys.argv[1:] if '=' in a); esc_final = float(args['esc']) if 'esc' in args else esc; ang_final = float(args['ang']) if 'ang' in args else None   # P2d: escala i rotació pels MARS contra la LROC (el disc fosc del POWAAAH3 és ~8 px més petit que el limbe: el glow hi vessa)
    if 'esc' in args: log(f'escala IMPOSADA (P2d, mars vs LROC): {esc_final:.4f} → el disc fosc del POWAAAH3 fa {Rm / esc_final:.1f} px al llenç (limbe real 453,5)')
    esc = esc_final
    # 2) rotació: perfils polars de la corona 1,15–1,9 R☉ (en píxels del POWAAAH3: R☉ ≈ RS·esc) al voltant del Sol ≈ centre del disc (l'error del centre del Sol és ≤ 30 px·esc)
    F = np.load(CAU38 / 'fusion_total_v38.npy', mmap_mode='r'); fg = np.log(np.maximum(np.nan_to_num(np.asarray(F[..., 1], np.float32)), 1))
    pg = np.log(np.maximum(g, 1)); RSp = RS * esc
    pa = polar_prof(pg, cxm, cym, 1.15 * RSp, 1.9 * RSp); pb = polar_prof(fg, CX, CY, 1.15 * RS, 1.9 * RS)
    ang, val, cc = corr_azimutal(pa, pb); ang180, val180, _ = corr_azimutal(np.roll(pa, pa.shape[1] // 2, axis=1), pb)
    if ang_final is not None: log(f'rotació IMPOSADA (P2d, mars vs LROC): {ang_final:+.2f}° (la de la corona interior saturada era {ang:+.2f}°)'); ang = ang_final
    log(f'rotació POWAAAH3→llenç per correlació azimutal de la corona: {ang:+.2f}° (pic {val:.3f}); nul (girat 180°): pic a {ang180:+.1f}° {val180:.3f}; segon pic {np.sort(cc)[-2] if False else float(np.partition(cc, -2)[-2]):.3f}')
    # 3) remostreig al llenç: p(llenç) = A·p(pow) amb A = escala 1/esc, rotació −ang, i el centre del disc → MOON_V38. Refinament del centre del Sol per correlació de fase de la corona després.
    th = np.deg2rad(ang); s = 1.0 / esc; c_, s_ = np.cos(-th), np.sin(-th)
    # coordenades del pow per a cada píxel del llenç: p_pow = disc + esc·R(+ang)·(p_llenç − MOON_V38)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); ux = xx - MOON_V38[0]; uy = yy - MOON_V38[1]; cth, sth = np.cos(th), np.sin(th)
    px = (cxm + esc * (cth * ux - sth * uy)).astype(np.float32); py = (cym + esc * (sth * ux + cth * uy)).astype(np.float32); del ux, uy
    out = np.zeros((H, W, 3), np.uint16)
    for c in range(3): out[..., c] = np.clip(cv2.remap(img[..., c].astype(np.float32), px, py, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0), 0, 65535).astype(np.uint16)
    inside = (px >= 0) & (px < Wp) & (py >= 0) & (py < Hp)
    # comprovació: correlació de fase de la corona (anell 1,2–2 R☉) entre la capa remostrejada i la fusió → desplaçament residual del SOL (= moviment de la Lluna entre instants + error)
    r, t_ = coords(); an = (r > 1.2 * RS) & (r < 2.0 * RS); y0, y1, x0, x1 = int(CY - 2.1 * RS), int(CY + 2.1 * RS), int(CX - 2.1 * RS), int(CX + 2.1 * RS)
    a = np.log(np.maximum(out[y0:y1, x0:x1, 1].astype(np.float32), 1)) * an[y0:y1, x0:x1]; b = fg[y0:y1, x0:x1] * an[y0:y1, x0:x1]
    (dx, dy), resp = cv2.phaseCorrelate((a - a.mean()).astype(np.float32), (b - b.mean()).astype(np.float32)); log(f'correlació de fase de la corona (capa→fusió): ({dx:+.1f}, {dy:+.1f}) px, resposta {resp:.3f} (amb el disc lunar clavat al forat V38: això és el moviment Lluna–Sol entre instants)')
    np.save(CAU42 / 'powaaah3_rgb_u16.npy', out)
    d = np.hypot(xx - MOON_V38[0], yy - MOON_V38[1]); mask = np.clip((RL_V38 + 6 - d) / 8.0, 0, 1); np.save(CAU42 / 'powaaah3_mascara_disc_u16.npy', np.round(mask * 65535).astype(np.uint16))
    savejson(REB42 / 'P2_powaaah.json', dict(font=str(SRC), mida=[Wp, Hp], disc=dict(cx=cxm, cy=cym, R=Rm, residu_px=res, raigs=nok), escala_pow_per_llenc=esc, escala_origen='P2d mars vs LROC' if 'esc' in args else 'disc/455,5', rotacio_deg=ang, rotacio_origen='P2d mars vs LROC' if ang_final is not None else 'corona interior (saturada: no fiable)', pic=val, nul_180=[ang180, val180], desplacament_sol_corona_px=[dx, dy], resposta=resp, colocacio='disc lunar → (CX+14,8, CY+0,9) = forat V38', cobertura_llenc=float(inside.mean())))
    from PIL import Image; Image.fromarray((np.clip(out[::4, ::4].astype(np.float32) / 65535, 0, 1) ** 0.5 * 255).astype(np.uint8)).save(VIS42 / 'P2_powaaah3_al_llenc_quart.png')
    y0, y1, x0, x1 = int(MOON_V38[1] - 560), int(MOON_V38[1] + 560), int(MOON_V38[0] - 560), int(MOON_V38[0] + 560)
    Image.fromarray((np.clip(out[y0:y1, x0:x1].astype(np.float32) / 65535, 0, 1) ** 0.5 * 255).astype(np.uint8)).save(VIS42 / 'P2_powaaah3_disc_1a1.png'); log('P2 fet')


if __name__ == '__main__':
    main()
