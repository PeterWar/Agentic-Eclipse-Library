"""E3 (V42) · Revisió de l'ALINEAMENT de totes les capes de la V42 (petició de Pere), mesurat, no suposat:
 · capes 06–12 de Pere (no linealitzades) contra la base corba V42: translació per correlació de fase de ln(G) a l'anell 1,05–1,6 R☉ i rotació per correlació azimutal (perfils polars);
 · filtres: translació per correlació de fase de la banda 8–32 px contra la 01 (haurien de ser 0: surten de la mateixa base);
 · capa d'estrelles: pics de la capa contra pics de la base amb estrelles (han de coincidir a 0 px);
 · POWAAAH3: disc (cercle ajustat a la vora de la màscara/contingut) contra el forat V38, i mars contra la LROC (rotació);
 · LROC: centre del disc de la capa contra el forat V38.
Sortida: REB42/E3_alineament.json i taula al rebut. Es fa sobre el PSB muntat (staging o publicat)."""
from comu42 import *
import importlib.util as _iu
from psd_tools import PSDImage
from scipy.ndimage import gaussian_filter, map_coordinates, rotate
_sp = _iu.spec_from_file_location('c4_v39', HERE39 / 'c4_projecte_v39.py'); C = _iu.module_from_spec(_sp); _sp.loader.exec_module(C)
MOON = (CX + 14.8, CY + 0.9); RL = 455.5


def capa_G(l):
    rec = l._record; g = C.channel(l, 1).astype(np.float32) / 65535; full = np.zeros((H, W), np.float32); full[rec.top:rec.bottom, rec.left:rec.right] = g; return full, (rec.left, rec.top, rec.right, rec.bottom)


def fase(a, b, m):
    a = np.where(m, a, 0); b = np.where(m, b, 0); ys, xs = np.nonzero(m); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    A = a[y0:y1, x0:x1]; B = b[y0:y1, x0:x1]; (dx, dy), resp = cv2.phaseCorrelate((A - A.mean()).astype(np.float32), (B - B.mean()).astype(np.float32)); return float(dx), float(dy), float(resp)


def polar(img, cx, cy, r0, r1, nr=48, nth=1440):
    th = np.linspace(0, 2 * np.pi, nth, endpoint=False); rs = np.linspace(r0, r1, nr); R, T = np.meshgrid(rs, th, indexing='ij'); v = map_coordinates(img, [cy + R * np.sin(T), cx + R * np.cos(T)], order=1, mode='nearest'); return v - gaussian_filter(v, (0, 40), mode='wrap')


def rot_az(a, b):
    Fa = np.fft.rfft(a, axis=1); Fb = np.fft.rfft(b, axis=1); cc = np.fft.irfft(Fa * np.conj(Fb), n=a.shape[1], axis=1).sum(axis=0) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12); k = int(np.argmax(cc)); return (k * 360.0 / a.shape[1] + 180) % 360 - 180, float(cc[k])


def cercle(mask, cx0, cy0, r0):
    th = np.linspace(0, 2 * np.pi, 720, endpoint=False); rs = np.arange(r0 - 40, r0 + 40, 0.5); R, T = np.meshgrid(rs, th, indexing='ij'); prof = map_coordinates(mask.astype(np.float32), [cy0 + R * np.sin(T), cx0 + R * np.cos(T)], order=1)
    i = np.argmin(np.abs(prof - 0.5), axis=0); redge = rs[i]; x = cx0 + redge * np.cos(th); y = cy0 + redge * np.sin(th); A = np.c_[2 * x, 2 * y, np.ones_like(x)]; sol = np.linalg.lstsq(A, x * x + y * y, rcond=None)[0]
    cx, cy = sol[0], sol[1]; return float(cx), float(cy), float(np.sqrt(sol[2] + cx * cx + cy * cy))


