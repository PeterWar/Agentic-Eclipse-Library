"""c4 · Les marques marrons als renders natius de Photoshop (c3): quocient de lluminància marca / corona del costat (mateixa distància, azimuts veïns)
a cada variant de visibilitat, i vista del llenç amb les marques perfilades. Sortida: C4_MARRO_NATIU.json, LAMINA_C4_marro.png."""
from v93_comu import *
import cv2, tifffile, io
from PIL import Image, ImageCms, ImageDraw, ImageFont
claim(); RD = SORT / 'renders'; F4 = W / 2638.0
z = np.load(SORT / 'marques_v92_classes.npz'); org = z['origin']
def a_quart(M):
    full = np.zeros((H, W), np.float32); full[org[1]:org[1] + M.shape[0], org[0]:org[0] + M.shape[1]] = M
    im0 = tifffile.imread(RD / 'V0_tal_com_esta_quart.tif'); return cv2.resize(full, (im0.shape[1], im0.shape[0]), interpolation=cv2.INTER_AREA) > 0.3
Mb = a_quart(z['to_30_40']); h4, w4 = Mb.shape; cx, cy, R = GEO['cx'] / F4, GEO['cy'] / F4, GEO['R'] / F4
yy, xx = np.mgrid[:h4, :w4]; d = (np.hypot(xx - cx, yy - cy) - R) * F4; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
n, lab = cv2.connectedComponents(cv2.dilate(Mb.astype(np.uint8), np.ones((5, 5), np.uint8))); comps = []; dil = cv2.dilate(Mb.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
for k in range(1, n):
    m = (lab == k) & Mb
    if m.sum() < 30: continue
    a0, a1 = np.percentile(th[m], [1, 99]); d0, d1 = np.percentile(d[m], [5, 95]); dl = max(3.0, 0.6 * max(a1 - a0, 2))
    nb = (d >= d0) & (d <= d1) & ~dil & ((((th - a0) % 360) > 360 - dl) | (((th - a1) % 360) < dl))
    # també: anell interior i exterior a la mateixa franja d'azimut (per si la marca és un graó radial)
    ins = (th >= a0) & (th <= a1) & (d >= d0 - 0.25 * (d1 - d0) - 150) & (d < d0) & ~dil; ext = (th >= a0) & (th <= a1) & (d > d1) & (d <= d1 + 0.25 * (d1 - d0) + 150) & ~dil
    comps.append((m, nb, ins, ext, dict(azimut=[round(float(a0), 1), round(float(a1), 1)], d=[round(float(d0)), round(float(d1))])))
lum = lambda C: 0.2126 * C[..., 0] + 0.7152 * C[..., 1] + 0.0722 * C[..., 2]
rep = {'components': [c[4] for c in comps], 'variants': {}}
for f in sorted(RD.glob('V*_quart.tif')):
    C = tifffile.imread(f)[..., :3].astype(np.float32) / 65535; Y = lum(C)
    rep['variants'][f.stem] = [dict(costats=round(float(Y[m].mean() / Y[nb].mean()), 4), dins=round(float(Y[m].mean() / Y[i_].mean()), 4) if i_.any() else None,
                                    fora=round(float(Y[m].mean() / Y[e_].mean()), 4) if e_.any() else None) for m, nb, i_, e_, _ in comps]
    log(f.stem + ' ' + json.dumps([r['costats'] for r in rep['variants'][f.stem]]))
desa_json('C4_MARRO_NATIU.json', rep)
icc = tifffile.TiffFile(RD / 'V0_tal_com_esta_quart.tif').pages[0].tags['InterColorProfile'].value
TR = ImageCms.buildTransform(ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile('sRGB'), 'RGB', 'RGB')
C0 = tifffile.imread(RD / 'V0_tal_com_esta_quart.tif')[..., :3]; img = np.asarray(ImageCms.applyTransform(Image.fromarray(np.uint8(C0 / 257)), TR)).copy()
vora = cv2.dilate(Mb.astype(np.uint8), np.ones((3, 3), np.uint8)) & ~Mb.astype(np.uint8); img[vora > 0] = (0, 255, 255)
Image.fromarray(img).save(SORT / 'LAMINA_C4_marro.png'); log('fet')
