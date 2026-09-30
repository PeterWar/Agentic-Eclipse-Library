"""P2d (V42) · Escala i rotació del POWAAAH3 pels MARS de la Lluna contra la LROC (el que compta per a la capa d'earthshine): escombrada d'escala 1,29–1,345 (pas 0,0025)
i de rotació 44 ± 1,5° (pas 0,25°), correlació del disc interior (r < 0,9 R) passa-alt σ 6 px. El disc del POWAAAH3 es remostreja a la graella de la capa LROC (991 px,
centre lunar de la capa) per a cada escala. Nul: LROC mirallada."""
from comu42 import *
import tifffile
from scipy.ndimage import gaussian_filter, rotate
SRC = Path('/Users/USUARI/Desktop/POWAAAH3.tif'); RL = 453.5


def main():
    P = json.loads((REB42 / 'P2_powaaah.json').read_text()); cxm, cym = P['disc']['cx'], P['disc']['cy']; a = np.load(CAU42 / 'lroc_capa_v39_rgba.npy'); lb = json.loads((REB42 / 'P2b_rotacio.json').read_text())['lroc_bbox']
    lroc = a[..., :3].mean(-1).astype(np.float32); hl, wl = lroc.shape; ccx, ccy = (CX + 14.8) - lb[0], (CY + 0.9) - lb[1]
    with tifffile.TiffFile(SRC) as t: g = t.pages[0].asarray()[..., 1].astype(np.float32)
    yy, xx = np.mgrid[0:hl, 0:wl].astype(np.float32); d = np.hypot(xx - ccx, yy - ccy); inn = d < 0.9 * RL
    B_ = np.where(inn, np.log(np.maximum(lroc, 1e-3)) - gaussian_filter(np.log(np.maximum(lroc, 1e-3)), 6), 0)
    def A_of(esc, ang):
        th = np.deg2rad(ang); c, s = np.cos(th), np.sin(th); px = (cxm + esc * (c * (xx - ccx) - s * (yy - ccy))).astype(np.float32); py = (cym + esc * (s * (xx - ccx) + c * (yy - ccy))).astype(np.float32)
        pd = cv2.remap(g, px, py, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT); z = np.log(np.maximum(pd, 1)); return np.where(inn, z - gaussian_filter(z, 6), 0)
    def corr(A, B): return float((A * B)[inn].sum() / (np.linalg.norm(A[inn]) * np.linalg.norm(B[inn]) + 1e-12))
    res = []
    for esc in np.arange(1.290, 1.3451, 0.0025):
        A = A_of(esc, 44.0); res.append((esc, corr(A, B_)))
    res = np.array(res); k = int(np.argmax(res[:, 1])); esc_b = float(res[k, 0]); log('escala pels mars: ' + ' '.join(f'{e:.4f}:{c:.3f}' for e, c in res))
    angs = np.arange(42.5, 45.51, 0.25); ra = [(ang, corr(A_of(esc_b, ang), B_)) for ang in angs]; ra = np.array(ra); j = int(np.argmax(ra[:, 1])); ang_b = float(ra[j, 0])
    nul = max(corr(A_of(esc_b, ang_b), np.where(inn, B_[:, ::-1], 0)), corr(A_of(esc_b, ang_b), np.where(inn, B_[::-1, :], 0)))
    log(f'MARS vs LROC: escala {esc_b:.4f} (pic {res[k, 1]:.3f}; a 1,3066 {res[np.argmin(np.abs(res[:, 0] - 1.3066)), 1]:.3f}; a 1,3306 {res[np.argmin(np.abs(res[:, 0] - 1.3306)), 1]:.3f}) · rotació {ang_b:+.2f}° (pic {ra[j, 1]:.3f}) · nul mirallat {nul:.3f} · R_lluna implicat pel disc fosc {P["disc"]["R"] / esc_b:.1f} px')
    savejson(REB42 / 'P2d_mars_escala.json', dict(escombrada_escala=res.tolist(), escala=esc_b, rotacio=ang_b, pic=float(ra[j, 1]), nul=nul, escombrada_rotacio=ra.tolist())); log('P2d fet')


if __name__ == '__main__':
    main()
