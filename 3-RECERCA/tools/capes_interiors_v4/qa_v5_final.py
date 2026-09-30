"""QA de V5 abans d'escriure el PSB: (1) el compost dins d'1,5 R☉ = el del V4 editat (protuberàncies/perles/limbe intactes);
(2) perfil radial suau (test d'anells) fins als cantons; (3) zooms."""
import numpy as np, json
from scipy import ndimage as ndi
from PIL import Image, ImageDraw
SUN = (4020.89, 2737.66); RS = 446.15
C5 = np.load('v5out/compost_rgb16.npy', mmap_mode='r')
# compost del V4 editat = compondre amb les màscares 10/11 originals? El tinc si reutilitzo el compositor amb elles.
# Més senzill: dins d'1,5 R☉ les màscares 04/03 noves són 0; comparo amb el que la merged del V4 editat digui? La merged
# del V4 editat és la que jo vaig escriure ahir (Photoshop actualitza la merged en desar? sí, Photoshop la recompon).
import os
from psd_tools import PSDImage
D = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/')
psd = PSDImage.open(D + 'CapesInteriorsV4.psb'); hdr = psd._record.header
img = psd._record.image_data.get_data(hdr)
mer4 = np.stack([np.frombuffer(c, dtype='>u2').reshape(hdr.height, hdr.width) for c in img[:3]], -1)
d = np.abs(np.asarray(C5, np.int32) - mer4.astype(np.int32)).max(-1) / 65535.
yy, xx = np.mgrid[0:hdr.height:4, 0:hdr.width:4]
rs = np.hypot(xx - SUN[0], yy - SUN[1]) / RS
ds = d[::4, ::4]
for r0, r1 in ((0.0, 1.3), (1.3, 1.9), (1.9, 2.6), (2.6, 4.0), (4.0, 12.0)):
    sel = (rs >= r0) & (rs < r1)
    print(f'|V5 − V4editat(merged)| a r {r0}–{r1}: mediana {np.median(ds[sel]):.4f}  p99 {np.percentile(ds[sel], 99):.4f}  màx {ds[sel].max():.4f}')
# perfil i test d'anells del compost V5
rr = np.arange(0.98, 9.5, 0.005); th = np.deg2rad(np.arange(0, 360, 0.5)); R, T = np.meshgrid(rr, th, indexing='ij')
X = SUN[0] + R * RS * np.cos(T); Y = SUN[1] - R * RS * np.sin(T)
inside = (X >= 458) & (X < 7416) & (Y >= 464) & (Y < 5102)
G = ndi.map_coordinates(np.asarray(C5[..., 1], np.float32) / 65535., [Y, X], order=1); G[~inside] = np.nan
prof = np.nanmedian(G, axis=1)
ok = np.isfinite(prof); prof[~ok] = np.interp(np.flatnonzero(~ok), np.flatnonzero(ok), prof[ok])
lnr = np.log(rr); g = np.linspace(lnr[0], lnr[-1], 8000)
yi = np.interp(g, lnr, np.log(np.maximum(prof, 1e-5))); ys = ndi.gaussian_filter1d(yi, 0.02 / (g[1] - g[0]), mode='nearest')
res = yi - ys; sel = (np.exp(g) > 1.09) & (np.exp(g) < 8.5)
print(f'\ntest anells V5 (1,09–8,5 R☉): rms {res[sel].std()*100:.2f} % màx |{np.abs(res[sel]).max()*100:.2f}| % a r={np.exp(g[sel][np.argmax(np.abs(res[sel]))]):.2f}')
print('perfil V5 (G, mediana az.):', {round(float(q), 1): round(float(prof[int(round((q - 0.98) / 0.005))]), 3) for q in (1.0, 1.2, 1.5, 1.8, 2.0, 2.2, 2.5, 2.8, 3.0, 3.5, 4.0, 5.0, 7.0, 9.0)})
# zooms: transició 1,8–3,2 R☉ (V4editat vs V5) i el creixent
def crop(arr, cx, cy, S, gain=1.0, step=1):
    x0, y0 = int(cx - S), int(cy - S)
    a = np.asarray(arr[y0:y0 + 2 * S:step, x0:x0 + 2 * S:step], np.float32) / 65535.
    return Image.fromarray((np.clip(a * gain, 0, 1) * 255).astype(np.uint8))
rows = []
for lab, cx, cy, S, gain, step in (('transició E (θ=0°)', SUN[0] + 2.5 * RS, SUN[1], 560, 1.5, 2), ('creixent', SUN[0] - 0.97 * RS, SUN[1] - 0.02 * RS, 260, 1.0, 1), ('camp llunyà NO', SUN[0] - 4.5 * RS, SUN[1] - 3.2 * RS, 500, 1.5, 2)):
    t4 = crop(mer4, cx, cy, S, gain, step); t5 = crop(C5, cx, cy, S, gain, step)
    row = Image.new('RGB', (t4.width * 2 + 10, t4.height + 22), (30, 30, 30))
    row.paste(t4, (0, 20)); row.paste(t5, (t4.width + 10, 20))
    ImageDraw.Draw(row).text((4, 4), f'{lab}: V4 editat | V5', fill=(255, 255, 0)); rows.append(row)
W = max(r.width for r in rows); Ht = sum(r.height for r in rows)
out = Image.new('RGB', (W, Ht), (30, 30, 30)); y = 0
for r2 in rows: out.paste(r2, (0, y)); y += r2.height
out.save('v5out/qa_zoom.png'); print(out.size)
