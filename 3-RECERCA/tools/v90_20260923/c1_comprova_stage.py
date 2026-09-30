"""c1 · Comprovació de V90_stage.psb abans del desament natiu (compost emulat, sense capes d'ajust): (1) cobertura a la caixa de la Lluna
(1 − Π(1 − α·màscara·opacitat) de les capes visibles per sota dels ajustos) ≥ 0,999; (2) canvis de pendent (derivada segona radial) a la vora
esquerra en polars, V88 contra V90, i la seva energia a DMIN−0,5..DMIN+7; (3) les marques de Pere a 4:1. Sortida: C1_COMPROVA.json,
LAMINA_C1_polars.png, LAMINA_C1_marques.png."""
from v90_comu import *
from psb69 import PSB
import cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v88_marques_pere_20260923'))
from vm_compost import comp, capa_box
claim(); GEO = json.loads((SORT / 'A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = GEO['cx'], GEO['cy'], GEO['R']
BX = (4780, 3230, 5980, 4330); x0, y0, x1, y1 = BX; h, w = y1 - y0, x1 - x0
P88 = PSB(str(ARREL / '1-PHOTOSHOP/V88.psb')); P90 = PSB(str(SORT / 'V90_stage.psb'))
def pila(p):
    ids = []
    for L in p.layers:
        if L['id'] in (239, 240, 241, 242, 243, 244): break
        if L['visible'] and L['right'] > L['left']: ids.append(L['id'])
    return ids
i88, i90 = pila(P88), pila(P90); log(f'pila V88 {i88}'); log(f'pila V90 {i90}')
C88, A88 = comp([capa_box(P88, i, BX) for i in i88], h, w); C90, A90 = comp([capa_box(P90, i, BX) for i in i90], h, w)
def lum(C): return 0.3 * C[..., 0] + 0.59 * C[..., 1] + 0.11 * C[..., 2]
yy, xx = np.mgrid[y0:y1, x0:x1]; d = np.hypot(xx - cx, yy - cy) - R
res = dict(cobertura_min_V88=float(A88[d > -40].min()), cobertura_min_V90=float(A90[d > -40].min()), px_V90_sota_0999=int((A90[d > -40] < 0.999).sum()))
Q = np.load(ARREL / '4-RESULTATS/v88_20260923/A3A_franja_un_instant.npz'); DMIN = Q['DMIN']; NBZ = len(DMIN)
T0, T1, DT = 95.0, 245.0, 0.1; D0_, D1_, DD = -4.0, 20.0, 0.1
tt = np.arange(T0, T1, DT); ddd = np.arange(D0_, D1_, DD); TT, DDg = np.meshgrid(np.radians(tt), ddd)
X = (cx + (R + DDg) * np.cos(TT) - x0).astype(np.float32); Y = (cy - (R + DDg) * np.sin(TT) - y0).astype(np.float32)
def pol(A): return cv2.remap(A.astype(np.float32), X, Y, cv2.INTER_LINEAR)
def d2(P): Ps = cv2.GaussianBlur(P, (0, 0), sigmaX=2, sigmaY=5); return np.gradient(np.gradient(Ps, axis=0), axis=0) / DD**2
p88, p90 = pol(lum(C88)), pol(lum(C90)); th_i = ((tt / 360) * NBZ).astype(int) % NBZ
mz = (DDg > DMIN[th_i][None, :] - 0.5) & (DDg < DMIN[th_i][None, :] + 7)
res['energia_curvatura_vora'] = dict(V88=float(np.sqrt(np.mean(d2(p88)[mz] ** 2))), V90=float(np.sqrt(np.mean(d2(p90)[mz] ** 2))))
far = (DDg > 12) & (DDg < 19); res['energia_curvatura_12_19px'] = dict(V88=float(np.sqrt(np.mean(d2(p88)[far] ** 2))), V90=float(np.sqrt(np.mean(d2(p90)[far] ** 2))))
desa_json('C1_COMPROVA.json', res); log(json.dumps(res))
F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15); FB = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 17)
def v(A, lo, hi): return np.uint8(np.clip((A - lo) / (hi - lo), 0, 1) * 255)
k = (DDg > 0.5) & (DDg < 15); lo, hi = np.percentile(p88[k], [1, 99])
pan = [('V88: canvis de pendent', v(-d2(p88), -0.02, 0.02)), ('V90: canvis de pendent', v(-d2(p90), -0.02, 0.02)), ('V88: lluminància', v(p88, lo, hi)), ('V90: lluminància', v(p90, lo, hi))]
hh, ww = p88.shape; zy = 3; S = Image.new('RGB', (ww, 40 + len(pan) * (hh * zy + 24)), 'white'); dr = ImageDraw.Draw(S)
dr.text((4, 6), 'Vora esquerra en polars, compost emulat sense capes d\'ajust: 95° → 245°; d −4..20 px (×3); vermell: d = 0', fill='black', font=FB)
for i, (et, img) in enumerate(pan):
    Y0 = 40 + i * (hh * zy + 24); pil = Image.fromarray(img).resize((ww, hh * zy), Image.NEAREST).convert('RGB'); di = ImageDraw.Draw(pil)
    di.line([(0, int((0 - D0_) / DD * zy)), (ww, int((0 - D0_) / DD * zy))], fill=(255, 0, 0))
    for az in range(100, 245, 10): xl = int((az - T0) / DT); di.line([(xl, 0), (xl, 8)], fill=(255, 255, 0)); di.text((xl + 2, 0), str(az), fill=(255, 255, 0), font=F)
    S.paste(pil, (0, Y0 + 22)); dr.text((4, Y0 + 3), et, fill='black', font=F)
