"""m4 · El solc de cada traç a CADA ETAPA de la cadena (geometria fina M3), amb un filtre adaptat i un control nul.
Per a cada font 2D: r = gauss(σa)/gauss(σb) − 1 (normalitzat per la dada vàlida); mitjana de r al llarg del traç a t = 0 (el solc) i a 60 desplaçaments
paral·lels nuls (|t| = 120…600 px); z = (solc − mediana nul) / MAD nul. Dues bandes: fina (σ 4/40) i ampla (σ 16/160).
Fonts: compost V107, capes de la V107 (base 3 i filtres 41–56), linealitzada E (base_G, fusion_starless G, sony/vixen starless G), d4 base_G,
b3 V98 (fusion_total G, sony_corrected G, sony_A_corr G), apilats per tren (Sony A, Sony B, Vixen comuna; G), pesos (fA, wv).
Sortida: M4_ETAPES.json."""
import sys, json, struct
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_marrons import *
g = json.loads((OUT / 'M3_GEOMETRIA.json').read_text())
for tr in TRACOS:
    z = g[str(tr['k'])]; tr['centre'] = np.array(z['centre']); tr['d'] = np.array(z['direccio']); tr['n'] = np.array([-tr['d'][1], tr['d'][0]])
R97 = ARREL / '4-RESULTATS/v97_refundacio_20260924'; CR = R97 / 'cadena_raw'; B3 = ARREL / '4-RESULTATS/v98_20260925/cadena_v98/b3/cau'
LE = ARREL / '4-RESULTATS/v103_banda_20260926/E/lineal_v103'; ES = ARREL / '4-RESULTATS/v105_limbe_20260926/claude/estat_v105'
FONTS = {'V107_compost': 'psb', 'L3_base_V107': (ES / 'L3_RGB.npy', 1)}
for lid in (54, 41, 42, 47, 49, 51, 45, 46, 55, 56): FONTS[f'L{lid}'] = (ES / f'L{lid}_G.npy', None)
FONTS.update({'E_base_G': (LE / 'base_G.npy', None), 'E_fusion_starless_G': (LE / 'fusion_starless.npy', 1), 'E_sony_starless_G': (LE / 'sony_starless.npy', 1), 'E_vixen_starless_G': (LE / 'vixen_starless.npy', 1),
              'd4_base_G': (ARREL / '4-RESULTATS/v98_20260925/cadena_v98/d4/products/sources/base_G.npy', None),
              'b3_fusion_total_G': (B3 / 'fusion_total_v42.npy', 1), 'b3_sony_corrected_G': (B3 / 'sony_corrected_total_v42.npy', 1), 'b3_sony_A_corr_G': (B3 / 'sony_A_corr_v42.npy', 1),
              'apilat_sony_A_G': (CR / 'b2_sony_A/cau/sony_A_total_v36.npy', 1), 'apilat_sony_B_G': (CR / 'b2_sony_B/cau/sony_B_total_v42.npy', 1),
              'apilat_vixen_comuna_G': (R97 / 'proves_apilat/vixen_comuna_taula_original/vixen_total.npy', 1),
              'pes_fA': (B3 / 'sony_fA_v42.npy', None), 'pes_wv': (B3 / 'weight_vixen_v42.npy', None)})
psb = ARREL / '1-PHOTOSHOP/V107.psb'
with open(psb, 'rb') as fh:
    hdr = fh.read(26); nch = struct.unpack('>H', hdr[12:14])[0]
    n = struct.unpack('>I', fh.read(4))[0]; fh.seek(n, 1); n = struct.unpack('>I', fh.read(4))[0]; fh.seek(n, 1); n = struct.unpack('>Q', fh.read(8))[0]; fh.seek(n, 1); pos = fh.tell()
MM = np.memmap(psb, dtype='>u2', mode='r', offset=pos + 2, shape=(nch, H, W))
NUL = np.concatenate([np.arange(-600, -119, 16), np.arange(120, 601, 16)]).astype(float)
def llegeix(nom, box):
    x0, y0, x1, y1 = box; f = FONTS[nom]
    if f == 'psb': return sum(np.asarray(MM[c, y0:y1, x0:x1], np.float32) for c in range(3)) / 3
    p, ch = f; a = np.load(p, mmap_mode='r'); a = a[y0:y1, x0:x1] if ch is None else a[y0:y1, x0:x1, ch]
    return np.asarray(a, np.float32)
res = {}
for tr in TRACOS:
    box = caixa(tr, 700); res[tr['k']] = {'nom': tr['nom']}
    for nom in FONTS:
        img = llegeix(nom, box); es_pes = nom.startswith('pes_')
        m = np.isfinite(img) & ((img > 0) if not es_pes else np.ones_like(img, bool)); w = m.astype(np.float32); img = np.where(m, img, 0)
        ng = lambda x, s: cv2.GaussianBlur(x * w, (0, 0), s) / np.maximum(cv2.GaussianBlur(w, (0, 0), s), 1e-6)
        row = {}
        for banda, (sa, sb) in (('fina', (4, 40)), ('ampla', (16, 160))):
            if es_pes: r = ng(img, sa) - ng(img, sb)
            else: r = ng(img, sa) / np.maximum(ng(img, sb), 1e-12) - 1
            r = np.where(m, r, np.nan).astype(np.float32)
            vals = []
            for t0 in np.concatenate([[0.0], NUL]):
                s, t, X, Y = graella(tr, tmax=0, dt=1, ds=2, dt0=t0); P = mostreja(r, X, Y, box[:2]); vals.append(np.nanmean(P) if np.isfinite(P).sum() > 20 else np.nan)
            vals = np.array(vals); nul = vals[1:][np.isfinite(vals[1:])]
            med = float(np.median(nul)); mad = float(1.4826 * np.median(np.abs(nul - med)) + 1e-15)
            row[banda] = dict(solc=float(vals[0]), nul_mediana=med, nul_mad=mad, z=float((vals[0] - med) / mad))
        # perfil ample (mediana al llarg) per a la forma
        if not es_pes:
            t, pr = perfil(np.where(m, img, np.nan).astype(np.float32), tr, box[:2], tmax=400, dt=2, ds=2)
            row['perfil_solc'] = solc(t, pr, fin=(-30, 30), flancs=(100, 390))
        res[tr['k']][nom] = row
        print(f"T{tr['k']} {nom:24s} fina {row['fina']['solc']:+.5f} z {row['fina']['z']:+6.1f} | ampla {row['ampla']['solc']:+.5f} z {row['ampla']['z']:+6.1f}", flush=True)
desa(OUT / 'M4_ETAPES.json', dict(geometria='M3 (P04 WOW)', fonts={k: (str(v[0].relative_to(ARREL)) if isinstance(v, tuple) else v) for k, v in FONTS.items()}, tracos=res))
