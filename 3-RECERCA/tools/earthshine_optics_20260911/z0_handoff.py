"""Preserve V48, inventory the rejected optical pilot, record next model and release."""
from optics_common import *
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import shutil,ast,subprocess,os

HERE=Path(__file__).resolve().parent;IA=Path('/Users/USUARI/Desktop/Eclipse 2026/IA');now=datetime.now(timezone.utc).isoformat()
def rec(p):
    p=Path(p)
    with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
    return dict(path=str(p),bytes=p.stat().st_size,sha256=h)
def write_json(p,a):p.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
prior_path=ROOT/'research/tools/earthshine_detail_20260911/delivery_manifest.json';prior=json.loads(prior_path.read_text())
prior_by_path={a['path']:a for a in prior['files']}
oldcanon=prior['canonical_after']+[prior['handoff']]
for a in oldcanon:assert rec(a['path'])['sha256']==a['sha256'],('Authority changed',a['path'])
snap=HERE/'docs_before';snap.mkdir(exist_ok=True)
for i,a in enumerate(oldcanon):
    target=snap/(str(i)+'_'+Path(a['path']).name)
    if target.exists():assert rec(target)['sha256']==a['sha256'],('Snapshot changed',target)
    else:shutil.copy2(a['path'],target)
native=json.loads((SRC/'B0_all_native.json').read_text())['frames']
inputs=[Path(m['file']) for m in native]+[SRC/'compositor_cache/G.npy',SRC/'compositor_cache/W.npy',SRC/'B0_all_native.json',SRC/'B1_full_native_ensemble.json',SRC/'B2_sony_reference.npz']
with ThreadPoolExecutor(max_workers=3) as pool:consumed=list(pool.map(rec,inputs))
for a in consumed:assert a['sha256']==prior_by_path[a['path']]['sha256'],('Consumed source changed',a['path'])
pub=prior['publication'];assert rec(pub['path'])['sha256']==pub['sha256']
base=Path(pub['path']).parent;originals=[]
for name,sha in [('Earthshine_V46_Detall.psb','0af484cb7f1919900a51267f053467974c57902414258e67f54fe98638d2eb3a'),('Earthshine_V47.psb','cd30789f64d4b6f736d176ff5eaac2f76a3ebbb546661d3b117462d26fca6227')]:
    a=rec(base/name);assert a['sha256']==sha;originals.append(a)
prefs=[]
for name in ['Previous.xmp','Preferences.xmp','Clipboard.xmp']:
    p=Path('/Users/USUARI/Library/Application Support/Adobe/CameraRaw/Defaults')/name;assert p.read_bytes()==(ROOT/'output/earthshine_reconstruction_20260911/settings_before'/name).read_bytes();prefs.append(rec(p))
js='var a=[];for(var i=0;i<app.documents.length;i++)a.push(app.documents[i].id+"|"+app.documents[i].name+"|"+app.documents[i].saved);a.join("\\n");'
sc='tell application id "com.adobe.Photoshop"\ndo javascript '+json.dumps(js)+'\nend tell'
state=subprocess.check_output(['osascript','-e',sc],text=True).strip()
assert '79|Earthshine_V45_Fonts.psb|false' in state and '140|Earthshine_V46_Detall.psb|false' in state
v48state=next(s for s in state.splitlines() if s.startswith('1297|Earthshine_V48.psb|'))
assert v48state.endswith('|false'),'Expected observed unsaved V48; re-inspect rather than overwrite changes'
save('Z0_preservation.json',dict(PASS=True,consumed_sources_exact=consumed,publication_unchanged=rec(pub['path']),originals=originals,camera_raw_preferences_exact=prefs,live_documents=state,V48_live_unsaved_changes_preserved=True,scope='Consumed native arrays and V46/V47/V48 disk files checked this round. V48 live document became unsaved and remains untouched; no claim of live pixel identity. RAW files not consumed or rewritten; previous RAW88 hashes remain traced through V48 preservation manifest.'))
print('PRESERVATION PASS',len(consumed),'source files',flush=True)

