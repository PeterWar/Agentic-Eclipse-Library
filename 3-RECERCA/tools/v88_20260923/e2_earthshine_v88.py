"""e2 · Capa «Earthshine V88» (Claude, 23-09-2026).
Encàrrec de Pere: refer l'earthshine des de zero perquè la vora exterior del disc (marques liles de la capa Artefactes V87) té massa textura,
potser per contaminació de saturació. Què s'ha trobat (e1, proves de meitats i LROC, 4-RESULTATS/v88_20260923/E*_*.json):
  · arran del limbe, els fotogrames llargs hi són saturats a pedaços (10 s: només el 54–57 % de píxels vàlids a −12..−2 px) i la llum dispersa
    de la corona hi és 2–7 vegades el nivell del disc;
  · un apilat des de zero amb fotogrames nets (e1: un sol registre sobre la Lluna, sense píxels supervivents d'una zona saturada, guarda de
    moviment) té, a −30..−2 px, un relleu que dues meitats independents reprodueixen (correlació 0,88–0,99) però que NO és lunar (correlació
    amb LROC 0,01–0,21): és estructura de la llum dispersa. A l'interior, en canvi, el relleu sí que és lunar;
  · amb només la Vixen, l'interior des de zero és pitjor que el de la capa de Pere (LROC 0,52 contra 0,66 a 6 px; 0,35 contra 0,66 a 12 px).
Per tant, la capa V88 conserva l'earthshine de Pere a l'interior i, a l'anell de la vora, treu l'estructura fina no lunar: cada canal es
suavitza AL LLARG DEL RADI (Gaussiana normalitzada σ 5 px, llegint només píxels del disc amb alfa ≥ 0,99 i a més de 12 px del limbe: els
últims px són els pitjors i, si hi entren, el suavitzat els allarga en flames radials), amb
transició de pes smoothstep de 24 px (res) a 12 px (tot) del limbe, i un suavitzat azimutal curt (σ 4 px d'arc) perquè l'extensió radial no
faci flames; la font és a més de 12 px del limbe (a 280° els arcs arriben a −15 px). L'alfa és exactament la de la capa de Pere (225).
Sortida: E2_earthshine_v88.npz (RGB u16 i alfa, a la caixa de la capa 225) i E2_EARTHSHINE_V88.json."""
from v88_comu import *
from psb69 import PSB
import cv2
from scipy.ndimage import gaussian_filter1d
claim()
SIGMA_R, SIGMA_T, D0, D1, D_FONT = 5.0, 4.0, -24.0, -12.0, -12.0   # font només a més de 12 px del limbe (a 280° els arcs arriben a −15 px); σ azimutal 4 px d'arc
p = PSB(str(ARREL / '1-PHOTOSHOP/V87.psb')); L = p.layer(225); box = (L['left'], L['top'], L['right'], L['bottom'])
rgb = np.stack([p.channel_box(225, c, box) for c in range(3)], -1).astype(np.float32) / 65535; alfa = p.channel_box(225, -1, box)
geo = json.loads((SORT / 'A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = geo['cx'], geo['cy'], geo['R']
x0, y0, x1, y1 = box; Hb, Wb = y1 - y0, x1 - x0
yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32); d = np.hypot(xx - cx, yy - cy) - R
# coordenades polars: 2880 azimuts (0,125°) i radis d'1/2 px entre R−80 i R+6
NT, r0, r1, dr = 2880, R - 80, R + 6, 0.5; rr = np.arange(r0, r1 + 1e-6, dr); tt = np.arange(NT) * 2 * np.pi / NT
MXp = (cx + rr[None, :] * np.cos(tt[:, None]) - x0).astype(np.float32); MYp = (cy - rr[None, :] * np.sin(tt[:, None]) - y0).astype(np.float32)
fiable = ((alfa.astype(np.float32) / 65535 >= 0.99) & (d < D_FONT)).astype(np.float32)
wp = cv2.remap(fiable, MXp, MYp, cv2.INTER_LINEAR, borderValue=0)
sig = SIGMA_R / dr; wps = gaussian_filter1d(wp, sig, axis=1, mode='nearest')
suau = np.zeros_like(rgb)
# de polar a cartesià: per a cada píxel, el seu (θ, r) a la graella polar
th_pix = (np.arctan2(-(yy - cy), xx - cx) % (2 * np.pi)) / (2 * np.pi) * NT; r_pix = (d + R - r0) / dr
for c in range(3):
    vp = cv2.remap(rgb[..., c], MXp, MYp, cv2.INTER_LINEAR, borderValue=0)
    num = gaussian_filter1d(vp * wp, sig, axis=1, mode='nearest'); num = gaussian_filter1d(num, SIGMA_T, axis=0, mode='wrap'); wpt = gaussian_filter1d(wps, SIGMA_T, axis=0, mode='wrap')
    sp = np.where(wpt > 1e-3, num / np.maximum(wpt, 1e-6), 0).astype(np.float32)
    # la graella és periòdica en θ: s'afegeix la primera fila al final per interpolar bé a 360°
    spp = np.vstack([sp, sp[:1]])
    suau[..., c] = cv2.remap(spp, r_pix.astype(np.float32), th_pix.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
def ss(x, a, b): t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
b = ss(d, D0, D1)[..., None] * (d > r0 - R + 4)[..., None]
nou = (1 - b) * rgb + b * suau
nou = np.where((alfa > 0)[..., None], nou, rgb)
u16 = np.round(np.clip(nou, 0, 1) * 65535).astype(np.uint16)
# control: textura fina per anells, abans i després
def tex(a): L_ = a.mean(-1); return np.abs(L_ - cv2.GaussianBlur(L_, (0, 0), 3))
T0, T1 = tex(rgb), tex(nou); dens = alfa.astype(np.float32) / 65535 > 0.99
rep = dict(capa_font=dict(id=225, nom=L['name'], caixa=list(box)), sigma_radial_px=SIGMA_R, sigma_azimutal_px=SIGMA_T, transicio_px=[D0, D1], font_fins_a_px=D_FONT, centre=[cx, cy, R], textura_per_anell={})
for a_, b_ in [(-300, -100), (-100, -50), (-50, -30), (-30, -20), (-20, -15), (-15, -10), (-10, -6), (-6, -3), (-3, -1)]:
    q = dens & (d >= a_) & (d < b_); rep['textura_per_anell'][f'{a_}..{b_}'] = [round(float(T0[q].std() * 1000), 2), round(float(T1[q].std() * 1000), 2)]
rep['canvi_interior_d_menor_que_24'] = int(np.abs(u16.astype(np.int32) - np.round(rgb * 65535).astype(np.int32))[d < -24.5].max())
np.savez_compressed(SORT / 'E2_earthshine_v88.npz', rgb=u16, alfa=alfa, caixa=np.array(box))
desa_json('E2_EARTHSHINE_V88.json', rep); log('E2 fet · textura (abans, després) ' + json.dumps(rep['textura_per_anell']) + f" · canvi màxim a l'interior {rep['canvi_interior_d_menor_que_24']} DN16")
