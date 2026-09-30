"""c11 · Restes de màscares a la zona de l'Earthshine (Pere: «em dona una mica de TOC veure restes de màscares sobre la zona de l'earthshine»).
Zona = on la capa 258 «Earthshine V88» és del tot opaca (alfa = 1) i d < −6 px del limbe de presentació, erosionada 2 px (lluny del limbe, de
la cromosfera i de les protuberàncies). Per a cada capa amb màscara que hi toca: contingut de la màscara a la zona, i si és a sota o a sobre
de la 258 (a sobre: el que hi pinta es VEU sobre l'Earthshine). Efecte de netejar-les (màscara 0 a la zona) al compost EMULAT.
Sortida: C11_MASCARES.json, zona_earthshine.npz."""
from v93_comu import *
from psb69 import PSB
from vm_compost import comp, capa_box
import cv2
claim(); p = PSB(str(PSB_PERE)); a258, o = p.channel(258, -1); x0, y0 = o; h, w = a258.shape; cx, cy, R = GEO['cx'], GEO['cy'], GEO['R']
yy, xx = np.mgrid[y0:y0 + h, x0:x0 + w]; d = np.hypot(xx - cx, yy - cy) - R
zona = ((a258 == 65535) & (d < -6)).astype(np.uint8); zona = cv2.erode(zona, np.ones((5, 5), np.uint8)) > 0
np.savez_compressed(SORT / 'zona_earthshine.npz', zona=zona, origen=np.array([x0, y0])); log(f'zona: {zona.sum()} px, d màx {d[zona].max():.1f}')
ordre = [L['id'] for L in p.layers]; i258 = ordre.index(258); rep = {'zona_px': int(zona.sum()), 'capes': {}}
for L in p.layers:
    lid = L['id']
    if not L['mask'] or lid in (239, 240, 241, 242, 243, 244): continue
    mb = (L['mask']['left'], L['mask']['top'], L['mask']['right'], L['mask']['bottom'])
    if mb[2] <= x0 or mb[0] >= x0 + w or mb[3] <= y0 or mb[1] >= y0 + h: continue
    m = p.channel_box(lid, -2, (x0, y0, x0 + w, y0 + h), fill=L['mask']['background'] * 257).astype(np.float32) / 65535
    px = p.channel_box(lid, -1, (x0, y0, x0 + w, y0 + h)).astype(np.float32) / 65535 if -1 in L['chans'] else np.ones_like(m)
    ef = m * px * (L['opacity'] / 255)
    rep['capes'][lid] = dict(nom=L['name'][:34], visible=L['visible'], sobre_earthshine=ordre.index(lid) > i258, mascara_zona_mitjana=round(float(m[zona].mean()), 4),
                             mascara_zona_max=round(float(m[zona].max()), 4), px_mascara_gt_0=int((m[zona] > 0).sum()), opacitat_efectiva_zona_max=round(float(ef[zona].max()), 4))
    log(f"{lid} {L['name'][:30]:30s} {'SOBRE' if ordre.index(lid) > i258 else 'sota '} vis={L['visible']} màscara mitjana {m[zona].mean():.4f} màx {m[zona].max():.3f} px>0 {(m[zona] > 0).sum()} opacitat efectiva màx {ef[zona].max():.3f}")
# efecte visible al compost emulat de netejar les de sobre de la 258
BX = (x0, y0, x0 + w, y0 + h); vis = [L['id'] for L in p.layers if L['visible'] and L['right'] > L['left'] and L['id'] not in (239, 240, 241, 242, 243, 244, 269)]
C0 = comp([capa_box(p, i, BX) for i in vis], h, w)[0]; capes = []
for i in vis:
    md, F_, a_ = capa_box(p, i, BX)
    if i in rep['capes']: a_ = np.where(zona, 0, a_)
    capes.append((md, F_, a_))
C1 = comp(capes, h, w)[0]; dif = np.abs(C1 - C0).max(-1)
rep['efecte_emulat'] = dict(px_canviats_mes_de_1_255=int((dif > 1 / 255).sum()), dif_max=round(float(dif.max()), 4), dif_mitjana_a_la_zona=round(float(dif[zona].mean()), 5),
                            px_canviats_fora_zona=int((dif[~zona] > 1e-6).sum()))
log(json.dumps(rep['efecte_emulat'])); desa_json('C11_MASCARES.json', rep)
ys, xs = np.nonzero(dif > 1 / 255)
if xs.size: log(f'on canvia: caixa {(x0 + xs.min(), y0 + ys.min(), x0 + xs.max(), y0 + ys.max())}, d {np.percentile(d[ys, xs], [0, 50, 100]).round(1)}')