report=OUT/'RESULTAT.md';handoff=ROOT/'.coordination/HANDOFF_2026-09-11_EARTHSHINE_OPTICS_V48.md';assert not handoff.exists()
text=f'''# Handoff — V48 preservada, prova òptica rebutjada — {now}

**Producte vigent al disc sense canvis:** `{pub['path']}`, SHA `{pub['sha256']}`. No hi ha V49 ni nova correcció incorporada. **V48 oberta, document1297 amb canvis NO DESATS observats al final; no s'ha desat ni alterat aquest document en la ronda.** No s'afirma identitat dels píxels vius ni se n'ha fet una còpia nova; inspeccionar i preservar aquest estat abans de construir qualsevol producte posterior. Originals79/140 sense desar i preservats. V46/V47/V48 al disc, fonts88 i caches consumits verificados byte a byte; tres XMP exactes. No es repeteix una porta Photoshop: no hi ha cap PSB nou.

Informe `{report}`. **Represa concreta:** `{HERE/'REPRESA.md'}`. Fonts externes i abast: `{OUT/'FONTS_I_HIPOTESI.md'}`. Manifest `{HERE/'delivery_manifest.json'}`.

## Evidència nova

- A0/A1: perfils de88 captures,48 sectors, només columnes completament vàlides. Sigma curt Vixen1,514px iSony2,143px; FWHM3,57/5,05px. Predicció en altres preses curtes: error mediana0,057/0,087px; el·lipse no aporta guany clar. A partir0,5s no hi ha perfils complets qualificats amb aquest criteri.
- A2: l'error aparentment petit del perfil (aprox1% de la corona) equival a1,04vegades la brillantor interior local alVixen. No n'hi ha prou per una resta precisa del vel ni per provar textura feble.
- B0: inversió gaussiana/Tikhonov de dos HDR de6preses, Vixen2(+12,575…17,915s C2) iVixen5(+74,285…79,625s). Convergeix numèricament i compleix la discrepància de soroll prevista, però crea8.618/6.655píxels negatius a r435–454, mínims−36.098/−14.799 i anells visibles. **Rebutjada.** No retallar els negatius ni amagar-los amb màscara.
- B1 entre fonts Vixen iSony/LROC: 1guany i1pèrdua puntuals (verd5/verd4,40–64px, lineal/asinh) a la font primerenca; cap canvi nominal a la tardana. No recuperació global. B2 està escrit peròNOEXECUTAT: el candidat ja falla fidelitat; capPASS d'injecció.
- B3: en la graella lunar els centres solars canvien entre captures; alinear solarment millora la corona exterior respecte del control contrari de mateixa magnitud, però deixa residus alts a la vora. Residual efectiu mediana~0,06–0,07 interior i8,5–9,4 al llimb. Els desplaçaments calculats inclouen registre heretat i no són moviment físic pur. Fotometria, seeing i mostreig també poden contribuir: no s'ha aïllat una causa única.

## Següent model, encara no implementat

Model directe separat per captura, amb textura lunar compartida i corona en coordenades solars pròpies, ocultació física observada i resposta òptica/sensor. Primer dues èpoques de6preses, mateixos inputs/pesos; prediccions reservades i control de moviment, abans d'ampliar a88 o construir un PSB. Fórmula, rutes i cauteles a REPRESA.md. No repetir la mateixa inversió estàtica només canviant força. No reaplicar desplaçaments del Sol a tota la Lluna ni retornar al registre de vora aparent que perjudicava textura.

L'objectiu global continua actiu; no s'ha recuperat tot l'últim llimb ni l'equivalència DHS. Continuació autònoma autoritzada, pas mesurat i claim nou. Cap fitxer de Claude, Git, maquinari o delegació. Zero processos propis pendents al release.
'''.replace('verificados','verificats')
handoff.write_text(text)
entry=f'> **11-09-2026 · V48 intacta; inversió òptica estàtica rebutjada.** Mesura de nucli curt corroborada, però error absolut comparable a la llum lunar. Dues inversions HDR creen anells no físics; capV49. Les discrepàncies entre preses es concentren al llimb; següent model separarà Lluna/corona per captura. Goal actiu. Represa: `{handoff}`; pla acotat `{HERE/'REPRESA.md'}`.\n\n'
canon=[ROOT/'CLAUDE.md',ROOT/'AGENTS.md',IA/'ACTIVE.json',IA/'ESTAT_ACTUAL.md',IA/'README.md',IA/'MAPA_RUTES_I_OUTPUTS.md',IA/'Coordinació/HANDOFF_VIGENT.md',ROOT/'research/README.md']
for p in [ROOT/'CLAUDE.md',ROOT/'AGENTS.md',IA/'ESTAT_ACTUAL.md',IA/'README.md',IA/'MAPA_RUTES_I_OUTPUTS.md',ROOT/'research/README.md']:p.write_text(entry+p.read_text())
(IA/'Coordinació/HANDOFF_VIGENT.md').write_text(text)
p=IA/'ACTIVE.json';a=json.loads(p.read_text());a['updated']=now;a['phase']='post-eclipse-earthshine-V48-preserved-static-inverse-rejected';a['formal_worktree_handoff']=str(handoff)
a['earthshine_task']=dict(status='V48_PRESERVED; OPTICAL_PILOT_REJECTED; GLOBAL_DETAIL_GOAL_ACTIVE',completed='All88 edge response measured; independent short-frame predictions; two inverse HDR pilots and source judge rejected; static-scene inconsistency measured',next_action='New bounded per-capture forward model with separate lunar and solar scenes; see REPRESA.md; no strength tuning of rejected static inverse',handoff=str(handoff))
a['earthshine_optics_diagnostic']=dict(status='STATIC_HDR_INVERSE_REJECTED',report=str(report),code=str(HERE),source_predictions=str(OUT/'A1_core_prediction.json'),inverse=str(OUT/'B0_epoch_inverse.json'),independent_judge=str(OUT/'B1_inverse_judge.json'),stationarity=str(OUT/'B3_epoch_stationarity.json'),new_PSB=False,injection_executed=False,all_limb_recovery_PASS=False,V48_live_unsaved_changes_preserved=True)
write_json(p,a)
link=IA/'output/earthshine_optics_20260911';assert not link.exists() and not link.is_symlink();link.symlink_to(OUT,target_is_directory=True)
for p in HERE.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
files=[p for directory in [HERE,OUT] for p in sorted(directory.rglob('*')) if p.is_file() and p.name!='delivery_manifest.json' and '__pycache__' not in p.parts]
with ThreadPoolExecutor(max_workers=3) as pool:inventory=list(pool.map(rec,files))
write_json(HERE/'delivery_manifest.json',dict(created=now,status='V48_PRESERVED; STATIC_INVERSE_REJECTED; GLOBAL_GOAL_ACTIVE',publication=pub,files=inventory,canonical_before=oldcanon,canonical_after=[rec(p) for p in canon],handoff=rec(handoff),prior_manifest=rec(prior_path),inputs=consumed,scope='Source optical diagnosis and rejected pilot only; no new PSB, no full RAW injection. B2 code explicitly not executed. Source stationarity is a diagnostic, not exclusive attribution of cause.'))
other=[]
for line in subprocess.check_output(['ps','-axo','pid=,command='],text=True).splitlines():
    f=line.strip().split(None,1)
    if len(f)!=2:continue
    pid=int(f[0]);cmd=f[1]
    if pid in [os.getpid(),os.getppid()]:continue
    if 'python' in cmd.lower() and 'earthshine_optics_20260911/' in cmd and '.py' in cmd:other.append(dict(pid=pid,cmd=cmd))
