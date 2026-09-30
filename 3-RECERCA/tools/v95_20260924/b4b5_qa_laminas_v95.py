"""b4/b5 (V95) · Proves de fitxer contra la V94 i làmines (V94 contra V95).
P2: capes que no són 55/56 idèntiques i propietats iguals; P3: 55/56 RGB i alfa = calculats (±1), màscara = la de la V94 (0).
Làmines: (1) el FILTRE a les marques de Pere de WOW.psb (56 i 55, ràster × alfa sobre gris, contrast ×4, 4:1); (2) NIVELL de la 56 (σ 6 px, ×8);
(3) compost de Photoshop a la vora (marques vermelles) 6:1; (4) línies de la V88 8:1; (5) Lluna 2:3; (6) llenç a 1/4 i quocient V95/V94."""
import sys, json, io, hashlib
from pathlib import Path
import numpy as np, cv2, tifffile
from PIL import Image, ImageCms, ImageDraw, ImageFont
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v95_20260924'
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917')); from psb69 import PSB
def sha(p):
    with open(p, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
p = PSB(str(ARREL / '1-PHOTOSHOP/V94.psb')); q = PSB(str(ARREL / '1-PHOTOSHOP/V95.psb')); NOU = {56: 'P05_WOW_bilateral', 55: 'P04_WOW'}
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
res['noms'] = {lid: q.layer(lid)['name'] for lid in NOU}
res['V95'] = dict(sha256=sha(ARREL / '1-PHOTOSHOP/V95.psb'), bytes=(ARREL / '1-PHOTOSHOP/V95.psb').stat().st_size, capes=len(q.layers))
print(json.dumps({k: res[k] for k in ('P2_PASS', 'P3_PASS', 'P3', 'props', 'noms')}, ensure_ascii=False), flush=True)
W, H = 10551, 7506; cx, cy, R = 5375.787, 3775.977, 452.979
FB = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 20); F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15)
# ---- (1) i (2): el filtre a les marques de Pere
Z = np.load(ARREL / '4-RESULTATS/wow_marques_pere_20260924/marques.npz'); COL = {'to_350_360': (255, 0, 40), 'to_280_290': (190, 0, 255), 'to_100_110': (60, 230, 20), 'to_120_130': (20, 200, 60)}
def marca(lid_m, nom, y0c, x0c, n):
    k = f'{lid_m}_{nom}'
    if k not in Z.files: return None
    mm = Z[k]; oy, ox = int(Z[f'{lid_m}_origen'][1]), int(Z[f'{lid_m}_origen'][0]); out = np.zeros((n, n), bool)
    ys0, xs0 = max(y0c, oy), max(x0c, ox); ys1, xs1 = min(y0c + n, oy + mm.shape[0]), min(x0c + n, ox + mm.shape[1])
    if ys1 > ys0 and xs1 > xs0: out[ys0 - y0c:ys1 - y0c, xs0 - x0c:xs1 - x0c] = mm[ys0 - oy:ys1 - oy, xs0 - ox:xs1 - ox]
    return out
LLOCS = [('vermella 0°', 0, 4), ('vermella 300°', 300, 4), ('vermella 211°', 211, 8), ('vermella 181°', 181, 8), ('lila 352°', 352, 106), ('lila 282°', 282, 105),
         ('lila 118°', 118, 34), ('lila 63°', 63, 19), ('verda 215°', 215, 45), ('verda 155°', 155, 21), ('verda 59°', 59, 50), ('verda 250°', 250, 22)]
