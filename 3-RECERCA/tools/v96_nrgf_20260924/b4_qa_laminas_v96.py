"""b4 (V96) · Proves de fitxer contra la V95 i làmines. P2: totes les capes menys la 41, idèntiques, i propietats iguals; P3: 41 RGB = calculat (±1),
alfa i màscara = V95 (0). Làmines: (1) la 41 a les marques de Pere (Artefactes_V95, capa 277) 5:1, V95 contra V96; (2) compost de Photoshop a la vora 6:1;
(3) Lluna 2:3; (4) llenç a 1/4 i quocient V96/V95 (suavitzat només amb imatge)."""
import sys, json, io, hashlib
from pathlib import Path
import numpy as np, cv2, tifffile
from PIL import Image, ImageCms, ImageDraw, ImageFont
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v96_nrgf_20260924'
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917')); from psb69 import PSB
def sha(p_):
    with open(p_, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
p = PSB(str(ARREL / '1-PHOTOSHOP/V95.psb')); q = PSB(str(ARREL / '1-PHOTOSHOP/V96.psb')); res = dict(P2={}, props=[])
assert [L['id'] for L in q.layers] == [L['id'] for L in p.layers]
for L0 in p.layers:
    lid = L0['id']; L1 = q.layer(lid)
    for k in ('visible', 'opacity', 'blend', 'left', 'top', 'right', 'bottom', 'clipping', 'mask'):
        if L0[k] != L1[k]: res['props'].append([lid, k])
    if L0['right'] <= L0['left'] or lid == 41: continue
    mx = 0
    for c in L0['chans']:
        a0 = p.channel(lid, c)[0]
        if a0 is None or a0.size == 0: continue
        mx = max(mx, int(np.abs(a0.astype(np.int32) - q.channel(lid, c)[0].astype(np.int32)).max()))
    res['P2'][lid] = mx
nou = np.load(SORT / 'P01_NRGF_V96_u16.npy')
res['P3'] = dict(rgb=max(int(np.abs(q.channel(41, c)[0].astype(np.int32) - nou.astype(np.int32)).max()) for c in range(3)), alfa=int(np.abs(q.channel(41, -1)[0].astype(np.int32) - p.channel(41, -1)[0].astype(np.int32)).max()),
                 mascara=int(np.abs(q.channel(41, -2)[0].astype(np.int32) - p.channel(41, -2)[0].astype(np.int32)).max()), nom=q.layer(41)['name'])
res['P2_PASS'] = all(v == 0 for v in res['P2'].values()) and not res['props']; res['P3_PASS'] = res['P3']['rgb'] <= 1 and res['P3']['alfa'] == 0 and res['P3']['mascara'] == 0
res['V96'] = dict(sha256=sha(ARREL / '1-PHOTOSHOP/V96.psb'), bytes=(ARREL / '1-PHOTOSHOP/V96.psb').stat().st_size, capes=len(q.layers))
print(json.dumps({k: res[k] for k in ('P2_PASS', 'P3_PASS', 'P3', 'props')}, ensure_ascii=False), flush=True)
W, H = 10551, 7506; cx, cy, R = 5375.787, 3775.977, 452.979; CX, CY = 5361.768111973117, 3775.747534140857
FB = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 20); F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15)
# (1) la 41 a les marques de Pere
B = 700; y0, x0 = int(cy) - B, int(cx) - B; sl = (slice(y0, y0 + 2 * B), slice(x0, x0 + 2 * B))
X5 = p.channel(41, 0)[0][sl].astype(np.float32) / 65535; X6 = q.channel(41, 0)[0][sl].astype(np.float32) / 65535
Z = np.load(ARREL / '4-RESULTATS/artefactes_v95_pere_20260924/marques.npz'); mk = np.zeros((H, W), bool)
for k in Z.files:
    if k.startswith('277_') and not k.endswith('origen'): g = Z[k]; ox, oy = Z['277_origen']; mk[oy:oy + g.shape[0], ox:ox + g.shape[1]] |= g
