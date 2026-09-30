"""c16 · Simulació (compost emulat, sense capes d'ajust; NO toca cap PSB): què passaria a les marques de l'esquerra si la Lluna mostrada tingués
l'alfa de l'INSTANT (el disc de 18,4 s, R 453) en lloc de l'actual (la 225 de Pere, allargada en horitzontal: la Lluna sumada al llarg del temps).
Alfa nova: a tots els azimuts, el perfil radial MITJÀ de l'alfa de Pere a dalt i a baix (60–120° i 240–300°), on no sobresurt; per tant, la mateixa
vora que Pere ja té allà. Màscares de la base (3) i dels filtres: la màscara de l'usuari continuada radialment cap endins × (1 − Lluna opaca nova),
com a la V86. Sortida: LAMINA_M16_simulacio_alfa_instant.png i SIMULACIO_ALFA.json (cobertura mínima)."""
from vm_comu import *
from psb69 import PSB
from vm_compost import comp, capa_box
import cv2
from PIL import Image, ImageDraw, ImageFont
claim()
BX = (4780, 3230, 5420, 4300); x0, y0, x1, y1 = BX; h, w = y1 - y0, x1 - x0
p = PSB(str(PSB_PERE)); vis = [l['id'] for l in p.layers if l['visible'] and l['right'] > l['left']][:vis_end] if False else None
vis = [l['id'] for l in p.layers if l['visible'] and l['right'] > l['left']]; vis = vis[:vis.index(224) + 1]
cx, cy, R = GEO['cx'], GEO['cy'], GEO['R']; yy, xx = np.mgrid[y0:y1, x0:x1]; d = np.hypot(xx - cx, yy - cy) - R; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
capes = {i: capa_box(p, i, BX) for i in vis}
# alfa actual de la 258 i perfil radial mitjà a dalt i a baix
a258 = p.channel_box(258, -1, BX).astype(np.float32) / 65535
Lf = p.layer(258); af, orgf = p.channel(258, -1); af = af.astype(np.float32) / 65535
yf, xf = np.mgrid[orgf[1]:orgf[1] + af.shape[0], orgf[0]:orgf[0] + af.shape[1]]; df = np.hypot(xf - cx, yf - cy) - R; tf = (np.degrees(np.arctan2(-(yf - cy), xf - cx)) + 360) % 360
selc = (((tf >= 60) & (tf <= 120)) | ((tf >= 240) & (tf <= 300))) & (np.abs(df) < 8); bins = np.arange(-8, 8.01, 0.25)
prof = np.array([np.median(af[selc & (np.abs(df - b) < 0.125)]) if (selc & (np.abs(df - b) < 0.125)).sum() > 10 else np.nan for b in bins])
prof = np.maximum.accumulate(prof[::-1])[::-1]        # monòton decreixent cap enfora
a_new = np.interp(d, bins, prof, left=1.0, right=0.0).astype(np.float32); a_new = np.where(d < -8, a258, a_new)   # interior intacte (més enllà de 8 px dins, la 258 tal qual)
op_old = a258 >= 0.999; op_new = a_new >= 0.999
res = dict(perfil_alfa_nou=dict(d=bins.tolist(), alfa=np.round(prof, 4).tolist()))
# màscares noves: la de l'usuari continuada cap endins des de fora de la Lluna opaca antiga, × (1 − opaca nova)
ang = np.radians(th)
def continua_mascara(mm):
    # per a cada píxel dins l'opaca antiga: el valor de la màscara al mateix azimut, 1 px fora de la vora de l'opaca antiga
    out = mm.copy(); edge = np.full(3600, np.nan); it = (th * 10).astype(int) % 3600
    dd_edge = np.zeros(3600)
    for k in range(3600):
        s = (it == k) & op_old
        dd_edge[k] = d[s].max() if s.any() else -50
    dd_edge = np.maximum.accumulate(np.r_[dd_edge, dd_edge])[3600:] * 0 + dd_edge
    dref = dd_edge[it] + 1.5; X = (cx + (R + dref) * np.cos(ang) - x0).astype(np.float32); Y = (cy - (R + dref) * np.sin(ang) - y0).astype(np.float32)
    val = cv2.remap(mm.astype(np.float32), X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return np.where(op_old, val, mm)
nous = {}
for i in vis:
    mode, F, a = capes[i]; L = p.layer(i)
    if i == 258: nous[i] = (mode, F, a_new * (L['opacity'] / 255)); continue
    if i in (3, 41, 42, 47, 49, 51, 45, 46, 55, 56) and L['mask'] is not None:
        m = p.channel_box(i, -2, BX, fill=65535 if L['mask']['background'] == 255 else 0).astype(np.float32) / 65535; al = p.channel_box(i, -1, BX).astype(np.float32) / 65535
        m2 = continua_mascara(m) * (1 - op_new); nous[i] = (mode, F, al * m2 * (L['opacity'] / 255))
    else: nous[i] = capes[i]
C0, a0 = comp([capes[i] for i in vis], h, w); C1, a1 = comp([nous[i] for i in vis], h, w)
res['cobertura_min_actual'] = float(a0[d > -30].min()); res['cobertura_min_simulada'] = float(a1[d > -30].min()); res['px_cobertura_simulada_sota_0999'] = int((a1 < 0.999).sum())
desa_json('SIMULACIO_ALFA.json', res); log(json.dumps({k: v for k, v in res.items() if k != 'perfil_alfa_nou'}))
np.savez_compressed(SORT / 'simulacio_alfa_instant.npz', caixa=np.array(BX), actual=np.round(C0 * 65535).astype(np.uint16), simulada=np.round(C1 * 65535).astype(np.uint16), a_new=np.round(a_new * 65535).astype(np.uint16))
try: F_ = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 14); FB = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 18)
except Exception: F_ = FB = ImageFont.load_default()
M = json.loads((SORT / 'MARQUES_V88.json').read_text()); llocs = [(g['nom'], cc) for g in M['grups_de_to'] for cc in g['components']]
def lum(C): return 0.3 * C[..., 0] + 0.59 * C[..., 1] + 0.11 * C[..., 2]
cw, zf = 100, 3; S = Image.new('RGB', (2 * (cw * zf + 8) + 10 + (w // 2) * 1 * 0, 40 + len(llocs) * (cw * zf + 22)), 'white'); dr = ImageDraw.Draw(S)
dr.text((6, 8), 'Compost emulat (sense capes d\'ajust), 3:1: alfa de la Lluna actual · alfa de l\'instant (simulació). Mateix estirament per fila', fill='black', font=FB)
for j, (nom, cc) in enumerate(llocs):
    az, dm = cc['azimut'][1], cc['d_limbe_px'][1]; t = np.radians(az); px_, py_ = cx + (R + dm) * np.cos(t) - x0, cy - (R + dm) * np.sin(t) - y0
    ax0, ay0 = int(px_ - cw / 2), int(py_ - cw / 2); lo, hi = np.percentile(lum(C0[ay0:ay0 + cw, ax0:ax0 + cw]), [1, 99.5]); Y0 = 40 + j * (cw * zf + 22)
    for i_, (C, et) in enumerate([(C0, 'actual'), (C1, 'alfa de l\'instant')]):
        c = np.clip((C[ay0:ay0 + cw, ax0:ax0 + cw] - lo) / (hi - lo), 0, 1)
        S.paste(Image.fromarray(np.uint8(c * 255)).resize((cw * zf, cw * zf), Image.LANCZOS), (i_ * (cw * zf + 8), Y0 + 20)); dr.text((i_ * (cw * zf + 8) + 3, Y0 + 2), f'{et} · {az:.0f}° · d {dm:+.0f} px', fill='black', font=F_)
S.save(SORT / 'LAMINA_M16_simulacio_alfa_instant.png')
# vista de conjunt de la vora esquerra (2:1)
BV = (4840 - x0, 3380 - y0, 5090 - x0, 4180 - y0); lo, hi = np.percentile(lum(C0[BV[1]:BV[3], BV[0]:BV[2]]), [1, 99.5])
S2 = Image.new('RGB', (2 * ((BV[2] - BV[0]) * 2 + 8), (BV[3] - BV[1]) * 2 + 34), 'white'); d2 = ImageDraw.Draw(S2)
for i_, (C, et) in enumerate([(C0, 'actual'), (C1, 'alfa de l\'instant (simulació)')]):
    c = np.clip((C[BV[1]:BV[3], BV[0]:BV[2]] - lo) / (hi - lo), 0, 1); im = Image.fromarray(np.uint8(c * 255)).resize(((BV[2] - BV[0]) * 2, (BV[3] - BV[1]) * 2), Image.LANCZOS)
    S2.paste(im, (i_ * ((BV[2] - BV[0]) * 2 + 8), 32)); d2.text((i_ * ((BV[2] - BV[0]) * 2 + 8) + 4, 8), 'Vora esquerra, 2:1 · ' + et, fill='black', font=FB)
S2.save(SORT / 'LAMINA_M17_vora_esquerra_simulada.png'); log('fet')
