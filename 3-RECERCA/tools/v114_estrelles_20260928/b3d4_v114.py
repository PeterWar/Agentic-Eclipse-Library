"""b3d4_v114 (V114, Claude 28-09 nit; opció --nucli-fi (V114b): a les estrelles brillants (pic ≥ 8σ al verd de la font), la base del model d'extracció s'amplia amb 25 gaussianes fines al nucli (±4 px, pas 2, σ 1,5) — el model de sempre (σ 2 cada 3 px) deixava a la S04/S01 residus de 4,5–7,4σ al nucli que els filtres amplifiquen; la base de nucli no treu més llum a r ≥ 8 px (mediana −2 unitats en estrelles de ~1.000). Còpia de b3d4_v113c amb l'opció --recentra: cada extracció del D4 es CENTRA on hi ha la llum de la font que es tracta —fusió, Vixen o Sony—, amb el centroide de la part positiva a r ≤ 4 px sobre un pla de fons ajustat a l'anell 6–8 px, iterat fins a 3 vegades i com a molt a 4 px de la posició de la llista; sense l'opció, és la v113c. Per què: la llista antiga dona posicions ENTERES que a les estrelles brillants es desvien fins a 3–4 px de la llum real (S06 3,8, S20 3,5, S04 3,3, S03 3,2 px) i el model restat deixava un dipol que els filtres amplifiquen (S04: S/N 5,8 al render sense capes d'estrelles). ·· b3d4_v113c (V113, estrelles; còpia de v112_claude_20260928/b3d4_v113.py): la mateixa fusió congelada i el mateix D4, amb DOS canvis al D4 — (i) extraccions SEQÜENCIALS (cada caixa parteix del resultat anterior; abans una caixa solapada desfeia l'anterior) i (ii)
les extraccions addicionals de 4-RESULTATS/v114_estrelles_20260928/fantasmes/EXTRA_ESTRELLES.json (còpies de cada estrella a la posició on la
treu la Vixen, girada 0,13°, i les estrelles del S22 que el D4 no treia). Les còpies Vixen no s'apliquen a la font Sony; les canòniques noves, no a la Vixen.
· · b3d4_flat2d_v2 (V108, flat 2D lliurable) · Fusió dels trens i fonts sense estrelles amb la FUSIÓ CONGELADA a la del control.
Per què: amb el flat 2D la Vixen perd gra fix i els pesos per variància de la fusió li donaven ~10 punts més de pes a 3–6 R☉ (verificador de la
ronda 1): més soroll de píxel (+10 %) i un graó de textura més gran a la vora del camp de la Vixen (−3,5 % → −17 %). Això és un SEGON canvi
(la barreja entre trens), no el flat. «Cada canvi, una capa»: aquí l'ÚNIC canvi que entra a la fusió és la dada dels apilats; tot el que la
fusió MESURA de la dada es pren del control (la fusió de la V98–V107, 4-RESULTATS/v98_20260925/cadena_v98/b3):
  · merge_pointings (Sony A + B): el guany A→B de grau 2 (coeficients del rebut B3_fusio.json del control), la fracció d'A (sony_fA_v42.npy)
    i la decisió de la porta A+B (acceptada, com al control). El residu local ja era 0 (--b3-sense-residu-local, com la V98).
  · fuse_trains (Vixen + Sony): ρ (conformació Vixen/Sony en baixa freqüència, rho_v42.npy), δ (delta_v42.npy) i el pes de la Vixen
    (weight_vixen_v42.npy).
Els mapes de variància i la porta es continuen calculant (només per al rebut: diuen quant s'hauria mogut la fusió si no estigués congelada).
Control: amb les entrades del control ha de donar la fusió i les fonts del control BIT A BIT (prova que els pegats són neutres).
Còpia de marrons/b3d4_v108.py (= v98_20260925/b3d4_v98.py) amb l'opció --congela <carpeta b3 del control>.
Ús: b3d4_flat2d_v2.py --out <carpeta> --vixen … --sony-a … --sony-b … --b3-sense-residu-local --congela 4-RESULTATS/v98_20260925/cadena_v98/b3"""
import sys, argparse, json, time, types
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'v97_refundacio_20260924/cadena_raw'))
import a4_sources as _A4; _A4.CID = 'CLAUDE_V114_ESTRELLES_GUARDRAILS_20260928'
from a5_recompose import *   # O, H, R, sha, save, frozen_map, literal_helpers, guard, np, cv2, ast, copy, distance_transform_edt
from scipy.ndimage import gaussian_filter
from scipy.optimize import nnls
ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); ap.add_argument('--vixen'); ap.add_argument('--sony-a'); ap.add_argument('--sony-b'); ap.add_argument('--s4')
ap.add_argument('--b3-sense-residu-local', action='store_true'); ap.add_argument('--recentra', action='store_true', help='centra cada extracció del D4 a la llum real (V114)'); ap.add_argument('--extra', default=None, help='llista d\'extraccions addicionals (per defecte, la de la V113)'); ap.add_argument('--nucli-fi', action='store_true', help='a les estrelles brillants (pic ≥ 8σ al verd), base de nucli fina (±4 px, pas 2, σ 1,5) a més de la de sempre (V114b)'); ap.add_argument('--congela', help='carpeta b3 del control (cau/ i receipts/B3_fusio.json)')
ap.add_argument('--control', default=str(R / '4-RESULTATS/v98_20260925/cadena_v98'), help='per a la comparació bit a bit')
a = ap.parse_args(); guard(); t0 = time.time(); OUT = Path(a.out); OUT.mkdir(parents=True, exist_ok=True)
subst = {'vixen_total_v38.npy': a.vixen, 'sony_A_total_v36.npy': a.sony_a, 'sony_B_total_v42.npy': a.sony_b}
# ---------- b3 ----------
out = OUT / 'b3'; (out / 'cau').mkdir(parents=True, exist_ok=True); (out / 'receipts').mkdir(exist_ok=True)
fr = frozen_map('B3_V42_FROZEN.json'); texts = {k: Path(row['copy']).read_text() for k, row in fr['sources'].items()}
PEGATS = []
def pega(on, vell, nou):
    assert texts['b3'].count(vell) == 1, (on, texts['b3'].count(vell)); texts['b3'] = texts['b3'].replace(vell, nou); PEGATS.append(dict(on=on, vell=vell, nou=nou))
