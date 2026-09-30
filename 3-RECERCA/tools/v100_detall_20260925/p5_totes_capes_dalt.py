"""p5 (pregunta de Pere, 26-09) · Inventari de TOTES les capes de la V101 (i el compost de la V101 i la V80 de Pere) als primers píxels de DALT
(PA 80–125°): per calaix de distància al cercle de presentació, (1) cobertura efectiva de cada capa (alfa × màscara × opacitat; 0 si és oculta) i
(2) detall TANGENCIAL del seu contingut (rms de la banda DoG 2→16 px al llarg de l'arc de ln de la lluminància), comparat amb el de 5–8 px.
També el contingut de les capes d'interiors de Pere (76, 96) encara que la seva màscara les amagui. Només lectura."""
import sys, json
from pathlib import Path
import numpy as np, cv2, tifffile
from scipy.ndimage import gaussian_filter1d
ARREL = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB
O = ARREL / '4-RESULTATS/v100_detall_20260925/pregunta_dalt'
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736; X0, Y0, X1, Y1 = 4980, 3250, 5700, 3420     # caixa de dalt
DR_, DS_ = 0.25, 0.5; rr = np.arange(-2.0, 12.0, DR_); tt = np.radians(np.arange(80, 125, DS_ / RL * 180 / np.pi))
R_, T_ = np.meshgrid(RL + rr, tt, indexing='ij'); PX = (LX + R_ * np.cos(T_) - X0).astype(np.float32); PY = (LY - R_ * np.sin(T_) - Y0).astype(np.float32)
BINS = [(-1, 0), (0, 1), (1, 2), (2, 3), (3, 5), (5, 8)]
def polar(img): return cv2.remap(img.astype(np.float32), PX, PY, cv2.INTER_LINEAR)
def detall(lnp):
    g2 = gaussian_filter1d(lnp, 2 / DS_, axis=1, mode='nearest'); g16 = gaussian_filter1d(lnp, 16 / DS_, axis=1, mode='nearest'); return g2 - g16
def perfil(img_lum, cob=None):
    P = polar(np.log(np.maximum(img_lum, 1e-6))); D = detall(P); C = polar(cob) if cob is not None else None; r = {}
    for lo, hi in BINS:
        m = (rr >= lo) & (rr < hi); r[f'{lo}..{hi}'] = dict(detall_rms=round(float(np.std(D[m])), 4), cobertura=None if C is None else round(float(np.mean(C[m])), 3))
    return r
def crop(a, L):   # retalla una capa (coordenades pròpies) a la caixa del llenç
    out = np.zeros((Y1 - Y0, X1 - X0) + a.shape[2:], a.dtype); l, t = int(L['left']), int(L['top'])
    ys, xs = max(Y0, t), max(X0, l); ye, xe = min(Y1, t + a.shape[0]), min(X1, l + a.shape[1])
    if ye > ys and xe > xs: out[ys - Y0:ye - Y0, xs - X0:xe - X0] = a[ys - t:ye - t, xs - l:xe - l]
    return out
p = PSB(str(ARREL / '1-PHOTOSHOP/V101.psb')); rep = {'capes': {}}
for L in p.layers:
    lid = L['id']; l, t, r_, b = int(L['left']), int(L['top']), int(L['right']), int(L['bottom'])
    if r_ <= X0 or l >= X1 or b <= Y0 or t >= Y1: continue
    ch = L['chans']; rgb = [crop(p.channel(lid, c)[0].astype(np.float64), L) for c in (0, 1, 2) if c in ch]
    if not rgb: continue
    lum = (rgb[0] + 2 * rgb[1] + rgb[2]) / 4 if len(rgb) == 3 else rgb[0]
    al = crop(p.channel(lid, -1)[0].astype(np.float64) / 65535, L) if -1 in ch else np.ones_like(lum)
    if -2 in ch:
        m = L['mask']; mk = p.channel(lid, -2)[0].astype(np.float64) / 65535; mk = crop(mk, dict(left=m['left'], top=m['top'])); al = al * mk
    cob = al * (L.get('opacity', 255) / 255) * (1.0 if L.get('visible') else 0.0)
    rep['capes'][f"{lid} {L.get('name')}"] = dict(mode=str(L.get('blend')), visible=bool(L.get('visible')), opacitat=L.get('opacity'), perfil=perfil(lum + 1, cob))
    if lid in (76, 96): rep['capes'][f"{lid} {L.get('name')} [CONTINGUT sense la màscara de Pere]"] = dict(perfil=perfil(lum + 1, crop(p.channel(lid, -1)[0].astype(np.float64) / 65535, L)))
C = tifffile.imread(ARREL / '4-RESULTATS/v100_detall_20260925/final_V101/vistes/V100_lluna.tif')[..., :3].astype(np.float64)[Y0 - 3000:Y1 - 3000, X0 - 4600:X1 - 4600]
rep['compost_V101'] = perfil((C[..., 0] + 2 * C[..., 1] + C[..., 2]) / 4 + 1)
V80 = tifffile.imread(ARREL / '1-PHOTOSHOP/V80.tif')[..., :3].astype(np.float64)[Y0 - 1142:Y1 - 1142, X0 - 1325:X1 - 1325]
rep['V80_de_Pere'] = perfil((V80[..., 0] + 2 * V80[..., 1] + V80[..., 2]) / 4 + 1)
(O / 'P5_TOTES_LES_CAPES_DALT.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
fmt = lambda pr: ' '.join(f"{k}:{v['detall_rms']:.3f}" + (f"(c{v['cobertura']:.2f})" if v.get('cobertura') is not None else '') for k, v in pr.items())
for k, v in rep['capes'].items(): print(k[:44].ljust(44), fmt(v['perfil']))
print('COMPOST V101'.ljust(44), fmt(rep['compost_V101'])); print('V80 de Pere'.ljust(44), fmt(rep['V80_de_Pere']))
