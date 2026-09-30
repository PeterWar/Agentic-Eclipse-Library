"""QA de V5: perfil radial contra V3, estructura azimutal contra V3 i les capes soles, i zooms (centre, creixent, Lluna)."""
import numpy as np, json, glob
from scipy import ndimage as ndi
from PIL import Image, ImageDraw
meta = json.load(open('v3/meta.json'))
files = sorted(glob.glob('v3/*_rgb.npy')); files = [f for f in files if 'merged' not in f]
SUN3 = (4021.89, 2738.66); RS = 446.15
mer = np.load('v3/merged_rgb.npy', mmap_mode='r'); V5 = np.load('v5/compost_rgb16.npy', mmap_mode='r')
MOON3 = (4035.8, 2737.3); MR = 451.5
rf = np.arange(0.98, 3.0, 0.002); th = np.deg2rad(np.arange(0, 360, 0.5)); R, T = np.meshgrid(rf, th, indexing='ij')
def pol(arr, sun, off):
    X = sun[0] + R * RS * np.cos(T) - off[0]; Y = sun[1] - R * RS * np.sin(T) - off[1]
    return np.stack([ndi.map_coordinates(np.asarray(arr[..., c], np.float32) / 65535., [Y, X], order=1) for c in range(3)])
lum = lambda C: 0.2126 * C[0] + 0.7152 * C[1] + 0.0722 * C[2]
X3 = SUN3[0] + R * RS * np.cos(T); Y3 = SUN3[1] - R * RS * np.sin(T)
ok = (np.hypot(X3 - MOON3[0], Y3 - MOON3[1]) / MR > 1.03) & (~((np.rad2deg(T) > 160) & (np.rad2deg(T) < 178)) | (R > 1.12))
P3 = pol(mer, SUN3, (0, 0)); P5 = pol(V5, (SUN3[0] - 1, SUN3[1] - 1), (457, 463))
def med(P):
    L = np.where(ok, lum(P), np.nan); m = np.nanmedian(L, axis=1)
    o = np.isfinite(m); m[~o] = np.interp(np.flatnonzero(~o), np.flatnonzero(o), m[o]); return m
m3, m5 = med(P3), med(P5)
print('perfil (mediana az.):   r   V3     V5    V5/V3')
for r in (1.0, 1.02, 1.05, 1.1, 1.2, 1.3, 1.5, 1.7, 2.0, 2.5, 2.98):
    j = int(np.argmin(np.abs(rf - r))); print(f'  {rf[j]:4.2f}  {m3[j]:.3f}  {m5[j]:.3f}  {m5[j]/max(m3[j],1e-6):.3f}')
lnr = np.log(rf); g = np.linspace(lnr[0], lnr[-1], 6000)
def ring(m, lab):
    y = np.log(np.maximum(m, 1e-5)); yi = np.interp(g, lnr, y); ys = ndi.gaussian_filter1d(yi, 0.02 / (g[1] - g[0]), mode='nearest')
    res = yi - ys; sel = (np.exp(g) > 1.09) & (np.exp(g) < 2.9)
    print(f'test anells {lab}: rms {res[sel].std()*100:.2f} %, màx |{np.abs(res[sel]).max()*100:.2f}| % a r={np.exp(g[sel][np.argmax(np.abs(res[sel]))]):.3f}')
ring(m3, 'V3'); ring(m5, 'V5')
def struct(P):
    L = lum(P); mm = np.nanmedian(np.where(ok, L, np.nan), axis=1, keepdims=True); return np.log(np.maximum(L, 1e-5)) - np.log(np.maximum(mm, 1e-5))
S3, S5 = struct(P3), struct(P5)
for i, lab, r0, r1 in ((2, 'Capa 5 (1/125)', 1.0, 1.2), (4, '08 (1/30)', 1.25, 1.6), (5, '07 (1/15)', 1.4, 1.9), (6, '06 (1/8)', 1.55, 2.2)):
    Pi = pol(np.load(files[i], mmap_mode='r'), SUN3, tuple(meta['layers'][i]['bbox'][:2])); Si = struct(Pi)
    sel = ok & (R > r0) & (R < r1) & np.isfinite(Si) & np.isfinite(S3) & np.isfinite(S5)
    c3 = np.corrcoef(S3[sel], Si[sel])[0, 1]; c5 = np.corrcoef(S5[sel], Si[sel])[0, 1]
    a3 = np.polyfit(Si[sel], S3[sel], 1)[0]; a5 = np.polyfit(Si[sel], S5[sel], 1)[0]
    print(f'estructura vs {lab} a {r0}–{r1}: correlació V3 {c3:.3f} / V5 {c5:.3f}; contrast V3 {a3:.2f} / V5 {a5:.2f}')
# zooms
def crop(arr, ox, oy, cx, cy, S, gain=1.0, step=1):
    x0, y0 = int(cx - S) - ox, int(cy - S) - oy
    a = np.asarray(arr[y0:y0 + 2 * S:step, x0:x0 + 2 * S:step], np.float32) / 65535.
    return Image.fromarray((np.clip(a * gain, 0, 1) * 255).astype(np.uint8))
rows = []
for (lab, cx, cy, S, gain, step) in (('centre', SUN3[0], SUN3[1], 840, 1.0, 2), ('creixent', SUN3[0] - 0.97 * RS, SUN3[1] - 0.02 * RS, 260, 1.0, 1), ('Lluna ×6', SUN3[0] + 0.4 * RS, SUN3[1], 300, 6.0, 1)):
    t3 = crop(mer, 0, 0, cx, cy, S, gain, step); t5 = crop(V5, 457, 463, cx - 1, cy - 1, S, gain, step)
    row = Image.new('RGB', (t3.width + t5.width + 10, t3.height + 22), (30, 30, 30))
    row.paste(t3, (0, 20)); row.paste(t5, (t3.width + 10, 20))
    ImageDraw.Draw(row).text((4, 4), f'{lab}: V3 | V5', fill=(255, 255, 0)); rows.append(row)
W = max(r.width for r in rows); H = sum(r.height for r in rows)
out = Image.new('RGB', (W, H), (30, 30, 30)); y = 0
for r in rows: out.paste(r, (0, y)); y += r.height
out.save('v5/qa_zoom.png'); print(out.size)