if a.b3_sense_residu_local:   # V98 (com el control)
    pega('b3.merge_pointings', 'low = gauss(nr, 16) / np.maximum(gauss(wr, 16), 1e-6)', 'low = np.zeros_like(nr)')
CONG = None
if a.congela:
    CONG = Path(a.congela); cc = CONG / 'cau'; recb = json.loads((CONG / 'receipts/B3_fusio.json').read_text())
    COEF = {c: [float(x) for x in recb['pointings']['channels'][str(c)]['coefficients']] for c in range(3)}; ACC = bool(recb['pointings']['porta']['acceptada_A+B'])
    FRZ = dict(COEF=COEF, ACC=ACC, FA=cc / 'sony_fA_v42.npy', RHO=cc / 'rho_v42.npy', DELTA=cc / 'delta_v42.npy', WV=cc / 'weight_vixen_v42.npy', MESURAT={})
    # 1) guany A→B: el del control (el que s'hauria ajustat queda al rebut)
    pega('b3.merge_pointings · guany A→B congelat', 'pred = coef[0] + coef[1] * gx', "FRZ['MESURAT'].setdefault('coef_A_B', {})[str(c)] = [float(x) for x in coef]; coef = np.asarray(FRZ['COEF'][c], dtype=np.float64); pred = coef[0] + coef[1] * gx")
    # 2) fracció d'A: la del control
    pega('b3.merge_pointings · fA congelada', 'tot = wA + wB; fA = np.where(tot > 0, wA / np.maximum(tot, 1e-30), 0).astype(np.float32)',
         "tot = wA + wB; fA_mesurada = np.where(tot > 0, wA / np.maximum(tot, 1e-30), 0).astype(np.float32); fA = np.asarray(np.load(FRZ['FA']), np.float32); FRZ['MESURAT']['fA_mesurada_menys_control_p1_p50_p99_solapament'] = np.percentile((fA_mesurada - fA)[ma & mb], [1, 50, 99]).tolist(); del fA_mesurada")
    # 3) porta A+B: la decisió del control
    pega('b3.merge_pointings · porta congelada', "accept = all(gate[f'sigma{s}']['A+B'] is not None and gate[f'sigma{s}']['A+B'] >= gate[f'sigma{s}']['B_sola'] - 0.005 for s in (12, 24))",
         "FRZ['MESURAT']['porta_mesurada'] = bool(all(gate[f'sigma{s}']['A+B'] is not None and gate[f'sigma{s}']['A+B'] >= gate[f'sigma{s}']['B_sola'] - 0.005 for s in (12, 24))); accept = FRZ['ACC']")
    # 4) ρ i δ: els del control
    pega('b3.fuse_trains · ρ congelada', "rho_all[..., c] = np.exp(cv2.resize(low.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)).astype(np.float32)",
         "_rho_m = np.exp(cv2.resize(low.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)).astype(np.float32); rho_all[..., c] = np.load(FRZ['RHO'], mmap_mode='r')[..., c]; FRZ['MESURAT'].setdefault('rho_mesurada_sobre_control_p1_p50_p99', {})[str(c)] = np.percentile((_rho_m / rho_all[..., c])[ms & mv], [1, 50, 99]).tolist(); del _rho_m")
    pega('b3.fuse_trains · δ congelada', "delta_all[..., c] = dl.astype(np.float32)",
         "FRZ['MESURAT'].setdefault('delta_mesurada_menys_control_p1_p50_p99', {})[str(c)] = np.percentile((dl - np.load(FRZ['DELTA'], mmap_mode='r')[..., c])[both], [1, 50, 99]).tolist(); dl = np.asarray(np.load(FRZ['DELTA'], mmap_mode='r')[..., c], np.float32); delta_all[..., c] = dl")
    # 5) pes de la Vixen: el del control
    pega('b3.fuse_trains · pes de la Vixen congelat', "fv = np.where(ms, fv, mv.astype(np.float32)); wv = fv; ws = ((1 - wv) * ms).astype(np.float32)",
         "fv = np.where(ms, fv, mv.astype(np.float32)); wv = np.asarray(np.load(FRZ['WV']), np.float32); FRZ['MESURAT']['wv_mesurat_menys_control'] = {f'{r0}-{r1}R': float(np.median((fv - wv)[ms & mv & (r >= r0 * RS) & (r < r1 * RS)])) for r0, r1 in ((2, 3), (3, 4), (4, 5), (5, 6), (6, 8))}; ws = ((1 - wv) * ms).astype(np.float32)")
