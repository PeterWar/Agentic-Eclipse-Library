"""b4 · Proves de la V88 desada per Photoshop (1-PHOTOSHOP/V88.psb), declarades el 23-09 a les 14:40, abans del desament definitiu:
 P1 cobertura: la pila visible per sota de la capa de PixInsight (sense les capes d'ajust) no té cap píxel amb cobertura < 0,999 a la caixa de la Lluna.
 P2 capes de Pere intactes respecte de la V87: totes les capes que la V88 no declara canviades, canal per canal, ±1 DN16.
 P3 els 16 ràsters de filtre dins del PSB = els d'a4 (±1 DN16).
 P5 cantonada: nivell i gra a banda i banda de la hipotenusa (diferència de nivell < 0,005; gra 0,8–1,25).
 P6 textura arran del limbe al compost natiu: en cada sector de 45° on la Lluna no tapa, |L − gauss σ1,5| a d = 2–4 ≥ 0,5 × la de d = 8–15.
 P8 gra de la franja d'un instant («pixelat», marques verdes): al compost natiu, en cada sector de 45°, el gra fi (|L − gauss σ1,5|) a d = 5–15
    dividit pel de d = 25–40 ha de quedar entre 0,8 i 1,25. Es dona també per a la V87 (b1, vistes_v87/V87_lluna.tif).
 P9 vora de la Lluna (marques liles): a la capa Earthshine V88, la textura |L − gauss σ3| a d = −12..−2 no pot passar d'1,5 × la de d = −60..−30.
    Es dona també per a la 225 de Pere.
 P10 interior de l'earthshine: a d < −24,5 px la capa Earthshine V88 és idèntica a la 225 de Pere.
Escriu B4_QA.json."""
from v88_comu import *
from psb69 import PSB
from v88_compost import comp, capa_box
import tifffile, cv2
claim()
p = PSB(str(ARREL / '1-PHOTOSHOP/V88.psb')); p87 = PSB(str(ARREL / '1-PHOTOSHOP/V87.psb')); rep = {}
geo = json.loads((SORT / 'A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = geo['cx'], geo['cy'], geo['R']
FILTRES = {48: '03v30', 50: '01', 52: '05', 53: '06', 54: 'P03_MGN', 43: 'P02_RHEF', 44: 'P02b_RHEF_ups0.35', 41: 'P01_NRGF', 42: 'P01_NRGF_extrap',
           47: '03', 49: '07', 51: '04', 45: 'P02c_RHEF_local60_native', 46: 'P02d_RHEF_local30_native', 55: 'P04_WOW', 56: 'P05_WOW_bilateral', 250: 'P05_WOW_bilateral'}
AJUSTOS = {239, 240, 241, 242, 243, 244}
# ---- P1
bl = (4800, 3250, 5950, 4300); sota = []
for L in p.layers:
    if L['id'] == 234: break
    if L['visible'] and L['id'] not in AJUSTOS: sota.append(L['id'])
C, a = comp([capa_box(p, lid, bl) for lid in sota], bl[3] - bl[1], bl[2] - bl[0])
rep['P1_cobertura'] = dict(capes=sota, minim=float(a.min()), px_sota_0999=int((a < 0.999).sum()), PASS=bool(a.min() >= 0.999)); log(f'P1 {a.min():.5f}')
# ---- P2
canviades = set(FILTRES) | {258, 255}
difs = {}
for L in p87.layers:
    lid = L['id']
    if lid in canviades: continue
    worst = 0
    for cid in L['chans']:
        x, _ = p.channel(lid, cid); y, _ = p87.channel(lid, cid)
        if x is None or y is None or x.shape != y.shape: worst = 10 ** 9; break
        if x.size: worst = max(worst, int(np.abs(x.astype(np.int32) - y.astype(np.int32)).max()))
    difs[lid] = worst
vis = {L['id']: (L['visible'], p87.layer(L['id'])['visible'] if L['id'] in {q['id'] for q in p87.layers} else None) for L in p.layers}
rep['P2_capes_de_Pere'] = dict(diferencia_max_DN16=difs, visibilitat_canviada={k: v for k, v in vis.items() if v[1] is not None and v[0] != v[1]}, PASS=bool(max(difs.values()) <= 1)); log(f'P2 {max(difs.values())}')
# ---- P3
f3 = {lid: max(int(np.abs(p.channel(lid, c)[0].astype(np.int32) - np.load(SORT / 'filtres_finals' / f'{tag}_u16.npy').astype(np.int32)).max()) for c in range(3)) for lid, tag in FILTRES.items()}
rep['P3_filtres'] = dict(diferencia_max_DN16=f3, PASS=bool(max(f3.values()) <= 1)); log(f'P3 {max(f3.values())}')
# ---- P5
cant = json.loads((SORT / 'B2_CANTONADA.json').read_text()); rep['P5_cantonada'] = cant
# ---- P6, P8 al compost natiu
BL = (4600, 3000, 6150, 4550); yy, xx = np.mgrid[BL[1]:BL[3], BL[0]:BL[2]]; dq = np.hypot(xx - cx, yy - cy) - R; tq = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
L258 = p.layer(258); a258 = np.zeros(dq.shape, np.float32); al = p.channel(258, -1)[0].astype(np.float32) / 65535
a258[L258['top'] - BL[1]:L258['bottom'] - BL[1], L258['left'] - BL[0]:L258['right'] - BL[0]] = al
def mesures(path):
    c = tifffile.imread(path)[..., :3].astype(np.float32) / 65535; Lm = c.mean(-1); T = np.abs(Lm - cv2.GaussianBlur(Lm, (0, 0), 1.5)); out = {}
    for s0 in range(0, 360, 45):
        s = (tq >= s0) & (tq < s0 + 45); r = {}
        if np.median(a258[s & (np.abs(dq - 3) < 0.5)]) < 0.1:
            r['P6_textura_2_4_sobre_8_15'] = round(float(np.median(T[s & (dq >= 2) & (dq <= 4)]) / np.median(T[s & (dq >= 8) & (dq <= 15)])), 3)
        r['P8_gra_5_15_sobre_25_40'] = round(float(np.median(T[s & (dq >= 5) & (dq <= 15)]) / np.median(T[s & (dq >= 25) & (dq <= 40)])), 3)
        out[f'{s0}-{s0 + 45}'] = r
    return out
m88 = mesures(SORT / 'vistes/V88_lluna.tif'); m87 = mesures(SORT / 'vistes_v87/V87_lluna.tif')
rep['P6_P8_compost_natiu'] = dict(V88=m88, V87=m87,
    P6_PASS=all(v['P6_textura_2_4_sobre_8_15'] >= 0.5 for v in m88.values() if 'P6_textura_2_4_sobre_8_15' in v),
    P8_PASS=all(0.8 <= v['P8_gra_5_15_sobre_25_40'] <= 1.25 for v in m88.values()))
log(f"P6 {rep['P6_P8_compost_natiu']['P6_PASS']} P8 {rep['P6_P8_compost_natiu']['P8_PASS']}")
# ---- P9, P10 a les capes de la Lluna
box = (L258['left'], L258['top'], L258['right'], L258['bottom'])
e88 = np.stack([p.channel_box(258, c, box) for c in range(3)], -1).astype(np.float32) / 65535; e225 = np.stack([p.channel_box(225, c, box) for c in range(3)], -1).astype(np.float32) / 65535
yy2, xx2 = np.mgrid[box[1]:box[3], box[0]:box[2]]; d2 = np.hypot(xx2 - cx, yy2 - cy) - R; ok = al >= 0.99
def p9(e):
    Lm = e.mean(-1); m = ok.astype(np.float32); bl_ = cv2.GaussianBlur(Lm * m, (0, 0), 3) / np.maximum(cv2.GaussianBlur(m, (0, 0), 3), 1e-6); T = np.abs(Lm - bl_)
    return float(T[ok & (d2 >= -12) & (d2 <= -2)].std() / T[ok & (d2 >= -60) & (d2 <= -30)].std())
rep['P9_vora_lluna'] = dict(V88=round(p9(e88), 3), capa_225=round(p9(e225), 3), PASS=bool(p9(e88) <= 1.5))
dif = np.abs(np.round(e88 * 65535) - np.round(e225 * 65535))[d2 < -24.5].max()
rep['P10_interior_earthshine'] = dict(diferencia_max_DN16=int(dif), PASS=bool(dif == 0)); log(f"P9 {rep['P9_vora_lluna']} P10 {int(dif)}")
desa_json('B4_QA.json', rep); log('B4 fet')
