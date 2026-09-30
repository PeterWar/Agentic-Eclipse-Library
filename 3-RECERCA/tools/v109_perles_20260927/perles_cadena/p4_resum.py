"""p4 (V109 · perles a la cadena) · Resum llegible per màquina de P1/P2/P3 → PERLES_CADENA_RESULTATS.json (+ SHA dels guions i de les entrades clau).
Només llegeix els JSON de 4-RESULTATS/v109_perles_20260927/perles_cadena/ i calcula el SHA-256 dels guions d'aquesta carpeta."""
import json, hashlib, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from comu_perles import OUT, R0  # noqa: E402
P1 = json.loads((OUT / 'P1_ETAPES.json').read_text()); P2 = json.loads((OUT / 'P2_AJUST_I_PICS.json').read_text()); P3 = json.loads((OUT / 'P3_PERFILS.json').read_text())
F = 'COMPOST FUSIONAT (Photoshop, amb ajust)'; PL = 'COMPOST PLE (+ capes de Pere, sense ajust)'; C1 = 'COMPOST C1 (base + 10 filtres)'


def cel(k, z, b, e='1-4'):
    v = P1[k]
    if v.get('identic'): return dict(identic=True)
    x = v[z].get(b)
    return None if x is None else dict(dl_rms=x['dl_rms'], dl_mitjana=x['dl_mitjana'], beta=x[e]['beta'], quocient_E=x[e]['quocient'])


etapes = [k for k, v in P1.items() if isinstance(v, dict) and 'identic' in v]
res = dict(
    perles=P1['perles'],
    perles_per_etapa={k: (dict(identic=True) if P1[k]['identic'] else P1[k]['perles_resum']) for k in etapes},
    zona_perles_0_6px={k: dict(**{b: cel(k, 'PERLES', b) for b in ('0..3', '3..6')}) for k in etapes},
    zona_perles_6_80px={k: dict(**{b: cel(k, 'PERLES', b) for b in ('6..10', '10..20', '20..40', '40..80')}) for k in etapes},
    resta_limbe={k: dict(**{b: cel(k, 'RESTA', b) for b in ('0..3', '3..6', '6..10', '10..20', '20..40', '40..80')}) for k in etapes},
    capes_d_ajust=P2['A_zones'] | dict(local_o_global=P2['A_local_o_global'], flat2d_o_genoll=P2['A_flat2d_o_genoll'], llenc_pas2=P2['A_llenc_pas2']),
    metrica_de_pics={c: dict(directe=v['directe_V108_sobre_V107']['p5_p50_p95'], invers=v['invers_V107_sobre_V108']['p5_p50_p95'], k=v['atenuacio_real_k_mediana'],
                             perles_directe=v['directe_V108_sobre_V107']['perles_PA155_190'], perles_invers=v['invers_V107_sobre_V108']['perles_PA155_190'],
                             sectors_directe={s: w['mediana'] for s, w in v['directe_V108_sobre_V107']['per_sector_45'].items()}) for c, v in P2['B_pics'].items()},
    perfils_limbe_PA150_200=P3,
    LF_per_fotograma=[dict(nom=f['nom'], t=f['t'], exp=f['exp'], n_zona=f['n_zona'], lnq_rms=f['lnq_zona_rms'], lnq_mitjana=f['lnq_zona_mitjana'],
                           perles_sense_pes=f['perles_saturades_o_sense_pes']) for f in P1['LF_per_fotograma']],
)
T = Path(__file__).resolve().parent
res['guions_sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(T.glob('*.py'))}
(OUT / 'PERLES_CADENA_RESULTATS.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
print('desat', OUT / 'PERLES_CADENA_RESULTATS.json')
print(json.dumps(res['perles_per_etapa'][F]), json.dumps(res['perles_per_etapa'][PL]), json.dumps(res['perles_per_etapa'][C1]))
