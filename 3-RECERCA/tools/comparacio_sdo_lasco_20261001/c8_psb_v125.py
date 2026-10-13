"""c8 · V125-FINAL_comparacio.psb = la V125-FINAL.psb de Pere (49 capes, intactes, i la mateixa imatge fusionada)
+ 6 capes OCULTES amb els instruments alineats al seu marc (7933 × 5021, 16 bits, transparents fora del camp de cada instrument):
  K-Cor (NRGF del HAO) · LASCO C2 (sense fons d'angle) · SDO 304 Å · SDO 211·193·171 Å · contorns del 304 · graella solar.
Com la V82 amb Brno: referència per comparar, cap píxel seu al producte. La V125-FINAL no es toca; el fitxer nou té un nom nou.
Geometria: GEOMETRIA_FINAL.json (centre del Sol per efemèride; la V125 té el marc de la V123, desplaçament 0,0 px mesurat)."""
import os, sys, time, hashlib, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as nd
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from comu_comp import *
from lasco_vista import VistaLasco
sys.path.insert(0, str(ARREL / 'Sortides/apod_anotada_20260930')); import psd16
from psd_tools import PSDImage

SRC = ARREL / '1-PHOTOSHOP/V125-FINAL.psb'
OUTD = RES / 'psb'; OUTD.mkdir(exist_ok=True)
DST = OUTD / 'V125-FINAL_comparacio_v3.psb'   # v3 (01-10, vespre): v2 + graella amb el·lipses del marc afí (revisió 2 de Codex)
assert not DST.exists(), DST
FONT = '/System/Library/Fonts/Supplemental/Arial Unicode.ttf'
gF = geo_final('efemeride'); lluna = np.array(GEO['lluna_px']); RL = GEO['R_lluna_px']
H, W = 5021, 7933
t0 = time.time()
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
r, pa = gF.polar(xx, yy); r = r.astype(np.float32); pa = pa.astype(np.float32)
dins_lluna = np.hypot(xx - lluna[0], yy - lluna[1]) < RL + 1.0
del xx, yy
print(f'graella polar {time.time() - t0:.0f}s')

def rgba16(rgb01, alpha01):
    out = np.empty((H, W, 4), np.uint16)
    for c in range(3): out[..., c] = np.round(np.clip(np.nan_to_num(rgb01[..., c]), 0, 1) * 65535)
    out[..., 3] = np.round(np.clip(np.nan_to_num(alpha01), 0, 1) * 65535)
    return out

capes = []
# 1 · K-Cor (GIF NRGF del HAO, mitjana de 2 min a les 18:29:32)
kc, gK = carrega_kcor('20260812_182932_kcor_l2_nrgf_avg_cropped.gif')
kv = kc.copy(); rK, _ = gK.polar(*np.meshgrid(np.arange(512), np.arange(512)))
valid = (rK > 1.075) & (rK < 2.0)
for (a, b, c, d) in [(0, 150, 0, 48), (395, 512, 0, 40), (0, 265, 462, 512), (340, 512, 462, 512)]: valid[c:d, a:b] = False
v = mostreja(kv / 255.0, gK, r, pa); al = mostreja(valid.astype(np.float32), gK, r, pa)
al = np.where(np.isfinite(al) & (al > 0.5), 1.0, 0.0)
capes.append(('Comparació · K-Cor 18:29:32 UT · llum blanca polaritzada', rgba16(np.dstack([v, v, v]), al)))
print(f'K-Cor {time.time() - t0:.0f}s')

# 2 · LASCO C2 (vista sense harmònics baixos d'angle, vinyetatge corregit); pilar transparent
v2 = VistaLasco('24038985.fts', 2.25, 6.4, mmax=3, suau_r=1.0)
z = v2.mostra(r, pa); z[(pa >= 290) & (pa <= 352)] = np.nan
t = np.clip((z + 1.3) / 5.3, 0, 1)
capes.append(('Comparació · LASCO C2 18:24:31 UT · sense fons angular', rgba16(np.dstack([t, t, t]), np.isfinite(z).astype(np.float32))))
del z, t
print(f'C2 {time.time() - t0:.0f}s')

# 3 i 4 · SDO/AIA (la vista de c7: log, compensació radial fora del disc)
def vista_aia(d, g, eps, p=(1.0, 99.7), rmax=1.32, comp=0.85):
    yy2, xx2 = np.mgrid[0:d.shape[0], 0:d.shape[1]]
    rr2, _ = g.polar(xx2, yy2)
    vv = np.log10(np.clip(d, eps, None)).astype(np.float32); fora = rr2 > 1.0
    edges = np.linspace(1.0, 1.9, 181); k = np.digitize(rr2, edges) - 1
    med = np.asarray(nd.median(vv, labels=np.where(fora, k + 1, 0), index=np.arange(1, len(edges))), float)
    rc = 0.5 * (edges[1:] + edges[:-1]); ok = np.isfinite(med)
    vc = np.where(fora, vv - (np.interp(rr2, rc[ok], med[ok]) - np.interp(1.0, rc[ok], med[ok])) * comp, vv)
    sm = nd.gaussian_filter(vc, 1.2); w = np.clip((rr2 - 1.12) / 0.08, 0, 1); vc = vc * (1 - w) + sm * w
    lo, hi = np.nanpercentile(vc[rr2 < 1.3], p)
    out = mostreja((vc - lo) / (hi - lo), g, r, pa)
    camp = mostreja(np.ones_like(vc), g, r, pa)
    alpha = np.where(np.isfinite(camp) & (camp > 0.5), 1.0, 0.0) * np.clip((rmax + 0.05 - r) / 0.05, 0, 1)
    return np.clip(np.nan_to_num(out), 0, 1), alpha
