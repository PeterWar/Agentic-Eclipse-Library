"""P2c (V42) · L'ESCALA del POWAAAH3 mesurada a la CORONA, no suposada. P2 la treia del radi del disc suposant R_lluna = 455,5 px al llenç; però al llenç les capes de
Pere (perles/limbe, C2) fan R 453,5 (E4) i la LROC/earthshine s'hi van reescalar ×0,9956 (research/128). Aquí: escombrada d'escala 1,290–1,325 correlacionant
ln(corona) del POWAAAH3 (polar al voltant del seu Sol = disc + (Sol − forat)·esc girat) amb ln(fusió V42) a 1,25–2,3 R☉ (passa-alt radial i azimutal; la rotació fixa
a +44,0°). Es dona l'escala del pic i el radi lunar que implica (R_pow / esc)."""
from comu42 import *
import tifffile
from scipy.ndimage import map_coordinates, gaussian_filter
SRC = Path('/Users/USUARI/Desktop/POWAAAH3.tif'); MOON = (CX + 14.8, CY + 0.9)


def polar(img, cx, cy, rs, nth=1440, ang0=0.0):
    th = np.linspace(0, 2 * np.pi, nth, endpoint=False) + ang0; R, T = np.meshgrid(rs, th, indexing='ij'); v = map_coordinates(img, [cy + R * np.sin(T), cx + R * np.cos(T)], order=1, mode='nearest')
    v = v - gaussian_filter(v, (0, 30), mode='wrap'); v = v - gaussian_filter(v, (6, 0)); return v


def main():
    P = json.loads((REB42 / 'P2_powaaah.json').read_text()); cxm, cym, Rm = P['disc']['cx'], P['disc']['cy'], P['disc']['R']; ang = np.deg2rad(P['rotacio_deg'])
    with tifffile.TiffFile(SRC) as t: g = t.pages[0].asarray()[..., 1].astype(np.float32)
    pg = np.log(np.maximum(g, 1)); F = np.load(CAU42 / 'fusion_total_v42.npy', mmap_mode='r'); fg = np.log(np.maximum(np.nan_to_num(np.asarray(F[..., 1], np.float32)), 1))
    rs = np.linspace(2.3 * RS, 3.6 * RS, 90); pb = polar(fg, CX, CY, rs)
    # el Sol al POWAAAH3: disc + esc·R(ang)·(Sol − forat)  (la rotació POW→llenç és +ang, o sigui llenç→POW és −ang... es prova amb el signe que dona el pic més alt)
    v = np.array([CX - MOON[0], CY - MOON[1]]); res = []
    for esc in np.arange(1.280, 1.3401, 0.0025):
        best = None
        for sgn in (+1, -1):
            c, s = np.cos(sgn * ang), np.sin(sgn * ang); sun = (cxm + esc * (c * v[0] - s * v[1]), cym + esc * (s * v[0] + c * v[1]))
            pa = polar(pg, sun[0], sun[1], rs * esc, ang0=sgn * ang); pa2 = polar(pg, sun[0], sun[1], rs * esc, ang0=-sgn * ang)
            for cand, lab in ((pa, sgn), (pa2, -sgn)):
                cc = float((cand * pb).sum() / (np.linalg.norm(cand) * np.linalg.norm(pb) + 1e-12))
                if best is None or cc > best[0]: best = (cc, lab)
        res.append((esc, best[0], best[1])); log(f'esc {esc:.4f}: corr {best[0]:+.4f} (signe {best[1]:+d}) · R_lluna implicat {Rm / esc:.1f} px')
    res = np.array(res); k = int(np.argmax(res[:, 1])); esc_b = float(res[k, 0])
    # refinament parabòlic
    if 0 < k < len(res) - 1:
        y0, y1, y2 = res[k - 1, 1], res[k, 1], res[k + 1, 1]; d = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2) if (y0 - 2 * y1 + y2) != 0 else 0; esc_b = float(res[k, 0] + d * 0.0025)
    log(f'ESCALA per la corona: {esc_b:.4f} (pic {res[k, 1]:+.4f}) → R_lluna al llenç {Rm / esc_b:.1f} px · la de P2 (R=455,5) era {P["escala_pow_per_llenc"]:.4f}; la de R=453,5 seria {Rm / 453.5:.4f}')
    savejson(REB42 / 'P2c_escala.json', dict(escombrada=res.tolist(), escala_corona=esc_b, pic=float(res[k, 1]), R_lluna_implicat_px=Rm / esc_b, escala_P2=P['escala_pow_per_llenc'], escala_R453=Rm / 453.5)); log('P2c fet')


if __name__ == '__main__':
    main()
