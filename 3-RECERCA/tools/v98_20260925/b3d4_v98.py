"""b3d4 (V98) · Còpia de cadena_raw/b3d4_v97.py amb una opció nova, --b3-sense-residu-local (vegeu més avall), i el claim de la V98.

b3d4 (V97) · Fusió dels trens (b3, programes congelats de la V42) i fonts sense estrelles (d4, programes congelats D4/D4b), amb les
entrades triables. És `a5_recompose.b3()` i `a8_starless_baseline.d4()` de la cadena V85 amb només tres diferències:
  1. els apilats d'entrada poden venir d'una altra carpeta (p. ex. la Vixen amb finestra comuna, `b2_v97.py`);
  2. la sortida va a una carpeta nova (`--out`), mai sobre el control;
  3. no s'exigeix el SHA antic (la dada canvia a propòsit): s'anota el SHA nou i la comparació amb el control.
Ús: b3d4_v97.py --out <carpeta> [--vixen <vixen_total.npy>] [--sony-a <sony_A_total.npy>] [--sony-b <sony_B_total.npy>] [--s4 <carpeta s4 cau>]
Per defecte, les entrades són les del control (cadena_raw/b2_*, s4_baseline)."""
import sys, argparse, json, time, types
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'v97_refundacio_20260924/cadena_raw'))
import a4_sources as _A4; _A4.CID = 'CLAUDE_V98_20260925'
from a5_recompose import *   # O, H, R, sha, save, frozen_map, literal_helpers, guard, np, cv2, ast, copy, distance_transform_edt
from scipy.ndimage import gaussian_filter
from scipy.optimize import nnls
ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); ap.add_argument('--vixen'); ap.add_argument('--sony-a'); ap.add_argument('--sony-b'); ap.add_argument('--s4'); ap.add_argument('--b3-local-esvaeix', action='store_true'); ap.add_argument('--b3-sense-residu-local', action='store_true')
a = ap.parse_args(); guard(); t0 = time.time(); OUT = Path(a.out); OUT.mkdir(parents=True, exist_ok=True)
subst = {'vixen_total_v38.npy': a.vixen, 'sony_A_total_v36.npy': a.sony_a, 'sony_B_total_v42.npy': a.sony_b}
# ---------- b3 ----------
out = OUT / 'b3'; (out / 'cau').mkdir(parents=True, exist_ok=True); (out / 'receipts').mkdir(exist_ok=True)
fr = frozen_map('B3_V42_FROZEN.json'); texts = {k: Path(row['copy']).read_text() for k, row in fr['sources'].items()}
PEGATS = []
if a.b3_local_esvaeix:
    # V97 · A1 (el «marró»): el residu local A→B (σ16 a 1/8 = σ128 px) s'estenia fora del solapament amb una convolució normalitzada
    # de nucli TRUNCAT (OpenCV, ~4σ): on el nucli s'acaba, la correcció queia de cop del valor de la vora a 0 → graó paral·lel a la vora.
    # Cura: la correcció s'esvaeix de manera contínua amb la confiança del solapament gw (fracció de solapament dins del nucli):
    # igual on gw ≥ 0,5 (dins del solapament i fins a ~σ fora), i cap a 0 sense salt on gw → 0.
    vell = 'low = gauss(nr, 16) / np.maximum(gauss(wr, 16), 1e-6)'
    nou = 'gw_ = gauss(wr, 16); low = gauss(nr, 16) / np.maximum(gw_, 1e-6) * smooth(gw_, 0.0, 0.5)'
    assert texts['b3'].count(vell) == 1; texts['b3'] = texts['b3'].replace(vell, nou); PEGATS.append(dict(on='b3.merge_pointings', vell=vell, nou=nou))
if a.b3_sense_residu_local:
    # V98 · el graó diagonal de la Sony NO es va curar a la V97: es va DESPLAÇAR (control: −1 % a ~430 px de la vora del camp, on s'acabava el
    # nucli truncat; V97: −1 % a ~990 px, on s'esvaeix a la vora del solapament A∩B; D8_DIAGONAL.json). Qualsevol correcció local mesurada
    # només a A∩B i aplicada a tota la A (la A és l'única dada fora del solapament) fa un graó allà on s'acaba. Cura: NO aplicar el residu local
    # (σ128) a la A; només el guany global de grau 2 A→B (definit a tot arreu, sense vora). El desacord local que en queda entre A i B (≲ 1 %) el
    # barregen els pesos de la fusió, que ja s'esvaeixen amb suavitat a les vores dels camps (TAPER_A_PX): una transició, no un graó.
    vell = 'low = gauss(nr, 16) / np.maximum(gauss(wr, 16), 1e-6)'
    nou = 'low = np.zeros_like(nr)'
    assert texts['b3'].count(vell) == 1; texts['b3'] = texts['b3'].replace(vell, nou); PEGATS.append(dict(on='b3.merge_pointings', vell=vell, nou=nou))
