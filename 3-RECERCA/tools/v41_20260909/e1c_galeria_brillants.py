"""E1c · Les 8 estrelles més brillants (flux d'obertura a la fusió) a 1:1 ×4: fusió (σ-píxel ±5), nul (+40 px), i els filtres V38 (u16 ±0,15 al voltant de 0,5) amb el seu nul."""
from comu41 import *
import cv2
from scipy.ndimage import shift as ndshift
PC38 = ROOT / 'research/tools/v38_20260908/purs/cau'; R = 24; Z = 4; NUL = (40, 0)
rep = json.loads((REB41 / 'E1b_psf_apilada.json').read_text()); g = rep['per_estrella_fusio'][:8]
F = np.load(CAU38 / 'fusion_total_v38.npy', mmap_mode='r')
FIL = {'01 ACHF fi 2-32': CAU38 / '01_v38_u16.npy', 'P03 MGN': PC38 / 'P03_MGN_u16.npy', 'P04 WOW': PC38 / 'P04_WOW_u16.npy', 'P05 WOW bil.': PC38 / 'P05_WOW_bilateral_u16.npy', 'P02 RHEF': PC38 / 'P02_RHEF_u16.npy'}
arrs = {k: np.load(p, mmap_mode='r') for k, p in FIL.items()}
def ret(arr, x, y, c=None, dx=0, dy=0):
    s = arr[y + dy - R:y + dy + R + 1, x + dx - R:x + dx + R + 1]; return np.asarray(s[..., c] if c is not None else s, np.float64)
T = 2 * R + 1; cols = 2 + 2 * len(FIL); canvas = np.full((len(g) * (T * Z + 6) + 30, cols * (T * Z + 6) + 230, 3), 25, np.uint8)
heads = ['fusio +-5s', 'nul'] + sum([[k, 'nul'] for k in FIL], [])
for j, h in enumerate(heads): cv2.putText(canvas, h[:13], (230 + j * (T * Z + 6) + 2, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
for i, d in enumerate(g):
    x, y = d['x'], d['y']; tiles = []
    for dx, dy in ((0, 0), NUL):
        s = ret(F, x, y, 1, dx, dy); yy, xx = np.mgrid[-R:R + 1, -R:R + 1]; rr = np.hypot(xx, yy); an = (rr >= 14); bg = np.median(s[an]); sd = 1.4826 * np.median(np.abs(s[an] - bg)); tiles.append(np.clip(((s - bg) / sd / 5 + 1) / 2, 0, 1))
    for k, a in arrs.items():
        for dx, dy in ((0, 0), NUL):
            s = ret(a, x, y, None, dx, dy) / 65535.0; tiles.append(np.clip((s - 0.5) / 0.3 + 0.5, 0, 1))
    for j, tl in enumerate(tiles):
        img = cv2.resize((tl * 255).astype(np.uint8), (T * Z, T * Z), interpolation=cv2.INTER_NEAREST); y0, x0 = 30 + i * (T * Z + 6), 230 + j * (T * Z + 6); canvas[y0:y0 + T * Z, x0:x0 + T * Z] = img[..., None]
        cv2.drawMarker(canvas, (x0 + T * Z // 2, y0 + T * Z // 2), (0, 160, 0), cv2.MARKER_CROSS, 10, 1)
    cv2.putText(canvas, f"({x},{y}) {d['r_R']:.1f}R flux {d['flux_r4_sigma']:.0f} sigma-px", (4, 30 + i * (T * Z + 6) + T * Z // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (200, 255, 200), 1)
cv2.imwrite(str(VIS41 / 'E1c_galeria_8_brillants.png'), canvas); print('E1c fet', VIS41 / 'E1c_galeria_8_brillants.png')
