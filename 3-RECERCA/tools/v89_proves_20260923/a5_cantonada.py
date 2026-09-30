"""a5 · Cantonada del logo que es regenera (V86). Mateixa recepta que la capa 229 de la V79 (17-09, declarada al whitepaper):
el triangle sense imatge del racó inferior dret de l'enquadrament final s'omple continuant el cel del voltant:
  nivell  = polinomi 2D de 2n ordre per canal ajustat al cel a 20–700 px del triangle;
  gra     = residu del cel (pas alt σ 60 px, sense el triangle) reflectit a través de la hipotenusa (desplaçada 4 px enfora);
  ploma   = 24 px fora del triangle amb els píxels de sota (alfa decreixent).
No afegeix cap informació observacional: continua el fons per a la presentació.
La diferència amb la V79: aquí el triangle i el cel es llegeixen del COMPOST DE LES CAPES DE SOTA de la capa de la cantonada, de manera que
si Pere canvia qualsevol capa inferior, n'hi ha prou de tornar-la a calcular (Photoshop: regenera_cantonada.jsx; construcció: a7).

Ús des de Photoshop (el crida regenera_cantonada.jsx):
  python a5_cantonada.py --entrada compost_sota.tif --sortida capa.tif --x0 X --y0 Y --marc x0,y0,x1,y1
    entrada: TIFF RGB de 16 bits amb el compost de les capes de sota a la caixa (X,Y) del llenç; marc = enquadrament final al llenç.
    sortida: TIFF RGBA de 16 bits (alfa no associada) amb el mateix perfil ICC."""
import sys, json, argparse, numpy as np
from scipy.ndimage import binary_dilation, distance_transform_edt, label, map_coordinates, gaussian_filter
MARC_FINAL = (1325, 1142, 9348, 6263)   # enquadrament del V78-FINAL dins del llenç 10551×7506 (capa 234): x0, y0, x1, y1

def caixa_cantonada(marc=MARC_FINAL, marge=900, tri=(8256, 5220)):
    """Caixa de càlcul: des de 900 px abans del triangle fins a la cantonada inferior dreta de l'enquadrament."""
    x0, y0, x1, y1 = marc; return (max(x0, tri[0] - marge), max(y0, tri[1] - marge), x1, y1)

def calcula(sub, llindar=0.004):
    """sub: compost RGB 0–1 (float32) de la caixa; la cantonada inferior dreta de `sub` és la de l'enquadrament final.
    Retorna (rgb, alfa, rebut)."""
    Hs, Ws = sub.shape[:2]; L = sub.mean(-1); neg = L < llindar; lab, n = label(neg)
    k = lab[Hs - 1, Ws - 1]; assert k > 0, 'la cantonada inferior dreta no és buida: no hi ha res a omplir'
    T = lab == k; ys, xs = np.nonzero(T)
    P1 = (float(xs[ys == Hs - 1].min()), float(Hs - 1)); P2 = (float(Ws - 1), float(ys[xs == Ws - 1].min()))
    m_ = (P2[1] - P1[1]) / (P2[0] - P1[0]); b_ = P1[1] - m_ * P1[0]
    YY, XX = np.mgrid[0:Hs, 0:Ws]; T = T | (((m_ * XX - YY + b_) / np.sqrt(m_ * m_ + 1)) <= 4.0)
    d_out = distance_transform_edt(~T); ref = (~T) & (d_out > 20) & (d_out < 700); xn = (XX - Ws / 2) / Ws; yn = (YY - Hs / 2) / Hs
    B = lambda xv, yv: np.c_[np.ones(xv.size), xv, yv, xv ** 2, xv * yv, yv ** 2]
    suau = np.zeros_like(sub); res = np.zeros_like(sub)
    for c in range(3):
        coef = np.linalg.lstsq(B(xn[ref], yn[ref]), sub[..., c][ref], rcond=None)[0]; suau[..., c] = (B(xn.ravel(), yn.ravel()) @ coef).reshape(Hs, Ws); res[..., c] = sub[..., c] - suau[..., c]
    ty, tx = np.nonzero(T); nx, ny = m_, -1.0; nn = nx * nx + ny * ny; b_ref = b_ - 4.0 * np.sqrt(nn)
    dist = (nx * tx + ny * ty + b_ref) / nn; rx = tx - 2 * dist * nx; ry = ty - 2 * dist * ny
    rxl = np.clip(rx, 0, Ws - 1); ryl = np.clip(ry, 0, Hs - 1)
    res_hp = np.zeros_like(res); w = (~T).astype(np.float32)
    for c in range(3): res_hp[..., c] = res[..., c] - gaussian_filter(np.where(T, 0, res[..., c]), 60) / np.maximum(gaussian_filter(w, 60), 1e-6)
    grain = np.zeros((T.sum(), 3), np.float32)
    for c in range(3): grain[:, c] = map_coordinates(np.where(T, 0, res_hp[..., c]), [ryl, rxl], order=1, mode='nearest')
    out = sub.copy(); out[T] = np.clip(suau[T] + grain, 0, 1); alpha = np.clip(1 - d_out / 24.0, 0, 1).astype(np.float32); alpha[T] = 1.0
    rebut = dict(triangle_px=int((lab == k).sum()), regio_amb_vora_px=int(T.sum()), hipotenusa=dict(P1=P1, P2=P2, pendent=m_, angle_graus=float(np.degrees(np.arctan(m_)))),
                 cel_referencia_px=int(ref.sum()), nivell_cel_RGB=sub[ref].mean(0).round(5).tolist(), gra_cel_std=res_hp[ref].std(0).round(5).tolist(), gra_reflectit_std=grain.std(0).round(5).tolist(),
                 model_dins_L=[float(suau.mean(-1)[T].min()), float(suau.mean(-1)[T].max())], ploma_px=24, llindar_buit=llindar)
    return out.astype(np.float32), alpha, rebut

if __name__ == '__main__':
    import tifffile
    ap = argparse.ArgumentParser(); ap.add_argument('--entrada'); ap.add_argument('--sortida'); ap.add_argument('--x0', type=int); ap.add_argument('--y0', type=int); ap.add_argument('--rebut')
    a = ap.parse_args()
    with tifffile.TiffFile(a.entrada) as tf:
        pg = tf.pages[0]; img = pg.asarray(); icc = pg.tags.get('InterColorProfile'); icc = bytes(icc.value) if icc is not None else None
    img = img[..., :3].astype(np.float32) / (65535.0 if img.dtype == np.uint16 else 255.0)
    rgb, alpha, rebut = calcula(img)
    u = np.concatenate([np.round(np.clip(rgb, 0, 1) * 65535), np.round(alpha[..., None] * 65535)], -1).astype(np.uint16)
    u[0, 0, 3] = max(u[0, 0, 3], 1); u[-1, -1, 3] = max(u[-1, -1, 3], 1)   # 1 DN d'alfa a dues cantonades: els límits de la capa = la caixa (posició exacta a Photoshop)
    tifffile.imwrite(a.sortida, u, photometric='rgb', extrasamples=[2], iccprofile=icc, compression='zlib')
    rebut.update(entrada=a.entrada, sortida=a.sortida, origen=[a.x0, a.y0], mida=list(img.shape[:2]))
    if a.rebut: open(a.rebut, 'w').write(json.dumps(rebut, ensure_ascii=False, indent=1))
    print('CANTONADA', json.dumps(rebut, ensure_ascii=False))
