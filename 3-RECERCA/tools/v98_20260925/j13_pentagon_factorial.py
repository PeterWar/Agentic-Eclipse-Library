"""j13 (V98) · Punt 2 de Pere: què causava els «pentàgons» de la capa 49 (07 ACHF azimutal r8) que la V97 va fer desaparèixer.
Factorial 2×2 amb les quatre Vixen desades (finestra canal/comuna × φ original/zero, totes amb --vora taula), passades pel MATEIX nucli
de l'operador 49 (angular_polar sobre ln G de la Vixen + suavitzat radial r8 + back), amb el mateix suport. La Sony és idèntica a les quatre
variants i s'anul·la a la diferència. Mesura: RMS de la diferència (variant − comuna/original) a l'anell d = 100–450 px de la Lluna i
correlació amb el patró real que va desaparèixer (capa 49: V93 d'Artefactes_V95 − V97). Sortida: J13_PENTAGON_FACTORIAL.json + PNG."""
import sys, json, gc
from pathlib import Path
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[3]; T97 = ARREL / '3-RECERCA/tools/v97_refundacio_20260924'
sys.path.insert(0, str(T97)); sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v86_neta_20260923')); sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917'))
from v86_operadors import angular_polar, back
from scipy.ndimage import gaussian_filter1d
from psb69 import PSB
RES = ARREL / '4-RESULTATS/v97_refundacio_20260924'; O = ARREL / '4-RESULTATS/v98_20260925'; P = RES / 'proves_apilat'; V85D = RES / 'cadena_raw'
H, W = 7506, 10551; CX, CY = 5361.768111973117, 3775.747534140857; LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736
y, x = np.ogrid[:H, :W]; r = np.hypot(y - CY, x - CX).astype(np.float32); t = np.arctan2(y - CY, x - CX).astype(np.float32)
dL = (np.hypot(x - LX, y - LY) - RL).astype(np.float32)
mv = np.load(V85D / 'sources_v29/vixen_support.npy'); z4 = np.load(V85D / 's4_baseline/cau/s4_recomposicio_box.npz'); y0, y1, x0, x1 = z4['box'].astype(int)
mv[y0:y1, x0:x1] |= np.load(V85D / 's4_baseline/cau/s4_support_new_box.npy'); mv &= (dL > 60)
VAR = ['comuna_taula_original', 'canal_taula', 'canal_taula_zero', 'comuna_taula_zero']
def op49(nom):
    G = np.load(P / f'vixen_{nom}/vixen_total.npy', mmap_mode='r')[..., 1]; G = np.asarray(G, np.float32); m = mv & np.isfinite(G) & (G > 0)
    p, valid, r0, nt = angular_polar(np.log(np.maximum(np.nan_to_num(G), 1e-8)), m, r, t); del G; gc.collect()
    q = gaussian_filter1d(p * valid, 8, axis=0, mode='constant', cval=0) / np.maximum(gaussian_filter1d(valid, 8, axis=0, mode='constant', cval=0), 1e-8)
    out = back(q, m, r, t, r0, nt).astype(np.float32); del p, valid, q; gc.collect(); print('op49', nom, flush=True); return out, m
ref, mref = op49(VAR[0])
# el patró real que va desaparèixer: capa 49 de la V93 (Artefactes_V95) menys la de la V97, a la mateixa caixa
box = (3800, 2200, 7000, 5400); bx0, by0, bx1, by1 = box
def capa(p):
    s = PSB(p); return s.channel_box(49, 1, box).astype(np.float32) / 65535, s.channel_box(49, -1, box).astype(np.float32) / 65535
a93, al93 = capa(ARREL / '1-PHOTOSHOP/Artefactes_V95.psb'); a97, al97 = capa(ARREL / '1-PHOTOSHOP/V97.psb')
real = np.where((al93 > .99) & (al97 > .99), a93 - a97, np.nan)
dbox = dL[by0:by1, bx0:bx1]; anell = (dbox > 100) & (dbox < 450)
rep = dict(variants=VAR, referencia=VAR[0], anell_d_px=[100, 450], resultats={})
for nom in VAR[1:]:
    v, m = op49(nom); dif = np.where(m & mref, v - ref, np.nan)[by0:by1, bx0:bx1]
    ok = anell & np.isfinite(dif) & np.isfinite(real)
    rms = float(np.sqrt(np.nanmean(dif[ok] ** 2))); cc = float(np.corrcoef(dif[ok], real[ok])[0, 1])
    # nul: la mateixa correlació amb el patró real girat 90° (posicions sense relació)
    realg = np.rot90(np.nan_to_num(real), 2); okg = ok & (realg != 0); cn = float(np.corrcoef(dif[okg], realg[okg])[0, 1])
    rep['resultats'][nom] = dict(rms_dif_ln=round(rms, 5), corr_amb_patro_real=round(cc, 3), corr_nul_girat180=round(cn, 3))
    print(nom, rep['resultats'][nom], flush=True)
    D = cv2.resize(np.nan_to_num(dif), None, fx=.5, fy=.5, interpolation=cv2.INTER_AREA); s = np.percentile(np.abs(D), 99.5) + 1e-9
    cv2.imwrite(str(O / f'J13_{nom}_menys_comuna.png'), (np.clip(.5 + .5 * D / s, 0, 1) * 255).astype(np.uint8)); del v, m, dif; gc.collect()
(O / 'J13_PENTAGON_FACTORIAL.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
