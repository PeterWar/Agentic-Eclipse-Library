"""x1 (verificador adversari de la V108 final, 27-09) · El PSB de pas contra la V107, capa per capa, amb guió propi.
Comprova, sense fer servir cap funció de b2/v1 de la cadena (només el lector psb69 i psd_tools):
  1. els bytes de fora de la secció de capes (capçalera, recursos d'imatge, blocs etiquetats abans i després de Lr16, compost fusionat);
  2. cada registre de capa: tot igual a la V107 (mode, opacitat, retall, banderes, màscara, rangs de fusió, tots els blocs etiquetats)
     llevat del nom (pascal i unicode) i de la longitud dels canals; que els noms canviats només canvien «V10x» → «V108»;
  3. cada canal: bytes crus iguals a la V107, o bé (només capes 3 i 41–56, canals de color) = q(estat de la cadena v108) amb una q pròpia;
     que les màscares (−2) i les alfes (−1) són byte a byte les de la V107 a TOTES les capes; que els filtres són grisos (R = G = B);
  4. quants píxels canvien per capa i canal i quant (dif. màxima i p99,9 en unitats de 16 bits).
Sortida: 4-RESULTATS/v108_20260926/verifica_v108_final/X1_PSB.json. Només lectura de la resta."""
import sys, io, json, copy, hashlib, struct, time, re
from pathlib import Path
import numpy as np
R0 = Path('/Users/USUARI/Desktop/Eclipse 2026')
sys.path.insert(0, str(R0 / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB, BIG_KEYS, _rf  # noqa: E402
from psd_tools.psd.layer_and_mask import LayerRecord  # noqa: E402
from psd_tools.constants import Tag  # noqa: E402
V107 = R0 / '1-PHOTOSHOP/V107.psb'; STG = R0 / '4-RESULTATS/v108_20260926/cadena/v108/V108_stage.psb'
EST = R0 / '4-RESULTATS/v108_20260926/cadena/v108/estat_v108'
OUT = R0 / '4-RESULTATS/v108_20260926/verifica_v108_final'; OUT.mkdir(parents=True, exist_ok=True)
T0 = time.time(); rep = {}


def sha_rang(path, a, b):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        f.seek(a); n = b - a
        while n > 0:
            d = f.read(min(n, 64 << 20)); h.update(d); n -= len(d)
    return h.hexdigest()


def sha(path): return sha_rang(path, 0, Path(path).stat().st_size)


def estructura(path):
    """Posicions pròpies: final dels recursos, inici/final de la secció de capes, posició de Lr16, registres crus, inici del compost."""
    with open(path, 'rb') as f:
        f.seek(26); n = _rf(f, 'I')[0]; f.seek(n, 1); n = _rf(f, 'I')[0]; f.seek(n, 1)
        lm = f.tell(); lmlen = _rf(f, 'Q')[0]; lmend = f.tell() + lmlen
        li = _rf(f, 'Q')[0]; assert li == 0; gm = _rf(f, 'I')[0]; f.seek(gm, 1)
        blocs = []
        while f.tell() + 12 <= lmend:
            p0 = f.tell(); sig, key = _rf(f, '4s4s'); fmt = 'Q' if key in BIG_KEYS else 'I'; n = _rf(f, fmt)[0]; st = f.tell()
            blocs.append((key.decode(), p0, st, n)); f.seek(st + (n + 3) // 4 * 4)
        lr = [b for b in blocs if b[0] == 'Lr16'][0]; f.seek(lr[2]); cnt = _rf(f, 'h')[0]; recs = []
        for _ in range(abs(cnt)):
            p = f.tell(); r = LayerRecord.read(f, version=2); e = f.tell(); f.seek(p); recs.append((r, f.read(e - p)))
    return dict(lm=lm, lmend=lmend, blocs=blocs, lr=lr, recs=recs, mida=Path(path).stat().st_size)


rep['sha_V107'] = sha(V107); rep['sha_stage'] = sha(STG); rep['mida_stage'] = STG.stat().st_size
rep['sha_V107_es_5927342e'] = rep['sha_V107'].startswith('5927342e26fef8cf')
rep['sha_stage_es_1e4ea85e'] = rep['sha_stage'] == '1e4ea85e8959c68e8af0e4ec8f67ab15fb810557d529ccb938d0a0330c907d0a'
print('SHA', rep['sha_V107'][:16], rep['sha_stage'][:16], flush=True)
A = estructura(V107); B = estructura(STG)
# 1. bytes de fora de les capes
rep['capcalera_i_recursos_iguals'] = sha_rang(V107, 0, A['lm']) == sha_rang(STG, 0, B['lm'])
ka = [(k, n) for k, _, _, n in A['blocs'] if k != 'Lr16']; kb = [(k, n) for k, _, _, n in B['blocs'] if k != 'Lr16']
rep['blocs_etiquetats_de_la_seccio'] = [k for k, *_ in A['blocs']]
rep['blocs_no_Lr16_iguals'] = ka == kb and all(sha_rang(V107, a[1], a[2] + a[3]) == sha_rang(STG, b[1], b[2] + b[3])
                                                for a, b in zip([x for x in A['blocs'] if x[0] != 'Lr16'], [x for x in B['blocs'] if x[0] != 'Lr16']))
rep['compost_fusionat_igual_al_de_la_V107'] = sha_rang(V107, A['lmend'], A['mida']) == sha_rang(STG, B['lmend'], B['mida'])
print('fora de capes:', rep['capcalera_i_recursos_iguals'], rep['blocs_no_Lr16_iguals'], rep['compost_fusionat_igual_al_de_la_V107'], flush=True)

# 2. registres
def nom_u(r): return str(r.tagged_blocks.get_data(Tag.UNICODE_LAYER_NAME))
def lid_(r): return int(r.tagged_blocks.get_data(Tag.LAYER_ID))
def normal(r, nom_pascal, nom_uni):
    r = copy.deepcopy(r); r.name = nom_pascal; r.tagged_blocks.set_data(Tag.UNICODE_LAYER_NAME, nom_uni)
    for c in r.channel_info: c.length = 0
    b = io.BytesIO(); r.write(b, version=2); return b.getvalue()
regs = {}; assert [lid_(r) for r, _ in A['recs']] == [lid_(r) for r, _ in B['recs']], 'ordre de capes'
for (ra, rawa), (rb, rawb) in zip(A['recs'], B['recs']):
    lid = lid_(ra); na, nb = nom_u(ra), nom_u(rb)
    igual_sense_nom = normal(ra, ra.name, na) == normal(rb, ra.name, na)
    ch = [(int(c.id)) for c in ra.channel_info] == [(int(c.id)) for c in rb.channel_info]
    # el nom nou ha de ser el vell amb només «V9x/V10x» → «V108» (un sol cop)
    esperat = re.sub(r'\bV(9\d|1\d\d)\b', 'V108', na, count=1) if re.search(r'\bV(9\d|1\d\d)\b', na) else na + ' · V108'
    regs[lid] = dict(nom_V107=na, nom_stage=nb, nom_canviat=na != nb, nom_esperat_si_canvia=esperat, nom_ok=(nb == na) or (nb == esperat),
                     registre_igual_llevat_del_nom=igual_sense_nom, mateixos_canals=ch, pascal_V107=ra.name, pascal_stage=rb.name)
rep['registres'] = regs
print('registres diferents (llevat del nom):', [l for l, d in regs.items() if not d['registre_igual_llevat_del_nom']], flush=True)

# 3. canals
pa = PSB(str(V107)); pb = PSB(str(STG))
def q(v):   # q pròpia: 16 bits → 15 bits del Photoshop → 16 bits
    v = np.asarray(v, np.float64); return np.clip(np.floor(v * 32768 / 65535 + 0.5), 0, 32768) * 65535 / 32768
def qi(v): return np.floor(q(v) + 0.5).astype(np.uint16)
can = {}
for La in pa.layers:
    lid = La['id']; Lb = pb.layer(lid); d = {}
    for cid in sorted(La['chans']):
        oa, na_ = La['chans'][cid]; ob, nb_ = Lb['chans'][cid]
        crus = (na_ == nb_) and sha_rang(V107, oa, oa + na_) == sha_rang(STG, ob, ob + nb_)
        e = dict(bytes_iguals=crus)
        if not crus:
            a = pa.channel(lid, cid)[0]; b = pb.channel(lid, cid)[0]
            dif = a.astype(np.int32) - b.astype(np.int32); nz = dif != 0
            e.update(px_diferents=int(nz.sum()), frac=float(nz.mean()), dif_max=int(np.abs(dif).max()),
                     dif_p99_9_dels_canviats=float(np.percentile(np.abs(dif[nz]), 99.9)) if nz.any() else 0.0)
            if cid >= 0 and lid in [3] + list(range(41, 57)):
                src = np.load(EST / ('L3_RGB.npy' if lid == 3 else f'L{lid}_G.npy'), mmap_mode='r')
                s = np.asarray(src[..., cid]) if lid == 3 else np.asarray(src)
                qs = np.empty_like(b)
                for y in range(0, s.shape[0], 700): qs[y:y + 700] = qi(s[y:y + 700])
                e['igual_a_q_estat'] = bool(np.array_equal(qs, b)); e['px_diferents_de_q_estat'] = int((qs != b).sum())
                e['estat_cru_igual'] = bool(np.array_equal(s, b))   # si l'estat ja és quantitzat, igual
                e['stage_idempotent_q'] = bool(np.array_equal(qi(b[::7, ::7]), b[::7, ::7]))
                del src, s, qs
            del a, b, dif, nz
        d[str(cid)] = e
    if lid in range(41, 57):   # grisos
        g = pb.channel(lid, 1)[0]
        d['gris_RGB'] = bool(np.array_equal(pb.channel(lid, 0)[0], g) and np.array_equal(pb.channel(lid, 2)[0], g)); del g
    can[lid] = d; print(lid, {k: (v if isinstance(v, bool) else {kk: vv for kk, vv in v.items() if kk in ('bytes_iguals', 'px_diferents', 'dif_max', 'igual_a_q_estat')}) for k, v in d.items()}, flush=True)
rep['canals'] = can
canviades = sorted(l for l, d in can.items() if any(isinstance(v, dict) and not v['bytes_iguals'] for v in d.values()))
rep['capes_amb_canals_canviats'] = canviades
rep['mascares_i_alfes_iguals_a_totes'] = all(d[k]['bytes_iguals'] for d in can.values() for k in ('-1', '-2') if k in d)
rep['nomes_canals_de_color_canviats'] = all(int(k) >= 0 for d in can.values() for k, v in d.items() if isinstance(v, dict) and not v['bytes_iguals'])
rep['color_canviat_igual_a_q_estat'] = all(v.get('igual_a_q_estat', True) for d in can.values() for k, v in d.items() if isinstance(v, dict) and not v['bytes_iguals'])
rep['noms_canviats'] = sorted(l for l, d in regs.items() if d['nom_canviat'])
rep['capes_canviades_sense_nom_nou'] = sorted(set(canviades) - set(rep['noms_canviats']))
rep['capes_amb_nom_nou_sense_canvi'] = sorted(set(rep['noms_canviats']) - set(canviades))
rep['pascal_sense_V108_a_capes_canviades'] = sorted(l for l in canviades if 'V108' not in regs[l]['pascal_stage'])
rep['segons'] = round(time.time() - T0)
(OUT / 'X1_PSB.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1) + '\n')
print(json.dumps({k: v for k, v in rep.items() if k not in ('registres', 'canals')}, ensure_ascii=False, indent=1))
