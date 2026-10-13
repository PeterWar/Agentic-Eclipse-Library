"""v4 · Vistes per a Pere (llenç SENCER, a la meitat: 3967 px d'ample; JPEG amb el perfil Adobe RGB de la final incrustat).
Les fusionades es llegeixen dels FITXERS (V125-FINAL.psb i V128.psb, lector cru, sense Photoshop), no de la matriu calculada.
  01 · la fusionada de la V125-FINAL, tal com és;
  02 · la fusionada de la V128 (= la capa nova encesa);
  03 · el quocient V128 / V125 en lluminància lineal (Adobe RGB lineal), amb les isolínies d'E, el zenit i 1,5 i 4 R☉;
  04 · els tres de costat, petits i amb rètols a sobre (els rètols no tapen cap píxel del llenç).
Reducció: Lanczos per canal (ed_comu.redueix_float), com les vistes P2 de l'e3.
El PNG intermedi del panell 03 es deixa a la carpeta de treball (fora del projecte) i no s'esborra.
Ús: PYTHONDONTWRITEBYTECODE=1 <python> v4_vistes.py <V128.psb> <carpeta_de_treball>"""
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

AQUI = Path(__file__).resolve().parent
ARREL = AQUI.parents[2]
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/extincio_diferencial_20261012'))
import psb_cru as pc  # noqa: E402
import ed_comu as ed  # noqa: E402

T0 = time.time()
mc = ed.mc
SRC = ARREL / '1-PHOTOSHOP/V125-FINAL.psb'
DST = Path(sys.argv[1]).resolve()
TREB = Path(sys.argv[2]).resolve()                                    # carpeta de treball (fora del projecte)
TREB.mkdir(parents=True, exist_ok=True)
SORT = ARREL / 'Sortides/v128_extincio_20261012'
RES = ARREL / '3-RECERCA/resultats/v128_extincio_20261012'
SORT.mkdir(parents=True, exist_ok=True)
AMPLE = 3967                                                           # la meitat de 7933 (arrodonit amunt)


def fusionada(ruta):
    p = pc.PSB(ruta)
    H, W, n = p.alt, p.ample, p.alt * p.ample * 2
    assert p.id_compressio == 0
    a = np.stack([np.frombuffer(p.b, '>u2', H * W, p.id_pos + 2 + k * n).reshape(H, W) for k in range(3)], -1).astype(np.uint16)
    icc = [bytes(p.b[r['dades']:r['dades'] + r['mida']]) for r in p.recursos if r['id'] == 1039][0]
    p.tanca()
    return a, icc


U, icc = fusionada(SRC)
V, icc2 = fusionada(DST)
assert icc == icc2
H, W = U.shape[:2]
ii = ed.info_icc(icc)
YC = np.array(ii['Y'])
print(f'fusionades llegides ({time.time() - T0:.0f} s)', flush=True)


def vista(a16):
    return Image.fromarray((np.clip(np.stack([ed.redueix_float(a16[..., c].astype(np.float32) / 65535.0, AMPLE)
                                              for c in range(3)], -1), 0, 1) * 255 + 0.5).astype(np.uint8))


imA, imB = vista(U), vista(V)
ed.desa_jpeg(imA, SORT / '01_V125-FINAL_fusionada.jpg', icc)
ed.desa_jpeg(imB, SORT / '02_V128_fusionada_capa_nova_encesa.jpg', icc)
print(f'01 i 02 ({imA.size}) ({time.time() - T0:.0f} s)', flush=True)

