"""m0 (V108 · v108_final) · Els quatre composts emulats de la pila de la V107 (modes, opacitats, alfes i màscares de Pere llegits de la V107;
sense capes d'ajust), a resolució plena, i les proves de bit de la tirada v108.

LES QUATRE PILES (els ràsters de la base 3 i dels filtres visibles 54, 41, 42, 47, 49, 51, 45, 46, 55, 56):
  V107 = l'estat de la cadena de control (cadena/control/estat_v108), que reprodueix la V107 byte a byte (C8 del control: cap capa canvia);
  V108 = l'estat de la variant v108 (flat 2D v5 + genoll CEL_G_MAX_T_e30_W_H0 a la 41/42): el que b2 ha muntat al PSB de pas;
  F    = flat2d_v5 sol: l'estat de la V108 amb la 41/42 de la cadena estàndard de la mateixa variant (L_G + std − ganxo). Com que el ganxo
         és bit a bit l'estàndard dins de la Lluna (on r3 toca la 41/42), això refà l'estat de flat2d_v5: es comprova amb el SHA de
         L41_G/L42_G de flat2d_v5 que hi ha al manifest de la Paperera i amb el compost c1 contra flat2d_v5/compost_flat2d_v5.npy;
  N    = negres_v2 sol: l'estat de control amb la 41/42 del candidat de negres_v2 (L_G + candidat − std del control), com a1_avalua.combinat.
DUES SORTIDES PER PILA, en una sola passada per franges de 500 files:
  C1  = mitjana RGB de la base + els 10 filtres (exactament la de flat2d_v2/c1_compost_v107_mascares.py, la de les rondes del flat 2D:
        alfa efectiva = alfa × màscara de la V107 de la memòria cau del pilot) → comprovat contra flat2d_v2/compost_control.npy (V107)
        i flat2d_v5/compost_flat2d_v5.npy (F);
  PLE = + les capes ràster de sobre 305, 306, 258, 76, 224, 267 (alfa efectiva de l'estat de la V107, extret del PSB), fins a la 239
        exclosa (la pila de comu_negres.Pila, la de les rondes de les zones negres) → L = (R + 2G + B)/4 a pas 1 i RGB a pas 2;
        comprovat a pas 2 contra negres_v2/pas2/L_V107.npy i L_v4_CEL_G_MAX_T_e30_W_H0.npy (aquelles fan servir els ràsters quantitzats del PSB).
PROVES DE BIT (SHA-256 contra el manifest de la Paperera de flat2d_v5, que té el SHA de cada fitxer de l'estat, la base i els filtres de la v5):
  base, filtres estàndard i estat de la V108 = els de flat2d_v5 (tret de L41_G i L42_G, que han de canviar); F41/F42 refets = els de flat2d_v5;
  alfes dels filtres visibles de V108, F i N = les del control (= V107).
Ús: m0_composts_v108.py   Sortida: 4-RESULTATS/v108_20260926/v108_final/composts/ i M0_COMPOSTS.json. Només lectura de tota la resta."""
import sys, json, time, hashlib, io, resource
from pathlib import Path
import numpy as np
R0 = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(R0 / '3-RECERCA/tools/v97_refundacio_20260924'))
from jutge_comu import comp, Estat, W, H   # noqa: E402  (el compositor de sempre; només lectura)
V8R = R0 / '4-RESULTATS/v108_20260926'
OUT = V8R / 'v108_final'; CO = OUT / 'composts'; CO.mkdir(parents=True, exist_ok=True)
CTL = V8R / 'cadena/control'; V8 = V8R / 'cadena/v108'
CAND = V8R / 'negres_v2/candidats_v4/CEL_G_MAX_T_e30_W_H0'
E107 = Estat(V8R / 'negres/estat_v107')                 # modes, opacitats, visibilitat i capes de sobre de la V107 (extret del PSB)
CAU = V8R / 'marrons/pilot/tmp_mascares_v107'            # alfa × màscara de la V107 (la memòria cau que fa servir c1)
MANI = V8R / 'flat2d_v5/MOVIMENTS_PAPERERA_FLAT2D_V5.jsonl'
FILTRES = (54, 41, 42, 47, 49, 51, 45, 46, 55, 56); DALT = (305, 306, 258, 76, 224, 267)
TAG = {41: 'P01_NRGF', 42: 'P01_NRGF_extrap'}
T0 = time.time(); rep = dict(guio=str(Path(__file__).relative_to(R0)), data=time.strftime('%F %T'))
ordre = [l for l in E107.ordre if l in (3,) + FILTRES + DALT]
assert ordre == [3, 54, 41, 42, 47, 49, 51, 45, 46, 55, 56, 305, 306, 258, 76, 224, 267], ordre
assert all(E107.capes[l]['visible'] for l in ordre)
rep['pila'] = {str(l): dict(nom=E107.capes[l]['nom'], mode=E107.capes[l]['mode'], opacitat=E107.capes[l]['opacitat']) for l in ordre}