h = literal_helpers(H / 'b3_v42_replay.py', ['literal_programs']); programs, evidence = h['literal_programs'](texts)
lookup = {p.name: p for p in (O / 'sources_v29').glob('*.npy')}
for d in ['b2_sony_A', 'b2_vixen', 'b2_sony_B']: lookup.update({p.name: p for p in (O / d / 'cau').glob('*.npy')})
for k, v in subst.items():
    if v: lookup[k] = Path(v).resolve()
class ArrayInputs:
    def __getattr__(self, name): return getattr(np, name)
    def load(self, path, *args, **kw): return np.load(lookup.get(Path(path).name, path), *args, **kw)
geom = json.loads((H / 'v36_rgb_dependencies/geometry.json').read_text()); M = np.array(geom['M_llenc_a_v23']); CX, CY = 5361.768111973117, 3775.747534140857
# el namespace és el de a5_recompose.b3(), copiat literalment
src = Path(__file__).resolve().parents[1] / 'v97_refundacio_20260924/cadena_raw/a5_recompose.py'; line = next(l for l in src.read_text().splitlines() if l.startswith(' ns=dict(np=ArrayInputs()'))
exec(line.strip(), globals())
exec(programs['common'], ns); exec(programs['comu'], ns); ns['comu'] = types.SimpleNamespace(mascara_dada=ns['mascara_dada']); ns['_LIN'] = json.loads((H / 'v32g_r33_round1/receipts/R33_linealitat_sensor.json').read_text()); exec(programs['lut'], ns); ns['LIN_X'], ns['LIN_LN'] = ns['_lut']('sony')
for stage in ['34', '35', '36', '37']:
    if stage != '34': ns['REP_CANVIS_V' + str(int(stage) - 1)] = ns['REP_CANVIS']
    exec(programs[stage], ns)
save(out / 'MANIFEST.json', {'stage': 'B3 V97', 'AST': evidence, 'inputs': {k: str(v) for k, v in lookup.items()}, 'substitucions': {k: v for k, v in subst.items() if v}})
save(out / 'PEGATS.json', PEGATS)
exec(programs['b3'], ns); ns['main']()
ctrl = O / 'b3_baseline/cau'; comp = {}
for p in sorted((out / 'cau').glob('*.npy')):
    q = ctrl / p.name
    comp[p.name] = dict(sha256=sha(p), igual_al_control=(q.exists() and sha(q) == sha(p)))
save(out / 'COMPARACIO_CONTROL.json', comp); print('B3 FET', f'{time.time()-t0:.0f}s', flush=True)
# ---------- d4 ----------
fr = frozen_map('D4_D4B_FROZEN.json'); o4 = OUT / 'd4'; (o4 / 'products').mkdir(parents=True, exist_ok=True)
h = literal_helpers(H / 'd4_d4b_replay.py', ['programs']); texts = {k: Path(v['copy']).read_text() for k, v in fr['sources'].items()}; code, evidence = h['programs'](texts)
def current_claim(): assert json.loads((R / '.coordination/claim.lock/owner.json').read_text())['claim_id'] == _A4.CID
S4 = Path(a.s4) if a.s4 else O / 's4_baseline/cau'
ns = dict(__name__='v97_d4', np=np, Path=Path, json=json, hashlib=hashlib, ast=ast, time=time, gaussian_filter=gaussian_filter, nnls=nnls, R=R, O=o4 / 'products', T=H / 'd4_d4b_dependencies', V42=out, S4_DIR=S4, claim=current_claim,
          D3_INPUT=H / 'star_models_round1/products/D3_empirical_pilot.json', STARS_INPUT=H / 'star_catalog_round1/products/estrelles_v42.json',
          F_INPUT=out / 'cau/fusion_total_v42.npy', V_INPUT=lookup['vixen_total_v38.npy'], S_INPUT=out / 'cau/sony_corrected_total_v42.npy', SUP_INPUT=out / 'cau/support_v42.npy')
save(o4 / 'MANIFEST.json', {'stage': 'D4/D4b V97', 'AST': evidence, 'entrades': {k: str(ns[k]) for k in ('F_INPUT', 'V_INPUT', 'S_INPUT', 'SUP_INPUT', 'S4_DIR')}})
exec(code[0], ns); exec(code[1], ns); exec(code[2], ns)
ctrl = O / 'd4_baseline/products'; comp = {}
for p in sorted((o4 / 'products').rglob('*.npy')):
    rel = p.relative_to(o4 / 'products'); q = ctrl / rel
    comp[str(rel)] = dict(sha256=sha(p), igual_al_control=(q.exists() and sha(q) == sha(p)))
save(o4 / 'COMPARACIO_CONTROL.json', comp); save(OUT / 'COMPLETE.json', {'PASS': True, 'segons': time.time() - t0}); print('D4 FET', f'{time.time()-t0:.0f}s', flush=True)