h = literal_helpers(H / 'b3_v42_replay.py', ['literal_programs']); programs, evidence = h['literal_programs'](texts)
lookup = {p.name: p for p in (O / 'sources_v29').glob('*.npy')}
for d in ['b2_sony_A', 'b2_vixen', 'b2_sony_B']: lookup.update({p.name: p for p in (O / d / 'cau').glob('*.npy')})
# el control de la V98–V107 fa servir la Vixen de finestra comuna (proves_apilat/vixen_comuna_taula_original), no la de cadena_raw
lookup['vixen_total_v38.npy'] = R / '4-RESULTATS/v97_refundacio_20260924/proves_apilat/vixen_comuna_taula_original/vixen_total.npy'
for k, v in subst.items():
    if v: lookup[k] = Path(v).resolve()
class ArrayInputs:
    def __getattr__(self, name): return getattr(np, name)
    def load(self, path, *args, **kw): return np.load(lookup.get(Path(path).name, path), *args, **kw)
geom = json.loads((H / 'v36_rgb_dependencies/geometry.json').read_text()); M = np.array(geom['M_llenc_a_v23']); CX, CY = 5361.768111973117, 3775.747534140857
src = Path(__file__).resolve().parents[1] / 'v97_refundacio_20260924/cadena_raw/a5_recompose.py'; line = next(l for l in src.read_text().splitlines() if l.startswith(' ns=dict(np=ArrayInputs()'))
exec(line.strip(), globals())
if CONG is not None: ns['FRZ'] = FRZ
exec(programs['common'], ns); exec(programs['comu'], ns); ns['comu'] = types.SimpleNamespace(mascara_dada=ns['mascara_dada']); ns['_LIN'] = json.loads((H / 'v32g_r33_round1/receipts/R33_linealitat_sensor.json').read_text()); exec(programs['lut'], ns); ns['LIN_X'], ns['LIN_LN'] = ns['_lut']('sony')
for stage in ['34', '35', '36', '37']:
    if stage != '34': ns['REP_CANVIS_V' + str(int(stage) - 1)] = ns['REP_CANVIS']
    exec(programs[stage], ns)