def sha_fitxer(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(64 << 20), b''): h.update(b)
    return h.hexdigest()


def sha_npy(a):
    b = io.BytesIO(); np.save(b, a); return hashlib.sha256(b.getvalue()).hexdigest()


# ---------------------------------------------------------------- proves de bit contra flat2d_v5 (manifest de la Paperera)
man = {}
for l in open(MANI):
    d = json.loads(l); k = d['de'].split('cadena/flat2d_v5/')[-1]; man[k] = d['sha256']
bits = {}
for k in ['base/base_v108_final_u16.npy', 'base/base_v108_u16.npy'] + [f'filtres_std/filtres/{f.name}' for f in sorted((V8 / 'filtres_std/filtres').glob('*.npy'))] \
        + [f'estat_v108/{f.name}' for f in sorted((V8 / 'estat_v108').glob('L*.npy'))]:
    if k not in man: bits[k] = 'sense SHA al manifest'; continue
    s = sha_fitxer(V8 / k); bits[k] = 'igual' if s == man[k] else f'DIFERENT ({s[:16]} ≠ {man[k][:16]})'
dif = {k: v for k, v in bits.items() if v != 'igual'}
rep['bits_v108_contra_flat2d_v5'] = dict(fitxers_comparats=len(bits), iguals=sum(v == 'igual' for v in bits.values()), diferents_o_sense_sha=dif)
print('bits v108 contra flat2d_v5:', rep['bits_v108_contra_flat2d_v5']['iguals'], 'iguals de', len(bits), '· la resta:', dif, flush=True)
F5 = V8R / 'cadena/flat2d_v5'   # el que en queda a disc (lineal i franja)
rep['bits_v108_contra_flat2d_v5_a_disc'] = {k: ('igual' if sha_fitxer(V8 / k) == sha_fitxer(F5 / k) else 'DIFERENT') for k in ('lineal/base_G.npy', 'lineal/fusion_starless.npy')}
_a, _b = np.load(V8 / 'franja/A3C_franja_silueta.npz'), np.load(F5 / 'franja/A3C_franja_silueta.npz')
_dif = [k for k in _b.files if k not in _a.files or _a[k].tobytes() != _b[k].tobytes() or _a[k].dtype != _b[k].dtype]
rep['bits_v108_contra_flat2d_v5_a_disc']['franja/A3C_franja_silueta.npz (clau a clau)'] = 'igual' if not _dif else f'DIFERENT: {_dif}'
print('a disc:', rep['bits_v108_contra_flat2d_v5_a_disc'], flush=True)
rep['base_control_diferent_de_la_v108'] =sha_fitxer(CTL / 'base/base_v108_final_u16.npy') != sha_fitxer(V8 / 'base/base_v108_final_u16.npy')
org ={l.split('\t')[0]: l.rstrip('\n').split('\t')[2] for l in open(V8 / 'filtres_v108/ORIGEN.tsv').readlines()[1:]}
rep['origen_filtres_v108'] = org
assert 'filtres_alt' in org['41'] and 'filtres_alt' in org['42'], org


def ld(p): return np.load(p, mmap_mode='r')


def suma(base, mes, menys):
    """uint16: clip(base + mes − menys), per franges."""
    out = np.empty((H, W), np.uint16)
    for y0 in range(0, H, 1000):
        s = slice(y0, y0 + 1000)
        out[s] = np.clip(np.asarray(base[s], np.int32) + np.asarray(mes[s], np.int32) - np.asarray(menys[s], np.int32), 0, 65535)
    return out


