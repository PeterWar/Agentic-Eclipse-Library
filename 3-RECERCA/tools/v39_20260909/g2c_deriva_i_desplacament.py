"""G2c · (1) Deriva PREDITA del sensor de la Vixen respecte del cel entre les meitats temporals (mitjana de sol_x/sol_y del registre F1.3 dels fotogrames d'inici i de final, passada a píxels del llenç amb l'escala i la rotació de la cadena);
(2) desplaçament MESURAT del patró de la caixa entre les meitats temporals (mapa de correlació creuada normalitzada, banda 4–32 px, retards ±48 px) contra el control de meitats aleatòries;
(3) panell 1:1 de la caixa a la MATEIXA escala: Vixen, Sony, fusió (banda 4–64) i Vixen inici/final.
Ús: g2c_deriva_i_desplacament.py x0 y0 x1 y1"""
import sys as _s0; from pathlib import Path as _P0; _s0.path.insert(0, str(_P0(__file__).resolve().parent.parent / 'v38_20260908'))
from comu38 import *
import cv2
from scipy.ndimage import gaussian_filter
CAU39 = _P0(__file__).resolve().parent / 'cau'; REB39 = ROOT / 'research/tools/v39_20260909' / 'rebuts' if (ROOT / 'research/tools/v39_20260909/rebuts').exists() else None
import importlib.util
_c39 = importlib.util.spec_from_file_location('comu39', str(_P0(__file__).resolve().parent / 'comu39.py')); c39 = importlib.util.module_from_spec(_c39); _c39.loader.exec_module(c39); REB39 = c39.REB39; VIS39 = c39.VIS39
SONY36 = ROOT / 'research/tools/v36_20260908/cau/sony_corrected_total_v36.npy'


def band(a, s1, s2): return gaussian_filter(a, s1) - gaussian_filter(a, s2)
def ln_crop(p, sl, c=1):
    arr = np.load(p, mmap_mode='r'); a = np.asarray(arr[sl][..., c] if arr.ndim == 3 else arr[sl], np.float32); m = np.isfinite(a) & (a > 0); return np.where(m, np.log(np.maximum(a, 1e-9)), 0), m
def ncc_map(a, b, m, R=48):
    """correlació normalitzada de a contra b desplaçada (dx, dy) dins de ±R, sobre la màscara m (píxels vàlids a totes dues)"""
    out = np.full((2 * R + 1, 2 * R + 1), np.nan, np.float32); h, w = a.shape
    for dy in range(-R, R + 1):
        for dx in range(-R, R + 1):
            sa = (slice(max(0, dy), min(h, h + dy)), slice(max(0, dx), min(w, w + dx))); sb = (slice(max(0, -dy), min(h, h - dy)), slice(max(0, -dx), min(w, w - dx)))
            mm = m[sa] & m[sb]; u = a[sa][mm]; v = b[sb][mm]; u = u - u.mean(); v = v - v.mean(); d = np.sqrt((u * u).sum() * (v * v).sum())
            out[dy + R, dx + R] = (u * v).sum() / d if d > 0 else np.nan
    return out