save(out / 'MANIFEST.json', {'stage': 'B3 V108 flat2d_v2 (fusió congelada)', 'AST': evidence, 'inputs': {k: str(v) for k, v in lookup.items()}, 'substitucions': {k: v for k, v in subst.items() if v}, 'congela': str(CONG) if CONG else None})
save(out / 'PEGATS.json', PEGATS)
exec(programs['b3'], ns); ns['main']()
if CONG is not None: save(out / 'receipts/B3_CONGELAT_MESURAT.json', {k: (str(v) if isinstance(v, Path) else v) for k, v in FRZ.items()})
ctrl = Path(a.control) / 'b3/cau'; comp = {}
for p in sorted((out / 'cau').glob('*.npy')):
    q = ctrl / p.name
    comp[p.name] = dict(sha256=sha(p), igual_al_control=(q.exists() and sha(q) == sha(p)))
save(out / 'COMPARACIO_CONTROL.json', comp); print('B3 FET', f'{time.time()-t0:.0f}s', json.dumps({k: v['igual_al_control'] for k, v in comp.items()}), flush=True)
# ---------- d4 ----------
fr = frozen_map('D4_D4B_FROZEN.json'); o4 = OUT / 'd4'; (o4 / 'products').mkdir(parents=True, exist_ok=True)
h = literal_helpers(H / 'd4_d4b_replay.py', ['programs']); texts = {k: Path(v['copy']).read_text() for k, v in fr['sources'].items()}
_t = texts['d4_sources.py']; _v1 = "C=O/'sources';C.mkdir(exist_ok=True);"; _v2 = "  s=row['star'];x,y=int(s['x']),int(s['y']);"
assert _t.count(_v1) == 1 and _t.count(_v2) == 1
_t = _t.replace(_v1, "sel+=[dict(star=dict(x=e['x'],y=e['y']),vixen_copy=e['vixen_copy'],extra=e) for e in json.loads(EXTRA.read_text())];print('EXTRA',len(sel),flush=True)\n" + _v1)
_t = _t.replace(_v2, "  if 'extra' in row and ((tag=='sony' and row['vixen_copy']) or (tag=='vixen' and not row['vixen_copy'])):continue\n" + _v2)
_v3 = "q=np.array(src[y-32:y+33,x-32:x+33],float)"; assert _t.count(_v3) == 1
_t = _t.replace(_v3, "q=np.array(out[y-32:y+33,x-32:x+33],float)")   # extraccions SEQÜENCIALS: cada una parteix del resultat de l'anterior (abans, una caixa que se'n solapava desfeia l'extracció anterior)
if a.recentra:
    _d = ("RECENTRA=[]\n"
          "def recentra(a_,x,y,tag,r=4,passos=3):\n"
          " x0,y0=x,y;yy8,xx8=np.mgrid[-8:9,-8:9];rr8=np.hypot(xx8,yy8);ring=(rr8>=6)&(rr8<=8);Xr=np.stack([np.ones(ring.sum()),xx8[ring],yy8[ring]],1)\n"
          " for _ in range(passos):\n"
          "  w=np.array(a_[y-8:y+9,x-8:x+9],float)\n"
          "  if w.shape[:2]!=(17,17) or not np.isfinite(w).all():return x0,y0\n"
          "  L=w.mean(-1);cf=np.linalg.lstsq(Xr,L[ring],rcond=None)[0];L=L-(cf[0]+cf[1]*xx8+cf[2]*yy8);m=(rr8<=r)&(L>0)\n"
          "  if L[m].sum()<=0:break\n"
          "  cx=(xx8[m]*L[m]).sum()/L[m].sum();cy=(yy8[m]*L[m]).sum()/L[m].sum();nx,ny=int(round(x+cx)),int(round(y+cy))\n"
          "  if np.hypot(nx-x0,ny-y0)>4:return x0,y0\n"
          "  if (nx,ny)==(x,y):break\n"
          "  x,y=nx,ny\n"
          " RECENTRA.append([tag,int(x0),int(y0),int(x-x0),int(y-y0)]);return x,y\n")
    _t = _t.replace(_v1, _d + _v1)
    _v4 = "x,y=int(s['x']),int(s['y']);\n"
    _k = _t.find("x,y=int(s['x']),int(s['y']);"); assert _k > 0 and _t.count("x,y=int(s['x']),int(s['y']);") == 1
    _t = _t.replace("x,y=int(s['x']),int(s['y']);", "x,y=int(s['x']),int(s['y']);x,y=recentra(out,x,y,tag);")
    _v5 = "save('D4_sources.json',rep)"; assert _t.count(_v5) == 1
    _t = _t.replace(_v5, "rep['recentrat']=RECENTRA;" + _v5)