mk = mk[sl]; yy, xx = np.mgrid[y0:y0 + 2 * B, x0:x0 + 2 * B]; d = np.hypot(xx - cx, yy - cy) - R; circ = np.abs(np.hypot(xx - CX, yy - CY) - 469) < 0.7; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
res['perfil_41'] = {nom: {f'{a0}-{a1}': [round(float(X[(th >= a0) & (th < a1) & (np.abs(d - dd) < 0.5)].mean()), 3) for dd in (-2, 0, 1, 2, 4, 6, 8, 10, 12, 15, 20, 30, 50)] for a0, a1 in ((195, 295), (52, 108), (300, 360), (130, 190))} for nom, X in (('V95', X5), ('V96', X6))}
LL = [(245, 8), (270, 8), (85, 8), (60, 8), (215, 8), (160, 8), (330, 6), (20, 6)]; w, zf = 64, 5; Wt = w * zf
S1 = Image.new('RGB', (2 * (Wt + 8), len(LL) * (Wt + 24) + 36), 'white'); d1 = ImageDraw.Draw(S1); d1.text((6, 8), 'Capa 41 P01 NRGF 5:1 · V95 contra V96 · vermell limbe · blau cercle r=469 del Sol · taronja marques de Pere', fill='black', font=F)
for j, (az, dd) in enumerate(LL):
    px = int(cx + (R + dd) * np.cos(np.radians(az))) - x0; py = int(cy - (R + dd) * np.sin(np.radians(az))) - y0; lo, hi = np.percentile(X5[py - w // 2:py + w // 2, px - w // 2:px + w // 2], (2, 98))
    for i, X in enumerate((X5, X6)):
        im = cv2.resize(np.stack([np.uint8(np.clip((X[py - w // 2:py + w // 2, px - w // 2:px + w // 2] - lo) / max(hi - lo, 1e-6), 0, 1) * 255)] * 3, -1), (Wt, Wt), interpolation=cv2.INTER_NEAREST)
        for Mm, col in ((d >= 0, (255, 0, 0)), (mk, (255, 120, 0))):
            s = cv2.resize(Mm[py - w // 2:py + w // 2, px - w // 2:px + w // 2].astype(np.uint8), (Wt, Wt), interpolation=cv2.INTER_NEAREST); im[(cv2.dilate(s, np.ones((3, 3), np.uint8)) - cv2.erode(s, np.ones((3, 3), np.uint8))) > 0] = col
        s = cv2.resize(circ[py - w // 2:py + w // 2, px - w // 2:px + w // 2].astype(np.uint8), (Wt, Wt), interpolation=cv2.INTER_NEAREST); im[s > 0] = (0, 200, 255)
        S1.paste(Image.fromarray(im), (i * (Wt + 8), 36 + j * (Wt + 24) + 20)); d1.text((i * (Wt + 8) + 4, 36 + j * (Wt + 24) + 2), f'{az}° · {("V95", "V96")[i]}', fill='black', font=F)
S1.save(SORT / 'LAMINA_V96_1_capa41_marques.png')
# (2)–(4) compost de Photoshop
# compost: les VISTES renderitzades pel Photoshop (el compost fusionat desat pot sortir malmès; vegeu p6)
V5 = ARREL / '4-RESULTATS/v95_20260924/vistes'; V6 = SORT / 'vistes'
icc = tifffile.TiffFile(SORT / 'vistes/V96_lluna.tif').pages[0].tags['InterColorProfile'].value
TR = ImageCms.buildTransform(ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile('sRGB'), 'RGB', 'RGB'); im_ = lambda A: ImageCms.applyTransform(Image.fromarray(np.uint8(np.clip(A * 255, 0, 255))), TR)
L5 = tifffile.imread(V5 / 'V95_lluna.tif').astype(np.float32) / 65535; L6 = tifffile.imread(V6 / 'V96_lluna.tif').astype(np.float32) / 65535; Bx = (4600, 3000)
lum = lambda C: 0.2126 * C[..., 0] + 0.7152 * C[..., 1] + 0.0722 * C[..., 2]
yb, xb = np.mgrid[3000:4550, 4600:6150]; db = np.hypot(xb - cx, yb - cy) - R; tb = (np.degrees(np.arctan2(-(yb - cy), xb - cx)) + 360) % 360; rat = lum(L6) / np.maximum(lum(L5), 1e-4) - 1
res['compost_V96_sobre_V95_per_d'] = {f'{a0}-{a1}': [round(float(rat[(tb >= a0) & (tb < a1) & (np.abs(db - dd) < 0.25)].mean()) * 100, 2) for dd in (-1, 0, 1, 2, 3, 6, 10, 15, 20, 40)] for a0, a1 in ((0, 360), (195, 295), (52, 108), (300, 360), (130, 190))}
S2 = Image.new('RGB', (2 * (60 * 6 + 8), len(LL) * (60 * 6 + 24) + 36), 'white'); d2 = ImageDraw.Draw(S2); d2.text((6, 8), 'Compost de Photoshop a la vora, 6:1 · V95 contra V96', fill='black', font=FB)
for j, (az, dd) in enumerate(LL):
    t_ = np.radians(az); px, py = cx + (R + dd) * np.cos(t_) - Bx[0], cy - (R + dd) * np.sin(t_) - Bx[1]; xa, ya = int(px - 30), int(py - 30)
    for i, (A, v) in enumerate(((L5, 'V95'), (L6, 'V96'))): S2.paste(im_(A[ya:ya + 60, xa:xa + 60]).resize((360, 360), Image.NEAREST), (i * 368, 36 + j * 384 + 20)); d2.text((i * 368 + 4, 36 + j * 384 + 2), f'{v} · {az}°', fill='black', font=F)
S2.save(SORT / 'LAMINA_V96_2_compost_vora.png')
S3 = Image.new('RGB', (2 * 1032, 1024 + 36), 'white'); d3 = ImageDraw.Draw(S3)
for i, (A, v) in enumerate(((L5, 'V95'), (L6, 'V96'))): S3.paste(im_(A).resize((1024, 1024), Image.LANCZOS), (i * 1032, 34)); d3.text((i * 1032 + 6, 6), 'Lluna 2:3 · ' + v, fill='black', font=FB)
S3.save(SORT / 'LAMINA_V96_3_lluna.png')
Q5 = tifffile.imread(V5 / 'V95_llenc_sencer.tif').astype(np.float32) / 65535; Q6 = tifffile.imread(V6 / 'V96_llenc_sencer.tif').astype(np.float32) / 65535; fq = W / Q5.shape[1]; ok = lum(Q5) > 0.02; okf = ok.astype(np.float32)
ratio = cv2.GaussianBlur(np.where(ok, lum(Q6) / np.maximum(lum(Q5), 1e-3) - 1, 0).astype(np.float32), (0, 0), 20) / np.maximum(cv2.GaussianBlur(okf, (0, 0), 20), 1e-6)
yq, xq = np.mgrid[:Q5.shape[0], :Q5.shape[1]]; dq = np.hypot(xq - cx / fq, yq - cy / fq) * fq - R
res['compost_V96_sobre_V95'] = dict(max_abs_fora_150px=round(float(np.abs(ratio[ok & (dq > 150)]).max()), 4), d_150_600=round(float(ratio[ok & (dq > 150) & (dq < 600)].mean()), 5), dif_lluminancia_quart_p99_fora_100=round(float(np.percentile(np.abs(lum(Q6) - lum(Q5))[ok & (dq > 150)], 99)), 6))
print(json.dumps(res['compost_V96_sobre_V95'], ensure_ascii=False)); print(json.dumps(res['compost_V96_sobre_V95_per_d'], ensure_ascii=False))
(SORT / 'B4_QA.json').write_text(json.dumps(res, ensure_ascii=False, indent=2) + '\n'); print('fet')