def main():
    psb = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE42 / 'staging/V42.psb'; s = PSDImage.open(psb); L = {l.name: l for l in s}; r, t = coords(); rep = {'psb': str(psb), 'capes': {}}
    base, _ = capa_G(L['00 Base corba (total) · V42']); lb = np.log(np.maximum(base, 1e-4)); an = (r > 1.05 * RS) & (r < 1.6 * RS) & (base > 0.02)
    pb = polar(lb, CX, CY, 1.1 * RS, 1.5 * RS)
    for nom in ('12 1/3200 perles', '11 1/500 limbe', '10 1/125', '09 1/60 x2', '08 1/30 x4 quar', '07 1/15 x2 quar', '06 1/8 x4 quar'):
        g, box = capa_G(L[nom]); m = an & (g > 0.02) & (g < 0.98); 
        if m.sum() < 50000: rep['capes'][nom] = {'nota': 'sense solapament útil amb la base a 1,05–1,6 R☉ (capa curta/saturada)', 'px': int(m.sum())}; log(f'{nom}: sense solapament útil'); continue
        lg = np.log(np.maximum(g, 1e-4)); dx, dy, resp = fase(gaussian_filter(lg, 1) - gaussian_filter(lg, 12), gaussian_filter(lb, 1) - gaussian_filter(lb, 12), m); ang, val = rot_az(polar(lg, CX, CY, 1.1 * RS, 1.5 * RS), pb)
        rep['capes'][nom] = {'translacio_px': [dx, dy], 'resposta': resp, 'rotacio_deg': ang, 'pic_azimutal': val, 'px': int(m.sum())}; log(f'{nom}: translació ({dx:+.2f}, {dy:+.2f}) px (resp {resp:.2f}) · rotació {ang:+.2f}° (pic {val:.2f})')
    # filtres contra la 01 (banda 8–32)
    f01, _ = capa_G(L['01 ACHF fi 2-32 · V42']); mf = (r > 1.2 * RS) & (r < 3 * RS) & (base > 0.02); b01 = gaussian_filter(f01, 8) - gaussian_filter(f01, 32)
    for nom in [k for k in L if (k.startswith(('04 ', '05 ', '06 ACHF', '03 ', '07 ACHF', 'P0')) and 'V42' in k)]:
        g, _ = capa_G(L[nom]); dx, dy, resp = fase(gaussian_filter(g, 8) - gaussian_filter(g, 32), b01, mf); rep['capes'][nom] = {'translacio_px_vs_01': [dx, dy], 'resposta': resp}; log(f'{nom}: vs 01 ({dx:+.2f}, {dy:+.2f}) px resp {resp:.2f}')
    # estrelles: pics de la capa vs pics de la base
    e, _ = capa_G(L['Estrelles (llum mesurada) · V42']); st = json.loads((CAU42 / 'estrelles_v42.json').read_text())['estrelles']; d_ = []
    for sst in st[:40]:
        x, y = sst['x'], sst['y']; sub = e[y - 12:y + 13, x - 12:x + 13]
        if sub.max() <= 0: continue
        iy, ix = np.unravel_index(np.argmax(sub), sub.shape); d_.append([ix - 12, iy - 12])
    d_ = np.array(d_) if d_ else np.zeros((0, 2)); rep['capes']['Estrelles (llum mesurada) · V42'] = {'n': int(len(d_)), 'desplacament_pic_px_mediana': np.median(np.abs(d_), 0).tolist() if len(d_) else None}; log(f"estrelles: {len(d_)} pics, |desplaçament| mediana {np.median(np.abs(d_), 0) if len(d_) else 'n/d'} px")
    # POWAAAH3 i LROC: cercle del disc i mars
    for nom in [k for k in L if k.startswith('POWAAAH3')] + ['Compara LROC']:
        l = L[nom]; rec = l._record; md = rec.mask_data
        if md is not None:
            mk = np.zeros((H, W), np.float32); mm = C.channel(l, -2).astype(np.float32) / 65535; mt, mb, ml, mr = max(md.top, 0), min(md.bottom, H), max(md.left, 0), min(md.right, W); mk[mt:mb, ml:mr] = mm[mt - md.top:mt - md.top + (mb - mt), ml - md.left:ml - md.left + (mr - ml)]
            cx, cy, rr = cercle(mk, MOON[0], MOON[1], RL); rep['capes'][nom] = {'disc_mascara': {'cx': cx, 'cy': cy, 'R': rr, 'desplacament_vs_forat_px': [cx - MOON[0], cy - MOON[1]]}}; log(f'{nom}: disc de la màscara a ({cx:.1f}, {cy:.1f}) R {rr:.1f} → respecte del forat ({cx - MOON[0]:+.1f}, {cy - MOON[1]:+.1f}) px')
    # mars: POWAAAH3 vs LROC (rotació residual)
    pn = [k for k in L if k.startswith('POWAAAH3')][0]; gp, _ = capa_G(L[pn]); gl, _ = capa_G(L['Compara LROC']); y0, y1, x0, x1 = int(MOON[1] - 430), int(MOON[1] + 430), int(MOON[0] - 430), int(MOON[0] + 430)
    yy, xx = np.mgrid[y0:y1, x0:x1]; inn = np.hypot(xx - MOON[0], yy - MOON[1]) < 0.9 * RL
    A_ = np.where(inn, np.log(np.maximum(gp[y0:y1, x0:x1], 1e-4)) - gaussian_filter(np.log(np.maximum(gp[y0:y1, x0:x1], 1e-4)), 6), 0); B_ = np.where(inn, np.log(np.maximum(gl[y0:y1, x0:x1], 1e-4)) - gaussian_filter(np.log(np.maximum(gl[y0:y1, x0:x1], 1e-4)), 6), 0)
    angs = np.arange(-10, 10.01, 0.25); cc = [float((A_ * rotate(B_, a, reshape=False, order=1))[inn].sum() / (np.linalg.norm(A_[inn]) * np.linalg.norm(B_[inn]) + 1e-12)) for a in angs]; k = int(np.argmax(cc))
    dx, dy, resp = fase(A_, B_, inn); rep['capes'][pn]['mars_vs_LROC'] = {'rotacio_residual_deg': float(angs[k]), 'pic': cc[k], 'translacio_px': [dx, dy], 'resposta': resp}; log(f'POWAAAH3 mars vs LROC: rotació residual {angs[k]:+.2f}° (pic {cc[k]:.3f}), translació ({dx:+.1f}, {dy:+.1f}) px')
    savejson(REB42 / 'E3_alineament.json', rep); log('E3 fet')


if __name__ == '__main__':
    main()