if a.nucli_fi:
    _d = ("BRILLANT=[False];GN=np.concatenate([G,np.stack([np.exp(-((xx-a)**2+(yy-b)**2)/4.5) for a in range(-4,5,2) for b in range(-4,5,2)],axis=-1)],axis=-1);DN=GN[valid];_ext0=extract_empirical;N_FI=[0]\n"
          "def es_brillant(q):\n"
          " coef=np.linalg.lstsq(X[ann],q[ann],rcond=None)[0]\n"
          " for _ in range(3):\n"
          "  res=q-X@coef;sd=1.4826*np.median(np.abs(res[ann]-np.median(res[ann])))+1e-9;k=ann&(np.abs(res)<3*sd);coef=np.linalg.lstsq(X[k],q[k],rcond=None)[0]\n"
          " return bool((q-X@coef)[rr<3].max()/sd>=8)\n"
          "def extract_empirical(q):\n"
          " if not BRILLANT[0]:return _ext0(q)\n"
          " coef=np.linalg.lstsq(X[ann],q[ann],rcond=None)[0]\n"
          " for _ in range(3):\n"
          "  res=q-X@coef;sd=1.4826*np.median(np.abs(res[ann]-np.median(res[ann])))+1e-9;k=ann&(np.abs(res)<3*sd);coef=np.linalg.lstsq(X[k],q[k],rcond=None)[0]\n"
          " bg=X@coef;z=q-bg;p,_=nnls(DN,z[valid],maxiter=5000);comp=GN@p;after=q-comp;sm=gaussian_filter(after-bg,2);old=gaussian_filter(q-bg,2);outer=sm[(rr>16)&(rr<27)];noise=1.4826*np.median(np.abs(outer-np.median(outer)))+1e-9\n"
          " return comp,dict(core_before_sigma=float(old[rr<8].max()/noise),core_after_sigma=float(sm[rr<8].max()/noise),negative_after_sigma=float(sm[rr<8].min()/noise),component_peak=float(comp.max()),component_mass=float(comp.sum()),mass_r10=float(comp[rr<10].sum()/max(comp.sum(),1e-9)),noise_sm=noise,nucli_fi=True)\n")
    _t = _t.replace(_v1, _d + _v1)
    _k6 = "  model=[];r=None\n"; assert _t.count(_k6) == 1
    _t = _t.replace(_k6, "  model=[];r=None;BRILLANT[0]=es_brillant(q[...,1]);N_FI[0]+=BRILLANT[0]\n")
    _v7 = "save('D4_sources.json',rep)"; assert _t.count(_v7) == 1
    _t = _t.replace(_v7, "rep['nucli_fi_extraccions']=int(N_FI[0]);" + _v7)