d304, g304 = carrega_aia('1828', '0304')
t304, a304 = vista_aia(d304, g304, 0.3, p=(3.0, 99.9), comp=0.55); t304 = t304 ** 1.1
capes.append(('Comparació · SDO 304 Å 18:28:06 UT · protuberàncies', rgba16(np.dstack([t304, t304 * 0.60, t304 * 0.28]), a304)))
del t304
ch = []
for ona, eps in [('0211', 0.5), ('0193', 1.0), ('0171', 1.0)]:
    d, g = carrega_aia('1828', ona); tt, aa = vista_aia(d, g, eps); ch.append(tt ** 0.9)
capes.append(('Comparació · SDO 211·193·171 Å 18:28 UT', rgba16(np.dstack(ch), aa)))
del ch
print(f'AIA {time.time() - t0:.0f}s')

# 5 · contorns de l'AIA 304 (protuberàncies): fora del disc i de la Lluna, fins a 1,15 R☉
la = np.log10(np.clip(mostreja(d304, g304, r, pa), 0.3, None)).astype(np.float32)
zona = (r > 1.012) & (r < 1.15) & ~dins_lluna & np.isfinite(la)
sm = nd.gaussian_filter(np.nan_to_num(la, nan=0.0), 1.5)
niv = np.nanpercentile(sm[(r > 1.025) & (r < 1.15) & ~dins_lluna], [85, 95])
rgb = np.zeros((H, W, 3), np.float32); al = np.zeros((H, W), np.float32)
for lv_, col in zip(niv, [(0.35, 0.85, 1.0), (1.0, 1.0, 1.0)]):
    m = sm > lv_; vora = (m & ~nd.binary_erosion(m, iterations=2)) & zona
    rgb[vora] = col; al[vora] = 1.0
capes.append(('Comparació · contorns SDO 304 Å sobre la final', rgba16(rgb, al)))
del la, sm, rgb, al
print(f'contorns {time.time() - t0:.0f}s')

# 6 · graella solar: cercles a 1, 1,5, 2, 3, 4, 5 i 6 R☉, nord solar i marques d'angle cada 30°
im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(im); f = ImageFont.truetype(FONT, 34)
cx, cy, R = gF.cx, gF.cy, gF.R
for rr_ in (1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0):
    # revisió 2 de Codex: al marc afí, un radi constant és una el·lipse; es dibuixa amb px() i no amb un cercle euclidià
    ang = np.arange(0.0, 360.5, 0.25); xs_, ys_ = gF.px(np.full_like(ang, rr_), ang)
    dr.line(list(zip(xs_.tolist(), ys_.tolist())), fill=(255, 255, 255, 150), width=2)
    x_, y_ = gF.px(rr_, 300.0); dr.text((x_ + 6, y_ - 40), f'{rr_:g} R☉'.replace('.', ','), fill=(255, 255, 255, 200), font=f)
for p_ in range(0, 360, 30):
    x1, y1 = gF.px(1.02, p_); x2, y2 = gF.px(6.6 if p_ == 0 else 1.25, p_)
    dr.line([x1, y1, x2, y2], fill=(255, 215, 120, 220) if p_ == 0 else (255, 255, 255, 150), width=3 if p_ == 0 else 2)
    xt, yt = gF.px(1.33, p_); dr.text((xt - 30, yt - 20), f'{p_}°', fill=(255, 255, 255, 200), font=f)
xn, yn = gF.px(6.75, 0.0); dr.text((xn - 40, yn - 24), 'N☉', fill=(255, 215, 120, 230), font=f)
g8 = np.asarray(im).astype(np.float32) / 255.0
capes.append(('Comparació · graella solar: nord i radis', rgba16(g8[..., :3], g8[..., 3])))
del g8, im
print(f'graella {time.time() - t0:.0f}s')

# ---------------- el PSB: la V125-FINAL tal qual + les capes noves ocultes
src_sha = hashlib.file_digest(open(SRC, 'rb'), 'sha256').hexdigest()
psd = PSDImage.open(SRC); n0 = len(list(psd))
noms0 = [l.name for l in psd]
for nom, arr in capes:
    lay = psd16.capa(psd, nom, arr); lay.visible = False
print(f'capes afegides: {len(list(psd)) - n0} (de {n0} a {len(list(psd))}) {time.time() - t0:.0f}s')
psd16.a_lr16(psd)                      # com el Photoshop en 16 bits: capes al bloc Lr16
with open(DST, 'wb') as fh:            # la imatge fusionada i els recursos (ICC) es queden els de la V125-FINAL
    psd._record.write(fh)
dst_sha = hashlib.file_digest(open(DST, 'rb'), 'sha256').hexdigest()
info = dict(font=str(SRC.relative_to(ARREL)), font_sha256=src_sha, desti=str(DST.relative_to(ARREL)), desti_sha256=dst_sha,
            mida_GB=round(os.path.getsize(DST) / 1e9, 3), capes_originals=n0, capes_noves=[c[0] for c in capes], noms_originals=noms0)
json.dump(info, open(OUTD / 'C8_PSB_v3.json', 'w'), indent=1, ensure_ascii=False)
print(f"desat {DST} {info['mida_GB']} GB; SHA {dst_sha[:16]}… ({time.time() - t0:.0f}s)")