GANXO = {41: R0 / org['41'], 42: R0 / org['42']}
F41 = suma(ld(V8 / 'estat_v108/L41_G.npy'), ld(V8 / f'filtres_std/filtres/{TAG[41]}_u16.npy'), ld(GANXO[41]))
F42 = suma(ld(V8 / 'estat_v108/L42_G.npy'), ld(V8 / f'filtres_std/filtres/{TAG[42]}_u16.npy'), ld(GANXO[42]))
rep['F_41_42_refets'] = {f'L{lid}_G': ('igual al de flat2d_v5' if sha_npy(a) == man[f'estat_v108/L{lid}_G.npy'] else 'DIFERENT del de flat2d_v5') for lid, a in ((41, F41), (42, F42))}
print('F refet:', rep['F_41_42_refets'], flush=True)
N41 = suma(ld(CTL / 'estat_v108/L41_G.npy'), ld(CAND / f'{TAG[41]}_u16.npy'), ld(CTL / f'filtres_std/filtres/{TAG[41]}_u16.npy'))
N42 = suma(ld(CTL / 'estat_v108/L42_G.npy'), ld(CAND / f'{TAG[42]}_u16.npy'), ld(CTL / f'filtres_std/filtres/{TAG[42]}_u16.npy'))
# el delta del genoll dins de 40 px del limbe (on hauria de ser nul) i dins de la Lluna (on r3 toca la 41/42), a la v108 i al candidat
yy, xx = np.ogrid[:H, :W]; DL = (np.hypot(xx - 5375.786804312011, yy - 3775.9774911631) - 452.9785129274736).astype(np.float32); del yy, xx
for nom, g, s in (('v108', GANXO[41], V8 / 'filtres_std/filtres/P01_NRGF_u16.npy'), ('negres_v2', CAND / 'P01_NRGF_u16.npy', CTL / 'filtres_std/filtres/P01_NRGF_u16.npy')):
    d = np.asarray(ld(g), np.int32) - np.asarray(ld(s), np.int32)
    rep.setdefault('genoll_41_dins_del_limbe', {})[nom] = dict(px_diferents_dins_lluna=int((d[DL < 0] != 0).sum()), px_diferents_0_40px=int((d[(DL >= 0) & (DL < 40)] != 0).sum()),
                                                                max_abs_0_40px=int(np.abs(d[(DL >= 0) & (DL < 40)]).max()), px_diferents_total=int((d != 0).sum()))
    del d
print('genoll a la vora:', rep['genoll_41_dins_del_limbe'], flush=True)
# ---------------------------------------------------------------- les piles
PILES = {
    'V107': {3: ld(CTL / 'estat_v108/L3_RGB.npy'), **{l: ld(CTL / f'estat_v108/L{l}_G.npy') for l in FILTRES}},
    'V108': {3: ld(V8 / 'estat_v108/L3_RGB.npy'), **{l: ld(V8 / f'estat_v108/L{l}_G.npy') for l in FILTRES}},
}
PILES['F'] = {**PILES['V108'], 41: F41, 42: F42}
PILES['N'] = {**PILES['V107'], 41: N41, 42: N42}
ESTAT = {'V107': CTL / 'estat_v108', 'V108': V8 / 'estat_v108', 'F': V8 / 'estat_v108', 'N': CTL / 'estat_v108'}
alf = {}
for nom, est in ESTAT.items():   # l'alfa de dada de cada estat ha de ser la del control (= V107): si no, el compost no seria el del PSB
    alf[nom] = {str(l): int((np.asarray(ld(est / f'L{l}_alfa.npy')) != np.asarray(ld(CTL / f'estat_v108/L{l}_alfa.npy'))).sum()) for l in (3,) + FILTRES}
rep['px_alfa_diferent_del_control'] = alf
ALF = {l: ld(CAU / f'L{l}_alfa_efectiva_u16.npy') for l in (3,) + FILTRES}


