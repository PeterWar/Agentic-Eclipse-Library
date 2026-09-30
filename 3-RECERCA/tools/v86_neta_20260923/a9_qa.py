"""a9 · Proves de la V86 desada per Photoshop (1-PHOTOSHOP/V86.psb), totes predeclarades abans de mirar-ne el resultat:
 P1 cobertura: la pila visible per sota de la capa de PixInsight no té cap píxel amb cobertura < 0,999 (llenç sencer; la Lluna a resolució plena).
 P2 capes de Pere intactes respecte de la V85 (±1 DN16 per la requantització del desament natiu): Lluna, fotos, estrelles, ajustos, marques, referències.
 P3 els 16 ràsters de filtre dins del PSB = els d'a4 (±1 DN16).
 P4 continuïtat al limbe: per a cada filtre visible, salt mitjà per azimut a la vora exterior de la franja (anell d'ancoratge contra el d'a dins)
    i perfil radial de la mediana azimutal a r 440–560 (V84, V85, V86) — cap anell ni graó nou.
 P5 cantonada: nivell i gra del cel a banda i banda de la hipotenusa iguals (diferència de nivell < 0,005, relació de gra 0,8–1,25).
 P6 textura arran del limbe (afegida el 23-09 a les 3:40, abans del desament de Photoshop, després de trobar la tira llisa de la primera V86):
    al compost natiu de Photoshop (vistes/V86_lluna.tif), en cada sector de 45° on la Lluna no tapa (alfa < 0,1 a d = 3 px), la mediana de
    |L − gauss σ1,5| a d = 2–4 px del limbe ≥ 0,5 × la de d = 8–15 px.
 P7 sense vora: al mateix compost i sectors, la lluminància mediana a d = 1–4 px dins de ±10 % de la de d = 10–15 px.
    P6 i P7 es passen també a la V86 retirada (descartat_intent4_tira_llisa/vistes) com a control.
Escriu A9_QA.json; les vistes comparatives les fa a9b_vistes.py."""
from v86_comu import *
from psb69 import PSB
from v86_compost import comp, capa_box
claim()
V86 = ARREL / '1-PHOTOSHOP/V86.psb'; p = PSB(str(V86)); p85 = PSB(str(ARREL / '1-PHOTOSHOP/V85.psb')); p84 = PSB(str(ARREL / '1-PHOTOSHOP/V84.psb'))
rep = dict(fitxer=dict(path=str(V86.relative_to(ARREL)), sha256=sha(V86), bytes=V86.stat().st_size, capes=len(p.layers), llenc=[p.width, p.height]))
# ---- P1 cobertura per sota de PixInsight
i234 = next(L['i'] for L in p.layers if L['id'] == 234)
sota = [L for L in p.layers[:i234] if L['visible'] and (L['right'] - L['left']) > 0]
def cobertura(box):
    t = None
    for L in sota:
        _, _, a = capa_box(p, L['id'], box); t = (1 - a) if t is None else t * (1 - a)
    return 1 - t
