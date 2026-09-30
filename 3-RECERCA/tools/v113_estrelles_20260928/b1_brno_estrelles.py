"""b1 · V113 (Claude, 28-09-2026): les capes de referència de Brno (230 = 200 mm, 231 = 400 mm, 232 = 530 mm) encaixades per ESTRELLES.
Pere: «arregla-ho directament a V113; la seva òptica té una geometria diferent, si les estrelles no encaixen del tot no em preocupa».
L'encaix de la V82 (18-09) es va fer amb la corona, que no fixa l'escala (−0,84 / −0,11 / +0,67 %) ni el gir (5–10′): les estrelles de Brno hi queden
a 33 / 11 / 17 px RMS de les nostres. La transformació per estrelles (semblança, 'new_A' de 4-RESULTATS/v112_20260928/ASTROMETRIA.json, confirmada
per dues mesures independents: residu 4,4 / 3,0 / 1,5 px del llenç = 0,35–0,5 px del PNG) les deixa on són.
Recepta IDÈNTICA a la de la V82 (3-RECERCA/tools/v82_capes_brno_20260918/build_capes_v82.py): PNG sRGB 8 bits → lineal → Adobe RGB lineal → gamma
563/256 → 16 bits; alfa = 1 dins del marc del contingut (geometria.json); warpAffine bicúbic (RGB) i bilineal (alfa); caixa = contorn transformat
retallat al llenç. CONTROL: amb la transformació antiga ha de reproduir, després de la quantització del Photoshop, els canals de la V113.
La 233 (800 mm) no té prou estrelles per a un encaix estel·lar (2–5): es deixa com era. Ús: b1_brno_estrelles.py → 4-RESULTATS/v113_estrelles_20260928/brno/"""
import sys, json, time
from pathlib import Path
import numpy as np, cv2
from PIL import Image
R = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(R / '3-RECERCA/tools/v108_20260926/cadena'))
from comu_v108 import PSB, q_blocs
O = R / '4-RESULTATS/v113_estrelles_20260928/brno'; O.mkdir(parents=True, exist_ok=True)
BRNO = R / '3-RECERCA/druckmuller_fotos_finals'
GEO = json.loads((R / '3-RECERCA/tools/estudi_druckmuller/geometria.json').read_text())
J = json.loads((R / '4-RESULTATS/v82_capes_brno_20260918/registre_v82.json').read_text())
AST = json.loads((R / '4-RESULTATS/v112_20260928/ASTROMETRIA.json').read_text())['Brno']['references']
FW, FH = 10551, 7506
CAPES = {230: ('TSE_2026_200mm_DHS.png', 'optim3', '200'), 231: ('TSE_2026_400mm_DHS.png', 'optim3', '400'), 232: ('TSE_2026_530mm_DHS.png', 'optim', '530')}
M_sRGB_XYZ = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
M_XYZ_ARGB = np.array([[2.0413690, -0.5649464, -0.3446944], [-0.9692660, 1.8760108, 0.0415560], [0.0134474, -0.1183897, 1.0154096]])
M_sRGB_ARGB = M_XYZ_ARGB @ M_sRGB_XYZ; GAMMA_ARGB = 563.0 / 256.0
def srgb_a_lineal(c): return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def a_adobe16(rgb8):
    lin = srgb_a_lineal(rgb8.astype(np.float64) / 255.0)
    return np.round(np.clip(lin @ M_sRGB_ARGB.T, 0, 1) ** (1.0 / GAMMA_ARGB) * 65535).astype(np.uint16)

def capa(nom, A):
    f0, f1, c0, c1 = GEO[nom]['marc']
    im = np.asarray(Image.open(BRNO / nom).convert('RGB')); H, W = im.shape[:2]
    rgb16 = a_adobe16(im).astype(np.float32); alfa = np.zeros((H, W), np.float32); alfa[f0:f1, c0:c1] = 1.0
    cants = np.array([[c0, f0, 1], [c1, f0, 1], [c0, f1, 1], [c1, f1, 1]], np.float64) @ A.T
    x0, y0 = np.floor(cants.min(axis=0)).astype(int); x1, y1 = np.ceil(cants.max(axis=0)).astype(int)
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, FW), min(y1, FH)
    Ab = A.copy(); Ab[0, 2] -= x0; Ab[1, 2] -= y0
    out = np.zeros((y1 - y0, x1 - x0, 3), np.float32)
    for k in range(3): out[..., k] = cv2.warpAffine(rgb16[..., k], Ab, (x1 - x0, y1 - y0), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    al = cv2.warpAffine(alfa, Ab, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    rgb = np.clip(np.round(out), 0, 65535).astype(np.uint16); a16 = np.clip(np.round(al * 65535), 0, 65535).astype(np.uint16); rgb[a16 == 0] = 0
    return rgb, a16, (int(x0), int(y0), int(x1), int(y1))

def semblanca(A):
    s = float(np.hypot(A[0, 0], A[1, 0])); g = float(np.degrees(np.arctan2(A[1, 0], A[0, 0]))); return s, g

t0 = time.time(); p = PSB(str(R / '1-PHOTOSHOP/V113.psb')); rebut = {}
for lid, (nom, tria, clau) in CAPES.items():
    L = p.layer(lid); bb_v113 = (L['left'], L['top'], L['right'], L['bottom'])
    A_vell = np.asarray(J['imatges'][nom][tria]['A_png_a_v'], np.float64)
    rgb, a16, bb = capa(nom, A_vell)
    ctrl = dict(caixa_igual=bb == bb_v113)
    if bb == bb_v113:
        for k in range(3):
            act, _ = p.channel(lid, k); d = act.astype(np.int32) - q_blocs(rgb[..., k]).astype(np.int32)
            ctrl[f'canal{k}_diferents'] = int(np.count_nonzero(d)); ctrl[f'canal{k}_max_DN'] = int(np.abs(d).max())
        act, _ = p.channel(lid, -1); d = act.astype(np.int32) - q_blocs(a16).astype(np.int32)
        ctrl['alfa_diferents'] = int(np.count_nonzero(d)); ctrl['alfa_max_DN'] = int(np.abs(d).max())
    print(lid, nom, 'CONTROL', ctrl, f'{time.time()-t0:.0f}s', flush=True)
    A_nou = np.asarray(AST[clau]['new_A'], np.float64)
    rgb, a16, bb = capa(nom, A_nou)
    np.savez_compressed(O / f'L{lid}.npz', R=rgb[..., 0], G=rgb[..., 1], B=rgb[..., 2], A=a16, bbox=np.array(bb))
    sv, gv = semblanca(A_vell); sn, gn = semblanca(A_nou)
    rebut[str(lid)] = dict(png=nom, control_amb_encaix_V82=ctrl, caixa_V113=list(bb_v113), caixa_nova=list(bb),
                           encaix_V82=dict(escala=sv, gir_graus=gv, A=A_vell.tolist()), encaix_estrelles=dict(escala=sn, gir_graus=gn, A=A_nou.tolist(),
                           n_estrelles=AST[clau]['n'], RMS_final_px=AST[clau]['final_RMS_px'], RMS_reservades_px=AST[clau]['held_RMS_px']),
                           canvi=dict(escala_pct=(sn / sv - 1) * 100, gir_arcmin=(gn - gv) * 60))
    print(lid, 'NOU', rebut[str(lid)]['canvi'], bb, f'{time.time()-t0:.0f}s', flush=True)
(O / 'B1_REBUT.json').write_text(json.dumps(rebut, indent=1, ensure_ascii=False))
