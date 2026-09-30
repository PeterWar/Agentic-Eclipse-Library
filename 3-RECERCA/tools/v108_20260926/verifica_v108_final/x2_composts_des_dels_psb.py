"""x2 (verificador adversari de la V108 final, 27-09) · Composts PROPIS llegits directament dels PSB (V107.psb de Pere i V108_stage.psb),
amb els ràsters QUANTITZATS que hi ha al fitxer, l'alfa (−1) i la màscara (−2) de cada capa amb la seva caixa i el seu fons, i l'opacitat.
Compositor escrit de nou (fórmules W3C/Photoshop: B(Cb, Cs) + barreja per alfa), sense fer servir jutge_comu ni l'estat de la cadena.
  C1  = base 3 + filtres visibles 54, 41, 42, 47, 49, 51, 45, 46, 55, 56 → mitjana RGB (llenç sencer, float32)
  PLE = C1 + 305, 306, 258, 76, 224, 267 (les visibles ràster per sota de les capes d'ajust 239–244) → L = (R + 2G + B)/4 (llenç sencer)
L'ordre i la visibilitat es llegeixen del PSB i s'assereix que coincideixen amb aquesta llista.
Sortida: 4-RESULTATS/v108_20260926/verifica_v108_final/composts/{C1,L}_{V107,V108}.npy i X2_COMPOSTS.json (amb la comparació contra els
composts de v108_final). Només lectura de la resta."""
import sys, json, time
from pathlib import Path
import numpy as np
R0 = Path('/Users/USUARI/Desktop/Eclipse 2026')
sys.path.insert(0, str(R0 / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB  # noqa: E402
OUT = R0 / '4-RESULTATS/v108_20260926/verifica_v108_final'; CO = OUT / 'composts'; CO.mkdir(parents=True, exist_ok=True)
FONTS = {'V107': R0 / '1-PHOTOSHOP/V107.psb', 'V108': R0 / '4-RESULTATS/v108_20260926/cadena/v108/V108_stage.psb'}
C1L = [3, 54, 41, 42, 47, 49, 51, 45, 46, 55, 56]; DALT = [305, 306, 258, 76, 224, 267]
W, H = 10551, 7506; T0 = time.time(); rep = {}


def canvas(p, lid, cid, fill):
    """Canal col·locat al llenç (fora de la seva caixa, `fill`)."""
    a, (x, y) = p.channel(lid, cid); out = np.full((H, W), fill, np.uint16)
    h, w = a.shape; xa, ya, xb, yb = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if xb > xa and yb > ya: out[ya:yb, xa:xb] = a[ya - y:yb - y, xa - x:xb - x]
    return out


def blend(mode, Cb, Cs):
    if mode == 'NORMAL': return Cs
    if mode == 'MULTIPLY': return Cb * Cs
    if mode == 'OVERLAY': return np.where(Cb <= 0.5, 2 * Cb * Cs, 1 - 2 * (1 - Cb) * (1 - Cs))
    if mode == 'LIGHTEN': return np.maximum(Cb, Cs)
    if mode == 'LINEAR_DODGE': return np.minimum(Cb + Cs, 1)
    raise ValueError(mode)


for nom, path in FONTS.items():
    t = time.time(); p = PSB(str(path)); ordre = [L['id'] for L in p.layers]
    vis = [L['id'] for L in p.layers if L['visible']]
    pila = [l for l in vis if l in C1L + DALT]
    assert pila == C1L + DALT, pila
    primer_ajust = ordre.index(239); assert all(ordre.index(l) < primer_ajust for l in pila)
    # cap altra capa visible per sota de 239 que no sigui a la pila
    assert [l for l in vis if ordre.index(l) < primer_ajust and l not in pila] == [], 'capes visibles oblidades'
    CAP = {}
    for lid in C1L + DALT:
        L = p.layer(lid); gris = lid in range(41, 57)
        if gris: rgb = canvas(p, lid, 1, 0)
        else: rgb = np.stack([canvas(p, lid, k, 0) for k in (0, 1, 2)], -1)
        a = canvas(p, lid, -1, 0)
        if -2 in L['chans'] and L['mask'] is not None and not L['mask']['disabled']:
            m = canvas(p, lid, -2, 65535 if L['mask']['background'] == 255 else 0)
        else: m = None
        CAP[lid] = dict(mode=L['blend'], op=L['opacity'] / 255, rgb=rgb, a=a, m=m, gris=gris)
    rep.setdefault('pila', {})[nom] = {str(l): dict(mode=CAP[l]['mode'], opacitat=p.layer(l)['opacity'], mascara=CAP[l]['m'] is not None) for l in C1L + DALT}
    c1 = np.lib.format.open_memmap(CO / f'C1_{nom}.npy', 'w+', np.float32, (H, W))
    lp = np.lib.format.open_memmap(CO / f'L_{nom}.npy', 'w+', np.float32, (H, W))
    for y0 in range(0, H, 400):
        y1 = min(H, y0 + 400); Cb = np.zeros((y1 - y0, W, 3), np.float64); ab = np.zeros((y1 - y0, W), np.float64)
        for lid in C1L + DALT:
            c = CAP[lid]; Cs = c['rgb'][y0:y1].astype(np.float64) / 65535
            if c['gris']: Cs = np.repeat(Cs[..., None], 3, -1)
            a = c['a'][y0:y1].astype(np.float64) / 65535 * c['op']
            if c['m'] is not None: a = a * (c['m'][y0:y1].astype(np.float64) / 65535)
            B = blend(c['mode'], Cb, Cs); Csp = (1 - ab[..., None]) * Cs + ab[..., None] * B
            ao = a + ab * (1 - a); num = a[..., None] * Csp + ((1 - a) * ab)[..., None] * Cb
            Cb = np.where(ao[..., None] > 0, num / np.where(ao > 0, ao, 1)[..., None], 0); ab = ao
            if lid == 56: c1[y0:y1] = Cb.mean(-1).astype(np.float32)
        lp[y0:y1] = ((Cb[..., 0] + 2 * Cb[..., 1] + Cb[..., 2]) / 4).astype(np.float32)
    c1.flush(); lp.flush(); del c1, lp, CAP
    print(nom, 'compost', round(time.time() - t), 's', flush=True)

# comparació amb els composts de v108_final (els que ha fet servir el verificat)
VF = R0 / '4-RESULTATS/v108_20260926/v108_final/composts'; cmp = {}
for nom in ('V107', 'V108'):
    for k in ('C1', 'L'):
        a = np.load(CO / f'{k}_{nom}.npy', mmap_mode='r'); b = np.load(VF / f'{k}_{nom}.npy', mmap_mode='r'); mx = 0.0; qs = []
        for y0 in range(0, H, 1000):
            A = np.asarray(a[y0:y0 + 1000], np.float64); Bb = np.asarray(b[y0:y0 + 1000], np.float64)
            mx = max(mx, float(np.abs(A - Bb).max())); m = (A > 1e-3) & (Bb > 1e-3); qs.append((A[m] / Bb[m])[::17])
        qs = np.concatenate(qs)
        cmp[f'{k}_{nom}'] = dict(max_abs=mx, quocient_p0_01_p50_p99_99=[float(x) for x in np.percentile(qs, [0.01, 50, 99.99])])
rep['contra_v108_final'] = cmp; rep['segons'] = round(time.time() - T0)
(OUT / 'X2_COMPOSTS.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1) + '\n'); print(json.dumps(cmp, indent=1))