def main():
    x0, y0, x1, y1 = [int(v) for v in sys.argv[1:5]]
    # (1) deriva predita
    tag = 'vixen'; path = RUNS[tag]; run = comu.Run.obre(str(path)); ctx = f2.Ctx(run)
    pos = json.loads((path / '4-rebuts/F1.3_registre.json').read_text())['fotogrames']; meta = json.loads((CAU36 / f'{tag}_meta.json').read_text())['frames']
    names = [m['name'] for m in meta]; ordre = sorted(range(len(names)), key=lambda i: meta[i]['t']); n = len(ordre)
    ini = [names[i] for j, i in enumerate(ordre) if j < n / 2]; fin = [names[i] for j, i in enumerate(ordre) if j >= n / 2]
    def mitj(ns): return np.array([np.mean([pos[q]['sol_x'] for q in ns]), np.mean([pos[q]['sol_y'] for q in ns])]), np.mean([meta[names.index(q)]['t'] for q in ns])
    (si, ti), (sf, tf) = mitj(ini), mitj(fin); dsens = sf - si   # el Sol es mou al sensor → un patró fix del sensor es mou −d al cel (en coordenades del Sol)
    # sensor → llenç: rx = ca·dx + sa·dy + sol_x ⇒ un desplaçament del Sol al sensor (Δsx, Δsy) equival a moure el patró del sensor en coordenades del llenç per (−(ca·Δsx − sa·Δsy), −(sa·Δsx + ca·Δsy)) / k
    ca, sa, k = float(ctx.ca), float(ctx.sa), float(ctx.k); dll = np.array([-(ca * dsens[0] - sa * dsens[1]), -(sa * dsens[0] + ca * dsens[1])]) / k
    tot = np.array([pos[names[ordre[-1]]]['sol_x'] - pos[names[ordre[0]]]['sol_x'], pos[names[ordre[-1]]]['sol_y'] - pos[names[ordre[0]]]['sol_y']])
    log(f'Vixen: {n} fotogrames · t inici mitjà {ti:.1f} s, final {tf:.1f} s · Sol al sensor: inici ({si[0]:.1f}, {si[1]:.1f}) → final ({sf[0]:.1f}, {sf[1]:.1f}): Δ ({dsens[0]:+.1f}, {dsens[1]:+.1f}) px de sensor (primer→últim fotograma: ({tot[0]:+.1f}, {tot[1]:+.1f}))')
    log(f'  ⇒ un patró FIX del sensor es desplaça al llenç, entre les meitats temporals, ({dll[0]:+.1f}, {dll[1]:+.1f}) px (|d| {np.hypot(*dll):.1f}; k {k:.4f}, angle {np.degrees(np.arctan2(sa, ca)):+.1f}°)')
    # (2) desplaçament mesurat
    pad = 128; sl = (slice(max(y0 - pad, 0), min(y1 + pad, H)), slice(max(x0 - pad, 0), min(x1 + pad, W)))
    core = np.zeros((sl[0].stop - sl[0].start, sl[1].stop - sl[1].start), bool); core[y0 - sl[0].start:y1 - sl[0].start, x0 - sl[1].start:x1 - sl[1].start] = True
    VI, mI = ln_crop(CAU39 / 'vixen_total_v38_inici.npy', sl); VF, mF = ln_crop(CAU39 / 'vixen_total_v38_final.npy', sl); VE, mE = ln_crop(CAU39 / 'vixen_total_v38_parell.npy', sl); VO, mO = ln_crop(CAU39 / 'vixen_total_v38_senar.npy', sl)
    V, mV = ln_crop(CAU38 / 'vixen_total_v38.npy', sl); S, mS = ln_crop(SONY36, sl); F, mFu = ln_crop(CAU38 / 'fusion_total_v38.npy', sl); m = mI & mF & mE & mO & mV & mS & mFu & core
    rep = dict(caixa=[x0, y0, x1, y1], deriva_predita_llenc_px=[float(dll[0]), float(dll[1])], delta_sensor_px=[float(dsens[0]), float(dsens[1])], t_inici=float(ti), t_final=float(tf))
    for s1, s2 in ((4, 16), (8, 32)):
        for nom, (a, b) in {'inici→final': (VI, VF), 'parell→senar': (VE, VO)}.items():
            cc = ncc_map(band(a, s1, s2), band(b, s1, s2), m, R=40); R = 40; iy, ix = np.unravel_index(np.nanargmax(cc), cc.shape); dx, dy = ix - R, iy - R
            px, py = int(round(dll[0])), int(round(dll[1])); apred = float(cc[py + R, px + R]) if abs(px) <= R and abs(py) <= R else float('nan')
            rep[f'ncc_{s1}_{s2}_{nom}'] = dict(pic=[int(dx), int(dy)], valor_pic=float(cc[iy, ix]), a_zero=float(cc[R, R]), a_prediccio=apred)
            log(f'banda {s1}–{s2}: {nom}: pic a ({dx:+d}, {dy:+d}) px = {cc[iy, ix]:+.3f} · a (0,0) {cc[R, R]:+.3f} · a la deriva predita ({px:+d}, {py:+d}) {apred:+.3f}')
            # vista del mapa
            v = np.nan_to_num(cc); img = cv2.applyColorMap(np.clip((v - v.min()) / max(v.max() - v.min(), 1e-6) * 255, 0, 255).astype(np.uint8), cv2.COLORMAP_VIRIDIS); img = cv2.resize(img, (img.shape[1] * 6, img.shape[0] * 6), interpolation=cv2.INTER_NEAREST)
            cv2.circle(img, (int((px + R + 0.5) * 6), int((py + R + 0.5) * 6)), 10, (255, 255, 255), 2); cv2.drawMarker(img, (int((R + 0.5) * 6), int((R + 0.5) * 6)), (0, 0, 255), cv2.MARKER_CROSS, 16, 2)
            cv2.imwrite(str(VIS39 / f"G2c_ncc_{s1}_{s2}_{nom.replace('→', '_a_')}.png"), img)
    # (3) panell 1:1 a la mateixa escala (banda 4–64, ±3σ del rms de la Vixen)
    bV, bS, bF, bI, bFi = (band(x, 4, 64) for x in (V, S, F, VI, VF)); sc = 3 * float(np.std(bV[m]))
    def g8(a): return np.clip((a / sc + 1) / 2 * 255, 0, 255).astype(np.uint8)
    tiles = [('Vixen 4-64', bV), ('Sony 4-64', bS), ('fusio V38 4-64', bF), ('Vixen INICI 4-64', bI), ('Vixen FINAL 4-64', bFi), ('inici - final', bI - bFi)]
    hh, ww = bV.shape; canvas = np.zeros((2 * (hh + 30), 3 * ww, 3), np.uint8)
    for i, (t, a) in enumerate(tiles):
        r, c = divmod(i, 3); tile = cv2.cvtColor(g8(np.where(m | ~core, a, 0)), cv2.COLOR_GRAY2BGR); cv2.rectangle(tile, (x0 - sl[1].start, y0 - sl[0].start), (x1 - sl[1].start, y1 - sl[0].start), (0, 255, 0), 1)
        canvas[r * (hh + 30) + 30:(r + 1) * (hh + 30), c * ww:(c + 1) * ww] = tile; cv2.putText(canvas, f'{t}  (escala ±{sc:.4f} ln)', (c * ww + 6, r * (hh + 30) + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    cv2.imwrite(str(VIS39 / 'G2c_panell_caixa_1a1.png'), canvas); c39.savejson(REB39 / f'G2c_deriva_{x0}_{y0}.json', rep); log('G2c fet')


if __name__ == '__main__':
    main()
