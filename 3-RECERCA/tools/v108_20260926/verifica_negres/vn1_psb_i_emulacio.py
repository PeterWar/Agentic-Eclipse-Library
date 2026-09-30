"""vn1 (V108 · verificador adversari de «negres»). Refà, amb una mètrica PRÒPIA, la mesura de les zones negres:
 (1) al compost FUSIONAT del PSB V107 (el que Pere veu, amb capes d'ajust), llegit directament del fitxer (memmap, només lectura);
 (2) a la pila emulada (compositor jutge_comu.comp via comu_negres.Pila) per a V107, sense 41, sense 41+42, i amb el candidat CEL_TER_Q;
 (3) una aproximació independent de l'emulació: fusionat PSB × F_nou/F_vell, amb F = factor de Multiplicar de 41·42 calculat amb el ràster,
     l'alfa, la màscara i l'opacitat llegits DIRECTAMENT del PSB amb psb69 (no de l'estat extret per l'agent).
Mètrica pròpia (diferent implementació, i variants de sensibilitat):
  cel de referència = mediana per sector angular (Nsec) a la corona de cel [ra, rb] R☉, SENSE suavitzat entre sectors, interpolada circularment;
  zona negra = L suavitzada (gaussiana σ s px del llenç) < cel suavitzat del sector, a 1,3–4,5 R☉, dins del marc final, fora de la Lluna+3 px.
Sortida: 4-RESULTATS/v108_20260926/verifica_negres/VN1.json"""
import sys, json, struct, time
from pathlib import Path
import numpy as np, cv2
R0 = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(R0 / '3-RECERCA/tools/v108_20260926/negres'))
sys.path.insert(0, str(R0 / '3-RECERCA/tools/v73_marques_v71_20260917'))
from comu_negres import Pila, W, H, SOL, RSOL, LLUNA, RLLUNA, MARC, FILTRES
from psb69 import PSB
OUT = R0 / '4-RESULTATS/v108_20260926/verifica_negres'; OUT.mkdir(parents=True, exist_ok=True)
PAS = 2; PSBP = R0 / '1-PHOTOSHOP/V107.psb'
CAND = R0 / '4-RESULTATS/v108_20260926/negres/candidats/CEL_TER_Q'
ORIG = R0 / '4-RESULTATS/v103_banda_20260926/E/filtres_v103/filtres'
yy, xx = np.mgrid[0:H:PAS, 0:W:PAS].astype(np.float32)
r = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL; th = np.degrees(np.arctan2(-(yy - SOL[1]), xx - SOL[0])) % 360
lluna = np.hypot(xx - LLUNA[0], yy - LLUNA[1]) < RLLUNA + 3
marc = (xx >= MARC[0]) & (xx < MARC[2]) & (yy >= MARC[1]) & (yy < MARC[3]); del xx, yy


def lum(C): return (C[..., 0] + 2 * C[..., 1] + C[..., 2]) / 4


def fusionat():
    with open(PSBP, 'rb') as f:
        hdr = f.read(26); nch = struct.unpack('>H', hdr[12:14])[0]
        for _ in range(2):
            n = struct.unpack('>I', f.read(4))[0]; f.seek(n, 1)
        n = struct.unpack('>Q', f.read(8))[0]; f.seek(n, 1); pos = f.tell(); c = struct.unpack('>H', f.read(2))[0]
    assert c == 0
    mm = np.memmap(PSBP, dtype='>u2', mode='r', offset=pos + 2, shape=(nch, H, W))
    return lum(np.stack([np.asarray(mm[k, ::PAS, ::PAS], np.float32) / 65535 for k in range(3)], -1))


def cel_sector(L, valid, nsec, ra, rb):
    s = valid & (r >= ra) & (r < rb) & (L > 1e-4); sec = (th * nsec / 360).astype(int) % nsec
    v = np.array([np.median(L[s & (sec == i)]) if (s & (sec == i)).sum() > 200 else np.nan for i in range(nsec)])
    good = ~np.isnan(v); idx = np.arange(nsec); v = np.interp(idx, idx[good], v[good], period=nsec)
    x = th * nsec / 360 - 0.5; i0 = np.floor(x).astype(int) % nsec; f = (x - np.floor(x)).astype(np.float32)
    return v, ((1 - f) * v[i0] + f * v[(i0 + 1) % nsec]).astype(np.float32), int(good.sum())


VALID_CEL = ~lluna   # el cel de referència pot sortir del marc (a dalt i a baix, 6,5 R☉ és fora del marc final)
METRIQUES = {'M_ref(36s,6.5-8.5,s6)': (36, 6.5, 8.5, 6.0, VALID_CEL), 'M_72s': (72, 6.5, 8.5, 6.0, VALID_CEL), 'M_s12': (36, 6.5, 8.5, 12.0, VALID_CEL),
             'M_cel7-8.5': (36, 7.0, 8.5, 6.0, VALID_CEL), 'M_cel_dins_marc_5-5.6': (36, 5.0, 5.6, 6.0, marc & ~lluna)}
ZONA = marc & ~lluna & (r >= 1.3) & (r < 4.5)


