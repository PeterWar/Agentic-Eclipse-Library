"""b4/b5 (V94) · Proves de fitxer contra la V93 i làmines del compost de Photoshop (V93 contra V94).
P2: capes que no són 55/56 idèntiques; P3: 55/56 RGB i alfa = calculats (±1), màscara = la de la V93; P4: on canvia el compost.
Làmines: llenç a 1/4 amb el quocient V94/V93 (l'ombra que ja no hi és), marques taronja a 6:1, línies de la V88 a 8:1, Lluna a 2:3."""
import sys, json, io, hashlib
from pathlib import Path
import numpy as np, cv2, tifffile
from PIL import Image, ImageCms, ImageDraw, ImageFont
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v94_20260924'
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917')); from psb69 import PSB
def sha(p):
    with open(p, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
p = PSB(str(ARREL / '1-PHOTOSHOP/V93.psb')); q = PSB(str(ARREL / '1-PHOTOSHOP/V94.psb')); NOU = {56: 'P05_WOW_bilateral', 55: 'P04_WOW'}
assert [L['id'] for L in q.layers] == [L['id'] for L in p.layers]; res = dict(P2={}, P3={}, props=[])
for L0 in p.layers:
    lid = L0['id']; L1 = q.layer(lid)
    for k in ('visible', 'opacity', 'blend', 'left', 'top', 'right', 'bottom', 'clipping', 'mask'):
        if L0[k] != L1[k]: res['props'].append([lid, k])
    if L0['right'] <= L0['left']: continue
    if lid in NOU:
        t = NOU[lid]; res['P3'][lid] = dict(rgb=int(np.abs(q.channel(lid, 0)[0].astype(np.int32) - np.load(SORT / f'wow/{t}_u16.npy').astype(np.int32)).max()),
                                             alfa=int(np.abs(q.channel(lid, -1)[0].astype(np.int32) - np.load(SORT / f'wow/{t}_alfa_u16.npy').astype(np.int32)).max()),
                                             mascara=int(np.abs(q.channel(lid, -2)[0].astype(np.int32) - p.channel(lid, -2)[0].astype(np.int32)).max()))
    else:
        mx = 0
        for c in L0['chans']:
            a0 = p.channel(lid, c)[0]
            if a0 is None or a0.size == 0: continue
            mx = max(mx, int(np.abs(a0.astype(np.int32) - q.channel(lid, c)[0].astype(np.int32)).max()))
        res['P2'][lid] = mx
res['P2_PASS'] = all(v == 0 for v in res['P2'].values()) and not res['props']; res['P3_PASS'] = all(v['rgb'] <= 1 and v['alfa'] <= 1 and v['mascara'] == 0 for v in res['P3'].values())
res['V94'] = dict(sha256=sha(ARREL / '1-PHOTOSHOP/V94.psb'), bytes=(ARREL / '1-PHOTOSHOP/V94.psb').stat().st_size, capes=len(q.layers))
print(json.dumps({k: res[k] for k in ('P2_PASS', 'P3_PASS', 'P3', 'props')}), flush=True)
C3 = p.composite()[..., :3]; C4 = q.composite()[..., :3]; W, H = 10551, 7506
red = lambda A: cv2.resize(A.astype(np.float32) / 65535, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
lum = lambda X: 0.2126 * X[..., 0] + 0.7152 * X[..., 1] + 0.0722 * X[..., 2]
Q3, Q4 = red(C3), red(C4); ratio = cv2.GaussianBlur(lum(Q4) / np.maximum(lum(Q3), 1e-3) - 1, (0, 0), 20)
mk = cv2.resize(np.load(ARREL / '4-RESULTATS/v93_20260924/marques_FiltreWOW_Pere.npz')['negre'].astype(np.float32), (W // 4, H // 4), interpolation=cv2.INTER_AREA) > 0
yy, xx = np.mgrid[:H // 4, :W // 4]; dq = np.hypot(xx - 5376 / 4, yy - 3776 / 4) * 4 - 453; ok = lum(Q3) > 0.02
res['compost_V94_sobre_V93'] = dict(marques_negres=round(float(ratio[mk & ok].mean()), 4), d_150_600=round(float(ratio[ok & (dq > 150) & (dq < 600)].mean()), 4), d_800_1700=round(float(ratio[ok & (dq > 800) & (dq < 1700)].mean()), 4), d_2500_4000=round(float(ratio[ok & (dq > 2500) & (dq < 4000)].mean()), 4))
print(json.dumps(res['compost_V94_sobre_V93']), flush=True)
icc = tifffile.TiffFile(SORT / 'vistes/V94_lluna.tif').pages[0].tags['InterColorProfile'].value
TR = ImageCms.buildTransform(ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile('sRGB'), 'RGB', 'RGB'); im = lambda A: ImageCms.applyTransform(Image.fromarray(np.uint8(np.clip(A * 255, 0, 255))), TR)
FB = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 20); F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15)
S1 = Image.new('RGB', (3 * 1100 + 16, 783 + 36), 'white'); d1 = ImageDraw.Draw(S1)
for i, (img, et) in enumerate([(im(Q3), 'V93'), (im(Q4), 'V94'), (Image.fromarray(np.uint8(np.clip((ratio + 0.06) / 0.12, 0, 1) * 255)), 'V94/V93 − 1 (gris = igual, clar = V94 més clara; ±6 %)')]):
    S1.paste(img.resize((1100, 783), Image.LANCZOS), (i * 1108, 34)); d1.text((i * 1108 + 6, 6), et, fill='black', font=FB)
S1.save(SORT / 'LAMINA_V94_1_llenc_i_ombra.png')
B = (4600, 3000); cx, cy, R = 5375.787, 3775.977, 452.979; L3 = C3[3000:4550, 4600:6150].astype(np.float32) / 65535; L4 = C4[3000:4550, 4600:6150].astype(np.float32) / 65535; del C3, C4
def lamina(nom, titol, files, w=60, zf=6):
    S = Image.new('RGB', (2 * (w * zf + 8), 40 + len(files) * (w * zf + 24)), 'white'); d = ImageDraw.Draw(S); d.text((6, 8), titol, fill='black', font=FB)
    for j, (az, dm) in enumerate(files):
        t = np.radians(az); px, py = cx + (R + dm) * np.cos(t) - B[0], cy - (R + dm) * np.sin(t) - B[1]; x0, y0 = int(px - w / 2), int(py - w / 2); Y0 = 40 + j * (w * zf + 24)
        for i, (A, v) in enumerate(((L3, 'V93'), (L4, 'V94'))): S.paste(im(A[y0:y0 + w, x0:x0 + w]).resize((w * zf, w * zf), Image.LANCZOS), (i * (w * zf + 8), Y0 + 20)); d.text((i * (w * zf + 8) + 3, Y0 + 2), f'{v} · {az:.0f}°', fill='black', font=F)
    S.save(SORT / nom)
lamina('LAMINA_V94_2_taronja.png', 'Marques taronja (vora sense textura): V93 contra V94, compost de Photoshop, 6:1', [(70, 5), (85, 5), (215, 5), (240, 5), (335, 5), (345, 5)])
lamina('LAMINA_V94_3_linies_V88.png', 'Línies de la V88 (no han de tornar): V93 contra V94, compost de Photoshop, 8:1', [(112, 5), (136, 6), (211, 5), (219, 6), (223, 7)], w=44, zf=8)
S4 = Image.new('RGB', (2 * 1032, 1024 + 36), 'white'); d4 = ImageDraw.Draw(S4)
for i, (A, v) in enumerate(((L3, 'V93'), (L4, 'V94'))): S4.paste(im(A).resize((1024, 1024), Image.LANCZOS), (i * 1032, 34)); d4.text((i * 1032 + 6, 6), 'Lluna 2:3 · ' + v, fill='black', font=FB)
S4.save(SORT / 'LAMINA_V94_4_lluna.png'); (SORT / 'B4_QA.json').write_text(json.dumps(res, ensure_ascii=False, indent=2) + '\n'); print('fet')