n94 = {}; n95 = {}
for lid, lm in ((56, 272), (55, 270)):
    X94 = p.channel(lid, 0)[0].astype(np.float32) / 65535; A94 = p.channel(lid, -1)[0].astype(np.float32) / 65535
    X95 = q.channel(lid, 0)[0].astype(np.float32) / 65535; A95 = q.channel(lid, -1)[0].astype(np.float32) / 65535
    V94 = 0.5 + A94 * (X94 - 0.5); V95 = 0.5 + A95 * (X95 - 0.5); del X94, X95
    Wt, Z4 = 90, 4; tiles = []
    for nom, az, dd in LLOCS:
        px = cx + (R + dd) * np.cos(np.radians(az)); py = cy - (R + dd) * np.sin(np.radians(az)); xa, ya = int(px) - Wt // 2, int(py) - Wt // 2; row = []
        for X in (V94, V95):
            c = np.clip(0.5 + 4 * (X[ya:ya + Wt, xa:xa + Wt] - 0.5), 0, 1); im = cv2.resize(np.stack([np.uint8(c * 255)] * 3, -1), (Wt * Z4, Wt * Z4), interpolation=cv2.INTER_NEAREST)
            for k, col in COL.items():
                mb = marca(lm, k, ya, xa, Wt)
                if mb is None: continue
                mb = cv2.resize(mb.astype(np.uint8), (Wt * Z4, Wt * Z4), interpolation=cv2.INTER_NEAREST); v = cv2.dilate(mb, np.ones((3, 3), np.uint8)) - mb; im[v > 0] = col
            row.append(im)
        tiles.append((nom, np.concatenate([row[0], np.full((Wt * Z4, 8, 3), 255, np.uint8), row[1]], 1)))
    tw = 2 * Wt * Z4 + 8; th = Wt * Z4 + 30; out = Image.new('RGB', (2 * tw + 20, 6 * th + 40), 'white'); dr = ImageDraw.Draw(out)
    dr.text((6, 6), f'Capa {lid} ({NOU[lid]}) a les marques de Pere (capa {lm} de WOW.psb) · esquerra V94 · dreta V95 · ràster × alfa sobre gris, contrast ×4, 4:1', fill='black', font=FB)
    for i, (nom, t) in enumerate(tiles):
        X0, Y0 = (i % 2) * (tw + 20), 40 + (i // 2) * th; dr.text((X0 + 4, Y0 + 6), nom, fill='black', font=F); out.paste(Image.fromarray(t), (X0, Y0 + 28))
    out.save(SORT / f'LAMINA_V95_1_marques_capa_{lid}.png')
    # nivell
    Hh = 800; y0c, x0c = int(cy) - Hh, int(cx) - Hh; pan = []
    for et, X, A in (('V94', V94, A94), ('V95', V95, A95)):
        Xc = X[y0c:y0c + 2 * Hh, x0c:x0c + 2 * Hh]; Ac = (A[y0c:y0c + 2 * Hh, x0c:x0c + 2 * Hh] > 0.5).astype(np.float32)
        L = np.where(Ac > 0, cv2.GaussianBlur(Xc * Ac, (0, 0), 6) / np.maximum(cv2.GaussianBlur(Ac, (0, 0), 6), 1e-6), 0.5)
        im = np.stack([np.uint8(np.clip(0.5 + 8 * (L - 0.5), 0, 1) * 255)] * 3, -1)
        for k, col in COL.items():
            mb = marca(lm, k, y0c, x0c, 2 * Hh)
            if mb is None: continue
            mb = mb.astype(np.uint8); v = cv2.dilate(mb, np.ones((5, 5), np.uint8)) - mb; im[v > 0] = col
        pan.append((et, cv2.resize(im, (Hh, Hh), interpolation=cv2.INTER_AREA)))
        prof = {}
        yy, xx = np.mgrid[y0c:y0c + 2 * Hh, x0c:x0c + 2 * Hh]; d = np.hypot(xx - cx, yy - cy) - R; thg = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
        for s0, s1 in ((345, 360), (276, 288), (140, 170), (200, 230), (60, 90), (0, 360)):
            sel = (thg >= s0) & (thg < s1) & (Ac > 0); prof[f'{s0}-{s1}'] = [round(float(Xc[sel & (np.abs(d - dd) < 0.5)].mean()), 3) for dd in (2, 5, 10, 20, 40, 60, 90, 110, 130, 160, 200, 300)]
        res.setdefault('perfil_nivell', {})[f'{lid}_{et}'] = prof
    S2 = Image.new('RGB', (2 * Hh + 16, Hh + 34), 'white'); d2 = ImageDraw.Draw(S2)
    for i, (et, im) in enumerate(pan): d2.text((i * (Hh + 16) + 6, 6), f'Capa {lid} · {et} · NIVELL (pas baix σ 6 px, contrast ×8) · 1:2', fill='black', font=FB); S2.paste(Image.fromarray(im), (i * (Hh + 16), 34))
    S2.save(SORT / f'LAMINA_V95_2_nivell_capa_{lid}.png'); del V94, V95, A94, A95
print(json.dumps(res['perfil_nivell'], ensure_ascii=False), flush=True)
# ---- (3)–(6): compost de Photoshop
C4 = p.composite()[..., :3]; C5 = q.composite()[..., :3]
red = lambda A: cv2.resize(A.astype(np.float32) / 65535, (W // 4, H // 4), interpolation=cv2.INTER_AREA); lum = lambda X: 0.2126 * X[..., 0] + 0.7152 * X[..., 1] + 0.0722 * X[..., 2]
Q4, Q5 = red(C4), red(C5); ok = lum(Q4) > 0.02; okf = ok.astype(np.float32)   # quocient suavitzat NOMÉS amb píxels amb imatge (les zones negres del llenç el falsejaven)
ratio = cv2.GaussianBlur(np.where(ok, lum(Q5) / np.maximum(lum(Q4), 1e-3) - 1, 0).astype(np.float32), (0, 0), 20) / np.maximum(cv2.GaussianBlur(okf, (0, 0), 20), 1e-6)
yy, xx = np.mgrid[:H // 4, :W // 4]; dq = np.hypot(xx - cx / 4, yy - cy / 4) * 4 - R
mk = cv2.resize(np.load(ARREL / '4-RESULTATS/v93_20260924/marques_FiltreWOW_Pere.npz')['negre'].astype(np.float32), (W // 4, H // 4), interpolation=cv2.INTER_AREA) > 0
res['compost_V95_sobre_V94'] = {'ombra_quadrada (marques negres de FiltreWOW)': round(float(ratio[mk & ok].mean()), 4), 'd_0_150': round(float(ratio[ok & (dq > 0) & (dq < 150)].mean()), 4),
                                'd_150_600': round(float(ratio[ok & (dq > 150) & (dq < 600)].mean()), 4), 'd_800_1700': round(float(ratio[ok & (dq > 800) & (dq < 1700)].mean()), 4),
                                'd_2500_4000': round(float(ratio[ok & (dq > 2500) & (dq < 4000)].mean()), 4), 'max_abs_fora_150': round(float(np.abs(ratio[ok & (dq > 150)]).max()), 4), 'dif_lluminancia_quart_p99': round(float(np.percentile(np.abs(lum(Q5) - lum(Q4))[ok], 99)), 5)}
print(json.dumps(res['compost_V95_sobre_V94'], ensure_ascii=False), flush=True)
icc = tifffile.TiffFile(SORT / 'vistes/V95_lluna.tif').pages[0].tags['InterColorProfile'].value
TR = ImageCms.buildTransform(ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile('sRGB'), 'RGB', 'RGB'); im = lambda A: ImageCms.applyTransform(Image.fromarray(np.uint8(np.clip(A * 255, 0, 255))), TR)
S6 = Image.new('RGB', (3 * 1100 + 16, 783 + 36), 'white'); d6 = ImageDraw.Draw(S6)
for i, (img, et) in enumerate([(im(Q4), 'V94'), (im(Q5), 'V95'), (Image.fromarray(np.uint8(np.clip((ratio + 0.06) / 0.12, 0, 1) * 255)), 'V95/V94 − 1 (gris = igual; ±6 %)')]):
    S6.paste(img.resize((1100, 783), Image.LANCZOS), (i * 1108, 34)); d6.text((i * 1108 + 6, 6), et, fill='black', font=FB)
S6.save(SORT / 'LAMINA_V95_6_llenc_i_quocient.png')
B = (4600, 3000); L4 = C4[3000:4550, 4600:6150].astype(np.float32) / 65535; L5 = C5[3000:4550, 4600:6150].astype(np.float32) / 65535; del C4, C5
def lamina(nom, titol, files, w=60, zf=6):
    S = Image.new('RGB', (2 * (w * zf + 8), 40 + len(files) * (w * zf + 24)), 'white'); d = ImageDraw.Draw(S); d.text((6, 8), titol, fill='black', font=FB)
    for j, (az, dm) in enumerate(files):
        t = np.radians(az); px, py = cx + (R + dm) * np.cos(t) - B[0], cy - (R + dm) * np.sin(t) - B[1]; x0, y0 = int(px - w / 2), int(py - w / 2); Y0 = 40 + j * (w * zf + 24)
        for i, (A, v) in enumerate(((L4, 'V94'), (L5, 'V95'))): S.paste(im(A[y0:y0 + w, x0:x0 + w]).resize((w * zf, w * zf), Image.LANCZOS), (i * (w * zf + 8), Y0 + 20)); d.text((i * (w * zf + 8) + 3, Y0 + 2), f'{v} · {az:.0f}° · d {dm} px', fill='black', font=F)
    S.save(SORT / nom)
lamina('LAMINA_V95_3_compost_vora.png', 'La vora (marques vermelles): V94 contra V95, compost de Photoshop, 6:1', [(0, 5), (300, 5), (211, 8), (181, 8), (63, 10), (250, 10)])
lamina('LAMINA_V95_4_linies_V88.png', 'Línies de la V88 (no han de tornar): V94 contra V95, compost de Photoshop, 8:1', [(112, 5), (136, 6), (211, 5), (219, 6), (223, 7)], w=44, zf=8)
lamina('LAMINA_V95_7_compost_liles.png', 'Marques liles: V94 contra V95, compost de Photoshop, 3:1', [(352, 106), (282, 105), (118, 34)], w=120, zf=3)
S5 = Image.new('RGB', (2 * 1032, 1024 + 36), 'white'); d5 = ImageDraw.Draw(S5)
for i, (A, v) in enumerate(((L4, 'V94'), (L5, 'V95'))): S5.paste(im(A).resize((1024, 1024), Image.LANCZOS), (i * 1032, 34)); d5.text((i * 1032 + 6, 6), 'Lluna 2:3 · ' + v, fill='black', font=FB)
S5.save(SORT / 'LAMINA_V95_5_lluna.png'); (SORT / 'B4_QA.json').write_text(json.dumps(res, ensure_ascii=False, indent=2) + '\n'); print('fet')
