"""Construeix les 4 capes de referència (Brno alineades al llenç V81) a partir de registre_v82.json.

Per imatge: PNG sRGB 8 bits → lineal → Adobe RGB (1998) lineal (matriu, D65 als dos costats) → gamma
Adobe (563/256) → 16 bits; alfa = 1 dins del marc del contingut (el marc gris de 39 px fora; el peu de
foto amb el crèdit es conserva), 0 a la resta. Transformació afí PNG → llenç (semblança: escala, gir,
translació) amb interpolació bicúbica (cv2); l'alfa amb bilineal (vora suau). Caixa = contorn transformat
del contingut retallat al llenç. Sortida: capa_<nom>.npz (R,G,B,A uint16, bbox) + vistes de comprovació.
Tria de la transformació: 4 paràmetres si el control torna (800, 530); si no, 3 paràmetres amb l'escala
de la cadena declarada (400, 200) — el rebut ho diu.
"""
import json, numpy as np, cv2, time
from PIL import Image
ROOT = '/Users/USUARI/Desktop/Eclipse 2026'
S = '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/49e1d801-8306-4d45-9cae-a03da6b42a8d/scratchpad'
BRNO = ROOT + '/3-RECERCA/druckmuller_fotos_finals'
GEO = json.load(open(ROOT + '/3-RECERCA/tools/estudi_druckmuller/geometria.json'))
J = json.load(open(S + '/registre_v82.json')); FW, FH = 10551, 7506
TRIA = {'TSE2026_Trigaza_800mm.png': 'optim', 'TSE_2026_530mm_DHS.png': 'optim', 'TSE_2026_400mm_DHS.png': 'optim3', 'TSE_2026_200mm_DHS.png': 'optim3'}
NOMS = {'TSE2026_Trigaza_800mm.png': 'Brno 800 mm Trigaza alineada', 'TSE_2026_530mm_DHS.png': 'Brno 530 mm DHS alineada',
        'TSE_2026_400mm_DHS.png': 'Brno 400 mm DHS alineada', 'TSE_2026_200mm_DHS.png': 'Brno 200 mm DHS alineada'}
M_sRGB_XYZ = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
M_XYZ_ARGB = np.array([[2.0413690, -0.5649464, -0.3446944], [-0.9692660, 1.8760108, 0.0415560], [0.0134474, -0.1183897, 1.0154096]])
M_sRGB_ARGB = M_XYZ_ARGB @ M_sRGB_XYZ
GAMMA_ARGB = 563.0 / 256.0

def srgb_a_lineal(c): return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)

def a_adobe16(rgb8):
    lin = srgb_a_lineal(rgb8.astype(np.float64) / 255.0)
    argb = np.clip(lin @ M_sRGB_ARGB.T, 0, 1) ** (1.0 / GAMMA_ARGB)
    return np.round(argb * 65535).astype(np.uint16)

def capa(nom):
    g = GEO[nom]; f0, f1, c0, c1 = g['marc']; o = J['imatges'][nom][TRIA[nom]]; A = np.asarray(o['A_png_a_v'], np.float64)
    im = np.asarray(Image.open(f'{BRNO}/{nom}').convert('RGB')); H, W = im.shape[:2]
    rgb16 = a_adobe16(im).astype(np.float32); alfa = np.zeros((H, W), np.float32); alfa[f0:f1, c0:c1] = 1.0
    # caixa: contorn del contingut transformat, retallat al llenç
    cants = np.array([[c0, f0, 1], [c1, f0, 1], [c0, f1, 1], [c1, f1, 1]], np.float64) @ A.T
    x0, y0 = np.floor(cants.min(axis=0)).astype(int); x1, y1 = np.ceil(cants.max(axis=0)).astype(int)
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, FW), min(y1, FH)
    Ab = A.copy(); Ab[0, 2] -= x0; Ab[1, 2] -= y0           # origen de la caixa
    out = np.zeros((y1 - y0, x1 - x0, 3), np.float32)
    for k in range(3): out[..., k] = cv2.warpAffine(rgb16[..., k], Ab, (x1 - x0, y1 - y0), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    al = cv2.warpAffine(alfa, Ab, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    rgb = np.clip(np.round(out), 0, 65535).astype(np.uint16); a16 = np.clip(np.round(al * 65535), 0, 65535).astype(np.uint16)
    rgb[a16 == 0] = 0
    np.savez(f'{S}/capa_{nom[:-4]}.npz', R=rgb[..., 0], G=rgb[..., 1], B=rgb[..., 2], A=a16, bbox=np.array([x0, y0, x1, y1]))
    return dict(nom=NOMS[nom], bbox=[int(x0), int(y0), int(x1), int(y1)], escala=o['escala'], gir_deg=o['gir_deg'], sol_v=o['sol_v'], tria=TRIA[nom], corr=o['corr'], px_opacs=int((a16 == 65535).sum()))

def vistes(nom, rebut):
    """Comprovació visual: retall 3600×3600 al voltant del Sol, escaquer 300 px base V81 / Brno alineada, i parella."""
    z = np.load(f'{S}/capa_{nom[:-4]}.npz'); x0, y0, x1, y1 = z['bbox']; base = np.load(S + '/v81_base_lum.npy')
    sx, sy = J['SUN_V']; cx, cy = int(round(sx)), int(round(sy)); r = 1800
    B = base[cy - r:cy + r, cx - r:cx + r]; Bn = np.clip((B - np.percentile(B, 1)) / (np.percentile(B, 99.5) - np.percentile(B, 1)), 0, 1)
    K = np.zeros((FH, FW), np.float32); lum = (z['R'].astype(np.float32) + 2 * z['G'] + z['B']) / (4 * 65535.0); K[y0:y1, x0:x1] = np.where(z['A'] > 0, lum, 0)
    Kc = K[cy - r:cy + r, cx - r:cx + r]; Kn = np.clip((Kc - np.percentile(Kc[Kc > 0], 1)) / (np.percentile(Kc[Kc > 0], 99.5) - np.percentile(Kc[Kc > 0], 1)), 0, 1)
    yy, xx = np.mgrid[0:2 * r, 0:2 * r]; esc = ((xx // 300 + yy // 300) % 2) == 0
    E = np.where(esc, Bn, Kn); pare = np.hstack([Bn, Kn])
    Image.fromarray((E[::2, ::2] * 255).astype(np.uint8)).save(f'{S}/vista_escaquer_{nom[:-4]}.png')
    Image.fromarray((pare[::3, ::3] * 255).astype(np.uint8)).save(f'{S}/vista_parella_{nom[:-4]}.png')

if __name__ == '__main__':
    t0 = time.time(); rebut = {}
    for nom in TRIA:
        t1 = time.time(); rebut[nom] = capa(nom); print(nom, rebut[nom], f'[{time.time()-t1:.0f}s]', flush=True); vistes(nom, rebut)
    json.dump(rebut, open(S + '/capes_v82.json', 'w'), indent=1, ensure_ascii=False); print(f'fet ({time.time()-t0:.0f}s)')