# quocient de lluminància lineal, per blocs de la mida de la vista
hh = int(round(H * AMPLE / W))
Ya = cv2.resize((((U.astype(np.float64) / 65535.0) ** ed.GAMMA) @ YC).astype(np.float32), (AMPLE, hh), interpolation=cv2.INTER_AREA)
Yd = cv2.resize((((V.astype(np.float64) / 65535.0) ** ed.GAMMA) @ YC).astype(np.float32), (AMPLE, hh), interpolation=cv2.INTER_AREA)
quoc = Yd / np.maximum(Ya, 1e-9)
escala = W / AMPLE
xs = (np.arange(AMPLE) + 0.5) * escala - 0.5
ys = (np.arange(hh) + 0.5) * (H / hh) - 0.5
sp = ed.Spline(ed.GRAELLA_FINAL)
Ev = ed.factor_E(sp.X_graella(ys, xs), sp.X_sol).astype(np.float32)
XX, YY = np.meshgrid(xs, ys)
lluna = np.hypot(XX - ed.LLUNA_F[0], YY - ed.LLUNA_F[1]) <= ed.R_LLUNA_F
qv = np.where(lluna, np.nan, quoc)
fons = 0.75 * (Ya ** (1 / ed.GAMMA))
g = ed.geo_final()
geoV = mc.Geo(g.cx, g.cy, g.R, g.n, g.e)
PAZ = json.load(open(ed.RES / 'E1_MASSA_AIRE_FINAL.json'))['zenit']['PA_solar_deg']['r1']
tmp = TREB / 'v4_03_srgb.png'                                         # intermedi: es queda a la carpeta de treball
ed.panell_factor(fons, qv, Ev, geoV, escala, PAZ, tmp, ample=AMPLE, etiqueta='lluminància lineal: V128 / V125', r_fletxa=4.5, r_text=5.05)
imC = ed.srgb_a_adobe(Image.open(tmp), icc)
if imC.size != imA.size:
    imC = imC.resize(imA.size, Image.LANCZOS)
ed.desa_jpeg(imC, SORT / '03_quocient_V128_sobre_V125.jpg', icc)
print(f'03 ({time.time() - T0:.0f} s)', flush=True)

mig = 1500


def petit(im, t, s):
    return ed.amb_rotol(im.resize((mig, int(round(im.height * mig / im.width))), Image.LANCZOS), t, s, destacat=(255, 200, 80))


ed.desa_jpeg(ed.costat_a_costat([petit(imA, 'A · V125-FINAL (fusionada)', 'tal com és'),
                                  petit(imB, 'B · V128 (fusionada)', 'capa nova encesa · APROXIMACIÓ, no és una cura'),
                                  petit(imC, 'C · quocient B / A', 'isolínies: E; fletxa: zenit')]),
             SORT / '04_costat_a_costat.jpg', icc)
# xifres de control de la vista (per al rebut): quocient als sectors de ±15° a 1,5 i 4 R☉
r, pa = g.polar(XX, YY)
dpa = np.abs((pa - PAZ + 180) % 360 - 180)
sect = {}
for rr in (1.5, 2.0, 3.0, 4.0):
    for nom, m in (('zenit', dpa <= 15), ('horitzo', dpa >= 165)):
        m = m & (np.abs(r - rr) <= 0.1) & ~lluna
        sect[f'{rr}_{nom}'] = dict(quocient_mitja=float(np.nanmean(quoc[m])), E=float(Ev[m].mean()))
info = dict(guio=str(Path(__file__).resolve().relative_to(ARREL)), data=time.strftime('%Y-%m-%dT%H:%M:%S'),
            vistes={n.name: ed.sha256(n) for n in sorted(SORT.glob('0*.jpg'))}, mida_px=list(imA.size),
            perfil=ii['desc'], quocient_sectors_15graus=sect,
            fons_r_mes_6=dict(mediana=float(np.median(quoc[(r > 6) & ~lluna])), p5=float(np.percentile(quoc[(r > 6) & ~lluna], 5)),
                              p95=float(np.percentile(quoc[(r > 6) & ~lluna], 95))),
            segons=round(time.time() - T0, 1))
json.dump(info, open(RES / 'V4_VISTES.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(info, indent=1, ensure_ascii=False))