S.save(SORT / 'LAMINA_C1_polars.png')
M = json.loads((ARREL / '4-RESULTATS/v88_marques_pere_20260923/MARQUES_V88.json').read_text()); llocs = [(g['nom'], cc) for g in M['grups_de_to'] for cc in g['components']]
cw, zf = 100, 4; S2 = Image.new('RGB', (2 * (cw * zf + 8), 36 + len(llocs) * (cw * zf + 22)), 'white'); d2_ = ImageDraw.Draw(S2)
d2_.text((6, 8), 'Marques a 4:1, compost emulat sense capes d\'ajust (mateix estirament per fila): V88 · V90', fill='black', font=FB)
for j, (nom, cc) in enumerate(llocs):
    az, dm = cc['azimut'][1], cc['d_limbe_px'][1]; t = np.radians(az); px_, py_ = cx + (R + dm) * np.cos(t) - x0, cy - (R + dm) * np.sin(t) - y0
    ax0, ay0 = int(px_ - cw / 2), int(py_ - cw / 2); lo_, hi_ = np.percentile(lum(C88[ay0:ay0 + cw, ax0:ax0 + cw]), [1, 99.5]); Yj = 36 + j * (cw * zf + 22)
    for i_, (Cx, et) in enumerate([(C88, 'V88'), (C90, 'V90')]):
        c = np.clip((Cx[ay0:ay0 + cw, ax0:ax0 + cw] - lo_) / (hi_ - lo_), 0, 1)
        S2.paste(Image.fromarray(np.uint8(c * 255)).resize((cw * zf, cw * zf), Image.LANCZOS), (i_ * (cw * zf + 8), Yj + 20)); d2_.text((i_ * (cw * zf + 8) + 3, Yj + 2), f'{et} · {az:.0f}° · d {dm:+.0f} px', fill='black', font=F)
S2.save(SORT / 'LAMINA_C1_marques.png'); log('fet')
# la Lluna sencera a 2:3 i quatre zones de control a 2:1 (V88 · V90), compost emulat
BL = (4600, 3000, 6150, 4550); hL, wL = BL[3] - BL[1], BL[2] - BL[0]
L88 = comp([capa_box(P88, i, BL) for i in i88], hL, wL)[0]; L90 = comp([capa_box(P90, i, BL) for i in i90], hL, wL)[0]
k = 1024; S3 = Image.new('RGB', (2 * (k + 8), k + 34), 'white'); d3 = ImageDraw.Draw(S3)
for i_, (Cx, et) in enumerate([(L88, 'V88'), (L90, 'V90')]):
    S3.paste(Image.fromarray(np.uint8(np.clip(Cx, 0, 1) * 255)).resize((k, k), Image.LANCZOS), (i_ * (k + 8), 32)); d3.text((i_ * (k + 8) + 4, 8), f'Lluna 2:3, emulat sense ajustos · {et}', fill='black', font=FB)
S3.save(SORT / 'LAMINA_C1_lluna.png')
cxl, cyl = cx - BL[0], cy - BL[1]; cw2, z2 = 160, 2; azs = [90, 0, 270, 180]
S4 = Image.new('RGB', (2 * (cw2 * z2 + 8), len(azs) * (cw2 * z2 + 22)), 'white'); d4 = ImageDraw.Draw(S4)
for j, az in enumerate(azs):
    t = np.radians(az); px_, py_ = cxl + (R + 40) * np.cos(t), cyl - (R + 40) * np.sin(t); ax0, ay0 = int(px_ - cw2 / 2), int(py_ - cw2 / 2)
    lo_, hi_ = np.percentile(lum(L88[ay0:ay0 + cw2, ax0:ax0 + cw2]), [1, 99.5])
    for i_, (Cx, et) in enumerate([(L88, 'V88'), (L90, 'V90')]):
        c = np.clip((Cx[ay0:ay0 + cw2, ax0:ax0 + cw2] - lo_) / (hi_ - lo_), 0, 1)
        S4.paste(Image.fromarray(np.uint8(c * 255)).resize((cw2 * z2, cw2 * z2), Image.LANCZOS), (i_ * (cw2 * z2 + 8), j * (cw2 * z2 + 22) + 20)); d4.text((i_ * (cw2 * z2 + 8) + 3, j * (cw2 * z2 + 22) + 2), f'{et} · {az}° (centre a 40 px del limbe)', fill='black', font=F)
S4.save(SORT / 'LAMINA_C1_control.png'); log('vistes de control fetes')