def mesura(L):
    out = {}; valid_img = L > 1e-4
    for nom, (ns, ra, rb, s, vc) in METRIQUES.items():
        Ls = cv2.GaussianBlur(L, (0, 0), s / PAS); cv, sky, ng = cel_sector(Ls, vc & valid_img, ns, ra, rb)
        z = ZONA & valid_img; neg = z & (Ls < sky)
        d = dict(total=float(neg.sum() / z.sum()), cel_max_min=float(cv.max() / cv.min()), sectors_amb_cel=ng)
        for a, b in ((1.3, 2), (2, 3), (3, 4.5)):
            m = z & (r >= a) & (r < b); d[f'{a:g}-{b:g}'] = float(neg[m].sum() / m.sum())
        m = z & (th >= 45) & (th < 90); d['sector_45-90'] = float(neg[m].sum() / m.sum())
        out[nom] = d
    # píxel a píxel (sense suavitzar) amb el cel de referència
    cv, sky, _ = cel_sector(L, VALID_CEL & valid_img, 36, 6.5, 8.5); z = ZONA & valid_img
    out['pixel_a_pixel'] = float((L[z] < sky[z]).mean())
    return out


def factor_4142_psb(psb, cand=None):
    """F = Π (1 − o·α·m·(1 − u)) per a 41 i 42, a pas 2, amb el ràster del PSB o el del candidat."""
    F = np.ones(r.shape, np.float32); info = {}
    for lid, tag in ((41, 'P01_NRGF'), (42, 'P01_NRGF_extrap')):
        l = psb.layer(lid); o = l['opacity'] / 255; box = (0, 0, W, H)
        g = psb.channel_box(lid, 1, box)[::PAS, ::PAS].astype(np.float32) / 65535
        al = psb.channel_box(lid, -1, box)[::PAS, ::PAS].astype(np.float32) / 65535
        mk = l['mask']; mm_ = psb.channel_box(lid, -2, box, fill=65535 if mk['background'] == 255 else 0)
        mm_ = np.ones_like(g) if mm_ is None else mm_[::PAS, ::PAS].astype(np.float32) / 65535
        if cand is not None:
            g2 = np.load(cand / f'{tag}_u16.npy', mmap_mode='r')[::PAS, ::PAS].astype(np.float32) / 65535
        else: g2 = g
        orig = np.load(ORIG / f'{tag}_u16.npy', mmap_mode='r')[::PAS, ::PAS].astype(np.float32) / 65535
        info[lid] = dict(opacitat=l['opacity'], mode=l['blend'], max_dif_psb_vs_filtres_v103=float(np.abs(g - orig).max() * 65535),
                         mascara_mitjana_zona=float(mm_[ZONA].mean()))
        F *= 1 - o * al * mm_ * (1 - g2)
    return F, info


if __name__ == '__main__':
    T = time.time(); res = {}
    Lf = fusionat(); res['PSB_fusionat_V107'] = mesura(Lf); print('fusionat', json.dumps(res['PSB_fusionat_V107']['M_ref(36s,6.5-8.5,s6)']), flush=True)
    psb = PSB(str(PSBP))
    F0, inf0 = factor_4142_psb(psb); F1, _ = factor_4142_psb(psb, CAND); res['capes_psb'] = inf0
    Lap = Lf * F1 / np.maximum(F0, 1e-4); res['PSB_fusionat_x_Fnou_sobre_Fvell_CEL_TER_Q'] = mesura(Lap)
    Lno = Lf / np.maximum(F0, 1e-4); res['PSB_fusionat_sense_41_42_aprox'] = mesura(Lno)
    print('aprox CTQ', json.dumps(res['PSB_fusionat_x_Fnou_sobre_Fvell_CEL_TER_Q']['M_ref(36s,6.5-8.5,s6)']), flush=True)
    del psb
    P = Pila((0, 0, W, H), PAS)
    V = {'emul_V107': {}, 'emul_sense41': {41: 'oculta'}, 'emul_sense41_42': {41: 'oculta', 42: 'oculta'}, 'emul_sense56': {56: 'oculta'},
         'emul_sense_filtres': {k: 'oculta' for k in FILTRES},
         'emul_CEL_TER_Q': {41: {'F': str(CAND / 'P01_NRGF_u16.npy')}, 42: {'F': str(CAND / 'P01_NRGF_extrap_u16.npy')}}}
    REG = OUT / 'regen/CEL_Q'
    if (REG / 'P01_NRGF_u16.npy').exists():
        V['emul_CEL_Q_sol'] = {41: {'F': str(REG / 'P01_NRGF_u16.npy')}, 42: {'F': str(REG / 'P01_NRGF_extrap_u16.npy')}}
    for nom, esp in V.items():
        L = P.compon(esp); res[nom] = mesura(L)
        if nom == 'emul_V107':
            m = ZONA & (Lf > 1e-4)
            res['emul_vs_fusionat'] = dict(corr_lnL=float(np.corrcoef(np.log(np.maximum(L[m], 1e-3)), np.log(np.maximum(Lf[m], 1e-3)))[0, 1]),
                                           quocient_mediana=float(np.median(Lf[m] / np.maximum(L[m], 1e-4))))
            np.save(OUT / 'L_emul_V107_pas2.npy', L)
        if nom == 'emul_CEL_TER_Q': np.save(OUT / 'L_emul_CEL_TER_Q_pas2.npy', L)
        print(nom, json.dumps(res[nom]['M_ref(36s,6.5-8.5,s6)']), res[nom]['pixel_a_pixel'], flush=True)
    res['segons'] = round(time.time() - T)
    (OUT / 'VN1.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n'); print('FET')