geo = json.loads((SORT / 'A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy = geo['cx'], geo['cy']
bl = (int(cx) - 700, int(cy) - 700, int(cx) + 700, int(cy) + 700); cl = cobertura(bl)
rows = []
for s in range(0, H, 1500):
    cf = cobertura((0, s, W, min(H, s + 1500))); rows.append(float(cf.min()))
rep['P1_cobertura'] = dict(capes_sota_234=[L['id'] for L in sota], lluna_min=float(cl.min()), lluna_px_sota_0999=int((cl < 0.999).sum()), llenc_min_per_franges=rows,
                          PASS=bool(cl.min() >= 0.999 and min(rows) >= 0.999))
log(f"P1 cobertura: Lluna min {cl.min():.5f}, llenç min {min(rows):.5f}")
# ---- P2 capes de Pere intactes
difs = {}
for lid in [30, 76, 96, 204, 206, 224, 202, 239, 240, 241, 242, 243, 244, 246, 251, 203, 230, 231, 232, 233, 62, 252]:
    L = p.layer(lid); worst = 0
    for cid in L['chans']:
        a, _ = p.channel(lid, cid); b, _ = p85.channel(lid, cid)
        if a is None or b is None or a.shape != b.shape: worst = 1e9; break
        if a.size: worst = max(worst, int(np.abs(a.astype(np.int32) - b.astype(np.int32)).max()))
    difs[lid] = worst
rep['P2_capes_de_Pere'] = dict(diferencia_max_DN16=difs, PASS=bool(max(difs.values()) <= 1))
log(f"P2 capes de Pere: dif màx {max(difs.values())}")
# ---- P3 filtres
FILTRES = {48: '03v30', 50: '01', 52: '05', 53: '06', 54: 'P03_MGN', 43: 'P02_RHEF', 44: 'P02b_RHEF_ups0.35', 41: 'P01_NRGF', 42: 'P01_NRGF_extrap', 47: '03', 49: '07', 51: '04', 45: 'P02c_RHEF_local60_native', 46: 'P02d_RHEF_local30_native', 55: 'P04_WOW', 56: 'P05_WOW_bilateral', 250: 'P05_WOW_bilateral'}
f3 = {}
for lid, tag in FILTRES.items():
    ref = np.load(SORT / 'filtres_finals' / f'{tag}_u16.npy', mmap_mode='r'); f3[lid] = max(int(np.abs(p.channel(lid, c)[0].astype(np.int32) - ref.astype(np.int32)).max()) for c in range(3))
rep['P3_filtres'] = dict(diferencia_max_DN16=f3, PASS=bool(max(f3.values()) <= 1)); log(f"P3 filtres: dif màx {max(f3.values())}")
# ---- P4 continuïtat al limbe
g = np.load(SORT / 'A2_geometria.npz'); rb = g['rb_s']; NB = len(rb); MU = json.loads((SORT / 'A4_FRANJA.json').read_text())['mu_px']
x0, y0, x1, y1 = bl; yy, xx = np.mgrid[y0:y1, x0:x1]; rL = np.hypot(xx - cx, yy - cy); th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360; ib = (th / 360 * NB).astype(int) % NB; RB = rb[ib]
p4 = {}
for lid in [41, 42, 47, 49, 51, 45, 46, 55, 56]:
    out = {}
    for nom, psb in [('V84', p84), ('V85', p85), ('V86', p)]:
        a = psb.channel_box(lid, 1, bl).astype(np.float32) / 65535
        prof = [float(np.median(a[(rL >= r0) & (rL < r0 + 4)])) for r0 in range(440, 560, 4)]
        dentro = (rL >= RB + MU - 3) & (rL < RB + MU); fora = (rL >= RB + MU) & (rL < RB + MU + 3)
        salt = [abs(float(np.median(a[dentro & (ib // 8 == k)]) - np.median(a[fora & (ib // 8 == k)]))) for k in range(NB // 8)]
        rugositat = float(np.mean(np.abs(np.diff(prof))) * 65535)
        out[nom] = dict(perfil_radial_440_560=np.round(prof, 5).tolist(), salt_vora_franja_mitja_DN16=float(np.mean(salt) * 65535), salt_vora_franja_p95_DN16=float(np.percentile(salt, 95) * 65535), rugositat_perfil_DN16=rugositat)
    p4[lid] = out; log(f"P4 {lid}: rugositat perfil V84 {out['V84']['rugositat_perfil_DN16']:.0f} V85 {out['V85']['rugositat_perfil_DN16']:.0f} V86 {out['V86']['rugositat_perfil_DN16']:.0f} DN16")
rep['P4_limbe'] = p4
# ---- P5 cantonada
cant = next(L for L in p.layers if L['id'] == 255 or L['name'].startswith('Cantonada del logo'))
rep['P5_cantonada'] = json.loads((SORT / 'A7_CANTONADA.json').read_text()); rep['P5_cantonada']['capa'] = dict(id=cant['id'], nom=cant['name'], rect=[cant['left'], cant['top'], cant['right'], cant['bottom']], visible=cant['visible'])
# ---- P6 i P7 textura i vora arran del limbe, al compost natiu de Photoshop
import tifffile, cv2
BL = (4600, 3000, 6150, 4550); yy, xx = np.mgrid[BL[1]:BL[3], BL[0]:BL[2]]; dq = np.hypot(xx - cx, yy - cy) - geo['R']; tq = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
e30 = np.zeros(dq.shape, np.float32); by0, by1, bx0, bx1 = g['box']; e30[by0 - BL[1]:by1 - BL[1], bx0 - BL[0]:bx1 - BL[0]] = g['e30']
def p67(path):
    c = tifffile.imread(path)[..., :3].astype(np.float32) / 65535; L = c.mean(-1); T = np.abs(L - cv2.GaussianBlur(L, (0, 0), 1.5)); out = {}
    for s0 in range(0, 360, 45):
        s = (tq >= s0) & (tq < s0 + 45)
        if np.median(e30[s & (np.abs(dq - 3) < 0.5)]) >= 0.1: out[f'{s0}-{s0 + 45}'] = 'tapat per la Lluna'; continue
        tex = float(np.median(T[s & (dq >= 2) & (dq <= 4)]) / np.median(T[s & (dq >= 8) & (dq <= 15)]))
        niv = float(np.median(L[s & (dq >= 1) & (dq <= 4)]) / np.median(L[s & (dq >= 10) & (dq <= 15)]))
        out[f'{s0}-{s0 + 45}'] = dict(textura_2_4_sobre_8_15=round(tex, 3), nivell_1_4_sobre_10_15=round(niv, 4), P6=tex >= 0.5, P7=abs(niv - 1) <= 0.10)
    return out
r86 = p67(SORT / 'vistes/V86_lluna.tif'); rv = SORT / 'descartat_intent4_tira_llisa/vistes/V86_lluna.tif'
rep['P6_P7_limbe_natiu'] = dict(V86=r86, V86_retirada=p67(rv) if rv.exists() else None,
                               P6_PASS=all(v['P6'] for v in r86.values() if isinstance(v, dict)), P7_PASS=all(v['P7'] for v in r86.values() if isinstance(v, dict)))
log(f"P6 {rep['P6_P7_limbe_natiu']['P6_PASS']} P7 {rep['P6_P7_limbe_natiu']['P7_PASS']}")
desa_json('A9_QA.json', rep); log('A9 fet')