assert not other,other
with (ROOT/'.coordination/CODEX_STATUS.md').open('a') as f:
    f.write(f'\n\n## {now} — RELEASED — V48 PRESERVADA, INVERSIÓ ESTÀTICA REBUTJADA\n\nClaim {CLAIM}. PROGRÉS: perfils88fonts, nucli curt Vixen/Sony mesurat i predit; error absolut comparable a llum interior. Dues inversions HDR creen anells negatius, refusades; control independent i estacionarietat documentats. Següent model directe separarà les escenes per captura; no repetir ajust de força estàtic. V48 vigent aldisc, SHA{pub["sha256"]}; capPSBnou, capPASS d’injecció. Fonts consumides, V46/V47/V48 aldisc i XMP exactes; documents79/140 saved=false;1297 també saved=false observat alfinal i preservat, no desat ni comparat pixelapixel amb eldisc. Inspeccionar estatviu abans de qualsevol producte nou.\n\nHandoff explícit {handoff}; informe {report}; manifest {HERE/"delivery_manifest.json"}. Objectiu global actiu, no recuperació completa del llimb. Zero processos propis després de sortir el registrador; cap Git, maquinari, delegació ni fitxer de Claude. Allibero només owner propi i directori buit.\n')
claim=ROOT/'.coordination/claim.lock';assert json.loads((claim/'owner.json').read_text())['claim_id']==CLAIM
(claim/'owner.json').unlink();claim.rmdir();print('RELEASED',len(inventory),'files; V48 preserved; goal active',flush=True)