def pas_comp(Cb, ab, mode, F, a):
    """Una capa del compositor de jutge_comu.comp (la mateixa fórmula), aplicada només on a > 0."""
    if F.ndim == 2: F = F[..., None]
    if mode == 'NORMAL': B = np.broadcast_to(F, Cb.shape)
    elif mode == 'MULTIPLY': B = Cb * F
    elif mode == 'OVERLAY': B = np.where(Cb < 0.5, 2 * Cb * F, 1 - 2 * (1 - Cb) * (1 - F))
    elif mode == 'LINEAR_DODGE': B = np.clip(Cb + F, 0, 1)
    elif mode == 'LIGHTEN': B = np.maximum(Cb, F)
    else: raise ValueError(mode)
    Cs = (1 - ab[..., None]) * np.broadcast_to(F, Cb.shape) + ab[..., None] * B; ao = a + ab * (1 - a)
    num = a[..., None] * Cs + (1 - a[..., None]) * ab[..., None] * Cb
    Cn = np.where(ao[..., None] > 0, num / np.maximum(ao[..., None], 1e-9), 0).astype(np.float32)
    k = a > 0
    return np.where(k[..., None], Cn, Cb).astype(np.float32), np.where(k, ao, ab).astype(np.float32)


H2, W2 = len(range(0, H, 2)), len(range(0, W, 2))
for nom, src in PILES.items():
    t = time.time()
    c1 = np.lib.format.open_memmap(CO / f'C1_{nom}.npy', 'w+', np.float32, (H, W))
    lp = np.lib.format.open_memmap(CO / f'L_{nom}.npy', 'w+', np.float32, (H, W))
    rg = np.lib.format.open_memmap(CO / f'RGB2_{nom}.npy', 'w+', np.float32, (H2, W2, 3))
    for y0 in range(0, H, 500):
        y1 = min(H, y0 + 500); capes = []
        for l in (3,) + FILTRES:
            F = np.asarray(src[l][y0:y1], np.float32) / 65535
            a = np.asarray(ALF[l][y0:y1], np.float32) / 65535 * E107.capes[l]['opacitat'] / 255
            capes.append((E107.capes[l]['mode'], F, a))
        C, ab = comp(capes, y1 - y0, W); del capes
        c1[y0:y1] = C.mean(-1)
        for l in DALT:
            box = (0, y0, W, y1); a = E107.alfa_efectiva(l, box)
            if not (a > 0).any(): continue
            C, ab = pas_comp(C, ab, E107.capes[l]['mode'], E107.rgb(l, box), a)
        lp[y0:y1] = (C[..., 0] + 2 * C[..., 1] + C[..., 2]) / 4
        rg[y0 // 2:y0 // 2 + len(range(y0, y1, 2))] = C[::2, ::2]
    c1.flush(); lp.flush(); rg.flush(); del c1, lp, rg
    print(nom, 'compost', round(time.time() - t), 's', flush=True)
# ---------------------------------------------------------------- comprovacions contra els composts de les rondes anteriors
val = {}
for nom, ref in (('V107', V8R / 'flat2d_v2/compost_control.npy'), ('F', V8R / 'flat2d_v5/compost_flat2d_v5.npy')):
    a = np.load(CO / f'C1_{nom}.npy', mmap_mode='r'); b = np.load(ref, mmap_mode='r'); mx = 0.0; nd = 0
    for y0 in range(0, H, 1000):
        d = np.abs(np.asarray(a[y0:y0 + 1000], np.float64) - np.asarray(b[y0:y0 + 1000], np.float64)); mx = max(mx, float(d.max())); nd += int((d > 0).sum())
    val[f'C1_{nom}_contra_{ref.name}'] = dict(max_abs=mx, px_diferents=nd)
for nom, ref in (('V107', V8R / 'negres_v2/pas2/L_V107.npy'), ('N', V8R / 'negres_v2/pas2/L_v4_CEL_G_MAX_T_e30_W_H0.npy')):
    a = np.asarray(np.load(CO / f'L_{nom}.npy', mmap_mode='r')[::2, ::2], np.float64); b = np.load(ref).astype(np.float64); m = (a > 1e-4) & (b > 1e-4)
    q = a[m] / b[m]; val[f'L_{nom}_pas2_contra_{ref.name}'] = dict(quocient_p0_01_p50_p99_99=[float(x) for x in np.percentile(q, [0.01, 50, 99.99])], max_abs=float(np.abs(a - b).max()))
    del a, b, q, m
rep['validacio_composts'] = val; print('validació:', json.dumps(val), flush=True)
rep['segons'] = round(time.time() - T0); rep['RSS_max_GB'] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2 ** 30, 2)
(OUT / 'M0_COMPOSTS.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1) + '\n'); print('FET', rep['segons'], 's')