texts['d4_sources.py'] = _t; PEGATS_D4 = [dict(on='d4_sources: llista', afegit='extraccions addicionals (EXTRA_ESTRELLES.json)'), dict(on='d4_sources: bucle', afegit='còpies Vixen no a la Sony; canòniques noves no a la Vixen'), dict(on='d4_sources: extracció', vell='q = src (original)', nou='q = out (seqüencial): una caixa de 65 px que se\'n solapava tornava a escriure l\'original i desfeia l\'extracció anterior')] + ([dict(on='d4_sources: centre', vell='posició entera de la llista', nou='centroide de la llum de la font (V114, --recentra)')] if a.recentra else []) + ([dict(on='d4_sources: model', vell='25 gaussianes σ 2 cada 3 px', nou='+ 25 gaussianes σ 1,5 cada 2 px a ±4 px, només a les estrelles amb pic ≥ 8σ al verd (V114b, --nucli-fi)')] if a.nucli_fi else [])
code, evidence = h['programs'](texts)
def current_claim(): assert json.loads((R / '.coordination/claim.lock/owner.json').read_text())['claim_id'] == _A4.CID
S4 = Path(a.s4) if a.s4 else O / 's4_baseline/cau'
ns = dict(__name__='v97_d4', np=np, Path=Path, json=json, hashlib=hashlib, ast=ast, time=time, gaussian_filter=gaussian_filter, nnls=nnls, R=R, O=o4 / 'products', T=H / 'd4_d4b_dependencies', V42=out, S4_DIR=S4, claim=current_claim,
          EXTRA=Path(a.extra).resolve() if a.extra else R / '4-RESULTATS/v113_estrelles_20260928/fantasmes/EXTRA_ESTRELLES.json', D3_INPUT=H / 'star_models_round1/products/D3_empirical_pilot.json', STARS_INPUT=H / 'star_catalog_round1/products/estrelles_v42.json',
          F_INPUT=out / 'cau/fusion_total_v42.npy', V_INPUT=lookup['vixen_total_v38.npy'], S_INPUT=out / 'cau/sony_corrected_total_v42.npy', SUP_INPUT=out / 'cau/support_v42.npy')
save(o4 / 'MANIFEST.json', {'pegats_V113': PEGATS_D4, 'stage': 'D4/D4b V108 flat2d_v2', 'AST': evidence, 'entrades': {k: str(ns[k]) for k in ('F_INPUT', 'V_INPUT', 'S_INPUT', 'SUP_INPUT', 'S4_DIR')}})
exec(code[0], ns); exec(code[1], ns); exec(code[2], ns)
ctrl = Path(a.control) / 'd4/products'; comp = {}
for p in sorted((o4 / 'products').rglob('*.npy')):
    rel = p.relative_to(o4 / 'products'); q = ctrl / rel
    comp[str(rel)] = dict(sha256=sha(p), igual_al_control=(q.exists() and sha(q) == sha(p)))
save(o4 / 'COMPARACIO_CONTROL.json', comp); save(OUT / 'COMPLETE.json', {'PASS': True, 'segons': time.time() - t0}); print('D4 FET', f'{time.time()-t0:.0f}s', json.dumps({k: v['igual_al_control'] for k, v in comp.items()}), flush=True)
